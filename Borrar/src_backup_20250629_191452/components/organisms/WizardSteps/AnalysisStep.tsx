import { useEffect } from 'react'
import { 
  Box, 
  Typography,
  Paper,
  Chip,
  List,
  ListItem,
  ListItemText,
  Button,
  Alert
} from '@mui/material'
import {
  CheckCircle as CheckIcon,
  RssFeed as RssIcon,
  Code as CodeIcon,
  Javascript as JsIcon
} from '@mui/icons-material'
import { LoadingSpinner, StatusChip } from '@components/atoms'
import type { AnalysisResult } from '@/types'

interface AnalysisStepProps {
  isAnalyzing: boolean
  analysisResult: AnalysisResult | null
  error: Error | null
  onAnalyze: () => void
  onNext: () => void
  onBack: () => void
}

const strategyIcons = {
  rss: <RssIcon />,
  scraping: <CodeIcon />,
  playwright: <JsIcon />
}

const strategyLabels = {
  rss: 'Feed RSS',
  scraping: 'Scraping HTML',
  playwright: 'JavaScript Rendering'
}

function AnalysisStep({
  isAnalyzing,
  analysisResult,
  error,
  onAnalyze,
  onNext,
  onBack
}: AnalysisStepProps) {
  useEffect(() => {
    if (!analysisResult && !error && !isAnalyzing) {
      onAnalyze()
    }
  }, [analysisResult, error, isAnalyzing, onAnalyze])

  if (isAnalyzing) {
    return (
      <Box>
        <Typography variant="h6" gutterBottom>
          Analizando el sitio web...
        </Typography>
        <LoadingSpinner sx={{ my: 4 }} />
        <Typography variant="body2" color="text.secondary" align="center">
          Esto puede tomar unos momentos mientras examinamos la estructura del sitio
        </Typography>
      </Box>
    )
  }

  if (error) {
    return (
      <Box>
        <Typography variant="h6" gutterBottom>
          Error en el análisis
        </Typography>
        <Alert severity="error" sx={{ mt: 2 }}>
          {error.message}
        </Alert>
        <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
          <Button onClick={onBack}>Volver</Button>
          <Button variant="contained" onClick={onAnalyze}>
            Reintentar
          </Button>
        </Box>
      </Box>
    )
  }

  if (!analysisResult) {
    return null
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Análisis completado
      </Typography>
      
      <Paper elevation={0} sx={{ p: 3, mt: 2, bgcolor: 'grey.50' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <CheckIcon color="success" />
          <Typography variant="subtitle1">
            Dominio: <strong>{analysisResult.domain}</strong>
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          {analysisResult.has_rss && (
            <Chip 
              icon={<RssIcon />} 
              label="RSS Disponible" 
              color="success" 
              variant="outlined"
            />
          )}
          
          <Chip
            icon={strategyIcons[analysisResult.suggested_strategy]}
            label={`Estrategia: ${strategyLabels[analysisResult.suggested_strategy]}`}
            color="primary"
          />
          
          <Chip
            label={`Confianza: ${Math.round(analysisResult.pattern_confidence * 100)}%`}
            color={analysisResult.pattern_confidence > 0.8 ? 'success' : 'warning'}
            variant="outlined"
          />
        </Box>

        {analysisResult.rss_url && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Feed RSS detectado:
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', mt: 0.5 }}>
              {analysisResult.rss_url}
            </Typography>
          </Box>
        )}
      </Paper>

      {analysisResult.selectors && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="subtitle1" gutterBottom>
            Selectores detectados:
          </Typography>
          <List dense>
            {Object.entries(analysisResult.selectors).map(([key, value]) => (
              <ListItem key={key}>
                <ListItemText
                  primary={key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  secondary={
                    <Typography
                      variant="body2"
                      sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}
                    >
                      {value}
                    </Typography>
                  }
                />
              </ListItem>
            ))}
          </List>
        </Box>
      )}

      {analysisResult.sample_articles && analysisResult.sample_articles.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="subtitle1" gutterBottom>
            Artículos de muestra encontrados:
          </Typography>
          <List dense>
            {analysisResult.sample_articles.slice(0, 3).map((article, index) => (
              <ListItem key={index}>
                <ListItemText
                  primary={article.title}
                  secondary={article.date}
                />
              </ListItem>
            ))}
          </List>
        </Box>
      )}

      <Box sx={{ mt: 4, display: 'flex', justifyContent: 'space-between' }}>
        <Button onClick={onBack}>
          Atrás
        </Button>
        <Button variant="contained" onClick={onNext}>
          Siguiente
        </Button>
      </Box>
    </Box>
  )
}

export default AnalysisStep