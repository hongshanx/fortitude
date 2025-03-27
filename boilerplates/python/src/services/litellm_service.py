# pylint: disable=duplicate-code
"""LiteLLM API service implementation.

This module provides a service class for interacting with the LiteLLM API,
handling completions, model listing, and API availability checks with proper
error handling and response formatting.
"""

from datetime import datetime
from typing import List

import requests

from src.config.env import config
from src.middlewares.error_handler import ApiError
from src.types.api import (
    AIModel,
    AIProvider,
    CompletionRequest,
    CompletionResponse,
    UsageInfo,
)


class LiteLLMService:
    """Service for interacting with LiteLLM API."""

    REQUEST_TIMEOUT = 60  # seconds
    MODEL_TIMEOUT = 10  # seconds

    @staticmethod
    async def generate_completion(request: CompletionRequest) -> CompletionResponse:
        """Generate a completion using LiteLLM API.

        Args:
            request: The completion request parameters.

        Returns:
            CompletionResponse: The generated completion response.

        Raises:
            ApiError: If any error occurs during API communication.
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config.litellm.api_key}"
            }

            model_id = request.model

            payload = {
                "model": model_id,
                "messages": [
                    {"role": "user", "content": request.prompt}
                ],
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
            }

            response = requests.post(
                f"{config.litellm.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=LiteLLMService.REQUEST_TIMEOUT
            )

            response.raise_for_status()
            data = response.json()

            completion = data["choices"][0]["message"]["content"] if data["choices"] else ""

            return CompletionResponse(
                id=data["id"],
                model=data["model"],
                provider=AIProvider.LITELLM,
                content=completion,
                usage=UsageInfo(
                    prompt_tokens=data["usage"]["prompt_tokens"] if "usage" in data else 0,
                    completion_tokens=data["usage"]["completion_tokens"] if "usage" in data else 0,
                    total_tokens=data["usage"]["total_tokens"] if "usage" in data else 0,
                ),
                created_at=datetime.now().isoformat(),
            )

        except requests.exceptions.RequestException as e:
            print(f"LiteLLM API Error: {e}")

            if not hasattr(e, 'response'):
                raise ApiError(
                    500,
                    f"LiteLLM API connection error: {str(e)}",
                    "LITELLM_CONNECTION_ERROR"
                ) from e

            status = e.response.status_code
            try:
                data = e.response.json()
            except requests.exceptions.JSONDecodeError:
                data = {}

            error_message = data.get("error", {}).get("message", "Bad request to LiteLLM API")

            if status == 401:
                raise ApiError(401, "Invalid LiteLLM API key",
                             "LITELLM_UNAUTHORIZED") from e
            if status == 429:
                raise ApiError(429, "LiteLLM rate limit exceeded",
                             "LITELLM_RATE_LIMIT") from e
            if status == 400:
                raise ApiError(400, error_message, "LITELLM_BAD_REQUEST") from e

            raise ApiError(status, f"LiteLLM API error: {str(e)}",
                         "LITELLM_API_ERROR") from e

    @staticmethod
    async def get_models() -> List[AIModel]:
        """Get available models from LiteLLM API.

        Returns:
            List[AIModel]: List of available AI models.

        Raises:
            ApiError: If any error occurs during API communication.
        """
        try:
            if not config.litellm.api_key or config.litellm.api_key == "your_litellm_api_key_here":
                return []

            headers = {
                "Authorization": f"Bearer {config.litellm.api_key}"
            }

            response = requests.get(
                f"{config.litellm.base_url}/models",
                headers=headers,
                timeout=LiteLLMService.MODEL_TIMEOUT
            )
            response.raise_for_status()

            data = response.json()
            models = data.get("data", [])

            return [
                AIModel(
                    id=model["id"],
                    name=" ".join(word.capitalize() for word in model["id"].split("-")),
                    provider=AIProvider.LITELLM,
                    description=f"{model.get('owned_by', 'Unknown')} model",
                    max_tokens=100000,  # Default value as the API doesn't provide this
                )
                for model in models
            ]

        except requests.exceptions.RequestException as e:
            print(f"LiteLLM models fetch failed: {e}")
            return []

    @staticmethod
    async def check_availability() -> bool:
        """Check if LiteLLM API is configured and accessible.

        Returns:
            bool: True if the API is available and properly configured, False otherwise.
        """
        try:
            if not config.litellm.api_key or config.litellm.api_key == "your_litellm_api_key_here":
                return False

            headers = {
                "Authorization": f"Bearer {config.litellm.api_key}"
            }

            response = requests.get(
                f"{config.litellm.base_url}/models",
                headers=headers,
                timeout=LiteLLMService.MODEL_TIMEOUT
            )
            response.raise_for_status()

            data = response.json()
            return data and isinstance(data.get("data"), list)

        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"LiteLLM availability check failed: {e}")
            return False
