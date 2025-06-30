import React from 'react';
import { Tooltip, IconButton } from '@mui/material';
import { Help as HelpIcon } from '@mui/icons-material';

interface HelpTooltipProps {
  title: string;
  children?: React.ReactNode;
  placement?: 'top' | 'bottom' | 'left' | 'right';
  className?: string;
}

const HelpTooltip: React.FC<HelpTooltipProps> = ({ 
  title, 
  children, 
  placement = 'top',
  className 
}) => {
  const trigger = children || (
    <IconButton size="small" className={className}>
      <HelpIcon fontSize="small" />
    </IconButton>
  );

  return (
    <Tooltip title={title} placement={placement}>
      {React.isValidElement(trigger) ? trigger : <span>{trigger}</span>}
    </Tooltip>
  );
};

export default HelpTooltip;