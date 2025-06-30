import { 
  Box, 
  Button,
  Card,
  CardContent,
  Chip,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
  InputAdornment
} from '@mui/material'
import {
  Add as AddIcon,
  Search as SearchIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon
} from '@mui/icons-material'
import { useState } from 'react'

interface Pattern {
  id: string
  domain: string
  pattern_type: string
  confidence: number
  usage_count: number
  last_used: string
  success_rate: number
}

function PatternsPage() {
  const [searchTerm, setSearchTerm] = useState('')

  // Datos de ejemplo
  const patterns: Pattern[] = [
    {
      id: '1',
      domain: 'ejemplo.com',
      pattern_type: 'RSS',
      confidence: 0.95,
      usage_count: 150,
      last_used: '2024-01-15',
      success_rate: 98
    },
    {
      id: '2',
      domain: 'noticias.es',
      pattern_type: 'Scraping',
      confidence: 0.87,
      usage_count: 75,
      last_used: '2024-01-14',
      success_rate: 92
    },
    {
      id: '3',
      domain: 'blog.tech',
      pattern_type: 'Playwright',
      confidence: 0.78,
      usage_count: 45,
      last_used: '2024-01-13',
      success_rate: 85
    }
  ]

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'success'
    if (confidence >= 0.7) return 'warning'
    return 'error'
  }

  const getPatternTypeColor = (type: string) => {
    switch (type) {
      case 'RSS': return 'primary'
      case 'Scraping': return 'secondary'
      case 'Playwright': return 'info'
      default: return 'default'
    }
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Gestión de Patrones
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
        >
          Nuevo Patrón
        </Button>
      </Box>

      <Typography variant="body1" color="text.secondary" paragraph>
        Administra y optimiza los patrones de extracción para mejorar la eficiencia
      </Typography>

      <Paper sx={{ p: 2, mb: 3 }}>
        <TextField
          fullWidth
          placeholder="Buscar por dominio o tipo..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
        />
      </Paper>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Dominio</TableCell>
              <TableCell>Tipo</TableCell>
              <TableCell align="center">Confianza</TableCell>
              <TableCell align="center">Usos</TableCell>
              <TableCell align="center">Tasa de Éxito</TableCell>
              <TableCell>Último Uso</TableCell>
              <TableCell align="center">Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {patterns.map((pattern) => (
              <TableRow key={pattern.id} hover>
                <TableCell>
                  <Typography variant="body2" fontWeight="medium">
                    {pattern.domain}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip 
                    label={pattern.pattern_type}
                    size="small"
                    color={getPatternTypeColor(pattern.pattern_type) as any}
                  />
                </TableCell>
                <TableCell align="center">
                  <Chip
                    label={`${(pattern.confidence * 100).toFixed(0)}%`}
                    size="small"
                    color={getConfidenceColor(pattern.confidence) as any}
                  />
                </TableCell>
                <TableCell align="center">
                  {pattern.usage_count}
                </TableCell>
                <TableCell align="center">
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {pattern.success_rate >= 90 ? (
                      <TrendingUpIcon color="success" fontSize="small" />
                    ) : (
                      <TrendingDownIcon color="error" fontSize="small" />
                    )}
                    <Typography variant="body2" sx={{ ml: 0.5 }}>
                      {pattern.success_rate}%
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" color="text.secondary">
                    {new Date(pattern.last_used).toLocaleDateString('es-ES')}
                  </Typography>
                </TableCell>
                <TableCell align="center">
                  <IconButton size="small" color="primary">
                    <EditIcon fontSize="small" />
                  </IconButton>
                  <IconButton size="small" color="error">
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Box sx={{ mt: 4 }}>
        <Typography variant="h5" gutterBottom>
          Estadísticas de Patrones
        </Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 2 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total de Patrones
              </Typography>
              <Typography variant="h4">
                {patterns.length}
              </Typography>
            </CardContent>
          </Card>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Confianza Promedio
              </Typography>
              <Typography variant="h4">
                {(patterns.reduce((acc, p) => acc + p.confidence, 0) / patterns.length * 100).toFixed(0)}%
              </Typography>
            </CardContent>
          </Card>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Tasa de Éxito Global
              </Typography>
              <Typography variant="h4">
                {(patterns.reduce((acc, p) => acc + p.success_rate, 0) / patterns.length).toFixed(0)}%
              </Typography>
            </CardContent>
          </Card>
        </Box>
      </Box>
    </Box>
  )
}

export default PatternsPage