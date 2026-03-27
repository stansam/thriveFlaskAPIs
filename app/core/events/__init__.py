# core/events.py
"""
In-process synchronous domain event bus.

Architecture
------------
Services publish typed `DomainEvent` dataclasses to the bus.
Subscriber functions registered with `@subscribe(EventClass)` are
called synchronously in the same thread and transaction as the
publishing service.

This approach has a deliberate tradeoff:
  + Simplicity — no broker, no worker process, no serialisation overhead
  + Atomicity  — subscriber runs inside the same DB transaction as the
                 publisher; if the subscriber raises, the whole operation
                 rolls back
  - Latency    — slow subscribers block the HTTP response
  - Scale      — unsuitable for high-fan-out events (100+ subscribers)

For the current scale (Dr. Edna + a few agents), this is the right choice.
The `AsyncBridgeHook` extension point lets you swap in Celery later with
zero changes to publishers or subscribers.

Usage
-----
    # Define an event (in the domain module that owns it)
    @dataclass
    class BookingConfirmedEvent(DomainEvent):
        booking_id: str
        client_id: str
        reference_number: str

    # Register a subscriber (e.g. in services/notification_service.py)
    @subscribe(BookingConfirmedEvent)
    def send_booking_confirmation(event: BookingConfirmedEvent) -> None:
        notification_service.dispatch(
            NotificationEventType.BOOKING_CONFIRMED,
            ...
        )

    # Publish (inside BookingService.transition_status)
    event_bus.publish(BookingConfirmedEvent(
        booking_id=booking.id,
        client_id=booking.client_id,
        reference_number=booking.reference_number,
    ))

Thread safety
-------------
The subscriber registry is a plain dict.  Registrations happen at
import time (module load), before any request threads start.  No lock
is needed for reads; mutations at runtime are not supported.
"""

from __future__ import annotations

import logging
import threading
from collections import defaultdict
from typing import Callable, Type, TypeVar
from app.core.events.dataclass.base import DomainEvent
logger = logging.getLogger(__name__)

E = TypeVar("E", bound="DomainEvent")
SubscriberFn = Callable[["DomainEvent"], None]

class EventBus:
    """
    In-process publish/subscribe event bus.

    Registry is module-level and built at import time via `@subscribe`.
    Publishing is synchronous within the calling thread/transaction.

    Dead-letter logging
    -------------------
    If a subscriber raises an exception it is caught, logged at ERROR
    level, and the remaining subscribers still execute.  The original
    exception is re-raised after all subscribers have run only if
    `raise_on_subscriber_error=True` (default False — fail-soft to
    prevent a notification failure from rolling back a booking).

    Async bridge
    ------------
    Set `event_bus.async_bridge = my_celery_task.delay` to forward
    every published event to a Celery worker instead of (or in addition
    to) the synchronous subscribers.
    """

    def __init__(self, raise_on_subscriber_error: bool = False) -> None:
        self._subscribers: dict[type, list[SubscriberFn]] = defaultdict(list)
        self._lock = threading.RLock()
        self.raise_on_subscriber_error = raise_on_subscriber_error
        self.async_bridge: Callable[[DomainEvent], None] | None = None

    def subscribe(self, event_class: Type[E]) -> Callable[[SubscriberFn], SubscriberFn]:
        """
        Decorator factory: register a function as a subscriber for an event type.

            @event_bus.subscribe(BookingConfirmedEvent)
            def on_booking_confirmed(event: BookingConfirmedEvent) -> None:
                ...
        """
        def decorator(fn: SubscriberFn) -> SubscriberFn:
            with self._lock:
                self._subscribers[event_class].append(fn)
                logger.debug(
                    "EventBus: registered %s → %s.%s",
                    event_class.__name__,
                    fn.__module__,
                    fn.__qualname__,
                )
            return fn
        return decorator

    def publish(self, event: DomainEvent) -> None:
        """
        Publish an event synchronously to all registered subscribers.

        Execution order within each event type matches registration order
        (i.e. module import order).
        """
        event_class = type(event)
        subscribers = list(self._subscribers.get(event_class, []))

        logger.debug(
            "EventBus: publishing %s (id=%s, %d subscribers)",
            event_class.__name__,
            event.event_id,
            len(subscribers),
        )

        errors: list[tuple[SubscriberFn, Exception]] = []

        for fn in subscribers:
            try:
                fn(event)
            except Exception as exc:
                logger.error(
                    "EventBus subscriber %s.%s raised on %s (event_id=%s): %s",
                    fn.__module__,
                    fn.__qualname__,
                    event_class.__name__,
                    event.event_id,
                    exc,
                    exc_info=True,
                )
                errors.append((fn, exc))

        # Forward to async bridge if configured
        if self.async_bridge is not None:
            try:
                self.async_bridge(event)
            except Exception as exc:
                logger.error("EventBus async bridge failed: %s", exc, exc_info=True)

        if self.raise_on_subscriber_error and errors:
            # Re-raise the first subscriber error after all have run
            raise errors[0][1]

    def clear_subscribers(self) -> None:
        """Remove all subscribers. Useful for test isolation."""
        with self._lock:
            self._subscribers.clear()

    def subscriber_count(self, event_class: Type[DomainEvent]) -> int:
        return len(self._subscribers.get(event_class, []))

    def __repr__(self) -> str:
        total = sum(len(v) for v in self._subscribers.values())
        return f"<EventBus {len(self._subscribers)} event types, {total} subscribers>"


event_bus = EventBus(raise_on_subscriber_error=False)


def subscribe(event_class: Type[E]) -> Callable[[SubscriberFn], SubscriberFn]:
    """
    Module-level @subscribe decorator — shortcut for event_bus.subscribe.

        from app.core.events import subscribe, BookingConfirmedEvent

        @subscribe(BookingConfirmedEvent)
        def handle(event: BookingConfirmedEvent) -> None:
            ...
    """
    return event_bus.subscribe(event_class)