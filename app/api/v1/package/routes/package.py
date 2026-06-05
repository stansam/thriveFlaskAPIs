from __future__ import annotations

from flask import request
from flask.views import MethodView
from flask_login import login_required, current_user

from app.core.auth_user import require_roles
from app.enums import UserRole, PackageStatus
from app.core.security import csrf_protect
from app.extensions import limiter
from app.core.dependencies import get_services
from app.core.responses import (
    success_response,
    created_response,
)
from app.core.errors.handlers import BadRequestError
from app.dto import (
    TravelPackageCreateRequest,
    TravelPackageUpdateRequest,
)
from app.api.v1.package.schemas import (
    PackageListQuerySchema,
    PackageCreateSchema,
    PackageUpdateSchema,
)

class PackageListView(MethodView):
    decorators = [limiter.limit("60/minute")]

    def get(self) -> tuple:
        schema = PackageListQuerySchema()
        query_params = schema.load(request.args)

        status_val = query_params.get("status")
        try:
            status = PackageStatus(status_val) if status_val else None
        except ValueError:
            raise BadRequestError(f"Invalid status value: {status_val}")

        result = get_services().package.list_packages(
            status=status,
            destination_country=query_params.get("destination_country"),
            region=query_params.get("region"),
            is_featured=query_params.get("is_featured"),
            search=query_params.get("search"),
            min_price=query_params.get("min_price"),
            max_price=query_params.get("max_price"),
            page=query_params.get("page"),
            per_page=query_params.get("per_page")
        )
        data = {
            "items": [item.model_dump(mode="json") for item in result.get("items", [])],
            **{k: v for k, v in result.items() if k != "items"}
        }
        return success_response(
            data=data,
            message="Packages retrieved successfully."
        )

class PackageCreateView(MethodView):
    decorators = [login_required, require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN), csrf_protect]

    def post(self) -> tuple:
        json_data = request.get_json()
        if json_data is None:
            raise BadRequestError("Invalid JSON payload.")
        payload = PackageCreateSchema().load(json_data)
        data = TravelPackageCreateRequest.model_validate(payload)
        actor_id = current_user.get_id()
        result = get_services().package.create_package(data, actor_id=actor_id)
        return created_response(
            data=result.model_dump(mode="json"),
            message="Package created successfully."
        )

class PackageDetailView(MethodView):
    decorators = [limiter.limit("60/minute")]

    def get(self, package_id: str) -> tuple:
        result = get_services().package.get_package(package_id)
        return success_response(
            data=result.model_dump(mode="json"),
            message="Package details retrieved successfully."
        )

class PackageUpdateView(MethodView):
    decorators = [login_required, require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN), csrf_protect]

    def patch(self, package_id: str) -> tuple:
        json_data = request.get_json()
        if json_data is None:
            raise BadRequestError("Invalid JSON payload.")
        payload = PackageUpdateSchema().load(json_data)
        data = TravelPackageUpdateRequest.model_validate(payload)
        actor_id = current_user.get_id()
        result = get_services().package.update_package(package_id, data, actor_id=actor_id)
        return success_response(
            data=result.model_dump(mode="json"),
            message="Package updated successfully."
        )

class PackageBySlugView(MethodView):
    decorators = [limiter.limit("60/minute")]

    def get(self, slug: str) -> tuple:
        result = get_services().package.get_package_by_slug(slug)
        return success_response(
            data=result.model_dump(mode="json"),
            message="Package details retrieved successfully."
        )

class PackagePublishView(MethodView):
    decorators = [login_required, require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN), csrf_protect]

    def post(self, package_id: str) -> tuple:
        actor_id = current_user.get_id()
        result = get_services().package.publish_package(package_id, actor_id=actor_id)
        return success_response(
            data=result.model_dump(mode="json"),
            message="Package published successfully."
        )

class PackagePauseView(MethodView):
    decorators = [login_required, require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN), csrf_protect]

    def post(self, package_id: str) -> tuple:
        actor_id = current_user.get_id()
        result = get_services().package.pause_package(package_id, actor_id=actor_id)
        return success_response(
            data=result.model_dump(mode="json"),
            message="Package paused successfully."
        )

class PackageArchiveView(MethodView):
    decorators = [login_required, require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN), csrf_protect]

    def post(self, package_id: str) -> tuple:
        actor_id = current_user.get_id()
        result = get_services().package.archive_package(package_id, actor_id=actor_id)
        return success_response(
            data=result.model_dump(mode="json"),
            message="Package archived successfully."
        )

class PackageDuplicateView(MethodView):
    decorators = [login_required, require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN), csrf_protect]

    def post(self, package_id: str) -> tuple:
        actor_id = current_user.get_id()
        result = get_services().package.duplicate_package(package_id, actor_id=actor_id)
        return success_response(
            data=result.model_dump(mode="json"),
            message="Package duplicated successfully."
        )
