import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import {
  Box,
  Paper,
  Typography,
  Button,
  Alert,
  IconButton,
  Tooltip,
  Link
} from '@mui/material'
import {
  CloudUpload as UploadIcon,
  Download as DownloadIcon,
  Clear as ClearIcon,
  CheckCircle as CheckIcon
} from '@mui/icons-material'

interface BatchUploaderProps {
  onFileAccepted: (file: File) => void
  onClear: () => void
  acceptedFile?: File | null
  isProcessing?: boolean
}

const TEMPLATE_CSV = `url,name,language,category
https://ejemplo1.com,Ejemplo Noticias,es,general
https://ejemplo2.com/noticias,Blog Tech,es,tecnologia
https://ejemplo3.com,Medio Local,es,local`

function BatchUploader({ 
  onFileAccepted, 
  onClear, 
  acceptedFile,
  isProcessing = false 
}: BatchUploaderProps) {
  const [error, setError] = useState<string | null>(null)

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    setError(null)
    
    if (rejectedFiles.length > 0) {
      setError('Solo se aceptan archivos CSV')
      return
    }
    
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0]
      
      if (file.size > 5 * 1024 * 1024) {
        setError('El archivo no debe superar los 5MB')
        return
      }
      
      onFileAccepted(file)
    }
  }, [onFileAccepted])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.csv']
    },
    maxFiles: 1,
    disabled: isProcessing || !!acceptedFile
  })

  const handleDownloadTemplate = () => {
    const blob = new Blob([TEMPLATE_CSV], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'plantilla_spider_factory.csv'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  if (acceptedFile) {
    return (
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <CheckIcon color="success" />
            <Box>
              <Typography variant="subtitle1">
                Archivo cargado
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {acceptedFile.name} ({(acceptedFile.size / 1024).toFixed(1)} KB)
              </Typography>
            </Box>
          </Box>
          {!isProcessing && (
            <Tooltip title="Limpiar">
              <IconButton onClick={onClear}>
                <ClearIcon />
              </IconButton>
            </Tooltip>
          )}
        </Box>
      </Paper>
    )
  }

  return (
    <Box>
      <Paper
        {...getRootProps()}
        sx={{
          p: 4,
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'divider',
          backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
          cursor: 'pointer',
          transition: 'all 0.2s ease',
          '&:hover': {
            borderColor: 'primary.main',
            backgroundColor: 'action.hover'
          }
        }}
      >
        <input {...getInputProps()} />
        <Box sx={{ textAlign: 'center' }}>
          <UploadIcon 
            sx={{ 
              fontSize: 64, 
              color: isDragActive ? 'primary.main' : 'text.secondary',
              mb: 2 
            }} 
          />
          <Typography variant="h6" gutterBottom>
            {isDragActive ? 
              'Suelta el archivo aquí' : 
              'Arrastra tu archivo CSV aquí'
            }
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            o haz clic para seleccionar un archivo
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Máximo 5MB • Solo archivos .csv
          </Typography>
        </Box>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Box sx={{ mt: 2, textAlign: 'center' }}>
        <Button
          variant="text"
          startIcon={<DownloadIcon />}
          onClick={handleDownloadTemplate}
          size="small"
        >
          Descargar plantilla CSV
        </Button>
      </Box>

      <Alert severity="info" sx={{ mt: 2 }}>
        <Typography variant="body2" gutterBottom>
          <strong>Formato del archivo CSV:</strong>
        </Typography>
        <Typography variant="caption" component="div" sx={{ fontFamily: 'monospace' }}>
          url,name,language,category
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          Los campos language y category son opcionales
        </Typography>
      </Alert>
    </Box>
  )
}

export default BatchUploader