// API endpoints configuration
// Definición centralizada de endpoints del backend

/**
 * API endpoints constants
 * URLs que coinciden exactamente con las rutas del backend FastAPI
 */
export const API_ENDPOINTS = {
  // Dashboard endpoints (sin prefijo /api)
  DASHBOARD: {
    HECHOS_REVISION: '/dashboard/hechos_revision',
    FILTROS_OPCIONES: '/dashboard/filtros/opciones',
  },
  
  // Feedback endpoints (sin prefijo /api)
  FEEDBACK: {
    IMPORTANCIA: (hechoId: number) => `/dashboard/feedback/hecho/${hechoId}/importancia_feedback`,
    EVALUACION_EDITORIAL: (hechoId: number) => `/dashboard/feedback/hecho/${hechoId}/evaluacion_editorial`,
  },
  
  // Health check (sin prefijo /api)
  HEALTH: '/health',
} as const;

/**
 * Query parameters types
 * Tipos para parámetros de consulta comunes
 */
export interface PaginationParams {
  page?: number;
  limit?: number;
  offset?: number;
}

export interface SortParams {
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface FilterParams {
  fechaInicio?: string;
  fechaFin?: string;
  medio?: string;
  paisPublicacion?: string;
  importanciaMin?: number;
  importanciaMax?: number;
  tipoHecho?: string;
}

/**
 * Build query parameters helper
 * Construye query string para requests GET
 */
export const buildQueryParams = (params: Record<string, any>): string => {
  const searchParams = new URLSearchParams();
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.append(key, String(value));
    }
  });
  
  const queryString = searchParams.toString();
  return queryString ? `?${queryString}` : '';
};

/**
 * Build full URL helper
 * Construye URL completa con base y parámetros
 */
export const buildUrl = (endpoint: string, params?: Record<string, any>): string => {
  const queryParams = params ? buildQueryParams(params) : '';
  return `${endpoint}${queryParams}`;
};
