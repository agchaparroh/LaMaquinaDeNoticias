import { useState, useCallback } from 'react';
import type { Feedback, FeedbackResponse } from '@/types/domain';

// Mock API para desarrollo
const mockSubmitFeedback = async (feedback: Feedback): Promise<FeedbackResponse> => {
  console.log('📤 Mock feedback submission:', feedback);
  
  // Simular delay de API
  await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 1000));
  
  // Simular error ocasional (10% de probabilidad)
  if (Math.random() < 0.1) {
    throw new Error('Error de red: No se pudo conectar con el servidor');
  }
  
  return {
    success: true,
    message: 'Feedback enviado correctamente',
    data: {
      feedbackId: Date.now(),
      timestamp: new Date().toISOString()
    }
  };
};

const mockUpdateImportance = async (hechoId: number, importance: number): Promise<FeedbackResponse> => {
  console.log(`📊 Mock importance update for hecho ${hechoId}: ${importance}`);
  
  // Simular delay de API más corto para actualizaciones
  await new Promise(resolve => setTimeout(resolve, 500 + Math.random() * 500));
  
  // Simular error ocasional (5% de probabilidad)
  if (Math.random() < 0.05) {
    throw new Error('Error al actualizar importancia');
  }
  
  return {
    success: true,
    message: `Importancia actualizada a ${importance}`,
    data: {
      hechoId,
      newImportance: importance,
      timestamp: new Date().toISOString()
    }
  };
};

const mockSubmitEvaluacion = async (hechoId: number, evaluacion: any): Promise<FeedbackResponse> => {
  console.log(`📝 Mock evaluacion submission for hecho ${hechoId}:`, evaluacion);
  
  // Simular delay de API
  await new Promise(resolve => setTimeout(resolve, 800 + Math.random() * 700));
  
  // Simular error ocasional (7% de probabilidad)
  if (Math.random() < 0.07) {
    throw new Error('Error al enviar evaluación editorial');
  }
  
  return {
    success: true,
    message: 'Evaluación enviada correctamente',
    data: {
      hechoId,
      evaluacion,
      timestamp: new Date().toISOString()
    }
  };
};

export const useFeedback = () => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastSubmission, setLastSubmission] = useState<{
    feedback: Feedback;
    timestamp: Date;
  } | null>(null);
  
  // Estado por hecho individual
  const [submittingStates, setSubmittingStates] = useState<Record<number, {
    type: 'importancia' | 'evaluacion' | 'general';
    isSubmitting: boolean;
  }>>({});

  // Limpiar error después de un tiempo
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const submitFeedback = useCallback(async (feedback: Feedback): Promise<boolean> => {
    setIsSubmitting(true);
    setError(null);
    
    try {
      const response = await mockSubmitFeedback(feedback);
      
      if (response.success) {
        setLastSubmission({
          feedback,
          timestamp: new Date()
        });
        return true;
      } else {
        setError(response.message || 'Error desconocido al enviar feedback');
        return false;
      }
    } catch (err) {
      const errorMessage = err instanceof Error 
        ? err.message 
        : 'Error al enviar feedback. Por favor, intente nuevamente.';
      setError(errorMessage);
      console.error('Feedback submission error:', err);
      return false;
    } finally {
      setIsSubmitting(false);
    }
  }, []);
  
  const updateImportance = useCallback(async (hechoId: number, importance: number): Promise<boolean> => {
    setSubmittingStates(prev => ({
      ...prev,
      [hechoId]: { type: 'importancia', isSubmitting: true }
    }));
    setError(null);
    
    try {
      const response = await mockUpdateImportance(hechoId, importance);
      
      if (response.success) {
        return true;
      } else {
        setError(response.message || 'Error desconocido al actualizar importancia');
        return false;
      }
    } catch (err) {
      const errorMessage = err instanceof Error 
        ? err.message 
        : 'Error al actualizar importancia. Por favor, intente nuevamente.';
      setError(errorMessage);
      console.error('Importance update error:', err);
      return false;
    } finally {
      setSubmittingStates(prev => {
        const newState = { ...prev };
        delete newState[hechoId];
        return newState;
      });
    }
  }, []);

  // Nuevos métodos para compatibilidad con DashboardPage
  const submitImportanciaFeedback = useCallback(async (hechoId: number, importance: number): Promise<boolean> => {
    return updateImportance(hechoId, importance);
  }, [updateImportance]);

  const submitEvaluacionEditorial = useCallback(async (hechoId: number, evaluacion: any): Promise<boolean> => {
    setSubmittingStates(prev => ({
      ...prev,
      [hechoId]: { type: 'evaluacion', isSubmitting: true }
    }));
    setError(null);
    
    try {
      const response = await mockSubmitEvaluacion(hechoId, evaluacion);
      
      if (response.success) {
        return true;
      } else {
        setError(response.message || 'Error desconocido al enviar evaluación');
        return false;
      }
    } catch (err) {
      const errorMessage = err instanceof Error 
        ? err.message 
        : 'Error al enviar evaluación. Por favor, intente nuevamente.';
      setError(errorMessage);
      console.error('Evaluacion submission error:', err);
      return false;
    } finally {
      setSubmittingStates(prev => {
        const newState = { ...prev };
        delete newState[hechoId];
        return newState;
      });
    }
  }, []);

  // Función helper para crear feedback de importancia
  const createImportanceFeedback = useCallback((hechoId: number, importance: number): Feedback => {
    return {
      hechoId,
      type: 'IMPORTANCE',
      importance,
      comment: `Importancia ajustada a ${importance}/10`
    };
  }, []);

  // Función helper para crear feedback de evaluación
  const createEvaluationFeedback = useCallback((hechoId: number, isFalse: boolean, comment?: string): Feedback => {
    return {
      hechoId,
      type: 'FACTUAL_ERROR',
      isFalse,
      comment
    };
  }, []);

  // Verificar si un hecho específico está siendo procesado
  const isHechoSubmitting = useCallback((hechoId: number, type?: 'importancia' | 'evaluacion'): boolean => {
    const state = submittingStates[hechoId];
    if (!state) return false;
    if (type) return state.type === type && state.isSubmitting;
    return state.isSubmitting;
  }, [submittingStates]);

  // Obtener mensaje de error para un hecho específico
  const getErrorMessage = useCallback((hechoId?: number): string | null => {
    // Por simplicidad, retornamos el error general
    // En una implementación real, podríamos tener errores por hecho
    return error;
  }, [error]);

  return {
    // Estado general
    error,
    lastSubmission,
    
    // Acciones principales
    submitFeedback,
    updateImportance,
    
    // Métodos para compatibilidad con DashboardPage
    submitImportanciaFeedback,
    submitEvaluacionEditorial,
    
    // Helpers
    createImportanceFeedback,
    createEvaluationFeedback,
    clearError,
    
    // Funciones de estado por hecho
    isSubmitting: isHechoSubmitting,
    getErrorMessage,
    
    // Estados computados
    hasRecentSubmission: lastSubmission && 
      (new Date().getTime() - lastSubmission.timestamp.getTime()) < 30000, // 30 segundos
  };
};