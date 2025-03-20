import { z } from 'zod';
import { ALL_MODELS } from './api.js';

// Get the list of valid model IDs
const validModelIds = ALL_MODELS.map(model => model.id);

// Completion request schema
export const completionRequestSchema = z.object({
  model: z.string().refine(val => validModelIds.includes(val), {
    message: `Model must be one of: ${validModelIds.join(', ')}`,
  }),
  prompt: z.string().min(1, 'Prompt cannot be empty').max(32000, 'Prompt is too long'),
  maxTokens: z.number().int().positive().max(32000).optional(),
  temperature: z.number().min(0).max(2).optional().default(0.7),
  provider: z.enum(['openai', 'deepseek']).optional(),
});

// Export type
export type CompletionRequestSchema = z.infer<typeof completionRequestSchema>;

// Models list request schema
export const modelsRequestSchema = z.object({
  provider: z.enum(['openai', 'deepseek']).optional(),
});

// Export type
export type ModelsRequestSchema = z.infer<typeof modelsRequestSchema>;
