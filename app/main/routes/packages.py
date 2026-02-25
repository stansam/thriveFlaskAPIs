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
            country=data.get('country'),
            duration_days_min=data.get('duration_days_min'),
            duration_days_max=data.get('duration_days_max')
        )
        
        try:
             # Enforce pagination structurally
             limit = data['limit']
             offset = data['offset']
             
             packages = package_service.search_packages(payload, limit=limit, offset=offset)
             track_metric("package_catalog_viewed", category="main")
             
             return jsonify({
                 "packages": [p.to_dict() for p in packages]
             }), 200
        except Exception as e:
             return jsonify({"error": str(e)}), 400


class PackageDetailView(MethodView):
    def get(self, slug):
        package_service = PackageService()
        
        from app.repository import repositories
        package = repositories.package.find_by_slug(slug)
        
        if not package:
             return jsonify({"error": "Package explicitly not found natively."}), 404
             
        track_metric("package_detail_viewed", category="main", dimension_key=slug)
        return jsonify(package.to_dict()), 200

class FeaturedPackageListView(MethodView):
    def get(self):
        package_service = PackageService()
        
        from app.repository import repositories
        # Assuming our repository has a method to fetch featured packages natively
        featured_packages = repositories.package.get_featured_packages(limit=5)
        
        track_metric("featured_packages_viewed", category="main")
        return jsonify({"packages": [p.to_dict() for p in featured_packages]}), 200
