// API client configuration using axios
// Configuración base para todos los servicios de API

export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: number;
}

export interface ApiError {
  message: string;
  status: number;
  details?: any;
}

/**
 * Base API client configuration
 * Cliente HTTP centralizado con configuración común
 */
export const apiConfig = {
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8004',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Mock API client for development/testing
 * Cliente mock para desarrollo cuando backend no está disponible
 */
export const mockApiClient = {
  get: async <T>(url: string, params?: any): Promise<ApiResponse<T>> => {
    console.log(`Mock API GET: ${url}`, params);
    
    // Simular delay de red
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Retornar respuesta mock
    return {
      data: {} as T,
      message: 'Mock response',
      status: 200,
    };
  },

  post: async <T>(url: string, data?: any): Promise<ApiResponse<T>> => {
    console.log(`Mock API POST: ${url}`, data);
    
    // Simular delay de red
    await new Promise(resolve => setTimeout(resolve, 800));
    
    return {
      data: {} as T,
      message: 'Mock post successful',
      status: 201,
    };
  },

  put: async <T>(url: string, data?: any): Promise<ApiResponse<T>> => {
    console.log(`Mock API PUT: ${url}`, data);
    
    await new Promise(resolve => setTimeout(resolve, 600));
    
    return {
      data: {} as T,
      message: 'Mock update successful',
      status: 200,
    };
  },

  delete: async <T>(url: string): Promise<ApiResponse<T>> => {
    console.log(`Mock API DELETE: ${url}`);
    
    await new Promise(resolve => setTimeout(resolve, 400));
    
    return {
      data: {} as T,
      message: 'Mock delete successful',
      status: 200,
    };
  },
};

/**
 * Error handling helper
 * Manejo centralizado de errores de API
 */
export const handleApiError = (error: any): ApiError => {
  if (error.response) {
    // Error de respuesta del servidor
    return {
      message: error.response.data?.message || 'Error del servidor',
      status: error.response.status,
      details: error.response.data,
    };
  } else if (error.request) {
    // Error de red
    return {
      message: 'Error de conexión',
      status: 0,
      details: error.request,
    };
  } else {
    // Error de configuración
    return {
      message: error.message || 'Error desconocido',
      status: -1,
      details: error,
    };
  }
};
