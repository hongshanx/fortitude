import express from 'express';
import cors from 'cors';
import { config } from './config/env.js';
import apiRoutes from './routes/api.routes.js';
import { errorHandler, notFound } from './middlewares/error-handler.js';

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
    description: 'API server for OpenAI and DeepSeek models',
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
app.listen(port, () => {
  console.log(`✅ Server running at http://localhost:${port}`);
  console.log(`📝 API documentation available at http://localhost:${port}/api`);
  console.log(`🔍 Health check at http://localhost:${port}/api/health`);
  
  // Log environment
  console.log(`🌍 Environment: ${config.server.nodeEnv}`);
  
  // Check API keys
  const openaiKeyConfigured = config.openai.apiKey && config.openai.apiKey !== 'your_openai_api_key_here';
  const deepseekKeyConfigured = config.deepseek.apiKey && config.deepseek.apiKey !== 'your_deepseek_api_key_here';
  
  console.log(`🔑 OpenAI API key: ${openaiKeyConfigured ? 'Configured' : 'Not configured'}`);
  console.log(`🔑 DeepSeek API key: ${deepseekKeyConfigured ? 'Configured' : 'Not configured'}`);
  
  if (!openaiKeyConfigured && !deepseekKeyConfigured) {
    console.warn('⚠️  Warning: No API keys configured. Please set up API keys in .env file.');
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
