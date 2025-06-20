// User flow tests for editorial review process
import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@/tests/test-utils'
import App from '@/App'
import userEvent from '@testing-library/user-event'

describe('Editorial Review User Flows', () => {
  describe('Complete editorial review flow', () => {
    it('should allow editor to review, filter, and update hechos', async () => {
      const user = userEvent.setup()
      render(<App />)
      
      // 1. Navigate to dashboard
      await waitFor(() => {
        expect(screen.getByText(/dashboard de revisión editorial/i)).toBeInTheDocument()
      })
      
      // 2. Wait for initial data load
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
      })
      
      // 3. Apply filters
      const medioSelect = screen.getByLabelText(/medio/i)
      await user.click(medioSelect)
      const elPaisOption = await screen.findByText('El País')
      await user.click(elPaisOption)
      
      // 4. Change importance of first hecho
      await waitFor(() => {
        const firstImportanceButton = screen.getAllByLabelText(/cambiar importancia/i)[0]
        return user.click(firstImportanceButton)
      })
      
      // 5. Update importance value
      const slider = screen.getByRole('slider')
      fireEvent.change(slider, { target: { value: 9 } })
      
      const updateButton = screen.getByText(/actualizar/i)
      await user.click(updateButton)
      
      // 6. Verify success notification
      await waitFor(() => {
        expect(screen.getByText(/importancia actualizada/i)).toBeInTheDocument()
      })
      
      // 7. View hecho details
      const firstHecho = screen.getByText('Test news fact content')
      await user.click(firstHecho.closest('article')!)
      
      // 8. Verify modal opens with details
      await waitFor(() => {
        const modal = screen.getByRole('dialog')
        expect(modal).toBeInTheDocument()
        expect(within(modal).getByText(/detalles del hecho/i)).toBeInTheDocument()
        expect(within(modal).getByText(/información del artículo/i)).toBeInTheDocument()
      })
      
      // 9. Close modal
      const closeButton = screen.getByLabelText(/cerrar/i)
      await user.click(closeButton)
      
      // 10. Reset filters
      const resetButton = screen.getByText(/limpiar filtros/i)
      await user.click(resetButton)
      
      // Verify filters are cleared
      await waitFor(() => {
        expect(medioSelect).toHaveValue('')
      })
    })
  })

  describe('False marking flow with justification', () => {
    it('should complete false marking process with all validations', async () => {
      const user = userEvent.setup()
      render(<App />)
      
      // Wait for data
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
      })
      
      // Find a hecho that is not already marked as false
      const hechos = screen.getAllByRole('article')
      const targetHecho = hechos.find(h => !within(h).queryByText(/falso/i))
      
      expect(targetHecho).toBeDefined()
      
      // Click mark as false button
      const falseButton = within(targetHecho!).getByLabelText(/marcar como falso/i)
      await user.click(falseButton)
      
      // Dialog should appear
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })
      
      // Try to submit without justification
      const confirmButton = screen.getByText(/confirmar/i)
      await user.click(confirmButton)
      
      // Should show validation error
      expect(screen.getByText(/justificación es requerida/i)).toBeInTheDocument()
      
      // Add justification
      const justificationInput = screen.getByLabelText(/justificación/i)
      await user.type(justificationInput, 'Información verificada como incorrecta según fuentes oficiales')
      
      // Submit
      await user.click(confirmButton)
      
      // Should show success
      await waitFor(() => {
        expect(screen.getByText(/hecho marcado como falso/i)).toBeInTheDocument()
      })
    })
  })

  describe('Pagination and data persistence flow', () => {
    it('should maintain filters when navigating pages', async () => {
      const user = userEvent.setup()
      render(<App />)
      
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
      })
      
      // Apply filter
      const typeSelect = screen.getByLabelText(/tipo de hecho/i)
      await user.click(typeSelect)
      const suceso = await screen.findByText('SUCESO')
      await user.click(suceso)
      
      // Navigate to next page
      const nextButton = screen.getByLabelText(/siguiente página/i)
      await user.click(nextButton)
      
      // Filter should persist
      await waitFor(() => {
        expect(typeSelect).toHaveValue('SUCESO')
        expect(screen.getByText(/página 2/i)).toBeInTheDocument()
      })
      
      // Navigate back
      const prevButton = screen.getByLabelText(/página anterior/i)
      await user.click(prevButton)
      
      // Should be back on page 1 with filter
      await waitFor(() => {
        expect(screen.getByText(/página 1/i)).toBeInTheDocument()
        expect(typeSelect).toHaveValue('SUCESO')
      })
    })
  })

  describe('Error recovery flow', () => {
    it('should allow retry after error and show appropriate feedback', async () => {
      const user = userEvent.setup()
      
      // Start with error state
      server.use(errorHandlers.serverError)
      
      render(<App />)
      
      // Should show data (fallback to mocks)
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
        expect(screen.getByText('Test news fact content')).toBeInTheDocument()
      })
      
      // Should show info about using mock data
      expect(screen.getByText(/datos de respaldo/i)).toBeInTheDocument()
    })
  })

  describe('Multi-filter complex search flow', () => {
    it('should handle multiple filters simultaneously', async () => {
      const user = userEvent.setup()
      render(<App />)
      
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
      })
      
      // Apply multiple filters
      // 1. Medio
      const medioSelect = screen.getByLabelText(/medio/i)
      await user.click(medioSelect)
      await user.click(await screen.findByText('El País'))
      
      // 2. Importance
      const importanceSlider = screen.getByLabelText(/importancia mínima/i)
      fireEvent.change(importanceSlider, { target: { value: 7 } })
      
      // 3. Date range
      const startDateInput = screen.getByLabelText(/fecha inicio/i)
      await user.type(startDateInput, '01/01/2024')
      
      // 4. Evaluation status
      const evalSelect = screen.getByLabelText(/evaluación/i)
      await user.click(evalSelect)
      await user.click(await screen.findByText(/pendiente/i))
      
      // Should show filtered results
      await waitFor(() => {
        // Verify all filters are applied
        expect(medioSelect).toHaveValue('El País')
        expect(importanceSlider).toHaveValue('7')
        expect(startDateInput).toHaveValue('01/01/2024')
        expect(evalSelect).toHaveValue(expect.stringContaining('pendiente'))
      })
      
      // Clear specific filter
      await user.clear(startDateInput)
      
      // Other filters should remain
      expect(medioSelect).toHaveValue('El País')
      expect(importanceSlider).toHaveValue('7')
    })
  })
})
