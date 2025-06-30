import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import ThemeProvider from '@mui/material/styles/ThemeProvider'
import CssBaseline from '@mui/material/CssBaseline'
import { LocalizationProvider } from '@mui/x-date-pickers'
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns'
import { es } from 'date-fns/locale/es'

import App from './App'
import theme from './theme'
import { initializeServiceWorker } from './utils/serviceWorker'

// Configuración de React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutos
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

// Base path para routing cuando se sirve desde un subdirectorio
const basename = import.meta.env.VITE_BASE_PATH || '/'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter basename={basename}>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={es}>
            <App />
          </LocalizationProvider>
        </ThemeProvider>
      </BrowserRouter>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  </React.StrictMode>
)

// Según SECCIÓN 9.4 - Inicializar Service Worker después del render
// Inicializar service worker en producción
if (import.meta.env.PROD) {
  initializeServiceWorker().then((status) => {
    if (status.isRegistered) {
      console.log('Service Worker inicializado correctamente');
    } else {
      console.log('Service Worker no pudo inicializarse');
    }
  }).catch((error) => {
    console.error('Error al inicializar Service Worker:', error);
  });
}