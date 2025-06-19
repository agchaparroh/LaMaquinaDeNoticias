import { useState, useCallback, useRef } from 'react';
import { feedbackApi } from '@/services/api';
import { parseApiError, getUserFriendlyErrorMessage, isRetryableError } from '@/utils/api/errorHandling';
import type { 
  ImportanciaFeedbackRequest,
  ImportanciaFeedbackResponse,
  EvaluacionEditorialRequest,
  EvaluacionEditorialResponse,
  ApiError
} from '@/types/domain';

/**
 * Estado de submission por hecho
 */
interface SubmissionState {
  loading: boolean;
  error: ApiError | null;
  lastSubmission: Date | null;
  retryCount: number;
}

/**
 * Estado interno del hook
 */
interface FeedbackHookState {
  submissions: Record<number, SubmissionState>;
  globalStats: {
    totalSubmissions: number;
    successfulSubmissions: number;
    failedSubmissions: number;
  };
}

/**
 * Opciones de configuración
 */
interface UseFeedbackOptions {
  maxRetries?: number;
  retryDelay?: number;
  enableOptimisticUpdates?: boolean;
  debounceMs?: number;
}

/**
 * Resultado de una operación de feedback
 */
interface FeedbackResult<T = any> {
  success: boolean;
  data?: T;
  error?: ApiError;
  canRetry?: boolean;
}

/**
 * Hook de lógica de negocio para feedback editorial
 * Maneja envío de evaluaciones, importancia y historial de feedback
 */
export function useFeedback(options: UseFeedbackOptions = {}) {
  const {
    maxRetries = 3,
    retryDelay = 2000,
    enableOptimisticUpdates = true,
    debounceMs = 500
  } = options;

  // Estado principal
  const [state, setState] = useState<FeedbackHookState>({
    submissions: {},
    globalStats: {
      totalSubmissions: 0,
      successfulSubmissions: 0,
      failedSubmissions: 0
    }
  });

  // Referencias para debounce
  const debounceTimers = useRef<Record<string, NodeJS.Timeout>>({});
  const abortControllers = useRef<Record<string, AbortController>>({});

  /**
   * Obtener estado de submission para un hecho específico
   */
  const getSubmissionState = useCallback((hechoId: number): SubmissionState => {
    return state.submissions[hechoId] || {
      loading: false,
      error: null,
      lastSubmission: null,
      retryCount: 0
    };
  }, [state.submissions]);

  /**
   * Actualizar estado de submission para un hecho
   */
  const updateSubmissionState = useCallback((
    hechoId: number, 
    updates: Partial<SubmissionState>
  ) => {
    setState(prev => ({
      ...prev,
      submissions: {
        ...prev.submissions,
        [hechoId]: {
          ...getSubmissionState(hechoId),
          ...updates
        }
      }
    }));
  }, [getSubmissionState]);

  /**
   * Cancelar submission en progreso
   */
  const cancelSubmission = useCallback((hechoId: number) => {
    const key = `feedback-${hechoId}`;
    
    // Cancelar timer de debounce
    if (debounceTimers.current[key]) {
      clearTimeout(debounceTimers.current[key]);
      delete debounceTimers.current[key];
    }
    
    // Cancelar request HTTP
    if (abortControllers.current[key]) {
      abortControllers.current[key].abort();
      delete abortControllers.current[key];
    }
    
    // Limpiar estado de loading
    updateSubmissionState(hechoId, { loading: false });
  }, [updateSubmissionState]);

  /**
   * Enviar feedback de importancia
   */
  const submitImportanciaFeedback = useCallback(async (
    hechoId: number,
    request: ImportanciaFeedbackRequest
  ): Promise<FeedbackResult<ImportanciaFeedbackResponse>> => {
    const submissionKey = `importancia-${hechoId}`;
    
    // Cancelar cualquier submission anterior
    cancelSubmission(hechoId);
    
    // Establecer estado de loading
    updateSubmissionState(hechoId, {
      loading: true,
      error: null
    });

    // Actualizar estadísticas globales
    setState(prev => ({
      ...prev,
      globalStats: {
        ...prev.globalStats,
        totalSubmissions: prev.globalStats.totalSubmissions + 1
      }
    }));

    try {
      // Crear AbortController para esta request
      const abortController = new AbortController();
      abortControllers.current[submissionKey] = abortController;

      const response = await feedbackApi.submitImportanciaFeedback(hechoId, request);
      
      // Limpiar controller exitoso
      delete abortControllers.current[submissionKey];
      
      // Actualizar estado exitoso
      updateSubmissionState(hechoId, {
        loading: false,
        error: null,
        lastSubmission: new Date(),
        retryCount: 0
      });

      // Actualizar estadísticas exitosas
      setState(prev => ({
        ...prev,
        globalStats: {
          ...prev.globalStats,
          successfulSubmissions: prev.globalStats.successfulSubmissions + 1
        }
      }));

      console.log(`✅ Importance feedback submitted for hecho ${hechoId}`);
      
      return {
        success: true,
        data: response.data
      };
      
    } catch (error: any) {
      // Si fue cancelada, no procesar el error
      if (error.name === 'AbortError') {
        return { success: false };
      }
      
      const apiError = parseApiError(error);
      const currentState = getSubmissionState(hechoId);
      
      // Actualizar estado de error
      updateSubmissionState(hechoId, {
        loading: false,
        error: apiError,
        retryCount: currentState.retryCount + 1
      });

      // Actualizar estadísticas de fallo
      setState(prev => ({
        ...prev,
        globalStats: {
          ...prev.globalStats,
          failedSubmissions: prev.globalStats.failedSubmissions + 1
        }
      }));

      // Auto-retry si es posible
      const canRetry = isRetryableError(apiError) && currentState.retryCount < maxRetries;
      
      if (canRetry) {
        console.warn(`🔄 Retrying importance feedback for hecho ${hechoId} (attempt ${currentState.retryCount + 1})`);
        
        setTimeout(() => {
          submitImportanciaFeedback(hechoId, request);
        }, retryDelay * Math.pow(2, currentState.retryCount)); // Exponential backoff
      }

      return {
        success: false,
        error: apiError,
        canRetry
      };
    }
  }, [cancelSubmission, updateSubmissionState, getSubmissionState, maxRetries, retryDelay]);

  /**
   * Enviar evaluación editorial
   */
  const submitEvaluacionEditorial = useCallback(async (
    hechoId: number,
    request: EvaluacionEditorialRequest
  ): Promise<FeedbackResult<EvaluacionEditorialResponse>> => {
    const submissionKey = `evaluacion-${hechoId}`;
    
    // Cancelar cualquier submission anterior
    cancelSubmission(hechoId);
    
    // Establecer estado de loading
    updateSubmissionState(hechoId, {
      loading: true,
      error: null
    });

    // Actualizar estadísticas globales
    setState(prev => ({
      ...prev,
      globalStats: {
        ...prev.globalStats,
        totalSubmissions: prev.globalStats.totalSubmissions + 1
      }
    }));

    try {
      // Crear AbortController para esta request
      const abortController = new AbortController();
      abortControllers.current[submissionKey] = abortController;

      const response = await feedbackApi.submitEvaluacionEditorial(hechoId, request);
      
      // Limpiar controller exitoso
      delete abortControllers.current[submissionKey];
      
      // Actualizar estado exitoso
      updateSubmissionState(hechoId, {
        loading: false,
        error: null,
        lastSubmission: new Date(),
        retryCount: 0
      });

      // Actualizar estadísticas exitosas
      setState(prev => ({
        ...prev,
        globalStats: {
          ...prev.globalStats,
          successfulSubmissions: prev.globalStats.successfulSubmissions + 1
        }
      }));

      console.log(`✅ Editorial evaluation submitted for hecho ${hechoId}: ${request.evaluacion}`);
      
      return {
        success: true,
        data: response.data
      };
      
    } catch (error: any) {
      // Si fue cancelada, no procesar el error
      if (error.name === 'AbortError') {
        return { success: false };
      }
      
      const apiError = parseApiError(error);
      const currentState = getSubmissionState(hechoId);
      
      // Actualizar estado de error
      updateSubmissionState(hechoId, {
        loading: false,
        error: apiError,
        retryCount: currentState.retryCount + 1
      });

      // Actualizar estadísticas de fallo
      setState(prev => ({
        ...prev,
        globalStats: {
          ...prev.globalStats,
          failedSubmissions: prev.globalStats.failedSubmissions + 1
        }
      }));

      // Auto-retry si es posible
      const canRetry = isRetryableError(apiError) && currentState.retryCount < maxRetries;
      
      if (canRetry) {
        console.warn(`🔄 Retrying editorial evaluation for hecho ${hechoId} (attempt ${currentState.retryCount + 1})`);
        
        setTimeout(() => {
          submitEvaluacionEditorial(hechoId, request);
        }, retryDelay * Math.pow(2, currentState.retryCount)); // Exponential backoff
      }

      return {
        success: false,
        error: apiError,
        canRetry
      };
    }
  }, [cancelSubmission, updateSubmissionState, getSubmissionState, maxRetries, retryDelay]);

  /**
   * Enviar feedback de importancia con debounce
   */
  const submitImportanciaFeedbackDebounced = useCallback((
    hechoId: number,
    request: ImportanciaFeedbackRequest
  ) => {
    const key = `importancia-debounced-${hechoId}`;
    
    // Limpiar timer anterior
    if (debounceTimers.current[key]) {
      clearTimeout(debounceTimers.current[key]);
    }
    
    // Establecer nuevo timer
    debounceTimers.current[key] = setTimeout(() => {
      submitImportanciaFeedback(hechoId, request);
      delete debounceTimers.current[key];
    }, debounceMs);
  }, [submitImportanciaFeedback, debounceMs]);

  /**
   * Obtener historial de feedback para un hecho
   */
  const getFeedbackHistory = useCallback(async (hechoId: number) => {
    try {
      const response = await feedbackApi.getFeedbackHistory(hechoId);
      return response.data;
    } catch (error: any) {
      console.error(`❌ Failed to fetch feedback history for hecho ${hechoId}:`, error);
      return [];
    }
  }, []);

  /**
   * Obtener estadísticas de feedback del usuario
   */
  const getUserFeedbackStats = useCallback(async () => {
    try {
      const response = await feedbackApi.getUserFeedbackStats();
      return response.data;
    } catch (error: any) {
      console.error('❌ Failed to fetch user feedback stats:', error);
      return null;
    }
  }, []);

  /**
   * Limpiar errores para un hecho específico
   */
  const clearError = useCallback((hechoId: number) => {
    updateSubmissionState(hechoId, { error: null });
  }, [updateSubmissionState]);

  /**
   * Limpiar todos los errores
   */
  const clearAllErrors = useCallback(() => {
    setState(prev => ({
      ...prev,
      submissions: Object.fromEntries(
        Object.entries(prev.submissions).map(([id, state]) => [
          id,
          { ...state, error: null }
        ])
      )
    }));
  }, []);

  /**
   * Retry manual de una submission fallida
   */
  const retrySubmission = useCallback((hechoId: number) => {
    const submissionState = getSubmissionState(hechoId);
    
    if (submissionState.error && !submissionState.loading) {
      // Reset retry count para permitir retry manual
      updateSubmissionState(hechoId, { retryCount: 0 });
      
      // Aquí deberías implementar la lógica para re-enviar el último feedback
      // Esto requeriría almacenar el tipo de feedback y los datos originales
      console.log(`🔄 Manual retry requested for hecho ${hechoId}`);
    }
  }, [getSubmissionState, updateSubmissionState]);

  /**
   * Reiniciar estadísticas globales
   */
  const resetGlobalStats = useCallback(() => {
    setState(prev => ({
      ...prev,
      globalStats: {
        totalSubmissions: 0,
        successfulSubmissions: 0,
        failedSubmissions: 0
      }
    }));
  }, []);

  // Cleanup al desmontar
  const cleanup = useCallback(() => {
    // Limpiar todos los timers
    Object.values(debounceTimers.current).forEach(timer => clearTimeout(timer));
    debounceTimers.current = {};
    
    // Cancelar todas las requests
    Object.values(abortControllers.current).forEach(controller => controller.abort());
    abortControllers.current = {};
  }, []);

  return {
    // Acciones principales
    submitImportanciaFeedback,
    submitEvaluacionEditorial,
    submitImportanciaFeedbackDebounced,
    
    // Estado por hecho
    getSubmissionState,
    isSubmitting: (hechoId: number) => getSubmissionState(hechoId).loading,
    hasError: (hechoId: number) => !!getSubmissionState(hechoId).error,
    getError: (hechoId: number) => getSubmissionState(hechoId).error,
    getErrorMessage: (hechoId: number) => {
      const error = getSubmissionState(hechoId).error;
      return error ? getUserFriendlyErrorMessage(error) : null;
    },
    canRetry: (hechoId: number) => {
      const submissionState = getSubmissionState(hechoId);
      return submissionState.error ? isRetryableError(submissionState.error) : false;
    },
    
    // Gestión de errores
    clearError,
    clearAllErrors,
    retrySubmission,
    
    // Utilidades
    cancelSubmission,
    getFeedbackHistory,
    getUserFeedbackStats,
    
    // Estadísticas globales
    globalStats: state.globalStats,
    resetGlobalStats,
    
    // Cleanup
    cleanup,
    
    // Estado derivado
    hasAnySubmissions: Object.keys(state.submissions).length > 0,
    hasAnyErrors: Object.values(state.submissions).some(s => s.error),
    hasAnyLoading: Object.values(state.submissions).some(s => s.loading),
    successRate: state.globalStats.totalSubmissions > 0 
      ? (state.globalStats.successfulSubmissions / state.globalStats.totalSubmissions) * 100 
      : 0
  };
}

export type { UseFeedbackOptions, FeedbackResult, SubmissionState };
