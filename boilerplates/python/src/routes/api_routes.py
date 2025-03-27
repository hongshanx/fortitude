"""API route handlers for the AI service.

This module defines the Flask Blueprint containing all API endpoints
for model management, completions, and health checks.
"""

import asyncio
import datetime
import json
from typing import Generator, List, Optional, Tuple, Union

from asgiref.sync import async_to_sync
from flask import Blueprint, Response, jsonify, request, stream_with_context

from src.middlewares.error_handler import ApiError, handle_error, validate_request
from src.services.ai_service import AIService
from src.types.api import (
    AIModel,
    AIProvider,
    DEEPSEEK_MODELS,
    LITELLM_MODELS,
    OPENAI_COMPATIBLE_MODELS,
    OPENAI_MODELS,
    get_all_models,
)
from src.types.schemas import CompletionRequestSchema

# Create blueprint
api_bp = Blueprint('api', __name__)


@api_bp.route('/models', methods=['GET'])
def get_models() -> Tuple[dict, int]:
    """Get list of available models.

    Returns:
        Tuple[dict, int]: JSON response with models and providers, and HTTP status code.
    """
    # Parse and validate query parameters
    provider_param = request.args.get('provider')
    provider: Optional[AIProvider] = None

    if provider_param:
        try:
            provider = AIProvider(provider_param)
        except ValueError:
            return jsonify({
                "error": {
                    "message": f"Invalid provider: {provider_param}",
                    "code": "INVALID_PROVIDER"
                }
            }), 400

    try:
        # Get available providers
        providers = async_to_sync(AIService.get_available_providers)()

        # Get the latest models including any dynamically fetched ones
        models = get_all_models()

        # Filter by provider if specified
        if provider:
            models = [model for model in models if model.provider == provider]

        # Filter out models from unavailable providers
        models = [
            model for model in models
            if ((model.provider != AIProvider.OPENAI or providers["openai"]) and
                (model.provider != AIProvider.DEEPSEEK or providers["deepseek"]) and
                (model.provider != AIProvider.LITELLM or providers["litellm"]) and
                (model.provider != AIProvider.OPENAI_COMPATIBLE or
                 providers["openai_compatible"]))
        ]

        # Convert models to dict for JSON response
        models_json = [model.model_dump() for model in models]

        return jsonify({
            "models": models_json,
            "providers": providers,
        }), 200

    except (KeyError, ValueError) as e:
        return handle_error(
            ApiError(400, str(e), "INVALID_REQUEST")
        )
    except (ConnectionError, TimeoutError) as e:
        return handle_error(
            ApiError(503, f"Service unavailable: {str(e)}", "SERVICE_UNAVAILABLE")
        )
    except (TypeError, AttributeError) as e:
        return handle_error(
            ApiError(500, f"Internal server error: {str(e)}", "SERVER_ERROR")
        )


@api_bp.route('/providers', methods=['GET'])
def get_providers() -> Tuple[dict, int]:
    """Get available AI providers.

    Returns:
        Tuple[dict, int]: JSON response with provider information and HTTP status code.
    """
    def get_provider_models(
        models: List[AIModel],
        is_available: bool
    ) -> List[dict]:
        """Helper to get models for a provider if available."""
        if not is_available:
            return []
        return [model.model_dump() for model in models]

    try:
        providers = async_to_sync(AIService.get_available_providers)()

        return jsonify({
            "providers": {
                "openai": {
                    "available": providers["openai"],
                    "models": get_provider_models(
                        OPENAI_MODELS,
                        providers["openai"]
                    ),
                },
                "deepseek": {
                    "available": providers["deepseek"],
                    "models": get_provider_models(
                        DEEPSEEK_MODELS,
                        providers["deepseek"]
                    ),
                },
                "litellm": {
                    "available": providers["litellm"],
                    "models": get_provider_models(
                        LITELLM_MODELS,
                        providers["litellm"]
                    ),
                },
                "openai_compatible": {
                    "available": providers["openai_compatible"],
                    "models": get_provider_models(
                        OPENAI_COMPATIBLE_MODELS,
                        providers["openai_compatible"]
                    ),
                },
            },
        }), 200

    except KeyError as e:
        return handle_error(
            ApiError(500, f"Missing provider configuration: {e}", "PROVIDER_ERROR")
        )
    except (ConnectionError, TimeoutError) as e:
        return handle_error(
            ApiError(503, f"Service unavailable: {str(e)}", "SERVICE_UNAVAILABLE")
        )
    except (TypeError, AttributeError) as e:
        return handle_error(
            ApiError(500, f"Internal server error: {str(e)}", "SERVER_ERROR")
        )


CompletionResponse = Union[Response, Tuple[dict, int]]


@api_bp.route('/completions', methods=['POST'])
@validate_request(CompletionRequestSchema)
def generate_completion(validated_data: CompletionRequestSchema) -> CompletionResponse:
    """Generate a completion.

    Args:
        validated_data: Validated completion request data.

    Returns:
        CompletionResponse: Streaming response or JSON response with completion.
    """
    try:
        if validated_data.stream:
            return stream_completion(validated_data)

        result = async_to_sync(AIService.generate_completion)(validated_data)
        return jsonify(result.model_dump()), 200

    except (ConnectionError, TimeoutError) as e:
        return handle_error(
            ApiError(503, f"Service unavailable: {str(e)}", "SERVICE_UNAVAILABLE")
        )
    except ValueError as e:
        return handle_error(
            ApiError(400, str(e), "INVALID_REQUEST")
        )
    except (KeyError, TypeError) as e:
        return handle_error(
            ApiError(400, f"Invalid request format: {str(e)}", "INVALID_FORMAT")
        )
    except (RuntimeError, AssertionError) as e:
        print(f"Internal error in generate_completion: {e}")
        return handle_error(
            ApiError(500, "Internal server error", "SERVER_ERROR")
        )


def stream_completion(validated_data: CompletionRequestSchema) -> Response:
    """Stream a completion response.

    Args:
        validated_data: Validated completion request data.

    Returns:
        Response: Streaming response with Server-Sent Events.
    """
    def generate() -> Generator[str, None, None]:
        """Generate SSE formatted chunks.

        Yields:
            str: SSE formatted data chunks.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            async_gen = AIService.generate_stream(validated_data)

            while True:
                try:
                    chunk = loop.run_until_complete(async_gen.__anext__())
                    chunk_data = chunk.model_dump()
                    yield f"data: {json.dumps(chunk_data)}\n\n"

                except StopAsyncIteration:
                    break
                except (ConnectionError, TimeoutError) as e:
                    error_data = {
                        "error": {
                            "message": f"Service unavailable: {str(e)}",
                            "code": "SERVICE_UNAVAILABLE"
                        }
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    break
                except json.JSONDecodeError as e:
                    print(f"JSON encoding error in stream_completion: {e}")
                    error_data = {
                        "error": {
                            "message": "Failed to encode response",
                            "code": "ENCODING_ERROR"
                        }
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    break
                except (KeyError, TypeError) as e:
                    error_data = {
                        "error": {
                            "message": f"Invalid response format: {str(e)}",
                            "code": "INVALID_RESPONSE"
                        }
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    break
                except ValueError as e:
                    error_data = {
                        "error": {
                            "message": f"Invalid data in response: {str(e)}",
                            "code": "INVALID_DATA"
                        }
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    break
                except (AttributeError, RuntimeError, AssertionError) as e:
                    print(f"Internal error in stream_completion: {e}")
                    error_data = {
                        "error": {
                            "message": "Internal server error",
                            "code": "SERVER_ERROR"
                        }
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    break

            yield "data: [DONE]\n\n"

        finally:
            loop.close()

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'  # Disable buffering in Nginx
        }
    )


@api_bp.route('/health', methods=['GET'])
def health_check() -> Tuple[dict, int]:
    """Health check endpoint.

    Returns:
        Tuple[dict, int]: JSON response with health status and HTTP status code.
    """
    try:
        providers = async_to_sync(AIService.get_available_providers)()

        return jsonify({
            "status": "ok",
            "timestamp": datetime.datetime.now().isoformat(),
            "providers": providers,
        }), 200

    except (ConnectionError, TimeoutError) as e:
        return handle_error(
            ApiError(503, f"Service unavailable: {str(e)}", "SERVICE_UNAVAILABLE")
        )
    except (KeyError, ValueError) as e:
        return handle_error(
            ApiError(500, f"Invalid provider configuration: {str(e)}", "CONFIG_ERROR")
        )
    except (TypeError, AttributeError) as e:
        return handle_error(
            ApiError(500, f"Internal server error: {str(e)}", "SERVER_ERROR")
        )
