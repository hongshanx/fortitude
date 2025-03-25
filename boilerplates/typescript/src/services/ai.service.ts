import { CompletionRequest, CompletionResponse, ALL_MODELS, updateLiteLLMModels } from '../types/api.js';
import { OpenAIService } from './openai.service.js';
import { DeepSeekService } from './deepseek.service.js';
import { LiteLLMService } from './litellm.service.js';
import { OpenAICompatibleService } from './openai-compatible.service.js';
import { ApiError } from '../middlewares/error-handler.js';

export class AIService {
  /**
   * Generate a completion using the appropriate service based on the model
   */
  static async generateCompletion(request: CompletionRequest): Promise<CompletionResponse> {
    // Find the model in our list
    const modelInfo = ALL_MODELS.find(m => m.id === request.model);
    
    if (!modelInfo) {
      throw new ApiError(400, `Model '${request.model}' not found`, 'MODEL_NOT_FOUND');
    }
    
    // If provider is specified, ensure it matches the model's provider
    if (request.provider && request.provider !== modelInfo.provider) {
      throw new ApiError(
        400,
        `Model '${request.model}' belongs to provider '${modelInfo.provider}', not '${request.provider}'`,
        'PROVIDER_MODEL_MISMATCH'
      );
    }
    
    // Route to the appropriate service
    switch (modelInfo.provider) {
      case 'openai':
        return OpenAIService.generateCompletion(request);
      case 'deepseek':
        return DeepSeekService.generateCompletion(request);
      case 'litellm':
        return LiteLLMService.generateCompletion(request);
      case 'openai_compatible':
        return OpenAICompatibleService.generateCompletion(request);
      default:
        throw new ApiError(500, `Unsupported provider: ${modelInfo.provider}`, 'UNSUPPORTED_PROVIDER');
    }
  }

  /**
   * Check which AI providers are available
   */
  static async getAvailableProviders() {
    // Check all providers' availability
    const [openaiAvailable, deepseekAvailable, litellmAvailable, openaiCompatibleAvailable] = await Promise.all([
      OpenAIService.checkAvailability(),
      DeepSeekService.checkAvailability(),
      LiteLLMService.checkAvailability(),
      OpenAICompatibleService.checkAvailability(),
    ]);
    
    // If LiteLLM is available, fetch and update models
    if (litellmAvailable) {
      try {
        const litellmModels = await LiteLLMService.getModels();
        updateLiteLLMModels(litellmModels);
      } catch (error) {
        console.error('Failed to fetch LiteLLM models:', error);
        // Continue with empty models list
      }
    }
    
    return {
      openai: openaiAvailable,
      deepseek: deepseekAvailable,
      litellm: litellmAvailable,
      openai_compatible: openaiCompatibleAvailable,
    };
  }
}
