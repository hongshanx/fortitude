import openai
from openai import OpenAI
from src.config.env import config
from src.types.api import CompletionRequest, CompletionResponse, AIProvider, UsageInfo
from src.middlewares.error_handler import ApiError
from datetime import datetime

# Initialize OpenAI client
def get_openai_client():
    """Get a configured OpenAI client"""
    return OpenAI(
        api_key=config.openai.api_key,
        base_url=config.openai.base_url,
    )

class OpenAIService:
    """Service for interacting with OpenAI API"""
    
    @staticmethod
    async def generate_completion(request: CompletionRequest) -> CompletionResponse:
        """Generate a completion using OpenAI API"""
        try:
            # Get client
            client = get_openai_client()
            
            # Create completion request
            response = client.chat.completions.create(
                model=request.model,
                messages=[
                    {"role": "user", "content": request.prompt}
                ],
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            )

            # Extract response data
            completion = response.choices[0].message.content or ""
            
            # Return formatted response
            return CompletionResponse(
                id=response.id,
                model=response.model,
                provider=AIProvider.OPENAI,
                content=completion,
                usage=UsageInfo(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                ),
                created_at=datetime.fromtimestamp(response.created).isoformat(),
            )
        except openai.APIError as e:
            print(f"OpenAI API Error: {e}")
            
            # Handle API errors
            if e.status_code == 401:
                raise ApiError(401, "Invalid OpenAI API key", "OPENAI_UNAUTHORIZED")
            elif e.status_code == 429:
                raise ApiError(429, "OpenAI rate limit exceeded", "OPENAI_RATE_LIMIT")
            elif e.status_code == 400:
                raise ApiError(400, str(e) or "Bad request to OpenAI API", "OPENAI_BAD_REQUEST")
            
            # Generic error
            raise ApiError(
                500,
                f"OpenAI API error: {str(e)}",
                "OPENAI_API_ERROR"
            )
    
    @staticmethod
    async def check_availability() -> bool:
        """Check if OpenAI API is configured and accessible"""
        try:
            if not config.openai.api_key or config.openai.api_key == "your_openai_api_key_here":
                return False
            
            # Get client
            client = get_openai_client()
            
            # Make a simple models list request to check if API is accessible
            client.models.list()
            return True
        except Exception as e:
            print(f"OpenAI availability check failed: {e}")
            return False
