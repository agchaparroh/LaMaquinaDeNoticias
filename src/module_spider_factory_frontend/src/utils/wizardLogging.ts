// Sistema de logging estructurado para el wizard
interface WizardLogEvent {
  event: string;
  step: number;
  stepName: string;
  timestamp: string;
  userId?: string;
  sessionId: string;
  data?: any;
  duration?: number;
  error?: any;
}

class WizardLogger {
  private sessionId: string;
  private startTime: number;
  private stepStartTime: number;
  private userId?: string;

  constructor() {
    this.sessionId = this.generateSessionId();
    this.startTime = Date.now();
    this.stepStartTime = Date.now();
    this.userId = this.getUserId();
  }

  private generateSessionId(): string {
    return `wizard_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private getUserId(): string | undefined {
    // Intentar obtener ID de usuario desde localStorage o contexto
    try {
      return localStorage.getItem('userId') || undefined;
    } catch {
      return undefined;
    }
  }

  private createEvent(event: string, step: number, stepName: string, data?: any, error?: any): WizardLogEvent {
    return {
      event,
      step,
      stepName,
      timestamp: new Date().toISOString(),
      userId: this.userId,
      sessionId: this.sessionId,
      duration: Date.now() - this.stepStartTime,
      data,
      error
    };
  }

  private log(logEvent: WizardLogEvent): void {
    // Log a consola en desarrollo
    if (import.meta.env.DEV) {
      const emoji = this.getEventEmoji(logEvent.event);
      console.log(
        `${emoji} [Wizard] ${logEvent.event}:`,
        {
          step: `${logEvent.step + 1} - ${logEvent.stepName}`,
          duration: `${logEvent.duration}ms`,
          session: logEvent.sessionId,
          ...logEvent.data,
          ...(logEvent.error && { error: logEvent.error })
        }
      );
    }

    // En producción, enviar a servicio de logging
    if (import.meta.env.PROD) {
      this.sendToLoggingService(logEvent);
    }

    // Guardar en localStorage para debugging
    this.saveToLocalStorage(logEvent);
  }

  private getEventEmoji(event: string): string {
    const emojis: Record<string, string> = {
      'wizard_started': '🚀',
      'step_entered': '👆',
      'step_completed': '✅',
      'validation_error': '❌',
      'url_validated': '🔗',
      'duplicate_detected': '⚠️',
      'analysis_started': '🔍',
      'analysis_completed': '📊',
      'generation_started': '⚙️',
      'generation_completed': '🎉',
      'wizard_completed': '🏁',
      'wizard_abandoned': '🚪',
      'error_occurred': '💥'
    };
    return emojis[event] || '📝';
  }

  private async sendToLoggingService(logEvent: WizardLogEvent): Promise<void> {
    try {
      // Aquí se enviaría a un servicio real de logging
      await fetch('/api/logging/wizard', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(logEvent)
      });
    } catch (error) {
      console.error('Failed to send log to service:', error);
    }
  }

  private saveToLocalStorage(logEvent: WizardLogEvent): void {
    try {
      const existingLogs = JSON.parse(localStorage.getItem('wizard_logs') || '[]');
      existingLogs.push(logEvent);
      
      // Mantener solo los últimos 100 eventos
      if (existingLogs.length > 100) {
        existingLogs.splice(0, existingLogs.length - 100);
      }
      
      localStorage.setItem('wizard_logs', JSON.stringify(existingLogs));
    } catch (error) {
      console.error('Failed to save log to localStorage:', error);
    }
  }

  // Métodos públicos para logging de eventos específicos
  wizardStarted(): void {
    this.stepStartTime = Date.now();
    this.log(this.createEvent('wizard_started', 0, 'Inicio', {
      userAgent: navigator.userAgent,
      viewport: `${window.innerWidth}x${window.innerHeight}`,
      language: navigator.language
    }));
  }

  stepEntered(step: number, stepName: string, data?: any): void {
    this.stepStartTime = Date.now();
    this.log(this.createEvent('step_entered', step, stepName, data));
  }

  stepCompleted(step: number, stepName: string, data?: any): void {
    this.log(this.createEvent('step_completed', step, stepName, data));
  }

  validationError(step: number, stepName: string, field: string, error: string): void {
    this.log(this.createEvent('validation_error', step, stepName, { field, error }));
  }

  urlValidated(step: number, stepName: string, url: string, isValid: boolean, info?: any): void {
    this.log(this.createEvent('url_validated', step, stepName, { 
      url, 
      isValid, 
      domain: isValid ? new URL(url).hostname : null,
      ...info 
    }));
  }

  duplicateDetected(step: number, stepName: string, url: string, existingSpider: any): void {
    this.log(this.createEvent('duplicate_detected', step, stepName, { 
      url, 
      existingSpider: existingSpider.spider_name 
    }));
  }

  analysisStarted(step: number, stepName: string, analysisData: any): void {
    this.log(this.createEvent('analysis_started', step, stepName, analysisData));
  }

  analysisCompleted(step: number, stepName: string, result: any): void {
    this.log(this.createEvent('analysis_completed', step, stepName, {
      strategy: result.strategy,
      hasRSS: result.rss_detected,
      estimatedArticles: result.estimated_articles,
      renderingRequired: result.javascript_required
    }));
  }

  generationStarted(step: number, stepName: string, config: any): void {
    this.log(this.createEvent('generation_started', step, stepName, config));
  }

  generationCompleted(step: number, stepName: string, result: any): void {
    this.log(this.createEvent('generation_completed', step, stepName, {
      spiderId: result.spider_id,
      strategy: result.strategy,
      totalDuration: Date.now() - this.startTime
    }));
  }

  wizardCompleted(finalData: any): void {
    this.log(this.createEvent('wizard_completed', 5, 'Completado', {
      ...finalData,
      totalDuration: Date.now() - this.startTime,
      totalSteps: 5
    }));
  }

  wizardAbandoned(step: number, stepName: string): void {
    this.log(this.createEvent('wizard_abandoned', step, stepName, {
      durationBeforeAbandon: Date.now() - this.startTime
    }));
  }

  errorOccurred(step: number, stepName: string, error: any, context?: any): void {
    this.log(this.createEvent('error_occurred', step, stepName, context, {
      message: error.message,
      stack: error.stack,
      name: error.name
    }));
  }

  // Método para obtener métricas del wizard
  getSessionMetrics(): any {
    try {
      const logs = JSON.parse(localStorage.getItem('wizard_logs') || '[]');
      const sessionLogs = logs.filter((log: WizardLogEvent) => log.sessionId === this.sessionId);
      
      return {
        sessionId: this.sessionId,
        totalEvents: sessionLogs.length,
        duration: Date.now() - this.startTime,
        events: sessionLogs
      };
    } catch {
      return null;
    }
  }

  // Método para limpiar logs antiguos
  static cleanupOldLogs(): void {
    try {
      const logs = JSON.parse(localStorage.getItem('wizard_logs') || '[]');
      const oneDayAgo = Date.now() - (24 * 60 * 60 * 1000);
      
      const recentLogs = logs.filter((log: WizardLogEvent) => 
        new Date(log.timestamp).getTime() > oneDayAgo
      );
      
      localStorage.setItem('wizard_logs', JSON.stringify(recentLogs));
    } catch (error) {
      console.error('Failed to cleanup old logs:', error);
    }
  }
}

// Instancia singleton para usar en toda la aplicación
export const wizardLogger = new WizardLogger();

// Limpiar logs antiguos al inicializar
WizardLogger.cleanupOldLogs();

export default WizardLogger;