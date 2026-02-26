from app import create_app
from app.utils.celery_utils import celery_init_app
import app.tasks.email_tasks # Initialize physical backgrounds bounds securely
import app.tasks.package_tasks

app = create_app()
celery = celery_init_app(app)
