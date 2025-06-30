// Helpers de validación para tiempo real y feedback mejorado

export interface ValidationResult {
  isValid: boolean;
  message: string;
  severity: 'error' | 'warning' | 'info' | 'success';
  suggestions?: string[];
}

// Validación de URL
export const validateURL = (url: string): ValidationResult => {
  if (!url) {
    return {
      isValid: false,
      message: 'URL es requerida',
      severity: 'error'
    };
  }

  // Normalizar URL
  const normalizedUrl = normalizeURL(url);
  
  try {
    const urlObj = new URL(normalizedUrl);
    
    // Verificar protocolo
    if (!['http:', 'https:'].includes(urlObj.protocol)) {
      return {
        isValid: false,
        message: 'URL debe usar protocolo HTTP o HTTPS',
        severity: 'error',
        suggestions: [`https://${url.replace(/^[^:]+:\/\//, '')}`]
      };
    }

    // Verificar dominio válido
    if (!urlObj.hostname || urlObj.hostname.length < 3) {
      return {
        isValid: false,
        message: 'Dominio no válido',
        severity: 'error'
      };
    }

    // Advertencia para IPs
    if (/^\d+\.\d+\.\d+\.\d+$/.test(urlObj.hostname)) {
      return {
        isValid: true,
        message: 'URL con IP detectada - recomendamos usar dominio',
        severity: 'warning'
      };
    }

    // Verificar TLD básico
    const parts = urlObj.hostname.split('.');
    if (parts.length < 2 || parts[parts.length - 1].length < 2) {
      return {
        isValid: false,
        message: 'Dominio debe tener extensión válida (.com, .es, etc.)',
        severity: 'error'
      };
    }

    return {
      isValid: true,
      message: 'URL válida',
      severity: 'success'
    };
  } catch (error) {
    return {
      isValid: false,
      message: 'Formato de URL no válido',
      severity: 'error',
      suggestions: [
        url.startsWith('http') ? url : `https://${url}`,
        `https://www.${url.replace(/^(https?:\/\/)?(www\.)?/, '')}`
      ]
    };
  }
};

// Normalización de URL simple (según plan original)
export const normalizeURL = (url: string): string => {
  if (!url) return '';
  
  // Limpiar espacios en blanco
  url = url.trim();
  
  // Agregar protocolo HTTPS si falta
  if (!url.match(/^https?:\/\//)) {
    url = `https://${url}`;
  }
  
  // Convertir HTTP a HTTPS por seguridad
  if (url.startsWith('http://')) {
    url = url.replace('http://', 'https://');
  }
  
  // Remover barras finales innecesarias
  url = url.replace(/\/$/, '');
  
  return url;
};

// Validación de nombre de medio
export const validateMedioName = (name: string): ValidationResult => {
  if (!name) {
    return {
      isValid: false,
      message: 'Nombre del medio es requerido',
      severity: 'error'
    };
  }

  if (name.length < 2) {
    return {
      isValid: false,
      message: 'Nombre debe tener al menos 2 caracteres',
      severity: 'error'
    };
  }

  if (name.length > 50) {
    return {
      isValid: false,
      message: 'Nombre muy largo (máximo 50 caracteres)',
      severity: 'error'
    };
  }

  // Verificar caracteres especiales problemáticos
  if (/[<>\"'&]/.test(name)) {
    return {
      isValid: false,
      message: 'Nombre no puede contener caracteres especiales (<>\"\'&)',
      severity: 'error'
    };
  }

  // Sugerir mejoras
  const suggestions: string[] = [];
  
  // Capitalización
  const capitalized = name.replace(/\b\w/g, l => l.toUpperCase());
  if (capitalized !== name && name !== name.toUpperCase()) {
    suggestions.push(`Sugerencia: "${capitalized}"`);
  }

  // Verificar si es muy genérico
  const genericTerms = ['periódico', 'diario', 'noticias', 'medio', 'prensa'];
  if (genericTerms.some(term => name.toLowerCase().includes(term))) {
    return {
      isValid: true,
      message: 'Nombre válido, pero considere ser más específico',
      severity: 'warning',
      suggestions: suggestions.length > 0 ? suggestions : ['Ej: "El País", "ABC", "La Vanguardia"']
    };
  }

  return {
    isValid: true,
    message: suggestions.length > 0 ? 'Nombre válido' : 'Excelente nombre',
    severity: 'success',
    suggestions
  };
};

// Validación de sección
export const validateSection = (section: string): ValidationResult => {
  if (!section) {
    return {
      isValid: false,
      message: 'Sección es requerida',
      severity: 'error'
    };
  }

  if (section.length < 2) {
    return {
      isValid: false,
      message: 'Sección debe tener al menos 2 caracteres',
      severity: 'error'
    };
  }

  // Secciones comunes para sugerir
  const commonSections = [
    'portada', 'nacional', 'internacional', 'deportes', 'economía', 
    'tecnología', 'cultura', 'sociedad', 'política', 'local'
  ];

  const lowerSection = section.toLowerCase();
  const isCommon = commonSections.includes(lowerSection);

  if (isCommon) {
    return {
      isValid: true,
      message: 'Sección estándar reconocida',
      severity: 'success'
    };
  }

  // Buscar similares
  const similar = commonSections.filter(s => 
    s.includes(lowerSection) || lowerSection.includes(s)
  );

  if (similar.length > 0) {
    return {
      isValid: true,
      message: 'Sección válida',
      severity: 'info',
      suggestions: similar.map(s => `¿Quizás "${s}"?`)
    };
  }

  return {
    isValid: true,
    message: 'Sección personalizada válida',
    severity: 'info'
  };
};

// Validación de área geográfica
export const validateAreaGeografica = (area: string): ValidationResult => {
  if (!area) {
    return {
      isValid: false,
      message: 'Área geográfica es requerida',
      severity: 'error'
    };
  }

  const validAreas = [
    'españa', 'madrid', 'barcelona', 'valencia', 'sevilla', 'bilbao',
    'andalucía', 'cataluña', 'valencia', 'galicia', 'país vasco',
    'castilla-la mancha', 'castilla y león', 'aragón', 'murcia',
    'extremadura', 'asturias', 'cantabria', 'navarra', 'la rioja',
    'baleares', 'canarias', 'ceuta', 'melilla',
    'internacional', 'europa', 'latinoamérica', 'américa', 'asia', 'áfrica'
  ];

  const lowerArea = area.toLowerCase();
  const isValid = validAreas.some(valid => 
    valid === lowerArea || valid.includes(lowerArea) || lowerArea.includes(valid)
  );

  if (isValid) {
    return {
      isValid: true,
      message: 'Área geográfica reconocida',
      severity: 'success'
    };
  }

  // Buscar similares
  const similar = validAreas.filter(v => {
    const distance = levenshteinDistance(v, lowerArea);
    return distance <= 2 && distance > 0;
  }).slice(0, 3);

  return {
    isValid: true,
    message: 'Área geográfica personalizada',
    severity: 'info',
    suggestions: similar.length > 0 ? similar.map(s => `¿Quizás "${s}"?`) : undefined
  };
};

// Validación de frecuencia
export const validateFrequency = (frequency: number): ValidationResult => {
  if (!frequency || frequency <= 0) {
    return {
      isValid: false,
      message: 'Frecuencia debe ser mayor a 0',
      severity: 'error'
    };
  }

  if (frequency < 15) {
    return {
      isValid: true,
      message: 'Frecuencia muy alta - puede generar mucha carga',
      severity: 'warning',
      suggestions: ['Considere 30-60 minutos para mejores resultados']
    };
  }

  if (frequency > 1440) { // Más de 24 horas
    return {
      isValid: true,
      message: 'Frecuencia muy baja - puede perder noticias',
      severity: 'warning',
      suggestions: ['Recomendado: 60-480 minutos para noticias regulares']
    };
  }

  // Frecuencias recomendadas
  const recommendedFreqs = [30, 60, 120, 240, 480];
  if (recommendedFreqs.includes(frequency)) {
    return {
      isValid: true,
      message: 'Frecuencia optimizada',
      severity: 'success'
    };
  }

  return {
    isValid: true,
    message: 'Frecuencia válida',
    severity: 'info'
  };
};

// Utilidad: Distancia de Levenshtein simple
function levenshteinDistance(str1: string, str2: string): number {
  const matrix = [];
  
  for (let i = 0; i <= str2.length; i++) {
    matrix[i] = [i];
  }
  
  for (let j = 0; j <= str1.length; j++) {
    matrix[0][j] = j;
  }
  
  for (let i = 1; i <= str2.length; i++) {
    for (let j = 1; j <= str1.length; j++) {
      if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1,
          matrix[i][j - 1] + 1,
          matrix[i - 1][j] + 1
        );
      }
    }
  }
  
  return matrix[str2.length][str1.length];
}

// Detectar duplicados potenciales
export const checkForDuplicates = async (url: string, medio: string): Promise<ValidationResult> => {
  // Simulación de verificación de duplicados
  // En implementación real, esto consultaría la API
  const domain = new URL(normalizeURL(url)).hostname;
  
  // Simulación de base de datos local
  const existingSpiders = [
    { domain: 'elpais.com', medio: 'El País' },
    { domain: 'abc.es', medio: 'ABC' },
    { domain: 'elmundo.es', medio: 'El Mundo' }
  ];
  
  const duplicate = existingSpiders.find(spider => 
    spider.domain === domain || 
    spider.medio.toLowerCase() === medio.toLowerCase()
  );
  
  if (duplicate) {
    return {
      isValid: false,
      message: `Ya existe un monitor para ${duplicate.medio} (${duplicate.domain})`,
      severity: 'warning',
      suggestions: [
        'Verificar si el monitor existente cubre esta sección',
        'Usar una sección específica diferente',
        'Contactar administrador si necesita reemplazar'
      ]
    };
  }
  
  return {
    isValid: true,
    message: 'No se detectaron duplicados',
    severity: 'success'
  };
};

// Validación en tiempo real completa
export const validateFormField = async (
  field: string, 
  value: any, 
  formData?: Record<string, any>
): Promise<ValidationResult> => {
  switch (field) {
    case 'url':
      return validateURL(value);
    case 'medio':
      return validateMedioName(value);
    case 'seccion':
      return validateSection(value);
    case 'area_geografica':
      return validateAreaGeografica(value);
    case 'frecuencia_minutos':
      return validateFrequency(value);
    case 'duplicate_check':
      if (formData?.url && formData?.medio) {
        return await checkForDuplicates(formData.url, formData.medio);
      }
      break;
    default:
      return {
        isValid: true,
        message: 'Campo válido',
        severity: 'info'
      };
  }

  return {
    isValid: true,
    message: 'Campo válido',
    severity: 'info'
  };
};