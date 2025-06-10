"""
Demo del Sistema de Logging del Pipeline
=======================================

Script de demostración para mostrar las capacidades del sistema de logging.
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4
import time

# Agregar directorio padre al path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils.logging_config import (
    get_logger,
    log_execution_time,
    log_phase,
    LogContext,
    LoggingConfig
)
# Imports opcionales para la demo del pipeline
try:
    from src.models.entrada import FragmentoProcesableItem
    from src.pipeline.pipeline_coordinator import PipelineCoordinator
    PIPELINE_AVAILABLE = True
except ImportError:
    PIPELINE_AVAILABLE = False
    print("Nota: Algunas funcionalidades del pipeline no estan disponibles")


def demo_basic_logging():
    """Demuestra logging basico."""
    print("\n=== DEMO: Logging Basico ===")
    
    # Logger simple
    logger = get_logger("DemoComponent")
    logger.info("Este es un mensaje informativo basico")
    logger.debug("Este es un mensaje de debug con detalles")
    logger.warning("Este es un mensaje de advertencia")
    
    # Logger con request_id
    request_logger = get_logger("DemoComponent", "DEMO-REQ-001")
    request_logger.info("Mensaje con request_id para trazabilidad")


def demo_sensitive_data_protection():
    """Demuestra proteccion de datos sensibles."""
    print("\n=== DEMO: Proteccion de Datos Sensibles ===")
    
    logger = get_logger("SecurityDemo", "DEMO-REQ-002")
    
    # Intentar loggear datos sensibles
    logger.info("Conectando con api_key=sk-1234567890abcdef")
    logger.info("Token de autenticacion: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9")
    logger.info("Configuracion: GROQ_API_KEY=groq-secret-key-12345")
    logger.info("Usuario email=usuario@ejemplo.com registrado")
    
    print("Los datos sensibles han sido sanitizados automaticamente en los logs")


@log_execution_time(component="DemoSlowFunction")
def slow_function():
    """Funcion lenta para demostrar medicion de tiempo."""
    time.sleep(0.5)
    return "Operacion completada"


@log_execution_time()
async def async_slow_function():
    """Funcion async lenta."""
    await asyncio.sleep(0.3)
    return "Operacion async completada"


def demo_execution_timing():
    """Demuestra medicion de tiempos de ejecucion."""
    print("\n=== DEMO: Medicion de Tiempos ===")
    
    # Funcion sync
    result = slow_function()
    print(f"Resultado sync: {result}")
    
    # Funcion async
    async def run_async():
        result = await async_slow_function()
        print(f"Resultado async: {result}")
    
    asyncio.run(run_async())


def demo_phase_logging():
    """Demuestra logging de fases del pipeline."""
    print("\n=== DEMO: Logging de Fases ===")
    
    request_id = "DEMO-REQ-003"
    fragment_id = str(uuid4())
    
    # Simular procesamiento por fases
    with log_phase("Fase1_Triaje", request_id, fragment_id=fragment_id) as phase_logger:
        phase_logger.info("Analizando relevancia del fragmento")
        time.sleep(0.2)
        phase_logger.info("Fragmento marcado como relevante")
    
    with log_phase("Fase2_Extraccion", request_id, fragment_id=fragment_id) as phase_logger:
        phase_logger.info("Extrayendo hechos y entidades")
        time.sleep(0.3)
        phase_logger.info("Extraidos 3 hechos y 5 entidades")
    
    # Simular error en una fase
    try:
        with log_phase("Fase3_CitasDatos", request_id, fragment_id=fragment_id) as phase_logger:
            phase_logger.info("Procesando citas textuales")
            raise ValueError("Error simulado en extraccion de citas")
    except ValueError:
        pass  # El error ya fue loggeado por el context manager
    
    print("Fases ejecutadas con logging contextual")


def demo_structured_context():
    """Demuestra uso de contexto estructurado."""
    print("\n=== DEMO: Contexto Estructurado ===")
    
    # Crear contexto completo
    context = LogContext(
        request_id="DEMO-REQ-004",
        component="StructuredDemo",
        phase="ProcessingPhase",
        fragment_id=str(uuid4()),
        metadata={
            "article_id": "ART-123",
            "source": "demo_source",
            "processing_stage": "initial"
        }
    )
    
    logger = context.get_logger()
    logger.info("Mensaje con contexto estructurado completo")
    logger.debug("Todos los campos del contexto estan disponibles para analisis")


async def demo_pipeline_integration():
    """Demuestra integracion con el pipeline real."""
    print("\n=== DEMO: Integracion con Pipeline ===")
    
    if not PIPELINE_AVAILABLE:
        print("Pipeline no disponible para esta demo")
        return
    
    # Crear fragmento de prueba
    fragmento = FragmentoProcesableItem(
        id_fragmento=str(uuid4()),
        texto_original="El presidente Pedro Sanchez anuncio nuevas medidas economicas.",
        id_articulo_fuente="DEMO-ARTICLE-001",
        orden_en_articulo=1
    )
    
    # Crear coordinador
    coordinator = PipelineCoordinator()
    
    # Ejecutar pipeline con request_id
    request_id = "DEMO-PIPELINE-001"
    print(f"Ejecutando pipeline con request_id: {request_id}")
    
    # Nota: Esto ejecutara el pipeline real (o mocks si las fases no estan implementadas)
    resultado = coordinator.ejecutar_pipeline_completo(
        fragmento=fragmento,
        request_id=request_id
    )
    
    print(f"Pipeline completado: Exito={resultado['exito']}, Fases={resultado['fase_completada']}")


def demo_environment_configuration():
    """Demuestra configuracion por entorno."""
    print("\n=== DEMO: Configuracion por Entorno ===")
    
    import os
    
    # Mostrar configuracion actual
    env = LoggingConfig.get_environment()
    level = LoggingConfig.get_log_level()
    retention = LoggingConfig.get_retention_days()
    
    print(f"Entorno actual: {env}")
    print(f"Nivel de log: {level}")
    print(f"Retencion de logs: {retention} dias")
    
    # Simular cambio de entorno
    print("\nSimulando entorno de produccion:")
    os.environ["ENVIRONMENT"] = "production"
    
    env = LoggingConfig.get_environment()
    level = LoggingConfig.get_log_level()
    retention = LoggingConfig.get_retention_days()
    
    print(f"Entorno: {env}")
    print(f"Nivel de log: {level}")
    print(f"Retencion de logs: {retention} dias")
    
    # Restaurar
    os.environ.pop("ENVIRONMENT", None)


def show_log_files():
    """Muestra ubicacion de archivos de log."""
    print("\n=== Archivos de Log ===")
    
    log_dir = LoggingConfig.get_log_dir()
    print(f"Directorio de logs: {log_dir}")
    
    if log_dir.exists():
        log_files = list(log_dir.glob("*.log"))
        if log_files:
            print("\nArchivos de log encontrados:")
            for file in sorted(log_files):
                print(f"  - {file.name} ({file.stat().st_size:,} bytes)")
        else:
            print("No hay archivos de log aun")
    else:
        print("El directorio de logs no existe aun")


def main():
    """Ejecuta todas las demos."""
    print("=" * 60)
    print("DEMOSTRACION DEL SISTEMA DE LOGGING DEL PIPELINE")
    print("=" * 60)
    
    # Ejecutar demos
    demo_basic_logging()
    demo_sensitive_data_protection()
    demo_execution_timing()
    demo_phase_logging()
    demo_structured_context()
    demo_environment_configuration()
    
    # Demo async del pipeline (opcional)
    if PIPELINE_AVAILABLE:
        print("\nDesea ejecutar demo de integracion con pipeline? (s/n): ", end="")
        if input().lower() == 's':
            asyncio.run(demo_pipeline_integration())
    else:
        print("\n(Demo de pipeline no disponible debido a problemas de importacion)")
    
    # Mostrar archivos de log
    show_log_files()
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETADA")
    print("Revisa los archivos de log para ver los mensajes registrados")
    print("=" * 60)


if __name__ == "__main__":
    main()
