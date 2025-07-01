import { 
  Box, 
  Paper, 
  Step, 
  StepLabel, 
  Stepper, 
  Typography,
  IconButton,
  Fab,
  Tooltip
} from '@mui/material'
import { 
  ArrowBack as ArrowBackIcon,
  KeyboardArrowUp as KeyboardArrowUpIcon 
} from '@mui/icons-material'
import { useState, useEffect, useCallback } from 'react'
import { useWizardSpiderGeneration } from '@hooks/useWizardSpiderGeneration'
import SiteInfoStep from '../components/organisms/WizardSteps/SiteInfoStep'
import SectionUrlStep from '../components/steps/SectionUrlStep'
import AnalysisStep from '../components/organisms/WizardSteps/AnalysisStep'
import ConfigurationStep from '../components/organisms/WizardSteps/ConfigurationStep'
import GenerationStep from '../components/organisms/WizardSteps/GenerationStep'
import WizardSuccess from '../components/organisms/WizardSuccess'
import useLocalStorage from '../hooks/useLocalStorage'
import { useNotification } from '../contexts/NotificationContext'
import { WizardData } from '../types'
import { wizardLogger } from '../utils/wizardLogging'

const steps = [
  'Información Básica', 
  'URL y Sección', 
  'Análisis', 
  'Configuración',
  'Generación'
]

const stepDescriptions = [
  { label: 'Información Básica', description: 'Configurar sitio y medio', estimatedTime: '2 min' },
  { label: 'URL y Sección', description: 'Especificar contenido', estimatedTime: '1 min' },
  { label: 'Análisis', description: 'Detectar estructura', estimatedTime: '30 seg' },
  { label: 'Configuración', description: 'Ajustes finales', estimatedTime: '1 min' },
  { label: 'Generación', description: 'Crear monitor', estimatedTime: '15 seg' }
]

function WizardPage() {
  const {
    currentStep,
    setCurrentStep,
    wizardData,
    updateWizardData,
    analysisResult,
    generatedCode,
    isAnalyzing,
    isGenerating,
    analyzeError,
    generateError,
    analyzeSite,
    generateSpider,
    reset
  } = useWizardSpiderGeneration({
    url: '',
    medio: '',
    seccion: '',
    area_geografica: '',
    tipo_medio: 'diario',
    frecuencia_minutos: 60,
    rss_url: '',
    comentarios: '',
    tiene_rss: false,
    force_analysis: false
  })

  // Estado local manejado por el hook especializado
  const [wizardDraft, setWizardDraft] = useLocalStorage('wizard-draft', {});
  const [userPreferences, setUserPreferences] = useLocalStorage('preferences', {
    theme: 'light',
    lastAreaGeografica: '',
    lastTipoMedio: 'diario'
  });
  const { showNotification } = useNotification();

  // Actualizar draft cuando wizardData cambia
  useEffect(() => {
    setWizardDraft(wizardData);
  }, [wizardData, setWizardDraft]);

  // Cargar borrador al montar e inicializar logging
  useEffect(() => {
    wizardLogger.wizardStarted();
    
    if (Object.keys(wizardDraft).length > 0) {
      updateWizardData(wizardDraft);
      showNotification('Borrador cargado desde sesión anterior', 'info');
    }
  }, []);

  // Función simplificada - el hook maneja la navegación
  const handleSiteInfoNext = () => {
    wizardLogger.stepCompleted(0, 'Información Básica', { url: wizardData.url, medio: wizardData.medio });
    wizardLogger.stepEntered(1, 'URL y Sección');
    setCurrentStep(1)
  }

  const handleAnalysisNext = () => {
    setCurrentStep(2)
  }

  const handleConfigurationNext = (customSettings: Record<string, any>) => {
    generateSpider(customSettings)
  }

  const handleBack = () => {
    const newStep = Math.max(0, currentStep - 1);
    wizardLogger.stepEntered(newStep, stepDescriptions[newStep]?.label || `Paso ${newStep + 1}`);
    setCurrentStep(newStep)
  }

  // Navegación por teclado simple (según plan original)
  const handleKeyNavigation = useCallback((event: KeyboardEvent) => {
    // Enter = Avanzar (si es posible)
    if (event.key === 'Enter') {
      event.preventDefault()
      // Solo avanzar si no estamos en el último paso y hay datos básicos
      if (currentStep < steps.length - 1 && wizardData.url && wizardData.medio) {
        if (currentStep === 0) {
          handleSiteInfoNext()
        }
      }
    }
    // Escape = Retroceder
    if (event.key === 'Escape' && currentStep > 0) {
      event.preventDefault()
      handleBack()
    }
  }, [currentStep, handleSiteInfoNext, handleBack, wizardData])

  useEffect(() => {
    document.addEventListener('keydown', handleKeyNavigation)
    return () => document.removeEventListener('keydown', handleKeyNavigation)
  }, [handleKeyNavigation])

  return (
    <Box role="main" aria-labelledby="wizard-title" sx={{ position: 'relative' }}>
      {/* Botón de regreso siempre visible */}
      {currentStep > 0 && (
        <Box sx={{ position: 'fixed', top: 20, left: 20, zIndex: 1000 }}>
          <Tooltip title={`Volver a: ${stepDescriptions[currentStep - 1]?.label}`} placement="right">
            <IconButton
              onClick={handleBack}
              size="large"
              sx={{ 
                bgcolor: 'primary.main', 
                color: 'white',
                '&:hover': { bgcolor: 'primary.dark' },
                boxShadow: 2
              }}
              aria-label={`Volver al paso anterior: ${stepDescriptions[currentStep - 1]?.label}`}
            >
              <ArrowBackIcon />
            </IconButton>
          </Tooltip>
        </Box>
      )}

      {/* Botón para volver arriba */}
      <Box sx={{ position: 'fixed', bottom: 20, right: 20, zIndex: 1000 }}>
        <Fab
          size="medium"
          color="secondary"
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          aria-label="Volver arriba"
        >
          <KeyboardArrowUpIcon />
        </Fab>
      </Box>

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
        <Typography variant="h4" component="h1" id="wizard-title">
          Asistente de Configuración
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ 
          bgcolor: 'primary.light', 
          px: 2, 
          py: 0.5, 
          borderRadius: 2,
          color: 'primary.contrastText'
        }}>
          ⏱️ Tiempo estimado: {stepDescriptions[currentStep]?.estimatedTime}
        </Typography>
      </Box>
      
      <Typography variant="body1" color="text.secondary" paragraph>
        Te ayudamos a crear un monitor de noticias personalizado paso a paso
      </Typography>

      {/* Indicador de progreso */}
      <Stepper activeStep={currentStep} sx={{ mb: 3 }}>
        {steps.map((step, index) => (
          <Step key={step}>
            <StepLabel>
              <Typography variant="body2">
                {stepDescriptions[index]?.label || step}
              </Typography>
            </StepLabel>
          </Step>
        ))}
      </Stepper>


      <Paper sx={{ p: 3, mt: 3 }} role="region" aria-labelledby="wizard-steps">

        <Box sx={{ mt: 4, minHeight: 400 }} role="tabpanel" aria-labelledby={`step-${currentStep}-tab`} id={`step-${currentStep}-panel`}>
          {currentStep === 0 && (
            <SiteInfoStep 
              data={wizardData} 
              onUpdate={updateWizardData}
              onNext={handleSiteInfoNext}
            />
          )}
          
          {currentStep === 1 && (
            <SectionUrlStep 
              data={wizardData} 
              onUpdate={updateWizardData}
              onNext={() => {
                // Validar datos antes de continuar al análisis
                if (wizardData.seccion && wizardData.url) {
                  analyzeSite() // Disparar análisis automáticamente
                } else {
                  showNotification('Completa todos los campos requeridos', 'warning')
                }
              }}
            />
          )}
          
          {currentStep === 2 && (
            <AnalysisStep
              isAnalyzing={isAnalyzing}
              analysisResult={analysisResult}
              error={analyzeError}
              onAnalyze={analyzeSite}
              onNext={handleAnalysisNext}
              onBack={handleBack}
            />
          )}
          
          {currentStep === 3 && analysisResult && (
            <ConfigurationStep
              analysisResult={analysisResult}
              onNext={handleConfigurationNext}
              onBack={handleBack}
            />
          )}

          {currentStep === 4 && generatedCode && (
            <GenerationStep
              generatedCode={generatedCode}
              isGenerating={isGenerating}
              error={generateError}
              onGenerate={() => {}}
              onReset={() => {}}
              onFinish={() => {
                // Mostrar página de éxito
                setCurrentStep(5)
              }}
              onBack={handleBack}
            />
          )}

          {currentStep === 5 && (
            <WizardSuccess
              spiderData={{
                name: wizardData.medio,
                url: wizardData.url,
                section: wizardData.seccion,
                frequency: `Cada ${wizardData.frecuencia_minutos} minutos`,
                strategy: analysisResult?.strategy || 'Web Scraping',
                estimatedArticles: analysisResult?.estimated_articles || 25,
                nextExecution: new Date(Date.now() + wizardData.frecuencia_minutos * 60000).toLocaleTimeString()
              }}
              onGoToDashboard={() => {
                // Navegar al dashboard
                window.location.href = '/dashboard'
              }}
              onCreateAnother={() => {
                // Reiniciar el wizard
                reset()
                setCurrentStep(0)
              }}
              onViewSettings={() => {
                // Ir a configuración del spider
                window.location.href = `/spiders/${generatedCode?.spider_id}/settings`
              }}
            />
          )}
        </Box>
      </Paper>
    </Box>
  )
}

export default WizardPage