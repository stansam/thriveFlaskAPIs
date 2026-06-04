from __future__ import annotations

from flask import request
from flask.views import MethodView
from flask_login import login_required, current_user

from app.core.auth_user import require_roles
from app.enums import UserRole
from app.core.dependencies import get_services
from app.dto import (
    UserCreateRequest,
    UserUpdateRequest,
    UserPreferenceUpdateRequest,
)
from app.core.responses import (
    success_response,
    created_response,
    paginated_response_from_page,
)
from app.core.errors.handlers import (
    BadRequestError,
    InsufficientRoleError,
)
from app.api.v1.user.schemas import (
    UserListQuerySchema,
    UserAdminUpdateSchema,
    UserSelfUpdateSchema,
    UserCreateSchema,
    UserPreferenceUpdateSchema,
)


class UserListCreateView(MethodView):
    decorators = [login_required, require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)]

    def get(self) -> tuple:
        schema = UserListQuerySchema()
        query_params = schema.load(request.args)

        role_val = query_params.get("role")
        role = UserRole(role_val) if role_val else None
        is_active = query_params.get("is_active")
        search = query_params.get("search")
        page = query_params.get("page")
        per_page = query_params.get("per_page")

        result = get_services().user.list_users(
            role=role,
            is_active=is_active,
            search=search,
            page=page,
            per_page=per_page,
        )

        serialized_items = [item.model_dump(mode="json") for item in result.items]
        return paginated_response_from_page(
            page_obj=result,
            serialized_items=serialized_items,
            message="Users list retrieved successfully.",
        )

    def post(self) -> tuple:
        json_data = request.get_json()
        if json_data is None:
            raise BadRequestError("Invalid JSON payload.")
        payload = UserCreateSchema().load(json_data)
        data = UserCreateRequest.model_validate(payload)
        actor_id = current_user.get_id()

        result = get_services().user.create_user(data, actor_id=actor_id)
        return created_response(
            data=result.model_dump(mode="json"),
            message="User created successfully.",
        )


class MeView(MethodView):
    decorators = [login_required]

    def get(self) -> tuple:
        user_id = current_user.get_id()
        result = get_services().user.get_user(user_id)
        return success_response(
            data=result.model_dump(mode="json"),
            message="Current user profile retrieved successfully.",
        )


class UserDetailView(MethodView):
    decorators = [login_required]

    def get(self, user_id: str) -> tuple:
        actor = current_user.domain_user
        is_admin = actor.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)
        if current_user.get_id() != user_id and not is_admin:
            raise InsufficientRoleError("admin")

        result = get_services().user.get_user(user_id, is_admin=is_admin)
        return success_response(
            data=result.model_dump(mode="json"),
            message="User profile retrieved successfully.",
        )

    def patch(self, user_id: str) -> tuple:
        actor = current_user.domain_user
        is_admin = actor.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)
        if is_admin:
            schema = UserAdminUpdateSchema()
        elif current_user.get_id() == user_id:
            schema = UserSelfUpdateSchema()
        else:
            raise InsufficientRoleError("admin")

        json_data = request.get_json()
        if json_data is None:
            raise BadRequestError("Invalid JSON payload.")
        payload = schema.load(json_data)
        data = UserUpdateRequest.model_validate(payload)
        actor_id = current_user.get_id()

        result = get_services().user.update_user(user_id, data, actor_id=actor_id, is_admin=is_admin)
        return success_response(
            data=result.model_dump(mode="json"),
            message="User profile updated successfully.",
        )


class UserDeactivateView(MethodView):
    decorators = [login_required, require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)]

    def post(self, user_id: str) -> tuple:
        if current_user.get_id() == user_id:
            raise BadRequestError("You cannot deactivate your own account.")

        actor_id = current_user.get_id()
        result = get_services().user.deactivate_user(user_id, actor_id=actor_id)
        return success_response(
            data=result.model_dump(mode="json"),
            message="User deactivated successfully.",
        )


class UserReactivateView(MethodView):
    decorators = [login_required, require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)]

    def post(self, user_id: str) -> tuple:
        actor_id = current_user.get_id()
        result = get_services().user.reactivate_user(user_id, actor_id=actor_id)
        return success_response(
            data=result.model_dump(mode="json"),
            message="User reactivated successfully.",
        )


class UserPreferenceView(MethodView):
    decorators = [login_required]

    def get(self, user_id: str) -> tuple:
        actor = current_user.domain_user
        if current_user.get_id() != user_id and actor.role not in (
            UserRole.ADMIN,
            UserRole.SUPER_ADMIN,
        ):
            raise InsufficientRoleError("admin")

        result = get_services().user.get_preference(user_id)
        return success_response(
            data=result.model_dump(mode="json"),
            message="User preferences retrieved successfully.",
        )

    def patch(self, user_id: str) -> tuple:
        actor = current_user.domain_user
        if current_user.get_id() != user_id and actor.role not in (
            UserRole.ADMIN,
            UserRole.SUPER_ADMIN,
        ):
            raise InsufficientRoleError("admin")

        json_data = request.get_json()
        if json_data is None:
            raise BadRequestError("Invalid JSON payload.")
        payload = UserPreferenceUpdateSchema().load(json_data)
        data = UserPreferenceUpdateRequest.model_validate(payload)
        actor_id = current_user.get_id()
        result = get_services().user.update_preference(
            user_id,
            data,
            actor_id=actor_id,
        )
        return success_response(
            data=result.model_dump(mode="json"),
            message="User preferences updated successfully.",
        )
