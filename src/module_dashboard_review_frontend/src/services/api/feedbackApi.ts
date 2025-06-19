import apiClient from './apiClient';
import { env } from '@/utils/env';
import type { 
  ImportanciaFeedbackRequest,
  ImportanciaFeedbackResponse,
  EvaluacionEditorialRequest,
  EvaluacionEditorialResponse
} from '@/types/domain';

/**
 * Servicio API para operaciones de feedback editorial
 * Incluye implementaciones mock para desarrollo y calls reales para producción
 */
export const feedbackApi = {
  /**
   * Enviar feedback de importancia para un hecho
   */
  submitImportanciaFeedback: async (hechoId: number, request: ImportanciaFeedbackRequest) => {
    if (env.isDevelopment() && env.debug) {
      console.log('📝 Mock API: submitImportanciaFeedback', { hechoId, request });
      
      // Simular delay de procesamiento
      await new Promise(resolve => setTimeout(resolve, 1200));
      
      // Simular ocasionalmente un error para testing
      if (Math.random() < 0.1) {
        throw new Error('Error temporal en el servidor - intente nuevamente');
      }
      
      const mockResponse: ImportanciaFeedbackResponse = {
        id: Math.floor(Math.random() * 10000),
        hechoId: hechoId,
        nuevaImportancia: request.nuevaImportancia,
        importanciaAnterior: request.importanciaAnterior || 5,
        comentario: request.comentario,
        evaluadoPor: 'Usuario Mock',
        fechaEvaluacion: new Date().toISOString(),
        estado: 'aplicado'
      };
      
      return { data: mockResponse };
    }
    
    return apiClient.post(`/dashboard/feedback/hecho/${hechoId}/importancia_feedback`, request);
  },

  /**
   * Enviar evaluación editorial para un hecho
   */
  submitEvaluacionEditorial: async (hechoId: number, request: EvaluacionEditorialRequest) => {
    if (env.isDevelopment() && env.debug) {
      console.log('📝 Mock API: submitEvaluacionEditorial', { hechoId, request });
      
      // Simular delay de procesamiento
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Simular ocasionalmente un error para testing
      if (Math.random() < 0.05) {
        throw new Error('Error de validación - comentario requerido para evaluación negativa');
      }
      
      const mockResponse: EvaluacionEditorialResponse = {
        id: Math.floor(Math.random() * 10000),
        hechoId: hechoId,
        evaluacion: request.evaluacion,
        comentario: request.comentario,
        justificacion: request.justificacion,
        fuentesConsultadas: request.fuentesConsultadas || [],
        evaluadoPor: 'Usuario Mock',
        fechaEvaluacion: new Date().toISOString(),
        estado: 'registrado',
        requiereRevision: request.evaluacion === 'falso'
      };
      
      return { data: mockResponse };
    }
    
    return apiClient.post(`/dashboard/feedback/hecho/${hechoId}/evaluacion_editorial`, request);
  },

  /**
   * Obtener historial de feedback para un hecho específico
   */
  getFeedbackHistory: async (hechoId: number) => {
    if (env.isDevelopment() && env.debug) {
      console.log('📝 Mock API: getFeedbackHistory', hechoId);
      
      await new Promise(resolve => setTimeout(resolve, 600));
      
      // Generar historial mock aleatorio
      const historialItems = [];
      const numItems = Math.floor(Math.random() * 4) + 1; // 1-4 items
      
      for (let i = 0; i < numItems; i++) {
        const tipoFeedback = Math.random() > 0.5 ? 'importancia' : 'evaluacion';
        const fechaBase = new Date();
        fechaBase.setDate(fechaBase.getDate() - i * 2); // Espaciar por días
        
        if (tipoFeedback === 'importancia') {
          historialItems.push({
            id: Math.floor(Math.random() * 1000),
            tipo: 'importancia_feedback',
            hechoId: hechoId,
            nuevaImportancia: Math.floor(Math.random() * 10) + 1,
            importanciaAnterior: Math.floor(Math.random() * 10) + 1,
            comentario: `Ajuste de importancia ${i + 1}`,
            evaluadoPor: `Editor ${i + 1}`,
            fechaEvaluacion: fechaBase.toISOString(),
            estado: 'aplicado'
          });
        } else {
          const evaluaciones = ['verdadero', 'falso', 'necesita_verificacion'];
          const evaluacion = evaluaciones[Math.floor(Math.random() * evaluaciones.length)];
          
          historialItems.push({
            id: Math.floor(Math.random() * 1000),
            tipo: 'evaluacion_editorial', 
            hechoId: hechoId,
            evaluacion: evaluacion,
            comentario: `Evaluación editorial ${i + 1}`,
            evaluadoPor: `Editor ${i + 1}`,
            fechaEvaluacion: fechaBase.toISOString(),
            estado: 'registrado'
          });
        }
      }
      
      return { data: historialItems };
    }
    
    return apiClient.get(`/dashboard/feedback/hecho/${hechoId}/historial`);
  },

  /**
   * Obtener estadísticas de feedback del usuario
   */
  getUserFeedbackStats: async () => {
    if (env.isDevelopment() && env.debug) {
      console.log('📝 Mock API: getUserFeedbackStats');
      
      await new Promise(resolve => setTimeout(resolve, 500));
      
      return {
        data: {
          totalFeedbacks: Math.floor(Math.random() * 100) + 50,
          feedbacksHoy: Math.floor(Math.random() * 10) + 1,
          feedbacksSemana: Math.floor(Math.random() * 50) + 20,
          evaluacionesRealizadas: {
            verdadero: Math.floor(Math.random() * 30) + 10,
            falso: Math.floor(Math.random() * 15) + 5,
            necesita_verificacion: Math.floor(Math.random() * 20) + 8
          },
          importanciaPromedio: Math.round((Math.random() * 4 + 6) * 10) / 10, // 6.0-10.0
          tiempoPromedioEvaluacion: Math.floor(Math.random() * 120) + 60 // 60-180 segundos
        }
      };
    }
    
    return apiClient.get('/dashboard/feedback/stats/usuario');
  },

  /**
   * Descartar/cancelar feedback pendiente
   */
  cancelFeedback: async (feedbackId: number) => {
    if (env.isDevelopment() && env.debug) {
      console.log('📝 Mock API: cancelFeedback', feedbackId);
      
      await new Promise(resolve => setTimeout(resolve, 400));
      
      return {
        data: {
          id: feedbackId,
          estado: 'cancelado',
          fechaCancelacion: new Date().toISOString(),
          mensaje: 'Feedback cancelado exitosamente'
        }
      };
    }
    
    return apiClient.delete(`/dashboard/feedback/${feedbackId}`);
  }
};