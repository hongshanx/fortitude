from enum import Enum
from typing import List, Dict, Optional, Union
from pydantic import BaseModel, Field

# Provider types
class AIProvider(str, Enum):
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    LITELLM = "litellm"
    OPENAI_COMPATIBLE = "openai_compatible"

# Model types
class AIModel(BaseModel):
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

# LiteLLM models will be populated dynamically from the API
LITELLM_MODELS: List[AIModel] = []

# OpenAI-compatible models - default examples, will be customizable
OPENAI_COMPATIBLE_MODELS: List[AIModel] = [
    AIModel(
        id='llama3.3-70b-instruct',
        name='Llama 3',
        provider='openai_compatible',
        description="Meta's Llama 3 model via OpenAI-compatible API",
        maxTokens=30000,
    ),
    AIModel(
        id='deepseek-v3',
        name='DeepSeek-V3',
        provider='openai_compatible',
        description='DeepSeek V3 model via OpenAI-compatible API',
        maxTokens=57344,
    ),
    AIModel(
        id='qwen-max',
        name='通义千问-Max',
        provider='openai_compatible',
        description='通义千问-Max model via OpenAI-compatible API',
        maxTokens=30720,
    ),
]

# Function to get all models
def get_all_models() -> List[AIModel]:
    return OPENAI_MODELS + DEEPSEEK_MODELS + LITELLM_MODELS + OPENAI_COMPATIBLE_MODELS

# All available models
ALL_MODELS: List[AIModel] = get_all_models()

# Function to update LiteLLM models
def update_litellm_models(models: List[AIModel]) -> None:
    global LITELLM_MODELS, ALL_MODELS
    LITELLM_MODELS = models if models else []
    print("LITELLM_MODELS", LITELLM_MODELS)
    ALL_MODELS = get_all_models()
    print("ALL_MODELS2", ALL_MODELS)

# Request types
class CompletionRequest(BaseModel):
    model: str
    prompt: str
    max_tokens: Optional[int] = None
    temperature: Optional[float] = 0.7
    provider: Optional[AIProvider] = None

# Usage information
class UsageInfo(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

# Response types
class CompletionResponse(BaseModel):
    id: str
    model: str
    provider: AIProvider
    content: str
    usage: UsageInfo
    created_at: str

# Error response
class ErrorDetail(BaseModel):
    message: str
    code: Optional[str] = None
    type: Optional[str] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail
