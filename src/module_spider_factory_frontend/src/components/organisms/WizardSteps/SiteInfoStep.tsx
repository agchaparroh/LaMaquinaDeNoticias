import { useState } from 'react'
import { 
  Box, 
  TextField, 
  Button, 
  Typography,
  FormControlLabel,
  Checkbox,
  Alert
} from '@mui/material'
import { SiteAnalysisRequest } from '@hooks/useSpiderGeneration'

interface SiteInfoStepProps {
  onNext: (siteInfo: SiteAnalysisRequest) => void
  initialData?: SiteAnalysisRequest | null
}

function SiteInfoStep({ onNext, initialData }: SiteInfoStepProps) {
  const [url, setUrl] = useState(initialData?.url || '')
  const [name, setName] = useState(initialData?.name || '')
  const [forceAnalysis, setForceAnalysis] = useState(false)
  const [errors, setErrors] = useState<{ url?: string; name?: string }>({})

  const validateUrl = (value: string): boolean => {
    try {
      new URL(value)
      return true
    } catch {
      return false
    }
  }

  const validateForm = (): boolean => {
    const newErrors: { url?: string; name?: string } = {}
    
    if (!url) {
      newErrors.url = 'La URL es requerida'
    } else if (!validateUrl(url)) {
      newErrors.url = 'Ingresa una URL válida'
    }
    
    if (!name.trim()) {
      newErrors.name = 'El nombre del medio es requerido'
    } else if (name.length < 3) {
      newErrors.name = 'El nombre debe tener al menos 3 caracteres'
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = () => {
    if (validateForm()) {
      onNext({
        url,
        name: name.trim(),
        force_analysis: forceAnalysis
      })
    }
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Información del sitio web
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Ingresa la URL del sitio de noticias y un nombre identificativo
      </Typography>

      <Box sx={{ mt: 3 }}>
        <TextField
          fullWidth
          label="URL del sitio"
          placeholder="https://ejemplo.com"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          error={!!errors.url}
          helperText={errors.url}
          margin="normal"
          autoFocus
        />

        <TextField
          fullWidth
          label="Nombre del medio"
          placeholder="Ejemplo Noticias"
          value={name}
          onChange={(e) => setName(e.target.value)}
          error={!!errors.name}
          helperText={errors.name}
          margin="normal"
        />

        <FormControlLabel
          control={
            <Checkbox
              checked={forceAnalysis}
              onChange={(e) => setForceAnalysis(e.target.checked)}
            />
          }
          label="Forzar análisis nuevo (ignorar caché)"
          sx={{ mt: 2 }}
        />

        <Alert severity="info" sx={{ mt: 2 }}>
          El sistema analizará automáticamente el sitio para detectar:
          <ul style={{ marginTop: 8, marginBottom: 0 }}>
            <li>Feeds RSS disponibles</li>
            <li>Estructura del contenido</li>
            <li>Selectores HTML óptimos</li>
            <li>Necesidad de renderizado JavaScript</li>
          </ul>
        </Alert>

        <Box sx={{ mt: 4, display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            variant="contained"
            onClick={handleSubmit}
            size="large"
          >
            Siguiente
          </Button>
        </Box>
      </Box>
    </Box>
  )
}

export default SiteInfoStep