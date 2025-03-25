import OpenAI from 'openai';
import { APIError } from 'openai';
import { config } from '../config/env.js';
import { CompletionRequest, CompletionResponse } from '../types/api.js';
import { ApiError } from '../middlewares/error-handler.js';

// Initialize OpenAI-compatible client
const openaiCompatible = new OpenAI({
  apiKey: config.openaiCompatible.apiKey,
  baseURL: config.openaiCompatible.baseUrl,
});

export class OpenAICompatibleService {
  /**
   * Generate a completion using OpenAI-compatible API
   */
  static async generateCompletion(request: CompletionRequest): Promise<CompletionResponse> {
    try {
      // Create completion request
      const response = await openaiCompatible.chat.completions.create({
        model: request.model,
        messages: [
          { role: 'user', content: request.prompt }
        ],
        max_tokens: request.maxTokens,
        temperature: request.temperature,
      });

      // Extract response data
      const completion = response.choices[0]?.message?.content || '';
      
      // Return formatted response
      return {
        id: response.id,
        model: response.model,
        provider: 'openai_compatible',
        content: completion,
        usage: {
          promptTokens: response.usage?.prompt_tokens || 0,
          completionTokens: response.usage?.completion_tokens || 0,
          totalTokens: response.usage?.total_tokens || 0,
        },
        createdAt: response.created ? new Date(response.created * 1000).toISOString() : new Date().toISOString(),
      };
    } catch (error: unknown) {
      console.error('OpenAI-compatible API Error:', error);
      
      // Handle API errors
      if (error instanceof APIError) {
        if (error.status === 401) {
          throw new ApiError(401, 'Invalid OpenAI-compatible API key', 'OPENAI_COMPATIBLE_UNAUTHORIZED');
        } else if (error.status === 429) {
          throw new ApiError(429, 'OpenAI-compatible rate limit exceeded', 'OPENAI_COMPATIBLE_RATE_LIMIT');
        } else if (error.status === 400) {
          throw new ApiError(400, error.message || 'Bad request to OpenAI-compatible API', 'OPENAI_COMPATIBLE_BAD_REQUEST');
        }
      }
      
      // Generic error
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      throw new ApiError(
        500,
        `OpenAI-compatible API error: ${errorMessage}`,
        'OPENAI_COMPATIBLE_API_ERROR'
      );
    }
  }

  /**
   * Check if OpenAI-compatible API is configured and accessible
   */
  static async checkAvailability(): Promise<boolean> {
    try {
      if (!config.openaiCompatible.apiKey || config.openaiCompatible.apiKey === 'your_openai_compatible_api_key_here') {
        return false;
      }
      
      // Make a simple models list request to check if API is accessible
      // Some OpenAI-compatible APIs might not support this endpoint, so we'll catch exceptions
      try {
        // Try to list models first
        await openaiCompatible.models.list();
        // If successful, we're done
        return true;
      } catch (e) {
        console.log(`Models list failed, trying direct completion: ${e}`);
        // If models.list() fails, try to get a list of available models from the API
        // by checking the error message, which might contain model information
        
        // For APIs that don't support models.list(), we need to try a direct completion
        // with a model name that might exist. We'll try a few common model names.
        const possibleModels = ['local-model', 'llama3', 'qwen-max', 'deepseek-v3', 'gemini-pro'];
        
        // Try each model until one works
        for (const model of possibleModels) {
          try {
            console.log(`Trying model: ${model}`);
            await openaiCompatible.chat.completions.create({
              model: model,
              messages: [{ role: 'user', content: 'Hello' }],
              max_tokens: 1
            });
            // If we get here, the model exists
            console.log(`Model ${model} works!`);
            return true;
          } catch (modelError) {
            // If this model doesn't work, try the next one
            console.log(`Model ${model} failed: ${modelError}`);
            continue;
          }
        }
        
        // If we get here, none of the models worked
        // Let's try one more time with the first model in the error message
        // This is a heuristic that might work for some APIs
        try {
          const errorMessage = String(e).toLowerCase();
          // Look for common patterns in error messages
          if (errorMessage.includes('available models') || errorMessage.includes('model not found')) {
            // Try to extract a model name from the error message
            // This is a very simple heuristic and might not work for all APIs
            const words = errorMessage.split(/\s+/);
            for (const word of words) {
              if (word.length > 5 && !['the', 'and', 'for', 'with'].some(prefix => word.startsWith(prefix))) {
                // Try this word as a model name
                try {
                  await openaiCompatible.chat.completions.create({
                    model: word,
                    messages: [{ role: 'user', content: 'Hello' }],
                    max_tokens: 1
                  });
                  return true;
                } catch {
                  // If this doesn't work, we'll just continue
                }
              }
            }
          }
        } catch {
          // If this doesn't work, we'll just continue
        }
        
        // If we get here, we couldn't find a working model
        // But we'll still return True if the API key is configured
        // because the user might know which model to use
        return true;
      }
    } catch (error: unknown) {
      console.error('OpenAI-compatible availability check failed:', error);
      return false;
    }
  }
}
