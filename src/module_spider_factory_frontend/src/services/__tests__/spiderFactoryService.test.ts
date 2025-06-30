import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { setupServer } from 'msw/node';
import { rest } from 'msw';
import { spiderFactoryService } from '../spiderFactoryService';

// Según SECCIÓN 8.2 - Tests para servicios
// spiderFactoryService.test.ts
// Tests con MSW (Mock Service Worker)

const server = setupServer(
  rest.post('/api/analyze', (req, res, ctx) => {
    return res(
      ctx.json({
        strategy: 'rss',
        confidence: 0.95,
        rss_url: 'https://example.com/rss',
        needs_javascript: false
      })
    );
  }),

  rest.post('/api/check-duplicate', (req, res, ctx) => {
    return res(
      ctx.json({
        exists: false,
        message: 'Nombre disponible'
      })
    );
  }),

  rest.post('/api/generate', (req, res, ctx) => {
    return res(
      ctx.json({
        spider_name: 'test_spider',
        file_path: '/path/to/spider.py',
        code_preview: 'import scrapy...',
        is_valid: true
      })
    );
  })
);

describe('SpiderFactoryService', () => {
  beforeEach(() => server.listen());
  afterEach(() => server.resetHandlers());

  it('should analyze site successfully', async () => {
    const result = await spiderFactoryService.analyze({
      url: 'https://example.com',
      medio: 'Test Media',
      seccion: 'News',
      area_geografica: 'ESPAÑA',
      tipo_medio: 'diario',
      frecuencia_minutos: 60
    });

    expect(result.strategy).toBe('rss');
    expect(result.confidence).toBe(0.95);
  });

  it('should check for duplicates', async () => {
    const result = await spiderFactoryService.checkDuplicate('Test Media', 'News');
    expect(result.exists).toBe(false);
  });

  it('should generate spider', async () => {
    const analysisResult = {
      strategy: 'rss',
      confidence: 0.95,
      rss_url: 'https://example.com/rss',
      needs_javascript: false
    };

    const spiderConfig = {
      medio: 'Test Media',
      seccion: 'News',
      area_geografica: 'ESPAÑA',
      tipo_medio: 'diario',
      frecuencia_minutos: 60
    };

    const result = await spiderFactoryService.generateSpider(analysisResult, spiderConfig);
    expect(result.spider_name).toBe('test_spider');
    expect(result.is_valid).toBe(true);
  });

  it('should handle API errors gracefully', async () => {
    server.use(
      rest.post('/api/analyze', (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ error: 'Internal Server Error' }));
      })
    );

    await expect(
      spiderFactoryService.analyze({
        url: 'https://example.com',
        medio: 'Test',
        seccion: 'Test',
        area_geografica: 'ESPAÑA',
        tipo_medio: 'diario',
        frecuencia_minutos: 60
      })
    ).rejects.toThrow();
  });
});