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
from app.dto import (
    PackagePriceTierCreateRequest,
    PackagePriceTierUpdateRequest,
)
from app.api.v1.package.schemas import (
    PriceTierCreateSchema,
    PriceTierUpdateSchema,
)

class PriceTierListView(MethodView):
    decorators = [login_required, require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN), csrf_protect]

    def post(self, package_id: str) -> tuple:
        json_data = request.get_json()
        if json_data is None:
            raise BadRequestError("Invalid JSON payload.")
        payload = PriceTierCreateSchema().load(json_data)
        data = PackagePriceTierCreateRequest.model_validate(payload)
        actor_id = current_user.get_id()
        result = get_services().package.add_price_tier(package_id, data, actor_id=actor_id)
        return created_response(
            data=result.model_dump(mode="json"),
            message="Price tier added successfully."
        )

class PriceTierDetailView(MethodView):
    decorators = [login_required, require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN), csrf_protect]

    def patch(self, package_id: str, tier_id: str) -> tuple:
        json_data = request.get_json()
        if json_data is None:
            raise BadRequestError("Invalid JSON payload.")
        payload = PriceTierUpdateSchema().load(json_data)
        data = PackagePriceTierUpdateRequest.model_validate(payload)
        actor_id = current_user.get_id()
        result = get_services().package.update_price_tier(tier_id, data, actor_id=actor_id)
        return success_response(
            data=result.model_dump(mode="json"),
            message="Price tier updated successfully."
        )

class PriceTierDeactivateView(MethodView):
    decorators = [login_required, require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN), csrf_protect]

    def delete(self, package_id: str, tier_id: str) -> tuple:
        actor_id = current_user.get_id()
        get_services().package.deactivate_price_tier(tier_id, actor_id=actor_id)
        return no_content_response()

class ResolvePriceView(MethodView):
    decorators = [limiter.limit("60/minute")]

    def get(self, package_id: str) -> tuple:
        num_participants = request.args.get("num_participants", type=int)
        if not num_participants:
            raise BadRequestError("num_participants query parameter is required.")
        add_flight = request.args.get("add_flight", default=False, type=lambda v: v.lower() == 'true')
        add_insurance = request.args.get("add_insurance", default=False, type=lambda v: v.lower() == 'true')

        price = get_services().package.resolve_price_for_booking(
            package_id=package_id,
            num_participants=num_participants,
            add_flight=add_flight,
            add_insurance=add_insurance
        )
        return success_response(
            data={"resolved_price_usd": str(price)},
            message="Price resolved successfully."
        )
