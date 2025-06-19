import React, { useState, useCallback, useRef } from 'react';
import {
  Container,
  Box,
  Typography,
  Pagination,
  Alert,
  Paper,
  Stack,
} from '@mui/material';
import { FilterHeader, HechosList } from '@/components/organisms';
import { FeedbackSnackbar, type FeedbackSnackbarRef } from '@/components/molecules';
import { useDashboard, useFilters, useFeedback } from '@/hooks/dashboard';
import type { FilterState } from '@/types/domain';

export const DashboardPage: React.FC = () => {
  // State management
  const snackbarRef = useRef<FeedbackSnackbarRef>(null);

  // Hooks
  const filters = useFilters();
  const feedback = useFeedback();
  const dashboard = useDashboard({
    filters: filters.filters,
    autoRefresh: true,
  });

  // Event handlers
  const handleFiltersChange = useCallback(
    (newFilters: Partial<FilterState>) => {
      filters.updateFilters(newFilters);
      // Reset to page 1 when filters change
      dashboard.changePage(1);
    },
    [filters, dashboard]
  );

  const handleResetFilters = useCallback(() => {
    filters.clearAllFilters();
    dashboard.changePage(1);
  }, [filters, dashboard]);

  const handlePageChange = useCallback(
    (_: React.ChangeEvent<unknown>, value: number) => {
      dashboard.changePage(value);
    },
    [dashboard]
  );

  const handleImportanceChange = useCallback(
    async (hechoId: number, newImportance: number) => {
      try {
        await feedback.submitImportanciaFeedback(hechoId, newImportance);
        snackbarRef.current?.showSuccess(`Importancia actualizada a ${newImportance}/10`);
        
        // Refresh data to reflect changes
        dashboard.refreshData();
      } catch (error) {
        const errorMessage = feedback.getErrorMessage(hechoId) || 'Error al actualizar importancia';
        snackbarRef.current?.showError(errorMessage);
      }
    },
    [feedback, dashboard]
  );

  const handleMarkAsFalse = useCallback(
    async (hechoId: number) => {
      try {
        await feedback.submitEvaluacionEditorial(hechoId, {
          evaluacion: 'falso',
          justificacion: 'Marcado como falso desde el dashboard',
        });
        snackbarRef.current?.showSuccess('Hecho marcado como falso correctamente');
        
        // Refresh data to reflect changes
        dashboard.refreshData();
      } catch (error) {
        const errorMessage = feedback.getErrorMessage(hechoId) || 'Error al marcar como falso';
        snackbarRef.current?.showError(errorMessage);
      }
    },
    [feedback, dashboard]
  );

  const handleFeedbackSubmitted = useCallback(() => {
    dashboard.refreshData();
    snackbarRef.current?.showSuccess('Feedback enviado correctamente');
  }, [dashboard]);

  const isImportanceLoading = useCallback(
    (hechoId: number) => {
      return feedback.isSubmitting(hechoId, 'importancia');
    },
    [feedback]
  );

  // Calculate total pages
  const totalPages = Math.ceil(
    (dashboard.stats?.totalHechos || 0) / dashboard.pagination.pageSize
  );

  return (
    <Container 
      maxWidth="xl" 
      sx={{ 
        py: { xs: 2, sm: 3, md: 4 },
        px: { xs: 1, sm: 2, md: 3 },
        backgroundColor: 'background.default',
        minHeight: '100vh'
      }}
    >
      {/* Header premium con gradiente sutil */}
      <Paper
        elevation={0}
        sx={{
          p: 5,
          mb: 5,
          background: 'linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%)',
          borderRadius: 3,
          border: '1px solid',
          borderColor: '#E5E7EB',
          position: 'relative',
          overflow: 'hidden',
          '&::before': {
            content: '""',
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            height: '3px',
            background: 'linear-gradient(90deg, #005A99 0%, #1976D2 50%, #D3264C 100%)'
          }
        }}
      >
        <Box sx={{ maxWidth: '700px' }}>
          <Typography 
            variant="h4" 
            component="h1" 
            gutterBottom
            sx={{
              fontWeight: 800,
              color: '#0F0F0F',
              mb: 2,
              background: 'linear-gradient(135deg, #005A99 0%, #1976D2 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}
          >
            📊 Dashboard Editorial
          </Typography>
          <Typography 
            variant="body1" 
            color="text.secondary"
            sx={{ 
              mb: 4,
              fontSize: '1.25rem',
              lineHeight: 1.6,
              fontWeight: 500
            }}
          >
            Revisa y valida hechos extraídos por La Máquina de Noticias con herramientas de análisis editorial profesional
          </Typography>
          
          {dashboard.stats && (
            <Stack direction="row" spacing={3} sx={{ flexWrap: 'wrap', gap: 2 }}>
              <Box sx={{ 
                display: 'flex', 
                alignItems: 'center',
                px: 3,
                py: 1.5,
                backgroundColor: 'rgba(0, 90, 153, 0.08)',
                borderRadius: 2,
                border: '1px solid rgba(0, 90, 153, 0.2)'
              }}>
                <Typography variant="h6" color="#005A99" sx={{ fontWeight: 700, mr: 1 }}>
                  {dashboard.stats.totalHechos.toLocaleString()}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 600 }}>
                  hechos totales
                </Typography>
              </Box>
              <Box sx={{ 
                display: 'flex', 
                alignItems: 'center',
                px: 3,
                py: 1.5,
                backgroundColor: 'rgba(107, 114, 128, 0.08)',
                borderRadius: 2,
                border: '1px solid rgba(107, 114, 128, 0.2)'
              }}>
                <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 600 }}>
                  Página {dashboard.pagination.page} de {totalPages}
                </Typography>
              </Box>
            </Stack>
          )}
        </Box>
      </Paper>

      {/* Error Display */}
      {dashboard.error && (
        <Alert 
          severity="error" 
          sx={{ mb: 3 }}
          action={
            dashboard.canRetry ? (
              <Typography 
                variant="body2" 
                sx={{ cursor: 'pointer', textDecoration: 'underline' }}
                onClick={dashboard.retryLastOperation}
              >
                Reintentar
              </Typography>
            ) : undefined
          }
        >
          {dashboard.errorMessage}
        </Alert>
      )}

      {/* Filters */}
      <Box mb={4}>
        <FilterHeader
          filters={filters.filters}
          filterOptions={filters.options}
          onFiltersChange={handleFiltersChange}
          onResetFilters={handleResetFilters}
          isLoading={dashboard.loading || filters.optionsLoading}
          totalResults={dashboard.stats?.totalHechos || 0}
        />
      </Box>

      {/* Main Content */}
      <Box mb={4}>
        <HechosList
          hechos={dashboard.hechos}
          isLoading={dashboard.loading}
          onImportanceChange={handleImportanceChange}
          onMarkAsFalse={handleMarkAsFalse}
          onFeedbackSubmitted={handleFeedbackSubmitted}
          isImportanceLoading={isImportanceLoading}
        />
      </Box>

      {/* Pagination */}
      {totalPages > 1 && (
        <Box 
          display="flex" 
          justifyContent="center" 
          mt={4}
        >
          <Pagination
            count={totalPages}
            page={dashboard.pagination.page}
            onChange={handlePageChange}
            color="primary"
            size="large"
            showFirstButton
            showLastButton
            disabled={dashboard.loading}
            sx={{
              '& .MuiPaginationItem-root': {
                fontSize: '0.875rem',
                borderRadius: 1
              }
            }}
          />
        </Box>
      )}

      {/* Feedback Snackbar */}
      <FeedbackSnackbar 
        ref={snackbarRef}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      />
    </Container>
  );
};