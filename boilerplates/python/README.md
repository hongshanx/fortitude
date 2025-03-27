# AI API Server (Python)

A Python Flask API server that connects to OpenAI, DeepSeek, and LiteLLM AI models, allowing users to select models and customize prompts to get AI-generated responses.

## Features

- Connect to multiple AI providers (OpenAI, DeepSeek, LiteLLM, and OpenAI-compatible)
- Select from various AI models
- Customize prompts and parameters
- Support for streaming responses
- RESTful API with proper error handling
- Type validation with Pydantic
- Built with Flask and asyncio

## Tech Stack

- Python 3.9+
- Flask
- Flask-CORS
- Pydantic for validation
- OpenAI SDK
- Requests for API calls
- Python-dotenv for environment variables

## Prerequisites

- Python 3.9+ installed
- OpenAI API key (optional)
- DeepSeek API key (optional)
- LiteLLM API key (optional)

## Installation

1. Clone the repository
2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Copy the example environment file and configure your API keys:

```bash
cp .env.example .env
```

5. Edit the `.env` file and add your API keys:

```
OPENAI_API_KEY=your_openai_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
LITELLM_API_KEY=your_litellm_api_key_here
LITELLM_API_BASE_URL=http://localhost:4000
```

## Development

Start the development server:

```bash
python main.py
```

The server will run at http://localhost:3000 by default.

## Code Quality

### Running Pylint

Check code quality with pylint:

```bash
pylint $(git ls-files 'boilerplates/python/*.py')
```

### Fixing Common Pylint Errors

1. **Missing Docstrings** (C0114, C0115, C0116):
   ```python
   """Module docstring."""
   
   class MyClass:
       """Class docstring."""
       
       def my_method(self):
           """Method docstring."""
           pass
   ```

2. **Invalid Names** (C0103):
   - Use `snake_case` for functions and variables
   - Use `PascalCase` for classes
   - Use `UPPER_CASE` for constants

3. **Too Many Arguments** (R0913):
   - Use dataclasses or Pydantic models to group related parameters
   - Consider breaking down complex functions

4. **Too Many Instance Attributes** (R0902):
   - Break large classes into smaller ones
   - Use composition over inheritance

5. **Too Many Local Variables** (R0914):
   - Break down complex functions
   - Use helper methods for clarity

6. **Line Too Long** (C0301):
   - Break long lines at 100 characters
   - Use line continuation with parentheses
   - Format long strings with multiple lines

7. **Import Order** (C0411):
   ```python
   # Standard library imports
   import os
   import sys
   
   # Third-party imports
   import requests
   from pydantic import BaseModel
   
   # Local imports
   from .models import User
   ```

To disable specific warnings in code:
```python
# pylint: disable=specific-warning-code
code_that_triggers_warning
# pylint: enable=specific-warning-code
```

Or in `.pylintrc`:
```ini
[MESSAGES CONTROL]
disable=C0111,C0103
```

## Logic Development

The server's logic is organized in a modular structure:

### Services Layer (`src/services/`)
- `ai_service.py`: Base abstract class defining the AI service interface
- `openai_service.py`: OpenAI-specific implementation
- `deepseek_service.py`: DeepSeek-specific implementation
- `litellm_service.py`: LiteLLM integration
- `openai_compatible_service.py`: Generic OpenAI-compatible service

To add a new AI provider:
1. Create a new service class in `src/services/` that extends `AIService`
2. Implement the required methods: `get_models()` and `create_completion()`
3. Register the service in `src/routes/api_routes.py`

### Types and Schemas (`src/types/`)
- `api.py`: API request/response types
- `schemas.py`: Pydantic models for validation

To add new functionality:
1. Define new schemas in `schemas.py` if needed
2. Add new route handlers in `api_routes.py`
3. Implement the business logic in appropriate service classes
4. Update the API types in `api.py`

### Configuration (`src/config/`)
- `env.py`: Environment variables and configuration

To modify configuration:
1. Add new environment variables to `.env.example`
2. Update `env.py` with new configuration options
3. Use `config` object in your code to access settings

## API Endpoints

### GET /api/models

Get a list of available AI models.

Query parameters:
- `provider` (optional): Filter models by provider ('openai', 'deepseek', or 'litellm')

### GET /api/providers

Get information about available AI providers.

### POST /api/completions

Generate a completion from an AI model.

Request body:
```json
{
  "model": "gpt-3.5-turbo",
  "prompt": "Hello, how are you?",
  "max_tokens": 100,
  "temperature": 0.7,
  "provider": "openai" 
}
```

### GET /api/health

Health check endpoint.

## Example Usage

### Using the Test Client

Run the included test client to interact with the API:

```bash
python test_api.py
```

### Fetch Available Models

```bash
curl http://localhost:3000/api/models
```

### Generate a Completion

```bash
curl -X POST http://localhost:3000/api/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "prompt": "Write a short poem about programming"
  }'
```

### Generate a Streaming Completion

```bash
curl -X POST http://localhost:3000/api/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "prompt": "Write a short poem about programming",
    "stream": true
  }' --no-buffer
```

The streaming response will be delivered as Server-Sent Events (SSE), with each chunk of the completion sent as it's generated.

## License

ISC
