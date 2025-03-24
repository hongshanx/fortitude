import axios, { AxiosError } from 'axios';
import { config } from '../config/env.js';
import { CompletionRequest, CompletionResponse } from '../types/api.js';
import { ApiError } from '../middlewares/error-handler.js';

// Create axios instance for DeepSeek API
const deepseekApi = axios.create({
  baseURL: config.deepseek.baseUrl,
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${config.deepseek.apiKey}`,
  },
});

export class DeepSeekService {
  /**
   * Generate a completion using DeepSeek API
   */
  static async generateCompletion(request: CompletionRequest): Promise<CompletionResponse> {
    try {
      // Create completion request
      const response = await deepseekApi.post('/chat/completions', {
        model: request.model,
        messages: [
          { role: 'user', content: request.prompt }
        ],
        max_tokens: request.maxTokens,
        temperature: request.temperature,
      });

      const data = response.data;
      
      // Extract response data
      const completion = data.choices[0]?.message?.content || '';
      
      // Return formatted response
      return {
        id: data.id,
        model: data.model,
        provider: 'deepseek',
        content: completion,
        usage: {
          promptTokens: data.usage?.prompt_tokens || 0,
          completionTokens: data.usage?.completion_tokens || 0,
          totalTokens: data.usage?.total_tokens || 0,
        },
        createdAt: new Date().toISOString(),
      };
    } catch (error: unknown) {
      console.error('DeepSeek API Error:', error);
      
      // Handle API errors
      if (axios.isAxiosError(error) && error.response) {
        const status = error.response.status;
        const data = error.response.data;
        
        if (status === 401) {
          throw new ApiError(401, 'Invalid DeepSeek API key', 'DEEPSEEK_UNAUTHORIZED');
        } else if (status === 429) {
          throw new ApiError(429, 'DeepSeek rate limit exceeded', 'DEEPSEEK_RATE_LIMIT');
        } else if (status === 400) {
          throw new ApiError(
            400,
            data.error?.message || 'Bad request to DeepSeek API',
            'DEEPSEEK_BAD_REQUEST'
          );
        }
      }
      
      // Generic error
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      throw new ApiError(
        500,
        `DeepSeek API error: ${errorMessage}`,
        'DEEPSEEK_API_ERROR'
      );
    }
  }

  /**
   * Check if DeepSeek API is configured and accessible
   */
  static async checkAvailability(): Promise<boolean> {
    try {
      if (!config.deepseek.apiKey || config.deepseek.apiKey === 'your_deepseek_api_key_here') {
        return false;
      }
      
      // Make a simple models list request to check if API is accessible
      await deepseekApi.get('/models');
      return true;
    } catch (error: unknown) {
      console.error('DeepSeek availability check failed:', error);
      return false;
    }
  }
}
