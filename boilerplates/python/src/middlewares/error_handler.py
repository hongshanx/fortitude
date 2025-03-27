# pylint: disable=too-many-return-statements
"""Error handling middleware and utilities.

This module provides error handling functionality for the API, including:
- Custom API error class
- Error handling middleware
- Request validation decorator
- 404 error handler
"""

import json
import traceback
from functools import wraps
from typing import Any, Callable, Dict, Tuple, TypeVar, cast

from flask import jsonify, request
from pydantic import ValidationError

from src.config.env import config

F = TypeVar('F', bound=Callable[..., Any])


class ApiError(Exception):
    """Custom API error class with status code and error code."""

    def __init__(self, status_code: int, message: str, code: str = "INTERNAL_ERROR") -> None:
        """Initialize API error.

        Args:
            status_code: HTTP status code
            message: Error message
            code: Error code for API clients
        """
        self.status_code = status_code
        self.message = message
        self.code = code
        super().__init__(self.message)


def handle_error(error: Exception) -> Tuple[dict, int]:
    """Handle different types of errors and return appropriate responses.

    Args:
        error: The exception to handle

    Returns:
        Tuple[dict, int]: Error response and HTTP status code
    """
    print(f"Error: {error}")

    # Default error values
    status_code = 500
    message = "Internal Server Error"
    error_code = "INTERNAL_ERROR"
    details = None

    # Handle specific error types
    if isinstance(error, ApiError):
        status_code = error.status_code
        message = error.message
        error_code = error.code
    elif isinstance(error, ValidationError):
        status_code = 400
        message = "Validation Error"
        error_code = "VALIDATION_ERROR"
        details = error.errors()
    elif isinstance(error, json.JSONDecodeError):
        status_code = 400
        message = "Invalid JSON"
        error_code = "INVALID_JSON"

    # Create error response
    response: Dict[str, Any] = {
        "error": {
            "message": message,
            "code": error_code,
        }
    }

    # Add details for validation errors
    if details:
        response["error"]["details"] = details

    # Add stack trace in development mode
    if config.server.is_dev:
        response["error"]["stack"] = traceback.format_exc()

    return jsonify(response), status_code


def not_found() -> Tuple[dict, int]:
    """Handle 404 errors.

    Returns:
        Tuple[dict, int]: Error response and 404 status code
    """
    return jsonify({
        "error": {
            "message": f"Not Found - {request.path}",
            "code": "NOT_FOUND",
        }
    }), 404


def validate_request(schema_class: Any) -> Callable[[F], F]:
    """Middleware to validate request data against a Pydantic schema.

    Args:
        schema_class: Pydantic model class to validate against

    Returns:
        Callable: Decorated function that includes validation
    """
    def decorator(f: F) -> F:
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            try:
                # Parse request data
                data = request.get_json() if request.is_json else {}

                # Validate against schema
                validated_data = schema_class(**data)

                # Pass validated data to the route handler
                kwargs['validated_data'] = validated_data
                return f(*args, **kwargs)
            except json.JSONDecodeError as e:
                return handle_error(e)
            except ValidationError as e:
                return handle_error(e)
            except (TypeError, ValueError) as e:
                return handle_error(ApiError(400, str(e), "VALIDATION_ERROR"))
            except AttributeError as e:
                return handle_error(
                    ApiError(400, f"Invalid request format: {str(e)}", "INVALID_FORMAT")
                )
            except KeyError as e:
                return handle_error(
                    ApiError(400, f"Missing required field: {str(e)}", "MISSING_FIELD")
                )
            except (ImportError, ModuleNotFoundError) as e:
                return handle_error(
                    ApiError(500, f"Schema validation error: {str(e)}", "SCHEMA_ERROR")
                )
            except (RuntimeError, AssertionError) as e:
                print(f"Unexpected validation error: {e}")
                return handle_error(
                    ApiError(500, "Internal validation error", "VALIDATION_SYSTEM_ERROR")
                )

        return cast(F, decorated_function)
    return decorator
