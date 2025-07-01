import { useState } from 'react'
import { Global, css } from '@emotion/react'
import {
  Box,
  Paper,
  Typography,
  LinearProgress,
  Chip,
  Alert
} from '@mui/material'
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import {
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  HourglassEmpty as PendingIcon,
  Sync as ProcessingIcon
} from '@mui/icons-material'
import { StatusChip } from '@components/atoms'
import type { BatchItem } from '@/types'

interface BatchProcessingStatusProps {
  items: BatchItem[]
  totalProgress: number
  isProcessing: boolean
}

function BatchProcessingStatus({ 
  items, 
  totalProgress,
  isProcessing 
}: BatchProcessingStatusProps) {
  const getStatusIcon = (status: BatchItem['status']) => {
    switch (status) {
      case 'completed':
        return <SuccessIcon color="success" />
      case 'error':
        return <ErrorIcon color="error" />
      case 'processing':
        return <ProcessingIcon color="primary" className="rotating" />
      default:
        return <PendingIcon color="disabled" />
    }
  }

  const stats = {
    completed: items.filter(i => i.status === 'completed').length,
    errors: items.filter(i => i.status === 'error').length,
    processing: items.filter(i => i.status === 'processing').length,
    pending: items.filter(i => i.status === 'pending').length
  }

  return (
    <Box>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Progreso General
        </Typography>
        
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2" color="text.secondary">
              {isProcessing ? 'Procesando...' : 'Completado'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {Math.round(totalProgress)}%
            </Typography>
          </Box>
          <LinearProgress 
            variant="determinate" 
            value={totalProgress} 
            sx={{ height: 8, borderRadius: 4 }}
          />
        </Box>

        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Chip
            icon={<SuccessIcon />}
            label={`Completados: ${stats.completed}`}
            color="success"
            size="small"
          />
          <Chip
            icon={<ErrorIcon />}
            label={`Errores: ${stats.errors}`}
            color="error"
            size="small"
          />
          <Chip
            icon={<ProcessingIcon />}
            label={`Procesando: ${stats.processing}`}
            color="primary"
            size="small"
          />
          <Chip
            icon={<PendingIcon />}
            label={`Pendientes: ${stats.pending}`}
            size="small"
          />
        </Box>
      </Paper>

      <Typography variant="h6" gutterBottom>
        Detalle de Procesamiento
      </Typography>

      {/* Según SECCIÓN 2.1 - Reemplazar List con DataGrid EXACTO */}
      <DataGrid
        rows={items.map(item => ({
          id: item.id,
          medio: item.name,
          seccion: item.seccion || 'N/A',
          url: item.url,
          area_geografica: item.area_geografica || 'N/A',
          tipo_medio: item.tipo_medio || 'N/A',
          status: item.status,
          progress: item.progress || 0
        }))}
        columns={[
          { field: 'medio', headerName: 'Medio', width: 150 },
          { field: 'seccion', headerName: 'Sección', width: 120 },
          { field: 'url', headerName: 'URL', width: 250 },
          { field: 'area_geografica', headerName: 'Área', width: 100 },
          { field: 'tipo_medio', headerName: 'Tipo', width: 100 },
          { 
            field: 'status', 
            headerName: 'Estado', 
            width: 120,
            renderCell: (params) => <Chip label={params.value} size="small" />
          },
          {
            field: 'progress',
            headerName: 'Progreso',
            width: 150,
            renderCell: (params) => <LinearProgress variant="determinate" value={params.value} />
          }
        ]}
        /* Según SECCIÓN 2.2 - Agregar funcionalidades de tabla */
        paginationModel={{ page: 0, pageSize: 10 }}
        pageSizeOptions={[10, 25, 50]}
        autoHeight
        checkboxSelection
        disableRowSelectionOnClick
      />

      <Global 
        styles={css`
          @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
          .rotating {
            animation: rotate 1s linear infinite;
          }
        `} 
      />
    </Box>
  )
}

export default BatchProcessingStatus