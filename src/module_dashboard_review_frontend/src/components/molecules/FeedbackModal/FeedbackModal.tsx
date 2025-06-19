import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControlLabel,
  Checkbox,
  Slider,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Divider,
  FormControl,
  FormLabel,
  RadioGroup,
  Radio,
  Paper,
  Stack
} from '@mui/material';
import {
  Feedback as FeedbackIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import type { Hecho, Feedback, FeedbackType } from '@/types/domain';

interface FeedbackModalProps {
  hecho: Hecho;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (updatedHecho: Partial<Hecho>) => void;
  isSubmitting?: boolean;
  onSubmitFeedback?: (feedback: Feedback) => Promise<boolean>;
}

const EVALUACION_OPTIONS = [
  { value: 'verdadero', label: 'Verificado como verdadero', icon: CheckIcon, color: 'success' },
  { value: 'falso', label: 'Marcado como falso', icon: WarningIcon, color: 'error' },
  { value: 'necesita_verificacion', label: 'Necesita verificación adicional', icon: InfoIcon, color: 'warning' }
] as const;

export const FeedbackModal: React.FC<FeedbackModalProps> = ({
  hecho,
  isOpen,
  onClose,
  onSuccess,
  isSubmitting = false,
  onSubmitFeedback
}) => {
  const [feedbackType, setFeedbackType] = useState<FeedbackType>('GENERAL');
  const [evaluacion, setEvaluacion] = useState<string>(
    hecho.evaluacionEditorial || ''
  );
  const [importance, setImportance] = useState<number>(hecho.importancia);
  const [comment, setComment] = useState<string>(hecho.comentarios || '');
  const [error, setError] = useState<string | null>(null);
  const [hasChanges, setHasChanges] = useState(false);

  // Reset form cuando se abre el modal
  useEffect(() => {
    if (isOpen) {
      setEvaluacion(hecho.evaluacionEditorial || '');
      setImportance(hecho.importancia);
      setComment(hecho.comentarios || '');
      setError(null);
      setHasChanges(false);
      setFeedbackType('GENERAL');
    }
  }, [isOpen, hecho]);

  // Detectar cambios en el formulario
  useEffect(() => {
    const hasEvaluacionChange = evaluacion !== (hecho.evaluacionEditorial || '');
    const hasImportanceChange = importance !== hecho.importancia;
    const hasCommentChange = comment !== (hecho.comentarios || '');
    
    setHasChanges(hasEvaluacionChange || hasImportanceChange || hasCommentChange);
  }, [evaluacion, importance, comment, hecho]);

  const handleSubmit = async () => {
    if (!hasChanges) {
      onClose();
      return;
    }

    setError(null);

    try {
      let feedbackTypeToSubmit: FeedbackType = 'GENERAL';
      
      if (evaluacion && evaluacion !== hecho.evaluacionEditorial) {
        feedbackTypeToSubmit = 'FACTUAL_ERROR';
      } else if (importance !== hecho.importancia) {
        feedbackTypeToSubmit = 'IMPORTANCE';
      }

      const feedback: Feedback = {
        hechoId: hecho.id,
        type: feedbackTypeToSubmit,
        isFalse: evaluacion === 'falso',
        importance,
        comment: comment.trim() || undefined
      };

      let success = false;
      
      if (onSubmitFeedback) {
        success = await onSubmitFeedback(feedback);
      } else {
        // Fallback: simular éxito después de un delay
        await new Promise(resolve => setTimeout(resolve, 800));
        success = true;
      }

      if (success) {
        // Crear objeto con los cambios para actualizar el hecho
        const updatedFields: Partial<Hecho> = {
          importancia: importance,
          comentarios: comment.trim() || undefined,
          fechaEvaluacion: new Date().toISOString(),
          evaluadoPor: 'Editor Actual' // En producción vendría del contexto de usuario
        };

        if (evaluacion) {
          updatedFields.evaluacionEditorial = evaluacion as any;
        }

        onSuccess(updatedFields);
        onClose();
      }
    } catch (err) {
      console.error('Error submitting feedback:', err);
      setError('Error al enviar el feedback. Por favor, intente nuevamente.');
    }
  };

  const handleClose = () => {
    if (hasChanges && !isSubmitting) {
      // Aquí podríamos mostrar una confirmación de pérdida de cambios
      // Por simplicidad, cerramos directamente
    }
    onClose();
  };

  const getSelectedEvaluacionOption = () => {
    return EVALUACION_OPTIONS.find(option => option.value === evaluacion);
  };

  return (
    <Dialog 
      open={isOpen} 
      onClose={handleClose}
      maxWidth="md" 
      fullWidth
      PaperProps={{
        sx: { minHeight: '500px' }
      }}
    >
      <DialogTitle sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: 1,
        pb: 1
      }}>
        <FeedbackIcon color="primary" />
        Evaluación Editorial
      </DialogTitle>
      
      <DialogContent>
        {/* Información del hecho */}
        <Paper 
          elevation={0} 
          sx={{ 
            p: 2, 
            mb: 3, 
            bgcolor: 'grey.50',
            border: 1,
            borderColor: 'divider'
          }}
        >
          <Typography variant="caption" color="text.secondary" gutterBottom>
            Hecho a evaluar:
          </Typography>
          <Typography variant="body2" sx={{ 
            fontStyle: 'italic',
            lineHeight: 1.5,
            maxHeight: '60px',
            overflow: 'hidden',
            textOverflow: 'ellipsis'
          }}>
            {hecho.contenido}
          </Typography>
          <Typography variant="caption" color="primary.main" sx={{ mt: 1, display: 'block' }}>
            {hecho.articuloMetadata.medio} • {new Date(hecho.articuloMetadata.fechaPublicacion).toLocaleDateString()}
          </Typography>
        </Paper>

        <Stack spacing={3}>
          {/* Evaluación Editorial */}
          <FormControl component="fieldset">
            <FormLabel component="legend" sx={{ mb: 2 }}>
              <Typography variant="subtitle2">
                Evaluación Editorial
              </Typography>
            </FormLabel>
            <RadioGroup
              value={evaluacion}
              onChange={(e) => setEvaluacion(e.target.value)}
            >
              {EVALUACION_OPTIONS.map((option) => {
                const IconComponent = option.icon;
                return (
                  <FormControlLabel
                    key={option.value}
                    value={option.value}
                    control={<Radio />}
                    label={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <IconComponent 
                          fontSize="small" 
                          color={option.color as any}
                        />
                        {option.label}
                      </Box>
                    }
                    sx={{ mb: 1 }}
                  />
                );
              })}
              <FormControlLabel
                value=""
                control={<Radio />}
                label="Sin evaluación"
                sx={{ mb: 1 }}
              />
            </RadioGroup>
          </FormControl>

          <Divider />

          {/* Slider de Importancia */}
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Nivel de Importancia: {importance}/10
            </Typography>
            <Slider
              value={importance}
              onChange={(_, newValue) => setImportance(newValue as number)}
              min={1}
              max={10}
              step={1}
              marks={[
                { value: 1, label: '1' },
                { value: 5, label: '5' },
                { value: 10, label: '10' }
              ]}
              valueLabelDisplay="auto"
              disabled={isSubmitting}
              sx={{ mt: 2, mb: 1 }}
            />
            <Typography variant="caption" color="text.secondary">
              1 = Baja importancia • 5 = Importancia media • 10 = Muy importante
            </Typography>
          </Box>

          <Divider />

          {/* Comentarios */}
          <TextField
            label="Comentarios adicionales"
            multiline
            rows={4}
            fullWidth
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Agregue observaciones, contexto adicional o justificación para la evaluación..."
            disabled={isSubmitting}
            helperText={`${comment.length}/500 caracteres`}
            inputProps={{ maxLength: 500 }}
          />
        </Stack>

        {/* Error Display */}
        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}

        {/* Cambios detectados */}
        {hasChanges && (
          <Alert severity="info" sx={{ mt: 2 }}>
            Se han detectado cambios en la evaluación.
          </Alert>
        )}
      </DialogContent>
      
      <DialogActions sx={{ p: 3, pt: 1 }}>
        <Button 
          onClick={handleClose} 
          disabled={isSubmitting}
          color="inherit"
        >
          Cancelar
        </Button>
        <Button 
          onClick={handleSubmit} 
          variant="contained"
          disabled={isSubmitting || !hasChanges}
          startIcon={isSubmitting ? <CircularProgress size={20} /> : null}
        >
          {isSubmitting ? 'Enviando...' : 
           hasChanges ? 'Guardar Evaluación' : 'Sin cambios'
          }
        </Button>
      </DialogActions>
    </Dialog>
  );
};
