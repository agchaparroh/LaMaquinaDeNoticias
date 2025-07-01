// Temporalmente simplificado para build Docker
import Papa from 'papaparse';

export interface CSVRow {
  medio: string;
  seccion: string;
  url: string;
  area_geografica: string;
  tipo_medio: 'diario' | 'revista' | 'agencia';
  frecuencia_minutos?: number;
  rss_url?: string;
}

export interface CSVParseResult {
  data: CSVRow[];
  errors: any[];
  meta: any;
}

export const parseCSVFile = (file: File): Promise<CSVParseResult> => {
  return new Promise((resolve) => {
    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      complete: (results: any) => {
        resolve({
          data: results.data || [],
          errors: results.errors || [],
          meta: results.meta || {}
        });
      },
      error: (error: any) => {
        resolve({
          data: [],
          errors: [error],
          meta: {}
        });
      }
    });
  });
};

export const validateCSV = (data: any[]): { isValid: boolean; errors: string[] } => {
  return { isValid: true, errors: [] };
};