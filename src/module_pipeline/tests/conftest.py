"""
Configuración central para tests del module_pipeline
==================================================

Fixtures y configuración compartida para todos los tests.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock

# Configurar event loop para tests async
@pytest.fixture(scope="session")
def event_loop():
    """Crea un event loop para toda la sesión de tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Mock de configuración para tests
@pytest.fixture
def mock_config():
    """Mock de configuración para tests."""
    return {
        'GROQ_API_KEY': 'test_groq_key',
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_KEY': 'test_supabase_key',
        'LOG_LEVEL': 'DEBUG',
        'API_HOST': '127.0.0.1',
        'API_PORT': 8000
    }

# Mock de cliente Groq
@pytest.fixture
def mock_groq_client():
    """Mock del cliente Groq para tests."""
    mock = AsyncMock()
    mock.chat.completions.create = AsyncMock()
    return mock

# Mock de cliente Supabase
@pytest.fixture
def mock_supabase_client():
    """Mock del cliente Supabase para tests."""
    mock = Mock()
    mock.rpc = Mock()
    return mock

# Datos de prueba para artículos
@pytest.fixture
def sample_article_data():
    """Datos de ejemplo para tests de artículos."""
    return {
        "medio": "Test News",
        "pais_publicacion": "España",
        "tipo_medio": "Digital",
        "titular": "Titular de prueba",
        "fecha_publicacion": "2024-01-15T10:00:00Z",
        "contenido_texto": "Este es un contenido de prueba para el pipeline de procesamiento."
    }

# Datos de prueba para fragmentos
@pytest.fixture
def sample_fragment_data():
    """Datos de ejemplo para tests de fragmentos."""
    return {
        "id_fragmento": "test_fragment_001",
        "texto_original": "Este es un fragmento de prueba para testing.",
        "id_articulo_fuente": "test_article_001",
        "orden_en_articulo": 1,
        "metadata_adicional": {"tipo": "test"}
    }

# Rutas de archivos de prueba
@pytest.fixture
def test_prompts_dir(tmp_path):
    """Crea directorio temporal con prompts de prueba."""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    
    # Crear archivos de prompts de prueba
    prompt_files = [
        "Prompt_1_filtrado.md",
        "Prompt_2_elementos_basicos.md", 
        "Prompt_3_citas_datos.md",
        "Prompt_4_relaciones.md"
    ]
    
    for prompt_file in prompt_files:
        (prompts_dir / prompt_file).write_text(f"# Test prompt for {prompt_file}")
    
    return prompts_dir
