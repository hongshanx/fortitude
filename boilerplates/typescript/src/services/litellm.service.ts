import axios, { AxiosError } from 'axios';
import { config } from '../config/env.js';
import { AIModel, CompletionRequest, CompletionResponse } from '../types/api.js';
import { ApiError } from '../middlewares/error-handler.js';

// Interface for LiteLLM API model response
interface LiteLLMModel {
  id: string;
  owned_by: string;
  [key: string]: any; // For other properties that might be present
}

// Create axios instance for LiteLLM API
const litellmApi = axios.create({
  baseURL: config.litellm.baseUrl,
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${config.litellm.apiKey}`,
  },
});

export class LiteLLMService {
  /**
   * Generate a completion using LiteLLM API
   */
  static async generateCompletion(request: CompletionRequest): Promise<CompletionResponse> {
    try {
      // Create completion request
      const response = await litellmApi.post('/chat/completions', {
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
        provider: 'litellm',
        content: completion,
        usage: {
          promptTokens: data.usage?.prompt_tokens || 0,
          completionTokens: data.usage?.completion_tokens || 0,
          totalTokens: data.usage?.total_tokens || 0,
        },
        createdAt: new Date().toISOString(),
      };
    } catch (error: unknown) {
      console.error('LiteLLM API Error:', error);
      
      // Handle API errors
      if (axios.isAxiosError(error) && error.response) {
        const status = error.response.status;
        const data = error.response.data;
        
        if (status === 401) {
          throw new ApiError(401, 'Invalid LiteLLM API key', 'LITELLM_UNAUTHORIZED');
        } else if (status === 429) {
          throw new ApiError(429, 'LiteLLM rate limit exceeded', 'LITELLM_RATE_LIMIT');
        } else if (status === 400) {
          throw new ApiError(
            400,
            data.error?.message || 'Bad request to LiteLLM API',
            'LITELLM_BAD_REQUEST'
          );
        }
      }
      
      // Generic error
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      throw new ApiError(
        500,
        `LiteLLM API error: ${errorMessage}`,
        'LITELLM_API_ERROR'
      );
    }
  }

  /**
   * Get available models from LiteLLM API
   */
  static async getModels(): Promise<AIModel[]> {
    try {
      if (!config.litellm.apiKey || config.litellm.apiKey === 'your_litellm_api_key_here') {
        return [];
      }
      
      const response = await litellmApi.get('/models');
      const models = response.data.data || [];
      
      // Transform API response to AIModel format
      return models.map((model: LiteLLMModel) => ({
        id: model.id,
        name: model.id.split('-').map((word: string) => word.charAt(0).toUpperCase() + word.slice(1)).join(' '),
        provider: 'litellm',
        description: `${model.owned_by} model`,
        maxTokens: 100000, // Default value as the API doesn't provide this information
      }));
    } catch (error: unknown) {
      console.error('LiteLLM models fetch failed:', error);
      return [];
    }
  }

  /**
   * Check if LiteLLM API is configured and accessible
   */
  static async checkAvailability(): Promise<boolean> {
    try {
      if (!config.litellm.apiKey || config.litellm.apiKey === 'your_litellm_api_key_here') {
        return false;
      }
      
      // Make a simple models list request to check if API is accessible
      const response = await litellmApi.get('/models');
      return response.data && Array.isArray(response.data.data);
    } catch (error: unknown) {
      console.error('LiteLLM availability check failed:', error);
      return false;
    }
  }
}
