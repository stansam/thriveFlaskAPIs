from app import create_app
from app.core.celery import celery_init_app
import app.tasks.emails
import app.tasks.package

app = create_app()
celery = celery_init_app(app)
