// Domain types for Hecho entity
// Tipos de dominio para la entidad Hecho (fact)

/**
 * Hecho (News Fact) entity
 * Entidad principal que representa un hecho noticioso extraído
 */
export interface Hecho {
  id: number;
  contenido: string;
  fechaOcurrencia: string;
  importancia: number; // 1-10 scale
  tipoHecho: TipoHecho;
  pais: string;
  evaluacionEditorial?: EvaluacionEditorial;
  creadoEn: string;
  actualizadoEn: string;
  articuloMetadata: ArticuloMetadata;
}

/**
 * Article metadata associated with a Hecho
 * Metadata del artículo que origina el hecho
 */
export interface ArticuloMetadata {
  id: number;
  medio: string;
  titular: string;
  url: string;
  fechaPublicacion: string;
  autor?: string;
  resumen?: string;
  categoria?: string;
}

/**
 * Types of facts/news
 * Tipos de hechos noticiosos
 */
export type TipoHecho = 
  | 'Político'
  | 'Económico'
  | 'Social'
  | 'Internacional'
  | 'Deportivo'
  | 'Cultural'
  | 'Científico'
  | 'Tecnológico'
  | 'Salud'
  | 'Medioambiente'
  | 'Educación'
  | 'Seguridad';

/**
 * Editorial evaluation status
 * Estados de evaluación editorial
 */
export type EvaluacionEditorial = 
  | 'Verificado'
  | 'Falso'
  | 'Dudoso'
  | 'Necesita_Revision'
  | 'Incompleto';

/**
 * Importance scale for facts
 * Escala de importancia para hechos
 */
export type ImportanciaLevel = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10;

/**
 * Editorial feedback data
 * Datos de feedback editorial
 */
export interface FeedbackEditorial {
  hechoId: number;
  evaluacion: EvaluacionEditorial;
  importanciaAnterior: number;
  importanciaNueva: number;
  comentarios?: string;
  revisorId?: string;
  fechaEvaluacion: string;
}

/**
 * Statistics for dashboard
 * Estadísticas para el dashboard
 */
export interface EstadisticasDashboard {
  totalHechos: number;
  hechosPendientes: number;
  hechosVerificados: number;
  hechosFalsos: number;
  importanciaPromedio: number;
  mediosMasActivos: string[];
  tiposHechoFrecuentes: { tipo: TipoHecho; cantidad: number }[];
}
