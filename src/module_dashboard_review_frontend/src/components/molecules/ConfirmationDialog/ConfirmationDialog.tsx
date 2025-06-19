import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  Box,
  Alert
} from '@mui/material';
import {
  Warning as WarningIcon,
  Info as InfoIcon,
  Error as ErrorIcon,
  CheckCircle as SuccessIcon
} from '@mui/icons-material';
import type { ConfirmationDialogState } from '@/types/domain';

interface ConfirmationDialogProps extends Omit<ConfirmationDialogState, 'action'> {
  onConfirm: () => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export const ConfirmationDialog: React.FC<ConfirmationDialogProps> = ({
  isOpen,
  title,
  message,
  confirmText,
  cancelText,
  severity = 'info',
  onConfirm,
  onCancel,
  isLoading = false
}) => {
  const getSeverityIcon = () => {
    switch (severity) {
      case 'error':
        return <ErrorIcon color="error" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      case 'success':
        return <SuccessIcon color="success" />;
      default:
        return <InfoIcon color="info" />;
    }
  };

  const getSeverityColor = () => {
    switch (severity) {
      case 'error':
        return 'error';
      case 'warning':
        return 'warning';
      case 'success':
        return 'success';
      default:
        return 'primary';
    }
  };

  return (
    <Dialog 
      open={isOpen} 
      onClose={onCancel}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        elevation: 8
      }}
    >
      <DialogTitle sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: 1.5,
        pb: 1
      }}>
        {getSeverityIcon()}
        {title}
      </DialogTitle>
      
      <DialogContent>
        <DialogContentText sx={{ 
          color: 'text.primary',
          fontSize: '1rem',
          lineHeight: 1.6
        }}>
          {message}
        </DialogContentText>
        
        {severity === 'warning' && (
          <Alert severity="warning" sx={{ mt: 2 }}>
            Esta acción no se puede deshacer. Asegúrese de que desea continuar.
          </Alert>
        )}
        
        {severity === 'error' && (
          <Alert severity="error" sx={{ mt: 2 }}>
            ¡Atención! Esta es una acción crítica.
          </Alert>
        )}
      </DialogContent>
      
      <DialogActions sx={{ p: 3, pt: 1, gap: 1 }}>
        <Button 
          onClick={onCancel}
          disabled={isLoading}
          color="inherit"
          variant="outlined"
        >
          {cancelText}
        </Button>
        <Button 
          onClick={onConfirm}
          disabled={isLoading}
          color={getSeverityColor() as any}
          variant="contained"
          autoFocus
        >
          {isLoading ? 'Procesando...' : confirmText}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
