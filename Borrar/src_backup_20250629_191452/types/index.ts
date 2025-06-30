// Tipos centralizados para el módulo Spider Factory Frontend

// Tipos de estado comunes
export type Status = 'success' | 'error' | 'warning' | 'info' | 'pending'

// Tipos para el análisis de sitios web
export interface AnalysisResult {
  domain: string
  has_rss: boolean
  rss_url?: string
  suggested_strategy: 'rss' | 'scraping' | 'playwright'
  pattern_confidence: number
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
  }>
  requires_javascript?: boolean
  detected_patterns?: Array<{
    pattern: string
    confidence: number
  }>
}

// Tipos para la generación de spiders
export interface SpiderCode {
  filename: string
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
export interface SiteInfo {
  url: string
  name: string
  language?: string
  category?: string
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

// Re-exportar tipos de bibliotecas externas que usamos frecuentemente
export type { Theme } from '@mui/material/styles'
export type { SxProps } from '@mui/material'