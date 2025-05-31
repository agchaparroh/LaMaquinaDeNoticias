#!/usr/bin/env python
"""
Demo script para mostrar el sistema de logging en acción.
Ejecuta ejemplos simples de todas las características de logging.
"""

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Set environment for demo
os.environ['ENVIRONMENT'] = 'development'
os.environ['LOG_LEVEL'] = 'DEBUG'
os.environ['LOG_TO_FILE'] = 'true'

from scraper_core.logging_config import LoggingConfig
from scraper_core.utils.logging_utils import (
    LoggerMixin, log_execution_time, log_exceptions,
    StructuredLogger, sanitize_log_data, SpiderLoggerAdapter
)


class LoggingDemo:
    """Demostración del sistema de logging."""
    
    def __init__(self):
        print("=" * 70)
        print("DEMOSTRACIÓN DEL SISTEMA DE LOGGING")
        print("=" * 70)
        print(f"Ambiente: {LoggingConfig.get_environment()}")
        print(f"Nivel de log: {LoggingConfig.get_log_level()}")
        print(f"Archivo de log: {LoggingConfig.get_log_file_path()}")
        print("=" * 70)
        print()
    
    def demo_basic_logging(self):
        """Demo 1: Logging básico con diferentes niveles."""
        print("📝 Demo 1: Logging Básico")
        print("-" * 40)
        
        logger = logging.getLogger('demo.basic')
        
        # Configurar para que también imprima en consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        logger.addHandler(console_handler)
        logger.setLevel(logging.DEBUG)
        
        # Ejemplos de cada nivel
        logger.debug("🔍 DEBUG: Información detallada para debugging")
        logger.info("ℹ️  INFO: Eventos importantes del flujo normal")
        logger.warning("⚠️  WARNING: Algo inesperado pero recuperable")
        logger.error("❌ ERROR: Un problema serio ocurrió")
        logger.critical("🚨 CRITICAL: Fallo del sistema")
        
        print()
    
    def demo_logger_mixin(self):
        """Demo 2: Uso de LoggerMixin."""
        print("🔌 Demo 2: LoggerMixin")
        print("-" * 40)
        
        class MyComponent(LoggerMixin):
            def do_something(self):
                self.logger.info("Haciendo algo importante...")
                time.sleep(0.5)
                self.logger.debug("Detalles de implementación aquí")
                return "resultado"
        
        component = MyComponent()
        result = component.do_something()
        print(f"Resultado: {result}")
        print()
    
    def demo_decorators(self):
        """Demo 3: Decoradores de logging."""
        print("🎯 Demo 3: Decoradores")
        print("-" * 40)
        
        # Demo @log_execution_time
        @log_execution_time
        def operacion_lenta():
            print("  Ejecutando operación lenta...")
            time.sleep(1.5)
            return "completado"
        
        print("Probando @log_execution_time:")
        resultado = operacion_lenta()
        print(f"  Resultado: {resultado}")
        
        # Demo @log_exceptions
        @log_exceptions(include_traceback=False)
        def operacion_riesgosa(dividir_por=1):
            print(f"  Dividiendo 10 por {dividir_por}")
            return 10 / dividir_por
        
        print("\nProbando @log_exceptions:")
        try:
            operacion_riesgosa(dividir_por=2)
            operacion_riesgosa(dividir_por=0)  # Esto causará error
        except ZeroDivisionError:
            print("  ❌ Error capturado y loggeado")
        
        print()
    
    def demo_structured_logging(self):
        """Demo 4: Logging estructurado."""
        print("📊 Demo 4: Logging Estructurado")
        print("-" * 40)
        
        structured = StructuredLogger('demo.structured')
        
        # Agregar handler de consola para ver el output
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(message)s'))
        structured.logger.addHandler(console_handler)
        structured.logger.setLevel(logging.INFO)
        
        # Eventos estructurados
        print("Eventos en formato JSON:")
        
        structured.info('user_login',
                       user_id=12345,
                       username='john_doe',
                       ip='192.168.1.100',
                       timestamp=datetime.now().isoformat())
        
        structured.warning('slow_query',
                         query_type='article_search',
                         duration_ms=2500,
                         threshold_ms=1000)
        
        structured.error('api_failure',
                        service='supabase',
                        error_code=500,
                        retry_count=3)
        
        print()
    
    def demo_data_sanitization(self):
        """Demo 5: Sanitización de datos sensibles."""
        print("🔒 Demo 5: Sanitización de Datos")
        print("-" * 40)
        
        # Datos con información sensible
        sensitive_data = {
            'url': 'https://api.example.com/data',
            'headers': {
                'User-Agent': 'Mozilla/5.0',
                'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGc...',
                'API-Key': 'sk-1234567890abcdef'
            },
            'response': {
                'status': 200,
                'data': {
                    'user': 'john_doe',
                    'password': 'super_secret_password',
                    'email': 'john@example.com',
                    'credit_card': '4111-1111-1111-1111'
                }
            }
        }
        
        print("Datos originales (con información sensible):")
        print(f"  - Headers.Authorization: {sensitive_data['headers']['Authorization'][:20]}...")
        print(f"  - Response.data.password: {sensitive_data['response']['data']['password']}")
        
        # Sanitizar
        safe_data = sanitize_log_data(sensitive_data)
        
        print("\nDatos sanitizados (seguros para logging):")
        print(f"  - Headers.Authorization: {safe_data['headers']['Authorization']}")
        print(f"  - Response.data.password: {safe_data['response']['data']['password']}")
        print(f"  - Response.data.email: {safe_data['response']['data']['email']} (no sensible)")
        
        print()
    
    def demo_spider_adapter(self):
        """Demo 6: SpiderLoggerAdapter."""
        print("🕷️  Demo 6: Spider Logger Adapter")
        print("-" * 40)
        
        # Simular un spider
        class MockSpider:
            def __init__(self, name):
                self.name = name
        
        spider = MockSpider('demo_spider')
        base_logger = logging.getLogger('demo.spider')
        
        # Configurar handler de consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(message)s'))
        base_logger.addHandler(console_handler)
        base_logger.setLevel(logging.INFO)
        
        # Crear adapter
        adapter = SpiderLoggerAdapter(base_logger, {'spider': spider})
        
        # Los mensajes incluirán automáticamente el contexto del spider
        adapter.info("Iniciando extracción de artículos")
        adapter.warning("Estructura de página cambió")
        adapter.error("Fallo al parsear fecha de publicación")
        
        print()
    
    def demo_performance_logging(self):
        """Demo 7: Logging de performance."""
        print("⚡ Demo 7: Logging de Performance")
        print("-" * 40)
        
        logger = logging.getLogger('demo.performance')
        structured = StructuredLogger('demo.performance.metrics')
        
        # Configurar handlers
        for log in [logger, structured.logger]:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
            log.addHandler(handler)
            log.setLevel(logging.INFO)
        
        # Simular procesamiento de items
        items_processed = 0
        total_time = 0
        
        print("Procesando items...")
        for i in range(5):
            start = time.time()
            
            # Simular procesamiento
            time.sleep(0.1 * (i + 1))  # Cada item toma más tiempo
            
            duration = time.time() - start
            total_time += duration
            items_processed += 1
            
            # Log de performance
            if duration > 0.3:
                logger.warning(f"Item #{i+1} procesado lentamente: {duration:.2f}s")
            else:
                logger.debug(f"Item #{i+1} procesado en {duration:.2f}s")
            
            # Métricas estructuradas
            structured.info('item_processed',
                          item_number=i+1,
                          duration_ms=duration*1000,
                          is_slow=duration > 0.3)
        
        # Resumen
        avg_time = total_time / items_processed
        logger.info(f"\nResumen: {items_processed} items, promedio {avg_time:.2f}s/item")
        
        print()
    
    def show_log_location(self):
        """Muestra dónde encontrar los logs."""
        print("📁 Ubicación de los Logs")
        print("-" * 40)
        
        log_path = LoggingConfig.get_log_file_path()
        log_dir = log_path.parent
        
        print(f"Los logs se están escribiendo en:")
        print(f"  {log_path}")
        
        if log_path.exists():
            size = log_path.stat().st_size
            print(f"  Tamaño actual: {size:,} bytes")
        
        print(f"\nPara ver los logs en tiempo real:")
        print(f"  tail -f {log_path}")
        
        print(f"\nPara ver solo errores:")
        print(f"  grep -E 'ERROR|CRITICAL' {log_path}")
        
        print()
    
    def run_all_demos(self):
        """Ejecuta todas las demostraciones."""
        demos = [
            self.demo_basic_logging,
            self.demo_logger_mixin,
            self.demo_decorators,
            self.demo_structured_logging,
            self.demo_data_sanitization,
            self.demo_spider_adapter,
            self.demo_performance_logging,
            self.show_log_location
        ]
        
        for demo in demos:
            try:
                demo()
                time.sleep(1)  # Pausa entre demos
            except Exception as e:
                print(f"❌ Error en {demo.__name__}: {e}")
                print()


def main():
    """Función principal."""
    demo = LoggingDemo()
    
    try:
        demo.run_all_demos()
        
        print("=" * 70)
        print("✅ DEMOSTRACIÓN COMPLETADA")
        print("=" * 70)
        print("\n💡 Revisa los archivos de log para ver todos los detalles!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demostración interrumpida por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error durante la demostración: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
