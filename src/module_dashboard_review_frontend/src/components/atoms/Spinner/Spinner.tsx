import React from 'react';
import { CircularProgress, CircularProgressProps, Box } from '@mui/material';

export interface SpinnerProps extends CircularProgressProps {
  size?: number;
  centered?: boolean;
}

/**
 * Atomic Spinner component
 * Loading indicator based on Material UI CircularProgress
 */
export const Spinner: React.FC<SpinnerProps> = ({ 
  size = 40, 
  centered = false, 
  ...props 
}) => {
  const spinner = <CircularProgress size={size} {...props} />;

  if (centered) {
    return (
      <Box 
        display="flex" 
        justifyContent="center" 
        alignItems="center" 
        width="100%" 
        height="100%"
      >
        {spinner}
      </Box>
    );
  }

  return spinner;
};
