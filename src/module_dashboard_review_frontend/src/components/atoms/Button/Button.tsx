import React from 'react';
import { Button as MUIButton, ButtonProps as MUIButtonProps } from '@mui/material';

export interface ButtonProps extends MUIButtonProps {
  children: React.ReactNode;
}

/**
 * Atomic Button component
 * Basic reusable button based on Material UI
 */
export const Button: React.FC<ButtonProps> = ({ children, ...props }) => {
  return (
    <MUIButton {...props}>
      {children}
    </MUIButton>
  );
};
