/**
 * Barrel exports para servicios API
 * Exporta el cliente base y todos los servicios específicos
 */

// Cliente base HTTP
export { default as apiClient } from './apiClient';

// Servicios específicos
export { feedbackApi } from './feedbackApi';

// Endpoints y utilidades
export { API_ENDPOINTS, buildUrl, buildQueryParams } from './endpoints';
export type { PaginationParams, SortParams, FilterParams } from './endpoints';

// Tipos de respuesta API
export interface ApiResponse<T = any> {
  data: T;
  success: boolean;
  message?: string;
  timestamp?: string;
  errors?: string[];
}

// Re-export de utilidades de manejo de errores para conveniencia
export {
  parseApiError,
  getUserFriendlyErrorMessage,
  getTechnicalErrorMessage,
  isRetryableError,
  requiresUserAction,
  getRetryDelay,
  logApiError,
  getDetailedErrorInfo,
  ApiErrorType,
  type ApiError
} from '../../utils/api/errorHandling';
