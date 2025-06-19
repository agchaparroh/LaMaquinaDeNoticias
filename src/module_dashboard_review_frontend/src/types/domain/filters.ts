// Domain types for filters
// Tipos de dominio para filtros y búsquedas

import type { TipoHecho, ImportanciaLevel } from './hecho';

/**
 * Filter state for dashboard
 * Estado de filtros del dashboard
 */
export interface DashboardFilters {
  // Date range filters
  fechaInicio?: string;
  fechaFin?: string;
  
  // Content filters
  busquedaTexto?: string;
  tipoHecho?: TipoHecho;
  
  // Source filters
  medio?: string;
  paisPublicacion?: string;
  
  // Importance filters
  importanciaMin?: ImportanciaLevel;
  importanciaMax?: ImportanciaLevel;
  
  // Editorial status filters
  evaluacionEditorial?: 'Todas' | 'Verificado' | 'Falso' | 'Pendiente';
  
  // Advanced filters
  soloSinEvaluar?: boolean;
  ordenarPor?: SortField;
  ordenDireccion?: SortDirection;
}

/**
 * Sort fields available
 * Campos disponibles para ordenamiento
 */
export type SortField = 
  | 'fechaOcurrencia'
  | 'fechaPublicacion'
  | 'importancia'
  | 'medio'
  | 'pais'
  | 'tipoHecho'
  | 'evaluacionEditorial';

/**
 * Sort directions
 * Direcciones de ordenamiento
 */
export type SortDirection = 'asc' | 'desc';

/**
 * Filter options available in the system
 * Opciones de filtros disponibles en el sistema
 */
export interface FilterOptions {
  medios: string[];
  paises: string[];
  tiposHecho: TipoHecho[];
  rangoFechas: {
    fechaMin: string;
    fechaMax: string;
  };
  rangosImportancia: {
    min: ImportanciaLevel;
    max: ImportanciaLevel;
  };
}

/**
 * Active filters summary
 * Resumen de filtros activos
 */
export interface ActiveFiltersState {
  count: number;
  hasDateFilter: boolean;
  hasContentFilter: boolean;
  hasSourceFilter: boolean;
  hasImportanceFilter: boolean;
  hasStatusFilter: boolean;
}

/**
 * Pagination state
 * Estado de paginación
 */
export interface PaginationState {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
  hasNext: boolean;
  hasPrevious: boolean;
}

/**
 * Search and filter result
 * Resultado de búsqueda y filtros
 */
export interface FilteredResults<T> {
  items: T[];
  pagination: PaginationState;
  appliedFilters: DashboardFilters;
  totalUnfiltered: number;
}
