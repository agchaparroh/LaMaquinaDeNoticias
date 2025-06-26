import { useEffect, useRef, useState, useCallback } from 'react'
import type { WebSocketMessage, BatchProgressMessage } from '@/types'

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

export interface AnalysisProgressMessage extends WebSocketMessage {
  type: 'analysis_progress'
  site_url: string
  stage: string
  progress: number
  details?: Record<string, any>
}

export interface GenerationCompleteMessage extends WebSocketMessage {
  type: 'generation_complete'
  spider_name: string
  file_path: string
  download_url?: string
}

export interface ErrorMessage extends WebSocketMessage {
  type: 'error'
  error_type: string
  error_message: string
  context?: Record<string, any>
}

export interface TaskProgressMessage extends WebSocketMessage {
  type: 'task_progress'
  task_id: string
  status: string
  progress: number
  current_step?: string
}

export type MessageHandler = (message: WebSocketMessage) => void

interface UseWebSocketOptions {
  session_id?: string
  onOpen?: () => void
  onClose?: () => void
  onError?: (error: Event) => void
  onMessage?: MessageHandler
  reconnect?: boolean
  reconnectInterval?: number
  reconnectAttempts?: number
}

interface UseWebSocketReturn {
  isConnected: boolean
  connectionState: 'connecting' | 'connected' | 'disconnected' | 'error'
  send: (data: any) => void
  reconnect: () => void
  disconnect: () => void
  lastMessage: WebSocketMessage | null
  error: Error | null
}

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    session_id,
    onOpen,
    onClose,
    onError,
    onMessage,
    reconnect = true,
    reconnectInterval = 5000,
    reconnectAttempts = 5
  } = options

  const ws = useRef<WebSocket | null>(null)
  const reconnectCount = useRef(0)
  const reconnectTimeoutId = useRef<NodeJS.Timeout | null>(null)
  
  const [isConnected, setIsConnected] = useState(false)
  const [connectionState, setConnectionState] = useState<UseWebSocketReturn['connectionState']>('disconnected')
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const [error, setError] = useState<Error | null>(null)

  const connect = useCallback(() => {
    try {
      setConnectionState('connecting')
      setError(null)
      
      const sessionPath = session_id || 'default'
      const wsUrl = `${WS_BASE_URL}/ws/${sessionPath}`
      
      ws.current = new WebSocket(wsUrl)
      
      ws.current.onopen = () => {
        console.log('WebSocket connected')
        setIsConnected(true)
        setConnectionState('connected')
        reconnectCount.current = 0
        onOpen?.()
      }
      
      ws.current.onclose = () => {
        console.log('WebSocket disconnected')
        setIsConnected(false)
        setConnectionState('disconnected')
        onClose?.()
        
        // Intento de reconexión
        if (reconnect && reconnectCount.current < reconnectAttempts) {
          reconnectCount.current++
          console.log(`Reconnecting in ${reconnectInterval}ms... (attempt ${reconnectCount.current})`)
          
          reconnectTimeoutId.current = setTimeout(() => {
            connect()
          }, reconnectInterval)
        }
      }
      
      ws.current.onerror = (event) => {
        console.error('WebSocket error:', event)
        setConnectionState('error')
        setError(new Error('WebSocket connection error'))
        onError?.(event)
      }
      
      ws.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as WebSocketMessage
          setLastMessage(message)
          onMessage?.(message)
        } catch (err) {
          console.error('Error parsing WebSocket message:', err)
        }
      }
    } catch (err) {
      console.error('Error creating WebSocket:', err)
      setError(err as Error)
      setConnectionState('error')
    }
  }, [session_id, onOpen, onClose, onError, onMessage, reconnect, reconnectInterval, reconnectAttempts])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutId.current) {
      clearTimeout(reconnectTimeoutId.current)
      reconnectTimeoutId.current = null
    }
    
    if (ws.current) {
      ws.current.close()
      ws.current = null
    }
    
    setIsConnected(false)
    setConnectionState('disconnected')
  }, [])

  const send = useCallback((data: any) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      const message = typeof data === 'string' ? data : JSON.stringify(data)
      ws.current.send(message)
    } else {
      console.warn('WebSocket is not connected')
    }
  }, [])

  const reconnectManually = useCallback(() => {
    disconnect()
    reconnectCount.current = 0
    connect()
  }, [connect, disconnect])

  // Efecto para conectar al montar y desconectar al desmontar
  useEffect(() => {
    connect()
    
    // Ping periódico para mantener la conexión viva
    const pingInterval = setInterval(() => {
      if (isConnected) {
        send('ping')
      }
    }, 30000) // Cada 30 segundos
    
    return () => {
      clearInterval(pingInterval)
      disconnect()
    }
  }, []) // Solo ejecutar al montar/desmontar

  return {
    isConnected,
    connectionState,
    send,
    reconnect: reconnectManually,
    disconnect,
    lastMessage,
    error
  }
}

// Hook especializado para progreso de batch
export function useBatchProgress(
  batch_id: string,
  onProgress?: (progress: BatchProgressMessage) => void
) {
  const [progress, setProgress] = useState<BatchProgressMessage | null>(null)
  
  const handleMessage = useCallback((message: WebSocketMessage) => {
    if (message.type === 'batch_progress' && 'batch_id' in message && (message as any).batch_id === batch_id) {
      const batchMessage = message as unknown as BatchProgressMessage
      setProgress(batchMessage)
      onProgress?.(batchMessage)
    }
  }, [batch_id, onProgress])
  
  const { isConnected, send } = useWebSocket({
    session_id: batch_id,
    onMessage: handleMessage
  })
  
  return { isConnected, progress, send }
}

// Hook especializado para progreso de análisis
export function useAnalysisProgress(
  site_url: string,
  onProgress?: (progress: AnalysisProgressMessage) => void
) {
  const [progress, setProgress] = useState<AnalysisProgressMessage | null>(null)
  
  const handleMessage = useCallback((message: WebSocketMessage) => {
    if (
      message.type === 'analysis_progress' && 
      'site_url' in message &&
      (message as any).site_url === site_url
    ) {
      const analysisMessage = message as unknown as AnalysisProgressMessage
      setProgress(analysisMessage)
      onProgress?.(analysisMessage)
    }
  }, [site_url, onProgress])
  
  const { isConnected, send } = useWebSocket({
    onMessage: handleMessage
  })
  
  return { isConnected, progress, send }
}