import React, { useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import { useMutation } from '@tanstack/react-query';
import { spiderFactoryService } from '../../../services/spiderFactory.service';
import { useNotification } from '../../../contexts/NotificationContext';
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
  FormHelperText,
  InputAdornment
} from '@mui/material'
import { WizardData } from '../../../types';
import { AREAS_GEOGRAFICAS_OFICIALES, TIPOS_MEDIO, FRECUENCIAS } from '../../../constants/areas';
import { normalizeURL, validateURL, validateMedioName } from '../../../utils/validationHelpers';
import HelpTooltip from '../../atoms/HelpTooltip';
import ExampleShowcase from '../../molecules/ExampleShowcase';
import { HELP_CONTENT, EXAMPLES, VALIDATION_MESSAGES } from '../../../constants/helpContent';

interface SiteInfoStepProps {
  data: WizardData
  onUpdate: (updates: Partial<WizardData>) => void
  onNext: () => void
}

function SiteInfoStep({ data, onUpdate, onNext }: SiteInfoStepProps) {
  const [errors, setErrors] = useState<{ url?: string; name?: string }>({})
  const { showNotification } = useNotification()

  // Mutation para verificar duplicados (API ya disponible)
  const checkDuplicateMutation = useMutation({
    mutationFn: async (url: string) => {
      if (!url) return null;
      try {
        const domain = new URL(url).hostname;
        return await spiderFactoryService.checkDuplicate({ domain });
      } catch {
        return null; // URL inválida, no verificar
      }
    },
    onSuccess: (result) => {
      if (result?.exists) {
        showNotification(
          `⚠️ Ya tienes un monitor para ${result.spider_name}. ¿Crear uno nuevo para una sección diferente?`, 
          'warning'
        );
      } else {
        showNotification('✅ Perfecto! No hay monitores duplicados para este sitio', 'success');
      }
    },
    onError: (error) => {
      console.warn('Error verificando duplicados:', error);
    }
  })

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
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        <Typography variant="h6">
          Información del sitio web
        </Typography>
        <HelpTooltip title="En este paso configuraremos la información básica del sitio de noticias que quieres monitorear" />
      </Box>
      
      <Typography variant="body2" color="text.secondary" paragraph>
        Proporciona la información básica del medio de comunicación que deseas monitorear
      </Typography>

      {/* Ejemplos de sitios populares */}
      <ExampleShowcase
        title="💡 Sitios populares de noticias:"
        examples={EXAMPLES.URLS_POPULARES}
        onSelect={(url) => {
          const normalizedUrl = normalizeURL(url);
          onUpdate({ url: normalizedUrl });
          if (normalizedUrl && validateUrl(normalizedUrl)) {
            checkDuplicateMutation.mutate(normalizedUrl);
          }
        }}
        maxVisible={3}
      />

      <Box sx={{ mt: 3 }}>
        <TextField
          fullWidth
          label="Dirección web del sitio de noticias"
          placeholder="https://elpais.com (incluye https://)"
          value={data.url}
          onChange={(e) => {
            const normalizedUrl = normalizeURL(e.target.value);
            onUpdate({ url: normalizedUrl });
            
            // Verificar duplicados después de normalizar URL
            if (normalizedUrl && validateUrl(normalizedUrl)) {
              checkDuplicateMutation.mutate(normalizedUrl);
            }
          }}
          error={!!errors.url}
          helperText={errors.url || "La dirección exacta del periódico o medio que quieres monitorear"}
          margin="normal"
          autoFocus
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <HelpTooltip title={HELP_CONTENT.URL_SITIO} />
              </InputAdornment>
            ),
          }}
        />

        {/* Ejemplos de nombres de medios */}
        <ExampleShowcase
          title="💡 Ejemplos de nombres de medios:"
          examples={EXAMPLES.NOMBRES_MEDIOS}
          onSelect={(nombre) => onUpdate({ medio: nombre })}
          maxVisible={3}
        />

        <TextField
          fullWidth
          label="¿Cómo se llama este periódico o medio?"
          placeholder="El País, La Vanguardia, ABC..."
          value={data.medio}
          onChange={(e) => onUpdate({ medio: e.target.value })}
          error={!!errors.name}
          helperText={errors.name || "Para identificar fácilmente este medio en tu lista"}
          margin="normal"
          required
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <HelpTooltip title={HELP_CONTENT.MEDIO} />
              </InputAdornment>
            ),
          }}
        />

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2, mb: 1 }}>
          <Typography variant="body2">¿De qué región o país es este medio?</Typography>
          <HelpTooltip title={HELP_CONTENT.AREA_GEOGRAFICA} />
        </Box>
        <FormControl fullWidth margin="normal" required>
          <InputLabel>Elige la región</InputLabel>
          <Select
            value={data.area_geografica}
            onChange={(e) => onUpdate({ area_geografica: e.target.value })}
            label="Elige la región"
          >
            {AREAS_GEOGRAFICAS_OFICIALES.map((area) => (
              <MenuItem key={area} value={area}>
                {area.replace(/_/g, ' ')}
              </MenuItem>
            ))}
          </Select>
          <FormHelperText>Nos ayuda a organizar mejor tus fuentes de noticias</FormHelperText>
        </FormControl>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2, mb: 1 }}>
          <Typography variant="body2">¿Qué tipo de publicación es?</Typography>
          <HelpTooltip title={HELP_CONTENT.TIPO_MEDIO} />
        </Box>
        <FormControl fullWidth margin="normal" required>
          <InputLabel>Elige el tipo</InputLabel>
          <Select
            value={data.tipo_medio}
            onChange={(e) => onUpdate({ tipo_medio: e.target.value as 'diario' | 'revista' | 'agencia' })}
            label="Elige el tipo"
          >
            {TIPOS_MEDIO.map((tipo) => (
              <MenuItem key={tipo.value} value={tipo.value}>
                {tipo.label}
              </MenuItem>
            ))}
          </Select>
          <FormHelperText>¿Publica noticias todos los días, semanalmente, o es una agencia?</FormHelperText>
        </FormControl>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2, mb: 1 }}>
          <Typography variant="body2">¿Cada cuánto tiempo quieres buscar noticias nuevas?</Typography>
          <HelpTooltip title={HELP_CONTENT.FRECUENCIA} />
        </Box>
        <FormControl fullWidth margin="normal" required>
          <InputLabel>Elige la frecuencia</InputLabel>
          <Select
            value={data.frecuencia_minutos}
            onChange={(e) => onUpdate({ frecuencia_minutos: Number(e.target.value) })}
            label="Elige la frecuencia"
          >
            {FRECUENCIAS.map((freq) => (
              <MenuItem key={freq.value} value={freq.value}>
                {freq.label}
              </MenuItem>
            ))}
          </Select>
          <FormHelperText>Más frecuente = noticias más frescas, pero usa más recursos del servidor</FormHelperText>
        </FormControl>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 3 }}>
          <FormControlLabel
            control={
              <Checkbox
                checked={data.force_analysis || false}
                onChange={(e) => onUpdate({ force_analysis: e.target.checked })}
              />
            }
            label="Analizar sitio desde cero (ignorar datos guardados)"
          />
          <HelpTooltip title={HELP_CONTENT.FORZAR_ANALISIS} />
        </Box>
        <Typography variant="caption" color="text.secondary" display="block" sx={{ ml: 4, mt: -1 }}>
          Útil si el sitio ha cambiado recientemente o si tienes problemas con un análisis previo
        </Typography>

        <Alert severity="info" sx={{ mt: 3 }}>
          <Typography variant="body2" sx={{ fontWeight: 500, mb: 1 }}>
            ¿Qué pasará en el siguiente paso?
          </Typography>
          <Typography variant="body2" color="text.secondary">
            El sistema analizará automáticamente el sitio para detectar la mejor forma de obtener las noticias:
          </Typography>
          <ul style={{ marginTop: 8, marginBottom: 0, fontSize: '0.875rem', color: 'rgba(0, 0, 0, 0.6)' }}>
            <li>📡 Feeds RSS disponibles (más eficiente)</li>
            <li>🏗️ Estructura del contenido de la página</li>
            <li>🎯 Selectores HTML para extraer noticias</li>
            <li>⚡ Si necesita JavaScript para funcionar</li>
          </ul>
        </Alert>

        <Box sx={{ mt: 4, display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            variant="contained"
            onClick={handleNext}
            size="large"
            disabled={!data.url || !data.medio || !data.area_geografica || !data.tipo_medio || !data.frecuencia_minutos}
          >
            Continuar al Siguiente Paso →
          </Button>
        </Box>
      </Box>
    </Box>
  )
}

export default SiteInfoStep