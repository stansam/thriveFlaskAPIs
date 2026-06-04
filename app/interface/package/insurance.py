from __future__ import annotations

from typing import Any
import logging

from app.enums import AuditActionType
from app.core.errors.handlers import (
    NotFoundError
)
from app.core.events.dataclass.package import (
    PackageInsuranceAddedEvent,
    PackageInsuranceUpdatedEvent,
    PackageInsuranceDeletedEvent,
)
from app.dto.package_insurance import (
    PackageInsuranceCreateRequest,
    PackageInsuranceUpdateRequest,
    PackageInsuranceResponse,
)
from app.interface._base import BaseService
from app.core.logging import get_logger

logger = get_logger(__name__)

def _publish_event(event: Any) -> None:
    from app.interface.package.services import event_bus
    event_bus.publish(event)

class PackageInsuranceService(BaseService):
    def __init__(
        self,
        package_repo: Any,
        insurance_repo: Any,
        audit_service: Any,
        uow: Any,
    ) -> None:
        self._packages = package_repo
        self._insurances = insurance_repo
        self._audits = audit_service
        self._uow = uow

    def list_insurance(self, package_id: str) -> list[PackageInsuranceResponse]:
        if not self._packages.exists(id=package_id):
            raise NotFoundError("Package", package_id)
        rows = self._insurances.list_by(package_id=package_id)
        return [PackageInsuranceResponse.model_validate(r) for r in rows]

    def add_insurance(self, package_id: str, data: PackageInsuranceCreateRequest, actor_id: str | None = None) -> PackageInsuranceResponse:
        with self._uow:
            if not self._packages.exists(id=package_id):
                raise NotFoundError("Package", package_id)
            
            ins = self._insurances.create(
                actor_id=actor_id, package_id=package_id, **data.model_dump()
            )
            self._uow.commit()

        _publish_event(PackageInsuranceAddedEvent(
            package_id=package_id, insurance_id=ins.id, actor_id=actor_id
        ))
        return PackageInsuranceResponse.model_validate(ins)

    def update_insurance(self, insurance_id: str, data: PackageInsuranceUpdateRequest, actor_id: str | None = None) -> PackageInsuranceResponse:
        with self._uow:
            ins = self._insurances.get(insurance_id)
            if not ins:
                raise NotFoundError("PackageInsurance", insurance_id)
            updates = data.model_dump(exclude_unset=True)
            if updates:
                self._insurances.update(ins, actor_id=actor_id, **updates)
            self._uow.commit()

        _publish_event(PackageInsuranceUpdatedEvent(
            package_id=ins.package_id, insurance_id=ins.id, actor_id=actor_id
        ))
        return PackageInsuranceResponse.model_validate(ins)

    def delete_insurance(self, insurance_id: str, actor_id: str | None = None) -> None:
        with self._uow:
            ins = self._insurances.get(insurance_id)
            if not ins:
                raise NotFoundError("PackageInsurance", insurance_id)
            package_id = ins.package_id
            self._insurances.delete(ins)
            self._uow.commit()

        _publish_event(PackageInsuranceDeletedEvent(
            package_id=package_id, insurance_id=insurance_id, actor_id=actor_id
        ))
