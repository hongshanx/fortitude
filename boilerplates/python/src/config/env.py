import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator
from typing import Literal

# Load environment variables from .env file
load_dotenv()

class ServerConfig(BaseModel):
    port: int = Field(default=3000)
    flask_env: Literal["development", "production", "testing"] = Field(default="development")
    
    @property
    def is_dev(self) -> bool:
        return self.flask_env == "development"
    
    @property
    def is_prod(self) -> bool:
        return self.flask_env == "production"
    
    @property
    def is_test(self) -> bool:
        return self.flask_env == "testing"

class ProviderConfig(BaseModel):
    api_key: str
    base_url: str

class Config(BaseModel):
    server: ServerConfig
    openai: ProviderConfig
    deepseek: ProviderConfig
    litellm: ProviderConfig
    openai_compatible: ProviderConfig

# Load and validate environment variables
def load_config() -> Config:
    try:
        server_config = ServerConfig(
            port=int(os.getenv("PORT", "3000")),
            flask_env=os.getenv("FLASK_ENV", "development")
        )
        
        openai_config = ProviderConfig(
            api_key=os.getenv("OPENAI_API_KEY", "your_openai_api_key_here"),
            base_url=os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
        )
        
        deepseek_config = ProviderConfig(
            api_key=os.getenv("DEEPSEEK_API_KEY", "your_deepseek_api_key_here"),
            base_url=os.getenv("DEEPSEEK_API_BASE_URL", "https://api.deepseek.com/v1")
        )
        
        litellm_config = ProviderConfig(
            api_key=os.getenv("LITELLM_API_KEY", "your_litellm_api_key_here"),
            base_url=os.getenv("LITELLM_API_BASE_URL", "http://localhost:4000")
        )
        
        openai_compatible_config = ProviderConfig(
            api_key=os.getenv("OPENAI_COMPATIBLE_API_KEY", "your_openai_compatible_api_key_here"),
            base_url=os.getenv("OPENAI_COMPATIBLE_API_BASE_URL", "http://localhost:8000/v1")
        )
        
        return Config(
            server=server_config,
            openai=openai_config,
            deepseek=deepseek_config,
            litellm=litellm_config,
            openai_compatible=openai_compatible_config
        )
    except Exception as e:
        print(f"❌ Invalid environment variables: {str(e)}")
        raise ValueError("Invalid environment variables")

# Export validated environment variables
config = load_config()
