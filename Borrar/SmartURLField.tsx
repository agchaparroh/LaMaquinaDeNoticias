import React, { useState, useEffect } from 'react';
import { 
  TextField, 
  Box, 
  CircularProgress,
  Chip,
  Typography,
  InputAdornment,
  Alert
} from '@mui/material';
import { 
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Language as LanguageIcon
} from '@mui/icons-material';
import { normalizeUrl } from '../../utils/validationHelpers';

interface SmartURLFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  onValidation?: (isValid: boolean, info?: any) => void;
  placeholder?: string;
  helperText?: string;
  required?: boolean;
  validateDuplicates?: boolean;
}

const SmartURLField: React.FC<SmartURLFieldProps> = ({
  label,
  value,
  onChange,
  onValidation,
  placeholder,
  helperText,
  required = false,
  validateDuplicates = false
}) => {
  const [isValidating, setIsValidating] = useState(false);
  const [validationStatus, setValidationStatus] = useState<'idle' | 'valid' | 'invalid'>('idle');
  const [siteInfo, setSiteInfo] = useState<any>(null);
  const [error, setError] = useState<string>('');

  const validateUrl = (url: string): boolean => {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  };

  const fetchSiteInfo = async (url: string) => {
    try {
      setIsValidating(true);
      // Simular llamada a API para obtener info del sitio
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      if (validateUrl(url)) {
        const domain = new URL(url).hostname;
        setSiteInfo({
          title: `Sitio: ${domain}`,
          accessible: true,
          hasRSS: Math.random() > 0.5,
          type: 'news'
        });
        setValidationStatus('valid');
        setError('');
        if (onValidation) onValidation(true, { domain, accessible: true });
      } else {
        setValidationStatus('invalid');
        setError('URL no válida');
        if (onValidation) onValidation(false);
      }
    } catch (err) {
      setValidationStatus('invalid');
      setError('No se pudo verificar la URL');
      if (onValidation) onValidation(false);
    } finally {
      setIsValidating(false);
    }
  };

  useEffect(() => {
    if (value && value.length > 10) {
      const normalizedUrl = normalizeUrl(value);
      if (normalizedUrl !== value) {
        onChange(normalizedUrl);
      }
      
      const timeoutId = setTimeout(() => {
        fetchSiteInfo(normalizedUrl);
      }, 500);

      return () => clearTimeout(timeoutId);
    } else {
      setValidationStatus('idle');
      setSiteInfo(null);
      setError('');
    }
  }, [value]);

  const getStatusIcon = () => {
    if (isValidating) return <CircularProgress size={20} />;
    if (validationStatus === 'valid') return <CheckIcon color="success" />;
    if (validationStatus === 'invalid') return <ErrorIcon color="error" />;
    return <LanguageIcon color="action" />;
  };

  return (
    <Box>
      <TextField
        fullWidth
        label={label}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        error={validationStatus === 'invalid'}
        helperText={error || helperText}
        required={required}
        InputProps={{
          endAdornment: (
            <InputAdornment position="end">
              {getStatusIcon()}
            </InputAdornment>
          ),
        }}
      />
      
      {siteInfo && validationStatus === 'valid' && (
        <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          <Chip 
            size="small" 
            label="✅ Sitio accesible" 
            color="success" 
            variant="outlined" 
          />
          {siteInfo.hasRSS && (
            <Chip 
              size="small" 
              label="📡 RSS disponible" 
              color="info" 
              variant="outlined" 
            />
          )}
          <Chip 
            size="small" 
            label={`🌐 ${new URL(value).hostname}`} 
            variant="outlined" 
          />
        </Box>
      )}

      {validateDuplicates && validationStatus === 'valid' && (
        <Alert severity="warning" sx={{ mt: 1 }}>
          <Typography variant="body2">
            ⚠️ Ya existe un monitor para este sitio. ¿Continuar creando uno nuevo para una sección diferente?
          </Typography>
        </Alert>
      )}
    </Box>
  );
};

export default SmartURLField;