import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import StatusChip from '../StatusChip'

describe('StatusChip', () => {
  it('renders success status correctly', () => {
    render(<StatusChip status="success" label="Completado" />)
    
    const chip = screen.getByText('Completado')
    expect(chip).toBeTruthy()
    
    // Verificar el ícono de éxito
    const icon = chip.closest('.MuiChip-root')?.querySelector('.MuiChip-icon')
    expect(icon).toBeTruthy()
  })

  it('renders error status correctly', () => {
    render(<StatusChip status="error" label="Error" />)
    
    const chip = screen.getByText('Error')
    expect(chip).toBeTruthy()
    
    // Verificar color error
    const chipElement = chip.closest('.MuiChip-colorError')
    expect(chipElement).toBeTruthy()
  })

  it('renders warning status correctly', () => {
    render(<StatusChip status="warning" label="Advertencia" />)
    
    const chip = screen.getByText('Advertencia')
    expect(chip).toBeTruthy()
    
    // Verificar color warning
    const chipElement = chip.closest('.MuiChip-colorWarning')
    expect(chipElement).toBeTruthy()
  })

  it('renders info status correctly', () => {
    render(<StatusChip status="info" label="Información" />)
    
    const chip = screen.getByText('Información')
    expect(chip).toBeTruthy()
    
    // Verificar color info
    const chipElement = chip.closest('.MuiChip-colorInfo')
    expect(chipElement).toBeTruthy()
  })

  it('renders pending status correctly', () => {
    render(<StatusChip status="pending" label="Pendiente" />)
    
    const chip = screen.getByText('Pendiente')
    expect(chip).toBeTruthy()
    
    // Verificar color default
    const chipElement = chip.closest('.MuiChip-colorDefault')
    expect(chipElement).toBeTruthy()
  })
})