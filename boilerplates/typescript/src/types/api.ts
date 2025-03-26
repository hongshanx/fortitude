// Provider types
export type AIProvider = 'openai' | 'deepseek' | 'litellm' | 'openai_compatible';

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

// LiteLLM models will be populated dynamically
export let LITELLM_MODELS: AIModel[] = [];

// OpenAI-compatible models - default examples, will be customizable
// using aliyun
export const OPENAI_COMPATIBLE_MODELS: AIModel[] = [
  {
    id: 'llama3.3-70b-instruct',
    name: 'Llama 3',
    provider: 'openai_compatible',
    description: "Meta's Llama 3 model via OpenAI-compatible API",
    maxTokens:  30000,
  },
  {
    id: 'deepseek-v3',
    name: 'DeepSeek-V3',
    provider: 'openai_compatible',
    description: 'DeepSeek V3 model via OpenAI-compatible API',
    maxTokens: 57344,
  },
  {
    id: 'qwen-max',
    name: '通义千问-Max',
    provider: 'openai_compatible',
    description: '通义千问-Max model via OpenAI-compatible API',
    maxTokens: 30720,
  },
];

// All available models
export const getALLModels = (): AIModel[] => [
  ...OPENAI_MODELS, 
  ...DEEPSEEK_MODELS, 
  ...LITELLM_MODELS,
  ...OPENAI_COMPATIBLE_MODELS
];
export let ALL_MODELS: AIModel[] = getALLModels();

// Function to update LiteLLM models
export const updateLiteLLMModels = (models: AIModel[]): void => {
  LITELLM_MODELS = models.length > 0 ? models : [];
  ALL_MODELS = getALLModels();
};

// Request types
export interface CompletionRequest {
  model: string;
  prompt: string;
  maxTokens?: number;
  temperature?: number;
  provider?: AIProvider; // Optional, can be inferred from model
  stream?: boolean; // Whether to stream the response
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

// Streaming response types
export interface StreamChunk {
  id: string;
  model: string;
  provider: AIProvider;
  content: string;
  createdAt: string;
  finishReason?: string;
  isLastChunk: boolean;
}

// Error response
export interface ErrorResponse {
  error: {
    message: string;
    code?: string;
    type?: string;
  };
}
