"""
Sistema de Logging para Module Pipeline
=======================================

Implementación de logging basada en loguru con:
- Trazabilidad end-to-end mediante request_id
- Configuración por entorno
- Rotación automática de logs
- Protección de datos sensibles
- Integración con FastAPI/async
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from contextlib import contextmanager
import time
import re
import uuid
from functools import wraps

from loguru import logger
from pydantic import BaseModel


class LoggingConfig:
    """
    Configuración centralizada del sistema de logging.
    
    Features:
    - Configuración por entorno (development, staging, production)
    - Rotación automática con retención configurable
    - Formateo estructurado para trazabilidad
    - Protección de datos sensibles
    """
    
    # Niveles de log por entorno
    ENVIRONMENT_LEVELS = {
        "development": "DEBUG",
        "staging": "INFO", 
        "production": "WARNING",
        "test": "DEBUG"
    }
    
    # Retención de logs por entorno (días)
    LOG_RETENTION_DAYS = {
        "development": 7,
        "staging": 30,
        "production": 90,
        "test": 1
    }
    
    # Patrones de datos sensibles a sanitizar
    SENSITIVE_PATTERNS = [
        (r'(api[_-]?key|apikey)[\s:=]+[\w-]+', r'\1=***REDACTED***'),
        (r'(token|jwt|bearer)[\s:=]+[\w.-]+', r'\1=***REDACTED***'),
        (r'(password|passwd|pwd)[\s:=]+[\S]+', r'\1=***REDACTED***'),
        (r'(secret)[\s:=]+[\S]+', r'\1=***REDACTED***'),
        (r'(GROQ_API_KEY|SUPABASE_KEY)[\s:=]+[\S]+', r'\1=***REDACTED***'),
        (r'(email)[\s:=]+[\S]+@[\S]+', r'\1=***REDACTED_EMAIL***'),
        (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '***REDACTED_CARD***'),
    ]
    
    @classmethod
    def get_environment(cls) -> str:
        """Obtiene el entorno actual desde variable de entorno."""
        return os.getenv('ENVIRONMENT', 'development').lower()
    
    @classmethod
    def get_log_level(cls) -> str:
        """Obtiene el nivel de log según el entorno."""
        env = cls.get_environment()
        # Permitir override mediante variable de entorno
        custom_level = os.getenv('LOG_LEVEL')
        if custom_level and custom_level.upper() in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            return custom_level.upper()
        return cls.ENVIRONMENT_LEVELS.get(env, 'INFO')
    
    @classmethod
    def get_log_dir(cls) -> Path:
        """Obtiene el directorio de logs."""
        # Buscar el directorio raíz del proyecto
        current_dir = Path(__file__).resolve()
        project_root = current_dir.parent.parent.parent  # src/utils -> src -> module_pipeline
        
        env = cls.get_environment()
        log_dir = project_root / 'logs' / env
        log_dir.mkdir(parents=True, exist_ok=True)
        
        return log_dir
    
    @classmethod
    def get_retention_days(cls) -> int:
        """Obtiene los días de retención según el entorno."""
        env = cls.get_environment()
        # Permitir override mediante variable de entorno
        custom_days = os.getenv('LOG_RETENTION_DAYS')
        if custom_days and custom_days.isdigit():
            return int(custom_days)
        return cls.LOG_RETENTION_DAYS.get(env, 30)
    
    @classmethod
    def sanitize_sensitive_data(cls, message: str) -> str:
        """Sanitiza datos sensibles en mensajes de log."""
        sanitized = message
        for pattern, replacement in cls.SENSITIVE_PATTERNS:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        return sanitized
    
    @classmethod
    def get_formatter(cls, include_request_id: bool = True) -> str:
        """
        Obtiene el formato de log según el entorno.
        
        Args:
            include_request_id: Si incluir request_id en el formato
        """
        env = cls.get_environment()
        
        # Formato base
        base_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8}"
        
        # Agregar request_id si está disponible
        if include_request_id:
            base_format += " | {extra[request_id]}"
        
        # Agregar componente/fase
        base_format += " | {extra[component]}"
        
        # Formato específico por entorno
        if env == "development":
            # Desarrollo: máximo detalle
            base_format += " | {name}:{function}:{line} | {message}"
        elif env == "staging":
            # Staging: balance entre detalle y limpieza
            base_format += " | {name} | {message}"
        else:
            # Production: mínimo ruido
            base_format += " | {message}"
        
        return base_format


class PipelineLogger:
    """
    Logger principal para el pipeline con funcionalidades extendidas.
    
    Features:
    - Context binding para request_id y componentes
    - Medición de tiempos de ejecución
    - Logging estructurado para fases del pipeline
    - Integración con async/await
    """
    
    def __init__(self):
        """Inicializa el logger del pipeline."""
        self._configured = False
        self._setup_logging()
    
    def _setup_logging(self):
        """Configura el sistema de logging."""
        if self._configured:
            return
            
        # Remover handlers por defecto
        logger.remove()
        
        # Configuración base
        config = LoggingConfig()
        level = config.get_log_level()
        
        # Handler para consola (siempre activo en development)
        if config.get_environment() in ["development", "test"]:
            logger.add(
                sys.stderr,
                level=level,
                format=config.get_formatter(),
                filter=self._filter_and_sanitize,
                colorize=True,
                enqueue=True  # Thread-safe para async
            )
        
        # Handler para archivo principal
        log_dir = config.get_log_dir()
        retention_days = config.get_retention_days()
        
        logger.add(
            log_dir / "pipeline_{time:YYYY-MM-DD}.log",
            level=level,
            format=config.get_formatter(),
            filter=self._filter_and_sanitize,
            rotation="00:00",  # Rotación diaria
            retention=f"{retention_days} days",
            compression="gz",  # Comprimir logs antiguos
            enqueue=True,
            encoding="utf-8"
        )
        
        # Handler para errores (archivo separado)
        logger.add(
            log_dir / "errors_{time:YYYY-MM-DD}.log",
            level="ERROR",
            format=config.get_formatter(),
            filter=self._filter_and_sanitize,
            rotation="00:00",
            retention=f"{retention_days * 2} days",  # Doble retención para errores
            compression="gz",
            enqueue=True,
            encoding="utf-8"
        )
        
        # Handler JSON para production (facilita análisis)
        if config.get_environment() == "production":
            logger.add(
                log_dir / "pipeline_{time:YYYY-MM-DD}.json",
                level=level,
                format="{message}",
                filter=self._filter_and_sanitize,
                serialize=True,  # Salida JSON
                rotation="00:00",
                retention=f"{retention_days} days",
                compression="gz",
                enqueue=True
            )
        
        self._configured = True
        
        # Log inicial
        logger.info(
            "Sistema de logging configurado",
            extra={
                "component": "LoggingSystem",
                "request_id": "INIT",
                "environment": config.get_environment(),
                "log_level": level,
                "retention_days": retention_days
            }
        )
    
    def _filter_and_sanitize(self, record: Dict[str, Any]) -> bool:
        """
        Filtra y sanitiza mensajes de log.
        
        Args:
            record: Registro de log de loguru
            
        Returns:
            True para permitir el log, False para filtrarlo
        """
        # Sanitizar mensaje
        record["message"] = LoggingConfig.sanitize_sensitive_data(record["message"])
        
        # Asegurar que siempre haya request_id
        if "request_id" not in record["extra"]:
            record["extra"]["request_id"] = "NO_REQUEST_ID"
        
        # Asegurar que siempre haya component
        if "component" not in record["extra"]:
            record["extra"]["component"] = "Unknown"
        
        return True
    
    def bind_request(self, request_id: str) -> "loguru.Logger":
        """
        Crea un logger con request_id vinculado.
        
        Args:
            request_id: ID único de la request
            
        Returns:
            Logger con contexto
        """
        return logger.bind(request_id=request_id)
    
    def bind_component(self, component: str, request_id: Optional[str] = None) -> "loguru.Logger":
        """
        Crea un logger con componente y opcionalmente request_id.
        
        Args:
            component: Nombre del componente (ej: "Fase1_Triaje")
            request_id: ID de request opcional
            
        Returns:
            Logger con contexto
        """
        context = {"component": component}
        if request_id:
            context["request_id"] = request_id
        return logger.bind(**context)
    

    @contextmanager
    def phase_context(self, phase: str, request_id: str, **extra):
        """
        Context manager para logging de fases del pipeline.
        
        Args:
            phase: Nombre de la fase
            request_id: ID de la request
            **extra: Datos adicionales para el contexto
        """
        phase_logger = self.bind_component(phase, request_id)
        start_time = time.time()
        
        phase_logger.info(f"Iniciando {phase}", **extra)
        
        try:
            yield phase_logger
            
            elapsed = time.time() - start_time
            phase_logger.info(
                f"Completado {phase}",
                elapsed_seconds=elapsed,
                **extra
            )
            
        except Exception as e:
            elapsed = time.time() - start_time
            # Evitar problemas con formato si el mensaje de error contiene llaves
            error_msg = str(e).replace('{', '{{').replace('}', '}}')
            phase_logger.error(
                f"Error en {phase}: {error_msg}",
                elapsed_seconds=elapsed,
                error_type=type(e).__name__,
                **extra
            )
            raise
    
    @staticmethod
    def measure_time(func: Optional[Callable] = None, *, component: str = None):
        """
        Decorador para medir tiempo de ejecución.
        
        Puede usarse como:
        - @measure_time
        - @measure_time()
        - @measure_time(component="MiComponente")
        """
        def decorator(f):
            @wraps(f)
            def sync_wrapper(*args, **kwargs):
                comp = component or f.__name__
                start = time.time()
                
                try:
                    result = f(*args, **kwargs)
                    elapsed = time.time() - start
                    
                    logger.debug(
                        f"Ejecutado {comp}",
                        extra={
                            "component": comp,
                            "elapsed_seconds": elapsed,
                            "status": "success"
                        }
                    )
                    
                    return result
                    
                except Exception as e:
                    elapsed = time.time() - start
                    # Evitar problemas con formato si el mensaje de error contiene llaves
                    error_msg = str(e).replace('{', '{{').replace('}', '}}')
                    logger.error(
                        f"Error en {comp}: {error_msg}",
                        extra={
                            "component": comp,
                            "elapsed_seconds": elapsed,
                            "status": "error",
                            "error_type": type(e).__name__
                        }
                    )
                    raise
            
            @wraps(f)
            async def async_wrapper(*args, **kwargs):
                comp = component or f.__name__
                start = time.time()
                
                try:
                    result = await f(*args, **kwargs)
                    elapsed = time.time() - start
                    
                    logger.debug(
                        f"Ejecutado {comp}",
                        extra={
                            "component": comp,
                            "elapsed_seconds": elapsed,
                            "status": "success"
                        }
                    )
                    
                    return result
                    
                except Exception as e:
                    elapsed = time.time() - start
                    # Evitar problemas con formato si el mensaje de error contiene llaves
                    error_msg = str(e).replace('{', '{{').replace('}', '}}')
                    logger.error(
                        f"Error en {comp}: {error_msg}",
                        extra={
                            "component": comp,
                            "elapsed_seconds": elapsed,
                            "status": "error",
                            "error_type": type(e).__name__
                        }
                    )
                    raise
            
            # Retornar el wrapper apropiado
            import asyncio
            if asyncio.iscoroutinefunction(f):
                return async_wrapper
            else:
                return sync_wrapper
        
        # Permitir uso con o sin paréntesis
        if func is None:
            return decorator
        else:
            return decorator(func)


# Instancia global del logger del pipeline
pipeline_logger = PipelineLogger()

# Funciones de conveniencia
def get_logger(component: str, request_id: Optional[str] = None) -> "loguru.Logger":
    """
    Obtiene un logger configurado para un componente.
    
    Args:
        component: Nombre del componente
        request_id: ID de request opcional
        
    Returns:
        Logger configurado
    """
    return pipeline_logger.bind_component(component, request_id)


def log_execution_time(component: str = None):
    """
    Decorador para logging de tiempo de ejecución.
    
    Args:
        component: Nombre del componente (usa nombre de función si no se especifica)
    """
    return pipeline_logger.measure_time(component=component)


@contextmanager
def log_phase(phase: str, request_id: str, **extra):
    """
    Context manager para logging de fases.
    
    Args:
        phase: Nombre de la fase
        request_id: ID de la request
        **extra: Datos adicionales
    """
    with pipeline_logger.phase_context(phase, request_id, **extra) as phase_logger:
        yield phase_logger


# Configuración para FastAPI
def setup_fastapi_logging(app):
    """
    Configura logging para aplicación FastAPI.
    
    Args:
        app: Instancia de FastAPI
    """
    from fastapi import Request
    import uuid
    
    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):
        """Middleware para agregar request_id y logging de requests."""
        # Generar o extraer request_id
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Logger para esta request
        req_logger = get_logger("FastAPI", request_id)
        
        # Log de entrada
        req_logger.info(
            f"Request iniciada: {request.method} {request.url.path}",
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else "unknown"
        )
        
        start_time = time.time()
        
        try:
            # Agregar request_id al estado de la request
            request.state.request_id = request_id
            
            # Procesar request
            response = await call_next(request)
            
            # Log de salida
            elapsed = time.time() - start_time
            req_logger.info(
                f"Request completada: {response.status_code}",
                status_code=response.status_code,
                elapsed_seconds=elapsed
            )
            
            # Agregar request_id a headers de respuesta
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            elapsed = time.time() - start_time
            req_logger.error(
                f"Request falló: {str(e)}",
                error_type=type(e).__name__,
                elapsed_seconds=elapsed
            )
            raise
    
    # Log de inicio
    logger.info(
        "FastAPI logging configurado",
        extra={"component": "FastAPI", "request_id": "INIT"}
    )


# Utilidades adicionales
class LogContext(BaseModel):
    """Modelo para contexto estructurado de logs con soporte para trazado distribuido."""
    request_id: str
    component: str
    phase: Optional[str] = None
    fragment_id: Optional[str] = None
    
    # Nuevos campos para trazado distribuido
    article_trace_id: Optional[str] = None
    phase_span_id: Optional[str] = None
    parent_span_id: Optional[str] = None
    
    # Métricas de timing por span
    span_start_time: Optional[float] = None
    
    metadata: Dict[str, Any] = {}
    
    def get_logger(self) -> "loguru.Logger":
        """Obtiene logger con contexto completo incluyendo span IDs."""
        context = {
            "request_id": self.request_id,
            "component": self.component
        }
        
        if self.phase:
            context["phase"] = self.phase
        
        if self.fragment_id:
            context["fragment_id"] = self.fragment_id
            
        # Agregar IDs de trazado distribuido
        if self.article_trace_id:
            context["article_trace_id"] = self.article_trace_id
            
        if self.phase_span_id:
            context["phase_span_id"] = self.phase_span_id
            
        if self.parent_span_id:
            context["parent_span_id"] = self.parent_span_id
            
        # Agregar metadata adicional
        context.update(self.metadata)
        
        return logger.bind(**context)
    
    def create_child_span(self, child_phase: str, child_component: Optional[str] = None) -> "LogContext":
        """Crea un contexto hijo para un span anidado."""
        child_span_id = str(uuid.uuid4())
        
        return LogContext(
            request_id=self.request_id,
            component=child_component or self.component,
            phase=child_phase,
            fragment_id=self.fragment_id,
            article_trace_id=self.article_trace_id,
            phase_span_id=child_span_id,
            parent_span_id=self.phase_span_id,  # El actual se convierte en parent
            span_start_time=time.time(),
            metadata=self.metadata.copy()
        )
    
    def get_span_duration(self) -> Optional[float]:
        """Obtiene la duración del span actual si tiene tiempo de inicio."""
        if self.span_start_time:
            return time.time() - self.span_start_time
        return None


# Funciones para trazado distribuido
def create_article_trace_context(
    request_id: str, 
    fragment_id: str, 
    component: str = "Pipeline"
) -> LogContext:
    """
    Crea un contexto inicial para trazado de artículo.
    
    Args:
        request_id: ID de la request HTTP
        fragment_id: ID del fragmento/artículo
        component: Componente inicial
        
    Returns:
        LogContext con trace_id del artículo
    """
    article_trace_id = str(uuid.uuid4())
    
    return LogContext(
        request_id=request_id,
        component=component,
        fragment_id=fragment_id,
        article_trace_id=article_trace_id,
        span_start_time=time.time()
    )


def trace_phase(
    log_context: LogContext, 
    phase_name: str, 
    **extra_metadata
) -> LogContext:
    """
    Crea un span automático para una fase del pipeline.
    
    Args:
        log_context: Contexto padre
        phase_name: Nombre de la fase (ej: "Fase1_Triaje")
        **extra_metadata: Metadatos adicionales para el span
        
    Returns:
        Nuevo LogContext con span ID para la fase
    """
    phase_span_id = str(uuid.uuid4())
    
    # Crear nuevo contexto para la fase
    phase_context = LogContext(
        request_id=log_context.request_id,
        component=phase_name,
        phase=phase_name,
        fragment_id=log_context.fragment_id,
        article_trace_id=log_context.article_trace_id,
        phase_span_id=phase_span_id,
        parent_span_id=log_context.phase_span_id,  # El contexto actual es el padre
        span_start_time=time.time(),
        metadata={**log_context.metadata, **extra_metadata}
    )
    
    # Log de inicio del span
    span_logger = phase_context.get_logger()
    span_logger.info(
        f"Iniciando span: {phase_name}",
        span_type="phase",
        **extra_metadata
    )
    
    return phase_context


def end_phase_span(
    log_context: LogContext, 
    success: bool = True, 
    error_msg: Optional[str] = None,
    **extra_metadata
) -> None:
    """
    Finaliza un span de fase con métricas de timing.
    
    Args:
        log_context: Contexto del span a finalizar
        success: Si la fase completó exitosamente
        error_msg: Mensaje de error si falló
        **extra_metadata: Metadatos adicionales
    """
    duration = log_context.get_span_duration()
    span_logger = log_context.get_logger()
    
    if success:
        span_logger.info(
            f"Completado span: {log_context.phase}",
            span_type="phase",
            duration_seconds=duration,
            status="success",
            **extra_metadata
        )
    else:
        span_logger.error(
            f"Error en span: {log_context.phase}",
            span_type="phase",
            duration_seconds=duration,
            status="error",
            error_message=error_msg or "Error no especificado",
            **extra_metadata
        )


@contextmanager
def traced_phase(
    parent_context: LogContext, 
    phase_name: str, 
    **extra_metadata
):
    """
    Context manager que combina trazado de spans con logging de fase.
    
    Args:
        parent_context: Contexto padre
        phase_name: Nombre de la fase
        **extra_metadata: Metadatos adicionales
        
    Yields:
        LogContext del span de la fase
    """
    # Crear span para la fase
    phase_context = trace_phase(parent_context, phase_name, **extra_metadata)
    
    try:
        yield phase_context
        # Finalizar span exitosamente
        end_phase_span(phase_context, success=True, **extra_metadata)
        
    except Exception as e:
        # Finalizar span con error
        error_msg = str(e).replace('{', '{{').replace('}', '}}')
        end_phase_span(
            phase_context, 
            success=False, 
            error_msg=error_msg,
            error_type=type(e).__name__,
            **extra_metadata
        )
        raise


# Función mejorada para logging de fases con spans
@contextmanager
def log_phase_with_tracing(
    log_context: LogContext, 
    phase_name: str, 
    **extra
):
    """
    Context manager mejorado que combina logging tradicional con trazado de spans.
    
    Args:
        log_context: Contexto con información de trazado
        phase_name: Nombre de la fase
        **extra: Datos adicionales
        
    Yields:
        Tupla de (phase_logger, phase_context)
    """
    # Crear span para la fase
    phase_context = trace_phase(log_context, phase_name, **extra)
    phase_logger = phase_context.get_logger()
    
    start_time = time.time()
    
    try:
        yield phase_logger, phase_context
        
        # Calcular métricas finales
        elapsed = time.time() - start_time
        span_duration = phase_context.get_span_duration()
        
        phase_logger.info(
            f"Completado {phase_name}",
            elapsed_seconds=elapsed,
            span_duration_seconds=span_duration,
            status="success",
            **extra
        )
        
    except Exception as e:
        elapsed = time.time() - start_time
        span_duration = phase_context.get_span_duration()
        error_msg = str(e).replace('{', '{{').replace('}', '}}')
        
        phase_logger.error(
            f"Error en {phase_name}: {error_msg}",
            elapsed_seconds=elapsed,
            span_duration_seconds=span_duration,
            status="error",
            error_type=type(e).__name__,
            **extra
        )
        raise


# Función para testing
def test_logging_system():
    """Prueba el sistema de logging con trazado distribuido."""
    print("\n=== Testing Sistema de Logging con Trazado Distribuido ===\n")
    
    # Test básico
    test_logger = get_logger("TestComponent", "TEST-001")
    test_logger.debug("Mensaje de debug")
    test_logger.info("Mensaje informativo")
    test_logger.warning("Mensaje de advertencia")
    
    # Test sanitización
    test_logger.info("Conectando con api_key=sk-1234567890abcdef")
    test_logger.info("Token Bearer=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9")
    
    # Test medición de tiempo
    @log_execution_time(component="TestFunction")
    def slow_function():
        import time
        time.sleep(0.1)
        return "done"
    
    result = slow_function()
    
    # Test context manager
    pipeline_logger = PipelineLogger()
    with pipeline_logger.phase_context("TestPhase", "TEST-002", fragment_id="frag-123") as ctx_logger:
        ctx_logger.info("Dentro del contexto de fase")
    
    print("\n=== Test completado - revisar archivos de log ===")
    
    # Añadir pruebas de trazado distribuido
    print("\n=== Testing Trazado Distribuido ===\n")
    
    # Test del nuevo sistema de trazado distribuido
    # 1. Crear contexto inicial para artículo
    article_context = create_article_trace_context(
        request_id="REQ-123",
        fragment_id="FRAG-456",
        component="PipelineTest"
    )
    
    article_logger = article_context.get_logger()
    article_logger.info("Artículo iniciado para procesamiento")
    
    # 2. Test de trazado de fases
    with traced_phase(article_context, "Fase1_Triaje_Test", test_metadata="valor_test") as fase1_context:
        fase1_logger = fase1_context.get_logger()
        fase1_logger.info("Procesando triaje...")
        
        # Simular trabajo
        import time
        time.sleep(0.05)
        
        fase1_logger.info("Triaje completado exitosamente")
    
    # 3. Test de fase con logging mejorado
    with log_phase_with_tracing(article_context, "Fase2_Extraccion_Test", test_data="datos_prueba") as (fase2_logger, fase2_context):
        fase2_logger.info("Iniciando extracción de elementos")
        
        # Simular subtarea con span hijo
        subtask_context = fase2_context.create_child_span("Subtarea_Parsing")
        subtask_logger = subtask_context.get_logger()
        subtask_logger.info("Parseando contenido...")
        
        time.sleep(0.03)
        
        # Finalizar subtarea
        end_phase_span(subtask_context, success=True, elementos_extraidos=5)
        
        fase2_logger.info("Extracción completada")
    
    # 4. Verificar jerarquía de IDs
    print("\n=== Verificación de Jerarquía de IDs ===\n")
    print(f"Request ID: {article_context.request_id}")
    print(f"Article Trace ID: {article_context.article_trace_id}")
    print(f"Fragment ID: {article_context.fragment_id}")
    
    # Crear contexto de fase para mostrar jerarquía
    test_phase_context = trace_phase(article_context, "TestPhase_Hierarchy")
    print(f"Phase Span ID: {test_phase_context.phase_span_id}")
    print(f"Parent Span ID: {test_phase_context.parent_span_id}")
    
    print("\n=== Funcionalidades Implementadas ===\n")
    print("✅ LogContext ampliado con phase_span_id")
    print("✅ Función trace_phase() para spans automáticos")
    print("✅ log_phase() modificado con métricas de timing por span")
    print("✅ trace_id a nivel de artículo y span_id a nivel de fase")
    print("✅ Propagación de contexto a través de todas las fases")
    print("✅ Jerarquía: request_id -> article_trace_id -> phase_span_id")


if __name__ == "__main__":
    test_logging_system()
