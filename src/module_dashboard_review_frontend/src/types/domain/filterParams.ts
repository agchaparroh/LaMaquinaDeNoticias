// Filter parameters for Task 33 implementation
// Parámetros de filtros para la implementación de la tarea 33

/**
 * Filter parameters for the complete filter system
 * Parámetros de filtros para el sistema completo de filtros
 */
export interface FilterParams {
  startDate: Date | null;
  endDate: Date | null;
  source: string;
  country: string;
  importance: number[]; // Range [min, max]
  page: number;
  pageSize: number;
}

/**
 * Default filter parameters
 * Parámetros de filtros por defecto
 */
export const defaultFilters: FilterParams = {
  startDate: null,
  endDate: null,
  source: '',
  country: '',
  importance: [0, 10],
  page: 1,
  pageSize: 10
};

/**
 * Dashboard response with pagination
 * Respuesta del dashboard con paginación
 */
export interface DashboardResponse {
  data: any[]; // Will be replaced with actual Hecho type
  pagination: {
    page: number;
    pageSize: number;
    totalItems: number;
    totalPages: number;
  };
}

/**
 * Filter options available in the system
 * Opciones de filtros disponibles en el sistema
 */
export interface FilterOptionsResponse {
  countries: string[];
  sources: string[];
}
