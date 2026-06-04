from __future__ import annotations

from flask import request
from flask.views import MethodView
from flask_login import login_required, current_user

from app.core.auth_user import require_roles
from app.enums import UserRole, AssetType, AssetOwnerType
from app.core.security import csrf_protect
from app.extensions import limiter
from app.core.dependencies import get_services
from app.core.responses import (
    success_response,
    created_response,
    no_content_response,
)
from app.core.errors.handlers import BadRequestError
from app.dto import MediaAssetUploadRequest
from app.api.v1.package.schemas import (
    MediaAttachSchema,
    MediaSetCoverSchema,
)

class PackageMediaListView(MethodView):
    decorators = [limiter.limit("60/minute")]

    def get(self, package_id: str) -> tuple:
        result = get_services().package.list_media(package_id)
        serialized = [r.model_dump(mode="json") for r in result]
        return success_response(
            data=serialized,
            message="Package media retrieved successfully."
        )

class PackageMediaAttachView(MethodView):
    decorators = [login_required, require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN), csrf_protect]

    def post(self, package_id: str) -> tuple:
        json_data = request.get_json()
        if json_data is None:
            raise BadRequestError("Invalid JSON payload.")
        payload = MediaAttachSchema().load(json_data)
        actor_id = current_user.get_id()
        result = get_services().package.attach_media(
            package_id=package_id,
            asset_id=payload["asset_id"],
            caption=payload.get("caption"),
            itinerary_day_id=payload.get("itinerary_day_id"),
            display_order=payload.get("display_order", 0),
            actor_id=actor_id,
            is_cover=payload.get("is_cover", False)
        )
        return created_response(
            data=result.model_dump(mode="json"),
            message="Media attached successfully."
        )

class PackageMediaDetailView(MethodView):
    decorators = [login_required, require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN), csrf_protect]

    def delete(self, package_id: str, media_id: str) -> tuple:
        actor_id = current_user.get_id()
        get_services().package.detach_media(package_media_id=media_id, actor_id=actor_id)
        return no_content_response()

class PackageSetCoverView(MethodView):
    decorators = [login_required, require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN), csrf_protect]

    def post(self, package_id: str) -> tuple:
        json_data = request.get_json()
        if json_data is None:
            raise BadRequestError("Invalid JSON payload.")
        payload = MediaSetCoverSchema().load(json_data)
        actor_id = current_user.get_id()
        result = get_services().package.set_cover(
            package_id=package_id,
            asset_id=payload["asset_id"],
            actor_id=actor_id
        )
        return success_response(
            data=result.model_dump(mode="json"),
            message="Cover image updated successfully."
        )

class MediaAssetUploadView(MethodView):
    decorators = [login_required, require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN), csrf_protect]

    def post(self, package_id: str) -> tuple:
        if "file" not in request.files:
            raise BadRequestError("No file part in the request.")
        file = request.files["file"]
        if file.filename == "":
            raise BadRequestError("No selected file.")

        content_type = file.content_type or "image/jpeg"
        try:
            asset_type = AssetType(content_type)
        except ValueError:
            raise BadRequestError(f"Invalid content type: {content_type}")

        alt_text = request.form.get("alt_text", "")
        is_public = request.form.get("is_public", "true").lower() == "true"

        metadata = MediaAssetUploadRequest(
            asset_type=asset_type,
            alt_text=alt_text,
            is_public=is_public,
            owner_type=AssetOwnerType.TRAVEL_PACKAGE,
            owner_id=package_id
        )

        actor_id = current_user.get_id()
        result = get_services().media.upload_asset(
            file=file,
            metadata=metadata,
            actor_id=actor_id
        )
        return created_response(
            data=result.model_dump(mode="json"),
            message="Media asset uploaded successfully."
        )