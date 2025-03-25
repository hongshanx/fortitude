import requests
import os
import json
from src.config.env import config
from src.types.api import CompletionRequest, CompletionResponse, AIProvider, UsageInfo
from src.middlewares.error_handler import ApiError
from datetime import datetime

class OpenAIService:
    """Service for interacting with OpenAI API"""
    
    @staticmethod
    async def generate_completion(request: CompletionRequest) -> CompletionResponse:
        """Generate a completion using OpenAI API"""
        try:
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {config.openai.api_key}",
                "Content-Type": "application/json"
            }
            
            # Prepare request payload
            payload = {
                "model": request.model,
                "messages": [
                    {"role": "user", "content": request.prompt}
                ],
                "temperature": request.temperature,
            }
            
            # Add max_tokens if specified
            if request.max_tokens:
                payload["max_tokens"] = request.max_tokens
            
            # Make the API request
            response = requests.post(
                f"{config.openai.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60  # Longer timeout for completions
            )
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse the response
            response_data = response.json()
            
            # Extract response data
            completion = response_data["choices"][0]["message"]["content"] if response_data.get("choices") else ""
            
            # Extract usage information
            usage_data = response_data.get("usage", {})
            
            # Return formatted response
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
                created_at=datetime.fromtimestamp(response_data.get("created", datetime.now().timestamp())).isoformat(),
            )
        except requests.exceptions.HTTPError as e:
            print(f"OpenAI API HTTP Error: {e}")
            
            # Handle API errors based on status code
            status_code = e.response.status_code if hasattr(e, 'response') else 500
            
            if status_code == 401:
                raise ApiError(401, "Invalid OpenAI API key", "OPENAI_UNAUTHORIZED")
            elif status_code == 429:
                raise ApiError(429, "OpenAI rate limit exceeded", "OPENAI_RATE_LIMIT")
            elif status_code == 400:
                error_message = e.response.json().get("error", {}).get("message", str(e)) if hasattr(e, 'response') else str(e)
                raise ApiError(400, error_message or "Bad request to OpenAI API", "OPENAI_BAD_REQUEST")
            else:
                # Generic error
                raise ApiError(
                    status_code,
                    f"OpenAI API error: {str(e)}",
                    "OPENAI_API_ERROR"
                )
        except requests.exceptions.RequestException as e:
            print(f"OpenAI API Request Error: {e}")
            raise ApiError(
                500,
                f"OpenAI API connection error: {str(e)}",
                "OPENAI_CONNECTION_ERROR"
            )
        except Exception as e:
            print(f"OpenAI API Unexpected Error: {e}")
            raise ApiError(
                500,
                f"OpenAI API unexpected error: {str(e)}",
                "OPENAI_UNEXPECTED_ERROR"
            )
    
    @staticmethod
    async def check_availability() -> bool:
        """Check if OpenAI API is configured and accessible"""
        try:
            if not config.openai.api_key or config.openai.api_key == "your_openai_api_key_here":
                return False
            
            # Use requests directly to check API availability
            headers = {
                "Authorization": f"Bearer {config.openai.api_key}",
                "Content-Type": "application/json"
            }
            
            # Try to access the models endpoint
            response = requests.get(
                f"{config.openai.base_url}/models",
                headers=headers,
                timeout=10
            )
            
            # Check if the request was successful
            return response.status_code == 200
        except Exception as e:
            print(f"OpenAI availability check failed: {e}")
            return False
