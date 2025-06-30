import * as yup from 'yup';
import { AREAS_GEOGRAFICAS_OFICIALES } from '../constants/areas';

// Según SECCIÓN 1.3 - Schema de validación EXACTO del plan
export const schema = yup.object({
  medio: yup.string().required('El nombre del medio es obligatorio'),
  seccion: yup.string().required('La sección es obligatoria'),
  area_geografica: yup.string().required('El área geográfica es obligatoria'),
  tipo_medio: yup.string().oneOf(['diario', 'revista', 'agencia']).required(),
  url: yup.string().url('URL inválida').required('La URL es obligatoria'),
  frecuencia_minutos: yup.number().positive().integer(),
  rss_url: yup.string().url('URL inválida').when('tiene_rss', {
    is: true,
    then: (schema) => schema.required('La URL del RSS es obligatoria')
  })
});

// Según SECCIÓN 16.2 - Validación estricta
export const validationSchema = yup.object({
  area_geografica: yup
    .string()
    .oneOf(
      AREAS_GEOGRAFICAS_OFICIALES,
      'Área geográfica no válida'
    )
    .required('El área geográfica es obligatoria'),
  medio: yup.string().required('El nombre del medio es obligatorio'),
  seccion: yup.string().required('La sección es obligatoria'),
  tipo_medio: yup.string().oneOf(['diario', 'revista', 'agencia']).required(),
  url: yup.string().url('URL inválida').required('La URL es obligatoria'),
  frecuencia_minutos: yup.number().positive().integer().required(),
});