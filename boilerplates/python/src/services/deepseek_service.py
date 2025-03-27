# pylint: disable=duplicate-code
"""DeepSeek API service implementation.

This module provides a service class for interacting with the DeepSeek API,
handling completions and API availability checks with proper error handling
and response formatting.
"""

from datetime import datetime
from typing import Any, Dict

import requests

from src.config.env import config
from src.middlewares.error_handler import ApiError
from src.types.api import AIProvider, CompletionRequest, CompletionResponse, UsageInfo


class DeepSeekService:
    """Service for interacting with DeepSeek API."""

    REQUEST_TIMEOUT = 60  # seconds

    @staticmethod
    def _get_headers() -> Dict[str, str]:
        """Get headers for DeepSeek API request.

        Returns:
            Dict[str, str]: Headers for the request.
        """
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.deepseek.api_key}"
        }

    @staticmethod
    def _handle_api_error(e: requests.exceptions.RequestException) -> None:
        """Handle API errors from DeepSeek API.

        Args:
            e: The request exception.

        Raises:
            ApiError: A formatted API error with appropriate status code and message.
        """
        print(f"DeepSeek API Error: {e}")

        if not hasattr(e, 'response'):
            raise ApiError(
                500,
                f"DeepSeek API connection error: {str(e)}",
                "DEEPSEEK_CONNECTION_ERROR"
            ) from e

        status = e.response.status_code
        try:
            data = e.response.json()
        except requests.exceptions.JSONDecodeError:
            data = {}

        error_message = data.get("error", {}).get(
            "message", "Bad request to DeepSeek API"
        )

        if status == 401:
            raise ApiError(
                401,
                "Invalid DeepSeek API key",
                "DEEPSEEK_UNAUTHORIZED"
            ) from e
        if status == 429:
            raise ApiError(
                429,
                "DeepSeek rate limit exceeded",
                "DEEPSEEK_RATE_LIMIT"
            ) from e
        if status == 400:
            raise ApiError(
                400,
                error_message,
                "DEEPSEEK_BAD_REQUEST"
            ) from e

        raise ApiError(
            status,
            f"DeepSeek API error: {str(e)}",
            "DEEPSEEK_API_ERROR"
        ) from e

    @staticmethod
    def _create_usage_info(data: Dict[str, Any]) -> UsageInfo:
        """Create usage info from response data.

        Args:
            data: Response data from the API.

        Returns:
            UsageInfo: Formatted usage information.
        """
        usage_data = data.get("usage", {})
        return UsageInfo(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        )

    @staticmethod
    async def generate_completion(request: CompletionRequest) -> CompletionResponse:
        """Generate a completion using DeepSeek API.

        Args:
            request: The completion request parameters.

        Returns:
            CompletionResponse: The generated completion response.

        Raises:
            ApiError: If any error occurs during API communication.
        """
        try:
            headers = DeepSeekService._get_headers()
            payload = {
                "model": request.model,
                "messages": [
                    {"role": "user", "content": request.prompt}
                ],
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
            }

            response = requests.post(
                f"{config.deepseek.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=DeepSeekService.REQUEST_TIMEOUT
            )

            response.raise_for_status()
            data = response.json()

            completion = (data["choices"][0]["message"]["content"]
                        if data["choices"] else "")

            return CompletionResponse(
                id=data["id"],
                model=data["model"],
                provider=AIProvider.DEEPSEEK,
                content=completion,
                usage=DeepSeekService._create_usage_info(data),
                created_at=datetime.now().isoformat(),
            )

        except requests.exceptions.RequestException as e:
            DeepSeekService._handle_api_error(e)

    @staticmethod
    async def check_availability() -> bool:
        """Check if DeepSeek API is configured and accessible.

        Returns:
            bool: True if the API is available and properly configured, False otherwise.
        """
        if (not config.deepseek.api_key or
                config.deepseek.api_key == "your_deepseek_api_key_here"):
            return False

        try:
            headers = DeepSeekService._get_headers()
            response = requests.get(
                f"{config.deepseek.base_url}/models",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return True

        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"DeepSeek availability check failed: {e}")
            return False
