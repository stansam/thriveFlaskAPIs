from __future__ import annotations

from decimal import Decimal
from typing import Any
import logging

from app.core.errors.handlers import (
    BadRequestError,
    NotFoundError
)
from app.core.events.dataclass.package import (
    PackagePriceTierAddedEvent,
    PackagePriceTierUpdatedEvent,
    PackagePriceTierDeactivatedEvent,
)
from app.dto.package_items import (
    PackagePriceTierCreateRequest,
    PackagePriceTierUpdateRequest,
    PackagePriceTierResponse,
)
from app.interface._base import BaseService
from app.core.logging import get_logger

logger = get_logger(__name__)

def _publish_event(event: Any) -> None:
    from app.interface.package.services import event_bus
    event_bus.publish(event)

class PackagePriceService(BaseService):
    def __init__(
        self,
        package_repo: Any,
        price_tier_repo: Any,
        insurance_repo: Any,
        audit_service: Any,
        uow: Any,
    ) -> None:
        self._packages = package_repo
        self._tiers = price_tier_repo
        self._insurances = insurance_repo
        self._audits = audit_service
        self._uow = uow

    def add_tier(self, package_id: str, data: PackagePriceTierCreateRequest, actor_id: str) -> PackagePriceTierResponse:
        with self._uow:
            if not self._packages.exists(id=package_id):
                raise NotFoundError("Package", package_id)
            existing = self._tiers.find_by_package(package_id, active_only=True)
            for ex in existing:
                if not ex.is_add_on and not data.is_add_on:
                    ex_max = ex.max_participants if ex.max_participants is not None else float("inf")
                    dt_max = data.max_participants if data.max_participants is not None else float("inf")
                    overlap = (
                        data.min_participants <= ex_max
                        and dt_max >= ex.min_participants
                    )
                    if overlap:
                        raise BadRequestError(f"Tier participant range overlaps with existing tier '{ex.label}'.")
            
            tier = self._tiers.create(
                actor_id=actor_id, package_id=package_id, **data.model_dump()
            )
            self._uow.commit()
            
        _publish_event(PackagePriceTierAddedEvent(
            package_id=package_id, tier_id=tier.id, actor_id=actor_id
        ))
        return PackagePriceTierResponse.model_validate(tier)

    def update_tier(self, tier_id: str, data: PackagePriceTierUpdateRequest, actor_id: str) -> PackagePriceTierResponse:
        with self._uow:
            tier = self._tiers.get(tier_id)
            if not tier:
                raise NotFoundError("Package Price Tier", tier_id)
            updates = data.model_dump(exclude_unset=True)
            if updates:
                self._tiers.update(tier, actor_id=actor_id, **updates)
            self._uow.commit()
            
        _publish_event(PackagePriceTierUpdatedEvent(
            package_id=tier.package_id, tier_id=tier.id, actor_id=actor_id
        ))
        return PackagePriceTierResponse.model_validate(tier)

    def deactivate_tier(self, tier_id: str, actor_id: str) -> None:
        with self._uow:
            tier = self._tiers.get(tier_id)
            if not tier:
                raise NotFoundError("Package Price Tier", tier_id)
            package_id = tier.package_id
            self._tiers.update(tier, actor_id=actor_id, is_active=False)
            self._uow.commit()

        _publish_event(PackagePriceTierDeactivatedEvent(
            package_id=package_id, tier_id=tier_id, actor_id=actor_id
        ))

    def resolve_price(self, package_id: str, num_participants: int, add_flight: bool = False, add_insurance: bool = False) -> Decimal:
        tier = self._tiers.find_matching_tier(package_id, num_participants)
        if not tier:
            raise BadRequestError(f"No active price tier found for {num_participants} participant(s).")
            
        total = tier.price_usd * num_participants

        if add_flight:
            flight_tier = self._tiers.find_matching_tier(package_id, num_participants, is_add_on=True)
            if flight_tier:
                total += flight_tier.price_usd * num_participants

        if add_insurance:
            active_insurances = self._insurances.find_by_package(package_id, active_only=True)
            if active_insurances:
                policy = active_insurances[0]
                total += policy.premium_usd + (policy.per_person_rate * num_participants)

        return total
