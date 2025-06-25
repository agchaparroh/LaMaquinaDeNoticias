import { apiClient, downloadFile } from './api'
import {
  SiteAnalysisRequest,
  AnalysisResult,
  SpiderGenerationRequest,
  SpiderCode,
} from '@hooks/useSpiderGeneration'

export interface DuplicateCheckRequest {
  domain: string
  name?: string
}

export interface DuplicateCheckResponse {
  exists: boolean
  spider_name?: string
  file_path?: string
  similar_spiders: string[]
  message: string
}

export interface HealthCheckResponse {
  status: string
  version: string
  redis_connected: boolean
  firecrawl_available: boolean
  patterns_count: number
  uptime_seconds: number
  timestamp: string
}

export interface PatternSearchParams {
  domain?: string
  status?: string
  min_confidence?: number
  strategy?: string
  limit?: number
}

export interface Pattern {
  id: string
  domain: string
  section: string
  strategy: string
  confidence: number
  selectors?: Record<string, string>
  usage_count: number
  last_used?: string
  created_at: string
  updated_at: string
}

export interface PatternSearchResponse {
  total: number
  patterns: Pattern[]
}

export interface BatchSite {
  url: string
  name: string
  language?: string
  category?: string
}

export interface BatchAnalysisRequest {
  sites: BatchSite[]
  force_analysis?: boolean
  check_rss?: boolean
}

export interface BatchGenerateRequest {
  sites: Array<{
    url: string
    spider_name: string
    media_name: string
    area_geografica?: string
    excluded_urls?: string[]
    follow_pagination?: boolean
    max_pages?: number
    custom_settings?: Record<string, any>
  }>
  output_format?: string
  base_settings?: Record<string, any>
  session_id?: string
}

export interface TaskStatus {
  task_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  current_step?: string
  result?: any
  error?: string
  created_at: string
  updated_at: string
}

class SpiderFactoryService {
  // Health check
  async checkHealth(): Promise<HealthCheckResponse> {
    return apiClient.get<HealthCheckResponse>('/health')
  }

  // Duplicate check
  async checkDuplicate(request: DuplicateCheckRequest): Promise<DuplicateCheckResponse> {
    return apiClient.post<DuplicateCheckResponse>('/check-duplicate', request)
  }

  // Analysis
  async analyzeSite(request: SiteAnalysisRequest): Promise<AnalysisResult> {
    const payload = {
      url: request.url,
      section_name: request.section_name || null,
      force_analysis: request.force_analysis || false,
      check_rss: request.check_rss !== false,
    }
    
    return apiClient.post<AnalysisResult>('/analyze', payload)
  }

  // Generation
  async generateSpider(request: SpiderGenerationRequest): Promise<SpiderCode> {
    const payload = {
      analysis_url: request.analysis_result ? undefined : request.analysis_result,
      pattern_id: request.pattern_id,
      spider_name: request.spider_name,
      media_name: request.media_name || request.spider_name,
      excluded_urls: request.excluded_urls || [],
      follow_pagination: request.follow_pagination !== false,
      max_pages: request.max_pages || 100,
      area_geografica: request.area_geografica,
      custom_settings: request.custom_settings || {},
    }
    
    const response = await apiClient.post<{
      success: boolean
      spider_name: string
      file_path: string
      strategy: string
      code_preview: string
      message: string
      warnings?: string[]
    }>('/generate', payload)
    
    return {
      filename: `${response.spider_name}.py`,
      code: response.code_preview,
      formatted_code: response.code_preview,
    }
  }

  // Pattern search
  async searchPatterns(params: PatternSearchParams = {}): Promise<PatternSearchResponse> {
    return apiClient.get<PatternSearchResponse>('/patterns/search', params)
  }

  // Get top patterns
  async getTopPatterns(limit: number = 10): Promise<Array<{ pattern_id: string; usage_count: number }>> {
    const response = await apiClient.get<{ patterns: Array<{ pattern_id: string; usage_count: number }> }>(
      '/patterns/top',
      { limit }
    )
    return response.patterns
  }

  // Batch analysis
  async batchAnalyze(csvContent: string, options: { force_analysis?: boolean; check_rss?: boolean } = {}): Promise<string> {
    const response = await apiClient.post<{ task_id: string }>('/batch/analyze', {
      csv_content: csvContent,
      force_analysis: options.force_analysis || false,
      check_rss: options.check_rss !== false,
    })
    
    return response.task_id
  }

  // Batch generation
  async batchGenerate(request: BatchGenerateRequest): Promise<string> {
    const response = await apiClient.post<{ task_id: string }>('/batch/generate', request)
    return response.task_id
  }

  // Get task status
  async getTaskStatus(taskId: string): Promise<TaskStatus> {
    return apiClient.get<TaskStatus>(`/task/${taskId}`)
  }

  // Download spider
  async downloadSpider(spiderName: string): Promise<void> {
    await downloadFile(`/download/${spiderName}`, `${spiderName}.py`)
  }

  // Generate from pattern
  async generateFromPattern(
    patternId: string,
    spiderName: string,
    mediaName: string,
    options: {
      excluded_urls?: string[]
      follow_pagination?: boolean
      max_pages?: number
      area_geografica?: string
      custom_settings?: Record<string, any>
    } = {}
  ): Promise<SpiderCode> {
    const payload = {
      pattern_id: patternId,
      spider_name: spiderName,
      media_name: mediaName,
      ...options,
    }
    
    const response = await apiClient.post<{
      success: boolean
      spider_name: string
      file_path: string
      strategy: string
      code_preview: string
      message: string
    }>('/generate', payload)
    
    return {
      filename: `${response.spider_name}.py`,
      code: response.code_preview,
      formatted_code: response.code_preview,
    }
  }
}

// Exportar instancia única del servicio
export const spiderFactoryService = new SpiderFactoryService()

// Exportar también la clase por si se necesita crear instancias adicionales
export default SpiderFactoryService