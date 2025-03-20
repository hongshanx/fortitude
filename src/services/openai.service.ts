import OpenAI from 'openai';
import { config } from '../config/env.js';
import { CompletionRequest, CompletionResponse } from '../types/api.js';
import { ApiError } from '../middlewares/error-handler.js';

// Initialize OpenAI client
const openai = new OpenAI({
  apiKey: config.openai.apiKey,
  baseURL: config.openai.baseUrl,
});

export class OpenAIService {
  /**
   * Generate a completion using OpenAI API
   */
  static async generateCompletion(request: CompletionRequest): Promise<CompletionResponse> {
    try {
      // Create completion request
      const response = await openai.chat.completions.create({
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
        provider: 'openai',
        content: completion,
        usage: {
          promptTokens: response.usage?.prompt_tokens || 0,
          completionTokens: response.usage?.completion_tokens || 0,
          totalTokens: response.usage?.total_tokens || 0,
        },
        createdAt: new Date(response.created * 1000).toISOString(),
      };
    } catch (error: any) {
      console.error('OpenAI API Error:', error);
      
      // Handle API errors
      if (error.status === 401) {
        throw new ApiError(401, 'Invalid OpenAI API key', 'OPENAI_UNAUTHORIZED');
      } else if (error.status === 429) {
        throw new ApiError(429, 'OpenAI rate limit exceeded', 'OPENAI_RATE_LIMIT');
      } else if (error.status === 400) {
        throw new ApiError(400, error.message || 'Bad request to OpenAI API', 'OPENAI_BAD_REQUEST');
      }
      
      // Generic error
      throw new ApiError(
        500,
        `OpenAI API error: ${error.message || 'Unknown error'}`,
        'OPENAI_API_ERROR'
      );
    }
  }

  /**
   * Check if OpenAI API is configured and accessible
   */
  static async checkAvailability(): Promise<boolean> {
    try {
      if (!config.openai.apiKey || config.openai.apiKey === 'your_openai_api_key_here') {
        return false;
      }
      
      // Make a simple models list request to check if API is accessible
      await openai.models.list();
      return true;
    } catch (error) {
      console.error('OpenAI availability check failed:', error);
      return false;
    }
  }
}
