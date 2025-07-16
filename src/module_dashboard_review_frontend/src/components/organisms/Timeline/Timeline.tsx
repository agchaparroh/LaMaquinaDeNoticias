import React from 'react';
import {
  Box,
  Typography,
  Chip,
  Stack,
  Paper,
  useTheme
} from '@mui/material';
import {
  ArrowForward as ArrowForwardIcon,
  ArrowBack as ArrowBackIcon,
  SwapHoriz as SwapHorizIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Add as AddIcon
} from '@mui/icons-material';
import type { Hecho } from '@/types/domain';
import { getRelationType, getRelationStrength } from '@/utils/clustering';

interface TimelineProps {
  protagonist: Hecho;
  relatedHechos: Hecho[];
  onHechoClick?: (hecho: Hecho) => void;
}

export const Timeline: React.FC<TimelineProps> = React.memo(({
  protagonist,
  relatedHechos,
  onHechoClick
}) => {
  const theme = useTheme();

  const getRelationIcon = (tipo: string) => {
    switch (tipo) {
      case 'causa':
        return <ArrowBackIcon fontSize="small" />;
      case 'consecuencia':
        return <ArrowForwardIcon fontSize="small" />;
      case 'contradictorio':
        return <WarningIcon fontSize="small" />;
      case 'ampliacion':
        return <AddIcon fontSize="small" />;
      case 'relacionado':
      default:
        return <SwapHorizIcon fontSize="small" />;
    }
  };

  const getRelationColor = (tipo: string) => {
    switch (tipo) {
      case 'causa':
        return '#2196F3'; // Blue
      case 'consecuencia':
        return '#4CAF50'; // Green
      case 'contradictorio':
        return '#FF5722'; // Red
      case 'ampliacion':
        return '#9C27B0'; // Purple
      case 'relacionado':
      default:
        return '#607D8B'; // Blue Grey
    }
  };

  const getRelationLabel = (tipo: string) => {
    switch (tipo) {
      case 'causa':
        return 'Causa';
      case 'consecuencia':
        return 'Consecuencia';
      case 'contradictorio':
        return 'Contradice';
      case 'ampliacion':
        return 'Amplía';
      case 'relacionado':
      default:
        return 'Relacionado';
    }
  };

  return (
    <Box sx={{ py: 2 }}>
      <Typography 
        variant="subtitle2" 
        sx={{ 
          mb: 2, 
          fontWeight: 600,
          color: 'primary.main',
          display: 'flex',
          alignItems: 'center',
          gap: 1
        }}
      >
        <InfoIcon fontSize="small" />
        Línea temporal de hechos relacionados
      </Typography>

      <Stack spacing={2}>
        {relatedHechos.map((hecho) => {
          const relationType = getRelationType(protagonist, hecho.id) || 'relacionado';
          const relationStrength = getRelationStrength(protagonist, hecho.id);
          const relationColor = getRelationColor(relationType);

          return (
            <Paper
              key={hecho.id}
              elevation={0}
              sx={{
                p: 2,
                border: '1px solid',
                borderColor: 'divider',
                borderLeft: `4px solid ${relationColor}`,
                cursor: onHechoClick ? 'pointer' : 'default',
                transition: 'all 0.2s ease-in-out',
                '&:hover': onHechoClick ? {
                  backgroundColor: 'grey.50',
                  borderColor: relationColor,
                  transform: 'translateX(4px)'
                } : {}
              }}
              onClick={() => onHechoClick?.(hecho)}
            >
              <Box sx={{ mb: 1.5 }}>
                <Stack 
                  direction="row" 
                  spacing={1} 
                  alignItems="center"
                  sx={{ mb: 1 }}
                >
                  <Chip
                    icon={getRelationIcon(relationType)}
                    label={getRelationLabel(relationType)}
                    size="small"
                    sx={{
                      backgroundColor: relationColor,
                      color: 'white',
                      fontWeight: 600,
                      '& .MuiChip-icon': {
                        color: 'white'
                      }
                    }}
                  />
                  {relationStrength >= 7 && (
                    <Chip
                      label="Fuerte"
                      size="small"
                      variant="outlined"
                      sx={{
                        borderColor: relationColor,
                        color: relationColor,
                        fontWeight: 600
                      }}
                    />
                  )}
                  <Typography 
                    variant="caption" 
                    sx={{ 
                      ml: 'auto !important',
                      color: 'text.secondary' 
                    }}
                  >
                    {new Date(hecho.fechaOcurrencia).toLocaleDateString('es-ES', {
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric'
                    })}
                  </Typography>
                </Stack>
              </Box>

              <Typography 
                variant="body2" 
                sx={{ 
                  mb: 1.5,
                  fontWeight: 500,
                  lineHeight: 1.5
                }}
              >
                {hecho.contenido}
              </Typography>

              <Stack 
                direction="row" 
                spacing={1} 
                alignItems="center"
                sx={{ flexWrap: 'wrap', gap: 0.5 }}
              >
                <Typography 
                  variant="caption" 
                  sx={{ color: 'text.secondary' }}
                >
                  {hecho.articuloMetadata.medio}
                </Typography>
                {hecho.importancia >= 7 && (
                  <>
                    <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                      •
                    </Typography>
                    <Typography 
                      variant="caption" 
                      sx={{ 
                        color: 'warning.main',
                        fontWeight: 600 
                      }}
                    >
                      Alta importancia ({hecho.importancia}/10)
                    </Typography>
                  </>
                )}
              </Stack>
            </Paper>
          );
        })}
      </Stack>
    </Box>
  );
});