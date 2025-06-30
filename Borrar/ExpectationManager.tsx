import React from 'react';
import { 
  Box, 
  Typography, 
  Alert,
  Chip,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Paper
} from '@mui/material';
import { 
  Timer as TimerIcon,
  TrendingUp as TrendingUpIcon,
  Info as InfoIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon
} from '@mui/icons-material';

interface ExpectationManagerProps {
  currentStep: number;
  totalSteps: number;
  estimatedTimeRemaining: string;
  expectedResults?: {
    articlesPerDay?: number;
    detectionStrategy?: string;
    reliabilityScore?: number;
  };
  warnings?: string[];
  tips?: string[];
}

const ExpectationManager: React.FC<ExpectationManagerProps> = ({
  currentStep,
  totalSteps,
  estimatedTimeRemaining,
  expectedResults,
  warnings = [],
  tips = []
}) => {
  const progressPercentage = ((currentStep - 1) / (totalSteps - 1)) * 100;
  
  return (
    <Box sx={{ mb: 3 }}>
      {/* Progreso y tiempo estimado */}
      <Paper elevation={1} sx={{ p: 2, mb: 2, bgcolor: 'info.light', color: 'info.contrastText' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
          <TimerIcon fontSize="small" />
          <Typography variant="body2" sx={{ fontWeight: 500 }}>
            Tiempo restante estimado: {estimatedTimeRemaining}
          </Typography>
        </Box>
        
        <LinearProgress 
          variant="determinate" 
          value={progressPercentage}
          sx={{ 
            height: 6, 
            borderRadius: 3,
            backgroundColor: 'rgba(255,255,255,0.3)',
            '& .MuiLinearProgress-bar': {
              backgroundColor: 'info.contrastText'
            }
          }}
        />
        
        <Typography variant="caption" color="inherit" sx={{ mt: 1, display: 'block' }}>
          Paso {currentStep} de {totalSteps} - {Math.round(progressPercentage)}% completado
        </Typography>
      </Paper>

      {/* Resultados esperados */}
      {expectedResults && (
        <Paper elevation={1} sx={{ p: 2, mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <TrendingUpIcon fontSize="small" color="primary" />
            Qué esperar de tu monitor
          </Typography>
          
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 1 }}>
            {expectedResults.articlesPerDay && (
              <Chip 
                size="small" 
                label={`~${expectedResults.articlesPerDay} artículos/día`}
                color="primary"
                variant="outlined"
              />
            )}
            {expectedResults.detectionStrategy && (
              <Chip 
                size="small" 
                label={expectedResults.detectionStrategy}
                color="secondary"
                variant="outlined"
              />
            )}
            {expectedResults.reliabilityScore && (
              <Chip 
                size="small" 
                label={`${expectedResults.reliabilityScore}% confiabilidad`}
                color={expectedResults.reliabilityScore > 80 ? 'success' : 'warning'}
                variant="outlined"
              />
            )}
          </Box>
          
          <Typography variant="body2" color="text.secondary">
            Las primeras noticias aparecerán aproximadamente en 
            {expectedResults.articlesPerDay && expectedResults.articlesPerDay > 10 ? ' 1-2 horas' : ' 2-6 horas'}
          </Typography>
        </Paper>
      )}

      {/* Advertencias importantes */}
      {warnings.length > 0 && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          <Typography variant="body2" sx={{ fontWeight: 500, mb: 1 }}>
            ⚠️ Consideraciones importantes:
          </Typography>
          <List dense sx={{ pt: 0 }}>
            {warnings.map((warning, index) => (
              <ListItem key={index} sx={{ px: 0, py: 0.5 }}>
                <ListItemIcon sx={{ minWidth: 20 }}>
                  <WarningIcon fontSize="small" color="warning" />
                </ListItemIcon>
                <ListItemText 
                  primary={warning}
                  primaryTypographyProps={{ variant: 'body2' }}
                />
              </ListItem>
            ))}
          </List>
        </Alert>
      )}

      {/* Tips útiles */}
      {tips.length > 0 && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <Typography variant="body2" sx={{ fontWeight: 500, mb: 1 }}>
            💡 Tips para mejores resultados:
          </Typography>
          <List dense sx={{ pt: 0 }}>
            {tips.map((tip, index) => (
              <ListItem key={index} sx={{ px: 0, py: 0.5 }}>
                <ListItemIcon sx={{ minWidth: 20 }}>
                  <CheckIcon fontSize="small" color="info" />
                </ListItemIcon>
                <ListItemText 
                  primary={tip}
                  primaryTypographyProps={{ variant: 'body2' }}
                />
              </ListItem>
            ))}
          </List>
        </Alert>
      )}

      {/* Información adicional según el paso */}
      <StepSpecificInfo currentStep={currentStep} />
    </Box>
  );
};

// Información específica por paso
const StepSpecificInfo: React.FC<{ currentStep: number }> = ({ currentStep }) => {
  const getStepInfo = () => {
    switch (currentStep) {
      case 1:
        return {
          title: "Configurando información básica",
          message: "Asegúrate de que el nombre del medio sea reconocible y la URL sea exacta",
          icon: <InfoIcon fontSize="small" />
        };
      case 2:
        return {
          title: "Especificando contenido",
          message: "Cuanto más específica sea la sección, mejores resultados obtendrás",
          icon: <InfoIcon fontSize="small" />
        };
      case 3:
        return {
          title: "Analizando estructura del sitio",
          message: "Esto puede tomar 30-60 segundos dependiendo de la complejidad del sitio",
          icon: <InfoIcon fontSize="small" />
        };
      case 4:
        return {
          title: "Configuración final",
          message: "Revisa las configuraciones automáticas - puedes ajustarlas según tus necesidades",
          icon: <InfoIcon fontSize="small" />
        };
      case 5:
        return {
          title: "Generando monitor",
          message: "Estamos creando tu monitor personalizado - ¡ya casi terminamos!",
          icon: <InfoIcon fontSize="small" />
        };
      default:
        return null;
    }
  };

  const stepInfo = getStepInfo();
  
  if (!stepInfo) return null;

  return (
    <Box sx={{ 
      display: 'flex', 
      alignItems: 'center', 
      gap: 1, 
      p: 1.5, 
      bgcolor: 'grey.50', 
      borderRadius: 1,
      border: '1px solid',
      borderColor: 'grey.200'
    }}>
      {stepInfo.icon}
      <Box>
        <Typography variant="body2" sx={{ fontWeight: 500 }}>
          {stepInfo.title}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {stepInfo.message}
        </Typography>
      </Box>
    </Box>
  );
};

export default ExpectationManager;