import express from 'express';
import cors from 'cors';
import { config } from './config/env.js';
import apiRoutes from './routes/api.routes.js';
import { errorHandler, notFound } from './middlewares/error-handler.js';
import { LiteLLMService } from './services/litellm.service.js';
import { updateLiteLLMModels } from './types/api.js';
import { OpenAICompatibleService } from './services/openai-compatible.service.js';

// Create Express app
const app = express();
const port = config.server.port;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Request logging in development
if (config.server.isDev) {
  app.use((req, res, next) => {
    console.log(`${req.method} ${req.url}`);
    next();
  });
}

// API routes
app.use('/api', apiRoutes);

// Root route
app.get('/', (req, res) => {
  res.json({
    name: 'AI API Server',
    version: '1.0.0',
    description: 'API server for OpenAI, DeepSeek, LiteLLM, and OpenAI-compatible models',
    endpoints: {
      models: '/api/models',
      providers: '/api/providers',
      completions: '/api/completions',
      health: '/api/health',
    },
  });
});

// 404 handler
app.use(notFound);

// Error handler
app.use(errorHandler);

// Start server
app.listen(port, async () => {
  console.log(`✅ Server running at http://localhost:${port}`);
  console.log(`📝 API documentation available at http://localhost:${port}/api`);
  console.log(`🔍 Health check at http://localhost:${port}/api/health`);
  
  // Log environment
  console.log(`🌍 Environment: ${config.server.nodeEnv}`);
  
  // Check API keys
  const openaiKeyConfigured = config.openai.apiKey && config.openai.apiKey !== 'your_openai_api_key_here';
  const deepseekKeyConfigured = config.deepseek.apiKey && config.deepseek.apiKey !== 'your_deepseek_api_key_here';
  const litellmKeyConfigured = config.litellm.apiKey && config.litellm.apiKey !== 'your_litellm_api_key_here';
  const openaiCompatibleKeyConfigured = config.openaiCompatible.apiKey && config.openaiCompatible.apiKey !== 'your_openai_compatible_api_key_here';
  
  console.log(`🔑 OpenAI API key: ${openaiKeyConfigured ? 'Configured' : 'Not configured'}`);
  console.log(`🔑 DeepSeek API key: ${deepseekKeyConfigured ? 'Configured' : 'Not configured'}`);
  console.log(`🔑 LiteLLM API key: ${litellmKeyConfigured ? 'Configured' : 'Not configured'}`);
  console.log(`🔑 OpenAI-compatible API key: ${openaiCompatibleKeyConfigured ? 'Configured' : 'Not configured'}`);
  
  if (!openaiKeyConfigured && !deepseekKeyConfigured && !litellmKeyConfigured && !openaiCompatibleKeyConfigured) {
    console.warn('⚠️  Warning: No API keys configured. Please set up API keys in .env file.');
  }
  
  // Fetch LiteLLM models at startup if configured
  if (litellmKeyConfigured) {
    try {
      console.log('🔄 Fetching LiteLLM models...');
      const litellmModels = await LiteLLMService.getModels();
      updateLiteLLMModels(litellmModels);
      console.log(`✅ Fetched ${litellmModels.length} LiteLLM models`);
    } catch (error) {
      console.error('❌ Failed to fetch LiteLLM models:', error);
      console.log('⚠️  Using empty models list');
    }
  }
  
  // Check OpenAI-compatible API at startup if configured
  if (openaiCompatibleKeyConfigured) {
    try {
      console.log('🔄 Checking OpenAI-compatible API...');
      const available = await OpenAICompatibleService.checkAvailability();
      if (available) {
        console.log('✅ OpenAI-compatible API is accessible');
      } else {
        console.log('❌ OpenAI-compatible API is not accessible');
      }
    } catch (error) {
      console.error('❌ Failed to check OpenAI-compatible API:', error);
    }
  }
});

// Handle unhandled promise rejections
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
  process.exit(1);
});
