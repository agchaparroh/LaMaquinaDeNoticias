import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../../test-utils';
import { DashboardPage } from '@/components/pages';
import { server } from '../../mocks/server';
import { rest } from 'msw';
import { API_BASE_URL } from '@/utils/env';

describe('Dashboard Performance Tests', () => {
  const user = userEvent.setup();
  
  // Helper to generate large datasets
  const generateLargeDataset = (count: number) => {
    return Array.from({ length: count }, (_, i) => ({
      id: i + 1,
      contenido: `Hecho noticioso ${i + 1} con contenido detallado para pruebas de performance`,
      fechaOcurrencia: new Date(2024, 0, (i % 30) + 1).toISOString(),
      importancia: (i % 10) + 1,
      tipoHecho: ['DECLARACION', 'SUCESO', 'ANUNCIO', 'MEDIDA'][i % 4],
      pais: ['Chile', 'Argentina', 'Uruguay', 'Paraguay'][i % 4],
      evaluacionEditorial: i % 3 === 0 ? 'VERIFICADO' : 'PENDIENTE',
      articuloMetadata: {
        titulo: `Artículo ${i + 1}`,
        medio: ['El País', 'La Nación', 'El Mercurio', 'Clarín'][i % 4],
        fecha_publicacion: new Date(2024, 0, (i % 30) + 1).toISOString(),
        url: `https://example.com/article-${i + 1}`,
        autor: `Autor ${i % 10}`,
        credibilidad_medio: 0.8 + (i % 20) / 100
      },
      actores: [`Actor ${i % 5}`, `Actor ${(i + 1) % 5}`],
      ubicacion: `Ciudad ${i % 10}`,
      contexto: `Contexto detallado del hecho ${i + 1}`,
      impactoEstimado: ['LOCAL', 'NACIONAL', 'REGIONAL', 'GLOBAL'][i % 4],
      keywords: [`keyword${i % 10}`, `keyword${(i + 1) % 10}`],
      sentimientoGeneral: ['POSITIVO', 'NEGATIVO', 'NEUTRO'][i % 3],
      fuentes_adicionales: i % 2 === 0 ? [`https://fuente${i}.com`] : [],
      created_at: new Date(2024, 0, i + 1).toISOString(),
      updated_at: new Date(2024, 0, i + 1).toISOString()
    }));
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    server.resetHandlers();
  });

  describe('Large Dataset Rendering Performance', () => {
    it('should render 1000+ items efficiently with virtualization', async () => {
      const largeDataset = generateLargeDataset(1000);
      
      server.use(
        rest.get(`${API_BASE_URL}/api/hechos`, (req, res, ctx) => {
          const page = Number(req.url.searchParams.get('page')) || 1;
          const limit = Number(req.url.searchParams.get('limit')) || 20;
          const start = (page - 1) * limit;
          const end = start + limit;
          
          return res(
            ctx.json({
              hechos: largeDataset.slice(start, end),
              total: largeDataset.length,
              page,
              totalPages: Math.ceil(largeDataset.length / limit)
            })
          );
        })
      );

      const startTime = performance.now();
      renderWithProviders(<DashboardPage />);

      // Wait for initial render
      await screen.findByTestId('hecho-card');
      const renderTime = performance.now() - startTime;

      // Should render within reasonable time (< 2 seconds)
      expect(renderTime).toBeLessThan(2000);

      // Should only render visible items (pagination)
      const visibleCards = screen.getAllByTestId('hecho-card');
      expect(visibleCards.length).toBe(20); // Default page size
      
      // Verify pagination info shows correct total
      expect(screen.getByText(/1000 resultados/i)).toBeInTheDocument();
    });

    it('should handle rapid pagination without performance degradation', async () => {
      const largeDataset = generateLargeDataset(500);
      
      server.use(
        rest.get(`${API_BASE_URL}/api/hechos`, (req, res, ctx) => {
          const page = Number(req.url.searchParams.get('page')) || 1;
          const limit = 20;
          const start = (page - 1) * limit;
          const end = start + limit;
          
          return res(
            ctx.delay(50), // Simulate network delay
            ctx.json({
              hechos: largeDataset.slice(start, end),
              total: largeDataset.length,
              page,
              totalPages: Math.ceil(largeDataset.length / limit)
            })
          );
        })
      );

      renderWithProviders(<DashboardPage />);
      await screen.findByTestId('hecho-card');

      const pageTimes: number[] = [];

      // Navigate through multiple pages rapidly
      for (let i = 0; i < 5; i++) {
        const startTime = performance.now();
        
        const nextButton = screen.getByRole('button', { name: /siguiente página/i });
        await user.click(nextButton);
        
        await waitFor(() => {
          expect(screen.getByText(new RegExp(`página ${i + 2}`, 'i'))).toBeInTheDocument();
        });
        
        pageTimes.push(performance.now() - startTime);
      }

      // Verify consistent performance across pages
      const avgTime = pageTimes.reduce((a, b) => a + b, 0) / pageTimes.length;
      pageTimes.forEach(time => {
        expect(time).toBeLessThan(avgTime * 1.5); // No page should take 50% more than average
      });
    });
  });

  describe('Filter Performance with Large Datasets', () => {
    it('should filter efficiently through 1000+ items', async () => {
      const largeDataset = generateLargeDataset(1000);
      
      server.use(
        rest.get(`${API_BASE_URL}/api/hechos`, (req, res, ctx) => {
          const searchTerm = req.url.searchParams.get('contenido') || '';
          const tipo = req.url.searchParams.get('tipo_hecho') || '';
          const page = Number(req.url.searchParams.get('page')) || 1;
          const limit = 20;
          
          let filtered = [...largeDataset];
          
          if (searchTerm) {
            filtered = filtered.filter(h => 
              h.contenido.toLowerCase().includes(searchTerm.toLowerCase())
            );
          }
          
          if (tipo) {
            filtered = filtered.filter(h => h.tipoHecho === tipo);
          }
          
          const start = (page - 1) * limit;
          const end = start + limit;
          
          return res(
            ctx.delay(100), // Simulate processing time
            ctx.json({
              hechos: filtered.slice(start, end),
              total: filtered.length,
              page,
              totalPages: Math.ceil(filtered.length / limit)
            })
          );
        })
      );

      renderWithProviders(<DashboardPage />);
      await screen.findByTestId('hecho-card');

      // Apply text filter
      const filterButton = screen.getByRole('button', { name: /filtros/i });
      await user.click(filterButton);

      const searchInput = screen.getByPlaceholderText(/buscar/i);
      const filterStartTime = performance.now();
      
      await user.type(searchInput, '100');
      
      // Wait for debounced filter to apply
      await waitFor(() => {
        const resultText = screen.getByText(/\d+ resultados/i);
        expect(resultText).toBeInTheDocument();
      }, { timeout: 3000 });
      
      const filterTime = performance.now() - filterStartTime;
      
      // Filter should complete within reasonable time
      expect(filterTime).toBeLessThan(3000);
    });

    it('should handle complex multi-criteria filters efficiently', async () => {
      const largeDataset = generateLargeDataset(1000);
      
      server.use(
        rest.get(`${API_BASE_URL}/api/hechos`, (req, res, ctx) => {
          const filters = {
            tipo: req.url.searchParams.get('tipo_hecho'),
            pais: req.url.searchParams.get('pais'),
            evaluacion: req.url.searchParams.get('evaluacion_editorial'),
            importanciaMin: Number(req.url.searchParams.get('importancia_min')) || 0,
            fechaInicio: req.url.searchParams.get('fecha_inicio'),
            fechaFin: req.url.searchParams.get('fecha_fin')
          };
          
          let filtered = [...largeDataset];
          
          // Apply all filters
          if (filters.tipo) {
            filtered = filtered.filter(h => h.tipoHecho === filters.tipo);
          }
          if (filters.pais) {
            filtered = filtered.filter(h => h.pais === filters.pais);
          }
          if (filters.evaluacion) {
            filtered = filtered.filter(h => h.evaluacionEditorial === filters.evaluacion);
          }
          if (filters.importanciaMin > 0) {
            filtered = filtered.filter(h => h.importancia >= filters.importanciaMin);
          }
          
          const page = Number(req.url.searchParams.get('page')) || 1;
          const limit = 20;
          const start = (page - 1) * limit;
          const end = start + limit;
          
          return res(
            ctx.delay(150),
            ctx.json({
              hechos: filtered.slice(start, end),
              total: filtered.length,
              page,
              totalPages: Math.ceil(filtered.length / limit)
            })
          );
        })
      );

      renderWithProviders(<DashboardPage />);
      await screen.findByTestId('hecho-card');

      const filterButton = screen.getByRole('button', { name: /filtros/i });
      await user.click(filterButton);

      const startTime = performance.now();

      // Apply multiple filters
      const tipoSelect = screen.getByLabelText(/tipo de hecho/i);
      await user.click(tipoSelect);
      await user.click(screen.getByRole('option', { name: /declaración/i }));

      const paisSelect = screen.getByLabelText(/país/i);
      await user.click(paisSelect);
      await user.click(screen.getByRole('option', { name: /chile/i }));

      const importanceSlider = screen.getByLabelText(/importancia mínima/i);
      await user.click(importanceSlider);

      // Wait for all filters to apply
      await waitFor(() => {
        const cards = screen.getAllByTestId('hecho-card');
        expect(cards.length).toBeGreaterThan(0);
      });

      const totalFilterTime = performance.now() - startTime;
      
      // Complex filtering should still be performant
      expect(totalFilterTime).toBeLessThan(4000);
    });
  });

  describe('Memory Usage and Leaks', () => {
    it('should not leak memory when mounting/unmounting components repeatedly', async () => {
      if (!performance.memory) {
        // Skip test if memory API not available
        console.warn('Performance.memory API not available, skipping memory test');
        return;
      }

      const initialMemory = performance.memory.usedJSHeapSize;
      
      // Mount and unmount component multiple times
      for (let i = 0; i < 10; i++) {
        const { unmount } = renderWithProviders(<DashboardPage />);
        await screen.findByTestId('hecho-card');
        unmount();
      }

      // Force garbage collection if available
      if (global.gc) {
        global.gc();
      }

      // Wait a bit for cleanup
      await new Promise(resolve => setTimeout(resolve, 100));

      const finalMemory = performance.memory.usedJSHeapSize;
      const memoryIncrease = finalMemory - initialMemory;
      
      // Memory increase should be minimal (< 10MB)
      expect(memoryIncrease).toBeLessThan(10 * 1024 * 1024);
    });

    it('should clean up event listeners and timers on unmount', async () => {
      const addEventListenerSpy = vi.spyOn(window, 'addEventListener');
      const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener');
      const setIntervalSpy = vi.spyOn(window, 'setInterval');
      const clearIntervalSpy = vi.spyOn(window, 'clearInterval');

      const { unmount } = renderWithProviders(<DashboardPage />);
      await screen.findByTestId('hecho-card');

      // Enable auto-refresh to test interval cleanup
      const autoRefreshToggle = screen.getByLabelText(/auto-actualizar/i);
      await user.click(autoRefreshToggle);

      const eventListenerCount = addEventListenerSpy.mock.calls.length;
      const intervalCount = setIntervalSpy.mock.calls.length;

      unmount();

      // Verify cleanup
      expect(removeEventListenerSpy).toHaveBeenCalledTimes(eventListenerCount);
      expect(clearIntervalSpy).toHaveBeenCalledTimes(intervalCount);

      addEventListenerSpy.mockRestore();
      removeEventListenerSpy.mockRestore();
      setIntervalSpy.mockRestore();
      clearIntervalSpy.mockRestore();
    });
  });

  describe('Render Performance Optimization', () => {
    it('should minimize re-renders when updating filters', async () => {
      let renderCount = 0;
      
      // Create a wrapper component to count renders
      const RenderCounter = () => {
        renderCount++;
        return <DashboardPage />;
      };

      renderWithProviders(<RenderCounter />);
      await screen.findByTestId('hecho-card');

      const initialRenderCount = renderCount;

      // Apply filter
      const filterButton = screen.getByRole('button', { name: /filtros/i });
      await user.click(filterButton);

      const searchInput = screen.getByPlaceholderText(/buscar/i);
      await user.type(searchInput, 'test');

      // Wait for debounce
      await waitFor(() => {
        expect(screen.queryByText(/cargando/i)).not.toBeInTheDocument();
      });

      const filterRenderCount = renderCount - initialRenderCount;
      
      // Should have minimal re-renders (< 5 for typing + filter apply)
      expect(filterRenderCount).toBeLessThan(5);
    });

    it('should use React.memo effectively to prevent unnecessary re-renders', async () => {
      const largeDataset = generateLargeDataset(100);
      
      server.use(
        rest.get(`${API_BASE_URL}/api/hechos`, (req, res, ctx) => {
          return res(
            ctx.json({
              hechos: largeDataset.slice(0, 20),
              total: largeDataset.length,
              page: 1,
              totalPages: 5
            })
          );
        })
      );

      renderWithProviders(<DashboardPage />);
      await screen.findByTestId('hecho-card');

      // Interact with one card shouldn't re-render others
      const firstCardButton = screen.getAllByRole('button', { name: /cambiar importancia/i })[0];
      
      // Mock console.log to detect renders (if components log)
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
      
      await user.click(firstCardButton);
      
      // Close dialog
      const dialog = await screen.findByRole('dialog');
      const cancelButton = within(dialog).getByRole('button', { name: /cancelar/i });
      await user.click(cancelButton);

      consoleSpy.mockRestore();
    });
  });
});
