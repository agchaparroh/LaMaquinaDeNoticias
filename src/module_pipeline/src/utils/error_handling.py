"""
Sistema de Manejo de Errores para Module Pipeline
=================================================

Este módulo implementa el sistema robusto de manejo de errores siguiendo
estrictamente la documentación en docs/07-manejo-de-errores.md.

Principios clave:
- Nunca fallar completamente
- Degradación elegante
- Logs accionables
- Simplicidad sobre complejidad
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid
from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError


class ErrorPhase(str, Enum):
    """Fases del pipeline donde pueden ocurrir errores."""
    FASE_1_TRIAJE = "fase_1_triaje"
    FASE_2_EXTRACCION = "fase_2_extraccion"
    FASE_3_CITAS_DATOS = "fase_3_citas_datos"
    FASE_4_NORMALIZACION = "fase_4_normalizacion"
    FASE_5_PERSISTENCIA = "fase_5_persistencia"
    GENERAL = "general"


class ErrorType(str, Enum):
    """Tipos de errores según la documentación."""
    VALIDATION_ERROR = "validation_error"
    GROQ_API_ERROR = "groq_api_error"
    SUPABASE_ERROR = "supabase_error"
    PROCESSING_ERROR = "processing_error"
    INTERNAL_ERROR = "internal_error"
    SERVICE_UNAVAILABLE = "service_unavailable"


# ============================================================================
# EXCEPCIONES BASE
# ============================================================================

class PipelineException(Exception):
    """
    Excepción base para todas las excepciones del pipeline.
    
    Mantiene una jerarquía plana según el principio de simplicidad.
    """
    
    def __init__(
        self,
        message: str,
        error_type: ErrorType = ErrorType.INTERNAL_ERROR,
        phase: ErrorPhase = ErrorPhase.GENERAL,
        details: Optional[Dict[str, Any]] = None,
        article_id: Optional[str] = None,
        support_code: Optional[str] = None
    ):
        """
        Inicializa la excepción del pipeline.
        
        Args:
            message: Mensaje de error descriptivo
            error_type: Tipo de error según ErrorType
            phase: Fase del pipeline donde ocurrió el error
            details: Detalles adicionales del error
            article_id: ID del artículo siendo procesado
            support_code: Código de soporte para debugging
        """
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.phase = phase
        self.details = details or {}
        self.article_id = article_id
        # IMPORTANTE: Inicializar timestamp ANTES de generar support_code
        self.timestamp = datetime.utcnow()
        self.support_code = support_code or self._generate_support_code()
    
    def _generate_support_code(self) -> str:
        """Genera un código de soporte único para el error."""
        return f"ERR_PIPE_{self.phase.value.upper()}_{int(self.timestamp.timestamp())}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la excepción a diccionario para logging/respuesta."""
        return {
            "error": self.error_type.value,
            "message": self.message,
            "phase": self.phase.value,
            "details": self.details,
            "article_id": self.article_id,
            "support_code": self.support_code,
            "timestamp": self.timestamp.isoformat()
        }


# ============================================================================
# EXCEPCIONES ESPECÍFICAS - Jerarquía plana según documentación
# ============================================================================

class ValidationError(PipelineException):
    """
    Error de validación de datos de entrada.
    
    Usado cuando los datos no cumplen con los esquemas Pydantic.
    """
    
    def __init__(
        self,
        message: str,
        validation_errors: Optional[List[Dict[str, Any]]] = None,
        phase: ErrorPhase = ErrorPhase.GENERAL,
        article_id: Optional[str] = None
    ):
        details = {
            "validation_errors": validation_errors or [],
            "error_count": len(validation_errors) if validation_errors else 0
        }
        super().__init__(
            message=message,
            error_type=ErrorType.VALIDATION_ERROR,
            phase=phase,
            details=details,
            article_id=article_id
        )
        # La clase padre ya inicializa timestamp


class GroqAPIError(PipelineException):
    """
    Error específico de la API de Groq.
    
    Incluye información sobre reintentos y timeouts.
    """
    
    def __init__(
        self,
        message: str,
        phase: ErrorPhase,
        retry_count: int = 0,
        timeout_seconds: Optional[int] = None,
        status_code: Optional[int] = None,
        article_id: Optional[str] = None
    ):
        details = {
            "retry_count": retry_count,
            "max_retries": 2,  # Según documentación
            "timeout_seconds": timeout_seconds or 60,
            "status_code": status_code,
            "api_provider": "groq"
        }
        super().__init__(
            message=message,
            error_type=ErrorType.GROQ_API_ERROR,
            phase=phase,
            details=details,
            article_id=article_id
        )
        # La clase padre ya inicializa timestamp


class SupabaseRPCError(PipelineException):
    """
    Error específico de las llamadas RPC a Supabase.
    
    Diferencia entre errores de conexión y validación.
    """
    
    def __init__(
        self,
        message: str,
        rpc_name: str,
        phase: ErrorPhase = ErrorPhase.FASE_5_PERSISTENCIA,
        is_connection_error: bool = False,
        retry_count: int = 0,
        article_id: Optional[str] = None
    ):
        details = {
            "rpc_name": rpc_name,
            "is_connection_error": is_connection_error,
            "retry_count": retry_count,
            "max_retries": 1 if is_connection_error else 0  # Según documentación
        }
        super().__init__(
            message=message,
            error_type=ErrorType.SUPABASE_ERROR,
            phase=phase,
            details=details,
            article_id=article_id
        )


class ProcessingError(PipelineException):
    """
    Error durante el procesamiento de datos en cualquier fase.
    
    Usado para errores que no son de API externa pero afectan el procesamiento.
    """
    
    def __init__(
        self,
        message: str,
        phase: ErrorPhase,
        processing_step: str,
        fallback_used: bool = False,
        article_id: Optional[str] = None
    ):
        details = {
            "processing_step": processing_step,
            "fallback_used": fallback_used,
            "recovery_attempted": True
        }
        super().__init__(
            message=message,
            error_type=ErrorType.PROCESSING_ERROR,
            phase=phase,
            details=details,
            article_id=article_id
        )


class ServiceUnavailableError(PipelineException):
    """
    Error cuando el servicio está temporalmente no disponible.
    
    Usado para indicar sobrecarga o mantenimiento.
    """
    
    def __init__(
        self,
        message: str = "Pipeline temporalmente sobrecargado",
        retry_after: int = 300,
        queue_size: Optional[int] = None,
        workers_active: Optional[int] = None
    ):
        details = {
            "retry_after": retry_after,
            "queue_size": queue_size,
            "workers_active": workers_active,
            "status": "overloaded"
        }
        super().__init__(
            message=message,
            error_type=ErrorType.SERVICE_UNAVAILABLE,
            phase=ErrorPhase.GENERAL,
            details=details
        )


# ============================================================================
# EXCEPCIONES DE FALLBACK - Para tracking de degradación elegante
# ============================================================================

class FallbackExecuted(PipelineException):
    """
    No es un error real, sino una señal de que se usó un fallback.
    
    Permite tracking de degradación según la documentación.
    """
    
    def __init__(
        self,
        message: str,
        phase: ErrorPhase,
        fallback_reason: str,
        fallback_action: str,
        article_id: Optional[str] = None
    ):
        details = {
            "fallback_reason": fallback_reason,
            "fallback_action": fallback_action,
            "degraded_mode": True
        }
        # Nota: Esto se loggea como INFO, no como ERROR
        super().__init__(
            message=message,
            error_type=ErrorType.PROCESSING_ERROR,
            phase=phase,
            details=details,
            article_id=article_id
        )


# ============================================================================
# UTILIDADES DE RESPUESTA DE ERROR
# ============================================================================

def generate_request_id() -> str:
    """Genera un ID único para la solicitud."""
    return f"req_{uuid.uuid4().hex[:12]}"


def create_error_response(
    error: Exception,
    request_id: Optional[str] = None,
    status_code: Optional[int] = None
) -> JSONResponse:
    """
    Crea una respuesta JSON estandarizada para errores.
    
    Sigue el formato especificado en la documentación sección 11.
    
    Args:
        error: La excepción a convertir en respuesta
        request_id: ID de la solicitud (se genera si no se proporciona)
        status_code: Código HTTP a usar (se infiere del tipo de error si no se proporciona)
    
    Returns:
        JSONResponse con el formato apropiado según el tipo de error
    """
    if not request_id:
        request_id = generate_request_id()
    
    # Determinar el código de estado HTTP basado en el tipo de error
    if status_code is None:
        if isinstance(error, ValidationError) or isinstance(error, PydanticValidationError):
            status_code = status.HTTP_400_BAD_REQUEST
        elif isinstance(error, ServiceUnavailableError):
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        elif isinstance(error, PipelineException):
            # Para otros errores del pipeline, usar 500
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        else:
            # Error genérico
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    # Construir el contenido de la respuesta según el tipo
    if isinstance(error, ValidationError):
        # Formato para errores de validación (11.1)
        content = {
            "error": "validation_error",
            "mensaje": error.message,
            "detalles": [err for err in error.details.get("validation_errors", [])],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": request_id
        }
    
    elif isinstance(error, PydanticValidationError):
        # Manejar errores de validación de Pydantic directamente
        validation_errors = []
        for err in error.errors():
            field_path = " → ".join(str(loc) for loc in err["loc"])
            validation_errors.append(f"Campo '{field_path}': {err['msg']}")
        
        content = {
            "error": "validation_error",
            "mensaje": "Error en la validación de datos",
            "detalles": validation_errors,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": request_id
        }
    
    elif isinstance(error, ServiceUnavailableError):
        # Formato para servicio no disponible (11.3)
        content = {
            "error": "service_unavailable",
            "mensaje": error.message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "retry_after": error.details.get("retry_after", 300),
            "request_id": request_id
        }
    
    elif isinstance(error, PipelineException):
        # Formato para errores internos del pipeline (11.2)
        content = {
            "error": "internal_error",
            "mensaje": error.message,
            "timestamp": error.timestamp.isoformat() + "Z",
            "request_id": request_id,
            "support_code": error.support_code
        }
    
    else:
        # Error genérico no manejado
        content = {
            "error": "internal_error",
            "mensaje": "Error interno del pipeline",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": request_id,
            "support_code": f"ERR_PIPE_UNKNOWN_{int(datetime.utcnow().timestamp())}"
        }
    
    return JSONResponse(
        status_code=status_code,
        content=content
    )


def create_validation_error_response(
    validation_errors: List[str],
    request_id: Optional[str] = None
) -> JSONResponse:
    """
    Crea una respuesta específica para errores de validación.
    
    Útil cuando se necesita crear una respuesta de validación sin una excepción.
    
    Args:
        validation_errors: Lista de mensajes de error de validación
        request_id: ID de la solicitud
    
    Returns:
        JSONResponse con formato de error de validación
    """
    if not request_id:
        request_id = generate_request_id()
    
    content = {
        "error": "validation_error",
        "mensaje": "Error en la validación del artículo",
        "detalles": validation_errors,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "request_id": request_id
    }
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=content
    )


def extract_validation_errors(pydantic_error: PydanticValidationError) -> List[str]:
    """
    Extrae mensajes de error legibles de una excepción de Pydantic.
    
    Args:
        pydantic_error: Excepción de validación de Pydantic
    
    Returns:
        Lista de mensajes de error formateados
    """
    errors = []
    for error in pydantic_error.errors():
        # Construir la ruta del campo
        field_path = ".".join(str(loc) for loc in error["loc"])
        # Formatear el mensaje
        if error["type"] == "missing":
            errors.append(f"Campo '{field_path}' es requerido")
        elif error["type"] == "string_type":
            errors.append(f"Campo '{field_path}' debe ser texto")
        elif error["type"] == "int_type":
            errors.append(f"Campo '{field_path}' debe ser un número entero")
        else:
            errors.append(f"Campo '{field_path}': {error['msg']}")
    
    return errors


# ============================================================================
# UTILIDADES PARA CONTEXTO ASÍNCRONO
# ============================================================================

async def async_create_error_response(
    error: Exception,
    request_id: Optional[str] = None,
    status_code: Optional[int] = None
) -> JSONResponse:
    """
    Versión asíncrona de create_error_response.
    
    Útil cuando se necesita procesar errores en contextos async.
    Por ahora es un wrapper simple, pero permite extensión futura.
    
    Args:
        error: La excepción a convertir en respuesta
        request_id: ID de la solicitud
        status_code: Código HTTP a usar
    
    Returns:
        JSONResponse con el formato apropiado
    """
    return create_error_response(error, request_id, status_code)


# ============================================================================
# UTILIDADES PARA LOGGING DE ERRORES
# ============================================================================

def format_error_for_logging(error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Formatea un error para logging estructurado con Loguru.
    
    Sigue el formato especificado en la sección 9.4 de la documentación.
    
    Args:
        error: La excepción a formatear
        context: Contexto adicional para el log
    
    Returns:
        Diccionario con la estructura apropiada para logging
    """
    log_data = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "module": "module_pipeline",
        "message": str(error)
    }
    
    # Agregar información específica si es una PipelineException
    if isinstance(error, PipelineException):
        log_data.update({
            "level": "ERROR" if error.error_type != ErrorType.PROCESSING_ERROR else "WARNING",
            "fase": error.phase.value,
            "error_type": error.error_type.value,
            "details": error.details
        })
        
        if error.article_id:
            log_data["articulo_id"] = error.article_id
    else:
        log_data["level"] = "ERROR"
        log_data["error_type"] = "unknown_error"
    
    # Agregar contexto adicional si se proporciona
    if context:
        log_data["context"] = context
    
    return log_data


# ============================================================================
# DECORADORES DE RETRY CON TENACITY
# ============================================================================

from functools import wraps
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    wait_fixed,
    wait_random,
    retry_if_exception_type,
    before_log,
    after_log,
    RetryError
)
from loguru import logger
import asyncio


def retry_with_backoff(
    max_attempts: int = 3,
    wait_multiplier: float = 1.0,
    wait_min: float = 2.0,
    wait_max: float = 60.0,
    exceptions: tuple = (Exception,),
    log_level: str = "WARNING"
):
    """
    Decorador genérico de retry con backoff exponencial.
    
    Sigue los principios de la documentación:
    - Simplicidad sobre complejidad
    - Reintentos limitados para evitar bucles infinitos
    - Logging claro de reintentos
    
    Args:
        max_attempts: Número máximo de intentos (default: 3)
        wait_multiplier: Multiplicador para el backoff exponencial
        wait_min: Tiempo mínimo de espera entre reintentos (segundos)
        wait_max: Tiempo máximo de espera entre reintentos (segundos)
        exceptions: Tupla de excepciones que disparan reintentos
        log_level: Nivel de log para los reintentos
    
    Returns:
        Decorador configurado con tenacity
    """
    def decorator(func):
        @wraps(func)
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(
                multiplier=wait_multiplier,
                min=wait_min,
                max=wait_max
            ),
            retry=retry_if_exception_type(exceptions),
            before=before_log(logger, log_level),
            after=after_log(logger, log_level),
            reraise=True
        )
        def sync_wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        @wraps(func)
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(
                multiplier=wait_multiplier,
                min=wait_min,
                max=wait_max
            ),
            retry=retry_if_exception_type(exceptions),
            before=before_log(logger, log_level),
            after=after_log(logger, log_level),
            reraise=True
        )
        async def async_wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        # Detectar si la función es asíncrona
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def retry_groq_api(
    max_attempts: int = 2,  # Según documentación: máximo 2 reintentos
    wait_seconds: float = 5.0,  # Según documentación: pausa de 5 segundos
    add_jitter: bool = True  # Añadir jitter para evitar thundering herd
):
    """
    Decorador específico para llamadas a la API de Groq.
    
    Configurado según la sección 4 de la documentación:
    - Máximo 2 reintentos
    - Pausa de 5 segundos entre reintentos
    - Timeout de 60 segundos (manejado en el cliente)
    
    Args:
        max_attempts: Número máximo de intentos (default: 2)
        wait_seconds: Segundos de espera entre reintentos (default: 5)
    
    Returns:
        Decorador configurado para Groq API
    """
    # Importar aquí para evitar importaciones circulares
    from groq import APIConnectionError, RateLimitError, APIStatusError
    
    groq_exceptions = (
        APIConnectionError,
        RateLimitError,
        APIStatusError,
        TimeoutError,
        ConnectionError
    )
    
    def decorator(func):
        # Configurar estrategia de espera con jitter opcional
        wait_strategy = wait_fixed(wait_seconds)
        if add_jitter:
            # Añadir hasta 1 segundo de jitter aleatorio
            wait_strategy = wait_fixed(wait_seconds) + wait_random(0, 1)
        
        @wraps(func)
        @retry(
            stop=stop_after_attempt(max_attempts + 1),  # +1 porque incluye el intento inicial
            wait=wait_strategy,
            retry=retry_if_exception_type(groq_exceptions),
            reraise=True,
            before=before_log(logger, "WARNING"),
            after=after_log(logger, "INFO")
        )
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except RetryError as e:
                # Loggear el fallo final
                logger.error(
                    f"Groq API falló después de {max_attempts} reintentos: "
                    f"{e.last_attempt.exception()}"
                )
                # Re-lanzar como GroqAPIError para manejo consistente
                raise GroqAPIError(
                    message=f"Groq API no disponible después de {max_attempts} reintentos",
                    phase=ErrorPhase.GENERAL,
                    retry_count=max_attempts,
                    timeout_seconds=60
                ) from e
        
        @wraps(func)
        @retry(
            stop=stop_after_attempt(max_attempts + 1),
            wait=wait_strategy,
            retry=retry_if_exception_type(groq_exceptions),
            reraise=True,
            before=before_log(logger, "WARNING"),
            after=after_log(logger, "INFO")
        )
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except RetryError as e:
                logger.error(
                    f"Groq API falló después de {max_attempts} reintentos: "
                    f"{e.last_attempt.exception()}"
                )
                raise GroqAPIError(
                    message=f"Groq API no disponible después de {max_attempts} reintentos",
                    phase=ErrorPhase.GENERAL,
                    retry_count=max_attempts,
                    timeout_seconds=60
                ) from e
        
        # Detectar si la función es asíncrona
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def retry_supabase_rpc(
    connection_retries: int = 1,  # Según documentación: 1 reintento para conexión
    validation_retries: int = 0  # Según documentación: 0 reintentos para validación
):
    """
    Decorador específico para llamadas RPC a Supabase.
    
    Configurado según la sección 4 de la documentación:
    - Solo 1 reintento para errores de conexión
    - 0 reintentos para errores de validación
    - Timeout de 30 segundos
    
    Args:
        connection_retries: Reintentos para errores de conexión (default: 1)
        validation_retries: Reintentos para errores de validación (default: 0)
    
    Returns:
        Decorador configurado para Supabase RPC
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            last_exception = None
            
            while attempts <= connection_retries:
                try:
                    return func(*args, **kwargs)
                except (ConnectionError, TimeoutError) as e:
                    # Error de conexión - reintentar si no hemos alcanzado el límite
                    attempts += 1
                    last_exception = e
                    
                    if attempts <= connection_retries:
                        logger.warning(
                            f"Error de conexión con Supabase, reintento {attempts}/{connection_retries}: {e}"
                        )
                        # Esperar 2 segundos antes de reintentar
                        import time
                        time.sleep(2)
                    else:
                        logger.error(f"Supabase RPC falló después de {connection_retries} reintentos")
                        raise SupabaseRPCError(
                            message=f"Error de conexión con Supabase después de {connection_retries} reintentos",
                            rpc_name=func.__name__,
                            is_connection_error=True,
                            retry_count=connection_retries
                        ) from e
                        
                except ValueError as e:
                    # Error de validación - no reintentar
                    logger.error(f"Error de validación en Supabase RPC: {e}")
                    raise SupabaseRPCError(
                        message=f"Error de validación en RPC: {str(e)}",
                        rpc_name=func.__name__,
                        is_connection_error=False,
                        retry_count=0
                    ) from e
                    
                except Exception as e:
                    # Otros errores - tratar como error de validación (sin reintentos)
                    logger.error(f"Error inesperado en Supabase RPC: {e}")
                    raise SupabaseRPCError(
                        message=f"Error inesperado en RPC: {str(e)}",
                        rpc_name=func.__name__,
                        is_connection_error=False,
                        retry_count=0
                    ) from e
            
            # No deberíamos llegar aquí, pero por seguridad
            if last_exception:
                raise last_exception
                
        # Versión asíncrona del wrapper
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            attempts = 0
            last_exception = None
            
            while attempts <= connection_retries:
                try:
                    return await func(*args, **kwargs)
                except (ConnectionError, TimeoutError) as e:
                    attempts += 1
                    last_exception = e
                    
                    if attempts <= connection_retries:
                        logger.warning(
                            f"Error de conexión con Supabase, reintento {attempts}/{connection_retries}: {e}"
                        )
                        await asyncio.sleep(2)
                    else:
                        logger.error(f"Supabase RPC falló después de {connection_retries} reintentos")
                        raise SupabaseRPCError(
                            message=f"Error de conexión con Supabase después de {connection_retries} reintentos",
                            rpc_name=func.__name__,
                            is_connection_error=True,
                            retry_count=connection_retries
                        ) from e
                        
                except ValueError as e:
                    logger.error(f"Error de validación en Supabase RPC: {e}")
                    raise SupabaseRPCError(
                        message=f"Error de validación en RPC: {str(e)}",
                        rpc_name=func.__name__,
                        is_connection_error=False,
                        retry_count=0
                    ) from e
                    
                except Exception as e:
                    logger.error(f"Error inesperado en Supabase RPC: {e}")
                    raise SupabaseRPCError(
                        message=f"Error inesperado en RPC: {str(e)}",
                        rpc_name=func.__name__,
                        is_connection_error=False,
                        retry_count=0
                    ) from e
            
            if last_exception:
                raise last_exception
        
        # Detectar si la función es asíncrona
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    
    return decorator


def no_retry(func):
    """
    Decorador explícito para indicar que una función NO debe tener reintentos.
    
    Útil para documentar intencionalidad en operaciones críticas que no deben
    reintentarse (ej: operaciones de escritura no idempotentes).
    
    Este es principalmente un decorador de documentación, pero también puede
    usarse para logging.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"Ejecutando {func.__name__} sin reintentos")
        return func(*args, **kwargs)
    
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger.debug(f"Ejecutando {func.__name__} sin reintentos")
        return await func(*args, **kwargs)
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return wrapper

# FALLBACK LOGGING EVENT EXCEPTIONS
# ============================================================================

class SpaCyModelLoadFallbackLog(PipelineException):
    def __init__(self, message, article_id=None, model_name=None, original_exception_message=None):
        super().__init__(message, error_type=ErrorType.PROCESSING_ERROR,
                         phase=ErrorPhase.FASE_1_TRIAJE,
                         details={"model_name": model_name, "reason": "SpaCy model load failed, fallback used", "original_error": original_exception_message},
                         article_id=article_id)
        # La clase padre ya inicializa timestamp

class GroqRelevanceFallbackLog(PipelineException):
    def __init__(self, message, article_id=None, text_cleaned_excerpt=None, original_exception_message=None):
        super().__init__(message, error_type=ErrorType.GROQ_API_ERROR,
                         phase=ErrorPhase.FASE_1_TRIAJE,
                         details={"reason": "Groq API for relevance failed, fallback used", "text_cleaned_excerpt": text_cleaned_excerpt, "original_error": original_exception_message},
                         article_id=article_id)
        # La clase padre ya inicializa timestamp

class GroqTranslationFallbackLogEvent(PipelineException):
    def __init__(self, message, article_id=None, original_language=None, original_exception_message=None):
        super().__init__(message, error_type=ErrorType.PROCESSING_ERROR, # This will make format_error_for_logging use WARNING
                         phase=ErrorPhase.FASE_1_TRIAJE,
                         details={"reason": "Groq translation failed, using original text", "original_language": original_language, "original_error": original_exception_message},
                         article_id=article_id)

# Fallback logging events para otras fases
class GroqExtractionFallbackLog(PipelineException):
    def __init__(self, message, article_id=None, phase=ErrorPhase.FASE_2_EXTRACCION, original_exception_message=None):
        super().__init__(message, error_type=ErrorType.GROQ_API_ERROR,
                         phase=phase,
                         details={"reason": "Groq API extraction failed, using fallback data", "original_error": original_exception_message},
                         article_id=article_id)
        # La clase padre ya inicializa timestamp

class NormalizationFallbackLog(PipelineException):
    def __init__(self, message, article_id=None, entity_name=None, original_exception_message=None):
        super().__init__(message, error_type=ErrorType.SUPABASE_ERROR,
                         phase=ErrorPhase.FASE_4_NORMALIZACION,
                         details={"reason": "Entity normalization failed, treating as new entity", "entity_name": entity_name, "original_error": original_exception_message},
                         article_id=article_id)

# ============================================================================
# FALLBACK HANDLERS
# ============================================================================

def handle_spacy_load_error_fase1(
    article_id: Optional[str],
    model_name: str,
    exception: Exception
) -> Dict[str, Any]:
    """
    Handles spaCy model loading errors in Fase 1.
    Returns a partial ResultadoFase1Triaje dictionary.
    """
    log_event = SpaCyModelLoadFallbackLog(
        message=f"Fallback: spaCy model '{model_name}' loading failed for article {article_id}. Preprocessing degraded, article accepted by policy.",
        article_id=article_id,
        model_name=model_name,
        original_exception_message=str(exception)
    )
    log_details = format_error_for_logging(log_event, context={"model_name": model_name, "original_exception_type": type(exception).__name__})
    logger.bind(**log_details).warning(log_details.get("message"))

    # Previous simple logs are replaced by the structured one above.
    # logger.info(
    #     f"Usando fallback para Fase 1 (Artículo: {article_id}) debido a fallo en carga de modelo spaCy. Artículo aceptado por política de fallback.",
    #     article_id=article_id
    # )

    return {
        "id_fragmento": article_id,
        "es_relevante": True,  # Changed to True
        "decision_triaje": "FALLBACK_ACEPTADO_ERROR_PREPROCESO", # Changed decision
        "justificacion_triaje": f"Fallo al cargar modelo spaCy '{model_name}': {str(exception)}. Preprocesamiento degradado, artículo aceptado automáticamente.", # Updated justification
        "categoria_principal": "INDETERMINADO",
        "palabras_clave_triaje": [],
        "puntuacion_triaje": 0.0,
        "confianza_triaje": 0.0,
        "texto_para_siguiente_fase": "[PREPROCESAMIENTO_FALLIDO]", # Placeholder, original text to be handled by caller
        "metadatos_specificos_triaje": {
            "error_type": "SPACY_MODEL_LOAD_FAILURE",
            "model_name": model_name,
            "details": str(exception),
            "message": "SpaCy model loading failed, preprocessing degraded. Article accepted by fallback."
        }
    }

def handle_groq_relevance_error_fase1(
    article_id: Optional[str],
    text_cleaned: str,
    exception: Exception
) -> Dict[str, Any]:
    """
    Handles Groq API errors during relevance evaluation in Fase 1.
    Returns a partial ResultadoFase1Triaje dictionary.
    Now defaults to accepting the article.
    """
    log_event = GroqRelevanceFallbackLog(
        message=f"Fallback: Groq API relevance evaluation failed for article {article_id}. Accepting article by policy.",
        article_id=article_id,
        text_cleaned_excerpt=text_cleaned[:100] if text_cleaned else "N/A",
        original_exception_message=str(exception)
    )
    log_details = format_error_for_logging(log_event, context={"original_exception_type": type(exception).__name__})
    logger.bind(**log_details).error(log_details.get("message"))

    # Previous simple logs are replaced by the structured one above.
    # logger.info(
    #    f"Usando fallback para Fase 1 (Artículo: {article_id}) debido a fallo en API Groq para relevancia. Artículo aceptado por política de fallback.",
    #    article_id=article_id
    # )

    return {
        "id_fragmento": article_id,
        "es_relevante": True,  # Changed to True
        "decision_triaje": "FALLBACK_ACEPTADO_ERROR_LLM", # Changed decision
        "justificacion_triaje": f"Fallo en API Groq para evaluación de relevancia: {str(exception)}. Artículo aceptado automáticamente por política de fallback.", # Updated justification
        "categoria_principal": "INDETERMINADO",
        "palabras_clave_triaje": [],
        "puntuacion_triaje": 0.0, # Neutral default
        "confianza_triaje": 0.0, # Neutral default
        "texto_para_siguiente_fase": text_cleaned, # Cleaning was successful
        "metadatos_specificos_triaje": {
            "error_type": "GROQ_RELEVANCE_API_FAILURE",
            "details": str(exception),
            "message": "Groq API failed during relevance evaluation. Article accepted by fallback."
        }
    }

def handle_groq_translation_fallback_fase1(
    article_id: Optional[str],
    text_cleaned: str,
    original_language: str,
    exception: Optional[Exception]
) -> Dict[str, Any]:
    """
    Handles translation failures in Fase 1 by logging and returning original text.
    """
    log_event = GroqTranslationFallbackLogEvent(
        message=f"Fallback: Groq translation from '{original_language}' failed for article {article_id}. Using original text.",
        article_id=article_id,
        original_language=original_language,
        original_exception_message=str(exception) if exception else "N/A"
    )
    log_details = format_error_for_logging(log_event, context={"original_language": original_language, "original_exception_type": type(exception).__name__ if exception else "N/A"})
    # Logged as WARNING because ErrorType.PROCESSING_ERROR is used, and format_error_for_logging converts this to "WARNING" level in its output.
    logger.bind(**log_details).warning(log_details.get("message"))

    # Previous simple logs are replaced by the structured one above.
    # logger.info(
    #     f"Se usará texto original para Fase 1 (Artículo: {article_id}) debido a fallo en traducción.",
    #     article_id=article_id
    # )

    return {
        "status": "TRANSLATION_FALLBACK_APPLIED",
        "message": f"Traducción de '{original_language}' falló. Se usará texto original.",
        "original_text_used": True,
        "texto_para_siguiente_fase": text_cleaned,
        "error_details": str(exception) if exception else None,
        "article_id": article_id
    }

def handle_generic_phase_error(
    article_id: Optional[str],
    phase: ErrorPhase,
    step_failed: str,
    exception: Exception
) -> Dict[str, Any]:
    """
    Generic error handler for Fase 2, 3, 4.
    Returns a generic error structure for that phase's result.
    """
    # Use the original exception for logging if it's a PipelineException, otherwise wrap it for context.
    log_event = exception
    if not isinstance(exception, PipelineException):
        # Wrap generic exception for more structured logging if needed, though format_error_for_logging handles basic Exception
        # For now, we'll let format_error_for_logging handle it.
        # However, providing phase and article_id to the log context is crucial.
        pass

    log_message = f"Fallback: Failure in {phase.value} during step '{step_failed}' for article {article_id}. Exception: {str(exception)}"

    # If original exception is not PipelineException, format_error_for_logging will assign default error_type
    # We can provide more context here.
    current_context = {
        "article_id": article_id,
        "phase_value": phase.value,
        "step_failed": step_failed,
        "original_exception_type": type(exception).__name__
    }
    if isinstance(exception, PipelineException): # It will already have phase, error_type, details
        log_details = format_error_for_logging(exception, context=current_context)
    else: # Generic exception, ensure phase is part of the main log details if possible
        log_details = format_error_for_logging(
            ProcessingError(message=str(exception), phase=phase, processing_step=step_failed, article_id=article_id),
            context=current_context
        )
        # Override message if the generic one from ProcessingError is not what we want for the top-level log
        log_details["message"] = log_message


    # The level in log_details will be determined by format_error_for_logging.
    # We use logger.error() here to ensure it's treated as an error in sinks if not overridden by log_details' level.
    actual_log_level = log_details.get("level", "ERROR").upper()
    if actual_log_level == "WARNING":
        logger.bind(**log_details).warning(log_details.get("message", log_message))
    else:
        logger.bind(**log_details).error(log_details.get("message", log_message))

    # Determine error type for the returned dictionary based on exception
    error_type_str = "PROCESSING_ERROR"
    if isinstance(exception, GroqAPIError):
        error_type_str = ErrorType.GROQ_API_ERROR.value
    elif isinstance(exception, SupabaseRPCError):
        error_type_str = ErrorType.SUPABASE_ERROR.value
    elif isinstance(exception, ValidationError): # Pydantic or custom
        error_type_str = ErrorType.VALIDATION_ERROR.value
    elif isinstance(exception, PipelineException):
        error_type_str = exception.error_type.value

    return {
        "id_fragmento": article_id,
        "status": "ERROR",
        "phase_name": phase.value,
        "error_type": error_type_str,
        "message": f"Fallo en {phase.value} durante {step_failed}: {str(exception)}.",
        "step_failed": step_failed,
        "exception_type": type(exception).__name__,
        "details": str(exception),
        "data": {} # Empty data or minimal required structure for that phase's output model
    }


# ============================================================================
# FALLBACK HANDLERS ESPECÍFICOS PARA CADA FASE
# ============================================================================

def handle_groq_extraction_error_fase2(
    article_id: Optional[str],
    titulo: Optional[str] = None,
    medio: Optional[str] = None,
    exception: Exception = None
) -> Dict[str, Any]:
    """
    Handles Groq API errors during basic extraction in Fase 2.
    Returns fallback data with a basic fact from title.
    According to docs: Create basic fact using article title.
    """
    log_event = GroqExtractionFallbackLog(
        message=f"Fallback: Groq API extraction failed for article {article_id}. Creating basic fact from title.",
        article_id=article_id,
        phase=ErrorPhase.FASE_2_EXTRACCION,
        original_exception_message=str(exception) if exception else "N/A"
    )
    log_details = format_error_for_logging(log_event, context={"titulo": titulo, "medio": medio})
    logger.bind(**log_details).error(log_details.get("message"))

    # Crear hecho básico según documentación
    hecho_basico = {
        "id_hecho": 1,
        "texto_original_del_hecho": titulo or "[Sin título disponible]",
        "metadata_hecho": {
            "tipo_hecho": "SUCESO",
            "es_fallback": True
        }
    }

    # Crear entidad genérica con el nombre del medio
    entidad_basica = {
        "id_entidad": 1,
        "texto_entidad": medio or "[Medio desconocido]",
        "tipo_entidad": "ORGANIZACION",
        "metadata_entidad": {
            "tipo": "ORGANIZACION",
            "es_fallback": True
        }
    }

    return {
        "hechos_extraidos": [hecho_basico],
        "entidades_extraidas": [entidad_basica],
        "advertencias": [f"Extracción degradada: {str(exception) if exception else 'Error en Groq API'}"]
    }


def handle_json_parsing_error_fase2(
    article_id: Optional[str],
    json_response: str,
    exception: Exception
) -> Dict[str, Any]:
    """
    Handles JSON parsing errors in Fase 2.
    Attempts repair with json_repair or returns minimal data.
    """
    logger.warning(
        f"JSON parsing error in Fase 2 for article {article_id}. Attempting repair.",
        article_id=article_id,
        exception=str(exception)
    )

    # Intentar reparar JSON (simplificado, en producción usar json_repair)
    try:
        # Intentar extraer datos básicos manualmente
        import re
        
        # Buscar patrones de hechos
        hechos_match = re.search(r'"hechos"\s*:\s*\[(.*?)\]', json_response, re.DOTALL)
        if hechos_match:
            logger.info(f"Extracted partial facts data for article {article_id}")
            # Return partial data
            return {
                "hechos_extraidos": [],
                "entidades_extraidas": [],
                "advertencias": ["JSON malformado reparado parcialmente"]
            }
    except:
        pass

    # Si no se puede reparar, usar datos mínimos
    return handle_groq_extraction_error_fase2(article_id, exception=exception)


def handle_groq_citas_error_fase3(
    article_id: Optional[str],
    exception: Exception = None
) -> Dict[str, Any]:
    """
    Handles Groq API errors during quotes/data extraction in Fase 3.
    According to docs: Continue without quotes/quantitative data (not critical).
    """
    log_event = GroqExtractionFallbackLog(
        message=f"Fallback: Groq API quotes/data extraction failed for article {article_id}. Continuing without quotes/data.",
        article_id=article_id,
        phase=ErrorPhase.FASE_3_CITAS_DATOS,
        original_exception_message=str(exception) if exception else "N/A"
    )
    log_details = format_error_for_logging(log_event)
    logger.bind(**log_details).warning(log_details.get("message"))  # WARNING porque no es crítico

    return {
        "citas_textuales_extraidas": [],
        "datos_cuantitativos_extraidos": [],
        "advertencias_citas_datos": ["Extracción de citas y datos omitida por fallo en API"]
    }


def handle_normalization_error_fase4(
    article_id: Optional[str],
    entidades: List[Any],
    exception: Exception = None
) -> List[Any]:
    """
    Handles entity normalization errors in Fase 4.
    According to docs: Create all entities as new if DB search fails.
    """
    log_event = NormalizationFallbackLog(
        message=f"Fallback: Entity normalization failed for article {article_id}. Treating all entities as new.",
        article_id=article_id,
        entity_name="Multiple entities",
        original_exception_message=str(exception) if exception else "N/A"
    )
    log_details = format_error_for_logging(log_event, context={"num_entities": len(entidades)})
    logger.bind(**log_details).warning(log_details.get("message"))

    # Marcar todas las entidades como nuevas (sin normalización)
    for entidad in entidades:
        if hasattr(entidad, 'id_entidad_normalizada'):
            entidad.id_entidad_normalizada = None
            entidad.nombre_entidad_normalizada = None
            entidad.similitud_normalizacion = 0.0

    return entidades


def handle_groq_relations_error_fase4(
    article_id: Optional[str],
    exception: Exception = None
) -> Dict[str, Any]:
    """
    Handles Groq API errors during relationship extraction in Fase 4.
    According to docs: Continue without relationships.
    """
    log_event = GroqExtractionFallbackLog(
        message=f"Fallback: Groq API relationship extraction failed for article {article_id}. Continuing without relationships.",
        article_id=article_id,
        phase=ErrorPhase.FASE_4_NORMALIZACION,
        original_exception_message=str(exception) if exception else "N/A"
    )
    log_details = format_error_for_logging(log_event)
    logger.bind(**log_details).warning(log_details.get("message"))  # WARNING porque no es crítico

    return {
        "relaciones_hecho_entidad": [],
        "relaciones_hecho_hecho": [],
        "relaciones_entidad_entidad": [],
        "contradicciones": [],
        "indices": {
            "por_hecho": {},
            "por_entidad": {},
            "hecho_hecho": {},
            "entidad_entidad": {}
        }
    }


def handle_importance_ml_error(
    article_id: Optional[str],
    exception: Exception = None
) -> int:
    """
    Handles ML model errors for importance calculation in Fase 4.5.
    According to docs: Use default importance value (5).
    """
    logger.info(
        f"Using default importance for article {article_id} due to ML model error: {exception}",
        article_id=article_id
    )
    return 5  # Valor neutro según documentación


def handle_persistence_error_fase5(
    article_id: Optional[str],
    datos_completos: Dict[str, Any],
    exception: Exception = None
) -> Dict[str, Any]:
    """
    Handles persistence errors in Fase 5.
    According to docs: Save to error table for manual review.
    """
    logger.error(
        f"Critical persistence error for article {article_id}. Saving to error table.",
        article_id=article_id,
        exception=str(exception)
    )

    return {
        "status": "ERROR_PERSISTENCIA",
        "article_id": article_id,
        "error_details": str(exception),
        "timestamp": datetime.utcnow().isoformat(),
        "datos_para_revision": datos_completos,
        "mensaje": "Datos guardados en tabla de errores para revisión manual"
    }
