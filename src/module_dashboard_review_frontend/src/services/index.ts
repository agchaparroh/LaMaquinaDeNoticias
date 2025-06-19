/**
 * Barrel exports para todos los servicios
 * Punto de entrada centralizado para servicios de la aplicación
 */

// API Services
export * from './api';

// Servicios específicos exportados individualmente para conveniencia
export { dashboardApi } from './api/dashboardApi';
export { feedbackApi } from './api/feedbackApi';
export { apiClient } from './api';