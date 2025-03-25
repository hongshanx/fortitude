# TypeScript AI API Server Boilerplate Generation Prompt

## Objective
Create a production-ready TypeScript boilerplate for an AI API server that can interact with multiple AI providers (OpenAI, DeepSeek, and LiteLLM) through a unified API.

## Requirements

### Core Functionality
- Create an Express-based API server with the following endpoints:
  - `/api/models` - List available AI models
  - `/api/providers` - List available AI providers
  - `/api/completions` - Generate text completions
  - `/api/health` - Health check endpoint
- Support for multiple AI providers:
  - OpenAI
  - DeepSeek
  - LiteLLM (as a proxy for other models like Claude)
- Environment-based configuration using dotenv
- Comprehensive error handling
- Promise-based service layer for AI provider interactions

### Project Structure
- Use a modular architecture with clear separation of concerns
- Organize code into logical directories:
  - `src/` - Main source code
  - `src/config/` - Configuration management
  - `src/routes/` - API route definitions
  - `src/services/` - Service layer for AI providers
  - `src/middlewares/` - Middleware functions
  - `src/types/` - TypeScript type definitions

### Technical Specifications
- Use TypeScript 4.5+
- Use Express for the web server
- Use Zod or similar for data validation and schemas
- Implement proper error handling with custom error classes
- Use Promises for asynchronous operations
- Include proper logging
- Include comprehensive documentation
- Include a test script for API testing

### Configuration
- Use environment variables for configuration
- Include a `.env.example` file with all required variables
- Support for development and production environments
- Configuration for API keys for each provider

### Documentation
- Include a README.md with setup and usage instructions
- Include API documentation
- Include inline code comments and TypeScript type definitions

## Output
Generate all necessary files for a complete, working TypeScript boilerplate that meets the above requirements. The code should be production-ready, well-structured, and follow best practices for TypeScript development.
