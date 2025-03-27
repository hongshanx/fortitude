"""Request and response schemas for API validation.

This module defines Pydantic schemas used for validating API requests and responses,
ensuring data consistency and type safety throughout the application.
"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator

from src.types.api import AIProvider, get_all_models


class CompletionRequestSchema(BaseModel):
    """Schema for completion request validation.

    Attributes:
        model: The ID of the AI model to use
        prompt: The input text to generate completion for
        max_tokens: Maximum number of tokens to generate
        temperature: Sampling temperature for generation
        provider: Specific AI provider to use
        stream: Whether to stream the response
    """

    model: str
    prompt: str = Field(..., min_length=1, max_length=32000)
    max_tokens: Optional[int] = Field(None, gt=0, le=32000)
    temperature: Optional[float] = Field(0.7, ge=0, le=2)
    provider: Optional[AIProvider] = None
    stream: Optional[bool] = False

    @field_validator('model')
    @classmethod
    def validate_model(cls, value):
        """Validate that the requested model ID exists.

        Args:
            value: The model ID to validate

        Returns:
            str: The validated model ID

        Raises:
            ValueError: If the model ID is not found in the available models
        """
        valid_model_ids = [model.id for model in get_all_models()]
        if value not in valid_model_ids:
            raise ValueError(f"Invalid model ID: {value}")
        return value


class ModelsRequestSchema(BaseModel):
    """Schema for models list request validation.

    Attributes:
        provider: Optional provider to filter models by
    """

    provider: Optional[AIProvider] = None


class StockPredictionRequestSchema(BaseModel):
    """Schema for stock prediction request validation.

    Attributes:
        ticker: The stock ticker symbol to analyze
    """

    ticker: str = Field(..., min_length=1, max_length=10, description="Stock ticker symbol")


class StockPredictionResponseSchema(BaseModel):
    """Schema for stock prediction response.

    Attributes:
        ticker: The stock ticker symbol that was analyzed
        prediction: The predicted direction (up/down)
        confidence: Confidence score between 0 and 1
        summary: Brief summary of the analysis
    """

    ticker: str
    prediction: str = Field(..., pattern="^(up|down)$")
    confidence: float = Field(..., ge=0, le=1)
    summary: str
