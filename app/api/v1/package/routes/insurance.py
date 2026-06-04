from __future__ import annotations

from flask import request
from flask.views import MethodView
from flask_login import login_required, current_user

from app.core.auth_user import require_roles
from app.enums import UserRole
from app.core.security import csrf_protect
from app.extensions import limiter
from app.core.dependencies import get_services
from app.core.responses import (
    success_response,
    created_response,
    no_content_response,
)
from app.core.errors.handlers import BadRequestError
from app.dto.package_insurance import (
    PackageInsuranceCreateRequest,
    PackageInsuranceUpdateRequest,
)
from app.api.v1.package.schemas import (
    InsuranceCreateSchema,
    InsuranceUpdateSchema,
)

class InsuranceListView(MethodView):
    decorators = [limiter.limit("60/minute")]

    def get(self, package_id: str) -> tuple:
        result = get_services().package.list_insurance(package_id)
        serialized = [r.model_dump(mode="json") for r in result]
        return success_response(
            data=serialized,
            message="Package insurance options retrieved successfully."
        )

class InsuranceCreateView(MethodView):
    decorators = [login_required, require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN), csrf_protect]

    def post(self, package_id: str) -> tuple:
        json_data = request.get_json()
        if json_data is None:
            raise BadRequestError("Invalid JSON payload.")
        payload = InsuranceCreateSchema().load(json_data)
        data = PackageInsuranceCreateRequest.model_validate(payload)
        actor_id = current_user.get_id()
        result = get_services().package.add_insurance(package_id, data, actor_id=actor_id)
        return created_response(
            data=result.model_dump(mode="json"),
            message="Insurance option added successfully."
        )

class InsuranceDetailView(MethodView):
    decorators = [login_required, require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN), csrf_protect]

    def patch(self, package_id: str, insurance_id: str) -> tuple:
        json_data = request.get_json()
        if json_data is None:
            raise BadRequestError("Invalid JSON payload.")
        payload = InsuranceUpdateSchema().load(json_data)
        data = PackageInsuranceUpdateRequest.model_validate(payload)
        actor_id = current_user.get_id()
        result = get_services().package.update_insurance(insurance_id, data, actor_id=actor_id)
        return success_response(
            data=result.model_dump(mode="json"),
            message="Insurance option updated successfully."
        )

    def delete(self, package_id: str, insurance_id: str) -> tuple:
        actor_id = current_user.get_id()
        get_services().package.delete_insurance(insurance_id, actor_id=actor_id)
        return no_content_response()
