// Tipos para el sistema de feedback editorial
export type FeedbackType = 'IMPORTANCE' | 'FACTUAL_ERROR' | 'GENERAL';

export interface Feedback {
  hechoId: number;
  type: FeedbackType;
  isFalse?: boolean;
  importance?: number;
  comment?: string;
}

export interface FeedbackResponse {
  success: boolean;
  message: string;
  data?: any;
}

export interface FeedbackSubmission {
  hechoId: number;
  evaluacionEditorial: 'verdadero' | 'falso' | 'necesita_verificacion' | null;
  importancia: number;
  comentarios?: string;
  evaluadoPor?: string;
  fechaEvaluacion?: string;
}

// Estados de confirmación
export interface ConfirmationDialogState {
  isOpen: boolean;
  title: string;
  message: string;
  confirmText: string;
  cancelText: string;
  severity?: 'info' | 'warning' | 'error' | 'success';
  action?: () => void;
}

// Props para notificaciones
export interface NotificationProps {
  message: string;
  severity: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
}

// Request types for API
export interface ImportanciaFeedbackRequest {
  hechoId: number;
  importancia: number;
}

export interface ImportanciaFeedbackResponse {
  success: boolean;
  message: string;
  hechoId: number;
  importancia: number;
  updatedAt: string;
}

export interface FalseFeedbackRequest {
  hechoId: number;
  isFalse: boolean;
  justification?: string;
}

export interface GeneralFeedbackRequest {
  hechoId: number;
  comment: string;
  type?: FeedbackType;
}

export interface EvaluacionEditorialRequest {
  hechoId: number;
  evaluacion: 'verdadero' | 'falso' | 'necesita_verificacion';
  comentarios?: string;
  evaluadoPor?: string;
}

export interface EvaluacionEditorialResponse {
  success: boolean;
  message: string;
  hechoId: number;
  evaluacion: string;
  evaluadoPor?: string;
  fechaEvaluacion: string;
}