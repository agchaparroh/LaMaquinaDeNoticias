import React, { useState, useEffect } from 'react';
import { Box, Card, CardContent, Typography, Grid, LinearProgress } from '@mui/material';
import useWebSocket, { ReadyState } from 'react-use-websocket';

// Según SECCIÓN 19.1 - Monitor de rendimiento en tiempo real
interface PerformanceMetrics {
  activeConnections: number;
  cacheHitRate: number;
  averageResponseTime: number;
  requestsPerMinute: number;
  timestamp: string;
}

interface PerformanceMonitorProps {
  websocketUrl?: string;
}

const PerformanceMonitor: React.FC<PerformanceMonitorProps> = ({ 
  websocketUrl = 'ws://localhost:8080/performance' 
}) => {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    activeConnections: 0,
    cacheHitRate: 0,
    averageResponseTime: 0,
    requestsPerMinute: 0,
    timestamp: new Date().toISOString()
  });

  // Según SECCIÓN 19.1 - WebSocket para métricas en tiempo real
  const { lastMessage, readyState } = useWebSocket(websocketUrl, {
    onOpen: () => console.log('Performance monitor connected'),
    onClose: () => console.log('Performance monitor disconnected'),
    onError: (event) => console.error('Performance monitor error:', event),
    shouldReconnect: (closeEvent) => true,
    reconnectAttempts: 10,
    reconnectInterval: 3000,
    heartbeat: {
      message: 'ping',
      returnMessage: 'pong',
      timeout: 30000,
      interval: 15000
    }
  });

  // Procesar mensajes del WebSocket
  useEffect(() => {
    if (lastMessage !== null) {
      try {
        const data = JSON.parse(lastMessage.data);
        if (data.type === 'performance_metrics') {
          setMetrics(data.metrics);
        }
      } catch (error) {
        console.error('Error parsing performance data:', error);
      }
    }
  }, [lastMessage]);

  // Según SECCIÓN 19.1 - Fallback con datos simulados si no hay WebSocket
  useEffect(() => {
    if (readyState !== ReadyState.OPEN) {
      const interval = setInterval(() => {
        setMetrics({
          activeConnections: Math.floor(Math.random() * 50) + 10,
          cacheHitRate: Math.floor(Math.random() * 30) + 70,
          averageResponseTime: Math.floor(Math.random() * 500) + 100,
          requestsPerMinute: Math.floor(Math.random() * 100) + 50,
          timestamp: new Date().toISOString()
        });
      }, 2000);

      return () => clearInterval(interval);
    }
  }, [readyState]);

  const getStatusColor = (value: number, threshold: number, reverse = false) => {
    if (reverse) {
      return value < threshold ? 'success' : value < threshold * 1.5 ? 'warning' : 'error';
    }
    return value > threshold ? 'success' : value > threshold * 0.7 ? 'warning' : 'error';
  };

  const connectionStatus = {
    [ReadyState.CONNECTING]: 'Conectando...',
    [ReadyState.OPEN]: 'Conectado',
    [ReadyState.CLOSING]: 'Cerrando...',
    [ReadyState.CLOSED]: 'Desconectado',
    [ReadyState.UNINSTANTIATED]: 'Sin inicializar'
  }[readyState];

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Monitor de Rendimiento
      </Typography>
      
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Estado: {connectionStatus} | Última actualización: {new Date(metrics.timestamp).toLocaleTimeString()}
      </Typography>

      <Grid container spacing={2}>
        {/* Conexiones Activas */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" color={getStatusColor(metrics.activeConnections, 30)}>
                {metrics.activeConnections}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Conexiones Activas
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={Math.min((metrics.activeConnections / 50) * 100, 100)}
                color={getStatusColor(metrics.activeConnections, 30) as any}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Cache Hit Rate */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" color={getStatusColor(metrics.cacheHitRate, 80)}>
                {metrics.cacheHitRate}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Tasa de Acierto de Caché
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={metrics.cacheHitRate}
                color={getStatusColor(metrics.cacheHitRate, 80) as any}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Tiempo Promedio de Respuesta */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" color={getStatusColor(metrics.averageResponseTime, 200, true)}>
                {metrics.averageResponseTime}ms
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Tiempo Promedio de Respuesta
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={Math.min((metrics.averageResponseTime / 1000) * 100, 100)}
                color={getStatusColor(metrics.averageResponseTime, 200, true) as any}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Solicitudes por Minuto */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" color={getStatusColor(metrics.requestsPerMinute, 100)}>
                {metrics.requestsPerMinute}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Solicitudes por Minuto
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={Math.min((metrics.requestsPerMinute / 200) * 100, 100)}
                color={getStatusColor(metrics.requestsPerMinute, 100) as any}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default PerformanceMonitor;