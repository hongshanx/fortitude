# AI API Server

A Node.js API server that connects to OpenAI and DeepSeek AI models, allowing users to select models and customize prompts to get AI-generated responses.

## Features

- Connect to multiple AI providers (OpenAI and DeepSeek)
- Select from various AI models
- Customize prompts and parameters
- RESTful API with proper error handling
- TypeScript for type safety
- ESM modules
- Built with Express.js

## Tech Stack

- Node.js
- TypeScript
- Express.js
- PNPM (Package Manager)
- ESM Modules
- OpenAI SDK
- Axios for API requests
- Zod for validation

## Prerequisites

- Node.js 18+ installed
- PNPM installed
- OpenAI API key (optional)
- DeepSeek API key (optional)

## Installation

1. Clone the repository
2. Install dependencies:

```bash
pnpm install
```

3. Copy the example environment file and configure your API keys:

```bash
cp .env.example .env
```

4. Edit the `.env` file and add your API keys:

```
OPENAI_API_KEY=your_openai_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

## Development

Start the development server:

```bash
pnpm dev
```

The server will run at http://localhost:3000 by default.

## Build

Build the project:

```bash
pnpm build
```

## Production

Start the production server:

```bash
pnpm start
```

## API Endpoints

### GET /api/models

Get a list of available AI models.

Query parameters:
- `provider` (optional): Filter models by provider ('openai' or 'deepseek')

### GET /api/providers

Get information about available AI providers.

### POST /api/completions

Generate a completion from an AI model.

Request body:
```json
{
  "model": "gpt-3.5-turbo",
  "prompt": "Hello, how are you?",
  "maxTokens": 100,
  "temperature": 0.7,
  "provider": "openai" // Optional, can be inferred from model
}
```

### GET /api/health

Health check endpoint.

## Example Usage

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

## License

ISC
