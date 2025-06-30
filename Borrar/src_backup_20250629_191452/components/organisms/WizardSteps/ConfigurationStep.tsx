import { useState } from 'react'
import {
  Box,
  Typography,
  TextField,
  Button,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  FormControlLabel,
  Switch,
  Chip,
  Alert
} from '@mui/material'
import {
  ExpandMore as ExpandMoreIcon,
  Settings as SettingsIcon
} from '@mui/icons-material'
import { AnalysisResult } from '@hooks/useSpiderGeneration'

interface ConfigurationStepProps {
  analysisResult: AnalysisResult
  onNext: (customSettings: Record<string, any>) => void
  onBack: () => void
}

function ConfigurationStep({ analysisResult, onNext, onBack }: ConfigurationStepProps) {
  const [customSettings, setCustomSettings] = useState<Record<string, any>>({
    DOWNLOAD_DELAY: 1,
    CONCURRENT_REQUESTS: 16,
    AUTOTHROTTLE_ENABLED: true,
    ROBOTSTXT_OBEY: true,
    USER_AGENT: 'SpiderFactory/2.0 (+http://lamaquinadenoticias.com)',
  })

  const [advancedOpen, setAdvancedOpen] = useState(false)

  const handleSettingChange = (key: string, value: any) => {
    setCustomSettings(prev => ({
      ...prev,
      [key]: value
    }))
  }

  const handleSubmit = () => {
    onNext(customSettings)
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Configuración del Spider
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Ajusta los parámetros de extracción según tus necesidades
      </Typography>

      <Box sx={{ mt: 3 }}>
        <Alert severity="info" sx={{ mb: 3 }}>
          La estrategia <Chip label={analysisResult.suggested_strategy} size="small" /> 
          {' '}ha sido seleccionada automáticamente basada en el análisis del sitio.
        </Alert>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <TextField
            label="Retraso entre descargas (segundos)"
            type="number"
            value={customSettings.DOWNLOAD_DELAY}
            onChange={(e) => handleSettingChange('DOWNLOAD_DELAY', Number(e.target.value))}
            helperText="Tiempo de espera entre solicitudes para no sobrecargar el servidor"
            inputProps={{ min: 0.5, max: 10, step: 0.5 }}
          />

          <TextField
            label="Solicitudes concurrentes"
            type="number"
            value={customSettings.CONCURRENT_REQUESTS}
            onChange={(e) => handleSettingChange('CONCURRENT_REQUESTS', Number(e.target.value))}
            helperText="Número máximo de solicitudes simultáneas"
            inputProps={{ min: 1, max: 32 }}
          />

          <FormControlLabel
            control={
              <Switch
                checked={customSettings.AUTOTHROTTLE_ENABLED}
                onChange={(e) => handleSettingChange('AUTOTHROTTLE_ENABLED', e.target.checked)}
              />
            }
            label="Ajuste automático de velocidad"
          />

          <FormControlLabel
            control={
              <Switch
                checked={customSettings.ROBOTSTXT_OBEY}
                onChange={(e) => handleSettingChange('ROBOTSTXT_OBEY', e.target.checked)}
              />
            }
            label="Respetar robots.txt"
          />
        </Box>

        <Accordion 
          expanded={advancedOpen} 
          onChange={(_, isExpanded) => setAdvancedOpen(isExpanded)}
          sx={{ mt: 3 }}
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <SettingsIcon fontSize="small" />
              <Typography>Configuración avanzada</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField
                fullWidth
                label="User-Agent personalizado"
                value={customSettings.USER_AGENT}
                onChange={(e) => handleSettingChange('USER_AGENT', e.target.value)}
                helperText="Identificador del spider al hacer solicitudes"
              />

              {analysisResult.suggested_strategy === 'playwright' && (
                <>
                  <FormControlLabel
                    control={
                      <Switch
                        defaultChecked
                        onChange={(e) => handleSettingChange('PLAYWRIGHT_HEADLESS', e.target.checked)}
                      />
                    }
                    label="Modo headless (sin ventana del navegador)"
                  />
                  
                  <TextField
                    label="Tiempo de espera para JS (ms)"
                    type="number"
                    defaultValue={3000}
                    onChange={(e) => handleSettingChange('PLAYWRIGHT_WAIT_TIME', Number(e.target.value))}
                    helperText="Tiempo para que se cargue el contenido JavaScript"
                    inputProps={{ min: 1000, max: 10000, step: 500 }}
                  />
                </>
              )}
            </Box>
          </AccordionDetails>
        </Accordion>

        <Box sx={{ mt: 4, display: 'flex', justifyContent: 'space-between' }}>
          <Button onClick={onBack}>
            Atrás
          </Button>
          <Button variant="contained" onClick={handleSubmit}>
            Generar Spider
          </Button>
        </Box>
      </Box>
    </Box>
  )
}

export default ConfigurationStep