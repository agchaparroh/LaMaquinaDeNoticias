#!/usr/bin/env python
"""
Script de verificación del sistema de logging (versión corregida para Windows).
Ejecuta pruebas para confirmar que el logging está configurado correctamente.
"""

import os
import sys
import logging
from pathlib import Path
import tempfile
import json
from datetime import datetime
import time

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from scraper_core.logging_config import LoggingConfig
from scraper_core.log_rotation import LogRotationConfig
from scraper_core.utils.logging_utils import (
    LoggerMixin, log_execution_time, log_exceptions,
    StructuredLogger, sanitize_log_data
)


class LoggingVerification:
    """Verificación del sistema de logging."""
    
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def test(self, name, condition, error_msg=""):
        """Ejecuta una prueba y registra el resultado."""
        if condition:
            self.passed += 1
            self.results.append(f"✓ {name}")
            return True
        else:
            self.failed += 1
            self.results.append(f"✗ {name}: {error_msg}")
            return False
    
    def verify_environment_config(self):
        """Verifica la configuración por ambiente."""
        print("\n1. Verificando configuración por ambiente...")
        
        # Test default environment
        env = LoggingConfig.get_environment()
        self.test("Ambiente por defecto", 
                 env in ['development', 'staging', 'production', 'test'],
                 f"Ambiente inválido: {env}")
        
        # Test log levels by environment
        test_envs = {
            'development': 'DEBUG',
            'production': 'WARNING',
            'staging': 'INFO'
        }
        
        for env, expected_level in test_envs.items():
            level = LoggingConfig.get_log_level(env)
            self.test(f"Nivel de log para {env}", 
                     level == expected_level,
                     f"Esperado {expected_level}, obtenido {level}")
    
    def verify_log_formats(self):
        """Verifica los formatos de log."""
        print("\n2. Verificando formatos de log...")
        
        formats = ['detailed', 'simple', 'json', 'production']
        for format_name in formats:
            format_str = LoggingConfig.FORMATS.get(format_name)
            self.test(f"Formato {format_name} existe", 
                     format_str is not None,
                     "Formato no encontrado")
    
    def verify_file_paths(self):
        """Verifica la generación de rutas de archivos."""
        print("\n3. Verificando rutas de archivos de log...")
        
        # Test main log path
        main_path = LoggingConfig.get_log_file_path()
        self.test("Ruta principal de log", 
                 main_path.suffix == '.log',
                 f"Extensión incorrecta: {main_path}")
        
        # Test spider-specific path
        spider_path = LoggingConfig.get_log_file_path('test_spider')
        self.test("Ruta de log para spider", 
                 'spiders' in str(spider_path) and 'test_spider' in str(spider_path),
                 f"Ruta incorrecta: {spider_path}")
    
    def verify_rotation_config(self):
        """Verifica la configuración de rotación."""
        print("\n4. Verificando configuración de rotación...")
        
        # Test rotation settings by environment
        dev_settings = LogRotationConfig.get_rotation_settings('development')
        self.test("Rotación en development", 
                 dev_settings['type'] == 'size',
                 f"Tipo incorrecto: {dev_settings.get('type')}")
        
        prod_settings = LogRotationConfig.get_rotation_settings('production')
        self.test("Rotación en production", 
                 prod_settings['type'] == 'time' and prod_settings['backup_count'] == 30,
                 "Configuración incorrecta para production")
    
    def verify_logging_utils(self):
        """Verifica las utilidades de logging."""
        print("\n5. Verificando utilidades de logging...")
        
        # Test LoggerMixin
        class TestClass(LoggerMixin):
            pass
        
        obj = TestClass()
        self.test("LoggerMixin proporciona logger", 
                 hasattr(obj, 'logger') and isinstance(obj.logger, logging.Logger),
                 "Logger no disponible")
        
        # Test sanitize_log_data
        sensitive_data = {
            'username': 'test',
            'password': 'secret',
            'api_key': '12345'
        }
        
        sanitized = sanitize_log_data(sensitive_data)
        self.test("Sanitización de datos sensibles", 
                 sanitized['password'] == '***REDACTED***' and 
                 sanitized['api_key'] == '***REDACTED***' and
                 sanitized['username'] == 'test',
                 "Sanitización incorrecta")
        
        # Test StructuredLogger
        logger = StructuredLogger('test')
        self.test("StructuredLogger creado", 
                 hasattr(logger, 'info') and hasattr(logger, 'error'),
                 "Métodos de logging no disponibles")
    
    def verify_scrapy_integration(self):
        """Verifica la integración con Scrapy."""
        print("\n6. Verificando integración con Scrapy...")
        
        # Test Scrapy settings generation
        settings = LoggingConfig.get_scrapy_settings()
        
        required_keys = ['LOG_LEVEL', 'LOG_FORMAT', 'LOG_DATEFORMAT', 'LOGGERS']
        for key in required_keys:
            self.test(f"Setting {key} presente", 
                     key in settings,
                     "Setting faltante")
        
        # Test component loggers
        self.test("Loggers por componente configurados", 
                 isinstance(settings.get('LOGGERS'), dict) and len(settings['LOGGERS']) > 0,
                 "Loggers no configurados")
    
    def verify_file_creation(self):
        """Verifica que los archivos de log se pueden crear (versión corregida para Windows)."""
        print("\n7. Verificando creación de archivos de log...")
        
        # Usar directorio temporal manual en lugar de TemporaryDirectory
        # para tener mejor control sobre la limpieza en Windows
        import tempfile
        tmpdir = tempfile.mkdtemp()
        log_path = Path(tmpdir) / 'test.log'
        
        try:
            logger = LogRotationConfig.setup_rotating_logger(
                'test_logger_verification',
                log_path,
                max_bytes=1024,
                backup_count=3
            )
            
            # Write test message
            logger.info("Test message for verification")
            
            # Force flush and close handlers
            for handler in logger.handlers[:]:
                handler.flush()
                handler.close()
                logger.removeHandler(handler)
            
            # Small delay to ensure Windows releases the file
            time.sleep(0.1)
            
            self.test("Archivo de log creado", 
                     log_path.exists(),
                     "Archivo no creado")
            
            if log_path.exists():
                # Check content
                content = log_path.read_text(encoding='utf-8')
                self.test("Mensaje escrito en log", 
                         "Test message for verification" in content,
                         "Mensaje no encontrado")
            
            # Manual cleanup
            try:
                if log_path.exists():
                    log_path.unlink()
                Path(tmpdir).rmdir()
            except Exception as cleanup_error:
                print(f"⚠️  Advertencia: No se pudo limpiar archivo temporal: {cleanup_error}")
                
        except Exception as e:
            self.test("Creación de archivo de log", 
                     False,
                     str(e))
            # Cleanup on error
            try:
                if log_path.exists():
                    log_path.unlink()
                Path(tmpdir).rmdir()
            except:
                pass
    
    def verify_decorators(self):
        """Verifica los decoradores de logging."""
        print("\n8. Verificando decoradores...")
        
        # Test log_execution_time
        @log_execution_time
        def test_func():
            return "test"
        
        try:
            result = test_func()
            self.test("Decorador @log_execution_time", 
                     result == "test",
                     "Función no ejecutada correctamente")
        except Exception as e:
            self.test("Decorador @log_execution_time", 
                     False,
                     str(e))
        
        # Test log_exceptions
        @log_exceptions()
        def failing_func():
            raise ValueError("Test error")
        
        try:
            failing_func()
            self.test("Decorador @log_exceptions", 
                     False,
                     "Excepción no lanzada")
        except ValueError:
            self.test("Decorador @log_exceptions", 
                     True,
                     "")
        except Exception as e:
            self.test("Decorador @log_exceptions", 
                     False,
                     f"Excepción incorrecta: {e}")
    
    def print_summary(self):
        """Imprime el resumen de verificación."""
        print("\n" + "="*50)
        print("RESUMEN DE VERIFICACIÓN")
        print("="*50)
        
        for result in self.results:
            print(result)
        
        print("\n" + "-"*50)
        print(f"Total: {self.passed + self.failed} pruebas")
        print(f"Exitosas: {self.passed}")
        print(f"Fallidas: {self.failed}")
        
        if self.failed == 0:
            print("\n✅ ¡Sistema de logging configurado correctamente!")
        else:
            print("\n❌ Se encontraron problemas en la configuración")
        
        return self.failed == 0
    
    def run_all_tests(self):
        """Ejecuta todas las verificaciones."""
        print("VERIFICACIÓN DEL SISTEMA DE LOGGING (VERSIÓN CORREGIDA)")
        print("="*60)
        print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Ambiente: {LoggingConfig.get_environment()}")
        print(f"Nivel de log: {LoggingConfig.get_log_level()}")
        
        # Run all verifications
        self.verify_environment_config()
        self.verify_log_formats()
        self.verify_file_paths()
        self.verify_rotation_config()
        self.verify_logging_utils()
        self.verify_scrapy_integration()
        self.verify_file_creation()
        self.verify_decorators()
        
        # Print summary
        return self.print_summary()


def main():
    """Función principal."""
    verification = LoggingVerification()
    success = verification.run_all_tests()
    
    # Return appropriate exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
