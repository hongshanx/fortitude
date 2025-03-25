# Python AI API Server Boilerplate Generation Prompt

## Objective
Create a production-ready Python boilerplate for an AI API server that can interact with multiple AI providers (OpenAI, DeepSeek, and LiteLLM) through a unified API.

## Requirements

### Core Functionality
- Create a Flask-based API server with the following endpoints:
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
- Asynchronous service layer for AI provider interactions

### Project Structure
- Use a modular architecture with clear separation of concerns
- Organize code into logical directories:
  - `src/` - Main source code
  - `src/config/` - Configuration management
  - `src/routes/` - API route definitions
  - `src/services/` - Service layer for AI providers
  - `src/middlewares/` - Middleware functions
  - `src/types/` - Type definitions and schemas

### Technical Specifications
- Use Python 3.9+
- Use Flask for the web server
- Use Pydantic for data validation and schemas
- Implement proper error handling with custom error classes
- Use async/await for service layer operations
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
- Include inline code comments

## Output
Generate all necessary files for a complete, working Python boilerplate that meets the above requirements. The code should be production-ready, well-structured, and follow best practices for Python development.
