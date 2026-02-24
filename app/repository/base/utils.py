import functools
import logging
from typing import Callable, Any
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db

logger = logging.getLogger(__name__)

def handle_db_exceptions(func: Callable) -> Callable:
    """
    Decorator to safely catch SQLAlchemy database exceptions, trigger automated
    rollbacks to prevent stalled transactions, and securely log the trace context.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except SQLAlchemyError as e:
            logger.error(f"Database error in {func.__name__}: {str(e)}")
            db.session.rollback()
            # Depending on business rules, we could raise a custom application
            # exception here. For now, we cleanly raise the Database error.
            raise
    return wrapper
