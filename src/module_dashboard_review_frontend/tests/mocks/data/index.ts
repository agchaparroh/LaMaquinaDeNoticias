// Mock data fixtures for tests
import { Hecho, ArticuloMetadata } from '@/types/domain'

export const mockArticuloMetadata: ArticuloMetadata = {
  medio: 'El País',
  titular: 'Test Article Title',
  url: 'https://example.com/article',
  fechaPublicacion: '2024-01-15T10:00:00Z',
  paisPublicacion: 'España',
  tipoMedio: 'Periódico Digital',
  autor: 'John Doe',
  seccion: 'Nacional',
  esOpinion: false,
  esOficial: false,
  resumen: 'Test article summary',
  categoriasAsignadas: ['Política', 'Nacional'],
  puntuacionRelevancia: 8.5,
  estadoProcesamiento: 'completado'
}

export const mockHecho: Hecho = {
  id: 1,
  contenido: 'Test news fact content',
  fechaOcurrencia: '2024-01-15',
  precisionTemporal: 'día exacto',
  importancia: 7,
  tipoHecho: 'ANUNCIO',
  pais: 'España',
  region: 'Madrid',
  ciudad: 'Madrid',
  etiquetas: ['política', 'economía'],
  frecuenciaCitacion: 5,
  totalMenciones: 10,
  mencionesConfirmatorias: 8,
  fechaIngreso: '2024-01-15T12:00:00Z',
  evaluacionEditorial: 'pendiente_revision_editorial',
  editorEvaluador: null,
  fechaEvaluacionEditorial: null,
  justificacionEvaluacionEditorial: null,
  consensoFuentes: 'confirmado_multiples_fuentes',
  esEventoFuturo: false,
  estadoProgramacion: null,
  metadata: {},
  articuloMetadata: mockArticuloMetadata
}

export const mockHechosList: Hecho[] = [
  mockHecho,
  {
    ...mockHecho,
    id: 2,
    contenido: 'Another test fact',
    importancia: 9,
    tipoHecho: 'SUCESO',
    evaluacionEditorial: 'verificado_ok_editorial'
  },
  {
    ...mockHecho,
    id: 3,
    contenido: 'Third test fact',
    importancia: 3,
    tipoHecho: 'DECLARACION',
    evaluacionEditorial: 'declarado_falso_editorial',
    justificacionEvaluacionEditorial: 'Información incorrecta'
  }
]

export const mockPaginationResponse = {
  totalItems: 100,
  page: 1,
  limit: 20,
  totalPages: 5,
  hasNextPage: true,
  hasPreviousPage: false
}

export const mockFilterOptions = {
  medios: ['El País', 'ABC', 'La Vanguardia', 'El Mundo'],
  paises: ['España', 'México', 'Argentina', 'Colombia'],
  importanciaRange: { min: 1, max: 10 }
}

export const mockDashboardStats = {
  totalHechos: 150,
  hechosPorEvaluacion: {
    verificado_ok_editorial: 45,
    declarado_falso_editorial: 5,
    pendiente_revision_editorial: 80,
    sin_evaluar: 20
  },
  importanciaPromedio: 6.7,
  consensoFuentes: {
    confirmado_multiples_fuentes: 100,
    en_disputa_por_hechos_contradictorios: 20,
    pendiente_analisis_fuentes: 25,
    sin_confirmacion_suficiente_fuentes: 5
  },
  tiposHechoMasComunes: {
    ANUNCIO: 50,
    SUCESO: 40,
    DECLARACION: 35,
    EVENTO: 25
  }
}
