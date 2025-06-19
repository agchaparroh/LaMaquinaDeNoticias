import React, { Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, CssBaseline, Box, CircularProgress } from '@mui/material';
import { theme } from '@/theme';
import { ErrorBoundary } from '@/components/atoms';
import { DashboardPage, NotFoundPage } from '@/components/pages';

/**
 * ✅ MEJORADO: Componente de loading para Suspense
 */
const SuspenseLoader: React.FC = () => (
  <Box
    display="flex"
    justifyContent="center"
    alignItems="center"
    minHeight="100vh"
    bgcolor="background.default"
  >
    <CircularProgress size={48} />
  </Box>
);

/**
 * ✅ MEJORADO: App con Error Boundary y Suspense para mejor UX
 */
function App() {
  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        // ✅ Solo en desarrollo - loggear errores detallados
        if (import.meta.env.DEV) {
          console.group('🚨 App Level Error');
          console.error('Error:', error);
          console.error('Error Info:', errorInfo);
          console.groupEnd();
        }
        
        // En producción, podrías enviar a Sentry u otro servicio
        // sendErrorToService(error, errorInfo);
      }}
    >
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <BrowserRouter>
          <Suspense fallback={<SuspenseLoader />}>
            <Routes>
              {/* Main Dashboard Route */}
              <Route 
                path="/dashboard" 
                element={
                  <ErrorBoundary>
                    <DashboardPage />
                  </ErrorBoundary>
                } 
              />
              
              {/* Default Route - Redirect to Dashboard */}
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              
              {/* 404 Not Found Route */}
              <Route 
                path="/404" 
                element={
                  <ErrorBoundary>
                    <NotFoundPage />
                  </ErrorBoundary>
                } 
              />
              
              {/* Catch-all Route - Redirect to 404 */}
              <Route path="*" element={<Navigate to="/404" replace />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
