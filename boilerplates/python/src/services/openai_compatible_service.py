"""OpenAI-compatible API service implementation.

This module provides a service class for interacting with OpenAI-compatible APIs,
such as local LLM servers or third-party services that implement the OpenAI API
specification. It handles streaming and non-streaming completions with proper
error handling and response formatting.
"""

import json
from datetime import datetime
from typing import AsyncGenerator

import requests

from src.config.env import config
from src.middlewares.error_handler import ApiError
from src.types.api import (
    AIProvider,
    CompletionRequest,
    CompletionResponse,
    StreamChunk,
    UsageInfo,
)


class OpenAICompatibleService:
    """Service for interacting with OpenAI-compatible APIs."""

    REQUEST_TIMEOUT = 60  # seconds
    CHECK_TIMEOUT = 10  # seconds
    COMMON_MODELS = [
        "local-model",
        "llama3",
        "qwen-max",
        "deepseek-v3",
        "gemini-pro"
    ]

    @staticmethod
    def _handle_api_error(e: requests.exceptions.RequestException, prefix: str = "") -> None:
        """Handle API errors with consistent error messages.

        Args:
            e: The request exception to handle
            prefix: Optional prefix for error messages

        Raises:
            ApiError: With appropriate status code and message
        """
        if not hasattr(e, 'response'):
            raise ApiError(
                500,
                f"{prefix}connection error: {str(e)}",
                "OPENAI_COMPATIBLE_CONNECTION_ERROR"
            ) from e

        status = e.response.status_code
        try:
            data = e.response.json()
        except requests.exceptions.JSONDecodeError:
            data = {}

        error_message = data.get("error", {}).get("message", str(e))

        if status == 401:
            raise ApiError(401, f"{prefix}invalid API key",
                         "OPENAI_COMPATIBLE_UNAUTHORIZED") from e
        if status == 429:
            raise ApiError(429, f"{prefix}rate limit exceeded",
                         "OPENAI_COMPATIBLE_RATE_LIMIT") from e
        if status == 400:
            raise ApiError(400, error_message or f"{prefix}bad request",
                         "OPENAI_COMPATIBLE_BAD_REQUEST") from e

        raise ApiError(status, f"{prefix}API error: {str(e)}",
                      "OPENAI_COMPATIBLE_API_ERROR") from e

    @staticmethod
    async def generate_stream(request: CompletionRequest) -> AsyncGenerator[StreamChunk, None]:
        """Generate a streaming completion using OpenAI-compatible API.

        Args:
            request: The completion request parameters.

        Yields:
            StreamChunk: Chunks of the generated completion.

        Raises:
            ApiError: If any error occurs during API communication.
        """
        try:
            headers = {
                "Authorization": f"Bearer {config.openai_compatible.api_key}",
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            }

            payload = {
                "model": request.model,
                "messages": [
                    {"role": "user", "content": request.prompt}
                ],
                "temperature": request.temperature,
                "stream": True
            }

            if request.max_tokens:
                payload["max_tokens"] = request.max_tokens

            response = requests.post(
                f"{config.openai_compatible.base_url}/chat/completions",
                headers=headers,
                json=payload,
                stream=True,
                timeout=OpenAICompatibleService.REQUEST_TIMEOUT
            )

            response.raise_for_status()

            chunk_id = f"compat-{datetime.now().timestamp()}"
            model = request.model
            accumulated_content = ""

            for line in response.iter_lines():
                if not line:
                    continue

                if line.startswith(b"data: "):
                    line = line[6:]

                if line.strip() == b"[DONE]":
                    yield StreamChunk(
                        id=chunk_id,
                        model=model,
                        provider=AIProvider.OPENAI_COMPATIBLE,
                        content=accumulated_content,
                        created_at=datetime.now().isoformat(),
                        finish_reason="stop",
                        is_last_chunk=True
                    )
                    break

                try:
                    data = json.loads(line)

                    if "id" in data:
                        chunk_id = data["id"]
                    if "model" in data:
                        model = data["model"]

                    delta = data.get("choices", [{}])[0].get("delta", {})
                    content_delta = delta.get("content", "")

                    if content_delta:
                        accumulated_content += content_delta
                        yield StreamChunk(
                            id=chunk_id,
                            model=model,
                            provider=AIProvider.OPENAI_COMPATIBLE,
                            content=content_delta,
                            created_at=datetime.now().isoformat(),
                            finish_reason=None,
                            is_last_chunk=False
                        )

                    finish_reason = data.get("choices", [{}])[0].get("finish_reason")
                    if finish_reason:
                        yield StreamChunk(
                            id=chunk_id,
                            model=model,
                            provider=AIProvider.OPENAI_COMPATIBLE,
                            content="",
                            created_at=datetime.now().isoformat(),
                            finish_reason=finish_reason,
                            is_last_chunk=True
                        )
                        break

                except json.JSONDecodeError:
                    print(f"Failed to parse JSON: {line}")
                    continue

        except requests.exceptions.RequestException as e:
            print(f"OpenAI-compatible API Error: {e}")
            OpenAICompatibleService._handle_api_error(e, "OpenAI-compatible ")

    @staticmethod
    async def generate_completion(request: CompletionRequest) -> CompletionResponse:
        """Generate a completion using OpenAI-compatible API.

        Args:
            request: The completion request parameters.

        Returns:
            CompletionResponse: The generated completion.

        Raises:
            ApiError: If any error occurs during API communication.
        """
        try:
            headers = {
                "Authorization": f"Bearer {config.openai_compatible.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": request.model,
                "messages": [
                    {"role": "user", "content": request.prompt}
                ],
                "temperature": request.temperature,
            }

            if request.max_tokens:
                payload["max_tokens"] = request.max_tokens

            response = requests.post(
                f"{config.openai_compatible.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=OpenAICompatibleService.REQUEST_TIMEOUT
            )

            response.raise_for_status()
            response_data = response.json()

            completion = (response_data["choices"][0]["message"]["content"]
                        if response_data.get("choices") else "")
            usage_data = response_data.get("usage", {})

            return CompletionResponse(
                id=response_data.get("id", f"compat-{datetime.now().timestamp()}"),
                model=response_data.get("model", request.model),
                provider=AIProvider.OPENAI_COMPATIBLE,
                content=completion,
                usage=UsageInfo(
                    prompt_tokens=usage_data.get("prompt_tokens", 0),
                    completion_tokens=usage_data.get("completion_tokens", 0),
                    total_tokens=usage_data.get("total_tokens", 0),
                ),
                created_at=datetime.fromtimestamp(
                    response_data.get("created", datetime.now().timestamp())
                ).isoformat(),
            )

        except requests.exceptions.RequestException as e:
            print(f"OpenAI-compatible API Error: {e}")
            OpenAICompatibleService._handle_api_error(e, "OpenAI-compatible ")

    @staticmethod
    async def check_availability() -> bool:
        """Check if OpenAI-compatible API is configured and accessible.

        Returns:
            bool: True if the API is available and properly configured, False otherwise.
        """
        if (not config.openai_compatible.api_key or
                config.openai_compatible.api_key == "your_openai_compatible_api_key_here"):
            return False

        headers = {
            "Authorization": f"Bearer {config.openai_compatible.api_key}",
            "Content-Type": "application/json"
        }

        try:
            # Try models endpoint first
            response = requests.get(
                f"{config.openai_compatible.base_url}/models",
                headers=headers,
                timeout=OpenAICompatibleService.CHECK_TIMEOUT
            )
            if response.status_code == 200:
                return True

        except requests.exceptions.RequestException:
            pass

        # Try each model until one works
        for model in OpenAICompatibleService.COMMON_MODELS:
            try:
                response = requests.post(
                    f"{config.openai_compatible.base_url}/chat/completions",
                    headers=headers,
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": "Hello"}],
                        "max_tokens": 1
                    },
                    timeout=OpenAICompatibleService.CHECK_TIMEOUT
                )
                if response.status_code == 200:
                    return True
            except requests.exceptions.RequestException:
                continue

        # Return True if API key is configured, as user might know the correct model
        return True
