import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import LoadingSpinner from '../LoadingSpinner'

describe('LoadingSpinner', () => {
  it('renders with default props', () => {
    const { container } = render(<LoadingSpinner />)
    
    // Verificar que el spinner existe
    const spinner = container.querySelector('.MuiCircularProgress-root')
    expect(spinner).toBeTruthy()
    
    // Verificar tamaño por defecto
    const svg = spinner?.querySelector('svg')
    expect(svg?.getAttribute('width')).toBe('40')
    expect(svg?.getAttribute('height')).toBe('40')
  })

  it('renders with custom size', () => {
    const { container } = render(<LoadingSpinner size={60} />)
    
    const svg = container.querySelector('svg')
    expect(svg?.getAttribute('width')).toBe('60')
    expect(svg?.getAttribute('height')).toBe('60')
  })

  it('renders with custom color', () => {
    const { container } = render(<LoadingSpinner color="secondary" />)
    
    const spinner = container.querySelector('.MuiCircularProgress-colorSecondary')
    expect(spinner).toBeTruthy()
  })

  it('applies custom Box props', () => {
    render(<LoadingSpinner data-testid="custom-spinner" />)
    
    const box = screen.getByTestId('custom-spinner')
    expect(box).toBeTruthy()
  })
})