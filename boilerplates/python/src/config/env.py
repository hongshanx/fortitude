"""Environment configuration module for the application.

This module handles loading and validating environment variables using Pydantic models.
It provides type-safe configuration objects for different parts of the application.
"""

import os
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from .env file
load_dotenv()


class ServerConfig(BaseModel):
    """Server configuration settings."""

    port: int = Field(default=3000)
    flask_env: Literal["development", "production", "testing"] = Field(default="development")

    @property
    def is_dev(self) -> bool:
        """Check if the environment is development.

        Returns:
            bool: True if in development environment.
        """
        return self.flask_env == "development"

    @property
    def is_prod(self) -> bool:
        """Check if the environment is production.

        Returns:
            bool: True if in production environment.
        """
        return self.flask_env == "production"

    @property
    def is_test(self) -> bool:
        """Check if the environment is testing.

        Returns:
            bool: True if in testing environment.
        """
        return self.flask_env == "testing"


class ProviderConfig(BaseModel):
    """API provider configuration settings."""

    api_key: str
    base_url: str


class Config(BaseModel):
    """Main configuration class combining all config sections."""

    server: ServerConfig
    openai: ProviderConfig
    deepseek: ProviderConfig
    litellm: ProviderConfig
    openai_compatible: ProviderConfig


def load_config() -> Config:
    """Load and validate environment variables.

    Returns:
        Config: Validated configuration object.

    Raises:
        ValueError: If environment variables are invalid or missing.
    """
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
        raise ValueError("Invalid environment variables") from e


# Export validated environment variables
config = load_config()
