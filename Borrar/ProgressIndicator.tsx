import React from 'react';
import { 
  Box, 
  Typography, 
  LinearProgress, 
  Stepper, 
  Step, 
  StepLabel, 
  StepIcon
} from '@mui/material';
import { 
  Info as InfoIcon,
  Settings as SettingsIcon,
  Analytics as AnalyticsIcon,
  CheckCircle as CheckIcon
} from '@mui/icons-material';

interface ProgressIndicatorProps {
  currentStep: number;
  totalSteps: number;
  steps?: Array<{
    label: string;
    description: string;
    icon?: React.ReactNode;
  }>;
  showProgress?: boolean;
  orientation?: 'horizontal' | 'vertical';
}

const defaultSteps = [
  {
    label: 'Información Básica',
    description: 'Configurar sitio y medio',
    icon: <InfoIcon />
  },
  {
    label: 'Sección y URLs',
    description: 'Especificar contenido',
    icon: <SettingsIcon />
  },
  {
    label: 'Análisis',
    description: 'Detectar estructura',
    icon: <AnalyticsIcon />
  },
  {
    label: 'Configuración',
    description: 'Ajustes finales',
    icon: <CheckIcon />
  }
];

const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({
  currentStep,
  totalSteps,
  steps = defaultSteps,
  showProgress = true,
  orientation = 'horizontal'
}) => {
  const progressPercentage = ((currentStep - 1) / (totalSteps - 1)) * 100;

  const CustomStepIcon = (props: any) => {
    const { active, completed, icon } = props;
    const stepData = steps[icon - 1];
    
    if (completed) {
      return <CheckIcon sx={{ color: 'success.main' }} />;
    }
    
    if (active) {
      return React.cloneElement(stepData?.icon || <InfoIcon />, {
        sx: { color: 'primary.main' }
      });
    }
    
    return React.cloneElement(stepData?.icon || <InfoIcon />, {
      sx: { color: 'text.disabled' }
    });
  };

  return (
    <Box sx={{ width: '100%', mb: 3 }}>
      {/* Barra de progreso */}
      {showProgress && (
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Paso {currentStep} de {totalSteps}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {Math.round(progressPercentage)}%
            </Typography>
          </Box>
          <LinearProgress 
            variant="determinate" 
            value={progressPercentage}
            sx={{ height: 6, borderRadius: 3 }}
          />
        </Box>
      )}

      {/* Stepper */}
      <Stepper 
        activeStep={currentStep - 1} 
        orientation={orientation}
        sx={{ 
          '& .MuiStepLabel-root': {
            cursor: 'default'
          }
        }}
      >
        {steps.slice(0, totalSteps).map((step, index) => (
          <Step key={step.label}>
            <StepLabel 
              StepIconComponent={CustomStepIcon}
              optional={
                orientation === 'vertical' ? (
                  <Typography variant="caption" color="text.secondary">
                    {step.description}
                  </Typography>
                ) : undefined
              }
            >
              <Typography 
                variant="body2" 
                sx={{ 
                  fontWeight: index === currentStep - 1 ? 600 : 400,
                  color: index < currentStep ? 'success.main' : 
                         index === currentStep - 1 ? 'primary.main' : 'text.disabled'
                }}
              >
                {step.label}
              </Typography>
              {orientation === 'horizontal' && (
                <Typography variant="caption" color="text.secondary" display="block">
                  {step.description}
                </Typography>
              )}
            </StepLabel>
          </Step>
        ))}
      </Stepper>

      {/* Información del paso actual */}
      <Box sx={{ mt: 2, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          {steps[currentStep - 1]?.description || `Completando paso ${currentStep}`}
        </Typography>
      </Box>
    </Box>
  );
};

export default ProgressIndicator;