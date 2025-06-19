import React from 'react';
import {
  Box,
  Slider,
  Typography,
  IconButton,
  CircularProgress
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon
} from '@mui/icons-material';

interface ImportanceSliderProps {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  disabled?: boolean;
  loading?: boolean;
  label?: string;
  showButtons?: boolean;
}

export const ImportanceSlider: React.FC<ImportanceSliderProps> = ({
  value,
  onChange,
  min = 1,
  max = 10,
  disabled = false,
  loading = false,
  label = "Importancia",
  showButtons = true
}) => {
  
  const handleSliderChange = (_: Event, newValue: number | number[]) => {
    if (!disabled && !loading) {
      onChange(newValue as number);
    }
  };

  const handleIncrement = () => {
    if (value < max && !disabled && !loading) {
      onChange(value + 1);
    }
  };

  const handleDecrement = () => {
    if (value > min && !disabled && !loading) {
      onChange(value - 1);
    }
  };

  const getColorByValue = (val: number) => {
    if (val <= 3) return 'success.main';
    if (val <= 6) return 'warning.main';
    return 'error.main';
  };

  const getImportanceLabel = (val: number) => {
    if (val <= 3) return 'Baja';
    if (val <= 6) return 'Media';
    if (val <= 8) return 'Alta';
    return 'Crítica';
  };

  return (
    <Box sx={{ width: '100%', px: 1 }}>
      {/* Label y valor actual */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
        <Typography variant="subtitle2" color="text.secondary">
          {label}
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {loading && <CircularProgress size={16} />}
          <Typography 
            variant="h6" 
            sx={{ 
              color: getColorByValue(value),
              fontWeight: 'bold',
              minWidth: '20px'
            }}
          >
            {value}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            ({getImportanceLabel(value)})
          </Typography>
        </Box>
      </Box>

      {/* Slider con botones opcionales */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        {showButtons && (
          <IconButton
            size="small"
            onClick={handleDecrement}
            disabled={disabled || loading || value <= min}
            sx={{ 
              bgcolor: 'background.paper',
              border: 1,
              borderColor: 'divider'
            }}
          >
            <TrendingDownIcon fontSize="small" />
          </IconButton>
        )}
        
        <Slider
          value={value}
          onChange={handleSliderChange}
          min={min}
          max={max}
          step={1}
          marks={[
            { value: min, label: min.toString() },
            { value: Math.floor((min + max) / 2), label: Math.floor((min + max) / 2).toString() },
            { value: max, label: max.toString() }
          ]}
          disabled={disabled || loading}
          sx={{
            flexGrow: 1,
            '& .MuiSlider-thumb': {
              color: getColorByValue(value),
            },
            '& .MuiSlider-track': {
              color: getColorByValue(value),
            },
            '& .MuiSlider-markLabel': {
              fontSize: '0.75rem'
            }
          }}
        />
        
        {showButtons && (
          <IconButton
            size="small"
            onClick={handleIncrement}
            disabled={disabled || loading || value >= max}
            sx={{ 
              bgcolor: 'background.paper',
              border: 1,
              borderColor: 'divider'
            }}
          >
            <TrendingUpIcon fontSize="small" />
          </IconButton>
        )}
      </Box>

      {/* Descripción de escala */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
        <Typography variant="caption" color="success.main">
          Baja (1-3)
        </Typography>
        <Typography variant="caption" color="warning.main">
          Media (4-6)
        </Typography>
        <Typography variant="caption" color="error.main">
          Alta/Crítica (7-10)
        </Typography>
      </Box>
    </Box>
  );
};