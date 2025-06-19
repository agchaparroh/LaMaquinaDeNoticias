import { AxiosError } from 'axios';

/**
 * Enumeración de tipos de errores API para categorización
 */
export enum ApiErrorType {
  NETWORK = 'network',
  SERVER = 'server', 
  UNAUTHORIZED = 'unauthorized',
  FORBIDDEN = 'forbidden',
  NOT_FOUND = 'not_found',
  VALIDATION = 'validation',
  RATE_LIMIT = 'rate_limit',
  TIMEOUT = 'timeout',
  UNKNOWN = 'unknown'
}

/**
 * Interfaz para errores API estructurados
 */
export interface ApiError {
  type: ApiErrorType;
  status?: number;
  message: string;
  details?: any;
  timestamp: string;
  supportCode?: string;
}

/**
 * ✅ CORREGIDO: Convierte cualquier error en ApiError estructurado
 * Maneja tanto AxiosError como errores genéricos de forma segura
 */
export const parseApiError = (error: any): ApiError => {
  const timestamp = new Date().toISOString();
  const supportCode = generateSupportCode();

  // ✅ NUEVO: Verificar si es AxiosError específicamente
  if (error?.isAxiosError === true || error?.response || error?.request) {
    return parseAxiosError(error as AxiosError, timestamp, supportCode);
  }

  // ✅ NUEVO: Manejo de errores de AbortController
  if (error?.name === 'AbortError') {
    return {
      type: ApiErrorType.TIMEOUT,
      message: 'Solicitud cancelada por el usuario',
      details: { reason: 'aborted', name: error.name },
      timestamp,
      supportCode
    };
  }

  // ✅ NUEVO: Manejo de errores de red genéricos
  if (error?.code === 'NETWORK_ERROR' || error?.message?.includes('Network Error')) {
    return {
      type: ApiErrorType.NETWORK,
      message: 'Error de red. Verifique su conexión a internet.',
      details: { 
        code: error.code,
        message: error.message,
        type: 'generic_network_error'
      },
      timestamp,
      supportCode
    };
  }

  // ✅ NUEVO: Manejo de errores de timeout genéricos
  if (error?.name === 'TimeoutError' || error?.message?.toLowerCase().includes('timeout')) {
    return {
      type: ApiErrorType.TIMEOUT,
      message: 'La solicitud tardó demasiado en responder',
      details: { 
        name: error.name,
        message: error.message,
        type: 'generic_timeout'
      },
      timestamp,
      supportCode
    };
  }

  // ✅ NUEVO: Manejo de errores de JavaScript/Runtime
  if (error instanceof Error) {
    return {
      type: ApiErrorType.UNKNOWN,
      message: `Error del sistema: ${error.message}`,
      details: { 
        name: error.name,
        stack: import.meta.env.DEV ? error.stack?.split('\n').slice(0, 5) : undefined,
        type: 'javascript_error'
      },
      timestamp,
      supportCode
    };
  }

  // ✅ NUEVO: Fallback para cualquier otro tipo de error
  return {
    type: ApiErrorType.UNKNOWN,
    message: 'Error inesperado del sistema',
    details: { 
      error: typeof error === 'object' ? JSON.stringify(error, null, 2) : String(error),
      type: typeof error,
      isAxiosError: false
    },
    timestamp,
    supportCode
  };
};

/**
 * ✅ NUEVO: Función específica para manejar AxiosError
 */
const parseAxiosError = (error: AxiosError, timestamp: string, supportCode: string): ApiError => {
  // Error de red - no se recibió respuesta
  if (!error.response) {
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      return {
        type: ApiErrorType.TIMEOUT,
        message: 'La solicitud tardó demasiado en responder. Verifique su conexión.',
        details: { 
          code: error.code, 
          message: error.message,
          type: 'axios_timeout'
        },
        timestamp,
        supportCode
      };
    }

    return {
      type: ApiErrorType.NETWORK,
      message: 'Error de conexión. Verifique su conexión a internet.',
      details: { 
        code: error.code,
        message: error.message,
        request: error.request ? 'Request made but no response' : 'Request setup failed',
        type: 'axios_network'
      },
      timestamp,
      supportCode
    };
  }

  // Error con respuesta del servidor
  const status = error.response.status;
  const data = error.response.data as any;

  switch (status) {
    case 400:
      return {
        type: ApiErrorType.VALIDATION,
        status,
        message: data?.message || 'Datos de solicitud inválidos. Verifique la información enviada.',
        details: { 
          ...data,
          type: 'axios_validation'
        },
        timestamp,
        supportCode
      };

    case 401:
      return {
        type: ApiErrorType.UNAUTHORIZED,
        status,
        message: data?.message || 'Sesión expirada. Por favor, inicie sesión nuevamente.',
        details: {
          ...data,
          type: 'axios_unauthorized'
        },
        timestamp,
        supportCode
      };

    case 403:
      return {
        type: ApiErrorType.FORBIDDEN,
        status,
        message: data?.message || 'No tiene permisos para realizar esta acción.',
        details: {
          ...data,
          type: 'axios_forbidden'
        },
        timestamp,
        supportCode
      };

    case 404:
      return {
        type: ApiErrorType.NOT_FOUND,
        status,
        message: data?.message || 'El recurso solicitado no fue encontrado.',
        details: {
          ...data,
          type: 'axios_not_found'
        },
        timestamp,
        supportCode
      };

    case 422:
      return {
        type: ApiErrorType.VALIDATION,
        status,
        message: data?.message || 'Error de validación. Verifique los datos proporcionados.',
        details: {
          ...data,
          type: 'axios_unprocessable'
        },
        timestamp,
        supportCode
      };

    case 429:
      return {
        type: ApiErrorType.RATE_LIMIT,
        status,
        message: data?.message || 'Demasiadas solicitudes. Intente nuevamente en unos minutos.',
        details: {
          ...data,
          type: 'axios_rate_limit',
          retryAfter: error.response.headers?.['retry-after']
        },
        timestamp,
        supportCode
      };

    case 500:
    case 502:
    case 503:
    case 504:
      return {
        type: ApiErrorType.SERVER,
        status,
        message: data?.message || 'Error del servidor. Por favor, intente más tarde.',
        details: {
          ...data,
          type: 'axios_server_error'
        },
        timestamp,
        supportCode
      };

    default:
      return {
        type: ApiErrorType.UNKNOWN,
        status,
        message: data?.message || 'Ocurrió un error inesperado. Por favor, intente nuevamente.',
        details: {
          ...data,
          type: 'axios_unknown'
        },
        timestamp,
        supportCode
      };
  }
};

/**
 * Obtiene mensaje amigable para mostrar al usuario
 */
export const getUserFriendlyErrorMessage = (error: ApiError): string => {
  switch (error.type) {
    case ApiErrorType.NETWORK:
      return '🌐 Sin conexión a internet. Verifique su conexión y vuelva a intentar.';
    
    case ApiErrorType.TIMEOUT:
      return '⏱️ La solicitud tardó demasiado. Intente nuevamente.';
    
    case ApiErrorType.UNAUTHORIZED:
      return '🔐 Su sesión ha expirado. Por favor, inicie sesión nuevamente.';
    
    case ApiErrorType.FORBIDDEN:
      return '🚫 No tiene permisos para realizar esta acción.';
    
    case ApiErrorType.NOT_FOUND:
      return '🔍 No se encontró la información solicitada.';
    
    case ApiErrorType.VALIDATION:
      return '📝 Hay errores en la información. Verifique los datos ingresados.';
    
    case ApiErrorType.RATE_LIMIT:
      return '⏸️ Muchas solicitudes seguidas. Espere un momento antes de continuar.';
    
    case ApiErrorType.SERVER:
      return '🏥 Problema temporal del servidor. Intente en unos minutos.';
    
    default:
      return '❗ Error inesperado. Si persiste, contacte al soporte técnico.';
  }
};

/**
 * Obtiene mensaje técnico detallado para desarrolladores/logs
 */
export const getTechnicalErrorMessage = (error: ApiError): string => {
  const baseMessage = `[${error.type.toUpperCase()}] ${error.message}`;
  const statusInfo = error.status ? ` (HTTP ${error.status})` : '';
  const supportInfo = error.supportCode ? ` | Support Code: ${error.supportCode}` : '';
  
  return `${baseMessage}${statusInfo}${supportInfo}`;
};

/**
 * Determina si el error es recuperable (el usuario puede reintentar)
 */
export const isRetryableError = (error: ApiError): boolean => {
  return [
    ApiErrorType.NETWORK,
    ApiErrorType.TIMEOUT,
    ApiErrorType.SERVER,
    ApiErrorType.RATE_LIMIT
  ].includes(error.type);
};

/**
 * Determina si el error requiere acción del usuario (login, permisos, etc.)
 */
export const requiresUserAction = (error: ApiError): boolean => {
  return [
    ApiErrorType.UNAUTHORIZED,
    ApiErrorType.FORBIDDEN,
    ApiErrorType.VALIDATION
  ].includes(error.type);
};

/**
 * Obtiene el tiempo de espera sugerido antes de reintentar
 */
export const getRetryDelay = (error: ApiError, attempt: number = 1): number => {
  switch (error.type) {
    case ApiErrorType.RATE_LIMIT:
      // ✅ MEJORADO: Usar retry-after header si está disponible
      const retryAfter = error.details?.retryAfter;
      if (retryAfter && !isNaN(parseInt(retryAfter))) {
        return parseInt(retryAfter) * 1000; // Convertir a ms
      }
      return Math.min(30000, 5000 * attempt); // 5s, 10s, 15s, max 30s
    case ApiErrorType.SERVER:
      return Math.min(10000, 2000 * attempt); // 2s, 4s, 6s, max 10s
    case ApiErrorType.NETWORK:
    case ApiErrorType.TIMEOUT:
      return Math.min(5000, 1000 * attempt); // 1s, 2s, 3s, max 5s
    default:
      return 1000; // 1 segundo por defecto
  }
};

/**
 * Genera código de soporte único para tracking de errores
 */
const generateSupportCode = (): string => {
  const timestamp = Date.now().toString(36);
  const random = Math.random().toString(36).substring(2, 7);
  return `${timestamp}-${random}`.toUpperCase();
};

/**
 * ✅ MEJORADO: Logger estructurado para errores API con control de entorno
 */
export const logApiError = (error: ApiError, context?: string): void => {
  // ✅ Solo loggear en desarrollo
  if (!import.meta.env.DEV) {
    // En producción, podrías enviar a un servicio de logging como Sentry
    // sendToErrorTracking(error, context);
    return;
  }

  const contextInfo = context ? `[${context}] ` : '';
  const logMessage = `${contextInfo}${getTechnicalErrorMessage(error)}`;
  
  console.group(`🚨 API Error - ${error.type}`);
  console.error(logMessage);
  console.error('Timestamp:', error.timestamp);
  if (error.supportCode) {
    console.error('Support Code:', error.supportCode);
  }
  if (error.details) {
    console.error('Details:', error.details);
  }
  console.groupEnd();
};

/**
 * ✅ MEJORADO: Utilidad para extraer información detallada del error
 */
export const getDetailedErrorInfo = (error: any): object => {
  try {
    // Si es AxiosError, usar toJSON()
    if (error?.isAxiosError && typeof error.toJSON === 'function') {
      return error.toJSON();
    }
    
    // Para otros errores, crear objeto detallado
    return {
      name: error?.name,
      message: error?.message,
      code: error?.code,
      stack: import.meta.env.DEV ? error?.stack : undefined,
      type: typeof error,
      isAxiosError: error?.isAxiosError || false
    };
  } catch (e) {
    return {
      message: String(error),
      type: typeof error,
      parseError: 'Failed to parse error details'
    };
  }
};

/**
 * ✅ NUEVO: Utilidad para crear errores de desarrollo útiles
 */
export const createDevError = (message: string, details?: any): ApiError => {
  return {
    type: ApiErrorType.UNKNOWN,
    message: `[DEV] ${message}`,
    details: {
      ...details,
      isDevelopmentError: true
    },
    timestamp: new Date().toISOString(),
    supportCode: generateSupportCode()
  };
};

/**
 * ✅ NUEVO: Hook para manejar errores de forma consistente
 */
export const useErrorHandler = () => {
  const handleError = (error: any, context?: string) => {
    const apiError = parseApiError(error);
    logApiError(apiError, context);
    return apiError;
  };

  return { handleError };
};
