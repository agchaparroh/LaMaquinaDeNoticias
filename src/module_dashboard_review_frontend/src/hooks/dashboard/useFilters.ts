import { useState, useCallback, useMemo, useEffect } from 'react';
import { dashboardApi } from '@/services/dashboard';
import type { FilterState, FilterOptions } from '@/types/domain';

/**
 * Configuración del hook useFilters
 */
interface UseFiltersOptions {
  initialFilters?: Partial<FilterState>;
  autoLoadOptions?: boolean;
}

/**
 * Estado interno del hook
 */
interface FiltersHookState {
  filters: FilterState;
  options: FilterOptions | null;
  optionsLoading: boolean;
  optionsError: string | null;
  filtersHistory: FilterState[];
}

/**
 * Hook de lógica de negocio para manejo de filtros
 * Encapsula toda la lógica de filtrado, opciones dinámicas (sin localStorage)
 */
export function useFilters(options: UseFiltersOptions = {}) {
  const {
    initialFilters = {},
    autoLoadOptions = true
  } = options;

  /**
   * Filtros por defecto
   */
  function getDefaultFilters(): FilterState {
    return {
      medio: '',
      areaGeografica: '',
      tipoHecho: '',
      evaluacionEditorial: '',
      fechaInicio: null,
      fechaFin: null,
      importanciaMin: undefined
    };
  }

  // Estado principal (solo en memoria)
  const [state, setState] = useState<FiltersHookState>({
    filters: { ...getDefaultFilters(), ...initialFilters },
    options: null,
    optionsLoading: false,
    optionsError: null,
    filtersHistory: []
  });

  /**
   * Actualizar un filtro específico
   */
  const updateFilter = useCallback(<K extends keyof FilterState>(
    key: K,
    value: FilterState[K]
  ) => {
    setState(prev => {
      const newFilters = { ...prev.filters, [key]: value };
      
      // Agregar al historial
      const newHistory = [prev.filters, ...prev.filtersHistory.slice(0, 9)]; // Mantener últimos 10
      
      return {
        ...prev,
        filters: newFilters,
        filtersHistory: newHistory
      };
    });
  }, []);

  /**
   * Actualizar múltiples filtros a la vez
   */
  const updateFilters = useCallback((updates: Partial<FilterState>) => {
    setState(prev => {
      const newFilters = { ...prev.filters, ...updates };
      
      // Agregar al historial solo si hay cambios significativos
      const hasSignificantChanges = Object.keys(updates).some(
        key => updates[key as keyof FilterState] !== prev.filters[key as keyof FilterState]
      );
      
      const newHistory = hasSignificantChanges
        ? [prev.filters, ...prev.filtersHistory.slice(0, 9)]
        : prev.filtersHistory;
      
      return {
        ...prev,
        filters: newFilters,
        filtersHistory: newHistory
      };
    });
  }, []);

  /**
   * Limpiar filtros específicos
   */
  const clearFilter = useCallback(<K extends keyof FilterState>(key: K) => {
    const defaultValue = getDefaultFilters()[key];
    updateFilter(key, defaultValue);
  }, [updateFilter]);

  /**
   * Limpiar todos los filtros
   */
  const clearAllFilters = useCallback(() => {
    const defaultFilters = getDefaultFilters();
    setState(prev => ({
      ...prev,
      filters: defaultFilters,
      filtersHistory: [prev.filters, ...prev.filtersHistory.slice(0, 9)]
    }));
  }, []);

  /**
   * Restaurar filtros desde el historial
   */
  const restoreFromHistory = useCallback((index: number) => {
    if (index >= 0 && index < state.filtersHistory.length) {
      const historicalFilters = state.filtersHistory[index];
      setState(prev => ({
        ...prev,
        filters: historicalFilters,
        // Reorganizar historial
        filtersHistory: [
          prev.filters,
          ...prev.filtersHistory.filter((_, i) => i !== index).slice(0, 8)
        ]
      }));
    }
  }, [state.filtersHistory]);

  /**
   * Establecer filtros predefinidos
   */
  const applyPreset = useCallback((preset: {
    name: string;
    filters: Partial<FilterState>;
  }) => {
    console.log(`📋 Applying filter preset: ${preset.name}`);
    updateFilters(preset.filters);
  }, [updateFilters]);

  /**
   * Cargar opciones dinámicas para filtros
   */
  const loadFilterOptions = useCallback(async () => {
    setState(prev => ({ ...prev, optionsLoading: true, optionsError: null }));
    
    try {
      const response = await dashboardApi.getFilterOptions();
      const filterOptions: FilterOptions = {
        medios: response.data?.medios || [],
        paises: response.data?.paises || [],
        tiposHecho: response.data?.tiposHecho || [],
        evaluacionesEditoriales: ['pendiente_revision_editorial', 'verificado_ok_editorial', 'declarado_falso_editorial', 'sin_evaluar']
      };
      setState(prev => ({
        ...prev,
        options: filterOptions,
        optionsLoading: false,
        optionsError: null
      }));
    } catch (error: any) {
      console.error('❌ Failed to load filter options:', error);
      setState(prev => ({
        ...prev,
        optionsLoading: false,
        optionsError: error.message || 'Error loading filter options'
      }));
    }
  }, []);

  /**
   * Validar filtros actuales
   */
  const validateFilters = useCallback(() => {
    const { filters } = state;
    const errors: Record<string, string> = {};

    // Validar rango de fechas
    if (filters.fechaInicio && filters.fechaFin) {
      if (filters.fechaInicio > filters.fechaFin) {
        errors.dateRange = 'La fecha de inicio debe ser anterior a la fecha de fin';
      }
    }

    // Validar importancia mínima
    if (filters.importanciaMin !== undefined && filters.importanciaMin !== null) {
      if (filters.importanciaMin < 1 || filters.importanciaMin > 10) {
        errors.importancia = 'La importancia debe estar entre 1 y 10';
      }
    }

    return {
      isValid: Object.keys(errors).length === 0,
      errors
    };
  }, [state.filters]);

  // Valores computados y memoizados
  const computedValues = useMemo(() => {
    const { filters } = state;
    
    // Verificar si hay filtros activos
    const hasActiveFilters = Object.entries(filters).some(([key, value]) => {
      const defaultValue = getDefaultFilters()[key as keyof FilterState];
      return value !== defaultValue && value !== null && value !== undefined && value !== '';
    });

    // Contar filtros activos
    const activeFiltersCount = Object.entries(filters).filter(([key, value]) => {
      const defaultValue = getDefaultFilters()[key as keyof FilterState];
      return value !== defaultValue && value !== null && value !== undefined && value !== '';
    }).length;

    // Generar resumen de filtros activos
    const activeFiltersSummary = Object.entries(filters)
      .filter(([_, value]) => value !== null && value !== undefined && value !== '')
      .map(([key, value]) => {
        const displayKey = key.replace(/([A-Z])/g, ' $1').toLowerCase();
        return `${displayKey}: ${value}`;
      });

    // Verificar si los filtros han cambiado desde la carga inicial
    const hasChangedFromInitial = JSON.stringify(filters) !== JSON.stringify({
      ...getDefaultFilters(),
      ...initialFilters
    });

    return {
      hasActiveFilters,
      activeFiltersCount,
      activeFiltersSummary,
      hasChangedFromInitial,
      canClear: hasActiveFilters,
      canRestore: state.filtersHistory.length > 0
    };
  }, [state.filters, state.filtersHistory.length, initialFilters]);

  // Presets comunes de filtros
  const commonPresets = useMemo(() => [
    {
      name: 'Sin evaluar',
      filters: { evaluacionEditorial: 'sin_evaluar' }
    },
    {
      name: 'Verificados como verdaderos',
      filters: { evaluacionEditorial: 'verdadero' }
    },
    {
      name: 'Marcados como falsos',
      filters: { evaluacionEditorial: 'falso' }
    },
    {
      name: 'Necesitan verificación',
      filters: { evaluacionEditorial: 'necesita_verificacion' }
    },
    {
      name: 'Alta importancia',
      filters: { importanciaMin: 8 }
    },
    {
      name: 'Última semana',
      filters: {
        fechaInicio: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
        fechaFin: new Date()
      }
    }
  ], []);

  // Auto-cargar opciones al montar
  useEffect(() => {
    if (autoLoadOptions) {
      loadFilterOptions();
    }
  }, [autoLoadOptions, loadFilterOptions]);

  return {
    // Estado principal
    filters: state.filters,
    options: state.options,
    
    // Estado de carga de opciones
    optionsLoading: state.optionsLoading,
    optionsError: state.optionsError,
    
    // Acciones de filtros
    updateFilter,
    updateFilters,
    clearFilter,
    clearAllFilters,
    
    // Historial
    filtersHistory: state.filtersHistory,
    restoreFromHistory,
    
    // Presets
    commonPresets,
    applyPreset,
    
    // Utilidades
    loadFilterOptions,
    reloadOptions: loadFilterOptions,
    validation: validateFilters(),
    
    // Valores computados
    ...computedValues,
    
    // Helpers específicos por tipo de filtro
    setDateRange: (inicio: Date | null, fin: Date | null) => {
      updateFilters({ fechaInicio: inicio, fechaFin: fin });
    },
    
    clearDateRange: () => {
      updateFilters({ fechaInicio: null, fechaFin: null });
    },
    
    toggleEvaluacion: (evaluacion: string) => {
      const currentEval = state.filters.evaluacionEditorial;
      updateFilter('evaluacionEditorial', currentEval === evaluacion ? '' : evaluacion as FilterState['evaluacionEditorial']);
    },
    
    setImportanceRange: (min: number | null) => {
      updateFilter('importanciaMin', min === null ? undefined : min);
    }
  };
}

export type { UseFiltersOptions, FiltersHookState };
