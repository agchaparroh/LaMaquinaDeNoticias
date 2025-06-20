// MSW handlers for API mocking
import { http, HttpResponse } from 'msw'
import { 
  mockHechosList, 
  mockPaginationResponse, 
  mockFilterOptions,
  mockDashboardStats 
} from '../data'

const API_URL = process.env.VITE_APP_API_URL || 'http://localhost:8004'

export const handlers = [
  // Get hechos list
  http.get(`${API_URL}/api/dashboard/hechos-revision`, () => {
    const backendResponse = {
      items: mockHechosList.map(hecho => ({
        id: hecho.id,
        contenido: hecho.contenido,
        fecha_ocurrencia: hecho.fechaOcurrencia,
        importancia: hecho.importancia,
        tipo_hecho: hecho.tipoHecho,
        pais: hecho.pais,
        evaluacion_editorial: hecho.evaluacionEditorial,
        articulo_metadata: {
          medio: hecho.articuloMetadata.medio,
          titular: hecho.articuloMetadata.titular,
          url: hecho.articuloMetadata.url,
          fecha_publicacion: hecho.articuloMetadata.fechaPublicacion,
          pais_publicacion: hecho.articuloMetadata.paisPublicacion,
        }
      })),
      pagination: {
        total_items: mockPaginationResponse.totalItems,
        page: mockPaginationResponse.page,
        per_page: mockPaginationResponse.limit,
        total_pages: mockPaginationResponse.totalPages,
        has_next: mockPaginationResponse.hasNextPage,
        has_prev: mockPaginationResponse.hasPreviousPage
      }
    }
    
    return HttpResponse.json({
      data: backendResponse,
      success: true,
      message: 'Success'
    })
  }),

  // Get filter options
  http.get(`${API_URL}/api/dashboard/filtros-opciones`, () => {
    return HttpResponse.json({
      data: {
        medios_disponibles: mockFilterOptions.medios,
        paises_disponibles: mockFilterOptions.paises,
        importancia_range: mockFilterOptions.importanciaRange
      },
      success: true,
      message: 'Success'
    })
  }),

  // Get dashboard stats
  http.get(`${API_URL}/api/dashboard/stats`, () => {
    return HttpResponse.json({
      data: mockDashboardStats,
      success: true,
      message: 'Success'
    })
  }),

  // Update hecho importance
  http.patch(`${API_URL}/api/hechos/:id/importancia`, ({ params }) => {
    return HttpResponse.json({
      data: {
        id: params.id,
        importancia: 8,
        message: 'Importancia actualizada correctamente'
      },
      success: true,
      message: 'Success'
    })
  }),

  // Mark hecho as false
  http.patch(`${API_URL}/api/hechos/:id/marcar-falso`, ({ params }) => {
    return HttpResponse.json({
      data: {
        id: params.id,
        evaluacion_editorial: 'declarado_falso_editorial',
        message: 'Hecho marcado como falso'
      },
      success: true,
      message: 'Success'
    })
  }),

  // Get single hecho
  http.get(`${API_URL}/api/dashboard/hechos-revision/:id`, ({ params }) => {
    const hecho = mockHechosList.find(h => h.id === Number(params.id))
    
    if (!hecho) {
      return HttpResponse.json(
        { error: 'Not found' },
        { status: 404 }
      )
    }
    
    return HttpResponse.json({
      data: hecho,
      success: true,
      message: 'Success'
    })
  })
]

// Error handlers for testing error scenarios
export const errorHandlers = {
  serverError: http.get(`${API_URL}/api/dashboard/hechos-revision`, () => {
    return HttpResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }),
  
  networkError: http.get(`${API_URL}/api/dashboard/hechos-revision`, () => {
    return HttpResponse.error()
  })
}
