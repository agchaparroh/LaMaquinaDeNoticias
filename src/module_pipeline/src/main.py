import sys # Necesario para sys.stdout en la configuración de Loguru
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError as PydanticValidationError
from loguru import logger
import uvicorn
from datetime import datetime

# Importar configuraciones y configuración de loguru
from .config import settings, LOGURU_CONFIG
from .controller import PipelineController

# Importar utilidades de manejo de errores
from .utils.error_handling import (
    PipelineException,
    ValidationError,
    ServiceUnavailableError,
    create_error_response,
    extract_validation_errors,
    format_error_for_logging,
    generate_request_id
)

# --- Configuración del Logger ---
logger.remove() # Quitar handlers default
logger.configure(**LOGURU_CONFIG) # Aplicar configuración personalizada

# --- Inicialización de la Aplicación FastAPI ---
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# --- Middlewares ---
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS] if isinstance(settings.CORS_ORIGINS, list) else ([settings.CORS_ORIGINS] if isinstance(settings.CORS_ORIGINS, str) else []),
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )
    logger.info(f"CORS middleware configurado para orígenes: {settings.CORS_ORIGINS}")

# --- Manejadores de Excepciones Específicos ---

@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Maneja errores de validación de FastAPI/Pydantic en las requests.
    
    Convierte los errores de validación en respuestas consistentes según
    la sección 11.1 de la documentación.
    """
    request_id = generate_request_id()
    
    # Extraer el cuerpo de la request si es posible (para debugging)
    body = None
    try:
        body = await request.body()
    except:
        pass
    
    # Log estructurado del error
    log_data = format_error_for_logging(
        exc,
        context={
            "request_method": request.method,
            "request_url": str(request.url),
            "request_id": request_id,
            "body": body.decode() if body else None
        }
    )
    logger.bind(**log_data).warning("Error de validación en request")
    
    # Crear respuesta de error
    return create_error_response(exc, request_id=request_id)


@app.exception_handler(PydanticValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: PydanticValidationError):
    """
    Maneja errores de validación de Pydantic que ocurren durante el procesamiento.
    """
    request_id = generate_request_id()
    
    # Log estructurado
    log_data = format_error_for_logging(
        exc,
        context={
            "request_method": request.method,
            "request_url": str(request.url),
            "request_id": request_id
        }
    )
    logger.bind(**log_data).warning("Error de validación Pydantic durante procesamiento")
    
    return create_error_response(exc, request_id=request_id)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Maneja excepciones HTTP estándar de Starlette/FastAPI.
    """
    request_id = generate_request_id()
    
    # Para errores HTTP estándar, mantener el formato pero agregar request_id
    content = {
        "error": "http_error",
        "mensaje": exc.detail,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "request_id": request_id
    }
    
    # Log según el código de estado
    if exc.status_code >= 500:
        logger.error(f"HTTP {exc.status_code} error: {exc.detail} [request_id: {request_id}]")
    else:
        logger.warning(f"HTTP {exc.status_code} error: {exc.detail} [request_id: {request_id}]")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=exc.headers if hasattr(exc, 'headers') else None
    )


@app.exception_handler(PipelineException)
async def pipeline_exception_handler(request: Request, exc: PipelineException):
    """
    Maneja excepciones específicas del pipeline.
    
    Estas excepciones ya tienen toda la información necesaria para
    generar respuestas apropiadas.
    """
    request_id = generate_request_id()
    
    # Log estructurado según el tipo de error
    log_data = format_error_for_logging(
        exc,
        context={
            "request_method": request.method,
            "request_url": str(request.url),
            "request_id": request_id
        }
    )
    
    # Usar logger.bind para contexto
    if hasattr(exc, 'article_id') and exc.article_id:
        bound_logger = logger.bind(articulo_id=exc.article_id, **log_data)
    else:
        bound_logger = logger.bind(**log_data)
    
    # Log según el nivel apropiado
    if isinstance(exc, ServiceUnavailableError):
        bound_logger.warning("Servicio no disponible")
    elif hasattr(exc, 'fallback_used') and exc.fallback_used:
        bound_logger.info("Fallback ejecutado")
    else:
        bound_logger.error("Error en pipeline")
    
    return create_error_response(exc, request_id=request_id)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Manejador global para cualquier excepción no capturada.
    
    Este es el último recurso para errores inesperados.
    """
    request_id = generate_request_id()
    
    # Log completo del error no manejado
    logger.error(
        f"Error no manejado en {request.method} {request.url} [request_id: {request_id}]",
        exc_info=True
    )
    
    # En producción, no exponer detalles del error interno
    if settings.DEBUG_MODE:
        details = str(exc)
    else:
        details = None
    
    content = {
        "error": "internal_error",
        "mensaje": "Error interno del pipeline",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "request_id": request_id,
        "support_code": f"ERR_PIPE_UNKNOWN_{int(datetime.utcnow().timestamp())}"
    }
    
    if details:
        content["debug_details"] = details
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=content
    )

# --- Eventos de Inicio y Apagado ---
@app.on_event("startup")
async def startup_event():
    logger.info(f"Iniciando aplicación FastAPI: {settings.PROJECT_NAME} v{settings.PROJECT_VERSION}")
    logger.info(f"LOG_LEVEL actual: {settings.LOG_LEVEL}")
    
    # Inicializar controlador del pipeline
    global pipeline_controller
    pipeline_controller = PipelineController()
    logger.info("PipelineController inicializado")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Apagando aplicación FastAPI: {settings.PROJECT_NAME}")

# --- Endpoints de la API ---
@app.get("/health", tags=["Utilities"], summary="Verifica el estado de la aplicación")
async def health_check():
    """
    Endpoint de verificación de estado.
    Retorna un estado saludable si la aplicación está operativa.
    """
    logger.debug("Health check endpoint fue invocado.")
    return {"status": "healthy", "message": f"{settings.PROJECT_NAME} (Pipeline) está operativo."}

# --- Endpoints del Pipeline ---
# TODO: Implementar endpoints según Tareas #20 y #21

@app.post("/procesar_articulo", tags=["Pipeline"], summary="Procesa un artículo completo")
async def procesar_articulo():
    """Endpoint para procesar artículos completos - TODO: Implementar."""
    raise NotImplementedError("Pendiente de implementación - Tarea #20")

@app.post("/procesar_fragmento", tags=["Pipeline"], summary="Procesa un fragmento de documento")
async def procesar_fragmento():
    """Endpoint para procesar fragmentos - TODO: Implementar."""
    raise NotImplementedError("Pendiente de implementación - Tarea #21")

@app.get("/status/{job_id}", tags=["Pipeline"], summary="Consulta estado de procesamiento")
async def get_status(job_id: str):
    """Endpoint para consultar estado - TODO: Implementar."""
    raise NotImplementedError("Pendiente de implementación - Tarea #22")

# --- Bloque para ejecución directa con Uvicorn (para desarrollo) ---
if __name__ == "__main__":
    logger.info(f"Iniciando servidor Uvicorn directamente desde main.py en http://{settings.API_HOST}:{settings.API_PORT}")
    uvicorn.run(
        "src.main:app",  # Cambiado para reflejar la ubicación del módulo cuando se ejecuta con python -m src.main
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True, # Ideal para desarrollo
        log_level=settings.LOG_LEVEL.lower()
    )
