import React from 'react';
import { Alert } from '@mui/material';
import { Timer as TimerIcon } from '@mui/icons-material';

interface TimeEstimateProps {
  strategy: string;
}

// Según SECCIÓN 15.2 - Indicadores de tiempo en generación
// Agregar a WizardPage.tsx y AnalysisStep.tsx:
const TimeEstimate: React.FC<TimeEstimateProps> = ({ strategy }) => {
  const getEstimate = () => {
    switch (strategy) {
      case 'rss': return '<5 segundos';
      case 'cache': return '<2 segundos';
      case 'first_time': return '~20 segundos';
      default: return 'Calculando...';
    }
  };
  
  return (
    <Alert severity="info" icon={<TimerIcon />}>
      Tiempo estimado: {getEstimate()}
    </Alert>
  );
};

export default TimeEstimate;