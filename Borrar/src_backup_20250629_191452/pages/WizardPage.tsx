import { 
  Box, 
  Paper, 
  Step, 
  StepLabel, 
  Stepper, 
  Typography 
} from '@mui/material'
import { useSpiderGeneration } from '@hooks/useSpiderGeneration'
import {
  SiteInfoStep,
  AnalysisStep,
  ConfigurationStep,
  GenerationStep
} from '@components/organisms/WizardSteps'

const steps = [
  'Información del sitio',
  'Análisis automático',
  'Configuración de extracción',
  'Generación del spider'
]

function WizardPage() {
  const {
    currentStep,
    setCurrentStep,
    siteInfo,
    setSiteInfo,
    analysisResult,
    generatedCode,
    isAnalyzing,
    isGenerating,
    analyzeError,
    generateError,
    analyzeSite,
    generateSpider,
    reset
  } = useSpiderGeneration()

  const handleSiteInfoNext = (info: typeof siteInfo) => {
    setSiteInfo(info)
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
              onNext={handleSiteInfoNext}
              initialData={siteInfo}
            />
          )}
          
          {currentStep === 1 && (
            <AnalysisStep
              isAnalyzing={isAnalyzing}
              analysisResult={analysisResult}
              error={analyzeError}
              onAnalyze={analyzeSite}
              onNext={handleAnalysisNext}
              onBack={handleBack}
            />
          )}
          
          {currentStep === 2 && analysisResult && (
            <ConfigurationStep
              analysisResult={analysisResult}
              onNext={handleConfigurationNext}
              onBack={handleBack}
            />
          )}
          
          {currentStep === 3 && (
            <GenerationStep
              isGenerating={isGenerating}
              generatedCode={generatedCode}
              error={generateError}
              onGenerate={() => generateSpider({})}
              onReset={reset}
            />
          )}
        </Box>
      </Paper>
    </Box>
  )
}

export default WizardPage