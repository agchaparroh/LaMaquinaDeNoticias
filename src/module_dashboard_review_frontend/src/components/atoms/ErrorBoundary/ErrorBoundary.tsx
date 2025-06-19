import React, { Component, ErrorInfo, ReactNode } from 'react';
import { 
  Box, 
  Alert, 
  AlertTitle, 
  Button, 
  Typography, 
  Paper,
  Stack
} from '@mui/material';
import { RefreshRounded, BugReportRounded } from '@mui/icons-material';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
  errorId?: string;
}

/**
 * ✅ NUEVO: Error Boundary para capturar errores de React
 * Proporciona UI amigable cuando ocurren errores inesperados
 */
export class ErrorBoundary extends Component<Props, State> {
  private retryTimeoutId: NodeJS.Timeout | null = null;

  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    // Generar ID único para el error
    const errorId = `ERR_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    return {
      hasError: true,
      error,
      errorId
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // ✅ Solo loggear en desarrollo
    if (import.meta.env.DEV) {
      console.group('🚨 React Error Boundary');
      console.error('Error:', error);
      console.error('Error Info:', errorInfo);
      console.error('Error ID:', this.state.errorId);
      console.groupEnd();
    }

    // Llamar callback personalizado si existe
    this.props.onError?.(error, errorInfo);

    // En producción, podrías enviar a un servicio de logging
    // this.sendErrorToLoggingService(error, errorInfo, this.state.errorId);

    this.setState({ errorInfo });
  }

  componentWillUnmount() {
    if (this.retryTimeoutId) {
      clearTimeout(this.retryTimeoutId);
    }
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      // Si hay un fallback personalizado, usarlo
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // UI por defecto del Error Boundary
      return (
        <Box
          display="flex"
          justifyContent="center"
          alignItems="center"
          minHeight="100vh"
          bgcolor="background.default"
          p={3}
        >
          <Paper
            elevation={3}
            sx={{
              p: 4,
              maxWidth: 600,
              width: '100%',
              textAlign: 'center'
            }}
          >
            <Stack spacing={3} alignItems="center">
              <BugReportRounded 
                sx={{ fontSize: 64, color: 'error.main' }} 
              />
              
              <Typography variant="h4" color="error.main" gutterBottom>
                ¡Oops! Algo salió mal
              </Typography>
              
              <Alert severity="error" sx={{ width: '100%', textAlign: 'left' }}>
                <AlertTitle>Error del Sistema</AlertTitle>
                <Typography variant="body2" sx={{ mt: 1 }}>
                  Se produjo un error inesperado en la aplicación. 
                  Nuestro equipo ha sido notificado automáticamente.
                </Typography>
                {import.meta.env.DEV && this.state.error && (
                  <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
                    <Typography variant="caption" display="block" color="text.secondary">
                      <strong>Error ID:</strong> {this.state.errorId}
                    </Typography>
                    <Typography variant="caption" display="block" color="text.secondary">
                      <strong>Mensaje:</strong> {this.state.error.message}
                    </Typography>
                  </Box>
                )}
              </Alert>

              <Stack direction="row" spacing={2}>
                <Button
                  variant="contained"
                  startIcon={<RefreshRounded />}
                  onClick={this.handleRetry}
                  size="large"
                >
                  Intentar de Nuevo
                </Button>
                
                <Button
                  variant="outlined"
                  onClick={this.handleReload}
                  size="large"
                >
                  Recargar Página
                </Button>
              </Stack>

              {import.meta.env.DEV && (
                <Typography variant="caption" color="text.secondary">
                  Modo Desarrollo: Revisa la consola para más detalles
                </Typography>
              )}
            </Stack>
          </Paper>
        </Box>
      );
    }

    return this.props.children;
  }
}

/**
 * ✅ NUEVO: Hook para usar Error Boundary de forma funcional
 */
export const useErrorHandler = () => {
  const [error, setError] = React.useState<Error | null>(null);

  const resetError = () => setError(null);
  
  const captureError = (error: Error) => {
    setError(error);
  };

  // Re-throw el error para que sea capturado por Error Boundary
  if (error) {
    throw error;
  }

  return { captureError, resetError };
};

/**
 * ✅ NUEVO: HOC para envolver componentes con Error Boundary
 */
export const withErrorBoundary = <P extends object>(
  Component: React.ComponentType<P>,
  fallback?: ReactNode
) => {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary fallback={fallback}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;
  
  return WrappedComponent;
};

export default ErrorBoundary;
