import dotenv from 'dotenv';
import { z } from 'zod';

// Load environment variables from .env file
dotenv.config();

// Define environment variables schema
const envSchema = z.object({
  // Server
  PORT: z.string().default('3000'),
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  
  // OpenAI
  OPENAI_API_KEY: z.string(),
  OPENAI_API_BASE_URL: z.string().default('https://api.openai.com/v1'),
  
  // DeepSeek
  DEEPSEEK_API_KEY: z.string(),
  DEEPSEEK_API_BASE_URL: z.string().default('https://api.deepseek.com/v1'),
});

// Parse and validate environment variables
const env = envSchema.safeParse(process.env);

if (!env.success) {
  console.error('❌ Invalid environment variables:', env.error.format());
  throw new Error('Invalid environment variables');
}

// Export validated environment variables
export const config = {
  server: {
    port: parseInt(env.data.PORT, 10),
    nodeEnv: env.data.NODE_ENV,
    isDev: env.data.NODE_ENV === 'development',
    isProd: env.data.NODE_ENV === 'production',
    isTest: env.data.NODE_ENV === 'test',
  },
  openai: {
    apiKey: env.data.OPENAI_API_KEY,
    baseUrl: env.data.OPENAI_API_BASE_URL,
  },
  deepseek: {
    apiKey: env.data.DEEPSEEK_API_KEY,
    baseUrl: env.data.DEEPSEEK_API_BASE_URL,
  },
};
