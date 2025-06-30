import React from 'react';
import { TextField, Box, FormControlLabel, Checkbox, Alert, AlertTitle, Button } from '@mui/material';
import { WizardData } from '../../types';

interface SectionUrlStepProps {
  data: WizardData;
  onUpdate: (updates: Partial<WizardData>) => void;
  onNext: () => void;
}

// Según SECCIÓN 1.2 - Agregar Step 2 - URLs y sección (FALTANTE)
// Crear nuevo componente SectionUrlStep.tsx:
const SectionUrlStep: React.FC<SectionUrlStepProps> = ({ data, onUpdate, onNext }) => {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Alert severity="info">
        <AlertTitle>URLs y Sección</AlertTitle>
        Define la sección específica a monitorear y si el sitio tiene RSS.
      </Alert>

      {/* Campo seccion - Nombre de la sección a monitorear */}
      <TextField
        label="Sección"
        value={data.seccion || ''}
        onChange={(e) => onUpdate({ seccion: e.target.value })}
        fullWidth
        required
        helperText="Nombre de la sección a monitorear"
      />

      {/* Campo url - URL de la sección (ya existe pero moverlo aquí) */}
      <TextField
        label="URL de la sección"
        value={data.url || ''}
        onChange={(e) => onUpdate({ url: e.target.value })}
        fullWidth
        required
        type="url"
        helperText="URL específica de la sección a monitorear"
      />

      {/* Checkbox tiene_rss - ¿El sitio tiene RSS? */}
      <FormControlLabel
        control={
          <Checkbox
            checked={data.tiene_rss || false}
            onChange={(e) => onUpdate({ tiene_rss: e.target.checked })}
          />
        }
        label="¿El sitio tiene RSS?"
      />

      {/* Campo rss_url - URL del RSS (condicional si tiene_rss = true) */}
      {data.tiene_rss && (
        <TextField
          label="URL del RSS"
          value={data.rss_url || ''}
          onChange={(e) => onUpdate({ rss_url: e.target.value })}
          fullWidth
          type="url"
          helperText="URL del RSS (condicional si tiene_rss = true)"
        />
      )}

      <Box sx={{ mt: 4, display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          variant="contained"
          onClick={onNext}
          size="large"
          disabled={!data.seccion || !data.url}
        >
          Analizar Sitio
        </Button>
      </Box>
    </Box>
  );
};

export default SectionUrlStep;