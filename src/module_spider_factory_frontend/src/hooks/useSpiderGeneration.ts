import { useMutation, useQuery } from '@tanstack/react-query'
import { useState, useCallback } from 'react'
import { spiderFactoryService } from '@services/spiderFactory.service'

export interface SiteAnalysisRequest {
  url: string
  name: string
  force_analysis?: boolean
}

export interface AnalysisResult {
  domain: string
  has_rss: boolean
  rss_url?: string
  pattern_confidence: number
  suggested_strategy: 'rss' | 'scraping' | 'playwright'
  selectors?: {
    article_link: string
    title: string
    content: string
    date?: string
    author?: string
    category?: string
  }
  sample_articles?: Array<{
    title: string
    url: string
    date?: string
  }>
}

export interface SpiderGenerationRequest {
  analysis_result: AnalysisResult
  spider_name: string
  start_urls: string[]
  custom_settings?: Record<string, any>
}

export interface SpiderCode {
  filename: string
  code: string
  formatted_code: string
}

interface UseSpiderGenerationReturn {
  currentStep: number
  setCurrentStep: (step: number) => void
  siteInfo: SiteAnalysisRequest | null
  setSiteInfo: (info: SiteAnalysisRequest) => void
  analysisResult: AnalysisResult | null
  generatedCode: SpiderCode | null
  isAnalyzing: boolean
  isGenerating: boolean
  analyzeError: Error | null
  generateError: Error | null
  analyzeSite: () => void
  generateSpider: (customSettings?: Record<string, any>) => void
  reset: () => void
}

export function useSpiderGeneration(): UseSpiderGenerationReturn {
  const [currentStep, setCurrentStep] = useState(0)
  const [siteInfo, setSiteInfo] = useState<SiteAnalysisRequest | null>(null)
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [generatedCode, setGeneratedCode] = useState<SpiderCode | null>(null)

  const analyzeMutation = useMutation({
    mutationFn: (request: SiteAnalysisRequest) => spiderFactoryService.analyzeSite(request),
    onSuccess: (data: AnalysisResult) => {
      setAnalysisResult(data)
      setCurrentStep(2)
    },
  })

  const generateMutation = useMutation({
    mutationFn: (request: SpiderGenerationRequest) => spiderFactoryService.generateSpider(request),
    onSuccess: (data: SpiderCode) => {
      setGeneratedCode(data)
      setCurrentStep(3)
    },
  })

  const analyzeSite = useCallback(() => {
    if (siteInfo) {
      analyzeMutation.mutate(siteInfo)
    }
  }, [siteInfo, analyzeMutation])

  const generateSpider = useCallback((customSettings?: Record<string, any>) => {
    if (analysisResult && siteInfo) {
      const request: SpiderGenerationRequest = {
        analysis_result: analysisResult,
        spider_name: siteInfo.name.toLowerCase().replace(/\s+/g, '_'),
        start_urls: [siteInfo.url],
        custom_settings: customSettings,
      }
      generateMutation.mutate(request)
    }
  }, [analysisResult, siteInfo, generateMutation])

  const reset = useCallback(() => {
    setCurrentStep(0)
    setSiteInfo(null)
    setAnalysisResult(null)
    setGeneratedCode(null)
    analyzeMutation.reset()
    generateMutation.reset()
  }, [analyzeMutation, generateMutation])

  return {
    currentStep,
    setCurrentStep,
    siteInfo,
    setSiteInfo,
    analysisResult,
    generatedCode,
    isAnalyzing: analyzeMutation.isPending,
    isGenerating: generateMutation.isPending,
    analyzeError: analyzeMutation.error,
    generateError: generateMutation.error,
    analyzeSite,
    generateSpider,
    reset,
  }
}

export function usePatternSearch(domain: string) {
  return useQuery({
    queryKey: ['pattern', domain],
    queryFn: async () => {
      try {
        const response = await spiderFactoryService.searchPatterns({ domain })
        return response.patterns.length > 0 ? response.patterns[0] : null
      } catch (error) {
        if (error.status === 404) {
          return null
        }
        throw error
      }
    },
    enabled: !!domain,
  })
}