import axios, { AxiosError } from 'axios';
import { config } from '../config/env.js';
import { CompletionRequest, CompletionResponse, StreamChunk } from '../types/api.js';
import { ApiError } from '../middlewares/error-handler.js';
import { Response } from 'express';

// Create axios instance for DeepSeek API
const deepseekApi = axios.create({
  baseURL: config.deepseek.baseUrl,
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${config.deepseek.apiKey}`,
  },
});

export class DeepSeekService {
  /**
   * Generate a streaming completion using DeepSeek API
   */
  static async generateStream(request: CompletionRequest, res: Response): Promise<void> {
    try {
      // Set headers for SSE
      res.setHeader('Content-Type', 'text/event-stream');
      res.setHeader('Cache-Control', 'no-cache');
      res.setHeader('Connection', 'keep-alive');
      res.setHeader('X-Accel-Buffering', 'no'); // Disable buffering in Nginx

      // Create streaming request
      const response = await axios.post(
        `${config.deepseek.baseUrl}/chat/completions`,
        {
          model: request.model,
          messages: [
            { role: 'user', content: request.prompt }
          ],
          max_tokens: request.maxTokens,
          temperature: request.temperature,
          stream: true,
        },
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${config.deepseek.apiKey}`,
          },
          responseType: 'stream',
        }
      );

      // Process the stream
      let chunkId = `chatcmpl-${Date.now()}`;
      let model = request.model;
      let accumulatedContent = '';
      
      // Handle the stream data
      response.data.on('data', (chunk: Buffer) => {
        const lines = chunk.toString().split('\n');
        
        for (const line of lines) {
          if (!line.trim() || !line.startsWith('data: ')) continue;
          
          const data = line.substring(6); // Remove 'data: ' prefix
          
          if (data === '[DONE]') {
            // End of stream
            res.write('data: [DONE]\n\n');
            return;
          }
          
          try {
            const parsedData = JSON.parse(data);
            
            // Extract data
            if (parsedData.id) chunkId = parsedData.id;
            if (parsedData.model) model = parsedData.model;
            
            const content = parsedData.choices?.[0]?.delta?.content || '';
            const finishReason = parsedData.choices?.[0]?.finish_reason;
            
            if (content || finishReason) {
              // Accumulate content
              accumulatedContent += content;
              
              // Create chunk data
              const chunkData: StreamChunk = {
                id: chunkId,
                model,
                provider: 'deepseek',
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
          } catch (e) {
            console.error('Error parsing DeepSeek stream chunk:', e);
          }
        }
      });
      
      // Handle end of stream
      response.data.on('end', () => {
        res.write('data: [DONE]\n\n');
        res.end();
      });
      
      // Handle errors
      response.data.on('error', (err: Error) => {
        console.error('DeepSeek API Streaming Error:', err);
        
        // Send error as an SSE event
        const errorData = {
          error: {
            message: `DeepSeek API error: ${err.message}`,
            code: 'DEEPSEEK_API_ERROR'
          }
        };
        
        res.write(`data: ${JSON.stringify(errorData)}\n\n`);
        res.write('data: [DONE]\n\n');
        res.end();
      });
    } catch (error: unknown) {
      console.error('DeepSeek API Streaming Error:', error);
      
      // Send error as an SSE event
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      const errorData = {
        error: {
          message: `DeepSeek API error: ${errorMessage}`,
          code: 'DEEPSEEK_API_ERROR'
        }
      };
      
      res.write(`data: ${JSON.stringify(errorData)}\n\n`);
      res.write('data: [DONE]\n\n');
      res.end();
    }
  }

  /**
   * Generate a completion using DeepSeek API
   */
  static async generateCompletion(request: CompletionRequest): Promise<CompletionResponse> {
    try {
      // Create completion request
      const response = await deepseekApi.post('/chat/completions', {
        model: request.model,
        messages: [
          { role: 'user', content: request.prompt }
        ],
        max_tokens: request.maxTokens,
        temperature: request.temperature,
      });

      const data = response.data;
      
      // Extract response data
      const completion = data.choices[0]?.message?.content || '';
      
      // Return formatted response
      return {
        id: data.id,
        model: data.model,
        provider: 'deepseek',
        content: completion,
        usage: {
          promptTokens: data.usage?.prompt_tokens || 0,
          completionTokens: data.usage?.completion_tokens || 0,
          totalTokens: data.usage?.total_tokens || 0,
        },
        createdAt: new Date().toISOString(),
      };
    } catch (error: unknown) {
      console.error('DeepSeek API Error:', error);
      
      // Handle API errors
      if (axios.isAxiosError(error) && error.response) {
        const status = error.response.status;
        const data = error.response.data;
        
        if (status === 401) {
          throw new ApiError(401, 'Invalid DeepSeek API key', 'DEEPSEEK_UNAUTHORIZED');
        } else if (status === 429) {
          throw new ApiError(429, 'DeepSeek rate limit exceeded', 'DEEPSEEK_RATE_LIMIT');
        } else if (status === 400) {
          throw new ApiError(
            400,
            data.error?.message || 'Bad request to DeepSeek API',
            'DEEPSEEK_BAD_REQUEST'
          );
        }
      }
      
      // Generic error
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      throw new ApiError(
        500,
        `DeepSeek API error: ${errorMessage}`,
        'DEEPSEEK_API_ERROR'
      );
    }
  }

  /**
   * Check if DeepSeek API is configured and accessible
   */
  static async checkAvailability(): Promise<boolean> {
    try {
      if (!config.deepseek.apiKey || config.deepseek.apiKey === 'your_deepseek_api_key_here') {
        return false;
      }
      
      // Make a simple models list request to check if API is accessible
      await deepseekApi.get('/models');
      return true;
    } catch (error: unknown) {
      console.error('DeepSeek availability check failed:', error);
      return false;
    }
  }
}
