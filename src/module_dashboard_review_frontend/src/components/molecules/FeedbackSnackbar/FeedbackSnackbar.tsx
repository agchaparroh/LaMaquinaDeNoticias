import React, { useState, forwardRef, useImperativeHandle } from 'react';
import { Snackbar, Alert, AlertProps } from '@mui/material';

export interface FeedbackSnackbarRef {
  showSuccess: (message: string) => void;
  showError: (message: string) => void;
  showWarning: (message: string) => void;
  showInfo: (message: string) => void;
}

interface FeedbackSnackbarProps {
  autoHideDuration?: number;
  anchorOrigin?: {
    vertical: 'top' | 'bottom';
    horizontal: 'left' | 'center' | 'right';
  };
}

export const FeedbackSnackbar = forwardRef<FeedbackSnackbarRef, FeedbackSnackbarProps>(
  ({ autoHideDuration = 6000, anchorOrigin = { vertical: 'bottom', horizontal: 'center' } }, ref) => {
    const [open, setOpen] = useState(false);
    const [message, setMessage] = useState('');
    const [severity, setSeverity] = useState<AlertProps['severity']>('success');

    useImperativeHandle(ref, () => ({
      showSuccess: (message: string) => {
        setMessage(message);
        setSeverity('success');
        setOpen(true);
      },
      showError: (message: string) => {
        setMessage(message);
        setSeverity('error');
        setOpen(true);
      },
      showWarning: (message: string) => {
        setMessage(message);
        setSeverity('warning');
        setOpen(true);
      },
      showInfo: (message: string) => {
        setMessage(message);
        setSeverity('info');
        setOpen(true);
      },
    }));

    const handleClose = (event?: React.SyntheticEvent | Event, reason?: string) => {
      if (reason === 'clickaway') {
        return;
      }
      setOpen(false);
    };

    return (
      <Snackbar
        open={open}
        autoHideDuration={autoHideDuration}
        onClose={handleClose}
        anchorOrigin={anchorOrigin}
        data-testid="feedback-snackbar"
      >
        <Alert 
          onClose={handleClose} 
          severity={severity} 
          sx={{ 
            width: '100%',
            '& .MuiAlert-message': {
              fontSize: '0.95rem',
              fontWeight: 500,
            }
          }}
          variant="filled"
          data-testid="feedback-alert"
        >
          {message}
        </Alert>
      </Snackbar>
    );
  }
);

FeedbackSnackbar.displayName = 'FeedbackSnackbar';