import React from 'react';
import { TextField, TextFieldProps } from '@mui/material';

export interface InputProps extends Omit<TextFieldProps, 'variant'> {
  label: string;
}

/**
 * Atomic Input component
 * Basic reusable input field based on Material UI TextField
 */
export const Input: React.FC<InputProps> = ({ label, ...props }) => {
  return (
    <TextField
      variant="outlined"
      label={label}
      {...props}
    />
  );
};
