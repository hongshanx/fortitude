"""AI Service coordination module.

This module provides a central service for coordinating between different AI providers.
It handles routing requests to the appropriate service based on the requested model,
manages streaming and non-streaming completions, and checks provider availability.
"""

from typing import AsyncGenerator, Dict

from src.middlewares.error_handler import ApiError
from src.services.deepseek_service import DeepSeekService
from src.services.litellm_service import LiteLLMService
from src.services.openai_compatible_service import OpenAICompatibleService
from src.services.openai_service import OpenAIService
from src.types.api import (
    AIProvider,
    CompletionRequest,
    CompletionResponse,
    StreamChunk,
    ALL_MODELS,
    update_litellm_models,
)


class AIService:
    """Service for coordinating between different AI providers."""

    @staticmethod
    def _validate_model_request(request: CompletionRequest):
        """Validate model request and return model info.

        Args:
            request: The completion request parameters.

        Returns:
            The model info if valid.

        Raises:
            ApiError: If the model is not found or provider mismatch occurs.
        """
        model_info = next((m for m in ALL_MODELS if m.id == request.model), None)

        if not model_info:
            raise ApiError(400, f"Model '{request.model}' not found", "MODEL_NOT_FOUND")

        if request.provider and request.provider != model_info.provider:
            raise ApiError(
                400,
                f"Model '{request.model}' belongs to provider '{model_info.provider}', "
                f"not '{request.provider}'",
                "PROVIDER_MODEL_MISMATCH"
            )

        return model_info

    @staticmethod
    async def generate_stream(request: CompletionRequest) -> AsyncGenerator[StreamChunk, None]:
        """Generate a streaming completion using the appropriate service.

        Args:
            request: The completion request parameters.

        Returns:
            AsyncGenerator[StreamChunk, None]: Stream of response chunks.

        Raises:
            ApiError: If the model is not found or provider mismatch occurs.
        """
        model_info = AIService._validate_model_request(request)

        try:
            if model_info.provider == AIProvider.OPENAI:
                async for chunk in OpenAIService.generate_stream(request):
                    yield chunk
            elif model_info.provider == AIProvider.OPENAI_COMPATIBLE:
                async for chunk in OpenAICompatibleService.generate_stream(request):
                    yield chunk
            else:
                # For providers that don't support streaming, simulate with regular completion
                response = await {
                    AIProvider.DEEPSEEK: DeepSeekService.generate_completion,
                    AIProvider.LITELLM: LiteLLMService.generate_completion,
                }[model_info.provider](request)

                yield StreamChunk(
                    id=response.id,
                    model=response.model,
                    provider=response.provider,
                    content=response.content,
                    created_at=response.created_at,
                    finish_reason="stop",
                    is_last_chunk=True
                )
        except KeyError as e:
            raise ApiError(500, f"Unsupported provider: {model_info.provider}",
                         "UNSUPPORTED_PROVIDER") from e

    @staticmethod
    async def generate_completion(request: CompletionRequest) -> CompletionResponse:
        """Generate a completion using the appropriate service.

        Args:
            request: The completion request parameters.

        Returns:
            CompletionResponse: The generated completion.

        Raises:
            ApiError: If the model is not found or provider mismatch occurs.
        """
        model_info = AIService._validate_model_request(request)

        try:
            return await {
                AIProvider.OPENAI: OpenAIService.generate_completion,
                AIProvider.DEEPSEEK: DeepSeekService.generate_completion,
                AIProvider.LITELLM: LiteLLMService.generate_completion,
                AIProvider.OPENAI_COMPATIBLE: OpenAICompatibleService.generate_completion,
            }[model_info.provider](request)
        except KeyError as e:
            raise ApiError(500, f"Unsupported provider: {model_info.provider}",
                         "UNSUPPORTED_PROVIDER") from e

    @staticmethod
    async def get_available_providers() -> Dict[str, bool]:
        """Check which AI providers are available.

        Returns:
            Dict[str, bool]: Dictionary mapping provider names to availability status.
        """
        openai_available = await OpenAIService.check_availability()
        deepseek_available = await DeepSeekService.check_availability()
        litellm_available = await LiteLLMService.check_availability()
        openai_compatible_available = await OpenAICompatibleService.check_availability()

        if litellm_available:
            try:
                litellm_models = await LiteLLMService.get_models()
                update_litellm_models(litellm_models)
            except (ConnectionError, TimeoutError) as e:
                print(f"Failed to fetch LiteLLM models due to connection error: {e}")
            except (ValueError, TypeError) as e:
                print(f"Invalid response from LiteLLM API: {e}")
            except (KeyError, AttributeError) as e:
                print(f"Missing or invalid data in LiteLLM response: {e}")
            except (ImportError, ModuleNotFoundError) as e:
                print(f"LiteLLM module error: {e}")

        return {
            "openai": openai_available,
            "deepseek": deepseek_available,
            "litellm": litellm_available,
            "openai_compatible": openai_compatible_available,
        }
