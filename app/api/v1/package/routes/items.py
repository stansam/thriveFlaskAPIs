from __future__ import annotations

from flask import request
from flask.views import MethodView
from flask_login import login_required, current_user

from app.core.auth_user import require_roles
from app.enums import UserRole
from app.core.security import csrf_protect
from app.core.dependencies import get_services
from app.core.responses import (
    success_response,
    created_response,
    no_content_response,
)
from app.core.errors.handlers import BadRequestError
from app.dto import (
    PackageHighlightCreateRequest,
    PackageHighlightUpdateRequest,
    PackageInclusionCreateRequest,
    PackageInclusionUpdateRequest,
    PackageItineraryDayCreateRequest,
    PackageItineraryDayUpdateRequest,
)
from app.api.v1.package.schemas import (
    HighlightCreateSchema,
    HighlightUpdateSchema,
    HighlightReorderSchema,
    InclusionCreateSchema,
    InclusionUpdateSchema,
    ItineraryDayCreateSchema,
    ItineraryDayUpdateSchema,
)

class HighlightListView(MethodView):
    decorators = [login_required, require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN), csrf_protect]

    def post(self, package_id: str) -> tuple:
        json_data = request.get_json()
        if json_data is None:
            raise BadRequestError("Invalid JSON payload.")
        payload = HighlightCreateSchema().load(json_data)
        data = PackageHighlightCreateRequest.model_validate(payload)
        actor_id = current_user.get_id()
        result = get_services().package.add_highlight(package_id, data, actor_id=actor_id)
        return created_response(
            data=result.model_dump(mode="json"),
            message="Highlight added successfully."
        )

class HighlightDetailView(MethodView):
    decorators = [login_required, require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN), csrf_protect]

    def patch(self, package_id: str, highlight_id: str) -> tuple:
        json_data = request.get_json()
        if json_data is None:
            raise BadRequestError("Invalid JSON payload.")
        payload = HighlightUpdateSchema().load(json_data)
        data = PackageHighlightUpdateRequest.model_validate(payload)
        actor_id = current_user.get_id()
        result = get_services().package.update_highlight(highlight_id, data, actor_id=actor_id)
        return success_response(
            data=result.model_dump(mode="json"),
            message="Highlight updated successfully."
        )

    def delete(self, package_id: str, highlight_id: str) -> tuple:
        actor_id = current_user.get_id()
        get_services().package.delete_highlight(highlight_id, actor_id=actor_id)
        return no_content_response()

class HighlightReorderView(MethodView):
    decorators = [login_required, require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN), csrf_protect]

    def post(self, package_id: str) -> tuple:
        json_data = request.get_json()
        if json_data is None:
            raise BadRequestError("Invalid JSON payload.")
        payload = HighlightReorderSchema().load(json_data)
        actor_id = current_user.get_id()
        get_services().package.reorder_highlights(package_id, payload["ordered_ids"], actor_id=actor_id)
        return success_response(message="Highlights reordered successfully.")

class InclusionListView(MethodView):
    decorators = [login_required, require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN), csrf_protect]

    def post(self, package_id: str) -> tuple:
        json_data = request.get_json()
        if json_data is None:
            raise BadRequestError("Invalid JSON payload.")
        payload = InclusionCreateSchema().load(json_data)
        data = PackageInclusionCreateRequest.model_validate(payload)
        actor_id = current_user.get_id()
        result = get_services().package.add_inclusion(package_id, data, actor_id=actor_id)
        return created_response(
            data=result.model_dump(mode="json"),
            message="Inclusion added successfully."
        )

class InclusionDetailView(MethodView):
    decorators = [login_required, require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN), csrf_protect]

    def patch(self, package_id: str, inclusion_id: str) -> tuple:
        json_data = request.get_json()
        if json_data is None:
            raise BadRequestError("Invalid JSON payload.")
        payload = InclusionUpdateSchema().load(json_data)
        data = PackageInclusionUpdateRequest.model_validate(payload)
        actor_id = current_user.get_id()
        result = get_services().package.update_inclusion(inclusion_id, data, actor_id=actor_id)
        return success_response(
            data=result.model_dump(mode="json"),
            message="Inclusion updated successfully."
        )

    def delete(self, package_id: str, inclusion_id: str) -> tuple:
        actor_id = current_user.get_id()
        get_services().package.delete_inclusion(inclusion_id, actor_id=actor_id)
        return no_content_response()

class ItineraryListView(MethodView):
    decorators = [login_required, require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN), csrf_protect]

    def post(self, package_id: str) -> tuple:
        json_data = request.get_json()
        if json_data is None:
            raise BadRequestError("Invalid JSON payload.")
        payload = ItineraryDayCreateSchema().load(json_data)
        data = PackageItineraryDayCreateRequest.model_validate(payload)
        actor_id = current_user.get_id()
        result = get_services().package.add_itinerary_day(package_id, data, actor_id=actor_id)
        return created_response(
            data=result.model_dump(mode="json"),
            message="Itinerary day added successfully."
        )

class ItineraryDayView(MethodView):
    decorators = [login_required, require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN), csrf_protect]

    def patch(self, package_id: str, day_id: str) -> tuple:
        json_data = request.get_json()
        if json_data is None:
            raise BadRequestError("Invalid JSON payload.")
        payload = ItineraryDayUpdateSchema().load(json_data)
        data = PackageItineraryDayUpdateRequest.model_validate(payload)
        actor_id = current_user.get_id()
        result = get_services().package.update_itinerary_day(day_id, data, actor_id=actor_id)
        return success_response(
            data=result.model_dump(mode="json"),
            message="Itinerary day updated successfully."
        )

    def delete(self, package_id: str, day_id: str) -> tuple:
        actor_id = current_user.get_id()
        get_services().package.delete_itinerary_day(day_id, actor_id=actor_id)
        return no_content_response()
