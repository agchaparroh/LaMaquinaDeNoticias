// Tests for useDashboard hook
import { describe, it, expect, vi } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useDashboard } from '@/hooks/dashboard/useDashboard'
import { server } from '@/tests/mocks/server'
import { errorHandlers } from '@/tests/mocks/handlers'

describe('useDashboard', () => {
  it('should fetch hechos on mount', async () => {
    const { result } = renderHook(() => useDashboard())
    
    // Initially loading
    expect(result.current.loading).toBe(true)
    expect(result.current.hechos).toEqual([])
    
    // Wait for data to load
    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })
    
    // Should have data
    expect(result.current.hechos.length).toBeGreaterThan(0)
    expect(result.current.pagination).toBeDefined()
    expect(result.current.error).toBeNull()
  })

  it('should handle API errors gracefully', async () => {
    server.use(errorHandlers.serverError)
    
    const { result } = renderHook(() => useDashboard())
    
    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })
    
    // Should fallback to mock data
    expect(result.current.hechos.length).toBeGreaterThan(0)
    expect(result.current.error).toBeNull()
  })

  it('should apply filters', async () => {
    const { result } = renderHook(() => useDashboard())
    
    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })
    
    // Apply filters
    const filters = {
      medio: 'El País',
      tipoHecho: 'ANUNCIO'
    }
    
    result.current.setFilters(filters)
    
    // Should trigger new fetch
    expect(result.current.loading).toBe(true)
    
    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })
    
    expect(result.current.filters).toEqual(filters)
  })

  it('should handle pagination', async () => {
    const { result } = renderHook(() => useDashboard())
    
    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })
    
    // Change page
    result.current.handlePageChange(2)
    
    expect(result.current.loading).toBe(true)
    expect(result.current.pagination.page).toBe(2)
    
    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })
  })

  it('should reset filters', async () => {
    const { result } = renderHook(() => useDashboard())
    
    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })
    
    // Set filters
    result.current.setFilters({ medio: 'El País' })
    
    await waitFor(() => {
      expect(result.current.filters.medio).toBe('El País')
    })
    
    // Reset filters
    result.current.resetFilters()
    
    await waitFor(() => {
      expect(result.current.filters).toEqual({})
    })
  })

  it('should toggle auto-refresh', async () => {
    const { result } = renderHook(() => useDashboard())
    
    expect(result.current.autoRefresh).toBe(false)
    
    result.current.toggleAutoRefresh()
    
    expect(result.current.autoRefresh).toBe(true)
    
    result.current.toggleAutoRefresh()
    
    expect(result.current.autoRefresh).toBe(false)
  })
})
