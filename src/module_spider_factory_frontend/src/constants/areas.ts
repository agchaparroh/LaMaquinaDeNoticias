// Según SECCIÓN 1.1 - ESTÁNDAR OFICIAL DE ÁREAS GEOGRÁFICAS DE LA HISPANIDAD

// Países de la Hispanidad (21 países) - ESTÁNDAR OFICIAL
export const PAISES_HISPANIDAD = [
  "ARGENTINA", "BOLIVIA", "CHILE", "COLOMBIA", "COSTA_RICA",
  "CUBA", "ECUADOR", "EL_SALVADOR", "ESPAÑA", "FILIPINAS", 
  "GUATEMALA", "GUINEA_ECUATORIAL", "HONDURAS", "MÉXICO", 
  "NICARAGUA", "PANAMÁ", "PARAGUAY", "PERÚ", "PUERTO_RICO", 
  "REPÚBLICA_DOMINICANA", "SAHARA_OCCIDENTAL", "URUGUAY", "VENEZUELA"
] as const;

// Regiones geográficas - ESTÁNDAR OFICIAL
export const REGIONES = {
  "HISPANIDAD": "Todos los países y territorios de herencia cultural hispana",
  "HISPANOAMERICA": "Países de América con herencia hispana",
  "CENTROAMERICA": "Países de América Central",
  "CARIBE_HISPANO": "Países hispanos del Caribe",
  "TERRITORIOS_OCUPADOS": "Territorios en disputa",
  "DIASPORA_HISPANA_USA": "Comunidad hispana en Estados Unidos",
  "GLOBAL": "Cobertura mundial",
  "PAISES_NO_HISPANOS": "Países fuera de la Hispanidad"
} as const;

// Lista completa de áreas geográficas (regiones + países) - ESTÁNDAR OFICIAL
export const AREAS_GEOGRAFICAS = [
  ...Object.keys(REGIONES),
  ...PAISES_HISPANIDAD
] as const;

// Alias para compatibilidad con código existente
export const AREAS_GEOGRAFICAS_OFICIALES = AREAS_GEOGRAFICAS;

export const TIPOS_MEDIO = [
  { value: 'diario', label: 'Diario' },
  { value: 'revista', label: 'Revista' },
  { value: 'agencia', label: 'Agencia de noticias' }
] as const;

export const FRECUENCIAS = [
  { value: 15, label: 'Cada 15 minutos' },
  { value: 30, label: 'Cada 30 minutos' },
  { value: 60, label: 'Cada hora' },
  { value: 120, label: 'Cada 2 horas' },
  { value: 240, label: 'Cada 4 horas' },
  { value: 480, label: 'Cada 8 horas' },
  { value: 720, label: 'Cada 12 horas' },
  { value: 1440, label: 'Cada 24 horas' }
] as const;

export const PRIORIDADES = [
  { value: 'alta', label: 'Alta', color: '#f44336' },
  { value: 'media', label: 'Media', color: '#ff9800' },
  { value: 'baja', label: 'Baja', color: '#4caf50' }
] as const;

export const ESTADOS_SPIDER = [
  { value: 'activo', label: 'Activo', color: '#4caf50' },
  { value: 'inactivo', label: 'Inactivo', color: '#9e9e9e' },
  { value: 'error', label: 'Error', color: '#f44336' },
  { value: 'mantenimiento', label: 'Mantenimiento', color: '#ff9800' }
] as const;

export const METODOS_EXTRACCION = [
  { value: 'css', label: 'Selectores CSS' },
  { value: 'xpath', label: 'XPath' },
  { value: 'regex', label: 'Expresiones Regulares' },
  { value: 'ai', label: 'Extracción con IA' }
] as const;

export const FORMATOS_SALIDA = [
  { value: 'json', label: 'JSON' },
  { value: 'csv', label: 'CSV' },
  { value: 'xml', label: 'XML' },
  { value: 'database', label: 'Base de Datos' }
] as const;

// Tipos TypeScript para validación estricta
export type AreaGeografica = typeof AREAS_GEOGRAFICAS[number];
export type PaisHispanidad = typeof PAISES_HISPANIDAD[number];
export type Region = keyof typeof REGIONES;
export type TipoMedio = typeof TIPOS_MEDIO[number]['value'];
export type Frecuencia = typeof FRECUENCIAS[number]['value'];
export type Prioridad = typeof PRIORIDADES[number]['value'];
export type EstadoSpider = typeof ESTADOS_SPIDER[number]['value'];
export type MetodoExtraccion = typeof METODOS_EXTRACCION[number]['value'];
export type FormatoSalida = typeof FORMATOS_SALIDA[number]['value'];

// Helper functions para validaciones y UI
export const esRegion = (area: string): area is Region => {
  return area in REGIONES;
};

export const esPaisHispanidad = (area: string): area is PaisHispanidad => {
  return PAISES_HISPANIDAD.includes(area as PaisHispanidad);
};

export const getDescripcionArea = (area: AreaGeografica): string => {
  if (esRegion(area)) {
    return REGIONES[area];
  }
  return `País: ${area}`;
};

// Opciones organizadas para dropdowns de UI
export const OPCIONES_AREAS_ORGANIZADAS = [
  {
    group: 'Regiones',
    items: Object.keys(REGIONES).map(key => ({
      value: key,
      label: key,
      description: REGIONES[key as Region]
    }))
  },
  {
    group: 'Países de la Hispanidad',
    items: PAISES_HISPANIDAD.map(pais => ({
      value: pais,
      label: pais,
      description: `País: ${pais}`
    }))
  }
] as const;