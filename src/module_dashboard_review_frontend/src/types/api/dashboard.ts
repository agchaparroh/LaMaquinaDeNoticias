// API Types
// Tipos para requests y responses de la API

import type { 
  Hecho, 
  FilterState, 
  PaginationParams,
  ImportanciaFeedbackRequest,
  ImportanciaFeedbackResponse,
  EvaluacionEditorialRequest,
  EvaluacionEditorialResponse 
} from '../domain';

// API Response wrapper genérico
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
  timestamp: string;
}

// API Error response
export interface ApiError {
  error: string;
  message: string;
  statusCode: number;
  timestamp: string;
  path?: string;
}

// Dashboard API types
export interface GetHechosRequest {
  filters?: Partial<FilterState>;
  pagination?: Partial<PaginationParams>;
}

export interface GetHechosResponse {
  hechos: Hecho[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
  appliedFilters: FilterState;
}

export interface GetFilterOptionsResponse {
  medios: string[];
  paises: string[];
  tiposHecho: string[];
}

// Feedback API types
export type SubmitImportanciaRequest = ImportanciaFeedbackRequest;
export type SubmitImportanciaResponse = ImportanciaFeedbackResponse;

export type SubmitEvaluacionRequest = EvaluacionEditorialRequest;
export type SubmitEvaluacionResponse = EvaluacionEditorialResponse;

// API client configuration
export interface ApiClientConfig {
  baseURL: string;
  timeout: number;
  retries: number;
  headers?: Record<string, string>;
}

// Request/Response interceptor types
export interface RequestInterceptor {
  onRequest?: (config: any) => any;
  onRequestError?: (error: any) => Promise<any>;
}

export interface ResponseInterceptor {
  onResponse?: (response: any) => any;
  onResponseError?: (error: any) => Promise<any>;
}