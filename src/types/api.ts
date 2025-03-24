// Provider types
export type AIProvider = 'openai' | 'deepseek' | 'litellm';

// Model types
export interface AIModel {
  id: string;
  name: string;
  provider: AIProvider;
  description?: string;
  maxTokens?: number;
}

// OpenAI models
export const OPENAI_MODELS: AIModel[] = [
  {
    id: 'gpt-4o',
    name: 'GPT-4o',
    provider: 'openai',
    description: 'Most capable model for complex tasks',
    maxTokens: 128000,
  },
  {
    id: 'gpt-4-turbo',
    name: 'GPT-4 Turbo',
    provider: 'openai',
    description: 'Optimized version of GPT-4',
    maxTokens: 128000,
  },
  {
    id: 'gpt-3.5-turbo',
    name: 'GPT-3.5 Turbo',
    provider: 'openai',
    description: 'Fast and efficient for most tasks',
    maxTokens: 16385,
  },
];

// DeepSeek models
export const DEEPSEEK_MODELS: AIModel[] = [
  {
    id: 'deepseek-chat',
    name: 'DeepSeek Chat',
    provider: 'deepseek',
    description: 'General purpose chat model',
    maxTokens: 32768,
  },
  {
    id: 'deepseek-coder',
    name: 'DeepSeek Coder',
    provider: 'deepseek',
    description: 'Specialized for coding tasks',
    maxTokens: 32768,
  },
];

// LiteLLM models - these will be fetched dynamically from the API
// This is just a fallback in case the API is not available
export const LITELLM_MODELS_FALLBACK: AIModel[] = [
  {
    id: 'claude-3-opus',
    name: 'Claude 3 Opus',
    provider: 'litellm',
    description: 'Anthropic\'s most powerful model',
    maxTokens: 200000,
  },
  {
    id: 'claude-3-sonnet',
    name: 'Claude 3 Sonnet',
    provider: 'litellm',
    description: 'Balanced performance and efficiency',
    maxTokens: 180000,
  },
  {
    id: 'gemini-pro',
    name: 'Gemini Pro',
    provider: 'litellm',
    description: 'Google\'s advanced model',
    maxTokens: 30720,
  },
];

// LiteLLM models will be populated dynamically
export let LITELLM_MODELS: AIModel[] = [...LITELLM_MODELS_FALLBACK];

// All available models
export const getALLModels = (): AIModel[] => [...OPENAI_MODELS, ...DEEPSEEK_MODELS, ...LITELLM_MODELS];
export let ALL_MODELS: AIModel[] = getALLModels();

// Function to update LiteLLM models
export const updateLiteLLMModels = (models: AIModel[]): void => {
  LITELLM_MODELS = models.length > 0 ? models : LITELLM_MODELS_FALLBACK;
  ALL_MODELS = getALLModels();
};

// Request types
export interface CompletionRequest {
  model: string;
  prompt: string;
  maxTokens?: number;
  temperature?: number;
  provider?: AIProvider; // Optional, can be inferred from model
}

// Response types
export interface CompletionResponse {
  id: string;
  model: string;
  provider: AIProvider;
  content: string;
  usage: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
  createdAt: string;
}

// Error response
export interface ErrorResponse {
  error: {
    message: string;
    code?: string;
    type?: string;
  };
}
