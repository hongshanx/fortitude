import { Router, Request, Response, NextFunction } from 'express';
import { AIService } from '../services/ai.service.js';
import { validateRequest } from '../middlewares/error-handler.js';
import { completionRequestSchema, modelsRequestSchema } from '../types/schemas.js';
import { ALL_MODELS, OPENAI_MODELS, DEEPSEEK_MODELS, LITELLM_MODELS, getALLModels } from '../types/api.js';

// Create router
const router: Router = Router();

/**
 * GET /api/models
 * Get list of available models
 */
router.get('/models', async (req, res, next) => {
  try {
    const query = modelsRequestSchema.parse(req.query);
    const providers = await AIService.getAvailableProviders();
    
    // Get the latest models including any dynamically fetched ones
    let models = [...getALLModels()];
    
    // Filter by provider if specified
    if (query.provider) {
      models = models.filter(model => model.provider === query.provider);
    }
    
    // Filter out models from unavailable providers
    models = models.filter(model => {
      if (model.provider === 'openai' && !providers.openai) return false;
      if (model.provider === 'deepseek' && !providers.deepseek) return false;
      if (model.provider === 'litellm' && !providers.litellm) return false;
      return true;
    });
    
    res.json({
      models,
      providers,
    });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/providers
 * Get available AI providers
 */
router.get('/providers', async (req, res, next) => {
  try {
    const providers = await AIService.getAvailableProviders();
    
    res.json({
      providers: {
        openai: {
          available: providers.openai,
          models: providers.openai ? OPENAI_MODELS : [],
        },
        deepseek: {
          available: providers.deepseek,
          models: providers.deepseek ? DEEPSEEK_MODELS : [],
        },
        litellm: {
          available: providers.litellm,
          models: providers.litellm ? LITELLM_MODELS : [],
        },
      },
    });
  } catch (error) {
    next(error);
  }
});

/**
 * POST /api/completions
 * Generate a completion
 */
router.post('/completions', validateRequest(completionRequestSchema), async (req, res, next) => {
  try {
    const result = await AIService.generateCompletion(req.body);
    res.json(result);
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/health
 * Health check endpoint
 */
router.get('/health', async (req, res) => {
  const providers = await AIService.getAvailableProviders();
  
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    providers,
  });
});

export default router;
