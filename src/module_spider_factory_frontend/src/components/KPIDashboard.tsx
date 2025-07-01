import React from 'react';
import { Grid, Card, CardContent, Typography, Box } from '@mui/material';
import { Speed as SpeedIcon, Timeline as TimelineIcon } from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { KPIMetrics } from '../types';

interface MetricCardProps {
  title: string;
  value: string;
  target: string;
  icon: React.ReactNode;
  color: 'success' | 'warning' | 'error' | 'info';
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, target, icon, color }) => (
  <Card>
    <CardContent>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        {icon}
        <Typography variant="h6" sx={{ ml: 1 }}>
          {title}
        </Typography>
      </Box>
      <Typography variant="h4" color={color}>
        {value}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        Target: {target}
      </Typography>
    </CardContent>
  </Card>
);

// Según SECCIÓN 15.1 - Dashboard de KPIs
// Crear componente KPIDashboard.tsx:
const KPIDashboard = () => {
  const { data: metrics } = useQuery({
    queryKey: ['kpi-metrics'],
    queryFn: fetchKPIMetrics,
  });
  
  return (
    <Grid container spacing={2}>
      <Grid item xs={12} md={3}>
        <MetricCard
          title="Reducción de Tiempo"
          value={`${metrics?.tiempoReduccion || 0}%`}
          target="97%"
          icon={<SpeedIcon />}
          color={(metrics?.tiempoReduccion ?? 0) >= 97 ? 'success' : 'warning'}
        />
      </Grid>
      <Grid item xs={12} md={3}>
        <MetricCard
          title="Tiempo Promedio RSS"
          value={`${metrics?.tiempoPromedioRSS || 0}s`}
          target="<5s"
          icon={<TimelineIcon />}
          color={(metrics?.tiempoPromedioRSS ?? 0) < 5 ? 'success' : 'warning'}
        />
      </Grid>
      <Grid item xs={12} md={3}>
        <MetricCard
          title="Precisión Spiders"
          value={`${metrics?.precisionSpiders || 0}%`}
          target=">90%"
          icon={<SpeedIcon />}
          color={(metrics?.precisionSpiders ?? 0) > 90 ? 'success' : 'error'}
        />
      </Grid>
      <Grid item xs={12} md={3}>
        <MetricCard
          title="Spiders por Día"
          value={`${metrics?.spidersPorDia || 0}`}
          target="200+"
          icon={<TimelineIcon />}
          color={(metrics?.spidersPorDia ?? 0) >= 200 ? 'success' : 'warning'}
        />
      </Grid>
    </Grid>
  );
};

// Función fetch para las métricas
const fetchKPIMetrics = async (): Promise<KPIMetrics> => {
  const response = await fetch('/api/metrics');
  return response.json();
};

export default KPIDashboard;