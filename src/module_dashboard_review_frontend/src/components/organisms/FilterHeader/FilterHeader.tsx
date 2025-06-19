import React from 'react';
import {
  Box,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Grid,
  Paper,
  Typography,
  Chip,
  SelectChangeEvent
} from '@mui/material';
import {
  FilterList as FilterListIcon,
  Clear as ClearIcon,
  Search as SearchIcon
} from '@mui/icons-material';
import type { FilterState, FilterOptions } from '@/types/domain';

interface FilterHeaderProps {
  filters: FilterState;
  filterOptions: FilterOptions | null; // Permitir null
  onFiltersChange: (filters: FilterState) => void;
  onResetFilters: () => void;
  isLoading?: boolean;
  totalResults?: number;
}

export const FilterHeader: React.FC<FilterHeaderProps> = ({
  filters,
  filterOptions,
  onFiltersChange,
  onResetFilters,
  isLoading = false,
  totalResults
}) => {
  
  const handleInputChange = (field: keyof FilterState) => 
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const value = event.target.value;
      onFiltersChange({
        ...filters,
        [field]: value || undefined
      });
    };

  const handleSelectChange = (field: keyof FilterState) => 
    (event: SelectChangeEvent<string>) => {
      const value = event.target.value;
      onFiltersChange({
        ...filters,
        [field]: value || undefined
      });
    };

  const handleDateChange = (field: 'fechaInicio' | 'fechaFin') => 
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const value = event.target.value;
      onFiltersChange({
        ...filters,
        [field]: value ? new Date(value) : undefined
      });
    };

  const getActiveFiltersCount = () => {
    return Object.entries(filters).filter(([_, value]) => 
      value !== undefined && value !== null && value !== ''
    ).length;
  };

  const formatDateForInput = (date: Date | undefined | null) => {
    if (!date) return '';
    return date.toISOString().split('T')[0];
  };

  // Valores por defecto si filterOptions es null
  const medios = filterOptions?.medios || [];
  const paises = filterOptions?.paises || [];
  const tiposHecho = filterOptions?.tiposHecho || [];

  return (
    <Paper sx={{ p: 3, mb: 3, border: 1, borderColor: 'divider' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <FilterListIcon sx={{ mr: 1, color: 'primary.main' }} />
        <Typography variant="h6" component="h2">
          Filtros de Búsqueda
        </Typography>
        {getActiveFiltersCount() > 0 && (
          <Chip 
            label={`${getActiveFiltersCount()} filtros activos`}
            color="primary"
            size="small"
            sx={{ ml: 2 }}
          />
        )}
        {totalResults !== undefined && (
          <Typography variant="body2" color="text.secondary" sx={{ ml: 'auto' }}>
            {totalResults} resultados
          </Typography>
        )}
      </Box>

      {/* Filtros principales */}
      <Grid container spacing={2}>
        {/* Búsqueda por texto */}
        <Grid item xs={12} md={6}>
          <TextField
            label="Buscar en contenido"
            variant="outlined"
            fullWidth
            size="small"
            value={filters.medio || ''}
            onChange={handleInputChange('medio')}
            placeholder="Palabra clave en el hecho..."
            InputProps={{
              startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
            }}
            disabled={isLoading}
          />
        </Grid>

        {/* Medio/Fuente */}
        <Grid item xs={12} md={3}>
          <FormControl fullWidth size="small">
            <InputLabel>Medio</InputLabel>
            <Select
              value={filters.medio || ''}
              label="Medio"
              onChange={handleSelectChange('medio')}
              disabled={isLoading}
            >
              <MenuItem value="">Todos los medios</MenuItem>
              {medios.map((medio) => (
                <MenuItem key={medio} value={medio}>
                  {medio}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        {/* País */}
        <Grid item xs={12} md={3}>
          <FormControl fullWidth size="small">
            <InputLabel>País</InputLabel>
            <Select
              value={filters.paisPublicacion || ''}
              label="País"
              onChange={handleSelectChange('paisPublicacion')}
              disabled={isLoading}
            >
              <MenuItem value="">Todos los países</MenuItem>
              {paises.map((pais) => (
                <MenuItem key={pais} value={pais}>
                  {pais}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        {/* Tipo de hecho */}
        <Grid item xs={12} md={3}>
          <FormControl fullWidth size="small">
            <InputLabel>Tipo</InputLabel>
            <Select
              value={filters.tipoHecho || ''}
              label="Tipo"
              onChange={handleSelectChange('tipoHecho')}
              disabled={isLoading}
            >
              <MenuItem value="">Todos los tipos</MenuItem>
              {tiposHecho.map((tipo) => (
                <MenuItem key={tipo} value={tipo}>
                  {tipo}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        {/* Evaluación editorial */}
        <Grid item xs={12} md={3}>
          <FormControl fullWidth size="small">
            <InputLabel>Evaluación</InputLabel>
            <Select
              value={filters.evaluacionEditorial || ''}
              label="Evaluación"
              onChange={handleSelectChange('evaluacionEditorial')}
              disabled={isLoading}
            >
              <MenuItem value="">Todas las evaluaciones</MenuItem>
              <MenuItem value="sin_evaluar">Sin evaluar</MenuItem>
              <MenuItem value="verdadero">Verificado</MenuItem>
              <MenuItem value="falso">Falso</MenuItem>
              <MenuItem value="necesita_verificacion">Necesita verificación</MenuItem>
            </Select>
          </FormControl>
        </Grid>

        {/* Fecha inicio */}
        <Grid item xs={12} md={3}>
          <TextField
            label="Fecha desde"
            type="date"
            fullWidth
            size="small"
            value={formatDateForInput(filters.fechaInicio)}
            onChange={handleDateChange('fechaInicio')}
            InputLabelProps={{ shrink: true }}
            disabled={isLoading}
          />
        </Grid>

        {/* Fecha fin */}
        <Grid item xs={12} md={3}>
          <TextField
            label="Fecha hasta"
            type="date"
            fullWidth
            size="small"
            value={formatDateForInput(filters.fechaFin)}
            onChange={handleDateChange('fechaFin')}
            InputLabelProps={{ shrink: true }}
            disabled={isLoading}
          />
        </Grid>

        {/* Importancia mínima */}
        <Grid item xs={12} md={3}>
          <TextField
            label="Importancia mínima"
            type="number"
            fullWidth
            size="small"
            value={filters.importanciaMin || ''}
            onChange={handleInputChange('importanciaMin')}
            inputProps={{ min: 1, max: 10 }}
            disabled={isLoading}
          />
        </Grid>
      </Grid>

      {/* Botones de acción */}
      <Box sx={{ display: 'flex', gap: 2, mt: 3, justifyContent: 'flex-end' }}>
        <Button
          variant="outlined"
          startIcon={<ClearIcon />}
          onClick={onResetFilters}
          disabled={isLoading || getActiveFiltersCount() === 0}
        >
          Limpiar Filtros
        </Button>
        <Button
          variant="contained"
          startIcon={<SearchIcon />}
          disabled={isLoading}
        >
          {isLoading ? 'Filtrando...' : 'Aplicar Filtros'}
        </Button>
      </Box>
    </Paper>
  );
};