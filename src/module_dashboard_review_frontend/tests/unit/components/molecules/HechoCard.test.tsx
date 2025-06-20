// Tests for HechoCard component
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@/tests/test-utils'
import { HechoCard } from '@/components/molecules/HechoCard'
import { mockHecho } from '@/tests/mocks/data'

describe('HechoCard', () => {
  const defaultProps = {
    hecho: mockHecho,
    onImportanciaChange: vi.fn(),
    onMarcarFalso: vi.fn(),
    onVerDetalle: vi.fn(),
  }

  describe('rendering', () => {
    it('should render hecho content', () => {
      render(<HechoCard {...defaultProps} />)
      
      expect(screen.getByText(mockHecho.contenido)).toBeInTheDocument()
      expect(screen.getByText(mockHecho.articuloMetadata.medio)).toBeInTheDocument()
      expect(screen.getByText(mockHecho.tipoHecho)).toBeInTheDocument()
    })

    it('should display importance correctly', () => {
      render(<HechoCard {...defaultProps} />)
      
      const importanceText = `Importancia: ${mockHecho.importancia}/10`
      expect(screen.getByText(importanceText)).toBeInTheDocument()
    })

    it('should show evaluation status', () => {
      render(<HechoCard {...defaultProps} />)
      
      expect(screen.getByText(/pendiente/i)).toBeInTheDocument()
    })

    it('should display article metadata', () => {
      render(<HechoCard {...defaultProps} />)
      
      expect(screen.getByText(mockHecho.articuloMetadata.titular)).toBeInTheDocument()
      expect(screen.getByText(mockHecho.articuloMetadata.autor)).toBeInTheDocument()
    })
  })

  describe('interactions', () => {
    it('should call onVerDetalle when clicking on card', () => {
      render(<HechoCard {...defaultProps} />)
      
      const card = screen.getByRole('article')
      fireEvent.click(card)
      
      expect(defaultProps.onVerDetalle).toHaveBeenCalledWith(mockHecho)
    })

    it('should call onImportanciaChange when changing importance', () => {
      render(<HechoCard {...defaultProps} />)
      
      const changeButton = screen.getByLabelText(/cambiar importancia/i)
      fireEvent.click(changeButton)
      
      expect(defaultProps.onImportanciaChange).toHaveBeenCalledWith(mockHecho.id)
    })

    it('should call onMarcarFalso when marking as false', () => {
      render(<HechoCard {...defaultProps} />)
      
      const falseButton = screen.getByLabelText(/marcar como falso/i)
      fireEvent.click(falseButton)
      
      expect(defaultProps.onMarcarFalso).toHaveBeenCalledWith(mockHecho.id)
    })

    it('should prevent event bubbling on action buttons', () => {
      render(<HechoCard {...defaultProps} />)
      
      const changeButton = screen.getByLabelText(/cambiar importancia/i)
      fireEvent.click(changeButton)
      
      // Card click should not be called
      expect(defaultProps.onVerDetalle).not.toHaveBeenCalled()
    })
  })

  describe('conditional rendering', () => {
    it('should show false indicator when marked as false', () => {
      const falseHecho = {
        ...mockHecho,
        evaluacionEditorial: 'declarado_falso_editorial',
        justificacionEvaluacionEditorial: 'Test justification'
      }
      
      render(<HechoCard {...defaultProps} hecho={falseHecho} />)
      
      expect(screen.getByText(/falso/i)).toBeInTheDocument()
      expect(screen.getByText(falseHecho.justificacionEvaluacionEditorial)).toBeInTheDocument()
    })

    it('should show verified indicator when verified', () => {
      const verifiedHecho = {
        ...mockHecho,
        evaluacionEditorial: 'verificado_ok_editorial'
      }
      
      render(<HechoCard {...defaultProps} hecho={verifiedHecho} />)
      
      expect(screen.getByText(/verificado/i)).toBeInTheDocument()
    })

    it('should handle missing article metadata gracefully', () => {
      const hechoWithoutArticle = {
        ...mockHecho,
        articuloMetadata: {
          ...mockHecho.articuloMetadata,
          titular: null,
          autor: null
        }
      }
      
      render(<HechoCard {...defaultProps} hecho={hechoWithoutArticle} />)
      
      expect(screen.getByText(mockHecho.contenido)).toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    it('should have proper ARIA attributes', () => {
      render(<HechoCard {...defaultProps} />)
      
      const card = screen.getByRole('article')
      expect(card).toHaveAttribute('aria-label', expect.stringContaining('Hecho noticioso'))
    })

    it('should have keyboard accessible buttons', () => {
      render(<HechoCard {...defaultProps} />)
      
      const changeButton = screen.getByLabelText(/cambiar importancia/i)
      const falseButton = screen.getByLabelText(/marcar como falso/i)
      
      expect(changeButton).toHaveAttribute('type', 'button')
      expect(falseButton).toHaveAttribute('type', 'button')
    })
  })
})
