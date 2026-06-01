from typing import cast, TYPE_CHECKING
from flask import current_app, has_app_context

if TYPE_CHECKING:
    from app.interface import _ServiceRegistry

def get_services() -> "_ServiceRegistry":
    # services = cast(Services, current_app.extensions.get('services'))
    if not has_app_context():
        raise RuntimeError("No Flask application context found.")
    services = current_app.extensions.get('services')
    if services is None:
        raise RuntimeError("Services not initialized. Was create_app() called?")
    return cast("_ServiceRegistry", services)