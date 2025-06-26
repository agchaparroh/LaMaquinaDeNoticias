// Common hooks for API operations
// Hook reutilizable para manejo de API calls con estado

import { useState, useCallback } from 'react';
import type { ApiResponse } from '@/services/api';
import { ApiErrorType, type ApiError } from '@/utils/api/errorHandling';

/**
 * Hook states for API operations
 */
export interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: ApiError | null;
}

/**
 * Hook return type for API operations
 */
export interface UseApiReturn<T> {
  data: T | null;
  loading: boolean;
  error: ApiError | null;
  execute: () => Promise<void>;
  reset: () => void;
}

/**
 * Custom hook for handling API calls with loading and error states
 * Hook genérico para manejar API calls con estados de loading y error
 */
export const useApi = <T>(
  apiCall: () => Promise<ApiResponse<T>>
): UseApiReturn<T> => {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const execute = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const response = await apiCall();
      setState({
        data: response.data,
        loading: false,
        error: null,
      });
    } catch (error: any) {
      const apiError: ApiError = {
        type: ApiErrorType.UNKNOWN,
        message: error.message || 'Error desconocido',
        status: error.status || 500,
        details: error,
        timestamp: new Date().toISOString()
      };

      setState({
        data: null,
        loading: false,
        error: apiError,
      });
    }
  }, [apiCall]);

  const reset = useCallback(() => {
    setState({
      data: null,
      loading: false,
      error: null,
    });
  }, []);

  return {
    data: state.data,
    loading: state.loading,
    error: state.error,
    execute,
    reset,
  };
};
