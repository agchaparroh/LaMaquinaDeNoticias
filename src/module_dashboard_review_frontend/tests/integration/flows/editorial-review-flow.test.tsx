import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../../test-utils';
import App from '@/App';
import { server } from '../../mocks/server';
import { rest } from 'msw';
import { API_BASE_URL } from '@/utils/env';

describe('Editorial Review Flow - Complete Integration', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    // Reset any mocks
    vi.clearAllMocks();
  });

  afterEach(() => {
    // Reset MSW handlers
    server.resetHandlers();
  });

  describe('Complete Editorial Workflow', () => {
    it('should complete full editorial review process', async () => {
      // Arrange - Render the entire app
      renderWithProviders(<App />);

      // Act & Assert - Wait for initial load
      expect(screen.getByText(/cargando hechos/i)).toBeInTheDocument();
      
      // Wait for data to load
      await waitFor(() => {
        expect(screen.queryByText(/cargando hechos/i)).not.toBeInTheDocument();
      });

      // Verify dashboard loaded with hechos
      const hechoCards = await screen.findAllByTestId('hecho-card');
      expect(hechoCards.length).toBeGreaterThan(0);

      // Step 1: Apply filters
      const filterButton = screen.getByRole('button', { name: /filtros/i });
      await user.click(filterButton);

      // Filter by medio
      const medioSelect = screen.getByLabelText(/medio/i);
      await user.click(medioSelect);
      await user.click(screen.getByRole('option', { name: /el país/i }));

      // Filter by importance
      const importanceSlider = screen.getByLabelText(/importancia mínima/i);
      await user.click(importanceSlider);

      // Wait for filtered results
      await waitFor(() => {
        const filteredCards = screen.getAllByTestId('hecho-card');
        expect(filteredCards.length).toBeLessThan(hechoCards.length);
      });

      // Step 2: Open detail modal
      const firstHecho = screen.getAllByTestId('hecho-card')[0];
      await user.click(firstHecho);

      // Verify modal opened
      const modal = await screen.findByRole('dialog');
      expect(modal).toBeInTheDocument();
      expect(within(modal).getByText(/detalles del hecho/i)).toBeInTheDocument();

      // Close modal
      const closeButton = within(modal).getByRole('button', { name: /cerrar/i });
      await user.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });

      // Step 3: Change importance
      const importanceButton = screen.getAllByRole('button', { name: /cambiar importancia/i })[0];
      await user.click(importanceButton);

      // Update importance in dialog
      const importanceDialog = await screen.findByRole('dialog');
      const newImportanceSlider = within(importanceDialog).getByRole('slider');
      await user.click(newImportanceSlider); // Simulate slider change

      const confirmButton = within(importanceDialog).getByRole('button', { name: /confirmar/i });
      await user.click(confirmButton);

      // Verify success notification
      await waitFor(() => {
        expect(screen.getByText(/importancia actualizada/i)).toBeInTheDocument();
      });

      // Step 4: Mark as false
      const markFalseButton = screen.getAllByRole('button', { name: /marcar como falso/i })[0];
      await user.click(markFalseButton);

      // Fill justification
      const justificationDialog = await screen.findByRole('dialog');
      const justificationInput = within(justificationDialog).getByRole('textbox');
      await user.type(justificationInput, 'Información incorrecta verificada con fuentes oficiales');

      const confirmFalseButton = within(justificationDialog).getByRole('button', { name: /confirmar/i });
      await user.click(confirmFalseButton);

      // Verify success
      await waitFor(() => {
        expect(screen.getByText(/marcado como falso/i)).toBeInTheDocument();
      });

      // Step 5: Pagination
      const nextPageButton = screen.getByRole('button', { name: /siguiente página/i });
      await user.click(nextPageButton);

      // Verify new content loaded
      await waitFor(() => {
        const pageInfo = screen.getByText(/página 2/i);
        expect(pageInfo).toBeInTheDocument();
      });
    });

    it('should handle API errors gracefully and fallback to mocks', async () => {
      // Simulate API failure
      server.use(
        rest.get(`${API_BASE_URL}/api/hechos`, (req, res, ctx) => {
          return res(ctx.status(500), ctx.json({ error: 'Internal Server Error' }));
        })
      );

      renderWithProviders(<App />);

      // Should show error briefly
      await waitFor(() => {
        expect(screen.getByText(/error al cargar/i)).toBeInTheDocument();
      });

      // Should fallback to mock data
      await waitFor(() => {
        const hechoCards = screen.getAllByTestId('hecho-card');
        expect(hechoCards.length).toBeGreaterThan(0);
        expect(screen.getByText(/usando datos de respaldo/i)).toBeInTheDocument();
      });
    });

    it('should persist filters when navigating between pages', async () => {
      renderWithProviders(<App />);

      // Wait for initial load
      await screen.findAllByTestId('hecho-card');

      // Apply filters
      const filterButton = screen.getByRole('button', { name: /filtros/i });
      await user.click(filterButton);

      const tipoSelect = screen.getByLabelText(/tipo de hecho/i);
      await user.click(tipoSelect);
      await user.click(screen.getByRole('option', { name: /declaración/i }));

      // Navigate to page 2
      const nextPageButton = await screen.findByRole('button', { name: /siguiente página/i });
      await user.click(nextPageButton);

      // Navigate back to page 1
      const prevPageButton = await screen.findByRole('button', { name: /página anterior/i });
      await user.click(prevPageButton);

      // Verify filter is still applied
      const activeFilter = screen.getByText(/declaración/i);
      expect(activeFilter).toBeInTheDocument();
    });
  });

  describe('Concurrent Operations Handling', () => {
    it('should handle multiple simultaneous update requests', async () => {
      renderWithProviders(<App />);

      await screen.findAllByTestId('hecho-card');

      // Get multiple importance buttons
      const importanceButtons = screen.getAllByRole('button', { name: /cambiar importancia/i });
      
      // Click multiple buttons quickly
      await user.click(importanceButtons[0]);
      await user.click(importanceButtons[1]);

      // Should only show one dialog
      const dialogs = screen.getAllByRole('dialog');
      expect(dialogs).toHaveLength(1);
    });

    it('should cancel previous filter requests when applying new filters rapidly', async () => {
      let requestCount = 0;
      server.use(
        rest.get(`${API_BASE_URL}/api/hechos`, (req, res, ctx) => {
          requestCount++;
          return res(
            ctx.delay(100), // Add delay to simulate network
            ctx.json({ 
              hechos: [], 
              total: 0,
              page: 1,
              totalPages: 1 
            })
          );
        })
      );

      renderWithProviders(<App />);

      // Apply multiple filters rapidly
      const filterButton = await screen.findByRole('button', { name: /filtros/i });
      await user.click(filterButton);

      const searchInput = screen.getByPlaceholderText(/buscar/i);
      
      // Type rapidly
      await user.type(searchInput, 'test1');
      await user.clear(searchInput);
      await user.type(searchInput, 'test2');
      await user.clear(searchInput);
      await user.type(searchInput, 'test3');

      // Wait for debounce and final request
      await waitFor(() => {
        // Should not make a request for each keystroke due to debounce
        expect(requestCount).toBeLessThan(5);
      });
    });
  });

  describe('Auto-refresh Functionality', () => {
    it('should auto-refresh data when enabled', async () => {
      vi.useFakeTimers();
      
      let fetchCount = 0;
      server.use(
        rest.get(`${API_BASE_URL}/api/hechos`, (req, res, ctx) => {
          fetchCount++;
          return res(
            ctx.json({
              hechos: [{
                id: fetchCount,
                contenido: `Hecho actualizado ${fetchCount}`,
                fechaOcurrencia: new Date().toISOString(),
                importancia: 8,
                tipoHecho: 'DECLARACION',
                articuloMetadata: {
                  titulo: 'Artículo de prueba',
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

      renderWithProviders(<App />);

      // Wait for initial load
      await screen.findByText(/hecho actualizado 1/i);
      expect(fetchCount).toBe(1);

      // Enable auto-refresh
      const autoRefreshToggle = screen.getByLabelText(/auto-actualizar/i);
      await user.click(autoRefreshToggle);

      // Fast-forward 30 seconds
      vi.advanceTimersByTime(30000);

      // Wait for refresh
      await waitFor(() => {
        expect(screen.getByText(/hecho actualizado 2/i)).toBeInTheDocument();
        expect(fetchCount).toBe(2);
      });

      vi.useRealTimers();
    });
  });

  describe('Accessibility Features', () => {
    it('should support keyboard navigation throughout the application', async () => {
      renderWithProviders(<App />);

      await screen.findAllByTestId('hecho-card');

      // Tab to first interactive element
      await user.tab();
      
      // Should focus on filter button
      expect(screen.getByRole('button', { name: /filtros/i })).toHaveFocus();

      // Tab through hecho cards
      await user.tab();
      await user.tab();
      
      // Press Enter to open detail modal
      await user.keyboard('{Enter}');

      // Modal should be open
      const modal = await screen.findByRole('dialog');
      expect(modal).toBeInTheDocument();

      // Press Escape to close modal
      await user.keyboard('{Escape}');

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });
    });

    it('should announce important updates to screen readers', async () => {
      renderWithProviders(<App />);

      await screen.findAllByTestId('hecho-card');

      // Change importance
      const importanceButton = screen.getAllByRole('button', { name: /cambiar importancia/i })[0];
      await user.click(importanceButton);

      const dialog = await screen.findByRole('dialog');
      const confirmButton = within(dialog).getByRole('button', { name: /confirmar/i });
      await user.click(confirmButton);

      // Check for aria-live announcement
      const announcement = await screen.findByRole('status');
      expect(announcement).toHaveTextContent(/importancia actualizada/i);
    });
  });
});
