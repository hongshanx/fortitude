from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from src.types.api import AIProvider, get_all_models

# Completion request schema
class CompletionRequestSchema(BaseModel):
    model: str
    prompt: str = Field(..., min_length=1, max_length=32000)
    max_tokens: Optional[int] = Field(None, gt=0, le=32000)
    temperature: Optional[float] = Field(0.7, ge=0, le=2)
    provider: Optional[AIProvider] = None
    
    @field_validator('model')
    @classmethod
    def validate_model(cls, value):
        # Get the current list of valid model IDs at validation time
        valid_model_ids = [model.id for model in get_all_models()]
        if value not in valid_model_ids:
            raise ValueError(f"Invalid model ID: {value}")
        return value

# Models list request schema
class ModelsRequestSchema(BaseModel):
    provider: Optional[AIProvider] = None
