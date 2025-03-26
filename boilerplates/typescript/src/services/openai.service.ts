import OpenAI from 'openai';
import { APIError } from 'openai';
import { config } from '../config/env.js';
import { CompletionRequest, CompletionResponse, StreamChunk } from '../types/api.js';
import { ApiError } from '../middlewares/error-handler.js';
import { Response } from 'express';

// Initialize OpenAI client
const openai = new OpenAI({
  apiKey: config.openai.apiKey,
  baseURL: config.openai.baseUrl,
});

export class OpenAIService {
  /**
   * Generate a streaming completion using OpenAI API
   */
  static async generateStream(request: CompletionRequest, res: Response): Promise<void> {
    try {
      // Create streaming completion request
      const stream = await openai.chat.completions.create({
        model: request.model,
        messages: [
          { role: 'user', content: request.prompt }
        ],
        max_tokens: request.maxTokens,
        temperature: request.temperature,
        stream: true,
      });

      // Set headers for SSE
      res.setHeader('Content-Type', 'text/event-stream');
      res.setHeader('Cache-Control', 'no-cache');
      res.setHeader('Connection', 'keep-alive');
      res.setHeader('X-Accel-Buffering', 'no'); // Disable buffering in Nginx

      // Process the stream
      let accumulatedContent = '';
      let chunkId = '';
      let model = request.model;
      
      // For each chunk
      for await (const chunk of stream) {
        // Extract data
        if (chunk.id) chunkId = chunk.id;
        if (chunk.model) model = chunk.model;
        
        const content = chunk.choices[0]?.delta?.content || '';
        const finishReason = chunk.choices[0]?.finish_reason;
        
        if (content || finishReason) {
          // Accumulate content
          accumulatedContent += content;
          
          // Create chunk data
          const chunkData: StreamChunk = {
            id: chunkId,
            model,
            provider: 'openai',
            content,
            createdAt: new Date().toISOString(),
            isLastChunk: !!finishReason,
          };
          
          if (finishReason) {
            chunkData.finishReason = finishReason;
          }
          
          // Send the chunk as an SSE event
          res.write(`data: ${JSON.stringify(chunkData)}\n\n`);
        }
      }
      
      // End the stream
      res.write('data: [DONE]\n\n');
      res.end();
    } catch (error: unknown) {
      console.error('OpenAI API Streaming Error:', error);
      
      // Send error as an SSE event
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      const errorData = {
        error: {
          message: `OpenAI API error: ${errorMessage}`,
          code: 'OPENAI_API_ERROR'
        }
      };
      
      res.write(`data: ${JSON.stringify(errorData)}\n\n`);
      res.write('data: [DONE]\n\n');
      res.end();
    }
  }

  /**
   * Generate a completion using OpenAI API
   */
  static async generateCompletion(request: CompletionRequest): Promise<CompletionResponse> {
    try {
      // Create completion request
      const response = await openai.chat.completions.create({
        model: request.model,
        messages: [
          { role: 'user', content: request.prompt }
        ],
        max_tokens: request.maxTokens,
        temperature: request.temperature,
      });

      // Extract response data
      const completion = response.choices[0]?.message?.content || '';
      
      // Return formatted response
      return {
        id: response.id,
        model: response.model,
        provider: 'openai',
        content: completion,
        usage: {
          promptTokens: response.usage?.prompt_tokens || 0,
          completionTokens: response.usage?.completion_tokens || 0,
          totalTokens: response.usage?.total_tokens || 0,
        },
        createdAt: new Date(response.created * 1000).toISOString(),
      };
    } catch (error: unknown) {
      console.error('OpenAI API Error:', error);
      
      // Handle API errors
      if (error instanceof APIError) {
        if (error.status === 401) {
          throw new ApiError(401, 'Invalid OpenAI API key', 'OPENAI_UNAUTHORIZED');
        } else if (error.status === 429) {
          throw new ApiError(429, 'OpenAI rate limit exceeded', 'OPENAI_RATE_LIMIT');
        } else if (error.status === 400) {
          throw new ApiError(400, error.message || 'Bad request to OpenAI API', 'OPENAI_BAD_REQUEST');
        }
      }
      
      // Generic error
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      throw new ApiError(
        500,
        `OpenAI API error: ${errorMessage}`,
        'OPENAI_API_ERROR'
      );
    }
  }

  /**
   * Check if OpenAI API is configured and accessible
   */
  static async checkAvailability(): Promise<boolean> {
    try {
      if (!config.openai.apiKey || config.openai.apiKey === 'your_openai_api_key_here') {
        return false;
      }
      
      // Make a simple models list request to check if API is accessible
      await openai.models.list();
      return true;
    } catch (error: unknown) {
      console.error('OpenAI availability check failed:', error);
      return false;
    }
  }
}
