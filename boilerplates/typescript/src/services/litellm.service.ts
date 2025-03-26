import axios, { AxiosError } from 'axios';
import { config } from '../config/env.js';
import { AIModel, CompletionRequest, CompletionResponse, StreamChunk } from '../types/api.js';
import { ApiError } from '../middlewares/error-handler.js';
import { Response } from 'express';

// Interface for LiteLLM API model response
interface LiteLLMModel {
  id: string;
  owned_by: string;
  [key: string]: any; // For other properties that might be present
}

// Create axios instance for LiteLLM API
const litellmApi = axios.create({
  baseURL: config.litellm.baseUrl,
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${config.litellm.apiKey}`,
  },
});

export class LiteLLMService {
  /**
   * Generate a streaming completion using LiteLLM API
   */
  static async generateStream(request: CompletionRequest, res: Response): Promise<void> {
    try {
      // Set headers for SSE
      res.setHeader('Content-Type', 'text/event-stream');
      res.setHeader('Cache-Control', 'no-cache');
      res.setHeader('Connection', 'keep-alive');
      res.setHeader('X-Accel-Buffering', 'no'); // Disable buffering in Nginx

      console.log('Starting streaming request for model:', request.model);
      console.log('Base URL:', config.litellm.baseUrl);
      
      // Create streaming request
      const response = await axios.post(
        `${config.litellm.baseUrl}/chat/completions`,
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
            'Authorization': `Bearer ${config.litellm.apiKey}`,
            'Accept': 'text/event-stream',
          },
          responseType: 'stream',
          timeout: 60000, // 60 second timeout
        }
      );
      
      console.log('Stream connection established');

      // Process the stream
      let chunkId = `chatcmpl-${Date.now()}`;
      let model = request.model;
      let accumulatedContent = '';
      
      console.log('Starting stream processing for model:', model);
      
      // Handle the stream data
      const decoder = new TextDecoder();
      let buffer = '';
      
      response.data.on('data', (chunk: Buffer) => {
        buffer += decoder.decode(chunk, { stream: true });
        const lines = buffer.split('\n');
        
        // Keep the last partial line in the buffer
        buffer = lines.pop() || '';
        
        for (const line of lines) {
          if (!line.trim()) continue;
          
          if (!line.startsWith('data: ')) {
            console.log('Unexpected line format:', line);
            continue;
          }
          
          const data = line.substring(6); // Remove 'data: ' prefix
          
          if (data === '[DONE]') {
            console.log('Stream completed');
            res.write('data: [DONE]\n\n');
            return;
          }
          
          try {
            const parsedData = JSON.parse(data);
            
            // Check for error in the response
            if (parsedData.error) {
              console.error('LiteLLM API returned error:', parsedData.error);
              const errorData = {
                error: {
                  message: parsedData.error.message || 'Unknown API error',
                  code: 'LITELLM_API_ERROR',
                  details: parsedData.error
                }
              };
              res.write(`data: ${JSON.stringify(errorData)}\n\n`);
              res.write('data: [DONE]\n\n');
              res.end();
              return;
            }
            
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
                provider: 'litellm',
                content,
                createdAt: new Date().toISOString(),
                isLastChunk: !!finishReason,
              };
              
              if (finishReason) {
                chunkData.finishReason = finishReason;
                console.log('Stream finished. Total content length:', accumulatedContent.length);
              }
              
              // Send the chunk as an SSE event
              res.write(`data: ${JSON.stringify(chunkData)}\n\n`);
            }
          } catch (e: unknown) {
            console.error('Error parsing LiteLLM stream chunk:', e);
            console.error('Raw data:', data);
            
            const errorData = {
              error: {
                message: `Failed to parse stream chunk: ${e instanceof Error ? e.message : 'Unknown error'}`,
                code: 'STREAM_PARSE_ERROR',
                details: { raw: data }
              }
            };
            res.write(`data: ${JSON.stringify(errorData)}\n\n`);
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
        console.error('LiteLLM API Streaming Error:', err);
        
        // Send error as an SSE event
        const errorData = {
          error: {
            message: `LiteLLM API error: ${err.message}`,
            code: 'LITELLM_API_ERROR'
          }
        };
        
        res.write(`data: ${JSON.stringify(errorData)}\n\n`);
        res.write('data: [DONE]\n\n');
        res.end();
      });
    } catch (error: unknown) {
      console.error('LiteLLM API Streaming Error:', error);
      
      // Send error as an SSE event
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      const errorData = {
        error: {
          message: `LiteLLM API error: ${errorMessage}`,
          code: 'LITELLM_API_ERROR'
        }
      };
      
      res.write(`data: ${JSON.stringify(errorData)}\n\n`);
      res.write('data: [DONE]\n\n');
      res.end();
    }
  }

  /**
   * Generate a completion using LiteLLM API
   */
  static async generateCompletion(request: CompletionRequest): Promise<CompletionResponse> {
    try {
      // Create completion request
      const response = await litellmApi.post('/chat/completions', {
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
        provider: 'litellm',
        content: completion,
        usage: {
          promptTokens: data.usage?.prompt_tokens || 0,
          completionTokens: data.usage?.completion_tokens || 0,
          totalTokens: data.usage?.total_tokens || 0,
        },
        createdAt: new Date().toISOString(),
      };
    } catch (error: unknown) {
      console.error('LiteLLM API Error:', error);
      
      // Handle API errors
      if (axios.isAxiosError(error) && error.response) {
        const status = error.response.status;
        const data = error.response.data;
        
        if (status === 401) {
          throw new ApiError(401, 'Invalid LiteLLM API key', 'LITELLM_UNAUTHORIZED');
        } else if (status === 429) {
          throw new ApiError(429, 'LiteLLM rate limit exceeded', 'LITELLM_RATE_LIMIT');
        } else if (status === 400) {
          throw new ApiError(
            400,
            data.error?.message || 'Bad request to LiteLLM API',
            'LITELLM_BAD_REQUEST'
          );
        }
      }
      
      // Generic error
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      throw new ApiError(
        500,
        `LiteLLM API error: ${errorMessage}`,
        'LITELLM_API_ERROR'
      );
    }
  }

  /**
   * Get available models from LiteLLM API
   */
  static async getModels(): Promise<AIModel[]> {
    try {
      if (!config.litellm.apiKey || config.litellm.apiKey === 'your_litellm_api_key_here') {
        return [];
      }
      
      const response = await litellmApi.get('/models');
      const models = response.data.data || [];
      
      // Transform API response to AIModel format
      return models.map((model: LiteLLMModel) => ({
        id: model.id,
        name: model.id.split('-').map((word: string) => word.charAt(0).toUpperCase() + word.slice(1)).join(' '),
        provider: 'litellm',
        description: `${model.owned_by} model`,
        maxTokens: 100000, // Default value as the API doesn't provide this information
      }));
    } catch (error: unknown) {
      console.error('LiteLLM models fetch failed:', error);
      return [];
    }
  }

  /**
   * Check if LiteLLM API is configured and accessible
   */
  static async checkAvailability(): Promise<boolean> {
    try {
      if (!config.litellm.apiKey || config.litellm.apiKey === 'your_litellm_api_key_here') {
        return false;
      }
      
      // Make a simple models list request to check if API is accessible
      const response = await litellmApi.get('/models');
      return response.data && Array.isArray(response.data.data);
    } catch (error: unknown) {
      console.error('LiteLLM availability check failed:', error);
      return false;
    }
  }
}
