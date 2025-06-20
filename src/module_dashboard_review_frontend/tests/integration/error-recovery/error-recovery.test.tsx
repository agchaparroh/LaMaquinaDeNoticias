import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../../test-utils';
import App from '@/App';
import { DashboardPage } from '@/components/pages';
import { server } from '../../mocks/server';
import { rest } from 'msw';
import { API_BASE_URL } from '@/utils/env';

describe('Error Recovery Tests', () => {
  const user = userEvent.setup();
  
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock console.error to avoid noise in tests
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    server.resetHandlers();
    vi.restoreAllMocks();
  });

  describe('Network Error Recovery', () => {
    it('should recover from network failures and retry automatically', async () => {
      let attemptCount = 0;
      
      server.use(
        rest.get(`${API_BASE_URL}/api/hechos`, (req, res, ctx) => {
          attemptCount++;
          
          // Fail first 2 attempts, succeed on 3rd
          if (attemptCount < 3) {
            return res.networkError('Network failure');
          }
          
          return res(
            ctx.json({
              hechos: [{
                id: 1,
                contenido: 'Successfully recovered from network error',
                fechaOcurrencia: new Date().toISOString(),
                importancia: 8,
                tipoHecho: 'DECLARACION',
                articuloMetadata: {
                  titulo: 'Recovery Test',
                  medio: 'Test Media',
                  fecha_publicacion: new Date().toISOString()
                }
              }],
              total: 1,
              page: 1,
              totalPages: 1
            })
          );
        })
      );

      renderWithProviders(<DashboardPage />);

      // Should show error state initially
      await waitFor(() => {
        expect(screen.getByText(/error al cargar/i)).toBeInTheDocument();
      });

      // Click retry button
      const retryButton = screen.getByRole('button', { name: /reintentar/i });
      await user.click(retryButton);

      // Should eventually succeed and show data
      await waitFor(() => {
        expect(screen.getByText(/successfully recovered from network error/i)).toBeInTheDocument();
      }, { timeout: 5000 });

      // Verify multiple attempts were made
      expect(attemptCount).toBeGreaterThanOrEqual(3);
    });

    it('should fallback to mock data when API is completely unavailable', async () => {
      server.use(
        rest.get(`${API_BASE_URL}/api/hechos`, (req, res, ctx) => {
          return res.networkError('API Unavailable');
        })
      );

      renderWithProviders(<DashboardPage />);

      // Should show error briefly
      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument();
      });

      // Should automatically fallback to mock data
      await waitFor(() => {
        const mockDataIndicator = screen.getByText(/usando datos de respaldo/i);
        expect(mockDataIndicator).toBeInTheDocument();
      });

      // Should display mock hechos
      const hechoCards = await screen.findAllByTestId('hecho-card');
      expect(hechoCards.length).toBeGreaterThan(0);
    });

    it('should handle timeout errors with exponential backoff', async () => {
      vi.useFakeTimers();
      let attemptTimes: number[] = [];
      
      server.use(
        rest.get(`${API_BASE_URL}/api/hechos`, async (req, res, ctx) => {
          attemptTimes.push(Date.now());
          
          // Simulate timeout
          await new Promise((resolve, reject) => {
            setTimeout(() => reject(new Error('Timeout')), 5000);
          });
          
          return res(ctx.json({ hechos: [] }));
        })
      );

      renderWithProviders(<DashboardPage />);

      // Fast forward through retries
      for (let i = 0; i < 3; i++) {
        vi.advanceTimersByTime(10000);
        await vi.runOnlyPendingTimersAsync();
      }

      // Check exponential backoff pattern
      if (attemptTimes.length >= 2) {
        const firstInterval = attemptTimes[1] - attemptTimes[0];
        const secondInterval = attemptTimes[2] - attemptTimes[1];
        
        // Second interval should be longer (exponential backoff)
        expect(secondInterval).toBeGreaterThan(firstInterval);
      }

      vi.useRealTimers();
    });
  });

  describe('API Error Response Recovery', () => {
    it('should handle 500 errors gracefully', async () => {
      let errorCount = 0;
      
      server.use(
        rest.get(`${API_BASE_URL}/api/hechos`, (req, res, ctx) => {
          errorCount++;
          
          if (errorCount <= 2) {
            return res(
              ctx.status(500),
              ctx.json({ 
                error: 'Internal Server Error',
                message: 'Database connection failed'
              })
            );
          }
          
          return res(
            ctx.json({
              hechos: [{
                id: 1,
                contenido: 'Recovered from server error',
                fechaOcurrencia: new Date().toISOString(),
                importancia: 7,
                tipoHecho: 'SUCESO',
                articuloMetadata: {
                  titulo: 'Test',
                  medio: 'Test Media',
                  fecha_publicacion: new Date().toISOString()
                }
              }],
              total: 1,
              page: 1,
              totalPages: 1
            })
          );
        })
      );

      renderWithProviders(<DashboardPage />);

      // Should show error message
      await waitFor(() => {
        expect(screen.getByText(/error del servidor/i)).toBeInTheDocument();
      });

      // Manual retry
      const retryButton = screen.getByRole('button', { name: /reintentar/i });
      await user.click(retryButton);
      await user.click(retryButton); // May need multiple retries

      // Should eventually recover
      await waitFor(() => {
        expect(screen.getByText(/recovered from server error/i)).toBeInTheDocument();
      });
    });

    it('should handle 403 forbidden errors', async () => {
      server.use(
        rest.get(`${API_BASE_URL}/api/hechos`, (req, res, ctx) => {
          return res(
            ctx.status(403),
            ctx.json({ 
              error: 'Forbidden',
              message: 'You do not have permission to access this resource'
            })
          );
        })
      );

      renderWithProviders(<DashboardPage />);

      // Should show permission error
      await waitFor(() => {
        expect(screen.getByText(/no tienes permisos/i)).toBeInTheDocument();
      });

      // Should not show retry button for permission errors
      expect(screen.queryByRole('button', { name: /reintentar/i })).not.toBeInTheDocument();
    });

    it('should handle malformed response data', async () => {
      server.use(
        rest.get(`${API_BASE_URL}/api/hechos`, (req, res, ctx) => {
          return res(
            ctx.json({
              // Malformed response - missing required fields
              data: 'invalid',
              wrongField: true
            })
          );
        })
      );

      renderWithProviders(<DashboardPage />);

      // Should handle parsing error and fallback
      await waitFor(() => {
        const errorOrMockIndicator = 
          screen.queryByText(/error/i) || 
          screen.queryByText(/usando datos de respaldo/i);
        expect(errorOrMockIndicator).toBeInTheDocument();
      });

      // Should still be functional with mock data
      const hechoCards = screen.queryAllByTestId('hecho-card');
      expect(hechoCards.length).toBeGreaterThan(0);
    });
  });

  describe('Component Error Boundaries', () => {
    it('should catch and recover from React component errors', async () => {
      // Create a component that will throw an error
      const ThrowingComponent = () => {
        throw new Error('Component render error');
      };

      // Temporarily replace a component with one that throws
      const originalHechoCard = vi.fn();
      vi.mock('@/components/molecules/HechoCard', () => ({
        HechoCard: ThrowingComponent
      }));

      renderWithProviders(<App />);

      // Should show error boundary fallback
      await waitFor(() => {
        expect(screen.getByText(/algo salió mal/i)).toBeInTheDocument();
      });

      // Should provide option to reload
      const reloadButton = screen.getByRole('button', { name: /recargar/i });
      expect(reloadButton).toBeInTheDocument();

      // Restore mock
      vi.unmock('@/components/molecules/HechoCard');
    });

    it('should log errors to console in development', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error');
      
      server.use(
        rest.get(`${API_BASE_URL}/api/hechos`, (req, res, ctx) => {
          return res(
            ctx.status(500),
            ctx.json({ error: 'Test error for logging' })
          );
        })
      );

      renderWithProviders(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument();
      });

      // In development, errors should be logged
      if (import.meta.env.DEV) {
        expect(consoleErrorSpy).toHaveBeenCalled();
      }
    });
  });

  describe('Form Submission Error Recovery', () => {
    it('should handle failed importance update and allow retry', async () => {
      let updateAttempts = 0;
      
      server.use(
        rest.get(`${API_BASE_URL}/api/hechos`, (req, res, ctx) => {
          return res(
            ctx.json({
              hechos: [{
                id: 1,
                contenido: 'Test hecho',
                fechaOcurrencia: new Date().toISOString(),
                importancia: 5,
                tipoHecho: 'DECLARACION',
                articuloMetadata: {
                  titulo: 'Test',
                  medio: 'Test Media',
                  fecha_publicacion: new Date().toISOString()
                }
              }],
              total: 1,
              page: 1,
              totalPages: 1
            })
          );
        }),
        rest.put(`${API_BASE_URL}/api/hechos/:id/importancia`, (req, res, ctx) => {
          updateAttempts++;
          
          // Fail first attempt
          if (updateAttempts === 1) {
            return res(
              ctx.status(500),
              ctx.json({ error: 'Update failed' })
            );
          }
          
          return res(ctx.json({ success: true }));
        })
      );

      renderWithProviders(<DashboardPage />);
      await screen.findByTestId('hecho-card');

      // Open importance dialog
      const importanceButton = screen.getByRole('button', { name: /cambiar importancia/i });
      await user.click(importanceButton);

      // Try to update
      const dialog = screen.getByRole('dialog');
      const confirmButton = within(dialog).getByRole('button', { name: /confirmar/i });
      await user.click(confirmButton);

      // Should show error notification
      await waitFor(() => {
        expect(screen.getByText(/error al actualizar/i)).toBeInTheDocument();
      });

      // Dialog should remain open for retry
      expect(screen.getByRole('dialog')).toBeInTheDocument();

      // Retry the update
      await user.click(confirmButton);

      // Should succeed on retry
      await waitFor(() => {
        expect(screen.getByText(/importancia actualizada/i)).toBeInTheDocument();
      });
    });

    it('should validate form inputs before submission', async () => {
      renderWithProviders(<DashboardPage />);
      await screen.findByTestId('hecho-card');

      // Open mark as false dialog
      const markFalseButton = screen.getByRole('button', { name: /marcar como falso/i });
      await user.click(markFalseButton);

      const dialog = screen.getByRole('dialog');
      const confirmButton = within(dialog).getByRole('button', { name: /confirmar/i });
      
      // Try to submit without justification
      await user.click(confirmButton);

      // Should show validation error
      await waitFor(() => {
        expect(screen.getByText(/justificación requerida/i)).toBeInTheDocument();
      });

      // Fill justification
      const justificationInput = within(dialog).getByRole('textbox');
      await user.type(justificationInput, 'Valid justification');

      // Should now allow submission
      await user.click(confirmButton);

      await waitFor(() => {
        expect(screen.queryByText(/justificación requerida/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Pagination Error Recovery', () => {
    it('should handle pagination failures gracefully', async () => {
      let pageRequests = 0;
      
      server.use(
        rest.get(`${API_BASE_URL}/api/hechos`, (req, res, ctx) => {
          pageRequests++;
          const page = Number(req.url.searchParams.get('page')) || 1;
          
          // Fail on page 2
          if (page === 2) {
            return res(
              ctx.status(500),
              ctx.json({ error: 'Page load failed' })
            );
          }
          
          return res(
            ctx.json({
              hechos: [{
                id: page,
                contenido: `Page ${page} content`,
                fechaOcurrencia: new Date().toISOString(),
                importancia: 5,
                tipoHecho: 'SUCESO',
                articuloMetadata: {
                  titulo: 'Test',
                  medio: 'Test Media',
                  fecha_publicacion: new Date().toISOString()
                }
              }],
              total: 50,
              page,
              totalPages: 3
            })
          );
        })
      );

      renderWithProviders(<DashboardPage />);
      await screen.findByText(/page 1 content/i);

      // Try to navigate to page 2
      const nextButton = screen.getByRole('button', { name: /siguiente página/i });
      await user.click(nextButton);

      // Should show error but stay on current page
      await waitFor(() => {
        expect(screen.getByText(/error al cargar la página/i)).toBeInTheDocument();
      });

      // Should still show page 1 content
      expect(screen.getByText(/page 1 content/i)).toBeInTheDocument();

      // Try again - navigate to page 3
      await user.click(nextButton);
      await user.click(nextButton);

      // Should skip failed page and go to page 3
      await waitFor(() => {
        expect(screen.getByText(/page 3 content/i)).toBeInTheDocument();
      });
    });
  });

  describe('Session Recovery', () => {
    it('should preserve user state after error recovery', async () => {
      server.use(
        rest.get(`${API_BASE_URL}/api/hechos`, (req, res, ctx) => {
          // Check if filters are preserved
          const tipo = req.url.searchParams.get('tipo_hecho');
          
          return res(
            ctx.json({
              hechos: [{
                id: 1,
                contenido: `Filtered by: ${tipo || 'none'}`,
                fechaOcurrencia: new Date().toISOString(),
                importancia: 5,
                tipoHecho: tipo || 'SUCESO',
                articuloMetadata: {
                  titulo: 'Test',
                  medio: 'Test Media',
                  fecha_publicacion: new Date().toISOString()
                }
              }],
              total: 1,
              page: 1,
              totalPages: 1
            })
          );
        })
      );

      renderWithProviders(<DashboardPage />);
      await screen.findByTestId('hecho-card');

      // Apply filter
      const filterButton = screen.getByRole('button', { name: /filtros/i });
      await user.click(filterButton);

      const tipoSelect = screen.getByLabelText(/tipo de hecho/i);
      await user.click(tipoSelect);
      await user.click(screen.getByRole('option', { name: /declaración/i }));

      // Wait for filtered results
      await waitFor(() => {
        expect(screen.getByText(/filtered by: declaracion/i)).toBeInTheDocument();
      });

      // Simulate error and recovery
      server.use(
        rest.get(`${API_BASE_URL}/api/hechos`, (req, res, ctx) => {
          return res.networkError('Temporary network issue');
        })
      );

      // Trigger refresh
      const refreshButton = screen.getByRole('button', { name: /actualizar/i });
      await user.click(refreshButton);

      // Reset to working endpoint
      server.resetHandlers();

      // Retry
      const retryButton = await screen.findByRole('button', { name: /reintentar/i });
      await user.click(retryButton);

      // Filters should be preserved after recovery
      await waitFor(() => {
        expect(screen.getByText(/filtered by: declaracion/i)).toBeInTheDocument();
      });
    });
  });
});
