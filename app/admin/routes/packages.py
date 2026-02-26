import logging
import os
from flask import request, jsonify, current_app
from werkzeug.utils import secure_filename
from app.tasks.package_tasks import process_package_csv_task
from flask.views import MethodView
from app.admin.routes.dashboard import admin_required
from app.admin.schemas.packages import ManagePackageSchema
from marshmallow import ValidationError
from app.utils.audit_log import log_audit
from app.utils.analytics import track_metric
from app.models.enums import AuditAction, EntityType
from flask_login import current_user

logger = logging.getLogger(__name__)

class ManagePackageView(MethodView):
    decorators = [admin_required]

    def post(self):
        """Create a new holiday package explicitly mapping admin payload"""
        schema = ManagePackageSchema()
        try:
             data = schema.load(request.json)
        except ValidationError as err:
             return jsonify(err.messages), 400

        try:
             from app.services.package.service import PackageService
             from app.dto.package.schemas import CreatePackageDTO
             package_service = PackageService()
             
             dto = CreatePackageDTO(
                 name=data['name'],
                 slug=data['slug'],
                 description=data['description'],
                 price=data['price'],
                 currency=data['currency'],
                 duration_days=data['duration_days'],
                 country=data['country'],
                 is_featured=data['is_featured'],
                 is_active=data['is_active'],
                 available_slots=data['available_slots']
             )
             
             package = package_service.create_package(dto)
             
             log_audit(
                 action=AuditAction.CREATE,
                 entity_type=EntityType.PACKAGE,
                 entity_id=package.id,
                 user_id=current_user.id,
                 description=f"Generated new itinerary offering natively: {package.name}"
             )
             track_metric("package_modified", category="admin")

             return jsonify({
                 "message": "Package safely cataloged mapped natively.",
                 "package": package.to_dict()
             }), 201

        except Exception as e:
             logger.error(f"Admin pack insertion fault: {e}")
             return jsonify({"error": str(e)}), 400

class PackageCSVUploadView(MethodView):
    decorators = [admin_required]
    
    def post(self):
        """Receives a bulk CSV payload mapping rows asynchronously directly onto the Redis bus."""
        if 'file' not in request.files:
            return jsonify({"error": "Missing CSV file payload natively."}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Empty filename."}), 400
            
        if not file.filename.endswith('.csv'):
            return jsonify({"error": "Strictly limited to structurally mapped .csv schemas."}), 400
            
        # Secure the payload bounded logically into temporary OS scopes
        filename = secure_filename(file.filename)
        temp_dir = os.path.join(current_app.root_path, 'tmp')
        os.makedirs(temp_dir, exist_ok=True)
        filepath = os.path.join(temp_dir, filename)
        
        file.save(filepath)
        
        # Defer execution to Celery Fabric natively
        process_package_csv_task.delay(filepath, current_user.id)
        
        log_audit(
            action=AuditAction.CREATE,
            entity_type=EntityType.PACKAGE,
            entity_id="BULK_UPLOAD",
            user_id=current_user.id,
            description="Initiated asynchronous bulk package CSV upload dynamically."
        )
        
        return jsonify({
            "message": "CSV payload accepted securely. Processing initialized in the background fabric.",
            "status": "PROCESSING"
        }), 202
