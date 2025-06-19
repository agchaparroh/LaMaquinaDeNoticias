// Dashboard Domain Types
// Tipos principales para el sistema de revisión editorial

export interface ArticuloMetadata {
  // Basic article info
  medio: string;
  titular: string;
  url: string;
  fechaPublicacion: string;
  
  // Extended article information
  paisPublicacion?: string;
  tipoMedio?: string;
  autor?: string;
  seccion?: string;
  
  // Content classification
  esOpinion?: boolean;
  esOficial?: boolean;
  
  // AI-generated content
  resumen?: string;
  categoriasAsignadas?: string[];
  puntuacionRelevancia?: number;
  
  // Processing status
  estadoProcesamiento?: string;
}

export interface Hecho {
  // Core fact identification
  id: number;
  contenido: string;
  
  // Temporal information
  fechaOcurrencia: string;
  precisionTemporal?: string;
  
  // Classification and importance
  importancia: number; // 1-10
  tipoHecho: string;
  
  // Geographic information (flexible: string or arrays)
  pais?: string | string[];
  region?: string[];
  ciudad?: string[];
  
  // Metadata and tags
  etiquetas?: string[];
  
  // Citation and mention statistics
  frecuenciaCitacion?: number;
  totalMenciones?: number;
  mencionesConfirmatorias?: number;
  
  // Processing timestamps
  fechaIngreso?: string;
  
  // Editorial evaluation (expanded)
  evaluacionEditorial?: 'pendiente_revision_editorial' | 'verificado_ok_editorial' | 'declarado_falso_editorial';
  editorEvaluador?: string;
  fechaEvaluacionEditorial?: string;
  justificacionEvaluacionEditorial?: string;
  
  // Source consensus
  consensoFuentes?: string;
  
  // Future events
  esEventoFuturo?: boolean;
  estadoProgramacion?: string;
  
  // Additional metadata (flexible object)
  metadata?: Record<string, any>;
  
  // Article source information
  articuloMetadata: ArticuloMetadata;
  
  // UI-specific fields
  isLoading?: boolean;
  error?: string;
}

export interface FilterState {
  // Date filters
  fechaInicio?: Date | null;
  fechaFin?: Date | null;
  
  // Content filters
  medio?: string;
  paisPublicacion?: string;  // Note: This filters pais array in backend
  tipoHecho?: string;
  
  // Importance range
  importanciaMin?: number;
  importanciaMax?: number;
  
  // Editorial evaluation (updated values)
  evaluacionEditorial?: 'pendiente_revision_editorial' | 'verificado_ok_editorial' | 'declarado_falso_editorial' | 'sin_evaluar' | '';
  
  // Extended filters (for future use)
  esEventoFuturo?: boolean;
  consensoFuentes?: string;
  tipoMedio?: string;
}

export interface PaginationParams {
  page: number;
  pageSize: number;
  totalItems?: number;
  totalPages?: number;
  hasNextPage?: boolean;
  hasPreviousPage?: boolean;
}

export interface DashboardState {
  hechos: Hecho[];
  filters: FilterState;
  pagination: PaginationParams;
  loading: boolean;
  error: string | null;
  selectedHecho?: Hecho | null;
}

// Tipos para opciones de filtros (para dropdowns)
export interface FilterOptions {
  medios: string[];
  paises: string[];
  tiposHecho: string[];
  evaluacionesEditoriales: string[];
}

// Estadísticas del dashboard
export interface DashboardStats {
  totalHechos: number;
  hechosPorEvaluacion: {
    verdadero: number;
    falso: number;
    necesita_verificacion: number;
    sin_evaluar: number;
  };
  importanciaPromedio: number;
}

// Export de constantes útiles
export const IMPORTANCIA_MIN = 1;
export const IMPORTANCIA_MAX = 10;
export const DEFAULT_PAGE_SIZE = 20;

export const EVALUACION_OPTIONS = [
  'pendiente_revision_editorial',
  'verificado_ok_editorial',
  'declarado_falso_editorial'
] as const;

export type EvaluacionEditorial = typeof EVALUACION_OPTIONS[number];

// Additional type constants
export const PRECISION_TEMPORAL_OPTIONS = [
  'exacta', 'dia', 'semana', 'mes', 'trimestre', 'año', 'decada', 'periodo'
] as const;

export const TIPO_HECHO_OPTIONS = [
  'SUCESO', 'ANUNCIO', 'DECLARACION', 'BIOGRAFIA', 'CONCEPTO', 'NORMATIVA', 'EVENTO'
] as const;

export const CONSENSO_FUENTES_OPTIONS = [
  'pendiente_analisis_fuentes',
  'confirmado_multiples_fuentes', 
  'sin_confirmacion_suficiente_fuentes',
  'en_disputa_por_hechos_contradictorios'
] as const;

export type PrecisionTemporal = typeof PRECISION_TEMPORAL_OPTIONS[number];
export type TipoHecho = typeof TIPO_HECHO_OPTIONS[number];
export type ConsensoFuentes = typeof CONSENSO_FUENTES_OPTIONS[number];