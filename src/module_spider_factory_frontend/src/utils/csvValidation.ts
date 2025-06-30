import * as yup from 'yup';
import Papa from 'papaparse';
import { AREAS_GEOGRAFICAS, TIPOS_MEDIO } from '../constants/areas';

// Según SECCIÓN 2.4 - Agregar validación de CSV
// - Validar columnas obligatorias
// - Validar valores de tipo_medio
// - Validar URLs
// - Mostrar errores por fila

export interface CSVRow {
  medio: string;
  seccion: string;
  url: string;
  area_geografica: string;
  tipo_medio: string;
  frecuencia_minutos: number;
  rss_url?: string;
}

export interface CSVValidationError {
  row: number;
  field: string;
  message: string;
  value: any;
}

export interface CSVValidationResult {
  isValid: boolean;
  validRows: CSVRow[];
  errors: CSVValidationError[];
  totalRows: number;
  skippedRows: number;
  summary: {
    totalProcessed: number;
    validCount: number;
    errorCount: number;
    duplicateCount: number;
  };
}

export interface CSVParseResult {
  success: boolean;
  data?: any[];
  errors?: Papa.ParseError[];
  meta?: Papa.ParseMeta;
}

// Schema para validar cada fila del CSV usando PapaParse + Yup
const csvRowSchema = yup.object({
  medio: yup
    .string()
    .trim()
    .min(2, 'El nombre del medio debe tener al menos 2 caracteres')
    .max(100, 'El nombre del medio no puede exceder 100 caracteres')
    .required('El medio es obligatorio'),
    
  seccion: yup
    .string()
    .trim()
    .min(2, 'La sección debe tener al menos 2 caracteres')
    .max(100, 'La sección no puede exceder 100 caracteres')
    .required('La sección es obligatoria'),
    
  url: yup
    .string()
    .trim()
    .url('URL inválida')
    .matches(
      /^https?:\/\/.+/,
      'La URL debe comenzar con http:// o https://'
    )
    .required('La URL es obligatoria'),
    
  area_geografica: yup
    .string()
    .trim()
    .oneOf(AREAS_GEOGRAFICAS, 'Área geográfica no válida')
    .required('El área geográfica es obligatoria'),
    
  tipo_medio: yup
    .string()
    .trim()
    .oneOf(
      TIPOS_MEDIO.map(t => t.value), 
      'Tipo de medio inválido. Valores válidos: diario, revista, agencia'
    )
    .required('El tipo de medio es obligatorio'),
    
  frecuencia_minutos: yup
    .number()
    .positive('La frecuencia debe ser un número positivo')
    .integer('La frecuencia debe ser un número entero')
    .min(15, 'La frecuencia mínima es 15 minutos')
    .max(1440, 'La frecuencia máxima es 1440 minutos (24 horas)')
    .required('La frecuencia es obligatoria'),
    
  rss_url: yup
    .string()
    .trim()
    .url('URL del RSS inválida')
    .nullable()
    .transform((value) => value === '' ? null : value)
});

// Función para parsear CSV usando PapaParse
export const parseCSVFile = (file: File): Promise<CSVParseResult> => {
  return new Promise((resolve) => {
    Papa.parse(file, {
      header: true, // Primera fila como headers
      skipEmptyLines: 'greedy', // Saltar líneas vacías
      trimHeaders: true, // Limpiar espacios en headers
      dynamicTyping: true, // Convertir tipos automáticamente
      transform: (value: string, header: string) => {
        // Limpiar valores y convertir frecuencia_minutos a número
        if (header === 'frecuencia_minutos') {
          return value ? parseInt(value.toString(), 10) : null;
        }
        return typeof value === 'string' ? value.trim() : value;
      },
      complete: (results) => {
        resolve({
          success: results.errors.length === 0,
          data: results.data,
          errors: results.errors,
          meta: results.meta
        });
      },
      error: (error) => {
        resolve({
          success: false,
          errors: [error]
        });
      }
    });
  });
};

// Función para parsear CSV desde string usando PapaParse
export const parseCSVString = (csvContent: string): CSVParseResult => {
  const results = Papa.parse(csvContent, {
    header: true,
    skipEmptyLines: 'greedy',
    trimHeaders: true,
    dynamicTyping: true,
    transform: (value: string, header: string) => {
      if (header === 'frecuencia_minutos') {
        return value ? parseInt(value.toString(), 10) : null;
      }
      return typeof value === 'string' ? value.trim() : value;
    }
  });

  return {
    success: results.errors.length === 0,
    data: results.data,
    errors: results.errors,
    meta: results.meta
  };
};

// Función principal para validar CSV completo
export const validateCSV = async (
  file: File | string
): Promise<CSVValidationResult> => {
  const errors: CSVValidationError[] = [];
  const validRows: CSVRow[] = [];
  const duplicateTracker = new Set<string>();
  let skippedRows = 0;

  try {
    // Parsear el CSV
    const parseResult = typeof file === 'string' 
      ? parseCSVString(file)
      : await parseCSVFile(file);

    if (!parseResult.success || !parseResult.data) {
      // Errores de parsing
      parseResult.errors?.forEach((error, index) => {
        errors.push({
          row: error.row || index + 1,
          field: 'parsing',
          message: `Error de parsing: ${error.message}`,
          value: null
        });
      });

      return {
        isValid: false,
        validRows: [],
        errors,
        totalRows: 0,
        skippedRows: 0,
        summary: {
          totalProcessed: 0,
          validCount: 0,
          errorCount: errors.length,
          duplicateCount: 0
        }
      };
    }

    const rows = parseResult.data as any[];
    
    // Validar que el CSV tenga las columnas requeridas
    const requiredColumns = ['medio', 'seccion', 'url', 'area_geografica', 'tipo_medio', 'frecuencia_minutos'];
    const headers = parseResult.meta?.fields || Object.keys(rows[0] || {});
    const missingColumns = requiredColumns.filter(col => !headers.includes(col));
    
    if (missingColumns.length > 0) {
      errors.push({
        row: 0,
        field: 'estructura',
        message: `Faltan columnas obligatorias: ${missingColumns.join(', ')}`,
        value: headers
      });
    }

    // Validar cada fila
    for (let i = 0; i < rows.length; i++) {
      const row = rows[i];
      const rowNumber = i + 1;
      
      // Saltar filas vacías o incompletas
      if (!row || Object.values(row).every(val => !val)) {
        skippedRows++;
        continue;
      }

      try {
        // Validar con Yup schema
        const validatedRow = await csvRowSchema.validate(row, { 
          abortEarly: false,
          stripUnknown: true 
        });

        // Verificar duplicados (medio + sección)
        const duplicateKey = `${validatedRow.medio.toLowerCase()}::${validatedRow.seccion.toLowerCase()}`;
        if (duplicateTracker.has(duplicateKey)) {
          errors.push({
            row: rowNumber,
            field: 'duplicado',
            message: `Combinación de medio y sección ya existe: "${validatedRow.medio}" - "${validatedRow.seccion}"`,
            value: duplicateKey
          });
        } else {
          duplicateTracker.add(duplicateKey);
          validRows.push(validatedRow);
        }

      } catch (validationError: any) {
        if (validationError.inner) {
          // Errores múltiples de Yup
          validationError.inner.forEach((error: any) => {
            errors.push({
              row: rowNumber,
              field: error.path,
              message: error.message,
              value: row[error.path]
            });
          });
        } else {
          // Error único
          errors.push({
            row: rowNumber,
            field: validationError.path || 'unknown',
            message: validationError.message || 'Error de validación',
            value: row[validationError.path] || row
          });
        }
      }
    }

    const duplicateCount = rows.length - validRows.length - (errors.filter(e => e.field !== 'duplicado').length);

    return {
      isValid: errors.length === 0 && validRows.length > 0,
      validRows,
      errors,
      totalRows: rows.length,
      skippedRows,
      summary: {
        totalProcessed: rows.length - skippedRows,
        validCount: validRows.length,
        errorCount: errors.length,
        duplicateCount: Math.max(0, duplicateCount)
      }
    };

  } catch (error) {
    errors.push({
      row: 0,
      field: 'general',
      message: `Error general: ${error instanceof Error ? error.message : 'Error desconocido'}`,
      value: null
    });

    return {
      isValid: false,
      validRows: [],
      errors,
      totalRows: 0,
      skippedRows: 0,
      summary: {
        totalProcessed: 0,
        validCount: 0,
        errorCount: errors.length,
        duplicateCount: 0
      }
    };
  }
};

// Función para generar CSV template de ejemplo
export const generateCSVTemplate = (): string => {
  const templateData = [
    {
      medio: 'El País',
      seccion: 'Internacional',
      url: 'https://elpais.com/internacional',
      area_geografica: 'ESPAÑA',
      tipo_medio: 'diario',
      frecuencia_minutos: 60,
      rss_url: 'https://elpais.com/rss/internacional.xml'
    },
    {
      medio: 'La Nación',
      seccion: 'Política',
      url: 'https://lanacion.com.ar/politica',
      area_geografica: 'ARGENTINA',
      tipo_medio: 'diario',
      frecuencia_minutos: 30,
      rss_url: ''
    }
  ];

  return Papa.unparse(templateData, {
    header: true,
    delimiter: ',',
    quoteChar: '"',
    escapeChar: '"',
    newline: '\n'
  });
};

// Función para convertir datos validados de vuelta a CSV
export const exportValidatedRowsToCSV = (validRows: CSVRow[]): string => {
  return Papa.unparse(validRows, {
    header: true,
    delimiter: ',',
    quoteChar: '"',
    escapeChar: '"',
    newline: '\n'
  });
};

// Función para obtener estadísticas de validación
export const getValidationStats = (result: CSVValidationResult) => {
  const { summary, errors, totalRows } = result;
  
  return {
    processingRate: totalRows > 0 ? (summary.validCount / totalRows) * 100 : 0,
    errorRate: totalRows > 0 ? (summary.errorCount / totalRows) * 100 : 0,
    duplicateRate: totalRows > 0 ? (summary.duplicateCount / totalRows) * 100 : 0,
    mostCommonErrors: getMostCommonErrors(errors),
    fieldErrorStats: getFieldErrorStats(errors)
  };
};

// Helper para obtener errores más comunes
function getMostCommonErrors(errors: CSVValidationError[]): Array<{ message: string; count: number }> {
  const errorCounts = errors.reduce((acc, error) => {
    acc[error.message] = (acc[error.message] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return Object.entries(errorCounts)
    .map(([message, count]) => ({ message, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 5);
}

// Helper para obtener estadísticas de errores por campo
function getFieldErrorStats(errors: CSVValidationError[]): Array<{ field: string; count: number }> {
  const fieldCounts = errors.reduce((acc, error) => {
    acc[error.field] = (acc[error.field] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return Object.entries(fieldCounts)
    .map(([field, count]) => ({ field, count }))
    .sort((a, b) => b.count - a.count);
}

export default {
  parseCSVFile,
  parseCSVString,
  validateCSV,
  generateCSVTemplate,
  exportValidatedRowsToCSV,
  getValidationStats,
  csvRowSchema
};