import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { ThemeProvider, createTheme } from '@mui/material';
import WizardPage from '../WizardPage';
import { NotificationProvider } from '../../contexts/NotificationContext';

// Según SECCIÓN 8.3 - Tests para páginas
// WizardPage.test.tsx

const theme = createTheme();

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      <NotificationProvider>
        {component}
      </NotificationProvider>
    </ThemeProvider>
  );
};

describe('WizardPage', () => {
  it('should render wizard steps correctly', () => {
    renderWithProviders(<WizardPage />);
    
    expect(screen.getByText('Información Básica')).toBeInTheDocument();
    expect(screen.getByText('URL y Sección')).toBeInTheDocument();
    expect(screen.getByText('Análisis')).toBeInTheDocument();
    expect(screen.getByText('Revisión')).toBeInTheDocument();
  });

  it('should show first step initially', () => {
    renderWithProviders(<WizardPage />);
    
    expect(screen.getByLabelText('Medio')).toBeInTheDocument();
    expect(screen.getByLabelText('Área Geográfica')).toBeInTheDocument();
  });

  it('should allow user to fill form fields', async () => {
    const user = userEvent.setup();
    renderWithProviders(<WizardPage />);
    
    const medioInput = screen.getByLabelText('Medio');
    await user.type(medioInput, 'El País');
    
    expect(medioInput).toHaveValue('El País');
  });

  it('should validate required fields', async () => {
    const user = userEvent.setup();
    renderWithProviders(<WizardPage />);
    
    const nextButton = screen.getByText('Siguiente');
    await user.click(nextButton);
    
    await waitFor(() => {
      expect(screen.getByText('El nombre del medio es obligatorio')).toBeInTheDocument();
    });
  });

  it('should navigate between steps', async () => {
    const user = userEvent.setup();
    renderWithProviders(<WizardPage />);
    
    // Fill required fields
    await user.type(screen.getByLabelText('Medio'), 'Test Media');
    await user.click(screen.getByLabelText('Área Geográfica'));
    await user.click(screen.getByText('ESPAÑA'));
    
    // Go to next step
    await user.click(screen.getByText('Siguiente'));
    
    await waitFor(() => {
      expect(screen.getByLabelText('Sección')).toBeInTheDocument();
    });
  });

  it('should save draft to localStorage', async () => {
    const user = userEvent.setup();
    const setItemSpy = vi.spyOn(Storage.prototype, 'setItem');
    
    renderWithProviders(<WizardPage />);
    
    await user.type(screen.getByLabelText('Medio'), 'Test Media');
    
    expect(setItemSpy).toHaveBeenCalledWith(
      'wizard-draft',
      expect.stringContaining('Test Media')
    );
  });
});