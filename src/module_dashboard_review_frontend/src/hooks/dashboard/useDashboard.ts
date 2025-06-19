import { useState, useEffect, useCallback, useRef } from 'react';
import { dashboardApi } from '@/services/dashboard';
import { parseApiError, getUserFriendlyErrorMessage, isRetryableError, logApiError } from '@/utils/api/errorHandling';
import type { 
  Hecho, 
  FilterState, 
  PaginationParams, 
  ApiError,
  DashboardStats
} from '@/types/domain';

/**
 * Estado del hook useDashboard
 */
interface DashboardState {
  hechos: Hecho[];
  loading: boolean;
  error: ApiError | null;
  pagination: PaginationParams & {
    totalItems: number;
    totalPages: number;
    hasNextPage: boolean;
    hasPreviousPage: boolean;
  };
  stats: DashboardStats | null;
  lastFetch: Date | null;
}

/**
 * Opciones de configuración para el hook
 */
interface UseDashboardOptions {
  filters?: FilterState;
  autoRefresh?: boolean;
}

/**
 * Hook optimizado para el dashboard
 * ✅ CORREGIDO: Eliminado bucle infinito usando useRef para valores estables
 */
export function useDashboard(options: UseDashboardOptions = {}) {
  const {
    filters = {
      medio: '',
      paisPublicacion: '',
      tipoHecho: '',
      evaluacionEditorial: '',
      fechaInicio: null,
      fechaFin: null,
      importanciaMin: null
    },
    autoRefresh = false
  } = options;

  // ✅ NUEVO: Referencias estables para evitar bucles infinitos
  const filtersRef = useRef(filters);
  const requestAbortControllerRef = useRef<AbortController | null>(null);

  // Estado principal del dashboard
  const [state, setState] = useState<DashboardState>({
    hechos: [],
    loading: false,
    error: null,
    pagination: {
      page: 1,
      pageSize: 10,
      totalItems: 0,
      totalPages: 0,
      hasNextPage: false,
      hasPreviousPage: false
    },
    stats: null,
    lastFetch: null
  });

  // ✅ NUEVO: Actualizar referencias de forma controlada
  useEffect(() => {
    filtersRef.current = filters;
  }, [filters]);

  /**
   * ✅ CORREGIDO: Fetch de hechos sin dependencias que causen bucles
   */
  const fetchHechos = useCallback(async (customPage?: number) => {
    // Cancelar request anterior si existe
    if (requestAbortControllerRef.current) {
      requestAbortControllerRef.current.abort();
    }

    // Crear nuevo abort controller
    const abortController = new AbortController();
    requestAbortControllerRef.current = abortController;

    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const currentFilters = filtersRef.current;
      const currentPage = customPage || state.pagination.page;
      
      const response = await dashboardApi.getHechos(currentFilters, {
        page: currentPage,
        limit: state.pagination.pageSize
      }, { signal: abortController.signal });
      
      // ✅ Verificar si el request fue cancelado
      if (abortController.signal.aborted) {
        return;
      }

      const { hechos, pagination: paginationData } = response.data;
      
      setState(prev => ({
        ...prev,
        hechos,
        loading: false,
        error: null,
        pagination: {
          ...prev.pagination,
          page: currentPage,
          totalItems: paginationData.totalItems,
          totalPages: paginationData.totalPages,
          hasNextPage: paginationData.hasNextPage,
          hasPreviousPage: paginationData.hasPreviousPage
        },
        lastFetch: new Date()
      }));
      
    } catch (error: any) {
      // ✅ Ignorar errores de requests cancelados
      if (error?.name === 'AbortError') {
        return;
      }

      const apiError = parseApiError(error);
      
      // ✅ MEJORADO: Solo loggear en desarrollo
      if (import.meta.env.DEV) {
        console.error('❌ Error fetching hechos:', error);
      }
      logApiError(apiError, 'fetchHechos');
      
      setState(prev => ({
        ...prev,
        loading: false,
        error: apiError,
        hechos: prev.hechos, // Mantener datos anteriores en caso de error
      }));
    } finally {
      requestAbortControllerRef.current = null;
    }
  }, []); // ✅ Sin dependencias problemáticas

  /**
   * ✅ CORREGIDO: Fetch de estadísticas optimizado
   */
  const fetchStats = useCallback(async () => {
    try {
      const response = await dashboardApi.getDashboardStats();
      setState(prev => ({ ...prev, stats: response.data }));
    } catch (error: any) {
      const apiError = parseApiError(error);
      
      // ✅ CORREGIDO: Solo loggear en desarrollo
      if (import.meta.env.DEV) {
        console.warn('⚠️ Failed to fetch dashboard stats:', error);
      }
      logApiError(apiError, 'fetchStats');
    }
  }, []);

  /**
   * ✅ MEJORADO: Navegación de páginas optimizada
   */
  const changePage = useCallback((newPage: number) => {
    setState(prev => ({
      ...prev,
      pagination: { ...prev.pagination, page: newPage }
    }));
    
    // ✅ Fetch inmediato con la nueva página
    fetchHechos(newPage);
  }, [fetchHechos]);

  /**
   * ✅ MEJORADO: Refresh manual de datos
   */
  const refreshData = useCallback(() => {
    fetchHechos();
    fetchStats();
  }, [fetchHechos, fetchStats]);

  /**
   * ✅ NUEVO: Cleanup de recursos al desmontar
   */
  useEffect(() => {
    return () => {
      if (requestAbortControllerRef.current) {
        requestAbortControllerRef.current.abort();
      }
    };
  }, []);

  // ✅ CORREGIDO: Fetch inicial controlado
  useEffect(() => {
    fetchHechos();
    fetchStats();
  }, []); // Solo al montar

  // ✅ CORREGIDO: Fetch cuando cambian los filtros (sin bucle)
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      setState(prev => ({
        ...prev,
        pagination: { ...prev.pagination, page: 1 } // Reset a página 1
      }));
      fetchHechos(1); // Fetch con página 1
    }, 100); // Pequeño debounce para evitar múltiples calls

    return () => clearTimeout(timeoutId);
  }, [filters, fetchHechos]);

  // ✅ NUEVO: Auto-refresh opcional
  useEffect(() => {
    if (!autoRefresh) return;

    const intervalId = setInterval(() => {
      refreshData();
    }, 30000); // Refresh cada 30 segundos

    return () => clearInterval(intervalId);
  }, [autoRefresh, refreshData]);

  return {
    // Estado
    hechos: state.hechos,
    loading: state.loading,
    error: state.error,
    stats: state.stats,
    lastFetch: state.lastFetch,
    
    // Paginación
    pagination: state.pagination,
    changePage,
    
    // Utilidades
    refreshData,
    retryLastOperation: () => fetchHechos(),
    
    // Mensajes de error user-friendly
    errorMessage: state.error ? getUserFriendlyErrorMessage(state.error) : null,
    canRetry: state.error ? isRetryableError(state.error) : false,
    
    // Estado derivado
    isEmpty: state.hechos.length === 0 && !state.loading,
    hasData: state.hechos.length > 0,
    
    // ✅ NUEVO: Información de debug (solo en desarrollo)
    ...(import.meta.env.DEV && {
      debug: {
        currentFilters: filtersRef.current,
        rerenderCount: state.lastFetch ? 1 : 0
      }
    })
  };
}

export type { DashboardState, UseDashboardOptions };
