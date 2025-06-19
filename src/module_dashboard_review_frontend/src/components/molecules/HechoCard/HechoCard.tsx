import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Stack
} from '@mui/material';
import type { Hecho } from '@/types/domain';
import { HechoDetailModal } from '@/components/molecules/HechoDetailModal';

interface HechoCardProps {
  hecho: Hecho;
  onImportanceChange?: (hechoId: number, newImportance: number) => void;
  onMarkAsFalse?: (hechoId: number) => void;
  onFeedbackSubmitted?: () => void;
  isImportanceLoading?: (hechoId: number) => boolean;
}

export const HechoCard: React.FC<HechoCardProps> = ({
  hecho,
  onImportanceChange,
  onMarkAsFalse,
  onFeedbackSubmitted = () => {},
  isImportanceLoading
}) => {
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);

  const handleCardClick = () => {
    setIsDetailModalOpen(true);
  };

  const handleSourceClick = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevenir que se abra el modal
    window.open(hecho.articuloMetadata.url, '_blank', 'noopener,noreferrer');
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
          borderColor: '#E5E7EB',
          backgroundColor: '#FFFFFF',
          cursor: 'pointer',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            borderColor: '#005A99',
            transform: 'translateY(-1px)',
            boxShadow: '0 4px 12px rgba(0, 90, 153, 0.15)'
          }
        }} 
        onClick={handleCardClick}
        data-testid="hecho-card"
      >
        <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
          {/* PAÍS - PRESIDIENDO TODO EL BLOQUE */}
          <Box sx={{ mb: 2 }}>
            {/* Mostrar país(es) - manejar tanto string como array */}
            {hecho.pais && (
              Array.isArray(hecho.pais) ? (
                <Stack direction="row" spacing={0.5} sx={{ flexWrap: 'wrap', gap: 0.5 }}>
                  {hecho.pais.map((pais, index) => (
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
                  label={hecho.pais}
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

          {/* HECHO - MÁXIMA IMPORTANCIA */}
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
            {hecho.contenido}
          </Typography>

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
              {hecho.articuloMetadata.titular}
            </Typography>
            
            <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
              <Chip 
                label={hecho.articuloMetadata.medio}
                color="primary"
                size="small"
                sx={{ fontWeight: 600 }}
              />
              <Chip 
                label={new Date(hecho.articuloMetadata.fechaPublicacion).toLocaleDateString('es-ES', {
                  year: 'numeric',
                  month: 'short', 
                  day: 'numeric'
                })}
                variant="outlined"
                size="small"
              />
              {hecho.articuloMetadata.autor && (
                <Chip 
                  label={hecho.articuloMetadata.autor}
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
                label={new Date(hecho.fechaOcurrencia).toLocaleDateString('es-ES', {
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
                label={hecho.tipoHecho} 
                size="small" 
                variant="outlined"
                sx={{ 
                  borderColor: 'divider',
                  color: 'text.secondary'
                }}
              />
            </Stack>

            <Chip
              label={getEvaluationLabel(hecho.evaluacionEditorial)}
              color={getEvaluationColor(hecho.evaluacionEditorial) as any}
              size="small"
              sx={{ fontWeight: 600 }}
            />
          </Box>

          {/* INDICADOR DE IMPORTANCIA */}
          <Box sx={{ textAlign: 'right' }}>
            <Typography variant="caption" color="text.secondary">
              Importancia: <strong>{hecho.importancia}/10</strong>
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* Modal de Detalle */}
      <HechoDetailModal
        hecho={hecho}
        isOpen={isDetailModalOpen}
        onClose={() => setIsDetailModalOpen(false)}
        onImportanceChange={onImportanceChange}
        onMarkAsFalse={onMarkAsFalse}
        isImportanceLoading={isImportanceLoading ? isImportanceLoading(hecho.id) : false}
      />
    </>
  );
};
