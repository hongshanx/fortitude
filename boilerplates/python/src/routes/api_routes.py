from flask import Blueprint, request, jsonify, Response, stream_with_context
from asgiref.sync import async_to_sync
from src.services.ai_service import AIService
from src.middlewares.error_handler import validate_request, handle_error
from src.types.schemas import CompletionRequestSchema, ModelsRequestSchema
import src.types.api as api_types
from src.types.api import (
    AIProvider
)
import json
import asyncio

# Create blueprint
api_bp = Blueprint('api', __name__)

@api_bp.route('/models', methods=['GET'])
def get_models():
    """Get list of available models"""
    try:
        # Parse and validate query parameters
        provider = request.args.get('provider')
        if provider:
            try:
                provider = AIProvider(provider)
            except ValueError:
                return jsonify({
                    "error": {
                        "message": f"Invalid provider: {provider}",
                        "code": "INVALID_PROVIDER"
                    }
                }), 400
        
        # Get available providers
        providers = async_to_sync(AIService.get_available_providers)()
        
        # Get the latest models including any dynamically fetched ones
        models = api_types.get_all_models()
        
        # Filter by provider if specified
        if provider:
            models = [model for model in models if model.provider == provider]
        
        # Filter out models from unavailable providers
        models = [model for model in models if (
            (model.provider != AIProvider.OPENAI or providers["openai"]) and
            (model.provider != AIProvider.DEEPSEEK or providers["deepseek"]) and
            (model.provider != AIProvider.LITELLM or providers["litellm"]) and
            (model.provider != AIProvider.OPENAI_COMPATIBLE or providers["openai_compatible"])
        )]
        
        # Convert models to dict for JSON response
        models_json = [model.model_dump() for model in models]
        
        return jsonify({
            "models": models_json,
            "providers": providers,
        })
    except Exception as e:
        return handle_error(e)

@api_bp.route('/providers', methods=['GET'])
def get_providers():
    """Get available AI providers"""
    try:
        providers = async_to_sync(AIService.get_available_providers)()
        
        return jsonify({
            "providers": {
                "openai": {
                    "available": providers["openai"],
                    "models": [model.model_dump() for model in api_types.OPENAI_MODELS] if providers["openai"] else [],
                },
                "deepseek": {
                    "available": providers["deepseek"],
                    "models": [model.model_dump() for model in api_types.DEEPSEEK_MODELS] if providers["deepseek"] else [],
                },
                "litellm": {
                    "available": providers["litellm"],
                    "models": [model.model_dump() for model in api_types.LITELLM_MODELS] if providers["litellm"] else [],
                },
                "openai_compatible": {
                    "available": providers["openai_compatible"],
                    "models": [model.model_dump() for model in api_types.OPENAI_COMPATIBLE_MODELS] if providers["openai_compatible"] else [],
                },
            },
        })
    except Exception as e:
        return handle_error(e)

@api_bp.route('/completions', methods=['POST'])
@validate_request(CompletionRequestSchema)
def generate_completion(validated_data):
    """Generate a completion"""
    try:
        # Check if streaming is requested
        if validated_data.stream:
            return stream_completion(validated_data)
        
        # Regular non-streaming completion
        result = async_to_sync(AIService.generate_completion)(validated_data)
        return jsonify(result.model_dump())
    except Exception as e:
        return handle_error(e)

def stream_completion(validated_data):
    """Stream a completion response"""
    
    def generate():
        """Generator function that yields SSE formatted chunks"""
        # Create a new event loop for this request
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Get the async generator
            async_gen = AIService.generate_stream(validated_data)
            
            # Process chunks one by one
            while True:
                try:
                    # Get the next chunk (run the coroutine in the event loop)
                    chunk = loop.run_until_complete(async_gen.__anext__())
                    
                    # Format the chunk as a Server-Sent Event
                    chunk_data = chunk.model_dump()
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                    
                except StopAsyncIteration:
                    # End of the stream
                    break
                except Exception as e:
                    # Handle errors in the stream
                    error_data = {
                        "error": {
                            "message": str(e),
                            "code": getattr(e, "code", "STREAM_ERROR") if hasattr(e, "code") else "STREAM_ERROR"
                        }
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    break
            
            # End the stream
            yield "data: [DONE]\n\n"
            
        finally:
            # Clean up the event loop
            loop.close()
    
    # Create a streaming response
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
def health_check():
    """Health check endpoint"""
    try:
        providers = async_to_sync(AIService.get_available_providers)()
        
        return jsonify({
            "status": "ok",
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "providers": providers,
        })
    except Exception as e:
        return handle_error(e)
