import React from 'react';
import { Chip, Tooltip } from '@mui/material';
import { TrendingUp as TrendingUpIcon } from '@mui/icons-material';

interface PopularPatternBadgeProps {
  usageCount?: number;
}

// Según SECCIÓN 20.1 - Indicador de patrones populares
// Mostrar cuando se usa un patrón popular:
const PopularPatternBadge: React.FC<PopularPatternBadgeProps> = ({ usageCount }) => {
  if (!usageCount || usageCount < 10) return null;
  
  return (
    <Tooltip title="Este es un patrón popular pre-cargado en cache">
      <Chip
        label={`Usado ${usageCount} veces`}
        color="secondary"
        size="small"
        icon={<TrendingUpIcon />}
      />
    </Tooltip>
  );
};

export default PopularPatternBadge;