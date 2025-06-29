"""
Configuración de logging para Spider Factory 2.0
Utiliza Loguru para un sistema de logs robusto y flexible
"""
from loguru import logger
import sys
from pathlib import Path


def setup_logging():
    """
    Configura el sistema de logging con Loguru
    - Console output para desarrollo
    - Archivos con rotación diaria
    - Archivo separado para errores
    """
    # Remover handler por defecto de loguru
    logger.remove()
    
    # Crear directorio de logs si no existe
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Console handler - para desarrollo y debugging
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True
    )
    
    # File handler principal - con rotación diaria
    logger.add(
        "logs/spider_factory_{time:YYYY-MM-DD}.log",
        rotation="00:00",  # Rotar a medianoche
        retention="7 days",  # Mantener logs por 7 días
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} - {message}",
        compression="zip"  # Comprimir logs antiguos
    )
    
    # Error file - solo errores y críticos
    logger.add(
        "logs/errors_{time:YYYY-MM-DD}.log",
        level="ERROR",
        rotation="00:00",
        retention="30 days",  # Mantener errores por 30 días
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} - {message}\n{exception}",
        backtrace=True,  # Incluir traceback completo
        diagnose=True    # Incluir variables locales en errores
    )
    
    # Handler específico para análisis de rendimiento
    logger.add(
        "logs/performance_{time:YYYY-MM-DD}.log",
        filter=lambda record: "performance" in record["extra"],
        rotation="00:00",
        retention="3 days",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | PERF | {message}"
    )
    
    logger.info("Sistema de logging configurado con Loguru")
    logger.info(f"Logs guardados en: {log_dir.absolute()}")


def get_logger(name: str = None):
    """
    Obtiene una instancia del logger
    
    Args:
        name: Nombre del módulo (opcional)
    
    Returns:
        Logger configurado
    """
    if name:
        return logger.bind(module=name)
    return logger


# Configuración para capturar logs de bibliotecas externas
def configure_external_loggers():
    """
    Configura loggers de bibliotecas externas para usar Loguru
    """
    import logging
    
    class InterceptHandler(logging.Handler):
        """Handler para interceptar logs estándar y redirigirlos a Loguru"""
        
        def emit(self, record):
            # Obtener el nivel de Loguru correspondiente
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno
            
            # Encontrar el caller correcto
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1
            
            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )
    
    # Configurar loggers de bibliotecas importantes
    libraries = [
        "uvicorn",
        "uvicorn.access",
        "fastapi",
        "httpx",
        "redis",
        "scrapy"
    ]
    
    for lib in libraries:
        lib_logger = logging.getLogger(lib)
        lib_logger.handlers = [InterceptHandler()]
        lib_logger.propagate = False


# Funciones de utilidad para logging
def log_performance(operation: str, duration: float, metadata: dict = None):
    """
    Registra métricas de rendimiento
    
    Args:
        operation: Nombre de la operación
        duration: Duración en segundos
        metadata: Metadatos adicionales
    """
    logger.bind(performance=True).info(
        f"{operation} | Duration: {duration:.3f}s | {metadata or {}}"
    )


def log_api_request(method: str, path: str, status_code: int, duration: float):
    """
    Registra requests de API
    
    Args:
        method: Método HTTP
        path: Path del request
        status_code: Código de respuesta
        duration: Duración en segundos
    """
    level = "INFO" if 200 <= status_code < 400 else "WARNING"
    logger.log(
        level,
        f"API | {method} {path} | Status: {status_code} | Duration: {duration:.3f}s"
    )


def log_spider_generation(spider_name: str, strategy: str, success: bool, error: str = None):
    """
    Registra generación de spiders
    
    Args:
        spider_name: Nombre del spider
        strategy: Estrategia utilizada
        success: Si fue exitoso
        error: Mensaje de error si falló
    """
    if success:
        logger.success(f"Spider generado: {spider_name} | Estrategia: {strategy}")
    else:
        logger.error(f"Error generando spider {spider_name}: {error}")


# Ejemplo de uso
if __name__ == "__main__":
    # Configurar logging
    setup_logging()
    configure_external_loggers()
    
    # Ejemplos de uso
    logger.info("Sistema iniciado")
    logger.debug("Información de debug")
    logger.warning("Advertencia de ejemplo")
    
    # Log con contexto
    logger.bind(user_id=123, session="abc").info("Usuario autenticado")
    
    # Log de rendimiento
    log_performance("analyze_site", 1.234, {"url": "example.com", "cache_hit": True})
    
    # Simular error
    try:
        1 / 0
    except Exception as e:
        logger.exception("Error matemático")
    
    logger.success("Test de logging completado")