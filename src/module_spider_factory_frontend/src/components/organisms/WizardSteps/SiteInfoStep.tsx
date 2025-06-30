import React, { useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import { 
  Box, 
  TextField, 
  Button, 
  Typography,
  FormControlLabel,
  Checkbox,
  Alert,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Tooltip,
  FormHelperText
} from '@mui/material'
import { WizardData } from '../../../types';
import { AREAS_GEOGRAFICAS_OFICIALES, TIPOS_MEDIO, FRECUENCIAS } from '../../../constants/areas';

interface SiteInfoStepProps {
  data: WizardData
  onUpdate: (updates: Partial<WizardData>) => void
  onNext: () => void
}

function SiteInfoStep({ data, onUpdate, onNext }: SiteInfoStepProps) {
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
    
    if (!data.url) {
      newErrors.url = 'La URL es requerida'
    } else if (!validateUrl(data.url)) {
      newErrors.url = 'Ingresa una URL válida'
    }
    
    if (!data.medio.trim()) {
      newErrors.name = 'El nombre del medio es requerido'
    } else if (data.medio.length < 3) {
      newErrors.name = 'El nombre debe tener al menos 3 caracteres'
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleNext = () => {
    if (validateForm()) {
      onNext()
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
          value={data.url}
          onChange={(e) => onUpdate({ url: e.target.value })}
          error={!!errors.url}
          helperText={errors.url}
          margin="normal"
          autoFocus
        />

        {/* Según SECCIÓN 1.1 - Campos faltantes en Step 1 - Información básica EXACTOS */}
        {/* medio (actualmente usa "name") - RENOMBRAR */}
        <TextField
          fullWidth
          label="Medio"
          placeholder="Ejemplo Noticias"
          value={data.medio}
          onChange={(e) => onUpdate({ medio: e.target.value })}
          error={!!errors.name}
          helperText={errors.name || "Nombre del medio de comunicación"}
          margin="normal"
          required
        />

        {/* area_geografica - Dropdown con opciones: ESPAÑA, ARGENTINA, MÉXICO, etc. */}
        <FormControl fullWidth margin="normal" required>
          <InputLabel>Área Geográfica</InputLabel>
          <Select
            value={data.area_geografica}
            onChange={(e) => onUpdate({ area_geografica: e.target.value })}
            label="Área Geográfica"
          >
            {AREAS_GEOGRAFICAS_OFICIALES.map((area) => (
              <MenuItem key={area} value={area}>
                {area.replace(/_/g, ' ')}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* tipo_medio - Dropdown: "diario", "revista", "agencia" */}
        <FormControl fullWidth margin="normal" required>
          <InputLabel>Tipo de Medio</InputLabel>
          <Select
            value={data.tipo_medio}
            onChange={(e) => onUpdate({ tipo_medio: e.target.value as 'diario' | 'revista' | 'agencia' })}
            label="Tipo de Medio"
          >
            {TIPOS_MEDIO.map((tipo) => (
              <MenuItem key={tipo.value} value={tipo.value}>
                {tipo.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* frecuencia_minutos - Dropdown con opciones: 15, 30, 60, 120, 1440 */}
        <FormControl fullWidth margin="normal" required>
          <InputLabel>Frecuencia de Ejecución</InputLabel>
          <Select
            value={data.frecuencia_minutos}
            onChange={(e) => onUpdate({ frecuencia_minutos: Number(e.target.value) })}
            label="Frecuencia de Ejecución"
          >
            {FRECUENCIAS.map((freq) => (
              <MenuItem key={freq.value} value={freq.value}>
                {freq.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControlLabel
          control={
            <Checkbox
              checked={data.force_analysis || false}
              onChange={(e) => onUpdate({ force_analysis: e.target.checked })}
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
            onClick={handleNext}
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