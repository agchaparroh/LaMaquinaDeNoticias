// Text formatting utilities
// Utilidades para formateo de texto

/**
 * Truncate text to specified length with ellipsis
 * Trunca texto a longitud especificada con puntos suspensivos
 */
export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) {
    return text;
  }
  
  return text.substring(0, maxLength - 3) + '...';
};

/**
 * Capitalize first letter of string
 * Capitaliza la primera letra del string
 */
export const capitalizeFirst = (text: string): string => {
  if (!text) return text;
  return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
};

/**
 * Convert text to title case
 * Convierte texto a formato título
 */
export const toTitleCase = (text: string): string => {
  return text
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
};

/**
 * Extract domain from URL
 * Extrae dominio de una URL
 */
export const extractDomain = (url: string): string => {
  try {
    const urlObj = new URL(url);
    return urlObj.hostname.replace(/^www\./, '');
  } catch {
    return url;
  }
};

/**
 * Format importance level to text
 * Formatea nivel de importancia a texto
 */
export const formatImportanceText = (importance: number): string => {
  if (importance <= 2) return 'Muy Baja';
  if (importance <= 4) return 'Baja';
  if (importance <= 6) return 'Media';
  if (importance <= 8) return 'Alta';
  return 'Muy Alta';
};

/**
 * Get importance color for Material UI
 * Obtiene color de importancia para Material UI
 */
export const getImportanceColor = (importance: number): 'success' | 'warning' | 'error' => {
  if (importance <= 4) return 'success';
  if (importance <= 7) return 'warning';
  return 'error';
};

/**
 * Highlight search terms in text
 * Resalta términos de búsqueda en texto
 */
export const highlightSearchTerms = (text: string, searchTerm: string): string => {
  if (!searchTerm) return text;
  
  const regex = new RegExp(`(${searchTerm})`, 'gi');
  return text.replace(regex, '<mark>$1</mark>');
};

/**
 * Convert bytes to human readable format
 * Convierte bytes a formato legible
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * Generate initials from name
 * Genera iniciales de un nombre
 */
export const getInitials = (name: string): string => {
  return name
    .split(' ')
    .map(word => word.charAt(0))
    .slice(0, 2)
    .join('')
    .toUpperCase();
};

/**
 * Clean and normalize text for search
 * Limpia y normaliza texto para búsqueda
 */
export const normalizeForSearch = (text: string): string => {
  return text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '') // Remove accents
    .replace(/[^\w\s]/g, '') // Remove special characters
    .trim();
};
