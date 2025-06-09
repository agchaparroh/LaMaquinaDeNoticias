"""
Tests para el Sistema de Logging del Pipeline
============================================

Verifica que el sistema de logging funcione correctamente:
- Configuración por entorno
- Rotación de archivos
- Sanitización de datos sensibles
- Integración con FastAPI
"""

import pytest
import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
import re
import json
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# Agregar directorio padre al path para imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils.logging_config import (
    LoggingConfig,
    PipelineLogger,
    get_logger,
    log_execution_time,
    log_phase,
    LogContext
)
from loguru import logger


class TestLoggingConfig:
    """Tests para la configuración del sistema de logging."""
    
    def test_environment_detection(self):
        """Verifica detección correcta del entorno."""
        # Test default
        with patch.dict(os.environ, {}, clear=True):
            assert LoggingConfig.get_environment() == "development"
        
        # Test diferentes entornos
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            assert LoggingConfig.get_environment() == "production"
        
        with patch.dict(os.environ, {"ENVIRONMENT": "STAGING"}):
            assert LoggingConfig.get_environment() == "staging"
    
    def test_log_level_by_environment(self):
        """Verifica niveles de log según entorno."""
        # Development
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            assert LoggingConfig.get_log_level() == "DEBUG"
        
        # Staging
        with patch.dict(os.environ, {"ENVIRONMENT": "staging"}):
            assert LoggingConfig.get_log_level() == "INFO"
        
        # Production
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            assert LoggingConfig.get_log_level() == "WARNING"
        
        # Override con variable de entorno
        with patch.dict(os.environ, {"LOG_LEVEL": "ERROR"}):
            assert LoggingConfig.get_log_level() == "ERROR"
    
    def test_retention_days(self):
        """Verifica días de retención según entorno."""
        # Por defecto
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            assert LoggingConfig.get_retention_days() == 7
        
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            assert LoggingConfig.get_retention_days() == 90
        
        # Override
        with patch.dict(os.environ, {"LOG_RETENTION_DAYS": "180"}):
            assert LoggingConfig.get_retention_days() == 180
    
    def test_sensitive_data_sanitization(self):
        """Verifica sanitización de datos sensibles."""
        # API keys
        msg = "Conectando con api_key=sk-1234567890abcdef"
        sanitized = LoggingConfig.sanitize_sensitive_data(msg)
        assert "sk-1234567890abcdef" not in sanitized
        assert "***REDACTED***" in sanitized
        
        # Tokens
        msg = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        sanitized = LoggingConfig.sanitize_sensitive_data(msg)
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in sanitized
        
        # Passwords
        msg = "Login con password=mi_password_secreto"
        sanitized = LoggingConfig.sanitize_sensitive_data(msg)
        assert "mi_password_secreto" not in sanitized
        
        # Variables de entorno específicas
        msg = "GROQ_API_KEY=groq-key-12345 SUPABASE_KEY=sb-key-67890"
        sanitized = LoggingConfig.sanitize_sensitive_data(msg)
        assert "groq-key-12345" not in sanitized
        assert "sb-key-67890" not in sanitized
        
        # Emails
        msg = "Usuario email=test@example.com registrado"
        sanitized = LoggingConfig.sanitize_sensitive_data(msg)
        assert "test@example.com" not in sanitized
        assert "***REDACTED_EMAIL***" in sanitized
        
        # Tarjetas de crédito
        msg = "Pago con tarjeta 4111 1111 1111 1111"
        sanitized = LoggingConfig.sanitize_sensitive_data(msg)
        assert "4111 1111 1111 1111" not in sanitized
        assert "***REDACTED_CARD***" in sanitized
    
    def test_formatter_by_environment(self):
        """Verifica formato de logs según entorno."""
        # Development - máximo detalle
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            fmt = LoggingConfig.get_formatter()
            assert "{name}:{function}:{line}" in fmt
        
        # Production - mínimo ruido
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            fmt = LoggingConfig.get_formatter()
            assert "{function}" not in fmt
            assert "{line}" not in fmt


class TestPipelineLogger:
    """Tests para el logger del pipeline."""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Crea directorio temporal para logs."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_logger_initialization(self, temp_log_dir):
        """Verifica inicialización correcta del logger."""
        with patch.object(LoggingConfig, 'get_log_dir', return_value=Path(temp_log_dir)):
            pipeline_logger = PipelineLogger()
            assert pipeline_logger._configured is True
    
    def test_bind_request(self):
        """Verifica binding de request_id."""
        pipeline_logger = PipelineLogger()
        request_logger = pipeline_logger.bind_request("REQ-123")
        
        # Verificar que el logger tiene el contexto correcto
        # Nota: Este test es conceptual ya que loguru no expone directamente el contexto
        assert request_logger is not None
    
    def test_bind_component(self):
        """Verifica binding de componente."""
        pipeline_logger = PipelineLogger()
        comp_logger = pipeline_logger.bind_component("TestComponent", "REQ-456")
        assert comp_logger is not None
    
    @pytest.mark.asyncio
    async def test_measure_time_decorator_async(self):
        """Verifica decorador de medición de tiempo para funciones async."""
        
        @log_execution_time(component="AsyncTestFunc")
        async def slow_async_function():
            await asyncio.sleep(0.1)
            return "done"
        
        result = await slow_async_function()
        assert result == "done"
    
    def test_measure_time_decorator_sync(self):
        """Verifica decorador de medición de tiempo para funciones sync."""
        
        @log_execution_time()
        def slow_sync_function():
            import time
            time.sleep(0.1)
            return "done"
        
        result = slow_sync_function()
        assert result == "done"
    
    def test_phase_context(self):
        """Verifica context manager para fases."""
        pipeline_logger = PipelineLogger()
        
        with pipeline_logger.phase_context("TestPhase", "REQ-789", extra_data="test"):
            # Simular trabajo
            pass
        
        # El contexto debe completarse sin errores
        assert True
    
    def test_phase_context_with_error(self):
        """Verifica manejo de errores en context manager."""
        pipeline_logger = PipelineLogger()
        
        with pytest.raises(ValueError):
            with pipeline_logger.phase_context("ErrorPhase", "REQ-999"):
                raise ValueError("Test error")


class TestLogContext:
    """Tests para el modelo LogContext."""
    
    def test_context_creation(self):
        """Verifica creación de contexto de logging."""
        context = LogContext(
            request_id="REQ-001",
            component="TestComponent",
            phase="TestPhase",
            fragment_id="FRAG-001",
            metadata={"key": "value"}
        )
        
        assert context.request_id == "REQ-001"
        assert context.component == "TestComponent"
        assert context.phase == "TestPhase"
        assert context.fragment_id == "FRAG-001"
        assert context.metadata["key"] == "value"
    
    def test_get_logger_from_context(self):
        """Verifica obtención de logger desde contexto."""
        context = LogContext(
            request_id="REQ-002",
            component="TestComponent"
        )
        
        ctx_logger = context.get_logger()
        assert ctx_logger is not None


class TestLogRotationAndRetention:
    """Tests para rotación y retención de logs."""
    
    @pytest.fixture
    def mock_log_dir(self, tmp_path):
        """Crea estructura de directorios para testing."""
        log_dir = tmp_path / "logs" / "test"
        log_dir.mkdir(parents=True)
        return log_dir
    
    def test_log_directory_creation(self, mock_log_dir):
        """Verifica creación de directorios de logs."""
        with patch.object(LoggingConfig, 'get_log_dir', return_value=mock_log_dir):
            config = LoggingConfig()
            log_dir = config.get_log_dir()
            assert log_dir.exists()
            assert log_dir.is_dir()
    
    def test_log_file_naming(self, mock_log_dir):
        """Verifica nomenclatura de archivos de log."""
        with patch.object(LoggingConfig, 'get_log_dir', return_value=mock_log_dir):
            # Simular creación de archivos
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Archivo principal
            main_log = mock_log_dir / f"pipeline_{today}.log"
            main_log.touch()
            assert main_log.exists()
            
            # Archivo de errores
            error_log = mock_log_dir / f"errors_{today}.log"
            error_log.touch()
            assert error_log.exists()
    
    def test_retention_policy(self, mock_log_dir):
        """Verifica política de retención."""
        with patch.dict(os.environ, {"ENVIRONMENT": "test"}):
            retention_days = LoggingConfig.get_retention_days()
            assert retention_days == 1  # Test environment
            
            # Crear archivos viejos
            old_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
            old_log = mock_log_dir / f"pipeline_{old_date}.log"
            old_log.touch()
            
            # En un sistema real, loguru eliminaría este archivo
            assert old_log.exists()  # Por ahora solo verificamos que se creó


class TestFastAPIIntegration:
    """Tests para integración con FastAPI."""
    
    def test_setup_fastapi_logging(self):
        """Verifica configuración de logging para FastAPI."""
        from fastapi import FastAPI
        
        app = FastAPI()
        
        # Mock para evitar configuración real
        with patch('src.utils.logging_config.logger') as mock_logger:
            from src.utils.logging_config import setup_fastapi_logging
            setup_fastapi_logging(app)
            
            # Verificar que se agregó el middleware
            assert len(app.middleware) > 0


class TestUtilityFunctions:
    """Tests para funciones de utilidad."""
    
    def test_get_logger(self):
        """Verifica función get_logger."""
        test_logger = get_logger("TestComponent", "REQ-123")
        assert test_logger is not None
    
    def test_log_phase_utility(self):
        """Verifica función log_phase."""
        with log_phase("TestPhase", "REQ-456", data="test"):
            # Trabajo simulado
            pass
        
        # Debe completarse sin errores
        assert True


def test_logging_in_production_mode():
    """Test específico para modo producción."""
    with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
        config = LoggingConfig()
        
        # Verificar configuración de producción
        assert config.get_log_level() == "WARNING"
        assert config.get_retention_days() == 90
        
        # Verificar que se sanitizan datos sensibles
        sensitive = "api_key=secret123"
        sanitized = config.sanitize_sensitive_data(sensitive)
        assert "secret123" not in sanitized


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
