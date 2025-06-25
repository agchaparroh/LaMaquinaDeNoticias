import { 
  Box, 
  Button, 
  Card, 
  CardContent, 
  Grid, 
  Typography,
  Paper,
  Stack
} from '@mui/material'
import { useNavigate } from 'react-router-dom'
import {
  Build as BuildIcon,
  CloudUpload as CloudUploadIcon,
  Pattern as PatternIcon,
  TrendingUp as TrendingUpIcon
} from '@mui/icons-material'

function HomePage() {
  const navigate = useNavigate()

  const features = [
    {
      title: 'Wizard de Generación',
      description: 'Genera spiders individuales con asistencia inteligente',
      icon: <BuildIcon fontSize="large" />,
      action: () => navigate('/wizard'),
      color: 'primary'
    },
    {
      title: 'Carga Masiva',
      description: 'Procesa múltiples sitios desde archivos CSV',
      icon: <CloudUploadIcon fontSize="large" />,
      action: () => navigate('/bulk'),
      color: 'secondary'
    },
    {
      title: 'Gestión de Patrones',
      description: 'Administra y optimiza patrones de extracción',
      icon: <PatternIcon fontSize="large" />,
      action: () => navigate('/patterns'),
      color: 'success'
    }
  ]

  const stats = [
    { label: 'Spiders Generados', value: '0' },
    { label: 'Patrones Activos', value: '0' },
    { label: 'Sitios Analizados', value: '0' },
    { label: 'Tasa de Éxito', value: '0%' }
  ]

  return (
    <Box>
      <Typography variant="h3" component="h1" gutterBottom>
        Bienvenido a Spider Factory 2.0
      </Typography>
      <Typography variant="h6" color="text.secondary" paragraph>
        Sistema inteligente de generación de spiders para scraping de noticias
      </Typography>

      <Grid container spacing={3} sx={{ mt: 2 }}>
        {features.map((feature) => (
          <Grid item xs={12} md={4} key={feature.title}>
            <Card 
              sx={{ 
                height: '100%',
                transition: 'transform 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4
                }
              }}
            >
              <CardContent>
                <Box 
                  sx={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    mb: 2,
                    color: `${feature.color}.main`
                  }}
                >
                  {feature.icon}
                  <Typography variant="h5" component="h2" sx={{ ml: 1 }}>
                    {feature.title}
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" paragraph>
                  {feature.description}
                </Typography>
                <Button 
                  variant="contained" 
                  color={feature.color as any}
                  onClick={feature.action}
                  fullWidth
                >
                  Acceder
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Typography variant="h4" component="h2" sx={{ mt: 6, mb: 3 }}>
        Estadísticas
      </Typography>
      
      <Grid container spacing={2}>
        {stats.map((stat) => (
          <Grid item xs={6} md={3} key={stat.label}>
            <Paper 
              elevation={2} 
              sx={{ 
                p: 3, 
                textAlign: 'center',
                background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)'
              }}
            >
              <TrendingUpIcon color="primary" sx={{ mb: 1 }} />
              <Typography variant="h4" component="div">
                {stat.value}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {stat.label}
              </Typography>
            </Paper>
          </Grid>
        ))}
      </Grid>

      <Box sx={{ mt: 6 }}>
        <Typography variant="h5" gutterBottom>
          Acerca de Spider Factory 2.0
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          Spider Factory 2.0 es un sistema avanzado que automatiza la creación de spiders 
          para la extracción de noticias. Utiliza inteligencia artificial para analizar 
          sitios web, detectar patrones de contenido y generar código optimizado para Scrapy.
        </Typography>
        <Stack direction="row" spacing={2}>
          <Typography variant="body2" color="text.secondary">
            • Análisis inteligente con Firecrawl
          </Typography>
          <Typography variant="body2" color="text.secondary">
            • Generación automática de código
          </Typography>
          <Typography variant="body2" color="text.secondary">
            • Soporte para RSS, HTML y JavaScript
          </Typography>
        </Stack>
      </Box>
    </Box>
  )
}

export default HomePage