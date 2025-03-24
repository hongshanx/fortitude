import { Request, Response, NextFunction } from 'express';
import { ZodError, z } from 'zod';
import { config } from '../config/env.js';

// Custom error class
export class ApiError extends Error {
  statusCode: number;
  code: string;
  
  constructor(statusCode: number, message: string, code: string = 'INTERNAL_ERROR') {
    super(message);
    this.statusCode = statusCode;
    this.code = code;
    Error.captureStackTrace(this, this.constructor);
  }
}

// Error handler middleware
export const errorHandler = (
  err: Error,
  req: Request,
  res: Response,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  next: NextFunction
) => {
  console.error('Error:', err);
  
  // Default error
  let statusCode = 500;
  let message = 'Internal Server Error';
  let errorCode = 'INTERNAL_ERROR';
  
  // Handle specific error types
  if (err instanceof ApiError) {
    statusCode = err.statusCode;
    message = err.message;
    errorCode = err.code;
  } else if (err instanceof ZodError) {
    statusCode = 400;
    message = 'Validation Error';
    errorCode = 'VALIDATION_ERROR';
  } else if (err.name === 'SyntaxError') {
    statusCode = 400;
    message = 'Invalid JSON';
    errorCode = 'INVALID_JSON';
  }
  
  // Send error response
  res.status(statusCode).json({
    error: {
      message,
      code: errorCode,
      details: err instanceof ZodError ? err.errors : undefined,
      stack: config.server.isDev ? err.stack : undefined,
    },
  });
};

// Not found middleware
export const notFound = (req: Request, res: Response) => {
  res.status(404).json({
    error: {
      message: `Not Found - ${req.originalUrl}`,
      code: 'NOT_FOUND',
    },
  });
};

// Validation middleware
export const validateRequest = (schema: z.ZodSchema) => {
  return (req: Request, res: Response, next: NextFunction) => {
    try {
      req.body = schema.parse(req.body);
      next();
    } catch (error) {
      next(error);
    }
  };
};
