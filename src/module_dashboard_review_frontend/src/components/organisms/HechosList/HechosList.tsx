import React from 'react';
import {
  Box,
  CircularProgress,
  Typography,
  Paper,
  Alert,
  Pagination,
  useMediaQuery,
  useTheme,
  Skeleton,
  Stack,
  Divider
} from '@mui/material';
import {
  ErrorOutline as ErrorIcon,
  SearchOff as EmptyIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { HechoCard } from '@/components/molecules';
import type { Hecho } from '@/types/domain';

interface HechosListProps {
  hechos: Hecho[];
  isLoading: boolean;
  error?: string | null;
  // Paginación
  page?: number;
  totalPages?: number;
  itemsPerPage?: number;
  totalItems?: number;
  onPageChange?: (page: number) => void;
  // Callbacks existentes
  onImportanceChange?: (hechoId: number, newImportance: number) => void;
  onMarkAsFalse?: (hechoId: number) => void;
  onFeedbackSubmitted?: () => void;
  isImportanceLoading?: (hechoId: number) => boolean;
  // Callback para retry en caso de error
  onRetry?: () => void;
}

// Componente de loading skeleton para mejor UX
const HechoCardSkeleton: React.FC = () => (
  <Paper
    elevation={1}
    sx={{
      p: 3,
      mb: 2,
      border: 1,
      borderColor: 'divider'
    }}
  >
    <Skeleton variant="text" width="100%" height={60} sx={{ mb: 2 }} />
    <Box sx={{ mb: 2 }}>
      <Skeleton variant="text" width="80%" height={24} sx={{ mb: 1 }} />
      <Skeleton variant="text" width="60%" height={20} sx={{ mb: 1 }} />
      <Skeleton variant="text" width="40%" height={20} />
    </Box>
    <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
      <Skeleton variant="rectangular" width={80} height={24} />
      <Skeleton variant="rectangular" width={100} height={24} />
      <Skeleton variant="rectangular" width={70} height={24} />
    </Box>
    <Skeleton variant="rectangular" width="100%" height={40} sx={{ mb: 2 }} />
    <Skeleton variant="rectangular" width={120} height={32} />
  </Paper>
);

export const HechosList: React.FC<HechosListProps> = ({
  hechos,
  isLoading,
  error,
  page = 1,
  totalPages = 1,
  itemsPerPage = 10,
  totalItems = 0,
  onPageChange,
  onImportanceChange,
  onMarkAsFalse,
  onFeedbackSubmitted,
  isImportanceLoading,
  onRetry
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  // Estado de loading - mostrar skeletons
  if (isLoading) {
    return (
      <Box>
        <Stack spacing={0}>
          {Array.from({ length: itemsPerPage }, (_, index) => (
            <HechoCardSkeleton key={index} />
          ))}
        </Stack>
        {/* Pagination skeleton durante loading */}
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
          <Skeleton variant="rectangular" width={300} height={32} />
        </Box>
      </Box>
    );
  }

  // Estado de error
  if (error) {
    return (
      <Paper
        elevation={1}
        sx={{
          p: 4,
          textAlign: 'center',
          backgroundColor: 'error.50',
          border: 1,
          borderColor: 'error.200',
          borderRadius: 2,
        }}
      >
        <Box sx={{ mb: 2 }}>
          <ErrorIcon 
            sx={{ 
              fontSize: 48, 
              color: 'error.main',
              mb: 2
            }} 
          />
        </Box>
        <Typography variant="h6" color="error.main" gutterBottom>
          Error al cargar los hechos
        </Typography>
        <Typography variant="body2" color="error.dark" sx={{ mb: 3 }}>
          {error}
        </Typography>
        {onRetry && (
          <Alert 
            severity="error" 
            action={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <RefreshIcon 
                  sx={{ cursor: 'pointer' }} 
                  onClick={onRetry}
                />
                <Typography variant="button" onClick={onRetry} sx={{ cursor: 'pointer' }}>
                  Reintentar
                </Typography>
              </Box>
            }
          >
            Ocurrió un problema al cargar los datos
          </Alert>
        )}
      </Paper>
    );
  }

  // Estado vacío
  if (hechos.length === 0) {
    return (
      <Paper
        elevation={1}
        sx={{
          p: 6,
          textAlign: 'center',
          backgroundColor: 'background.paper',
          borderRadius: 2,
          border: 1,
          borderColor: 'divider'
        }}
      >
        <Box sx={{ mb: 2 }}>
          <EmptyIcon 
            sx={{ 
              fontSize: 64, 
              color: 'text.secondary',
              mb: 2
            }} 
          />
        </Box>
        <Typography variant="h6" color="text.secondary" gutterBottom>
          No se encontraron hechos
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Intenta ajustar los filtros para encontrar más contenido.
        </Typography>
        <Typography variant="caption" color="text.disabled">
          O verifica que haya datos disponibles para el período seleccionado
        </Typography>
      </Paper>
    );
  }

  // Estado con datos - lista de hechos
  return (
    <Box>
      {/* Header simplificado */}
      {totalItems > 0 && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="body2" color="text.secondary">
            {totalItems.toLocaleString()} hechos encontrados
          </Typography>
        </Box>
      )}

      {/* Lista de HechoCards */}
      <Stack spacing={0}>
        {hechos.map((hecho) => (
          <HechoCard
            key={hecho.id}
            hecho={hecho}
            onImportanceChange={onImportanceChange}
            onMarkAsFalse={onMarkAsFalse}
            onFeedbackSubmitted={onFeedbackSubmitted}
            isImportanceLoading={isImportanceLoading}
          />
        ))}
      </Stack>

      {/* Paginación */}
      {totalPages > 1 && onPageChange && (
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center',
          py: 4,
          mt: 3,
          borderTop: 1,
          borderColor: 'divider'
        }}>
          <Pagination
            count={totalPages}
            page={page}
            onChange={(_, newPage) => onPageChange(newPage)}
            color="primary"
            size={isMobile ? 'small' : 'medium'}
            showFirstButton
            showLastButton
            sx={{
              '& .MuiPagination-ul': {
                flexWrap: 'wrap',
                justifyContent: 'center'
              }
            }}
          />
        </Box>
      )}


    </Box>
  );
};