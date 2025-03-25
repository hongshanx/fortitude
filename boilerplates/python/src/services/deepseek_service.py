import requests
from src.config.env import config
from src.types.api import CompletionRequest, CompletionResponse, AIProvider, UsageInfo
from src.middlewares.error_handler import ApiError
from datetime import datetime

class DeepSeekService:
    """Service for interacting with DeepSeek API"""
    
    @staticmethod
    async def generate_completion(request: CompletionRequest) -> CompletionResponse:
        """Generate a completion using DeepSeek API"""
        try:
            # Create completion request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config.deepseek.api_key}"
            }
            
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
                provider=AIProvider.DEEPSEEK,
                content=completion,
                usage=UsageInfo(
                    prompt_tokens=data["usage"]["prompt_tokens"] if "usage" in data else 0,
                    completion_tokens=data["usage"]["completion_tokens"] if "usage" in data else 0,
                    total_tokens=data["usage"]["total_tokens"] if "usage" in data else 0,
                ),
                created_at=datetime.now().isoformat(),
            )
        except requests.exceptions.RequestException as e:
            print(f"DeepSeek API Error: {e}")
            
            # Handle API errors
            if e.response:
                status = e.response.status_code
                try:
                    data = e.response.json()
                except:
                    data = {}
                
                if status == 401:
                    raise ApiError(401, "Invalid DeepSeek API key", "DEEPSEEK_UNAUTHORIZED")
                elif status == 429:
                    raise ApiError(429, "DeepSeek rate limit exceeded", "DEEPSEEK_RATE_LIMIT")
                elif status == 400:
                    error_message = data.get("error", {}).get("message", "Bad request to DeepSeek API")
                    raise ApiError(400, error_message, "DEEPSEEK_BAD_REQUEST")
            
            # Generic error
            raise ApiError(
                500,
                f"DeepSeek API error: {str(e)}",
                "DEEPSEEK_API_ERROR"
            )
    
    @staticmethod
    async def check_availability() -> bool:
        """Check if DeepSeek API is configured and accessible"""
        try:
            if not config.deepseek.api_key or config.deepseek.api_key == "your_deepseek_api_key_here":
                return False
            
            # Make a simple models list request to check if API is accessible
            headers = {
                "Authorization": f"Bearer {config.deepseek.api_key}"
            }
            
            response = requests.get(f"{config.deepseek.base_url}/models", headers=headers)
            response.raise_for_status()
            
            return True
        except Exception as e:
            print(f"DeepSeek availability check failed: {e}")
            return False
