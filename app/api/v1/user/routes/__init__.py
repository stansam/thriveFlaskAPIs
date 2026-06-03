from app.api.v1.user.routes.routes import (
    UserListCreateView,
    MeView,
    UserDetailView,
    UserDeactivateView,
    UserReactivateView,
    UserPreferenceView,
)
from app.api.v1.utils import RouteConfig

USER_ROUTES: list[RouteConfig] = [
    {
        "url_rule": "/",
        "view_func": UserListCreateView.as_view("user_list_create"),
        "methods": ["GET", "POST"],
    },
    {
        "url_rule": "/me",
        "view_func": MeView.as_view("user_me"),
        "methods": ["GET"],
    },
    {
        "url_rule": "/<user_id>",
        "view_func": UserDetailView.as_view("user_detail"),
        "methods": ["GET", "PATCH"],
    },
    {
        "url_rule": "/<user_id>/deactivate",
        "view_func": UserDeactivateView.as_view("user_deactivate"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/<user_id>/reactivate",
        "view_func": UserReactivateView.as_view("user_reactivate"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/<user_id>/preferences",
        "view_func": UserPreferenceView.as_view("user_preferences"),
        "methods": ["GET", "PATCH"],
    },
]
