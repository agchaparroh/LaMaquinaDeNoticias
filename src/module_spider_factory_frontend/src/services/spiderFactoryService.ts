import type { 
  AnalysisResult, 
  SpiderCode, 
  SiteAnalysisRequest,
  SpiderGenerationRequest 
} from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/spider-factory/api';

// Servicio para interactuar con la API del Spider Factory
class SpiderFactoryService {
  
  // Analizar un sitio web
  async analyzeSite(request: SiteAnalysisRequest): Promise<AnalysisResult> {
    try {
      const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Error en análisis: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      
      // Asegurar que devolvemos el formato correcto
      return {
        domain: data.domain || new URL(request.url).hostname,
        has_rss: data.has_rss || false,
        rss_url: data.rss_url,
        suggested_strategy: data.suggested_strategy || data.strategy || 'scraping',
        strategy: data.strategy || data.suggested_strategy || 'scraping',
        pattern_confidence: data.pattern_confidence || data.confidence || 0.5,
        confidence: data.confidence || data.pattern_confidence || 0.5,
        estimated_articles: data.estimated_articles,
        selectors: data.selectors,
        sample_articles: data.sample_articles || [],
        requires_javascript: data.requires_javascript || data.needs_javascript,
        needs_javascript: data.needs_javascript || data.requires_javascript,
        detected_patterns: data.detected_patterns
      };
    } catch (error) {
      console.error('Error analyzing site:', error);
      throw error; // Propagar el error real al componente
    }
  }

  // Generar un spider
  async generateSpider(request: SpiderGenerationRequest): Promise<SpiderCode> {
    try {
      const response = await fetch(`${API_BASE_URL}/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Error en generación: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      
      // Generar nombre del spider automáticamente
      const spider_name = `${request.medio.toLowerCase().replace(/\s+/g, '_')}_${request.seccion.toLowerCase().replace(/\s+/g, '_')}`;
      
      return {
        filename: data.filename || `${spider_name}.py`,
        spider_id: data.spider_id || `spider-${Date.now()}`,
        code: data.code || data.formatted_code,
        code_structure: data.code_structure,
        formatted_code: data.formatted_code || data.code,
        generation_metadata: data.generation_metadata || {
          timestamp: new Date().toISOString(),
          strategy: 'auto-detected',
          confidence: 0.8
        }
      };
    } catch (error) {
      console.error('Error generating spider:', error);
      throw error; // Propagar el error real al componente
    }
  }

  // Obtener historial (temporal)
  async getHistory(): Promise<any[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/history`);
      if (!response.ok) {
        throw new Error('No se pudo obtener el historial');
      }
      return await response.json();
    } catch (error) {
      console.warn('No se pudo conectar al backend, usando historial local');
      return [];
    }
  }

  // Obtener medios populares (temporal)
  async getPopularMedia(): Promise<any[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/popular-media`);
      if (!response.ok) {
        throw new Error('No se pudo obtener medios populares');
      }
      return await response.json();
    } catch (error) {
      console.warn('No se pudo conectar al backend');
      return [];
    }
  }

}

// Instancia singleton del servicio
export const spiderFactoryService = new SpiderFactoryService();
export default spiderFactoryService;