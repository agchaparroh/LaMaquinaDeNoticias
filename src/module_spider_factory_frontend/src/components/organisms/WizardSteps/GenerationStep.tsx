import { useEffect, useState } from 'react'
import {
  Box,
  Typography,
  Button,
  Alert,
  Paper,
  IconButton,
  Tooltip
} from '@mui/material'
import {
  Download as DownloadIcon,
  ContentCopy as CopyIcon,
  Check as CheckIcon
} from '@mui/icons-material'
import { LoadingSpinner, CodeBlock } from '@components/atoms'
import type { SpiderCode } from '@/types'

interface GenerationStepProps {
  isGenerating: boolean
  generatedCode: SpiderCode | null
  error: Error | null
  onGenerate: () => void
  onReset: () => void
}

function GenerationStep({
  isGenerating,
  generatedCode,
  error,
  onGenerate,
  onReset
}: GenerationStepProps) {
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (!generatedCode && !error && !isGenerating) {
      onGenerate()
    }
  }, [generatedCode, error, isGenerating, onGenerate])

  const handleCopyCode = async () => {
    if (generatedCode) {
      await navigator.clipboard.writeText(generatedCode.formatted_code)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleDownload = () => {
    if (generatedCode) {
      const blob = new Blob([generatedCode.formatted_code], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = generatedCode.filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    }
  }

  if (isGenerating) {
    return (
      <Box>
        <Typography variant="h6" gutterBottom>
          Generando el spider...
        </Typography>
        <LoadingSpinner sx={{ my: 4 }} />
        <Typography variant="body2" color="text.secondary" align="center">
          Creando el código optimizado para tu sitio
        </Typography>
      </Box>
    )
  }

  if (error) {
    return (
      <Box>
        <Typography variant="h6" gutterBottom>
          Error al generar el spider
        </Typography>
        <Alert severity="error" sx={{ mt: 2 }}>
          {error.message}
        </Alert>
        <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
          <Button onClick={onReset}>Volver al inicio</Button>
          <Button variant="contained" onClick={onGenerate}>
            Reintentar
          </Button>
        </Box>
      </Box>
    )
  }

  if (!generatedCode) {
    return null
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Spider generado exitosamente
      </Typography>
      
      <Alert severity="success" sx={{ mt: 2, mb: 3 }}>
        Tu spider ha sido generado y está listo para usar. 
        Puedes descargarlo o copiarlo al portapapeles.
      </Alert>

      <Paper elevation={0} sx={{ p: 2, bgcolor: 'grey.50', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography variant="subtitle1">
            <strong>Archivo:</strong> {generatedCode.filename}
          </Typography>
          <Box>
            <Tooltip title={copied ? 'Copiado!' : 'Copiar código'}>
              <IconButton onClick={handleCopyCode}>
                {copied ? <CheckIcon /> : <CopyIcon />}
              </IconButton>
            </Tooltip>
            <Tooltip title="Descargar archivo">
              <IconButton onClick={handleDownload}>
                <DownloadIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </Paper>

      <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
        <CodeBlock 
          code={generatedCode.formatted_code} 
          language="python"
        />
      </Box>

      <Alert severity="info" sx={{ mt: 3 }}>
        <Typography variant="subtitle2" gutterBottom>
          <strong>Próximos pasos:</strong>
        </Typography>
        <ol style={{ margin: '8px 0', paddingLeft: '20px' }}>
          <li>Guarda el archivo en tu proyecto de Scrapy</li>
          <li>Ejecuta: <code>scrapy crawl {generatedCode.filename.replace('.py', '')}</code></li>
          <li>Monitorea los resultados y ajusta si es necesario</li>
        </ol>
      </Alert>

      <Box sx={{ mt: 4, display: 'flex', gap: 2, justifyContent: 'center' }}>
        <Button
          variant="contained"
          startIcon={<DownloadIcon />}
          onClick={handleDownload}
        >
          Descargar Spider
        </Button>
        <Button
          variant="outlined"
          onClick={onReset}
        >
          Generar Nuevo Spider
        </Button>
      </Box>
    </Box>
  )
}

export default GenerationStep