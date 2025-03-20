// Provider types
export type AIProvider = 'openai' | 'deepseek';

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

// All available models
export const ALL_MODELS: AIModel[] = [...OPENAI_MODELS, ...DEEPSEEK_MODELS];

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
