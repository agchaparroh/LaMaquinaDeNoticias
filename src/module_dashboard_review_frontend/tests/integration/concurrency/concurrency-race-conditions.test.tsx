import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../../test-utils';
import { DashboardPage } from '@/components/pages';
import { server } from '../../mocks/server';
import { rest } from 'msw';
import { API_BASE_URL } from '@/utils/env';

describe('Concurrency and Race Condition Tests', () => {
  const user = userEvent.setup();
  
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    server.resetHandlers();
  });

  describe('Concurrent API Requests', () => {
    it('should handle multiple simultaneous filter changes correctly', async () => {
      let requestOrder: string[] = [];
      let resolveCallbacks: Record<string, () => void> = {};
      
      server.use(
        rest.get(`${API_BASE_URL}/api/hechos`, async (req, res, ctx) => {
          const requestId = `${req.url.searchParams.get('contenido')}-${Date.now()}`;
          requestOrder.push(requestId);
          
          // Create a promise that we can resolve manually
          await new Promise(resolve => {
            resolveCallbacks[requestId] = resolve as () => void;
          });
          
          return res(
            ctx.json({
              hechos: [{
                id: 1,
                contenido: `Result for: ${req.url.searchParams.get('contenido')}`,
                fechaOcurrencia: new Date().toISOString(),
                importancia: 8,
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
        })
      );

      renderWithProviders(<DashboardPage />);
      
      // Wait for initial load
      await waitFor(() => {
        expect(requestOrder.length).toBeGreaterThan(0);
      });
      
      // Resolve initial request
      const initialRequest = requestOrder[0];
      resolveCallbacks[initialRequest]?.();
      
      await screen.findByTestId('hecho-card');

      // Open filters
      const filterButton = screen.getByRole('button', { name: /filtros/i });
      await user.click(filterButton);

      const searchInput = screen.getByPlaceholderText(/buscar/i);
      
      // Type multiple search terms rapidly
      await user.type(searchInput, 'first');
      await user.clear(searchInput);
      await user.type(searchInput, 'second');
      await user.clear(searchInput);
      await user.type(searchInput, 'third');

      // Wait for debounce and requests
      await waitFor(() => {
        // Should have made additional requests after initial
        expect(requestOrder.length).toBeGreaterThan(1);
      });

      // Resolve requests out of order (second, third, first)
      const requests = requestOrder.slice(1);
      if (requests[1]) resolveCallbacks[requests[1]]?.();
      if (requests[2]) resolveCallbacks[requests[2]]?.();
      if (requests[0]) resolveCallbacks[requests[0]]?.();

      // Should show the result from the last request made
      await waitFor(() => {
        expect(screen.getByText(/result for: third/i)).toBeInTheDocument();
      });
      
      // Should NOT show results from earlier requests
      expect(screen.queryByText(/result for: first/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/result for: second/i)).not.toBeInTheDocument();
    });

    it('should cancel in-flight requests when component unmounts', async () => {
      let abortedRequests = 0;
      
      server.use(
        rest.get(`${API_BASE_URL}/api/hechos`, async (req, res, ctx) => {
          // Listen for abort signal
          req.signal.addEventListener('abort', () => {
            abortedRequests++;
          });
          
          // Delay to ensure request is in-flight when we unmount
          await new Promise(resolve => setTimeout(resolve, 1000));
          
          return res(
            ctx.json({
              hechos: [],
              total: 0,
              page: 1,
              totalPages: 1
            })
          );
        })
      );

      const { unmount } = renderWithProviders(<DashboardPage />);
      
      // Wait a bit to ensure request is sent
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Unmount while request is in-flight
      unmount();
      
      // Wait to see if abort was called
      await new Promise(resolve => setTimeout(resolve, 100));
      
      expect(abortedRequests).toBeGreaterThan(0);
    });

    it('should handle rapid pagination without mixing results', async () => {
      let requestCount = 0;
      const delays: Record<number, number> = {
        1: 200,  // Page 1 - slow
        2: 50,   // Page 2 - fast
        3: 100   // Page 3 - medium
      };
      
      server.use(
        rest.get(`${API_BASE_URL}/api/hechos`, async (req, res, ctx) => {
          requestCount++;
          const page = Number(req.url.searchParams.get('page')) || 1;
          
          // Variable delay based on page
          await new Promise(resolve => setTimeout(resolve, delays[page] || 100));
          
          return res(
            ctx.json({
              hechos: [{
                id: page,
                contenido: `Content for page ${page}`,
                fechaOcurrencia: new Date().toISOString(),
                importancia: 5,
                tipoHecho: 'SUCESO',
                articuloMetadata: {
                  titulo: `Page ${page} Article`,
                  medio: 'Test Media',
                  fecha_publicacion: new Date().toISOString()
                }
              }],
              total: 100,
              page,
              totalPages: 5
            })
          );
        })
      );

      renderWithProviders(<DashboardPage />);
      
      // Wait for initial page 1 load
      await screen.findByText(/content for page 1/i);

      // Click next rapidly multiple times
      const nextButton = screen.getByRole('button', { name: /siguiente página/i });
      await user.click(nextButton); // Request page 2
      await user.click(nextButton); // Request page 3
      
      // Page 2 will respond faster than page 3, but we should see page 3
      await waitFor(() => {
        expect(screen.getByText(/content for page 3/i)).toBeInTheDocument();
        expect(screen.queryByText(/content for page 2/i)).not.toBeInTheDocument();
      });
      
      // Verify we made all requests
      expect(requestCount).toBe(3); // Initial + 2 paginations
    });
  });

  describe('State Update Race Conditions', () => {
    it('should handle concurrent feedback operations correctly', async () => {
      const feedbackRequests: Array<{ id: number; type: string }> = [];
      
      server.use(
        rest.put(`${API_BASE_URL}/api/hechos/:id/importancia`, async (req, res, ctx) => {
          const id = Number(req.params.id);
          feedbackRequests.push({ id, type: 'importancia' });
          
          // Simulate variable processing time
          await new Promise(resolve => setTimeout(resolve, Math.random() * 200));
          
          return res(ctx.json({ success: true }));
        }),
        rest.put(`${API_BASE_URL}/api/hechos/:id/marcar-falso`, async (req, res, ctx) => {
          const id = Number(req.params.id);
          feedbackRequests.push({ id, type: 'falso' });
          
          await new Promise(resolve => setTimeout(resolve, Math.random() * 200));
          
          return res(ctx.json({ success: true }));
        })
      );

      renderWithProviders(<DashboardPage />);
      await screen.findAllByTestId('hecho-card');

      // Start multiple operations on different hechos
      const importanceButtons = screen.getAllByRole('button', { name: /cambiar importancia/i });
      const markFalseButtons = screen.getAllByRole('button', { name: /marcar como falso/i });

      // Click operations in rapid succession
      await user.click(importanceButtons[0]);
      await user.click(markFalseButtons[1]);
      
      // Should show only one modal at a time
      const modals = screen.getAllByRole('dialog');
      expect(modals).toHaveLength(1);
      
      // Complete first operation
      const confirmButton = screen.getByRole('button', { name: /confirmar/i });
      await user.click(confirmButton);
      
      // Wait for notification
      await waitFor(() => {
        expect(screen.getByText(/actualizada|marcado/i)).toBeInTheDocument();
      });
      
      // All requests should have been made
      await waitFor(() => {
        expect(feedbackRequests.length).toBeGreaterThan(0);
      });
    });

    it('should maintain UI consistency during concurrent updates', async () => {
      let updateCount = 0;
      
      server.use(
        rest.get(`${API_BASE_URL}/api/hechos`, async (req, res, ctx) => {
          updateCount++;
          
          return res(
            ctx.json({
              hechos: [{
                id: 1,
                contenido: `Updated content ${updateCount}`,
                fechaOcurrencia: new Date().toISOString(),
                importancia: updateCount,
                tipoHecho: 'ANUNCIO',
                evaluacionEditorial: updateCount > 2 ? 'VERIFICADO' : 'PENDIENTE',
                articuloMetadata: {
                  titulo: 'Test Article',
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

      // Enable auto-refresh
      const autoRefreshToggle = screen.getByLabelText(/auto-actualizar/i);
      await user.click(autoRefreshToggle);

      // Simultaneously trigger manual refresh
      const refreshButton = screen.getByRole('button', { name: /actualizar/i });
      await user.click(refreshButton);
      await user.click(refreshButton); // Click twice rapidly

      // Wait for updates
      await waitFor(() => {
        expect(updateCount).toBeGreaterThan(1);
      });

      // UI should show consistent state (latest update)
      const content = screen.getByText(/updated content \d+/i);
      const contentNumber = parseInt(content.textContent?.match(/\d+/)?.[0] || '0');
      
      // Should show the latest update number
      expect(contentNumber).toBe(updateCount);
    });
  });

  describe('Debouncing and Throttling', () => {
    it('should properly debounce filter inputs', async () => {
      let searchRequests = 0;
      
      server.use(
        rest.get(`${API_BASE_URL}/api/hechos`, (req, res, ctx) => {
          if (req.url.searchParams.get('contenido')) {
            searchRequests++;
          }
          
          return res(
            ctx.json({
              hechos: [],
              total: 0,
              page: 1,
              totalPages: 1
            })
          );
        })
      );

      renderWithProviders(<DashboardPage />);
      await screen.findByRole('button', { name: /filtros/i });

      const filterButton = screen.getByRole('button', { name: /filtros/i });
      await user.click(filterButton);

      const searchInput = screen.getByPlaceholderText(/buscar/i);
      
      // Type rapidly
      const testString = 'testing debounce';
      for (const char of testString) {
        await user.type(searchInput, char);
        // Small delay between keystrokes
        await new Promise(resolve => setTimeout(resolve, 50));
      }

      // Wait for debounce period
      await new Promise(resolve => setTimeout(resolve, 500));

      // Should only make one request after debounce
      expect(searchRequests).toBe(1);
    });

    it('should handle filter changes during ongoing requests', async () => {
      let ongoingRequest: Promise<any> | null = null;
      let completedRequests = 0;
      
      server.use(
        rest.get(`${API_BASE_URL}/api/hechos`, async (req, res, ctx) => {
          const filter = req.url.searchParams.get('tipo_hecho');
          
          // Create a promise we can track
          ongoingRequest = new Promise(async (resolve) => {
            await new Promise(r => setTimeout(r, 200));
            completedRequests++;
            resolve(null);
          });
          
          await ongoingRequest;
          
          return res(
            ctx.json({
              hechos: [{
                id: 1,
                contenido: `Filtered by: ${filter || 'none'}`,
                fechaOcurrencia: new Date().toISOString(),
                importancia: 5,
                tipoHecho: filter || 'SUCESO',
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

      const filterButton = screen.getByRole('button', { name: /filtros/i });
      await user.click(filterButton);

      // Apply first filter
      const tipoSelect = screen.getByLabelText(/tipo de hecho/i);
      await user.click(tipoSelect);
      await user.click(screen.getByRole('option', { name: /declaración/i }));

      // Immediately apply another filter while first is processing
      await user.click(tipoSelect);
      await user.click(screen.getByRole('option', { name: /suceso/i }));

      // Wait for all requests to complete
      await waitFor(() => {
        expect(completedRequests).toBeGreaterThan(0);
      });

      // Should show result from the latest filter
      await waitFor(() => {
        expect(screen.getByText(/filtered by: suceso/i)).toBeInTheDocument();
      });
    });
  });

  describe('WebSocket-like Updates (Simulated)', () => {
    it('should handle real-time updates without conflicts', async () => {
      let version = 1;
      
      server.use(
        rest.get(`${API_BASE_URL}/api/hechos`, (req, res, ctx) => {
          return res(
            ctx.json({
              hechos: [{
                id: 1,
                contenido: `Version ${version} content`,
                fechaOcurrencia: new Date().toISOString(),
                importancia: 5,
                tipoHecho: 'SUCESO',
                version: version,
                articuloMetadata: {
                  titulo: 'Test Article',
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
      await screen.findByText(/version 1 content/i);

      // Simulate external update
      version = 2;

      // Enable auto-refresh to simulate real-time updates
      const autoRefreshToggle = screen.getByLabelText(/auto-actualizar/i);
      await user.click(autoRefreshToggle);

      // User starts editing while update happens
      const importanceButton = screen.getByRole('button', { name: /cambiar importancia/i });
      await user.click(importanceButton);

      // Simulate time passing for auto-refresh
      vi.useFakeTimers();
      vi.advanceTimersByTime(30000);
      vi.useRealTimers();

      // Wait for update
      await waitFor(() => {
        expect(screen.getByText(/version 2 content/i)).toBeInTheDocument();
      });

      // User dialog should still be open
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });
  });

  describe('Error Recovery with Concurrent Operations', () => {
    it('should recover from failed requests during concurrent operations', async () => {
      let requestCount = 0;
      
      server.use(
        rest.get(`${API_BASE_URL}/api/hechos`, (req, res, ctx) => {
          requestCount++;
          
          // Fail every other request
          if (requestCount % 2 === 0) {
            return res(
              ctx.status(500),
              ctx.json({ error: 'Internal Server Error' })
            );
          }
          
          return res(
            ctx.json({
              hechos: [{
                id: requestCount,
                contenido: `Success request ${requestCount}`,
                fechaOcurrencia: new Date().toISOString(),
                importancia: 5,
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
      
      // First request should succeed
      await screen.findByText(/success request 1/i);

      // Trigger multiple operations
      const refreshButton = screen.getByRole('button', { name: /actualizar/i });
      
      // Click refresh multiple times
      await user.click(refreshButton); // Will fail
      await user.click(refreshButton); // Will succeed
      
      // Should recover and show successful data
      await waitFor(() => {
        expect(screen.getByText(/success request 3/i)).toBeInTheDocument();
      });
      
      // Should not be stuck in error state
      expect(screen.queryByText(/error/i)).not.toBeInTheDocument();
    });

    it('should handle network timeout gracefully', async () => {
      let timeoutOccurred = false;
      
      server.use(
        rest.get(`${API_BASE_URL}/api/hechos`, async (req, res, ctx) => {
          // Simulate network timeout
          req.signal.addEventListener('abort', () => {
            timeoutOccurred = true;
          });
          
          // Long delay to trigger timeout
          await new Promise((resolve, reject) => {
            const timeout = setTimeout(resolve, 10000);
            req.signal.addEventListener('abort', () => {
              clearTimeout(timeout);
              reject(new Error('Request aborted'));
            });
          });
          
          return res(ctx.json({ hechos: [], total: 0, page: 1, totalPages: 1 }));
        })
      );

      renderWithProviders(<DashboardPage />);
      
      // Should show loading initially
      expect(screen.getByText(/cargando/i)).toBeInTheDocument();
      
      // Wait for timeout handling
      await waitFor(() => {
        // Should show error or fallback to mocks
        expect(screen.queryByText(/cargando/i)).not.toBeInTheDocument();
      }, { timeout: 5000 });
      
      // Should have content (either error message or mock data)
      const content = screen.queryByTestId('hecho-card') || screen.queryByText(/error/i);
      expect(content).toBeInTheDocument();
    });
  });
});
