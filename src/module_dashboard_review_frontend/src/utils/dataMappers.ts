/**
 * Data mappers for transforming backend responses to frontend domain models
 * 
 * Handles field name conversions from snake_case (backend) to camelCase (frontend)
 * and data type transformations as needed.
 */

import type { Hecho, ArticuloMetadata } from '@/types/domain';

/**
 * Maps backend hecho response to frontend Hecho interface
 */
export function mapHechoFromBackend(backendHecho: any): Hecho {
  // Extract and map articulo metadata
  const articuloMetadata: ArticuloMetadata = mapArticuloMetadataFromBackend(
    backendHecho.articulo_metadata || {}
  );

  // Map main hecho fields
  const mapped: Hecho = {
    // Core identification
    id: backendHecho.id,
    contenido: backendHecho.contenido,

    // Temporal information  
    fechaOcurrencia: backendHecho.fecha_ocurrencia || '',
    precisionTemporal: backendHecho.precision_temporal,

    // Classification and importance
    importancia: backendHecho.importancia,
    tipoHecho: backendHecho.tipo_hecho,

    // Geographic information (ensure arrays)
    pais: Array.isArray(backendHecho.pais) ? backendHecho.pais : 
          backendHecho.pais ? [backendHecho.pais] : undefined,
    region: backendHecho.region,
    ciudad: backendHecho.ciudad,

    // Metadata and tags
    etiquetas: backendHecho.etiquetas,

    // Citation and mention statistics
    frecuenciaCitacion: backendHecho.frecuencia_citacion,
    totalMenciones: backendHecho.total_menciones,
    mencionesConfirmatorias: backendHecho.menciones_confirmatorias,

    // Processing timestamps
    fechaIngreso: backendHecho.fecha_ingreso,

    // Editorial evaluation
    evaluacionEditorial: backendHecho.evaluacion_editorial,
    editorEvaluador: backendHecho.editor_evaluador,
    fechaEvaluacionEditorial: backendHecho.fecha_evaluacion_editorial,
    justificacionEvaluacionEditorial: backendHecho.justificacion_evaluacion_editorial,

    // Source consensus
    consensoFuentes: backendHecho.consenso_fuentes,

    // Future events
    esEventoFuturo: backendHecho.es_evento_futuro,
    estadoProgramacion: backendHecho.estado_programacion,

    // Additional metadata
    metadata: backendHecho.metadata,

    // Article source information
    articuloMetadata
  };

  return mapped;
}

/**
 * Maps backend articulo metadata to frontend ArticuloMetadata interface
 */
export function mapArticuloMetadataFromBackend(backendArticulo: any): ArticuloMetadata {
  return {
    // Basic article info
    medio: backendArticulo.medio || '',
    titular: backendArticulo.titular || '',
    url: backendArticulo.url || '',
    fechaPublicacion: backendArticulo.fecha_publicacion || '',

    // Extended article information
    paisPublicacion: backendArticulo.pais_publicacion,
    tipoMedio: backendArticulo.tipo_medio,
    autor: backendArticulo.autor,
    seccion: backendArticulo.seccion,

    // Content classification
    esOpinion: backendArticulo.es_opinion,
    esOficial: backendArticulo.es_oficial,

    // AI-generated content
    resumen: backendArticulo.resumen,
    categoriasAsignadas: backendArticulo.categorias_asignadas,
    puntuacionRelevancia: backendArticulo.puntuacion_relevancia,

    // Processing status
    estadoProcesamiento: backendArticulo.estado_procesamiento
  };
}

/**
 * Maps an array of backend hechos to frontend format
 */
export function mapHechosFromBackend(backendHechos: any[]): Hecho[] {
  return backendHechos.map(mapHechoFromBackend);
}

/**
 * Maps backend filter options response to frontend format
 */
export function mapFilterOptionsFromBackend(backendOptions: any) {
  return {
    medios: backendOptions.medios_disponibles || [],
    paises: backendOptions.paises_disponibles || [],
    importanciaRange: {
      min: backendOptions.importancia_range?.min || 1,
      max: backendOptions.importancia_range?.max || 10
    }
  };
}

/**
 * Maps frontend filter state to backend query parameters
 */
export function mapFiltersToBackend(frontendFilters: any) {
  const backendParams: any = {};

  // Date filters
  if (frontendFilters.fechaInicio) {
    backendParams.fecha_inicio = frontendFilters.fechaInicio;
  }
  if (frontendFilters.fechaFin) {
    backendParams.fecha_fin = frontendFilters.fechaFin;
  }

  // Content filters
  if (frontendFilters.medio) {
    backendParams.medio = frontendFilters.medio;
  }
  if (frontendFilters.paisPublicacion) {
    backendParams.pais_publicacion = frontendFilters.paisPublicacion;
  }
  if (frontendFilters.tipoHecho) {
    backendParams.tipo_hecho = frontendFilters.tipoHecho;
  }

  // Importance range
  if (frontendFilters.importanciaMin !== undefined) {
    backendParams.importancia_min = frontendFilters.importanciaMin;
  }
  if (frontendFilters.importanciaMax !== undefined) {
    backendParams.importancia_max = frontendFilters.importanciaMax;
  }

  // Editorial evaluation
  if (frontendFilters.evaluacionEditorial) {
    backendParams.evaluacion_editorial = frontendFilters.evaluacionEditorial;
  }

  return backendParams;
}

/**
 * Validates that a backend hecho response has required fields
 */
export function validateBackendHecho(hecho: any): boolean {
  const required = ['id', 'contenido', 'importancia', 'tipo_hecho'];
  return required.every(field => hecho[field] !== undefined && hecho[field] !== null);
}

/**
 * Validates that a backend articulo metadata has required fields
 */
export function validateBackendArticulo(articulo: any): boolean {
  const required = ['medio', 'titular', 'url'];
  return required.every(field => articulo[field] !== undefined && articulo[field] !== null);
}
