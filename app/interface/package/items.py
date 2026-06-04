from __future__ import annotations

from typing import Any
import logging

from app.core.errors.handlers import (
    BadRequestError,
    NotFoundError
)
from app.core.events.dataclass.package import (
    PackageHighlightAddedEvent,
    PackageHighlightUpdatedEvent,
    PackageHighlightDeletedEvent,
    PackageInclusionAddedEvent,
    PackageInclusionUpdatedEvent,
    PackageInclusionDeletedEvent,
    PackageItineraryDayAddedEvent,
    PackageItineraryDayUpdatedEvent,
    PackageItineraryDayDeletedEvent,
)
from app.dto.package_items import (
    PackageHighlightCreateRequest,
    PackageHighlightUpdateRequest,
    PackageHighlightResponse,
    PackageInclusionCreateRequest,
    PackageInclusionUpdateRequest,
    PackageInclusionResponse,
    PackageItineraryDayCreateRequest,
    PackageItineraryDayUpdateRequest,
    PackageItineraryDayResponse,
)
from app.interface._base import BaseService
from app.core.logging import get_logger

logger = get_logger(__name__)

def _publish_event(event: Any) -> None:
    from app.interface.package.services import event_bus
    event_bus.publish(event)

class PackageItemsService(BaseService):
    def __init__(
        self,
        package_repo: Any,
        highlight_repo: Any,
        inclusion_repo: Any,
        itinerary_repo: Any,
        audit_service: Any,
        uow: Any,
    ) -> None:
        self._packages = package_repo
        self._highlights = highlight_repo
        self._inclusions = inclusion_repo
        self._itineraries = itinerary_repo
        self._audits = audit_service
        self._uow = uow

    # Highlights
    def add_highlight(self, package_id: str, data: PackageHighlightCreateRequest, actor_id: str) -> PackageHighlightResponse:
        with self._uow:
            if not self._packages.exists(id=package_id):
                raise NotFoundError("Package", package_id)
            
            max_order = self._highlights.max_display_order(package_id)
            new_order = max_order + 1
            
            h = self._highlights.create(
                actor_id=actor_id, package_id=package_id,
                text=data.text, icon=data.icon, display_order=new_order
            )
            self._uow.commit()

        _publish_event(PackageHighlightAddedEvent(
            package_id=package_id, highlight_id=h.id, actor_id=actor_id
        ))
        return PackageHighlightResponse.model_validate(h)

    def update_highlight(self, highlight_id: str, data: PackageHighlightUpdateRequest, actor_id: str) -> PackageHighlightResponse:
        with self._uow:
            h = self._highlights.get(highlight_id)
            if not h:
                raise NotFoundError("Package Highlight", highlight_id)
            
            updates = data.model_dump(exclude_unset=True)
            if updates:
                self._highlights.update(h, actor_id=actor_id, **updates)
            self._uow.commit()

        _publish_event(PackageHighlightUpdatedEvent(
            package_id=h.package_id, highlight_id=h.id, actor_id=actor_id
        ))
        return PackageHighlightResponse.model_validate(h)

    def delete_highlight(self, highlight_id: str, actor_id: str) -> None:
        with self._uow:
            h = self._highlights.get(highlight_id)
            if not h:
                raise NotFoundError("Package Highlight", highlight_id)
            package_id = h.package_id
            self._highlights.delete(h)
            self._uow.commit()
            
        _publish_event(PackageHighlightDeletedEvent(
            package_id=package_id, highlight_id=highlight_id, actor_id=actor_id
        ))

    def reorder_highlights(self, package_id: str, ordered_ids: list[str], actor_id: str) -> None:
        with self._uow:
            if not self._packages.exists(id=package_id):
                raise NotFoundError("Package", package_id)
            self._highlights.reorder(package_id, ordered_ids, actor_id=actor_id)
            self._uow.commit()

    # Inclusions
    def add_inclusion(self, package_id: str, data: PackageInclusionCreateRequest, actor_id: str) -> PackageInclusionResponse:
        with self._uow:
            if not self._packages.exists(id=package_id):
                raise NotFoundError("Package", package_id)
            inc = self._inclusions.create(
                actor_id=actor_id, package_id=package_id, **data.model_dump()
            )
            self._uow.commit()

        _publish_event(PackageInclusionAddedEvent(
            package_id=package_id, inclusion_id=inc.id, actor_id=actor_id
        ))
        return PackageInclusionResponse.model_validate(inc)

    def update_inclusion(self, inclusion_id: str, data: PackageInclusionUpdateRequest, actor_id: str) -> PackageInclusionResponse:
        with self._uow:
            inc = self._inclusions.get(inclusion_id)
            if not inc:
                raise NotFoundError("Package Inclusion", inclusion_id)
            updates = data.model_dump(exclude_unset=True)
            if updates:
                self._inclusions.update(inc, actor_id=actor_id, **updates)
            self._uow.commit()

        _publish_event(PackageInclusionUpdatedEvent(
            package_id=inc.package_id, inclusion_id=inc.id, actor_id=actor_id
        ))
        return PackageInclusionResponse.model_validate(inc)

    def delete_inclusion(self, inclusion_id: str, actor_id: str) -> None:
        with self._uow:
            inc = self._inclusions.get(inclusion_id)
            if not inc:
                raise NotFoundError("Package Inclusion", inclusion_id)
            package_id = inc.package_id
            self._inclusions.delete(inc)
            self._uow.commit()
            
        _publish_event(PackageInclusionDeletedEvent(
            package_id=package_id, inclusion_id=inclusion_id, actor_id=actor_id
        ))

    # Itineraries
    def add_itinerary_day(self, package_id: str, data: PackageItineraryDayCreateRequest, actor_id: str) -> PackageItineraryDayResponse:
        with self._uow:
            if not self._packages.exists(id=package_id):
                raise NotFoundError("Package", package_id)
            expected = self._itineraries.max_day_number(package_id) + 1
            if data.day_number != expected:
                raise BadRequestError(
                    f"Day number must be sequential. Expected day {expected}, got {data.day_number}."
                )
            day = self._itineraries.create(
                actor_id=actor_id, package_id=package_id, **data.model_dump()
            )
            self._uow.commit()
            
        _publish_event(PackageItineraryDayAddedEvent(
            package_id=package_id, day_id=day.id, actor_id=actor_id
        ))
        return PackageItineraryDayResponse.model_validate(day)

    def update_itinerary_day(self, day_id: str, data: PackageItineraryDayUpdateRequest, actor_id: str) -> PackageItineraryDayResponse:
        with self._uow:
            day = self._itineraries.get(day_id)
            if not day:
                raise NotFoundError("Package Itinerary Day", day_id)
            updates = data.model_dump(exclude_unset=True)
            if updates:
                self._itineraries.update(day, actor_id=actor_id, **updates)
            self._uow.commit()
            
        _publish_event(PackageItineraryDayUpdatedEvent(
            package_id=day.package_id, day_id=day.id, actor_id=actor_id
        ))
        return PackageItineraryDayResponse.model_validate(day)

    def delete_itinerary_day(self, day_id: str, actor_id: str) -> None:
        with self._uow:
            day = self._itineraries.get(day_id)
            if not day:
                raise NotFoundError("Package Itinerary Day", day_id)
            package_id = day.package_id
            self._itineraries.delete(day)
            self._uow.commit()
            
        _publish_event(PackageItineraryDayDeletedEvent(
            package_id=package_id, day_id=day_id, actor_id=actor_id
        ))
