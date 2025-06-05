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
        self.support_code = support_code or self._generate_support_code()
        self.timestamp = datetime.utcnow()
    
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
    wait_seconds: float = 5.0  # Según documentación: pausa de 5 segundos
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
        @wraps(func)
        @retry(
            stop=stop_after_attempt(max_attempts + 1),  # +1 porque incluye el intento inicial
            wait=wait_fixed(wait_seconds),
            retry=retry_if_exception_type(groq_exceptions),
            reraise=True
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
            wait=wait_fixed(wait_seconds),
            retry=retry_if_exception_type(groq_exceptions),
            reraise=True
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
