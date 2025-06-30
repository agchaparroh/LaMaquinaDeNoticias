import { 
  Box, 
  Button, 
  Typography,
  Alert,
  Divider
} from '@mui/material'
import { 
  Download as DownloadIcon,
  PlayArrow as StartIcon
} from '@mui/icons-material'
import { useBatchProcessing } from '@hooks/useBatchProcessing'
import { 
  BatchUploader, 
  BatchProcessingStatus 
} from '@components/organisms/BatchUploader'

function BulkUploadPage() {
  const {
    file,
    items,
    totalProgress,
    isProcessing,
    error,
    handleFileAccepted,
    handleClear,
    startProcessing,
    downloadResults
  } = useBatchProcessing()

  const hasResults = items.some(item => 
    item.status === 'completed' || item.status === 'error'
  )

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Carga Masiva de Sitios
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Procesa múltiples sitios de noticias desde un archivo CSV
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error.message}
        </Alert>
      )}

      <BatchUploader
        onFileAccepted={handleFileAccepted}
        onClear={handleClear}
        acceptedFile={file}
        isProcessing={isProcessing}
      />

      {file && items.length > 0 && (
        <>
          <Box sx={{ mt: 3, mb: 3, display: 'flex', gap: 2, justifyContent: 'center' }}>
            {!isProcessing && totalProgress === 0 && (
              <Button
                variant="contained"
                startIcon={<StartIcon />}
                onClick={startProcessing}
                size="large"
              >
                Iniciar Procesamiento
              </Button>
            )}
            
            {hasResults && !isProcessing && (
              <Button
                variant="outlined"
                startIcon={<DownloadIcon />}
                onClick={downloadResults}
              >
                Descargar Resultados
              </Button>
            )}
          </Box>

          <Divider sx={{ my: 4 }} />

          <BatchProcessingStatus
            items={items}
            totalProgress={totalProgress}
            isProcessing={isProcessing}
          />
        </>
      )}

      {!file && (
        <Alert severity="info" sx={{ mt: 4 }}>
          <Typography variant="subtitle2" gutterBottom>
            <strong>Cómo funciona la carga masiva:</strong>
          </Typography>
          <ol style={{ margin: '8px 0', paddingLeft: '20px' }}>
            <li>Descarga la plantilla CSV y complétala con los sitios a procesar</li>
            <li>Sube el archivo CSV usando el área de carga</li>
            <li>Revisa la lista de sitios e inicia el procesamiento</li>
            <li>El sistema analizará y generará spiders para cada sitio automáticamente</li>
            <li>Descarga los resultados y los spiders generados</li>
          </ol>
        </Alert>
      )}
    </Box>
  )
}

export default BulkUploadPage