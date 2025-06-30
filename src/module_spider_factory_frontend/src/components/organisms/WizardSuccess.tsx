import React from 'react';
import { 
  Box, 
  Typography, 
  Button, 
  Paper, 
  Chip,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Alert
} from '@mui/material';
import { 
  CheckCircle as CheckIcon,
  Schedule as ScheduleIcon,
  Dashboard as DashboardIcon,
  Settings as SettingsIcon,
  Refresh as RefreshIcon,
  Analytics as AnalyticsIcon
} from '@mui/icons-material';

interface WizardSuccessProps {
  spiderData: {
    name: string;
    url: string;
    section: string;
    frequency: string;
    strategy: string;
    estimatedArticles: number;
    nextExecution: string;
  };
  onGoToDashboard: () => void;
  onCreateAnother: () => void;
  onViewSettings: () => void;
}

const WizardSuccess: React.FC<WizardSuccessProps> = ({
  spiderData,
  onGoToDashboard,
  onCreateAnother,
  onViewSettings
}) => {
  return (
    <Box sx={{ maxWidth: 600, mx: 'auto', p: 3 }}>
      {/* Cabecera de éxito */}
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <CheckIcon sx={{ fontSize: 64, color: 'success.main', mb: 2 }} />
        <Typography variant="h4" gutterBottom color="success.main">
          ¡Monitor Creado Exitosamente!
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Tu monitor de noticias está activo y funcionando
        </Typography>
      </Box>

      {/* Información del monitor */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          📊 Resumen del Monitor
        </Typography>
        
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
            {spiderData.name}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {spiderData.url}
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
          <Chip label={`📰 ${spiderData.section}`} variant="outlined" />
          <Chip label={`⏰ ${spiderData.frequency}`} variant="outlined" />
          <Chip label={`🔄 ${spiderData.strategy}`} variant="outlined" color="primary" />
        </Box>

        <Divider sx={{ my: 2 }} />

        <Typography variant="body2" color="text.secondary">
          <strong>Estimación:</strong> ~{spiderData.estimatedArticles} artículos por día
        </Typography>
        <Typography variant="body2" color="text.secondary">
          <strong>Próxima ejecución:</strong> {spiderData.nextExecution}
        </Typography>
      </Paper>

      {/* Qué puedes hacer ahora */}
      <Paper elevation={1} sx={{ p: 3, mb: 3, bgcolor: 'primary.light', color: 'primary.contrastText' }}>
        <Typography variant="h6" gutterBottom>
          🎯 ¿Qué puedes hacer ahora?
        </Typography>
        
        <List dense>
          <ListItem>
            <ListItemIcon>
              <DashboardIcon sx={{ color: 'primary.contrastText' }} />
            </ListItemIcon>
            <ListItemText 
              primary="Ver el Dashboard"
              secondary="Monitorea todas tus fuentes de noticias en tiempo real"
            />
          </ListItem>
          
          <ListItem>
            <ListItemIcon>
              <AnalyticsIcon sx={{ color: 'primary.contrastText' }} />
            </ListItemIcon>
            <ListItemText 
              primary="Revisar Noticias Capturadas"
              secondary="Ve las últimas noticias que ya hemos encontrado"
            />
          </ListItem>
          
          <ListItem>
            <ListItemIcon>
              <SettingsIcon sx={{ color: 'primary.contrastText' }} />
            </ListItemIcon>
            <ListItemText 
              primary="Ajustar Configuración"
              secondary="Modifica frecuencia, filtros o notificaciones"
            />
          </ListItem>
          
          <ListItem>
            <ListItemIcon>
              <RefreshIcon sx={{ color: 'primary.contrastText' }} />
            </ListItemIcon>
            <ListItemText 
              primary="Crear Más Monitores"
              secondary="Agrega más fuentes para una cobertura completa"
            />
          </ListItem>
        </List>
      </Paper>

      {/* Consejos útiles */}
      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body2" sx={{ fontWeight: 500, mb: 1 }}>
          💡 Consejos para optimizar tu monitor:
        </Typography>
        <Typography variant="body2" component="div">
          • Las primeras noticias aparecerán en los próximos {spiderData.frequency}<br/>
          • Puedes pausar, editar o eliminar el monitor desde el Dashboard<br/>
          • Configura notificaciones para palabras clave importantes<br/>
          • Revisa las métricas semanales para ajustar la frecuencia
        </Typography>
      </Alert>

      {/* Botones de acción */}
      <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, gap: 2 }}>
        <Button
          variant="contained"
          size="large"
          startIcon={<DashboardIcon />}
          onClick={onGoToDashboard}
          sx={{ flex: 1 }}
        >
          Ir al Dashboard
        </Button>
        
        <Button
          variant="outlined"
          size="large"
          startIcon={<RefreshIcon />}
          onClick={onCreateAnother}
          sx={{ flex: 1 }}
        >
          Crear Otro Monitor
        </Button>
      </Box>

      <Box sx={{ textAlign: 'center', mt: 2 }}>
        <Button
          variant="text"
          startIcon={<SettingsIcon />}
          onClick={onViewSettings}
          size="small"
        >
          Configuración Avanzada
        </Button>
      </Box>
    </Box>
  );
};

export default WizardSuccess;