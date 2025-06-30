import { Routes, Route, Navigate } from 'react-router-dom'
import { Suspense, lazy } from 'react'
import { Box, CircularProgress } from '@mui/material'

// Layout principal
import MainLayout from '@components/templates/MainLayout'

// Lazy loading de páginas
const HomePage = lazy(() => import('@pages/HomePage'))
const WizardPage = lazy(() => import('@pages/WizardPage'))
const BulkUploadPage = lazy(() => import('@pages/BulkUploadPage'))
const PatternsPage = lazy(() => import('@pages/PatternsPage'))

// Componente de carga
const LoadingFallback = () => (
  <Box
    display="flex"
    justifyContent="center"
    alignItems="center"
    minHeight="100vh"
  >
    <CircularProgress />
  </Box>
)

function App() {
  return (
    <MainLayout>
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/wizard" element={<WizardPage />} />
          <Route path="/bulk" element={<BulkUploadPage />} />
          <Route path="/patterns" element={<PatternsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </MainLayout>
  )
}

export default App