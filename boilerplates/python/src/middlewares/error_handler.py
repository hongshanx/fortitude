from flask import jsonify, request
from pydantic import ValidationError
from functools import wraps
import traceback
import json
from src.config.env import config

# Custom error class
class ApiError(Exception):
    def __init__(self, status_code, message, code="INTERNAL_ERROR"):
        self.status_code = status_code
        self.message = message
        self.code = code
        super().__init__(self.message)

# Error handler function
def handle_error(error):
    """Handle different types of errors and return appropriate responses"""
    print(f"Error: {error}")
    
    # Default error
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
    response = {
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

# Not found handler
def not_found():
    """Handle 404 errors"""
    return jsonify({
        "error": {
            "message": f"Not Found - {request.path}",
            "code": "NOT_FOUND",
        }
    }), 404

# Validation middleware
def validate_request(schema_class):
    """Middleware to validate request data against a Pydantic schema"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Parse request data
                if request.is_json:
                    data = request.get_json()
                else:
                    data = {}
                
                # Validate against schema
                validated_data = schema_class(**data)
                
                # Pass validated data to the route handler
                kwargs['validated_data'] = validated_data
                return f(*args, **kwargs)
            except Exception as e:
                return handle_error(e)
        return decorated_function
    return decorator
