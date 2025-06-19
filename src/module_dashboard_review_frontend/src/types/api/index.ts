// Barrel exports for API types
// Tipos de respuestas API y requests

// API Common types
export type {
  ApiResponse,
  ApiError,
  ApiClientConfig,
  RequestInterceptor,
  ResponseInterceptor
} from './dashboard';

// Dashboard API types
export type {
  GetHechosRequest,
  GetHechosResponse,
  GetFilterOptionsResponse,
  SubmitImportanciaRequest,
  SubmitImportanciaResponse,
  SubmitEvaluacionRequest,
  SubmitEvaluacionResponse
} from './dashboard';