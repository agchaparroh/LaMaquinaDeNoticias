import debounce from 'lodash.debounce';
import { useMemo } from 'react';

// Según SECCIÓN 7.1 - Validar duplicados mientras escribe
export const checkDuplicateSpider = async (medio: string, seccion: string) => {
  if (medio && seccion) {
    // Simular API call - reemplazar con llamada real al backend
    const response = await fetch('/api/check-duplicate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ medio, seccion })
    });
    
    if (response.ok) {
      const result = await response.json();
      return result.exists;
    }
  }
  return false;
};

// Debounce la validación
export const useDebouncedValidation = () => {
  return useMemo(
    () => debounce(checkDuplicateSpider, 500),
    []
  );
};

// Según SECCIÓN 7.2 - Indicadores visuales según plan
export const getStatusColor = (status: string) => {
  switch (status) {
    case 'success': return 'success';  // Verde para éxito
    case 'warning': return 'warning';  // Amarillo para advertencias
    case 'error': return 'error';      // Rojo para errores
    case 'info': return 'info';        // Azul para información
    default: return 'default';
  }
};