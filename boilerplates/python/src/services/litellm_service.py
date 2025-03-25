import requests
from typing import List, Dict
from src.config.env import config
from src.types.api import CompletionRequest, CompletionResponse, AIProvider, UsageInfo, AIModel
from src.middlewares.error_handler import ApiError
from datetime import datetime

class LiteLLMService:
    """Service for interacting with LiteLLM API"""
    
    @staticmethod
    async def generate_completion(request: CompletionRequest) -> CompletionResponse:
        """Generate a completion using LiteLLM API"""
        try:
            # Create completion request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config.litellm.api_key}"
            }
            
            # Use model ID directly
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
                json=payload
            )
            
            # Check for errors
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # Extract response data
            completion = data["choices"][0]["message"]["content"] if data["choices"] else ""
            
            # Return formatted response
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
            
            # Handle API errors
            if e.response:
                status = e.response.status_code
                try:
                    data = e.response.json()
                except:
                    data = {}
                
                if status == 401:
                    raise ApiError(401, "Invalid LiteLLM API key", "LITELLM_UNAUTHORIZED")
                elif status == 429:
                    raise ApiError(429, "LiteLLM rate limit exceeded", "LITELLM_RATE_LIMIT")
                elif status == 400:
                    error_message = data.get("error", {}).get("message", "Bad request to LiteLLM API")
                    raise ApiError(400, error_message, "LITELLM_BAD_REQUEST")
            
            # Generic error
            raise ApiError(
                500,
                f"LiteLLM API error: {str(e)}",
                "LITELLM_API_ERROR"
            )
    
    @staticmethod
    async def get_models() -> List[AIModel]:
        """Get available models from LiteLLM API"""
        try:
            if not config.litellm.api_key or config.litellm.api_key == "your_litellm_api_key_here":
                return []
            
            headers = {
                "Authorization": f"Bearer {config.litellm.api_key}"
            }
            
            response = requests.get(f"{config.litellm.base_url}/models", headers=headers)
            response.raise_for_status()
            
            data = response.json()
            models = data.get("data", [])
            
            # Transform API response to AIModel format
            result_models = []
            for model in models:
                model_id = model["id"]
                # Use the original model ID for display purposes
                result_models.append(
                    AIModel(
                        id=model_id,
                        name=" ".join(word.capitalize() for word in model_id.split("-")),
                        provider=AIProvider.LITELLM,
                        description=f"{model.get('owned_by', 'Unknown')} model",
                        max_tokens=100000,  # Default value as the API doesn't provide this information
                    )
                )
            print(result_models)                
            return result_models
        except Exception as e:
            print(f"LiteLLM models fetch failed: {e}")
            return []
    
    @staticmethod
    async def check_availability() -> bool:
        """Check if LiteLLM API is configured and accessible"""
        try:
            if not config.litellm.api_key or config.litellm.api_key == "your_litellm_api_key_here":
                return False
            
            # Make a simple models list request to check if API is accessible
            headers = {
                "Authorization": f"Bearer {config.litellm.api_key}"
            }
            
            response = requests.get(f"{config.litellm.base_url}/models", headers=headers)
            response.raise_for_status()
            
            data = response.json()
            return data and isinstance(data.get("data"), list)
        except Exception as e:
            print(f"LiteLLM availability check failed: {e}")
            return False
