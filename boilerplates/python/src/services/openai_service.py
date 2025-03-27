# pylint: disable=duplicate-code
"""OpenAI API service implementation."""

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


class OpenAIService:
    """Service for interacting with OpenAI API."""

    @staticmethod
    def _handle_http_error(e: requests.exceptions.HTTPError) -> None:
        """Handle HTTP errors from OpenAI API.

        Args:
            e: The HTTP error from the request.

        Raises:
            ApiError: A formatted API error with appropriate status code and message.
        """
        print(f"OpenAI API HTTP Error: {e}")
        status_code = e.response.status_code if hasattr(e, 'response') else 500

        if status_code == 401:
            raise ApiError(401, "Invalid OpenAI API key", "OPENAI_UNAUTHORIZED") from e
        if status_code == 429:
            raise ApiError(429, "OpenAI rate limit exceeded", "OPENAI_RATE_LIMIT") from e
        if status_code == 400:
            error_message = (e.response.json().get("error", {}).get("message", str(e))
                           if hasattr(e, 'response') else str(e))
            raise ApiError(400, error_message or "Bad request to OpenAI API",
                         "OPENAI_BAD_REQUEST") from e
        raise ApiError(status_code, f"OpenAI API error: {str(e)}", "OPENAI_API_ERROR") from e

    @staticmethod
    def _create_stream_chunk(
        chunk_id: str,
        model: str,
        content: str,
        finish_reason: str | None = None,
        is_last_chunk: bool = False
    ) -> StreamChunk:
        """Create a StreamChunk object with common parameters.

        Args:
            chunk_id: The ID of the chunk.
            model: The model name.
            content: The content of the chunk.
            finish_reason: The reason for finishing, if any.
            is_last_chunk: Whether this is the last chunk.

        Returns:
            StreamChunk: A formatted stream chunk.
        """
        return StreamChunk(
            id=chunk_id,
            model=model,
            provider=AIProvider.OPENAI,
            content=content,
            created_at=datetime.now().isoformat(),
            finish_reason=finish_reason,
            is_last_chunk=is_last_chunk
        )

    @staticmethod
    def _get_request_headers(stream: bool = False) -> dict:
        """Get headers for OpenAI API request.

        Args:
            stream: Whether this is a streaming request.

        Returns:
            dict: Headers for the request.
        """
        headers = {
            "Authorization": f"Bearer {config.openai.api_key}",
            "Content-Type": "application/json"
        }
        if stream:
            headers["Accept"] = "text/event-stream"
        return headers

    @staticmethod
    def _create_request_payload(request: CompletionRequest, stream: bool = False) -> dict:
        """Create payload for OpenAI API request.

        Args:
            request: The completion request parameters.
            stream: Whether this is a streaming request.

        Returns:
            dict: Request payload.
        """
        payload = {
            "model": request.model,
            "messages": [
                {"role": "user", "content": request.prompt}
            ],
            "temperature": request.temperature
        }
        if stream:
            payload["stream"] = True
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens
        return payload

    @staticmethod
    async def generate_stream(request: CompletionRequest) -> AsyncGenerator[StreamChunk, None]:
        """Generate a streaming completion using OpenAI API.

        Args:
            request: The completion request parameters.

        Returns:
            AsyncGenerator yielding StreamChunk objects.

        Raises:
            ApiError: If any error occurs during API communication.
        """
        try:
            headers = OpenAIService._get_request_headers(stream=True)
            payload = OpenAIService._create_request_payload(request, stream=True)

            response = requests.post(
                f"{config.openai.base_url}/chat/completions",
                headers=headers,
                json=payload,
                stream=True,
                timeout=60  # Longer timeout for completions
            )

            response.raise_for_status()

            chunk_id = f"chatcmpl-{datetime.now().timestamp()}"
            model = request.model
            accumulated_content = ""

            for line in response.iter_lines():
                if not line:
                    continue

                if line.startswith(b"data: "):
                    line = line[6:]

                if line.strip() == b"[DONE]":
                    yield OpenAIService._create_stream_chunk(
                        chunk_id, model, accumulated_content,
                        finish_reason="stop", is_last_chunk=True
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
                        yield OpenAIService._create_stream_chunk(
                            chunk_id, model, content_delta
                        )

                    finish_reason = data.get("choices", [{}])[0].get("finish_reason")
                    if finish_reason:
                        yield OpenAIService._create_stream_chunk(
                            chunk_id, model, "",
                            finish_reason=finish_reason, is_last_chunk=True
                        )
                        break

                except json.JSONDecodeError:
                    print(f"Failed to parse JSON: {line}")
                    continue

        except requests.exceptions.HTTPError as e:
            OpenAIService._handle_http_error(e)
        except requests.exceptions.RequestException as e:
            print(f"OpenAI API Request Error: {e}")
            raise ApiError(500, f"OpenAI API connection error: {str(e)}",
                         "OPENAI_CONNECTION_ERROR") from e
        except Exception as e:
            print(f"OpenAI API Unexpected Error: {e}")
            raise ApiError(500, f"OpenAI API unexpected error: {str(e)}",
                         "OPENAI_UNEXPECTED_ERROR") from e

    @staticmethod
    async def generate_completion(request: CompletionRequest) -> CompletionResponse:
        """Generate a completion using OpenAI API.

        Args:
            request: The completion request parameters.

        Returns:
            CompletionResponse: The generated completion response.

        Raises:
            ApiError: If any error occurs during API communication.
        """
        try:
            headers = OpenAIService._get_request_headers()
            payload = OpenAIService._create_request_payload(request)

            response = requests.post(
                f"{config.openai.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60  # Longer timeout for completions
            )

            response.raise_for_status()
            response_data = response.json()

            completion = (response_data["choices"][0]["message"]["content"]
                        if response_data.get("choices") else "")
            usage_data = response_data.get("usage", {})

            return CompletionResponse(
                id=response_data.get("id", f"openai-{datetime.now().timestamp()}"),
                model=response_data.get("model", request.model),
                provider=AIProvider.OPENAI,
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

        except requests.exceptions.HTTPError as e:
            OpenAIService._handle_http_error(e)
        except requests.exceptions.RequestException as e:
            print(f"OpenAI API Request Error: {e}")
            raise ApiError(500, f"OpenAI API connection error: {str(e)}",
                         "OPENAI_CONNECTION_ERROR") from e
        except (KeyError, ValueError, TypeError) as e:
            print(f"OpenAI API Response Error: {e}")
            raise ApiError(500, f"Invalid response from OpenAI API: {str(e)}",
                         "OPENAI_RESPONSE_ERROR") from e
        except Exception as e:
            print(f"OpenAI API Unexpected Error: {e}")
            raise ApiError(500, f"OpenAI API unexpected error: {str(e)}",
                         "OPENAI_UNEXPECTED_ERROR") from e

    @staticmethod
    async def check_availability() -> bool:
        """Check if OpenAI API is configured and accessible.

        Returns:
            bool: True if the API is available and properly configured, False otherwise.
        """
        if not config.openai.api_key or config.openai.api_key == "your_openai_api_key_here":
            return False

        try:
            headers = OpenAIService._get_request_headers()
            response = requests.get(
                f"{config.openai.base_url}/models",
                headers=headers,
                timeout=10
            )
            return response.status_code == 200

        except requests.exceptions.RequestException as e:
            print(f"OpenAI API connection error during availability check: {e}")
            return False
        except (ValueError, TypeError) as e:
            print(f"OpenAI API configuration error: {e}")
            return False
        except (AttributeError, KeyError) as e:
            print(f"OpenAI API response error: {e}")
            return False
