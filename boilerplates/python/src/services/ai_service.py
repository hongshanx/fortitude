from typing import Dict, List, Any, AsyncGenerator
import src.types.api as api_types
from src.types.api import (
    CompletionRequest, 
    CompletionResponse, 
    AIProvider, 
    update_litellm_models,
    StreamChunk
)
from src.middlewares.error_handler import ApiError
from src.services.openai_service import OpenAIService
from src.services.deepseek_service import DeepSeekService
from src.services.litellm_service import LiteLLMService
from src.services.openai_compatible_service import OpenAICompatibleService

class AIService:
    """Service for coordinating AI providers"""
    
    @staticmethod
    async def generate_stream(request: CompletionRequest) -> AsyncGenerator[StreamChunk, None]:
        """Generate a streaming completion using the appropriate service based on the model"""
        # Find the model in our list
        model_info = next((m for m in api_types.ALL_MODELS if m.id == request.model), None)
        
        if not model_info:
            raise ApiError(400, f"Model '{request.model}' not found", "MODEL_NOT_FOUND")
        
        # If provider is specified, ensure it matches the model's provider
        if request.provider and request.provider != model_info.provider:
            raise ApiError(
                400,
                f"Model '{request.model}' belongs to provider '{model_info.provider}', not '{request.provider}'",
                "PROVIDER_MODEL_MISMATCH"
            )
        
        # Route to the appropriate service
        if model_info.provider == AIProvider.OPENAI:
            async for chunk in OpenAIService.generate_stream(request):
                yield chunk
        elif model_info.provider == AIProvider.OPENAI_COMPATIBLE:
            async for chunk in OpenAICompatibleService.generate_stream(request):
                yield chunk
        else:
            # For providers that don't support streaming yet, simulate streaming with the regular completion
            try:
                if model_info.provider == AIProvider.DEEPSEEK:
                    response = await DeepSeekService.generate_completion(request)
                elif model_info.provider == AIProvider.LITELLM:
                    response = await LiteLLMService.generate_completion(request)
                else:
                    raise ApiError(500, f"Unsupported provider: {model_info.provider}", "UNSUPPORTED_PROVIDER")
                
                # Yield the content as a single chunk
                yield StreamChunk(
                    id=response.id,
                    model=response.model,
                    provider=response.provider,
                    content=response.content,
                    created_at=response.created_at,
                    finish_reason="stop",
                    is_last_chunk=True
                )
            except Exception as e:
                # Re-raise any exceptions
                raise e
    
    @staticmethod
    async def generate_completion(request: CompletionRequest) -> CompletionResponse:
        """Generate a completion using the appropriate service based on the model"""
        # Find the model in our list
        model_info = next((m for m in api_types.ALL_MODELS if m.id == request.model), None)
        print("model_info", model_info)
        print("ALL_MODELS", api_types.ALL_MODELS)
        # Use model ID directly without mapping
        
        if not model_info:
            raise ApiError(400, f"Model '{request.model}' not found", "MODEL_NOT_FOUND")
        
        # If provider is specified, ensure it matches the model's provider
        if request.provider and request.provider != model_info.provider:
            raise ApiError(
                400,
                f"Model '{request.model}' belongs to provider '{model_info.provider}', not '{request.provider}'",
                "PROVIDER_MODEL_MISMATCH"
            )
        
        # Route to the appropriate service
        if model_info.provider == AIProvider.OPENAI:
            return await OpenAIService.generate_completion(request)
        elif model_info.provider == AIProvider.DEEPSEEK:
            return await DeepSeekService.generate_completion(request)
        elif model_info.provider == AIProvider.LITELLM:
            return await LiteLLMService.generate_completion(request)
        elif model_info.provider == AIProvider.OPENAI_COMPATIBLE:
            return await OpenAICompatibleService.generate_completion(request)
        else:
            raise ApiError(500, f"Unsupported provider: {model_info.provider}", "UNSUPPORTED_PROVIDER")
    
    @staticmethod
    async def get_available_providers() -> Dict[str, bool]:
        """Check which AI providers are available"""
        # Check all providers' availability
        openai_available = await OpenAIService.check_availability()
        deepseek_available = await DeepSeekService.check_availability()
        litellm_available = await LiteLLMService.check_availability()
        openai_compatible_available = await OpenAICompatibleService.check_availability()
        
        # If LiteLLM is available, fetch and update models
        if litellm_available:
            try:
                litellm_models = await LiteLLMService.get_models()
                update_litellm_models(litellm_models)
            except Exception as e:
                print(f"Failed to fetch LiteLLM models: {e}")
                # Continue with empty models list
        
        return {
            "openai": openai_available,
            "deepseek": deepseek_available,
            "litellm": litellm_available,
            "openai_compatible": openai_compatible_available,
        }
