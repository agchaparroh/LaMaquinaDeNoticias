import React from 'react';
import { 
  TextField, 
  Box, 
  FormControlLabel, 
  Checkbox, 
  Alert, 
  AlertTitle, 
  Button, 
  Typography,
  InputAdornment
} from '@mui/material';
import { WizardData } from '../../types';
import HelpTooltip from '../atoms/HelpTooltip';
import ExampleShowcase from '../molecules/ExampleShowcase';
import { HELP_CONTENT, EXAMPLES } from '../../constants/helpContent';

interface SectionUrlStepProps {
  data: WizardData;
  onUpdate: (updates: Partial<WizardData>) => void;
  onNext: () => void;
}

const SectionUrlStep: React.FC<SectionUrlStepProps> = ({ data, onUpdate, onNext }) => {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        <Typography variant="h6">
          URLs y Sección Específica
        </Typography>
        <HelpTooltip title="Ahora vamos a configurar qué sección específica del sitio quieres monitorear" />
      </Box>
      
      <Alert severity="info">
        <AlertTitle>🎯 Configuración de Sección</AlertTitle>
        Define la sección específica que quieres monitorear. Esto te permite obtener solo las noticias que realmente te interesan.
      </Alert>

      {/* Ejemplos de secciones comunes */}
      <ExampleShowcase
        title="💡 Secciones más comunes:"
        examples={EXAMPLES.SECCIONES_COMUNES}
        onSelect={(seccion) => onUpdate({ seccion })}
        maxVisible={4}
      />

      {/* Campo seccion - Nombre de la sección a monitorear */}
      <TextField
        label="Nombre de la sección"
        placeholder="Política, Deportes, Internacional..."
        value={data.seccion || ''}
        onChange={(e) => onUpdate({ seccion: e.target.value })}
        fullWidth
        required
        helperText="Especifica qué sección del sitio quieres monitorear"
        InputProps={{
          endAdornment: (
            <InputAdornment position="end">
              <HelpTooltip title={HELP_CONTENT.SECCION} />
            </InputAdornment>
          ),
        }}
      />

      {/* Ejemplos de URLs de sección */}
      <ExampleShowcase
        title="💡 Ejemplos de URLs de sección:"
        examples={EXAMPLES.URLS_SECCION}
        onSelect={(url) => onUpdate({ url })}
        maxVisible={2}
      />

      {/* Campo url - URL de la sección */}
      <TextField
        label="URL específica de la sección"
        placeholder="https://ejemplo.com/politica/"
        value={data.url || ''}
        onChange={(e) => onUpdate({ url: e.target.value })}
        fullWidth
        required
        type="url"
        helperText="Dirección web específica de la sección que quieres monitorear"
        InputProps={{
          endAdornment: (
            <InputAdornment position="end">
              <HelpTooltip title={HELP_CONTENT.URL_SECCION} />
            </InputAdornment>
          ),
        }}
      />

      {/* Checkbox tiene_rss - ¿El sitio tiene RSS? */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2 }}>
        <FormControlLabel
          control={
            <Checkbox
              checked={data.tiene_rss || false}
              onChange={(e) => onUpdate({ tiene_rss: e.target.checked })}
            />
          }
          label="¿El sitio web tiene feeds RSS?"
        />
        <HelpTooltip title={HELP_CONTENT.TIENE_RSS} />
      </Box>
      <Typography variant="caption" color="text.secondary" display="block" sx={{ ml: 4, mt: -1 }}>
        Los feeds RSS son más eficientes para obtener noticias actualizadas
      </Typography>

      {/* Campo rss_url - URL del RSS (condicional si tiene_rss = true) */}
      {data.tiene_rss && (
        <TextField
          label="URL del feed RSS"
          placeholder="https://ejemplo.com/rss/politica.xml"
          value={data.rss_url || ''}
          onChange={(e) => onUpdate({ rss_url: e.target.value })}
          fullWidth
          type="url"
          helperText="Dirección del feed RSS de la sección específica"
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <HelpTooltip title={HELP_CONTENT.RSS_URL} />
              </InputAdornment>
            ),
          }}
        />
      )}

      <Box sx={{ mt: 4, display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          variant="contained"
          onClick={onNext}
          size="large"
          disabled={!data.seccion || !data.url || (data.tiene_rss && !data.rss_url)}
        >
          Continuar al Análisis →
        </Button>
      </Box>
    </Box>
  );
};

export default SectionUrlStep;