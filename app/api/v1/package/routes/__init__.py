# app/api/v1/package/routes/__init__.py
"""
Aggregated package routes.
"""
from app.api.v1.package.routes.package import(
    PackageListView,
    PackageCreateView,
    PackageDetailView,
    PackageUpdateView,
    PackageBySlugView,
    PackagePublishView,
    PackagePauseView,
    PackageArchiveView,
    PackageDuplicateView,
)
from app.api.v1.package.routes.items import (
    HighlightListView,
    HighlightDetailView,
    HighlightReorderView,
    InclusionListView,
    InclusionDetailView,
    ItineraryListView,
    ItineraryDayView,
)
from app.api.v1.package.routes.price import (
    PriceTierListView,
    PriceTierDetailView,
    PriceTierDeactivateView,
    ResolvePriceView,
)
from app.api.v1.package.routes.media import (
    PackageMediaListView,
    PackageMediaAttachView,
    PackageMediaDetailView,
    PackageSetCoverView,
    MediaAssetUploadView,
)
from app.api.v1.package.routes.insurance import(
    InsuranceListView,
    InsuranceCreateView,
    InsuranceDetailView,
)

from app.api.v1.utils import RouteConfig

PACKAGE_CORE_ROUTES: list[RouteConfig] = [
    {
        "url_rule": "",
        "view_func": PackageListView.as_view("package_list"),
        "methods": ["GET"],
    },
    {
        "url_rule": "",
        "view_func": PackageCreateView.as_view("package_create"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/<package_id>",
        "view_func": PackageDetailView.as_view("package_detail"),
        "methods": ["GET"],
    },
    {
        "url_rule": "/<package_id>",
        "view_func": PackageUpdateView.as_view("package_update"),
        "methods": ["PATCH"],
    },
    {
        "url_rule": "/slug/<slug>",
        "view_func": PackageBySlugView.as_view("package_by_slug"),
        "methods": ["GET"],
    },
    {
        "url_rule": "/<package_id>/publish",
        "view_func": PackagePublishView.as_view("package_publish"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/<package_id>/pause",
        "view_func": PackagePauseView.as_view("package_pause"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/<package_id>/archive",
        "view_func": PackageArchiveView.as_view("package_archive"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/<package_id>/duplicate",
        "view_func": PackageDuplicateView.as_view("package_duplicate"),
        "methods": ["POST"],
    },
]

PACKAGE_ITEM_ROUTES: list[RouteConfig] = [
    {
        "url_rule": "/<package_id>/highlights",
        "view_func": HighlightListView.as_view("highlight_list"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/<package_id>/highlights/<highlight_id>",
        "view_func": HighlightDetailView.as_view("highlight_detail"),
        "methods": ["PATCH", "DELETE"],
    },
    {
        "url_rule": "/<package_id>/highlights/reorder",
        "view_func": HighlightReorderView.as_view("highlight_reorder"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/<package_id>/inclusions",
        "view_func": InclusionListView.as_view("inclusion_list"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/<package_id>/inclusions/<inclusion_id>",
        "view_func": InclusionDetailView.as_view("inclusion_detail"),
        "methods": ["PATCH", "DELETE"],
    },
    {
        "url_rule": "/<package_id>/itinerary",
        "view_func": ItineraryListView.as_view("itinerary_list"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/<package_id>/itinerary/<day_id>",
        "view_func": ItineraryDayView.as_view("itinerary_day_detail"),
        "methods": ["PATCH", "DELETE"],
    },
]

PACKAGE_MEDIA_ROUTES: list[RouteConfig] = [
    {
        "url_rule": "/<package_id>/media",
        "view_func": PackageMediaListView.as_view("package_media_list"),
        "methods": ["GET"],
    },
    {
        "url_rule": "/<package_id>/media",
        "view_func": PackageMediaAttachView.as_view("package_media_attach"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/<package_id>/media/<media_id>",
        "view_func": PackageMediaDetailView.as_view("package_media_detail"),
        "methods": ["DELETE"],
    },
    {
        "url_rule": "/<package_id>/media/set-cover",
        "view_func": PackageSetCoverView.as_view("package_set_cover"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/<package_id>/media/upload",
        "view_func": MediaAssetUploadView.as_view("package_media_upload"),
        "methods": ["POST"],
    },
]

PACKAGE_PRICE_ROUTES: list[RouteConfig] = [
    {
        "url_rule": "/<package_id>/price-tiers",
        "view_func": PriceTierListView.as_view("price_tier_list"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/<package_id>/price-tiers/<tier_id>",
        "view_func": PriceTierDetailView.as_view("price_tier_detail"),
        "methods": ["PATCH"],
    },
    {
        "url_rule": "/<package_id>/price-tiers/<tier_id>",
        "view_func": PriceTierDeactivateView.as_view("price_tier_deactivate"),
        "methods": ["DELETE"],
    },
    {
        "url_rule": "/<package_id>/resolve-price",
        "view_func": ResolvePriceView.as_view("package_resolve_price"),
        "methods": ["GET"],
    },
]

PACKAGE_INSURANCE_ROUTES: list[RouteConfig] = [
    {
        "url_rule": "/<package_id>/insurance",
        "view_func": InsuranceListView.as_view("package_insurance_list"),
        "methods": ["GET"],
    },
    {
        "url_rule": "/<package_id>/insurance",
        "view_func": InsuranceCreateView.as_view("package_insurance_create"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/<package_id>/insurance/<insurance_id>",
        "view_func": InsuranceDetailView.as_view("package_insurance_detail"),
        "methods": ["PATCH", "DELETE"],
    },
]

PACKAGE_ROUTES = (
    PACKAGE_CORE_ROUTES
    + PACKAGE_ITEM_ROUTES
    + PACKAGE_PRICE_ROUTES
    + PACKAGE_MEDIA_ROUTES
    + PACKAGE_INSURANCE_ROUTES
)

__all__ = ["PACKAGE_ROUTES"]