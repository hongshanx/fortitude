"""API types and models for the AI service.

This module defines the core data structures and types used throughout the API,
including models, providers, requests, and responses.
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class AIProvider(str, Enum):
    """Supported AI service providers."""

    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    LITELLM = "litellm"
    OPENAI_COMPATIBLE = "openai_compatible"


class AIModel(BaseModel):
    """AI model configuration and metadata."""

    id: str
    name: str
    provider: AIProvider
    description: Optional[str] = None
    max_tokens: Optional[int] = None


# OpenAI models
OPENAI_MODELS: List[AIModel] = [
    AIModel(
        id="gpt-4o",
        name="GPT-4o",
        provider=AIProvider.OPENAI,
        description="Most capable model for complex tasks",
        max_tokens=128000,
    ),
    AIModel(
        id="gpt-4-turbo",
        name="GPT-4 Turbo",
        provider=AIProvider.OPENAI,
        description="Optimized version of GPT-4",
        max_tokens=128000,
    ),
    AIModel(
        id="gpt-3.5-turbo",
        name="GPT-3.5 Turbo",
        provider=AIProvider.OPENAI,
        description="Fast and efficient for most tasks",
        max_tokens=16385,
    ),
]

# DeepSeek models
DEEPSEEK_MODELS: List[AIModel] = [
    AIModel(
        id="deepseek-chat",
        name="DeepSeek Chat",
        provider=AIProvider.DEEPSEEK,
        description="General purpose chat model",
        max_tokens=32768,
    ),
    AIModel(
        id="deepseek-coder",
        name="DeepSeek Coder",
        provider=AIProvider.DEEPSEEK,
        description="Specialized for coding tasks",
        max_tokens=32768,
    ),
]

class ModelRegistry:
    """Registry for managing AI models from different providers."""

    def __init__(self):
        """Initialize the model registry with default models."""
        self._litellm_models: List[AIModel] = []
        self._openai_compatible_models: List[AIModel] = [
            AIModel(
                id='llama3.3-70b-instruct',
                name='Llama 3',
                provider=AIProvider.OPENAI_COMPATIBLE,
                description="Meta's Llama 3 model via OpenAI-compatible API",
                max_tokens=30000,
            ),
            AIModel(
                id='deepseek-v3',
                name='DeepSeek-V3',
                provider=AIProvider.OPENAI_COMPATIBLE,
                description='DeepSeek V3 model via OpenAI-compatible API',
                max_tokens=57344,
            ),
            AIModel(
                id='qwen-max',
                name='通义千问-Max',
                provider=AIProvider.OPENAI_COMPATIBLE,
                description='通义千问-Max model via OpenAI-compatible API',
                max_tokens=30720,
            ),
        ]

    def _get_all_models(self) -> List[AIModel]:
        """Get a list of all available AI models.

        Returns:
            List[AIModel]: Combined list of models from all providers.
        """
        return (
            OPENAI_MODELS +
            DEEPSEEK_MODELS +
            self._litellm_models +
            self._openai_compatible_models
        )

    @property
    def all_models(self) -> List[AIModel]:
        """Get all available models.

        Returns:
            List[AIModel]: All registered models.
        """
        return self._get_all_models()

    @property
    def litellm_models(self) -> List[AIModel]:
        """Get LiteLLM models.

        Returns:
            List[AIModel]: Registered LiteLLM models.
        """
        return self._litellm_models

    @property
    def openai_compatible_models(self) -> List[AIModel]:
        """Get OpenAI-compatible models.

        Returns:
            List[AIModel]: Registered OpenAI-compatible models.
        """
        return self._openai_compatible_models

    def update_litellm_models(self, models: List[AIModel]) -> None:
        """Update the list of available LiteLLM models.

        Args:
            models: List of AIModel objects representing available LiteLLM models.
        """
        self._litellm_models = models if models else []


# Initialize the model registry
model_registry = ModelRegistry()


def get_litellm_models() -> List[AIModel]:
    """Get the current list of LiteLLM models.

    Returns:
        List[AIModel]: Current list of LiteLLM models.
    """
    return model_registry.litellm_models


def get_openai_compatible_models() -> List[AIModel]:
    """Get the current list of OpenAI-compatible models.

    Returns:
        List[AIModel]: Current list of OpenAI-compatible models.
    """
    return model_registry.openai_compatible_models


def get_all_models() -> List[AIModel]:
    """Get a list of all available AI models.

    Returns:
        List[AIModel]: Combined list of models from all providers.
    """
    return model_registry.all_models


def update_litellm_models(models: List[AIModel]) -> None:
    """Update the list of available LiteLLM models.

    Args:
        models: List of AIModel objects representing available LiteLLM models.
    """
    model_registry.update_litellm_models(models)


class CompletionRequest(BaseModel):
    """Request parameters for generating completions."""

    model: str
    prompt: str
    max_tokens: Optional[int] = None
    temperature: Optional[float] = 0.7
    provider: Optional[AIProvider] = None
    stream: Optional[bool] = False


class UsageInfo(BaseModel):
    """Token usage information for API requests."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class CompletionResponse(BaseModel):
    """Response format for completion requests."""

    id: str
    model: str
    provider: AIProvider
    content: str
    usage: UsageInfo
    created_at: str


class StreamChunk(BaseModel):
    """Individual chunk in a streaming response."""

    id: str
    model: str
    provider: AIProvider
    content: str
    created_at: str
    finish_reason: Optional[str] = None
    is_last_chunk: bool = False


class ErrorDetail(BaseModel):
    """Detailed error information."""

    message: str
    code: Optional[str] = None
    type: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response format."""

    error: ErrorDetail
