import { 
  Box, 
  Paper, 
  Step, 
  StepLabel, 
  Stepper, 
  Typography 
} from '@mui/material'
import { useState, useEffect } from 'react'
import { useWizardSpiderGeneration } from '@hooks/useWizardSpiderGeneration'
import SiteInfoStep from '../components/organisms/WizardSteps/SiteInfoStep'
import SectionUrlStep from '../components/steps/SectionUrlStep'
import AnalysisStep from '../components/organisms/WizardSteps/AnalysisStep'
import ConfigurationStep from '../components/organisms/WizardSteps/ConfigurationStep'
import GenerationStep from '../components/organisms/WizardSteps/GenerationStep'
import useLocalStorage from '../hooks/useLocalStorage'
import { useNotification } from '../contexts/NotificationContext'
import { WizardData } from '../types'

const steps = ['Información Básica', 'URL y Sección', 'Análisis', 'Revisión']

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

  // Cargar borrador al montar
  useEffect(() => {
    if (Object.keys(wizardDraft).length > 0) {
      updateWizardData(wizardDraft);
      showNotification('Borrador cargado desde sesión anterior', 'info');
    }
  }, []);

  // Función simplificada - el hook maneja la navegación
  const handleSiteInfoNext = () => {
    setCurrentStep(1)
  }

  const handleAnalysisNext = () => {
    setCurrentStep(2)
  }

  const handleConfigurationNext = (customSettings: Record<string, any>) => {
    generateSpider(customSettings)
  }

  const handleBack = () => {
    setCurrentStep(Math.max(0, currentStep - 1))
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Wizard de Generación de Spider
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Sigue los pasos para generar un spider personalizado para tu sitio de noticias
      </Typography>

      <Paper sx={{ p: 3, mt: 3 }}>
        <Stepper activeStep={currentStep}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        <Box sx={{ mt: 4, minHeight: 400 }}>
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
        </Box>
      </Paper>
    </Box>
  )
}

export default WizardPage