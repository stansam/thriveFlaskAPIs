from flask import jsonify
from typing import Any, Dict, Optional, List, Union
import math

def success_response(
    data: Any = None,
    message: Optional[str] = None,
    status: int = 200
) -> tuple[Any, int]:
    response = {
        'success': True,
        'data': data
    }
    
    if message:
        response['message'] = message
        
    return jsonify(response), status


def error_response(
    message: str,
    errors: Optional[Dict[str, List[str]]] = None,
    status: int = 400
) -> tuple[Any, int]:
    response = {
        'success': False,
        'message': message
    }
    
    if errors:
        response['errors'] = errors
        
    return jsonify(response), status


def validation_error_response(errors: Union[dict[str, Any], list[Any]]) -> tuple[Any, int]:
    normalized: dict[str, Any] = (
        errors if isinstance(errors, dict) else {"_errors": errors}
    )
    return error_response(
        message='Validation failed',
        errors=normalized,
        status=422
    )


def paginated_response(
    items: list[Any],
    page: int,
    per_page: int,
    total: int,
    message: Optional[str] = None
) -> tuple[Any, int]:
    total_pages = math.ceil(total / per_page) if per_page > 0 else 0
    
    response = {
        'success': True,
        'data': items,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    }
    
    if message:
        response['message'] = message
        
    return jsonify(response), 200


def created_response(data: Any, message: str = 'Resource created successfully') -> tuple[Any, int]:
    return success_response(data, message, 201)


def no_content_response() -> tuple[str, int]:
    return '', 204


def unauthorized_response(message: str = 'Unauthorized') -> tuple[Any, int]:
    return error_response(message, status=401)


def forbidden_response(message: str = 'Forbidden') -> tuple[Any, int]:
    return error_response(message, status=403)


def not_found_response(message: str = 'Resource not found') -> tuple[Any, int]:
    return error_response(message, status=404)


def conflict_response(message: str = 'Resource already exists.') -> tuple[Any, int]:
    return error_response(message, status=409)


def paginated_response_from_page(
    page_obj: Any,
    serialized_items: list[Any],
    message: Optional[str] = None,
) -> tuple[Any, int]:
    """Build a paginated response directly from a repository Page or typed result object."""
    return paginated_response(
        items=serialized_items,
        page=page_obj.page,
        per_page=page_obj.per_page,
        total=page_obj.total,
        message=message,
    )
