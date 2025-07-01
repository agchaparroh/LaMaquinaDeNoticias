import { useState, useCallback } from 'react'
import { useMutation } from '@tanstack/react-query'
import { spiderFactoryService, type CustomSettings } from '@services/spiderFactory.service'
import type { AnalysisResult, SpiderCode, WizardData, SiteAnalysisRequest } from '@/types'

// Interface para el hook especializado en wizard
interface UseWizardSpiderGenerationReturn {
  // Estado del wizard
  currentStep: number
  setCurrentStep: (step: number) => void
  wizardData: WizardData
  updateWizardData: (updates: Partial<WizardData>) => void
  
  // Resultados del análisis y generación
  analysisResult: AnalysisResult | null
  generatedCode: SpiderCode | null
  
  // Estados de carga
  isAnalyzing: boolean
  isGenerating: boolean
  
  // Errores
  analyzeError: Error | null
  generateError: Error | null
  
  // Acciones
  analyzeSite: () => void
  generateSpider: (customSettings?: CustomSettings) => void
  reset: () => void
}

// Hook especializado para el wizard - maneja WizardData nativamente
export function useWizardSpiderGeneration(initialData: WizardData): UseWizardSpiderGenerationReturn {
  const [currentStep, setCurrentStep] = useState(0)
  const [wizardData, setWizardData] = useState<WizardData>(initialData)
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [generatedCode, setGeneratedCode] = useState<SpiderCode | null>(null)

  // Mutation para análisis - mapeo simplificado
  const analyzeMutation = useMutation({
    mutationFn: (data: WizardData): Promise<AnalysisResult> => {
      const request: SiteAnalysisRequest = {
        url: data.url,
        name: data.medio,
        force_analysis: data.force_analysis,
        section_name: data.seccion,
        check_rss: data.tiene_rss !== false
      }
      return spiderFactoryService.analyzeSite(request)
    },
    onSuccess: (result: AnalysisResult) => {
      setAnalysisResult(result)
      setCurrentStep(2) // Avanzar al paso de análisis
    },
    onError: (error) => {
      console.error('Error en análisis:', error)
    }
  })

  // Mutation para generación - USA TODOS LOS DATOS del wizard
  const generateMutation = useMutation({
    mutationFn: (customSettings: CustomSettings) => {
      if (!analysisResult) {
        throw new Error('No hay resultado de análisis disponible')
      }

      return spiderFactoryService.generateSpider({
        analysis_result: analysisResult,
        spider_name: wizardData.medio.toLowerCase().replace(/\s+/g, '_'),
        start_urls: [wizardData.url],
        custom_settings: customSettings || {},
        // media_name: wizardData.medio,
        // area_geografica: wizardData.area_geografica,
        // excluded_urls: [],
        // follow_pagination: true,
        // max_pages: 100
      })
    },
    onSuccess: (code: SpiderCode) => {
      setGeneratedCode(code)
      setCurrentStep(3) // Avanzar al paso final
    },
    onError: (error) => {
      console.error('Error en generación:', error)
    }
  })

  // Función para actualizar datos del wizard con useCallback para optimización
  const updateWizardData = useCallback((updates: Partial<WizardData>) => {
    setWizardData(prev => ({ ...prev, ...updates }))
  }, [])

  // Función para analizar sitio con useCallback
  const analyzeSite = useCallback(() => {
    analyzeMutation.mutate(wizardData)
  }, [wizardData, analyzeMutation])

  // Función para generar spider con useCallback
  const generateSpider = useCallback((customSettings?: CustomSettings) => {
    generateMutation.mutate(customSettings || {})
  }, [generateMutation])

  // Función de reset con useCallback
  const reset = useCallback(() => {
    setCurrentStep(0)
    setAnalysisResult(null)
    setGeneratedCode(null)
    analyzeMutation.reset()
    generateMutation.reset()
  }, [analyzeMutation, generateMutation])

  return {
    // Estado del wizard
    currentStep,
    setCurrentStep,
    wizardData,
    updateWizardData,
    
    // Resultados
    analysisResult,
    generatedCode,
    
    // Estados de carga
    isAnalyzing: analyzeMutation.isPending,
    isGenerating: generateMutation.isPending,
    
    // Errores
    analyzeError: analyzeMutation.error,
    generateError: generateMutation.error,
    
    // Acciones
    analyzeSite,
    generateSpider,
    reset
  }
}