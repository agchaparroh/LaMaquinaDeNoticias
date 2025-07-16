import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Stack,
  Collapse,
  IconButton,
  Badge,
  Divider
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Timeline as TimelineIcon
} from '@mui/icons-material';
import type { HechoCluster } from '@/utils/clustering';
import { HechoDetailModal } from '@/components/molecules/HechoDetailModal';
import { Timeline } from '@/components/organisms/Timeline';

interface ClusterCardProps {
  cluster: HechoCluster;
  onImportanceChange?: (hechoId: number, newImportance: number) => void;
  onMarkAsFalse?: (hechoId: number) => void;
  onFeedbackSubmitted?: () => void;
  isImportanceLoading?: (hechoId: number) => boolean;
}

export const ClusterCard: React.FC<ClusterCardProps> = ({
  cluster,
  onImportanceChange,
  onMarkAsFalse,
  onFeedbackSubmitted = () => {},
  isImportanceLoading
}) => {
  const [isTimelineExpanded, setIsTimelineExpanded] = useState(false);
  const [selectedHecho, setSelectedHecho] = useState<any>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);

  const { protagonista, hechos } = cluster;
  const related = hechos.filter(h => h.id !== protagonista.id);
  const hasRelated = related.length > 0;

  const handleProtagonistClick = () => {
    setSelectedHecho(protagonista);
    setIsDetailModalOpen(true);
  };

  const handleSourceClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    window.open(protagonista.articuloMetadata.url, '_blank', 'noopener,noreferrer');
  };

  const toggleTimeline = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsTimelineExpanded(!isTimelineExpanded);
  };

  const getEvaluationColor = (evaluacion: string | null | undefined) => {
    switch (evaluacion) {
      case 'verdadero': return 'success';
      case 'falso': return 'error';
      case 'necesita_verificacion': return 'warning';
      default: return 'default';
    }
  };

  const getEvaluationLabel = (evaluacion: string | null | undefined) => {
    switch (evaluacion) {
      case 'verdadero': return 'Verificado';
      case 'falso': return 'Falso';
      case 'necesita_verificacion': return 'Necesita Verificación';
      default: return 'Sin Evaluar';
    }
  };

  return (
    <>
      <Card 
        sx={{ 
          mb: 3,
          border: '1px solid',
          borderColor: hasRelated ? '#005A99' : '#E5E7EB',
          borderWidth: hasRelated ? 2 : 1,
          backgroundColor: '#FFFFFF',
          position: 'relative',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            borderColor: '#005A99',
            transform: 'translateY(-1px)',
            boxShadow: '0 4px 12px rgba(0, 90, 153, 0.15)'
          }
        }} 
        data-testid="cluster-card"
        data-importance={protagonista.importancia}
      >
        <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
          {/* INDICADOR DE CLUSTER */}
          {hasRelated && (
            <Box sx={{ position: 'absolute', top: 16, right: 16 }}>
              <Badge 
                badgeContent={related.length} 
                color="primary"
                sx={{
                  '& .MuiBadge-badge': {
                    backgroundColor: '#005A99',
                    color: 'white',
                    fontWeight: 700
                  }
                }}
              >
                <TimelineIcon sx={{ color: '#005A99' }} />
              </Badge>
            </Box>
          )}

          {/* PAÍS - PRESIDIENDO TODO EL BLOQUE */}
          <Box sx={{ mb: 2 }}>
            {protagonista.pais && (
              Array.isArray(protagonista.pais) ? (
                <Stack direction="row" spacing={0.5} sx={{ flexWrap: 'wrap', gap: 0.5 }}>
                  {protagonista.pais.map((pais: string, index: number) => (
                    <Chip 
                      key={index}
                      label={pais}
                      color="primary"
                      sx={{
                        fontWeight: 600,
                        fontSize: { xs: '0.75rem', sm: '0.8rem' },
                        height: { xs: 28, sm: 32 },
                        letterSpacing: '0.25px',
                        textTransform: 'uppercase'
                      }}
                    />
                  ))}
                </Stack>
              ) : (
                <Chip 
                  label={protagonista.pais}
                  color="primary"
                  sx={{
                    fontWeight: 600,
                    fontSize: { xs: '0.75rem', sm: '0.8rem' },
                    height: { xs: 28, sm: 32 },
                    letterSpacing: '0.25px',
                    textTransform: 'uppercase'
                  }}
                />
              )
            )}
          </Box>

          {/* HECHO PROTAGONISTA */}
          <Box onClick={handleProtagonistClick} sx={{ cursor: 'pointer' }}>
            <Typography 
              variant="h4"
              component="h2"
              sx={{ 
                mb: 3,
                fontSize: { xs: '1.25rem', sm: '1.5rem' },
                lineHeight: 1.3,
                fontWeight: 700,
                color: 'text.primary'
              }}
            >
              {protagonista.contenido}
            </Typography>
          </Box>

          {/* FUENTE ORIGINAL - CLICKEABLE SEPARADO */}
          <Box 
            onClick={handleSourceClick}
            sx={{ 
              mb: 3,
              p: { xs: 2, sm: 3 },
              border: '2px solid',
              borderColor: 'primary.main',
              borderRadius: 2,
              bgcolor: 'grey.50',
              cursor: 'pointer',
              transition: 'all 0.2s ease-in-out',
              '&:hover': {
                borderColor: 'primary.dark',
                transform: 'scale(1.02)',
                boxShadow: '0 4px 12px rgba(0, 90, 153, 0.2)'
              }
            }}
          >
            <Typography 
              variant="caption" 
              color="primary.main"
              sx={{ 
                fontWeight: 600,
                letterSpacing: '0.5px',
                textTransform: 'uppercase',
                display: 'block',
                mb: 1.5
              }}
            >
              📰 Fuente Original (Click para abrir)
            </Typography>
            
            <Typography 
              variant="h5"
              component="h3"
              sx={{ 
                mb: 2,
                fontSize: { xs: '1.1rem', sm: '1.25rem' },
                lineHeight: 1.4,
                fontWeight: 600,
                color: 'text.primary'
              }}
            >
              {protagonista.articuloMetadata.titular}
            </Typography>
            
            <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
              <Chip 
                label={protagonista.articuloMetadata.medio}
                color="primary"
                size="small"
                sx={{ fontWeight: 600 }}
              />
              <Chip 
                label={new Date(protagonista.articuloMetadata.fechaPublicacion).toLocaleDateString('es-ES', {
                  year: 'numeric',
                  month: 'short', 
                  day: 'numeric'
                })}
                variant="outlined"
                size="small"
              />
              {protagonista.articuloMetadata.autor && (
                <Chip 
                  label={protagonista.articuloMetadata.autor}
                  variant="outlined"
                  size="small"
                />
              )}
            </Stack>
          </Box>

          {/* METADATA SIMPLIFICADA */}
          <Box sx={{ mb: 2 }}>
            <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1, mb: 2 }}>
              <Chip 
                label={new Date(protagonista.fechaOcurrencia).toLocaleDateString('es-ES', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                })} 
                size="small" 
                variant="outlined"
                sx={{ 
                  borderColor: 'divider',
                  color: 'text.secondary'
                }}
              />
              <Chip 
                label={protagonista.tipoHecho} 
                size="small" 
                variant="outlined"
                sx={{ 
                  borderColor: 'divider',
                  color: 'text.secondary'
                }}
              />
            </Stack>

            <Chip
              label={getEvaluationLabel(protagonista.evaluacionEditorial)}
              color={getEvaluationColor(protagonista.evaluacionEditorial) as any}
              size="small"
              sx={{ fontWeight: 600 }}
            />
          </Box>

          {/* INDICADOR DE IMPORTANCIA Y TIMELINE TOGGLE */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="caption" color="text.secondary">
              Importancia: <strong>{protagonista.importancia}/10</strong>
            </Typography>

            {hasRelated && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="caption" color="primary">
                  {related.length} hecho{related.length > 1 ? 's' : ''} relacionado{related.length > 1 ? 's' : ''}
                </Typography>
                <IconButton
                  onClick={toggleTimeline}
                  size="small"
                  sx={{ 
                    color: 'primary.main',
                    '&:hover': { backgroundColor: 'primary.light', color: 'white' }
                  }}
                >
                  {isTimelineExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                </IconButton>
              </Box>
            )}
          </Box>

          {/* TIMELINE EXPANDIBLE */}
          {hasRelated && (
            <Collapse in={isTimelineExpanded} timeout="auto" unmountOnExit>
              <Divider sx={{ my: 2 }} />
              <Timeline
                protagonist={protagonista}
                relatedHechos={related}
                onHechoClick={(hecho) => {
                  setSelectedHecho(hecho);
                  setIsDetailModalOpen(true);
                }}
              />
            </Collapse>
          )}
        </CardContent>
      </Card>

      {/* Modal de Detalle */}
      {selectedHecho && (
        <HechoDetailModal
          hecho={selectedHecho}
          isOpen={isDetailModalOpen}
          onClose={() => {
            setIsDetailModalOpen(false);
            setSelectedHecho(null);
          }}
          onImportanceChange={onImportanceChange}
          onMarkAsFalse={onMarkAsFalse}
          isImportanceLoading={isImportanceLoading ? isImportanceLoading(selectedHecho.id) : false}
        />
      )}
    </>
  );
};