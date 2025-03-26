import { z } from 'zod';
import { getALLModels } from './api.js';

// Completion request schema
export const completionRequestSchema = z.object({
  model: z.string().refine(val => {
    // Get the current list of valid model IDs at validation time
    const validModelIds = getALLModels().map(model => model.id);
    return validModelIds.includes(val);
  }, {
    message: 'Invalid model ID',
  }),
  prompt: z.string().min(1, 'Prompt cannot be empty').max(32000, 'Prompt is too long'),
  maxTokens: z.number().int().positive().max(32000).optional(),
  temperature: z.number().min(0).max(2).optional().default(0.7),
  provider: z.enum(['openai', 'deepseek', 'litellm', 'openai_compatible']).optional(),
  stream: z.boolean().optional().default(false),
});

// Export type
export type CompletionRequestSchema = z.infer<typeof completionRequestSchema>;

// Models list request schema
export const modelsRequestSchema = z.object({
  provider: z.enum(['openai', 'deepseek', 'litellm']).optional(),
});

// Export type
export type ModelsRequestSchema = z.infer<typeof modelsRequestSchema>;
