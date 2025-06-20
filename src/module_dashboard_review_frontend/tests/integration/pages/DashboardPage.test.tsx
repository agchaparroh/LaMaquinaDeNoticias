// Integration tests for DashboardPage
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@/tests/test-utils'
import { DashboardPage } from '@/components/pages/DashboardPage'
import { server } from '@/tests/mocks/server'
import { errorHandlers } from '@/tests/mocks/handlers'
import { http, HttpResponse } from 'msw'

describe('DashboardPage Integration', () => {
  describe('initial load', () => {
    it('should load and display hechos', async () => {
      render(<DashboardPage />)
      
      // Should show loading initially
      expect(screen.getByRole('progressbar')).toBeInTheDocument()
      
      // Wait for data to load
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
      })
      
      // Should display hechos
      expect(screen.getByText('Test news fact content')).toBeInTheDocument()
      expect(screen.getByText('Another test fact')).toBeInTheDocument()
    })

    it('should display dashboard stats', async () => {
      render(<DashboardPage />)
      
      await waitFor(() => {
        expect(screen.getByText(/Total de hechos:/)).toBeInTheDocument()
        expect(screen.getByText(/Importancia promedio:/)).toBeInTheDocument()
      })
    })
  })

  describe('filtering', () => {
    it('should apply filters when selecting options', async () => {
      render(<DashboardPage />)
      
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
      })
      
      // Open filter for medio
      const medioSelect = screen.getByLabelText(/medio/i)
      fireEvent.mouseDown(medioSelect)
      
      // Select an option
      const option = await screen.findByText('El País')
      fireEvent.click(option)
      
      // Should trigger loading
      expect(screen.getByRole('progressbar')).toBeInTheDocument()
      
      // Wait for filtered results
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
      })
    })

    it('should reset filters when clicking reset button', async () => {
      render(<DashboardPage />)
      
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
      })
      
      // Apply a filter
      const importanceSlider = screen.getByLabelText(/importancia mínima/i)
      fireEvent.change(importanceSlider, { target: { value: 7 } })
      
      // Click reset
      const resetButton = screen.getByText(/limpiar filtros/i)
      fireEvent.click(resetButton)
      
      // Filters should be cleared
      await waitFor(() => {
        expect(importanceSlider).toHaveValue('1')
      })
    })
  })

  describe('pagination', () => {
    it('should navigate between pages', async () => {
      render(<DashboardPage />)
      
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
      })
      
      // Should show pagination
      expect(screen.getByText(/página 1 de/i)).toBeInTheDocument()
      
      // Click next page
      const nextButton = screen.getByLabelText(/siguiente página/i)
      fireEvent.click(nextButton)
      
      // Should update page
      await waitFor(() => {
        expect(screen.getByText(/página 2 de/i)).toBeInTheDocument()
      })
    })
  })

  describe('hecho interactions', () => {
    it('should open detail modal when clicking on hecho', async () => {
      render(<DashboardPage />)
      
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
      })
      
      // Click on first hecho card
      const firstHecho = screen.getByText('Test news fact content')
      fireEvent.click(firstHecho.closest('article')!)
      
      // Should open modal
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
        expect(screen.getByText(/detalles del hecho/i)).toBeInTheDocument()
      })
      
      // Close modal
      const closeButton = screen.getByLabelText(/cerrar/i)
      fireEvent.click(closeButton)
      
      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
      })
    })

    it('should update importance and show notification', async () => {
      render(<DashboardPage />)
      
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
      })
      
      // Click change importance button
      const changeButton = screen.getAllByLabelText(/cambiar importancia/i)[0]
      fireEvent.click(changeButton)
      
      // Should show importance dialog
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })
      
      // Change value
      const slider = screen.getByRole('slider')
      fireEvent.change(slider, { target: { value: 9 } })
      
      // Confirm
      const confirmButton = screen.getByText(/actualizar/i)
      fireEvent.click(confirmButton)
      
      // Should show success notification
      await waitFor(() => {
        expect(screen.getByText(/importancia actualizada/i)).toBeInTheDocument()
      })
    })

    it('should mark as false and show notification', async () => {
      render(<DashboardPage />)
      
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
      })
      
      // Click mark as false button
      const falseButton = screen.getAllByLabelText(/marcar como falso/i)[0]
      fireEvent.click(falseButton)
      
      // Should show confirmation dialog
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
        expect(screen.getByText(/¿marcar este hecho como falso/i)).toBeInTheDocument()
      })
      
      // Add justification
      const justificationInput = screen.getByLabelText(/justificación/i)
      fireEvent.change(justificationInput, { target: { value: 'Test justification' } })
      
      // Confirm
      const confirmButton = screen.getByText(/confirmar/i)
      fireEvent.click(confirmButton)
      
      // Should show success notification
      await waitFor(() => {
        expect(screen.getByText(/hecho marcado como falso/i)).toBeInTheDocument()
      })
    })
  })

  describe('error handling', () => {
    it('should handle API errors gracefully', async () => {
      server.use(errorHandlers.serverError)
      
      render(<DashboardPage />)
      
      // Should still show data (fallback to mocks)
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
        expect(screen.getByText('Test news fact content')).toBeInTheDocument()
      })
    })

    it('should handle network errors', async () => {
      server.use(errorHandlers.networkError)
      
      render(<DashboardPage />)
      
      // Should fallback to mock data
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
        expect(screen.getByText('Test news fact content')).toBeInTheDocument()
      })
    })
  })

  describe('auto-refresh', () => {
    it('should toggle auto-refresh', async () => {
      vi.useFakeTimers()
      
      render(<DashboardPage />)
      
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
      })
      
      // Toggle auto-refresh
      const autoRefreshButton = screen.getByLabelText(/auto-actualizar/i)
      fireEvent.click(autoRefreshButton)
      
      // Should show active state
      expect(autoRefreshButton).toHaveAttribute('aria-pressed', 'true')
      
      // Advance time by 30 seconds
      vi.advanceTimersByTime(30000)
      
      // Should trigger refresh
      await waitFor(() => {
        expect(screen.getByRole('progressbar')).toBeInTheDocument()
      })
      
      vi.useRealTimers()
    })
  })

  describe('empty states', () => {
    it('should show empty state when no hechos', async () => {
      server.use(
        http.get('*/api/dashboard/hechos-revision', () => {
          return HttpResponse.json({
            data: {
              items: [],
              pagination: {
                total_items: 0,
                page: 1,
                per_page: 20,
                total_pages: 0,
                has_next: false,
                has_prev: false
              }
            },
            success: true
          })
        })
      )
      
      render(<DashboardPage />)
      
      await waitFor(() => {
        expect(screen.getByText(/no se encontraron hechos/i)).toBeInTheDocument()
      })
    })
  })
})
