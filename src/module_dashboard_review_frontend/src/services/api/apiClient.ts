import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { env } from '@/utils/env';

/**
 * Cliente HTTP base configurado con Axios
 * Incluye interceptores para manejo automático de autenticación y errores
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: env.apiUrl,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
  // Validar solo errores 500+ por defecto
  validateStatus: (status: number) => status < 500,
});

/**
 * Interceptor de Request - Agregar headers de autenticación automáticamente
 */
apiClient.interceptors.request.use(
  (config: AxiosRequestConfig): AxiosRequestConfig => {
    // Agregar token de autorización si está disponible
    const token = localStorage.getItem('auth_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Log de requests en desarrollo
    if (env.isDevelopment() && env.debug) {
      console.log('🚀 API Request:', {
        method: config.method?.toUpperCase(),
        url: config.url,
        baseURL: config.baseURL,
        data: config.data,
        params: config.params,
      });
    }

    return config;
  },
  (error: AxiosError): Promise<AxiosError> => {
    console.error('❌ Request Error:', error.message);
    return Promise.reject(error);
  }
);

/**
 * Interceptor de Response - Manejo automático de errores y logging
 */
apiClient.interceptors.response.use(
  (response: AxiosResponse): AxiosResponse => {
    // Log de responses exitosas en desarrollo
    if (env.isDevelopment() && env.debug) {
      console.log('✅ API Response:', {
        status: response.status,
        statusText: response.statusText,
        url: response.config.url,
        data: response.data,
      });
    }

    return response;
  },
  (error: AxiosError): Promise<AxiosError> => {
    // Manejo centralizado de errores
    if (error.response) {
      // El servidor respondió con un código de error
      const status = error.response.status;
      const data = error.response.data;

      switch (status) {
        case 401:
          console.error('🔐 Unauthorized access - Token expired or invalid');
          // Limpiar token inválido
          localStorage.removeItem('auth_token');
          // En futuro: redirigir a login o refrescar token
          break;
        case 403:
          console.error('🚫 Forbidden access to resource');
          break;
        case 404:
          console.error('🔍 Resource not found');
          break;
        case 422:
          console.error('📝 Validation error:', data);
          break;
        case 429:
          console.error('⏱️ Rate limit exceeded');
          break;
        case 500:
        case 502:
        case 503:
        case 504:
          console.error('🏥 Server error:', status, error.message);
          break;
        default:
          console.error('❗ Unexpected error:', status, error.message);
      }

      // Log detallado en desarrollo
      if (env.isDevelopment()) {
        console.error('📊 Error Details:', {
          status: error.response.status,
          statusText: error.response.statusText,
          data: error.response.data,
          headers: error.response.headers,
          config: {
            method: error.config?.method,
            url: error.config?.url,
            data: error.config?.data,
          },
        });
      }
    } else if (error.request) {
      // La request se hizo pero no hubo respuesta
      console.error('🌐 No response received from server - Check network connection');
      if (env.isDevelopment()) {
        console.error('Request details:', error.request);
      }
    } else {
      // Error en la configuración de la request
      console.error('⚙️ Error setting up the request:', error.message);
    }

    return Promise.reject(error);
  }
);

export default apiClient;