import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  Box,
  Button,
  Chip,
  Stack,
  Slider,
  Divider,
  IconButton
} from '@mui/material';
import {
  Close as CloseIcon,
  OpenInNew as OpenInNewIcon,
  Warning as WarningIcon
} from '@mui/icons-material';
import type { Hecho } from '@/types/domain';
import { ConfirmationDialog } from '@/components/molecules/ConfirmationDialog';
import type { ConfirmationDialogState } from '@/types/domain';

interface HechoDetailModalProps {
  hecho: Hecho | null;
  isOpen: boolean;
  onClose: () => void;
  onImportanceChange?: (hechoId: number, newImportance: number) => void;
  onMarkAsFalse?: (hechoId: number) => void;
  isImportanceLoading?: boolean;
}

export const HechoDetailModal: React.FC<HechoDetailModalProps> = ({
  hecho,
  isOpen,
  onClose,
  onImportanceChange,
  onMarkAsFalse,
  isImportanceLoading = false
}) => {
  const [confirmationState, setConfirmationState] = useState<ConfirmationDialogState>({
    isOpen: false,
    title: '',
    message: '',
    confirmText: '',
    cancelText: '',
    severity: 'info'
  });

  if (!hecho) return null;

  const showConfirmation = (
    title: string,
    message: string,
    confirmText: string,
    cancelText: string,
    severity: 'info' | 'warning' | 'error' | 'success',
    action: () => void
  ) => {
    setConfirmationState({
      isOpen: true,
      title,
      message,
      confirmText,
      cancelText,
      severity,
      action
    });
  };

  const handleConfirmationConfirm = () => {
    if (confirmationState.action) {
      confirmationState.action();
    }
    setConfirmationState(prev => ({ ...prev, isOpen: false }));
  };

  const handleConfirmationCancel = () => {
    setConfirmationState(prev => ({ ...prev, isOpen: false }));
  };

  const handleImportanceChange = (_: Event, newValue: number | number[]) => {
    const importance = newValue as number;
    
    if (importance !== hecho.importancia && onImportanceChange) {
      showConfirmation(
        'Cambiar importancia',
        `¿Estás seguro de que quieres cambiar la importancia de ${hecho.importancia} a ${importance}?`,
        'Confirmar',
        'Cancelar',
        'warning',
        () => onImportanceChange(hecho.id, importance)
      );
    }
  };

  const handleMarkAsFalse = () => {
    if (onMarkAsFalse) {
      showConfirmation(
        'Marcar como falso',
        '¿Estás seguro de que quieres marcar este hecho como falso? Esta acción quedará registrada en el historial editorial.',
        'Marcar como Falso',
        'Cancelar',
        'error',
        () => onMarkAsFalse(hecho.id)
      );
    }
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
      <Dialog
        open={isOpen}
        onClose={onClose}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 3,
            maxHeight: '90vh'
          }
        }}
      >
        <DialogTitle sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'flex-start',
          pb: 2
        }}>
          <Box>
            <Typography variant="h5" component="h2" sx={{ mb: 1, fontWeight: 700 }}>
              Detalle del Hecho Noticioso
            </Typography>
            {/* Mostrar todos los países */}
            {hecho.pais && (
              <Stack direction="row" spacing={0.5} sx={{ flexWrap: 'wrap', gap: 0.5 }}>
                {/* Manejar tanto string como array */}
                {Array.isArray(hecho.pais) ? (
                  hecho.pais.map((pais, index) => (
                    <Chip 
                      key={index}
                      label={pais}
                      color="primary"
                      size="small"
                      sx={{
                        fontWeight: 600,
                        textTransform: 'uppercase'
                      }}
                    />
                  ))
                ) : (
                  <Chip 
                    label={hecho.pais}
                    color="primary"
                    size="small"
                    sx={{
                      fontWeight: 600,
                      textTransform: 'uppercase'
                    }}
                  />
                )}
              </Stack>
            )}
          </Box>
          <IconButton 
            onClick={onClose}
            size="small"
            aria-label="Cerrar modal"
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>

        <DialogContent sx={{ pb: 3 }}>
          <Typography 
            variant="h4"
            component="h3"
            sx={{ 
              mb: 4,
              lineHeight: 1.4,
              fontWeight: 700,
              color: 'text.primary'
            }}
          >
            {hecho.contenido}
          </Typography>

          <Box sx={{ 
            mb: 4,
            p: 3,
            border: '2px solid',
            borderColor: 'primary.main',
            borderRadius: 2,
            bgcolor: 'grey.50'
          }}>
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
              📰 Fuente Original
            </Typography>
            
            <Typography 
              variant="h6"
              sx={{ 
                mb: 2,
                lineHeight: 1.4,
                fontWeight: 600
              }}
            >
              {hecho.articuloMetadata.titular}
            </Typography>
            
            <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1, mb: 3 }}>
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
              {hecho.articuloMetadata.paisPublicacion && (
                <Chip 
                  label={`📍 ${hecho.articuloMetadata.paisPublicacion}`}
                  variant="outlined"
                  size="small"
                />
              )}
              {hecho.articuloMetadata.autor && (
                <Chip 
                  label={hecho.articuloMetadata.autor}
                  variant="outlined"
                  size="small"
                />
              )}
            </Stack>

            {/* Resumen del artículo si está disponible */}
            {hecho.articuloMetadata.resumen && (
              <Box sx={{ mb: 3, p: 2, bgcolor: 'background.paper', borderRadius: 1, border: 1, borderColor: 'divider' }}>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1, fontWeight: 600 }}>
                  📄 Resumen del artículo:
                </Typography>
                <Typography variant="body2" sx={{ fontStyle: 'italic', lineHeight: 1.5 }}>
                  {hecho.articuloMetadata.resumen}
                </Typography>
              </Box>
            )}
            
            <Button
              href={hecho.articuloMetadata.url}
              target="_blank"
              rel="noopener noreferrer"
              variant="contained"
              startIcon={<OpenInNewIcon />}
              sx={{ fontWeight: 600 }}
            >
              Abrir Artículo Original
            </Button>
          </Box>

          <Box sx={{ mb: 4 }}>
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
              Información Adicional
            </Typography>
            
            <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1, mb: 2 }}>
              <Chip 
                label={`Fecha: ${new Date(hecho.fechaOcurrencia).toLocaleDateString('es-ES', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                })}`} 
                variant="outlined"
                sx={{ borderColor: 'divider', color: 'text.secondary' }}
              />
              <Chip 
                label={`Tipo: ${hecho.tipoHecho}`}
                variant="outlined"
                sx={{ borderColor: 'divider', color: 'text.secondary' }}
              />
            </Stack>

            <Chip
              label={getEvaluationLabel(hecho.evaluacionEditorial)}
              color={getEvaluationColor(hecho.evaluacionEditorial) as any}
              sx={{ fontWeight: 600 }}
            />
          </Box>

          {/* Etiquetas y Categorías */}
          {((hecho.etiquetas && hecho.etiquetas.length > 0) || (hecho.articuloMetadata.categoriasAsignadas && hecho.articuloMetadata.categoriasAsignadas.length > 0)) && (
            <>
              <Box sx={{ mb: 4 }}>
                <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                  Clasificación y Etiquetas
                </Typography>
                
                {/* Etiquetas */}
                {hecho.etiquetas && hecho.etiquetas.length > 0 && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" sx={{ mb: 1, color: 'text.secondary' }}>
                      🏷️ Etiquetas:
                    </Typography>
                    <Stack direction="row" spacing={0.5} sx={{ flexWrap: 'wrap', gap: 0.5 }}>
                      {hecho.etiquetas.map((etiqueta, index) => (
                        <Chip 
                          key={index}
                          label={etiqueta}
                          variant="outlined"
                          size="small"
                          color="secondary"
                        />
                      ))}
                    </Stack>
                  </Box>
                )}
                
                {/* Categorías Asignadas por IA */}
                {hecho.articuloMetadata.categoriasAsignadas && hecho.articuloMetadata.categoriasAsignadas.length > 0 && (
                  <Box>
                    <Typography variant="subtitle2" sx={{ mb: 1, color: 'text.secondary' }}>
                      🤖 Categorías IA:
                    </Typography>
                    <Stack direction="row" spacing={0.5} sx={{ flexWrap: 'wrap', gap: 0.5 }}>
                      {hecho.articuloMetadata.categoriasAsignadas.map((categoria, index) => (
                        <Chip 
                          key={index}
                          label={categoria}
                          variant="outlined"
                          size="small"
                          color="info"
                        />
                      ))}
                    </Stack>
                  </Box>
                )}
              </Box>
            </>
          )}

          {/* Estadísticas de Credibilidad */}
          {(hecho.frecuenciaCitacion !== undefined || hecho.totalMenciones !== undefined || hecho.mencionesConfirmatorias !== undefined || hecho.consensoFuentes) && (
            <>
              <Box sx={{ mb: 4 }}>
                <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                  📊 Estadísticas de Credibilidad
                </Typography>
                
                <Box sx={{ 
                  p: 2, 
                  bgcolor: 'grey.50', 
                  borderRadius: 2, 
                  border: 1, 
                  borderColor: 'divider' 
                }}>
                  <Stack spacing={2}>
                    {hecho.totalMenciones !== undefined && (
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="body2" color="text.secondary">
                          📰 Total de menciones:
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          {hecho.totalMenciones}
                        </Typography>
                      </Box>
                    )}
                    
                    {hecho.mencionesConfirmatorias !== undefined && (
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="body2" color="text.secondary">
                          ✅ Menciones confirmatorias:
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 600, color: 'success.main' }}>
                          {hecho.mencionesConfirmatorias}
                        </Typography>
                      </Box>
                    )}
                    
                    {hecho.frecuenciaCitacion !== undefined && (
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="body2" color="text.secondary">
                          🔗 Frecuencia de citación:
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          {hecho.frecuenciaCitacion}
                        </Typography>
                      </Box>
                    )}
                    
                    {hecho.consensoFuentes && (
                      <Box>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                          🎯 Consenso entre fuentes:
                        </Typography>
                        <Chip 
                          label={hecho.consensoFuentes.replace(/_/g, ' ').toLowerCase().replace(/^\w/, c => c.toUpperCase())}
                          color={hecho.consensoFuentes.includes('confirmado') ? 'success' : hecho.consensoFuentes.includes('disputa') ? 'error' : 'warning'}
                          size="small"
                          sx={{ fontWeight: 600 }}
                        />
                      </Box>
                    )}
                  </Stack>
                </Box>
              </Box>
            </>
          )}

          <Divider sx={{ my: 3 }} />

          <Box>
            <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
              Evaluación Editorial
            </Typography>

            <Box sx={{ mb: 4 }}>
              <Typography 
                variant="body2" 
                component="label"
                htmlFor={`modal-importance-slider-${hecho.id}`}
                sx={{ 
                  display: 'block',
                  mb: 2,
                  fontWeight: 600,
                  color: 'text.primary'
                }}
              >
                Importancia Editorial (1-10): <strong>{hecho.importancia}</strong>
              </Typography>
              <Slider
                id={`modal-importance-slider-${hecho.id}`}
                value={hecho.importancia}
                onChange={handleImportanceChange}
                min={1}
                max={10}
                step={1}
                marks
                valueLabelDisplay="auto"
                disabled={isImportanceLoading}
                aria-label="Importancia editorial del hecho noticioso"
              />
              {isImportanceLoading && (
                <Typography variant="caption" color="primary" sx={{ mt: 1, display: 'block' }}>
                  Actualizando importancia...
                </Typography>
              )}
            </Box>

            {hecho.comentarios && (
              <Box sx={{ 
                mb: 3,
                p: 2, 
                bgcolor: 'grey.50',
                borderRadius: 1,
                border: '1px solid',
                borderColor: 'divider'
              }}>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                  Comentario editorial:
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  {hecho.comentarios}
                </Typography>
                {hecho.evaluadoPor && (
                  <Typography variant="caption" color="text.secondary">
                    Por: {hecho.evaluadoPor} • {hecho.fechaEvaluacion && new Date(hecho.fechaEvaluacion).toLocaleString()}
                  </Typography>
                )}
              </Box>
            )}
          </Box>
        </DialogContent>

        <DialogActions sx={{ p: 3, pt: 0, justifyContent: 'space-between' }}>
          <Button
            variant="contained"
            color="secondary"
            startIcon={<WarningIcon />}
            onClick={handleMarkAsFalse}
            disabled={hecho.evaluacionEditorial === 'falso'}
            sx={{ fontWeight: 600 }}
          >
            {hecho.evaluacionEditorial === 'falso' ? '✓ Marcado como Falso' : '⚠️ Marcar como Falso'}
          </Button>
          
          <Button
            onClick={onClose}
            variant="outlined"
            sx={{ fontWeight: 600 }}
          >
            Cerrar
          </Button>
        </DialogActions>
      </Dialog>

      <ConfirmationDialog
        isOpen={confirmationState.isOpen}
        title={confirmationState.title}
        message={confirmationState.message}
        confirmText={confirmationState.confirmText}
        cancelText={confirmationState.cancelText}
        severity={confirmationState.severity}
        onConfirm={handleConfirmationConfirm}
        onCancel={handleConfirmationCancel}
      />
    </>
  );
};
