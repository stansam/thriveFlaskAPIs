import logging
from flask import request, jsonify
from flask.views import MethodView
from marshmallow import ValidationError
from app.main.schemas.packages import PackageSearchSchema
from app.services.package.service import PackageService
from app.dto.package.schemas import SearchPackageDTO
from app.utils.analytics import track_metric

logger = logging.getLogger(__name__)

class PackageListView(MethodView):
    def get(self):
        schema = PackageSearchSchema()
        try:
            data = schema.load(request.args.to_dict())
        except ValidationError as err:
            return jsonify(err.messages), 400
        package_service = PackageService()
        payload = SearchPackageDTO(
            q=data.get('q'),
            country=data.get('country'),
            min_price=data.get('min_price'),
            max_price=data.get('max_price'),
            min_days=data.get('min_days'),
            max_days=data.get('max_days')
        )
        
        try:
             # Enforce pagination structurally
             limit = data['limit']
             offset = data['offset']
             packages, total = package_service.search_packages(payload, limit=limit, offset=offset)
             
             total_pages = (total + limit - 1) // limit if limit > 0 else 1
             current_page = (offset // limit) + 1 if limit > 0 else 1
             
             track_metric("package_catalog_viewed", category="main")
             return jsonify({
                 "packages": [p.to_dict() for p in packages],
                 "pagination": {
                     "total": total,
                     "limit": limit,
                     "offset": offset,
                     "total_pages": total_pages,
                     "current_page": current_page
                 }
             }), 200
        except Exception as e:
             return jsonify({"error": str(e)}), 400

class PackageDetailView(MethodView):
    def get(self, slug):
        package_service = PackageService()
        package = package_service.find_by_slug(slug)
        if not package:
             return jsonify({"error": "Package explicitly not found natively."}), 404  
        track_metric("package_detail_viewed", category="main", dimension_key=slug)
        return jsonify(package.to_dict()), 200

class FeaturedPackageListView(MethodView):
    def get(self):
        package_service = PackageService()
        featured_packages = package_service.get_featured_packages()
        track_metric("featured_packages_viewed", category="main")
        return jsonify({"packages": [p.to_dict() for p in featured_packages]}), 200
