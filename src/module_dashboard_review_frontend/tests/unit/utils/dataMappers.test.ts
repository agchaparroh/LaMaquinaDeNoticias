// Tests for data mapper utilities
import { describe, it, expect } from 'vitest'
import { 
  mapHechoFromBackend, 
  mapHechosFromBackend,
  mapFilterOptionsFromBackend,
  mapFiltersToBackend 
} from '@/utils/dataMappers'

describe('dataMappers', () => {
  describe('mapHechoFromBackend', () => {
    it('should map backend hecho to frontend format', () => {
      const backendHecho = {
        id: 1,
        contenido: 'Test content',
        fecha_ocurrencia: '2024-01-15',
        precision_temporal: 'día exacto',
        importancia: 7,
        tipo_hecho: 'ANUNCIO',
        pais: 'España',
        region: 'Madrid',
        ciudad: 'Madrid',
        etiquetas: ['test'],
        frecuencia_citacion: 5,
        total_menciones: 10,
        menciones_confirmatorias: 8,
        fecha_ingreso: '2024-01-15T12:00:00Z',
        evaluacion_editorial: 'pendiente_revision_editorial',
        editor_evaluador: null,
        fecha_evaluacion_editorial: null,
        justificacion_evaluacion_editorial: null,
        consenso_fuentes: 'confirmado_multiples_fuentes',
        es_evento_futuro: false,
        estado_programacion: null,
        metadata: {},
        articulo_metadata: {
          medio: 'El País',
          titular: 'Test Title',
          url: 'https://example.com',
          fecha_publicacion: '2024-01-15T10:00:00Z',
          pais_publicacion: 'España',
          tipo_medio: 'Periódico Digital',
          autor: 'John Doe',
          seccion: 'Nacional',
          es_opinion: false,
          es_oficial: false,
          resumen: 'Test summary',
          categorias_asignadas: ['Nacional'],
          puntuacion_relevancia: 8.5,
          estado_procesamiento: 'completado'
        }
      }
      
      const result = mapHechoFromBackend(backendHecho)
      
      expect(result).toEqual({
        id: 1,
        contenido: 'Test content',
        fechaOcurrencia: '2024-01-15',
        precisionTemporal: 'día exacto',
        importancia: 7,
        tipoHecho: 'ANUNCIO',
        pais: 'España',
        region: 'Madrid',
        ciudad: 'Madrid',
        etiquetas: ['test'],
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
        articuloMetadata: {
          medio: 'El País',
          titular: 'Test Title',
          url: 'https://example.com',
          fechaPublicacion: '2024-01-15T10:00:00Z',
          paisPublicacion: 'España',
          tipoMedio: 'Periódico Digital',
          autor: 'John Doe',
          seccion: 'Nacional',
          esOpinion: false,
          esOficial: false,
          resumen: 'Test summary',
          categoriasAsignadas: ['Nacional'],
          puntuacionRelevancia: 8.5,
          estadoProcesamiento: 'completado'
        }
      })
    })

    it('should handle missing optional fields', () => {
      const minimalBackendHecho = {
        id: 1,
        contenido: 'Test',
        fecha_ocurrencia: '2024-01-15',
        importancia: 5,
        tipo_hecho: 'SUCESO',
        articulo_metadata: {
          medio: 'Test Medio',
          titular: 'Test Title',
          url: 'https://example.com',
          fecha_publicacion: '2024-01-15'
        }
      }
      
      const result = mapHechoFromBackend(minimalBackendHecho)
      
      expect(result.id).toBe(1)
      expect(result.contenido).toBe('Test')
      expect(result.importancia).toBe(5)
      expect(result.pais).toBeNull()
      expect(result.region).toBeNull()
    })
  })

  describe('mapHechosFromBackend', () => {
    it('should map array of backend hechos', () => {
      const backendHechos = [
        { id: 1, contenido: 'Test 1', fecha_ocurrencia: '2024-01-15', importancia: 5, tipo_hecho: 'ANUNCIO', articulo_metadata: { medio: 'Medio 1', titular: 'Title 1', url: 'url1', fecha_publicacion: '2024-01-15' } },
        { id: 2, contenido: 'Test 2', fecha_ocurrencia: '2024-01-16', importancia: 7, tipo_hecho: 'SUCESO', articulo_metadata: { medio: 'Medio 2', titular: 'Title 2', url: 'url2', fecha_publicacion: '2024-01-16' } }
      ]
      
      const result = mapHechosFromBackend(backendHechos)
      
      expect(result).toHaveLength(2)
      expect(result[0].id).toBe(1)
      expect(result[1].id).toBe(2)
    })

    it('should handle empty array', () => {
      const result = mapHechosFromBackend([])
      expect(result).toEqual([])
    })
  })

  describe('mapFilterOptionsFromBackend', () => {
    it('should map filter options correctly', () => {
      const backendOptions = {
        medios_disponibles: ['El País', 'ABC'],
        paises_disponibles: ['España', 'México'],
        importancia_range: { min: 1, max: 10 }
      }
      
      const result = mapFilterOptionsFromBackend(backendOptions)
      
      expect(result).toEqual({
        medios: ['El País', 'ABC'],
        paises: ['España', 'México'],
        importanciaRange: { min: 1, max: 10 }
      })
    })
  })

  describe('mapFiltersToBackend', () => {
    it('should map frontend filters to backend format', () => {
      const frontendFilters = {
        medio: 'El País',
        paisPublicacion: 'España',
        tipoHecho: 'ANUNCIO',
        evaluacionEditorial: 'pendiente_revision_editorial',
        importanciaMin: 5,
        importanciaMax: 8,
        fechaInicio: new Date('2024-01-01'),
        fechaFin: new Date('2024-01-31')
      }
      
      const result = mapFiltersToBackend(frontendFilters)
      
      expect(result).toEqual({
        medio: 'El País',
        pais_publicacion: 'España',
        tipo_hecho: 'ANUNCIO',
        evaluacion_editorial: 'pendiente_revision_editorial',
        importancia_min: 5,
        importancia_max: 8,
        fecha_inicio: '2024-01-01',
        fecha_fin: '2024-01-31'
      })
    })

    it('should omit undefined filter values', () => {
      const frontendFilters = {
        medio: 'El País',
        tipoHecho: undefined,
        importanciaMin: null
      }
      
      const result = mapFiltersToBackend(frontendFilters)
      
      expect(result).toEqual({
        medio: 'El País'
      })
      expect(result).not.toHaveProperty('tipo_hecho')
      expect(result).not.toHaveProperty('importancia_min')
    })

    it('should format dates as ISO strings', () => {
      const date = new Date('2024-01-15T10:30:00Z')
      const filters = {
        fechaInicio: date
      }
      
      const result = mapFiltersToBackend(filters)
      
      expect(result.fecha_inicio).toBe('2024-01-15')
    })
  })
})
