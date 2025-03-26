# AI API Server

A Node.js API server that connects to OpenAI, DeepSeek, and LiteLLM AI models, allowing users to select models and customize prompts to get AI-generated responses.

## Features

- Connect to multiple AI providers (OpenAI, DeepSeek, and LiteLLM)
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
- LiteLLM
- Axios for API requests
- Zod for validation

## Prerequisites

- Node.js 18+ installed
- PNPM installed
- OpenAI API key (optional)
- DeepSeek API key (optional)
- LiteLLM API key (optional)

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
LITELLM_API_KEY=your_litellm_api_key_here
LITELLM_API_BASE_URL=http://localhost:4000
```

## Development

Start the development server:

```bash
pnpm dev
```

The server will run at http://localhost:3000 by default.

## Logic Development

The server's logic is organized in a modular structure:

### Services Layer (`src/services/`)
- `ai.service.ts`: Base abstract class defining the AI service interface
- `openai.service.ts`: OpenAI-specific implementation
- `deepseek.service.ts`: DeepSeek-specific implementation
- `litellm.service.ts`: LiteLLM integration
- `openai-compatible.service.ts`: Generic OpenAI-compatible service

To add a new AI provider:
1. Create a new service class in `src/services/` that extends `AIService`
2. Implement the required methods: `getModels()` and `createCompletion()`
3. Register the service in `src/routes/api.routes.ts`

### Types and Schemas (`src/types/`)
- `api.ts`: API request/response types
- `schemas.ts`: Zod schemas for validation

To add new functionality:
1. Define new schemas in `schemas.ts` if needed
2. Add new route handlers in `api.routes.ts`
3. Implement the business logic in appropriate service classes
4. Update the API types in `api.ts`

### Configuration (`src/config/`)
- `env.ts`: Environment variables and configuration using Zod for validation

To modify configuration:
1. Add new environment variables to `.env.example`
2. Update `env.ts` with new configuration options and their Zod schemas
3. Use `config` object in your code to access typed settings

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
  "maxTokens": 100,
  "temperature": 0.7,
  "provider": "openai" // Optional, can be inferred from model (openai, deepseek, or litellm)
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
