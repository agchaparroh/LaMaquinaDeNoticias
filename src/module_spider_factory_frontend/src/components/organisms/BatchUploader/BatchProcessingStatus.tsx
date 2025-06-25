import {
  Box,
  Paper,
  Typography,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Collapse,
  IconButton,
  Alert
} from '@mui/material'
import {
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  HourglassEmpty as PendingIcon,
  Sync as ProcessingIcon,
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon
} from '@mui/icons-material'
import { useState } from 'react'
import { StatusChip } from '@components/atoms'

export interface BatchItem {
  id: string
  url: string
  name: string
  status: 'pending' | 'processing' | 'completed' | 'error'
  progress?: number
  result?: {
    spider_count: number
    strategy?: string
    error?: string
  }
}

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
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set())

  const toggleExpand = (id: string) => {
    setExpandedItems(prev => {
      const newSet = new Set(prev)
      if (newSet.has(id)) {
        newSet.delete(id)
      } else {
        newSet.add(id)
      }
      return newSet
    })
  }

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

      <List>
        {items.map((item) => (
          <Paper key={item.id} sx={{ mb: 1 }}>
            <ListItem
              secondaryAction={
                item.status !== 'pending' && (
                  <IconButton onClick={() => toggleExpand(item.id)}>
                    {expandedItems.has(item.id) ? <CollapseIcon /> : <ExpandIcon />}
                  </IconButton>
                )
              }
            >
              <ListItemIcon>
                {getStatusIcon(item.status)}
              </ListItemIcon>
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="subtitle2">{item.name}</Typography>
                    <StatusChip
                      status={
                        item.status === 'completed' ? 'success' :
                        item.status === 'error' ? 'error' :
                        item.status === 'processing' ? 'info' :
                        'pending'
                      }
                      label={
                        item.status === 'completed' ? 'Completado' :
                        item.status === 'error' ? 'Error' :
                        item.status === 'processing' ? 'Procesando' :
                        'Pendiente'
                      }
                    />
                  </Box>
                }
                secondary={
                  <Typography variant="caption" color="text.secondary">
                    {item.url}
                  </Typography>
                }
              />
            </ListItem>
            
            <Collapse in={expandedItems.has(item.id)} timeout="auto" unmountOnExit>
              <Box sx={{ px: 3, pb: 2 }}>
                {item.status === 'processing' && item.progress !== undefined && (
                  <LinearProgress 
                    variant="determinate" 
                    value={item.progress} 
                    sx={{ mb: 2 }}
                  />
                )}
                
                {item.result && (
                  <>
                    {item.status === 'completed' && (
                      <Alert severity="success" sx={{ mb: 1 }}>
                        Spider generado exitosamente
                        {item.result.spider_count > 0 && 
                          ` - ${item.result.spider_count} spider(s) creado(s)`
                        }
                        {item.result.strategy && 
                          ` usando estrategia ${item.result.strategy}`
                        }
                      </Alert>
                    )}
                    
                    {item.status === 'error' && (
                      <Alert severity="error">
                        {item.result.error || 'Error desconocido al procesar el sitio'}
                      </Alert>
                    )}
                  </>
                )}
              </Box>
            </Collapse>
          </Paper>
        ))}
      </List>

      <style jsx global>{`
        @keyframes rotate {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .rotating {
          animation: rotate 1s linear infinite;
        }
      `}</style>
    </Box>
  )
}

export default BatchProcessingStatus