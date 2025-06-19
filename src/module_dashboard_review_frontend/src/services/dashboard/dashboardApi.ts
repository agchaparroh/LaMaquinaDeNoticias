// Dashboard API service
// Servicios específicos para las APIs del dashboard de revisión editorial

import apiClient from '@/services/api/apiClient';
import { API_ENDPOINTS, buildUrl } from '@/services/api/endpoints';
import type { ApiResponse } from '@/services/api';
import type { Hecho, FilterState } from '@/types/domain';
import { mockHechos, mockFilterOptions, generateMockHechos } from '@/utils/mocks';
import { 
  mapHechosFromBackend, 
  mapHechoFromBackend,
  mapFilterOptionsFromBackend, 
  mapFiltersToBackend 
} from '@/utils/dataMappers';
import { env } from '@/utils/env';

/**
 * Convierte datos mock del frontend al formato backend
 */
function convertMockToBackendFormat(mockHecho: Hecho): any {
  return {
    id: mockHecho.id,
    contenido: mockHecho.contenido,
    fecha_ocurrencia: mockHecho.fechaOcurrencia,
    precision_temporal: mockHecho.precisionTemporal,
    importancia: mockHecho.importancia,
    tipo_hecho: mockHecho.tipoHecho,
    pais: mockHecho.pais,
    region: mockHecho.region,
    ciudad: mockHecho.ciudad,
    etiquetas: mockHecho.etiquetas,
    frecuencia_citacion: mockHecho.frecuenciaCitacion,
    total_menciones: mockHecho.totalMenciones,
    menciones_confirmatorias: mockHecho.mencionesConfirmatorias,
    fecha_ingreso: mockHecho.fechaIngreso,
    evaluacion_editorial: mockHecho.evaluacionEditorial,
    editor_evaluador: mockHecho.editorEvaluador,
    fecha_evaluacion_editorial: mockHecho.fechaEvaluacionEditorial,
    justificacion_evaluacion_editorial: mockHecho.justificacionEvaluacionEditorial,
    consenso_fuentes: mockHecho.consensoFuentes,
    es_evento_futuro: mockHecho.esEventoFuturo,
    estado_programacion: mockHecho.estadoProgramacion,
    metadata: mockHecho.metadata,
    articulo_metadata: {
      medio: mockHecho.articuloMetadata.medio,
      titular: mockHecho.articuloMetadata.titular,
      url: mockHecho.articuloMetadata.url,
      fecha_publicacion: mockHecho.articuloMetadata.fechaPublicacion,
      pais_publicacion: mockHecho.articuloMetadata.paisPublicacion,
      tipo_medio: mockHecho.articuloMetadata.tipoMedio,
      autor: mockHecho.articuloMetadata.autor,
      seccion: mockHecho.articuloMetadata.seccion,
      es_opinion: mockHecho.articuloMetadata.esOpinion,
      es_oficial: mockHecho.articuloMetadata.esOficial,
      resumen: mockHecho.articuloMetadata.resumen,
      categorias_asignadas: mockHecho.articuloMetadata.categoriasAsignadas,
      puntuacion_relevancia: mockHecho.articuloMetadata.puntuacionRelevancia,
      estado_procesamiento: mockHecho.articuloMetadata.estadoProcesamiento
    }
  };
}

/**
 * Simula filtros aplicados a los datos mock
 */
function applyFiltersToMockData(hechos: Hecho[], filters?: FilterState): Hecho[] {
  if (!filters) return hechos;
  
  return hechos.filter(hecho => {
    // Filtro por medio
    if (filters.medio && hecho.articuloMetadata.medio !== filters.medio) {
      return false;
    }
    
    // Filtro por país
    if (filters.paisPublicacion) {
      const paisArray = Array.isArray(hecho.pais) ? hecho.pais : [hecho.pais];
      if (!paisArray.some(p => p?.includes(filters.paisPublicacion!))) {
        return false;
      }
    }
    
    // Filtro por tipo de hecho
    if (filters.tipoHecho && hecho.tipoHecho !== filters.tipoHecho) {
      return false;
    }
    
    // Filtro por evaluación editorial
    if (filters.evaluacionEditorial && hecho.evaluacionEditorial !== filters.evaluacionEditorial) {
      return false;
    }
    
    // Filtro por importancia mínima
    if (filters.importanciaMin && hecho.importancia < filters.importanciaMin) {
      return false;
    }
    
    // Filtro por importancia máxima
    if (filters.importanciaMax && hecho.importancia > filters.importanciaMax) {
      return false;
    }
    
    // Filtro por fecha de inicio
    if (filters.fechaInicio) {
      const fechaHecho = new Date(hecho.fechaOcurrencia);
      if (fechaHecho < filters.fechaInicio) {
        return false;
      }
    }
    
    // Filtro por fecha de fin
    if (filters.fechaFin) {
      const fechaHecho = new Date(hecho.fechaOcurrencia);
      if (fechaHecho > filters.fechaFin) {
        return false;
      }
    }
    
    return true;
  });
}

/**
 * Simula paginación en los datos mock
 */
function paginateMockData<T>(items: T[], page: number = 1, limit: number = 20): {
  items: T[];
  pagination: {
    total_items: number;
    page: number;
    per_page: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
} {
  const totalItems = items.length;
  const totalPages = Math.ceil(totalItems / limit);
  const startIndex = (page - 1) * limit;
  const endIndex = startIndex + limit;
  const paginatedItems = items.slice(startIndex, endIndex);
  
  return {
    items: paginatedItems,
    pagination: {
      total_items: totalItems,
      page,
      per_page: limit,
      total_pages: totalPages,
      has_next: page < totalPages,
      has_prev: page > 1
    }
  };
}
/**
 * Generates mock hechos response with filters and pagination
 * Función centralizada para generar respuesta mock con filtros y paginación
 */
async function getMockHechosResponse(
  filters?: FilterState,
  pagination?: { page?: number; limit?: number }
): Promise<ApiResponse<HechosListResponse>> {
  // Generate additional mock data if needed
  const allMockData = [...mockHechos, ...generateMockHechos(20)];
  
  // Apply filters to mock data
  const filteredMockData = applyFiltersToMockData(allMockData, filters);
  
  // Apply pagination to filtered data
  const paginatedMockData = paginateMockData(
    filteredMockData, 
    pagination?.page || 1, 
    pagination?.limit || 20
  );
  
  // Convert frontend mock data to backend format
  const backendFormattedItems = paginatedMockData.items.map(convertMockToBackendFormat);
  
  const mockBackendResponse: BackendHechosResponse = {
    items: backendFormattedItems,
    pagination: paginatedMockData.pagination
  };

  // Map mock backend response to frontend format
  const mappedHechos = mapHechosFromBackend(mockBackendResponse.items);
  
  const frontendResponse: HechosListResponse = {
    hechos: mappedHechos,
    pagination: {
      totalItems: mockBackendResponse.pagination.total_items,
      page: mockBackendResponse.pagination.page,
      limit: mockBackendResponse.pagination.per_page,
      totalPages: mockBackendResponse.pagination.total_pages,
      hasNextPage: mockBackendResponse.pagination.has_next,
      hasPreviousPage: mockBackendResponse.pagination.has_prev
    }
  };

  if (env.isDevelopment()) {
    console.log('🎭 Mock data response generated:', {
      hechos: frontendResponse.hechos.length,
      total: frontendResponse.pagination.totalItems,
      page: frontendResponse.pagination.page,
      filters: filters
    });
  }

  return {
    data: frontendResponse,
    success: true,
    message: 'Hechos retrieved successfully from mock data (API unavailable)',
    timestamp: new Date().toISOString()
  };
}

/**
 * Generates mock dashboard stats response
 * Función centralizada para generar estadísticas mock del dashboard
 */
async function getMockStatsResponse(): Promise<ApiResponse<any>> {
  // Generate stats from mock data
  const allMockData = [...mockHechos, ...generateMockHechos(20)];
  
  const stats = {
    totalHechos: allMockData.length,
    hechosPorEvaluacion: {
      verificado_ok_editorial: allMockData.filter(h => h.evaluacionEditorial === 'verificado_ok_editorial').length,
      declarado_falso_editorial: allMockData.filter(h => h.evaluacionEditorial === 'declarado_falso_editorial').length,
      pendiente_revision_editorial: allMockData.filter(h => h.evaluacionEditorial === 'pendiente_revision_editorial').length,
      sin_evaluar: allMockData.filter(h => !h.evaluacionEditorial).length
    },
    importanciaPromedio: Math.round(allMockData.reduce((acc, h) => acc + h.importancia, 0) / allMockData.length * 10) / 10,
    consensoFuentes: {
      confirmado_multiples_fuentes: allMockData.filter(h => h.consensoFuentes === 'confirmado_multiples_fuentes').length,
      en_disputa_por_hechos_contradictorios: allMockData.filter(h => h.consensoFuentes === 'en_disputa_por_hechos_contradictorios').length,
      pendiente_analisis_fuentes: allMockData.filter(h => h.consensoFuentes === 'pendiente_analisis_fuentes').length,
      sin_confirmacion_suficiente_fuentes: allMockData.filter(h => h.consensoFuentes === 'sin_confirmacion_suficiente_fuentes').length
    },
    tiposHechoMasComunes: {
      ANUNCIO: allMockData.filter(h => h.tipoHecho === 'ANUNCIO').length,
      SUCESO: allMockData.filter(h => h.tipoHecho === 'SUCESO').length,
      DECLARACION: allMockData.filter(h => h.tipoHecho === 'DECLARACION').length,
      EVENTO: allMockData.filter(h => h.tipoHecho === 'EVENTO').length
    }
  };
  
  if (env.isDevelopment()) {
    console.log('📊 Mock dashboard stats generated:', stats);
  }
  
  return {
    data: stats,
    success: true,
    message: 'Dashboard stats retrieved successfully from mock data',
    timestamp: new Date().toISOString()
  };
}

interface BackendHechosResponse {
  items: any[];  // Raw backend hecho objects
  pagination: {
    total_items: number;
    page: number;
    per_page: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

interface BackendFilterOptionsResponse {
  medios_disponibles: string[];
  paises_disponibles: string[];
  importancia_range: {
    min: number;
    max: number;
  };
}

/**
 * Frontend API response types (what we return to components)
 */
export interface HechosListResponse {
  hechos: Hecho[];
  pagination: {
    totalItems: number;
    page: number;
    limit: number;
    totalPages: number;
    hasNextPage: boolean;
    hasPreviousPage: boolean;
  };
}

export interface FilterOptionsResponse {
  medios: string[];
  paises: string[];
  importanciaRange: {
    min: number;
    max: number;
  };
}

/**
 * Dashboard API service
 * Servicios para obtener y manejar datos del dashboard
 */
export const dashboardApi = {
  /**
   * Obtiene lista de hechos con filtros y paginación
   * Intenta usar API real, fallback a mocks si falla
   */
  getHechos: async (
    filters?: FilterState,
    pagination?: { page?: number; limit?: number } = {}
  ): Promise<ApiResponse<HechosListResponse>> => {
    try {
      // Check if we should force mock mode
      if (env.shouldUseMocks()) {
        console.log('🔧 Force mock mode enabled - Using mock data directly');
        return await getMockHechosResponse(filters, pagination);
      }

      // Map frontend filters to backend format
      const backendFilters = filters ? mapFiltersToBackend(filters) : {};
      
      // Prepare query parameters
      const params = {
        ...backendFilters,
        limit: pagination.limit || 20,
        offset: pagination.page ? (pagination.page - 1) * (pagination.limit || 20) : 0
      };

      const url = buildUrl(API_ENDPOINTS.DASHBOARD.HECHOS_REVISION, params);
      
      if (env.isDevelopment() && env.debug) {
        console.log('🔍 Calling real API:', url);
        console.log('📄 Parameters:', params);
      }
      
      // Try real API first
      try {
        const response = await apiClient.get<BackendHechosResponse>(url);
        
        // Map backend response to frontend format
        const mappedHechos = mapHechosFromBackend(response.data.items);
        
        const frontendResponse: HechosListResponse = {
          hechos: mappedHechos,
          pagination: {
            totalItems: response.data.pagination.total_items,
            page: response.data.pagination.page,
            limit: response.data.pagination.per_page,
            totalPages: response.data.pagination.total_pages,
            hasNextPage: response.data.pagination.has_next,
            hasPreviousPage: response.data.pagination.has_prev
          }
        };

        if (env.isDevelopment()) {
          console.log('✅ Real API response received:', {
            hechos: frontendResponse.hechos.length,
            total: frontendResponse.pagination.totalItems,
            page: frontendResponse.pagination.page
          });
        }

        return {
          data: frontendResponse,
          success: true,
          message: 'Hechos retrieved successfully from API',
          timestamp: new Date().toISOString()
        };
        
      } catch (apiError) {
        console.warn('⚠️ Real API failed, falling back to enhanced mock data:', apiError);
        return await getMockHechosResponse(filters, pagination);
      }

    } catch (error) {
      console.error('❌ Error fetching hechos:', error);
      throw error;
    }
  },

  /**
   * Obtiene estadísticas del dashboard
   */
  getDashboardStats: async (): Promise<ApiResponse<any>> => {
    try {
      // Check if we should force mock mode
      if (env.shouldUseMocks()) {
        console.log('🔧 Force mock mode enabled - Using mock stats directly');
        return await getMockStatsResponse();
      }

      // Try real API first
      try {
        // TODO: Replace with real API client when ready
        // const response = await apiClient.get(API_ENDPOINTS.DASHBOARD.STATS);
        throw new Error('Real API stats not implemented yet');
      } catch (apiError) {
        console.warn('⚠️ Real API stats failed, falling back to mock data:', apiError);
        return await getMockStatsResponse();
      }
      
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
      throw error;
    }
  },

  /**
   * Obtiene opciones disponibles para filtros
   */
  getFilterOptions: async (): Promise<ApiResponse<FilterOptionsResponse>> => {
    try {
      const url = API_ENDPOINTS.DASHBOARD.FILTROS_OPCIONES;
      
      // TODO: Replace with real API client when ready
      // const response = await apiClient.get<BackendFilterOptionsResponse>(url);
      
      // Use enhanced mock data for filter options
      const mockBackendResponse: BackendFilterOptionsResponse = {
        medios_disponibles: mockFilterOptions.medios,
        paises_disponibles: mockFilterOptions.paises,
        importancia_range: {
          min: 1,
          max: 10
        }
      };

      // Map backend response to frontend format
      const mappedOptions = mapFilterOptionsFromBackend(mockBackendResponse);

      return {
        data: mappedOptions,
        success: true,
        message: 'Filter options retrieved successfully',
        timestamp: new Date().toISOString()
      };

    } catch (error) {
      console.error('Error fetching filter options:', error);
      throw error;
    }
  },

  /**
   * Obtiene un hecho específico por ID
   */
  getHecho: async (hechoId: number): Promise<ApiResponse<Hecho>> => {
    try {
      const url = `${API_ENDPOINTS.DASHBOARD.HECHOS_REVISION}/${hechoId}`;
      
      // TODO: Replace with real API client when ready
      // const response = await apiClient.get<any>(url);
      
      // Find the hecho in our enhanced mock data
      const allMockData = [...mockHechos, ...generateMockHechos(20)];
      const foundHecho = allMockData.find(h => h.id === hechoId);
      
      if (!foundHecho) {
        throw new Error(`Hecho with ID ${hechoId} not found`);
      }
      
      // Convert to backend format
      const mockBackendHecho = convertMockToBackendFormat(foundHecho);

      // Map to frontend format
      const mappedHecho = mapHechoFromBackend(mockBackendHecho);

      return {
        data: mappedHecho,
        success: true,
        message: 'Hecho retrieved successfully',
        timestamp: new Date().toISOString()
      };

    } catch (error) {
      console.error('Error fetching hecho:', error);
      throw error;
    }
  },
};
