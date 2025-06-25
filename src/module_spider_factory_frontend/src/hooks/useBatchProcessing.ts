import { useState, useCallback, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import Papa from 'papaparse'
import { BatchItem } from '@components/organisms/BatchUploader'
import { useBatchProgress, BatchProgressMessage } from './useWebSocket'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface CSVRow {
  url: string
  name: string
  language?: string
  category?: string
}

interface BatchProcessRequest {
  sites: Array<{
    url: string
    name: string
    language?: string
    category?: string
  }>
}

interface UseBatchProcessingReturn {
  file: File | null
  items: BatchItem[]
  totalProgress: number
  isProcessing: boolean
  error: Error | null
  handleFileAccepted: (file: File) => void
  handleClear: () => void
  startProcessing: () => void
  downloadResults: () => void
}

export function useBatchProcessing(): UseBatchProcessingReturn {
  const [file, setFile] = useState<File | null>(null)
  const [items, setItems] = useState<BatchItem[]>([])
  const [totalProgress, setTotalProgress] = useState(0)
  const [csvData, setCsvData] = useState<CSVRow[]>([])
  const [batchId, setBatchId] = useState<string | null>(null)

  // Hook para WebSocket
  const handleBatchProgress = useCallback((message: BatchProgressMessage) => {
    setTotalProgress(message.progress.percentage)
    
    // Actualizar el item específico
    setItems(prev => prev.map(item => {
      if (item.url === message.item.url) {
        return {
          ...item,
          status: message.item.status as BatchItem['status'],
          progress: message.progress.percentage,
          result: message.item.result
        }
      }
      return item
    }))
  }, [])

  const { isConnected } = useBatchProgress(
    batchId || '',
    handleBatchProgress
  )

  const parseCSV = useCallback((file: File) => {
    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => {
        const validRows = results.data.filter((row: any) => 
          row.url && row.name
        ) as CSVRow[]
        
        setCsvData(validRows)
        
        const batchItems: BatchItem[] = validRows.map((row, index) => ({
          id: `item-${index}`,
          url: row.url,
          name: row.name,
          status: 'pending' as const,
          progress: 0
        }))
        
        setItems(batchItems)
      },
      error: (error) => {
        console.error('CSV parsing error:', error)
      }
    })
  }, [])

  const handleFileAccepted = useCallback((acceptedFile: File) => {
    setFile(acceptedFile)
    parseCSV(acceptedFile)
  }, [parseCSV])

  const handleClear = useCallback(() => {
    setFile(null)
    setItems([])
    setCsvData([])
    setTotalProgress(0)
  }, [])

  const processBatchMutation = useMutation({
    mutationFn: async (request: BatchProcessRequest) => {
      const response = await fetch(`${API_BASE_URL}/api/batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Error al procesar el lote')
      }
      
      return response.json()
    }
  })

  const startProcessing = useCallback(async () => {
    if (csvData.length === 0) return

    // Generar ID único para el batch
    const newBatchId = `batch-${Date.now()}`
    setBatchId(newBatchId)

    const totalItems = csvData.length
    let processedItems = 0

    // Si tenemos WebSocket, las actualizaciones vendrán por ahí
    if (!isConnected) {
      // Fallback sin WebSocket
      for (let i = 0; i < csvData.length; i++) {
      const row = csvData[i]
      const itemId = `item-${i}`

      setItems(prev => prev.map(item => 
        item.id === itemId 
          ? { ...item, status: 'processing' as const, progress: 0 }
          : item
      ))

      try {
        const analysisResponse = await fetch(`${API_BASE_URL}/api/analyze`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: row.url, name: row.name })
        })

        if (!analysisResponse.ok) {
          throw new Error('Error en el análisis')
        }

        const analysisResult = await analysisResponse.json()

        setItems(prev => prev.map(item => 
          item.id === itemId 
            ? { ...item, progress: 50 }
            : item
        ))

        const generateResponse = await fetch(`${API_BASE_URL}/api/generate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            analysis_result: analysisResult,
            spider_name: row.name.toLowerCase().replace(/\s+/g, '_'),
            start_urls: [row.url]
          })
        })

        if (!generateResponse.ok) {
          throw new Error('Error en la generación')
        }

        const spiderCode = await generateResponse.json()

        setItems(prev => prev.map(item => 
          item.id === itemId 
            ? { 
                ...item, 
                status: 'completed' as const, 
                progress: 100,
                result: {
                  spider_count: 1,
                  strategy: analysisResult.suggested_strategy
                }
              }
            : item
        ))
      } catch (error) {
        setItems(prev => prev.map(item => 
          item.id === itemId 
            ? { 
                ...item, 
                status: 'error' as const,
                result: {
                  spider_count: 0,
                  error: error instanceof Error ? error.message : 'Error desconocido'
                }
              }
            : item
        ))
      }

        processedItems++
        setTotalProgress((processedItems / totalItems) * 100)
      }
    } else {
      // Con WebSocket, enviar request batch a la API
      try {
        const response = await fetch(`${API_BASE_URL}/api/batch/generate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            sites: csvData.map((row, index) => ({
              url: row.url,
              spider_name: row.name.toLowerCase().replace(/\s+/g, '_'),
              media_name: row.name,
              area_geografica: row.category,
              custom_settings: {}
            })),
            output_format: 'python',
            base_settings: {},
            session_id: newBatchId
          })
        })

        if (!response.ok) {
          throw new Error('Error iniciando procesamiento batch')
        }

        // Las actualizaciones vendrán por WebSocket
      } catch (error) {
        console.error('Error en procesamiento batch:', error)
        // Manejar error
      }
    }
  }, [csvData, isConnected])

  const downloadResults = useCallback(() => {
    const results = items.map(item => ({
      url: item.url,
      name: item.name,
      status: item.status,
      strategy: item.result?.strategy || '',
      error: item.result?.error || ''
    }))

    const csv = Papa.unparse(results)
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `resultados_spider_factory_${new Date().toISOString().split('T')[0]}.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }, [items])

  return {
    file,
    items,
    totalProgress,
    isProcessing: processBatchMutation.isPending || items.some(i => i.status === 'processing'),
    error: processBatchMutation.error,
    handleFileAccepted,
    handleClear,
    startProcessing,
    downloadResults
  }
}