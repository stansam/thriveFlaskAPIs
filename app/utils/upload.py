import os
import uuid
import logging
from werkzeug.utils import secure_filename
from flask import current_app
from datetime import datetime

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024 # 5MB

class UploadService:
    @staticmethod
    def allowed_file(filename):
        return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    @staticmethod
    def save_file(file, subdir='receipts'):
        """
        Saves a file to the configured upload folder.
        
        Args:
            file: FileStorage object from Flask request.
            subdir: Subdirectory to organize uploads (default: 'receipts').
            
        Returns:
            str: Relative path to the saved file.
        """
        if not file or file.filename == '':
            raise ValueError("No file provided")
            
        if not UploadService.allowed_file(file.filename):
            raise ValueError("File type not allowed. Allowed: png, jpg, jpeg, pdf")
            
        # Secure filename and add UUID to prevent collisions
        original_filename = secure_filename(file.filename)
        file_ext = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
        
        # Organize by Year/Month
        now = datetime.now()
        relative_path = os.path.join(subdir, str(now.year), f"{now.month:02d}")
        
        # Base upload folder from config or default
        base_upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        full_upload_path = os.path.join(base_upload_folder, relative_path)
        
        os.makedirs(full_upload_path, exist_ok=True)
        
        save_path = os.path.join(full_upload_path, unique_filename)
        
        try:
            file.save(save_path)
            # Return relative path for DB storage (platform independent ideally, assume POSIX for web)
            return os.path.join(relative_path, unique_filename)
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            raise IOError("File save failed")

    @staticmethod
    def get_absolute_path(relative_path):
        base_upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        return os.path.join(base_upload_folder, relative_path)
