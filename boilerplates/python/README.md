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
