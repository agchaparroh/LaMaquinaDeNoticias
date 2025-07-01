// Tipos centralizados para el módulo Spider Factory Frontend

// Tipos de estado comunes
export type Status = 'success' | 'error' | 'warning' | 'info' | 'pending'

// Tipos para el análisis de sitios web
export interface AnalysisResult {
  domain: string
  has_rss: boolean
  rss_url?: string
  suggested_strategy: 'rss' | 'scraping' | 'playwright'
  strategy: 'rss' | 'scraping' | 'playwright' // Alias para compatibilidad
  pattern_confidence: number
  confidence: number // Alias para compatibilidad
  estimated_articles?: number
  selectors?: {
    title?: string
    content?: string
    date?: string
    author?: string
    tags?: string
  }
  sample_articles?: Array<{
    title: string
    url?: string
    date?: string
    excerpt?: string // Añadido para compatibilidad
  }>
  requires_javascript?: boolean
  needs_javascript?: boolean // Alias para compatibilidad
  detected_patterns?: Array<{
    pattern: string
    confidence: number
  }>
}

// Tipos para la generación de spiders
export interface SpiderCode {
  filename: string
  spider_id?: string
  code?: string  // Añadido para compatibilidad con el servicio
  code_structure?: {
    imports: string[]
    spider_definition: string
    methods: string[]
  }
  formatted_code: string
  generation_metadata?: {
    timestamp?: string
    strategy?: string
    confidence?: number
  }
}

// Tipos para el procesamiento batch
export interface BatchItem {
  id: string
  url: string
  name: string
  medio: string // Añadido para compatibilidad
  seccion: string // Añadido para compatibilidad
  area_geografica: string // Añadido para compatibilidad
  tipo_medio: 'diario' | 'revista' | 'agencia' // Añadido para compatibilidad
  status: 'pending' | 'processing' | 'completed' | 'error'
  progress?: number
  result?: {
    spider_count: number
    strategy?: string
    error?: string
  }
}

// Tipos para mensajes WebSocket
export interface WebSocketMessage {
  type: string
  payload: unknown
}

export interface BatchProgressMessage {
  type: 'batch_progress'
  batch_id: string
  item: {
    url: string
    status: string
    result?: {
      spider_count: number
      strategy?: string
      error?: string
    }
  }
  progress: {
    current: number
    total: number
    percentage: number
  }
  timestamp: string
}

// Tipos para la configuración del sitio
// Según SECCIÓN 10.1 - Completar tipos TypeScript
export interface SpiderConfig {
  medio: string
  seccion: string
  url: string
  area_geografica: string
  tipo_medio: 'diario' | 'revista' | 'agencia'
  frecuencia_minutos: number
  rss_url?: string
  comentarios?: string
}


export interface Article {
  title: string
  date: string
  excerpt: string
  url?: string
}

// Según SECCIÓN 21.4 - Mantener compatibilidad
export interface SiteInfo {
  url: string
  name: string  // MANTENER por compatibilidad
  
  // Nuevos campos opcionales
  medio?: string
  seccion?: string
  area_geografica?: string
  tipo_medio?: 'diario' | 'revista' | 'agencia'
  frecuencia_minutos?: number
  rss_url?: string
  comentarios?: string
  tiene_rss?: boolean
  language?: string
  category?: string
}

// Interface unificada para wizard y análisis - SIMPLICIDAD MÁXIMA
export interface WizardData {
  url: string
  medio: string  // Nombre del medio (antes 'name')
  seccion: string
  area_geografica: string
  tipo_medio: 'diario' | 'revista' | 'agencia'
  frecuencia_minutos: number
  rss_url?: string
  comentarios?: string
  tiene_rss?: boolean
  force_analysis?: boolean
}

// Para compatibilidad con servicios existentes
export interface SiteAnalysisRequest {
  url: string
  name: string
  force_analysis?: boolean
  section_name?: string
  check_rss?: boolean
}

// Según SECCIÓN 15.1 - Interface KPIMetrics
export interface KPIMetrics {
  tiempoReduccion: number  // Target: 97%
  tiempoPromedioRSS: number  // Target: <5s
  tiempoPromedioPrimeraVez: number  // Target: ~20s
  tiempoPromedioCache: number  // Target: <2s
  precisionSpiders: number  // Target: >90%
  reduccionRequests: number  // Target: 70%
  cacheHitRate: number
  spidersPorDia: number  // Target: 200+
  errorRate: number
  uptimePercentage: number
}

// Tipos para los pasos del wizard
export interface WizardStep {
  id: number
  label: string
  description?: string
  completed?: boolean
}

// Tipos para las respuestas de la API
export interface ApiResponse<T> {
  data?: T
  error?: string
  status: number
}

export interface AnalyzeRequest {
  url: string
  name: string
}

// DEPRECATED: Usar SpiderGenerationRequest en su lugar
export interface GenerateRequest {
  analysis_result: AnalysisResult
  spider_name: string
  start_urls: string[]
}

export interface BatchGenerateRequest {
  sites: Array<{
    url: string
    spider_name: string
    media_name: string
    area_geografica?: string
    custom_settings?: Record<string, unknown>
  }>
  output_format: 'python' | 'json'
  base_settings?: Record<string, unknown>
  session_id: string
}

// Tipos para el historial
export interface HistoryItem {
  id: string
  timestamp: string
  url: string
  name: string
  strategy: string
  status: 'success' | 'error'
}

// Tipo para spiders generados (HistoryPage)
export interface GeneratedSpider {
  id: string
  name: string
  domain: string
  created_at: string
  status: 'active' | 'inactive' | 'error'
  strategy: string
  last_run?: string
  articles_count?: number
  code?: string // Añadido para compatibilidad con HistoryPage
  formatted_code?: string // Añadido para compatibilidad
}

// Tipos para verificación de duplicados
export interface DuplicateCheckRequest {
  domain?: string
  medio?: string
  seccion?: string
  url?: string
}

export interface DuplicateCheckResponse {
  exists: boolean
  spider_name?: string
  spider_id?: string
  domain?: string
  message?: string
}

// Tipos para generación de spiders - ACTUALIZADO para coincidir con models.py
export interface SpiderGenerationRequest {
  // URL a analizar (REQUERIDA)
  analysis_url: string
  
  // Información del medio (OBLIGATORIOS)
  medio: string
  seccion: string
  area_geografica: string
  tipo_medio: 'diario' | 'revista' | 'agencia'
  
  // Configuración adicional
  frecuencia_minutos?: number
  comentarios?: string
  excluded_urls?: string[]
  follow_pagination?: boolean
  max_pages?: number
  custom_settings?: Record<string, unknown>
}

// Re-exportar tipos de bibliotecas externas que usamos frecuentemente
export type { Theme } from '@mui/material/styles'
export type { SxProps } from '@mui/material'