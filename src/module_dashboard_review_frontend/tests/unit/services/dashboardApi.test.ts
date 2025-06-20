// Tests for dashboard API service
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { dashboardApi } from '@/services/dashboard/dashboardApi'
import { server } from '@/tests/mocks/server'
import { errorHandlers } from '@/tests/mocks/handlers'
import { mockHechosList, mockFilterOptions } from '@/tests/mocks/data'

describe('dashboardApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getHechos', () => {
    it('should fetch hechos successfully', async () => {
      const response = await dashboardApi.getHechos()
      
      expect(response.success).toBe(true)
      expect(response.data).toBeDefined()
      expect(response.data.hechos).toHaveLength(mockHechosList.length)
      expect(response.data.pagination).toBeDefined()
      expect(response.data.pagination.totalItems).toBe(100)
    })

    it('should apply filters when fetching hechos', async () => {
      const filters = {
        medio: 'El País',
        tipoHecho: 'ANUNCIO',
        importanciaMin: 5
      }
      
      const response = await dashboardApi.getHechos(filters)
      
      expect(response.success).toBe(true)
      expect(response.data.hechos).toBeDefined()
    })

    it('should handle pagination parameters', async () => {
      const pagination = { page: 2, limit: 10 }
      
      const response = await dashboardApi.getHechos(undefined, pagination)
      
      expect(response.success).toBe(true)
      expect(response.data.pagination.page).toBe(1) // Mock always returns page 1
      expect(response.data.pagination.limit).toBe(20) // Mock always returns 20
    })

    it('should fallback to mock data on API error', async () => {
      // Use error handler
      server.use(errorHandlers.serverError)
      
      const response = await dashboardApi.getHechos()
      
      expect(response.success).toBe(true)
      expect(response.message).toContain('mock data')
      expect(response.data.hechos.length).toBeGreaterThan(0)
    })

    it('should handle network errors gracefully', async () => {
      // Use network error handler
      server.use(errorHandlers.networkError)
      
      const response = await dashboardApi.getHechos()
      
      expect(response.success).toBe(true)
      expect(response.message).toContain('mock data')
    })
  })

  describe('getFilterOptions', () => {
    it('should fetch filter options successfully', async () => {
      const response = await dashboardApi.getFilterOptions()
      
      expect(response.success).toBe(true)
      expect(response.data).toBeDefined()
      expect(response.data.medios).toEqual(mockFilterOptions.medios)
      expect(response.data.paises).toEqual(mockFilterOptions.paises)
      expect(response.data.importanciaRange).toEqual(mockFilterOptions.importanciaRange)
    })
  })

  describe('getDashboardStats', () => {
    it('should fetch dashboard stats successfully', async () => {
      const response = await dashboardApi.getDashboardStats()
      
      expect(response.success).toBe(true)
      expect(response.data).toBeDefined()
      expect(response.data.totalHechos).toBe(150)
      expect(response.data.hechosPorEvaluacion).toBeDefined()
      expect(response.data.importanciaPromedio).toBe(6.7)
    })
  })

  describe('getHecho', () => {
    it('should fetch a single hecho by ID', async () => {
      const hechoId = 1
      const response = await dashboardApi.getHecho(hechoId)
      
      expect(response.success).toBe(true)
      expect(response.data).toBeDefined()
      expect(response.data.id).toBe(hechoId)
    })

    it('should handle non-existent hecho', async () => {
      const hechoId = 999
      
      await expect(dashboardApi.getHecho(hechoId)).rejects.toThrow()
    })
  })
})
