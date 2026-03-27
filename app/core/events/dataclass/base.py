from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class DomainEvent:
    """
    Base class for all domain events.

    `event_id`   — automatically generated UUID for tracing.
    `occurred_at` — UTC timestamp of the moment the event was created.

    Subclasses should be frozen dataclasses so events are immutable
    once published (add `@dataclass(frozen=True)` or use `eq=True`).
    """
    event_id:    str     = field(default_factory=lambda: __import__("uuid").uuid4().hex)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
