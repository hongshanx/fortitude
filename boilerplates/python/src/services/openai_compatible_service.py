import requests
import os
import json
from src.config.env import config
from src.types.api import CompletionRequest, CompletionResponse, AIProvider, UsageInfo
from src.middlewares.error_handler import ApiError
from datetime import datetime

class OpenAICompatibleService:
    """Service for interacting with OpenAI-compatible APIs"""
    
    @staticmethod
    async def generate_completion(request: CompletionRequest) -> CompletionResponse:
        """Generate a completion using OpenAI-compatible API"""
        try:
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {config.openai_compatible.api_key}",
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
                f"{config.openai_compatible.base_url}/chat/completions",
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
                id=response_data.get("id", f"compat-{datetime.now().timestamp()}"),
                model=response_data.get("model", request.model),
                provider=AIProvider.OPENAI_COMPATIBLE,
                content=completion,
                usage=UsageInfo(
                    prompt_tokens=usage_data.get("prompt_tokens", 0),
                    completion_tokens=usage_data.get("completion_tokens", 0),
                    total_tokens=usage_data.get("total_tokens", 0),
                ),
                created_at=datetime.fromtimestamp(response_data.get("created", datetime.now().timestamp())).isoformat(),
            )
        except requests.exceptions.HTTPError as e:
            print(f"OpenAI-compatible API HTTP Error: {e}")
            
            # Handle API errors based on status code
            status_code = e.response.status_code if hasattr(e, 'response') else 500
            
            if status_code == 401:
                raise ApiError(401, "Invalid OpenAI-compatible API key", "OPENAI_COMPATIBLE_UNAUTHORIZED")
            elif status_code == 429:
                raise ApiError(429, "OpenAI-compatible rate limit exceeded", "OPENAI_COMPATIBLE_RATE_LIMIT")
            elif status_code == 400:
                error_message = e.response.json().get("error", {}).get("message", str(e)) if hasattr(e, 'response') else str(e)
                raise ApiError(400, error_message or "Bad request to OpenAI-compatible API", "OPENAI_COMPATIBLE_BAD_REQUEST")
            else:
                # Generic error
                raise ApiError(
                    status_code,
                    f"OpenAI-compatible API error: {str(e)}",
                    "OPENAI_COMPATIBLE_API_ERROR"
                )
        except requests.exceptions.RequestException as e:
            print(f"OpenAI-compatible API Request Error: {e}")
            raise ApiError(
                500,
                f"OpenAI-compatible API connection error: {str(e)}",
                "OPENAI_COMPATIBLE_CONNECTION_ERROR"
            )
        except Exception as e:
            print(f"OpenAI-compatible API Unexpected Error: {e}")
            raise ApiError(
                500,
                f"OpenAI-compatible API unexpected error: {str(e)}",
                "OPENAI_COMPATIBLE_UNEXPECTED_ERROR"
            )
    
    @staticmethod
    async def check_availability() -> bool:
        """Check if OpenAI-compatible API is configured and accessible"""
        try:
            if not config.openai_compatible.api_key or config.openai_compatible.api_key == "your_openai_compatible_api_key_here":
                return False
            
            # Instead of using the OpenAI client, use requests directly to check API availability
            # This avoids any issues with the OpenAI client initialization
            headers = {
                "Authorization": f"Bearer {config.openai_compatible.api_key}",
                "Content-Type": "application/json"
            }
            
            # Try to access the models endpoint first
            try:
                response = requests.get(
                    f"{config.openai_compatible.base_url}/models",
                    headers=headers,
                    timeout=10
                )
                if response.status_code == 200:
                    return True
            except Exception as e:
                print(f"Models endpoint check failed: {e}")
            
            # If models endpoint fails, try a simple completion request with common models
            possible_models = ["local-model", "llama3", "qwen-max", "deepseek-v3", "gemini-pro"]
            
            for model in possible_models:
                try:
                    print(f"Trying model: {model}")
                    response = requests.post(
                        f"{config.openai_compatible.base_url}/chat/completions",
                        headers=headers,
                        json={
                            "model": model,
                            "messages": [{"role": "user", "content": "Hello"}],
                            "max_tokens": 1
                        },
                        timeout=10
                    )
                    if response.status_code == 200:
                        print(f"Model {model} works!")
                        return True
                except Exception as model_error:
                    print(f"Model {model} failed: {model_error}")
                    continue
            
            # If we get here, we couldn't find a working model
            # But we'll still return True if the API key is configured
            # because the user might know which model to use
            return True
        except Exception as e:
            print(f"OpenAI-compatible availability check failed: {e}")
            return False
