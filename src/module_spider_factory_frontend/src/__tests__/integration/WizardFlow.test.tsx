import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from '../../App';
import { setupServer } from 'msw/node';
import { rest } from 'msw';

// Según SECCIÓN 8.4 - Tests de integración
// Flujo completo del wizard
// Procesamiento batch
// WebSocket updates

const server = setupServer(
  rest.post('/api/analyze', (req, res, ctx) => {
    return res(
      ctx.delay(100),
      ctx.json({
        strategy: 'rss',
        confidence: 0.95,
        rss_url: 'https://example.com/rss',
        needs_javascript: false,
        sample_articles: [
          {
            title: 'Test Article',
            date: '2023-01-01',
            excerpt: 'Test excerpt'
          }
        ]
      })
    );
  }),

  rest.post('/api/generate', (req, res, ctx) => {
    return res(
      ctx.delay(200),
      ctx.json({
        spider_name: 'elpais_internacional',
        file_path: '/spiders/elpais_internacional.py',
        code_preview: 'import scrapy\n\nclass ElPaisSpider(scrapy.Spider)...',
        is_valid: true
      })
    );
  })
);

describe('Wizard Integration Flow', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false }
      }
    });
    server.listen();
  });

  const renderApp = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </QueryClientProvider>
    );
  };

  it('should complete full wizard flow', async () => {
    const user = userEvent.setup();
    renderApp();

    // Navigate to wizard
    await user.click(screen.getByText('Wizard'));

    // Step 1: Fill basic information
    await user.type(screen.getByLabelText('Medio'), 'El País');
    await user.click(screen.getByLabelText('Área Geográfica'));
    await user.click(screen.getByText('ESPAÑA'));
    await user.click(screen.getByLabelText('Tipo de Medio'));
    await user.click(screen.getByText('Diario'));

    // Go to step 2
    await user.click(screen.getByText('Siguiente'));

    // Step 2: Fill URL and section
    await user.type(screen.getByLabelText('Sección'), 'Internacional');
    await user.type(screen.getByLabelText('URL de la sección'), 'https://elpais.com/internacional');

    // Go to step 3 (Analysis)
    await user.click(screen.getByText('Siguiente'));

    // Wait for analysis to complete
    await waitFor(() => {
      expect(screen.getByText('Análisis completado')).toBeInTheDocument();
    }, { timeout: 5000 });

    // Should show detected articles
    expect(screen.getByText('Artículos detectados:')).toBeInTheDocument();
    expect(screen.getByText('Test Article')).toBeInTheDocument();

    // Go to step 4 (Review)
    await user.click(screen.getByText('Siguiente'));

    // Generate spider
    await user.click(screen.getByText('Generar Spider'));

    // Wait for generation to complete
    await waitFor(() => {
      expect(screen.getByText('Spider generado exitosamente')).toBeInTheDocument();
    }, { timeout: 10000 });

    // Should show generated code preview
    expect(screen.getByText(/import scrapy/)).toBeInTheDocument();
    expect(screen.getByText(/ElPaisSpider/)).toBeInTheDocument();
  });

  it('should handle validation errors in workflow', async () => {
    const user = userEvent.setup();
    renderApp();

    await user.click(screen.getByText('Wizard'));

    // Try to proceed without filling required fields
    await user.click(screen.getByText('Siguiente'));

    await waitFor(() => {
      expect(screen.getByText('El nombre del medio es obligatorio')).toBeInTheDocument();
    });
  });

  it('should persist wizard state across page refreshes', async () => {
    const user = userEvent.setup();
    renderApp();

    await user.click(screen.getByText('Wizard'));
    await user.type(screen.getByLabelText('Medio'), 'Test Media');

    // Simulate page refresh by re-rendering
    queryClient.clear();
    renderApp();

    await user.click(screen.getByText('Wizard'));

    // Should show notification about loaded draft
    await waitFor(() => {
      expect(screen.getByText(/Borrador cargado/)).toBeInTheDocument();
    });

    // Field should be populated
    expect(screen.getByDisplayValue('Test Media')).toBeInTheDocument();
  });
});