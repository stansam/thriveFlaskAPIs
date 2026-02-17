from app import create_app
from app.utils.celery_utils import celery_init_app

app = create_app()
celery = celery_init_app(app)
