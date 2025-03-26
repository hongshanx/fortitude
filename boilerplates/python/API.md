# AI API Server (Python) - API Documentation

This document provides detailed information about the API endpoints available in the AI API Server.

## Base URL

By default, the API is available at `http://localhost:3000`.

## Authentication

Currently, the API does not require authentication. API keys for OpenAI, DeepSeek, and LiteLLM are configured server-side.

## Endpoints

### Get Available Models

Retrieves a list of available AI models.

```
GET /api/models
```

#### Query Parameters

| Parameter | Type   | Required | Description                                      |
|-----------|--------|----------|--------------------------------------------------|
| provider  | string | No       | Filter models by provider ('openai', 'deepseek', or 'litellm') |

#### Response

```json
{
  "models": [
    {
      "id": "gpt-4o",
      "name": "GPT-4o",
      "provider": "openai",
      "description": "Most capable model for complex tasks",
      "max_tokens": 128000
    },
    {
      "id": "gpt-3.5-turbo",
      "name": "GPT-3.5 Turbo",
      "provider": "openai",
      "description": "Fast and efficient for most tasks",
      "max_tokens": 16385
    },
    {
      "id": "deepseek-chat",
      "name": "DeepSeek Chat",
      "provider": "deepseek",
      "description": "General purpose chat model",
      "max_tokens": 32768
    }
  ],
  "providers": {
    "openai": true,
    "deepseek": true,
    "litellm": true
  }
}
```

### Get Provider Information

Retrieves information about available AI providers.

```
GET /api/providers
```

#### Response

```json
{
  "providers": {
    "openai": {
      "available": true,
      "models": [
        {
          "id": "gpt-4o",
          "name": "GPT-4o",
          "provider": "openai",
          "description": "Most capable model for complex tasks",
          "max_tokens": 128000
        },
        {
          "id": "gpt-3.5-turbo",
          "name": "GPT-3.5 Turbo",
          "provider": "openai",
          "description": "Fast and efficient for most tasks",
          "max_tokens": 16385
        }
      ]
    },
    "deepseek": {
      "available": true,
      "models": [
        {
          "id": "deepseek-chat",
          "name": "DeepSeek Chat",
          "provider": "deepseek",
          "description": "General purpose chat model",
          "max_tokens": 32768
        },
        {
          "id": "deepseek-coder",
          "name": "DeepSeek Coder",
          "provider": "deepseek",
          "description": "Specialized for coding tasks",
          "max_tokens": 32768
        }
      ]
    },
    "litellm": {
      "available": true,
      "models": [
        {

          "name": "Claude 3 Opus",
          "provider": "litellm",
          "description": "Anthropic's most powerful model",
          "max_tokens": 200000
        },
        {
          "id": "claude-3-sonnet",
          "name": "Claude 3 Sonnet",
          "provider": "litellm",
          "description": "Balanced performance and efficiency",
          "max_tokens": 180000
        },
        {
          "id": "gemini-pro",
          "name": "Gemini Pro",
          "provider": "litellm",
          "description": "Google's advanced model",
          "max_tokens": 30720
        }
      ]
    }
  }
}
```

### Generate Completion

Generates a completion from an AI model.

```
POST /api/completions
```

#### Request Body

| Field       | Type    | Required | Description                                      |
|-------------|---------|----------|--------------------------------------------------|
| model       | string  | Yes      | The ID of the model to use                       |
| prompt      | string  | Yes      | The prompt to generate a completion for          |
| max_tokens  | number  | No       | Maximum number of tokens to generate             |
| temperature | number  | No       | Sampling temperature (0-2, default: 0.7)         |
| provider    | string  | No       | Provider override ('openai', 'deepseek', 'litellm', or 'openai_compatible') |
| stream      | boolean | No       | Whether to stream the response (default: false)  |

#### Example Request

```json
{
  "model": "gpt-3.5-turbo",
  "prompt": "Write a short poem about programming",
  "max_tokens": 100,
  "temperature": 0.7
}
```

#### Response

For non-streaming requests:

```json
{
  "id": "cmpl-abc123",
  "model": "gpt-3.5-turbo",
  "provider": "openai",
  "content": "In lines of code, I find my way,\nA digital artist at play.\nWith logic and loops, I create,\nSolving problems, I feel great.\n\nBugs may come, errors arise,\nBut debugging makes me wise.\nIn this world of ones and zeros,\nProgrammers are the modern heroes.",
  "usage": {
    "prompt_tokens": 6,
    "completion_tokens": 48,
    "total_tokens": 54
  },
  "created_at": "2025-03-20T05:20:00.000Z"
}
```

For streaming requests (`stream: true`), the response is a stream of Server-Sent Events (SSE). Each event contains a chunk of the completion:

```
data: {"id":"cmpl-abc123","model":"gpt-3.5-turbo","provider":"openai","content":"In ","created_at":"2025-03-20T05:20:00.000Z","is_last_chunk":false}

data: {"id":"cmpl-abc123","model":"gpt-3.5-turbo","provider":"openai","content":"lines ","created_at":"2025-03-20T05:20:00.000Z","is_last_chunk":false}

data: {"id":"cmpl-abc123","model":"gpt-3.5-turbo","provider":"openai","content":"of ","created_at":"2025-03-20T05:20:00.000Z","is_last_chunk":false}

... more chunks ...

data: {"id":"cmpl-abc123","model":"gpt-3.5-turbo","provider":"openai","content":"heroes.","created_at":"2025-03-20T05:20:00.000Z","finish_reason":"stop","is_last_chunk":true}

data: [DONE]
```

Each chunk contains:
- `id`: The completion ID
- `model`: The model used
- `provider`: The AI provider
- `content`: The chunk of text
- `created_at`: Timestamp
- `finish_reason`: Reason for completion (only in the last chunk)
- `is_last_chunk`: Boolean indicating if this is the last chunk

The stream ends with a `data: [DONE]` message.

### Health Check

Checks the health status of the API server.

```
GET /api/health
```

#### Response

```json
{
  "status": "ok",
  "timestamp": "2025-03-20T05:20:00.000Z",
  "providers": {
    "openai": true,
    "deepseek": false,
    "litellm": true
  }
}
```

## Error Handling

The API returns appropriate HTTP status codes and error messages in case of failures.

### Error Response Format

```json
{
  "error": {
    "message": "Error message",
    "code": "ERROR_CODE",
    "details": {} // Optional additional details
  }
}
```

### Common Error Codes

| Status Code | Error Code           | Description                                      |
|-------------|----------------------|--------------------------------------------------|
| 400         | VALIDATION_ERROR     | Invalid request parameters                       |
| 400         | MODEL_NOT_FOUND      | Requested model not found                        |
| 401         | OPENAI_UNAUTHORIZED  | Invalid OpenAI API key                           |
| 401         | DEEPSEEK_UNAUTHORIZED| Invalid DeepSeek API key                         |
| 401         | LITELLM_UNAUTHORIZED | Invalid LiteLLM API key                          |
| 404         | NOT_FOUND            | Endpoint not found                               |
| 429         | OPENAI_RATE_LIMIT    | OpenAI rate limit exceeded                       |
| 429         | DEEPSEEK_RATE_LIMIT  | DeepSeek rate limit exceeded                     |
| 429         | LITELLM_RATE_LIMIT   | LiteLLM rate limit exceeded                      |
| 500         | INTERNAL_ERROR       | Server error                                     |
