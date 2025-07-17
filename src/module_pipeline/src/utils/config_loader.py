"""
Pipeline Configuration Loader
=============================

Sistema de configuración específico para el Pipeline de 7 Fases.
Extiende la configuración base con variables específicas de pipeline.

Este módulo centraliza todas las configuraciones relacionadas con:
- Thresholds de chunking por tipo de contenido
- Configuración de modelos Groq 
- Parámetros de procesamiento paralelo
- Configuración de consolidación
- Configuración de reintentos y timeouts

Variables de entorno específicas del pipeline:
- PIPELINE_CHUNKING_ENTITIES_THRESHOLD (default: 30)
- PIPELINE_CHUNKING_CHARS_THRESHOLD (default: 6000)
- PIPELINE_CHUNKING_QUOTES_THRESHOLD (default: 30)
- PIPELINE_CHUNKING_DATA_THRESHOLD (default: 30)
- PIPELINE_GROQ_MODEL_DEFAULT (default: llama-3.1-8b-instant)
- PIPELINE_GROQ_MODEL_LARGE (default: llama-3.2-90b-text-preview)
- PIPELINE_GROQ_MODEL_TOKEN_THRESHOLD (default: 8000)
- PIPELINE_CONSOLIDATION_SIMILARITY_THRESHOLD (default: 0.85)
- PIPELINE_MAX_RETRIES_PER_PHASE (default: 3)
- PIPELINE_CHUNK_PARALLEL_ENABLED (default: true)
- PIPELINE_MAX_CONCURRENT_CHUNKS (default: 5)
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# =============================================================================
# UTILIDADES DE CONVERSIÓN DE TIPOS
# =============================================================================

def _get_bool_env(var_name: str, default: bool = False) -> bool:
    """Convierte variable de entorno a booleano con manejo robusto."""
    value = os.getenv(var_name, str(default)).lower()
    return value in ('true', '1', 'yes', 'on', 'enabled')

def _get_int_env(var_name: str, default: int) -> int:
    """Convierte variable de entorno a entero con manejo de errores."""
    try:
        return int(os.getenv(var_name, str(default)))
    except ValueError:
        print(f"⚠️  WARNING: Variable {var_name} no es un número válido, usando default: {default}")
        return default

def _get_float_env(var_name: str, default: float) -> float:
    """Convierte variable de entorno a float con manejo de errores."""
    try:
        return float(os.getenv(var_name, str(default)))
    except ValueError:
        print(f"⚠️  WARNING: Variable {var_name} no es un número válido, usando default: {default}")
        return default

def _get_str_env(var_name: str, default: str) -> str:
    """Obtiene variable de entorno string con valor por defecto."""
    return os.getenv(var_name, default)

# =============================================================================
# CLASES DE CONFIGURACIÓN
# =============================================================================

@dataclass
class ChunkingConfig:
    """Configuración para thresholds de chunking por tipo de contenido."""
    entities_threshold: int = field(default=30)
    chars_threshold: int = field(default=6000)
    quotes_threshold: int = field(default=30)
    data_threshold: int = field(default=30)
    
    def __post_init__(self):
        """Validar thresholds después de inicialización."""
        if self.entities_threshold <= 0:
            raise ValueError("entities_threshold debe ser > 0")
        if self.chars_threshold <= 100:
            raise ValueError("chars_threshold debe ser > 100")
        if self.quotes_threshold <= 0:
            raise ValueError("quotes_threshold debe ser > 0")
        if self.data_threshold <= 0:
            raise ValueError("data_threshold debe ser > 0")

@dataclass 
class GroqModelConfig:
    """Configuración para modelos Groq utilizados en el pipeline."""
    default_model: str = field(default="llama-3.1-8b-instant")
    large_model: str = field(default="llama3-70b-8192")
    token_threshold: int = field(default=8000)
    
    def __post_init__(self):
        """Validar configuración de modelos."""
        if self.token_threshold <= 0:
            raise ValueError("token_threshold debe ser > 0")
        if not self.default_model:
            raise ValueError("default_model no puede estar vacío")
        if not self.large_model:
            raise ValueError("large_model no puede estar vacío")

@dataclass
class ProcessingConfig:
    """Configuración para procesamiento del pipeline."""
    consolidation_similarity_threshold: float = field(default=0.85)
    max_retries_per_phase: int = field(default=3)
    chunk_parallel_enabled: bool = field(default=True)
    max_concurrent_chunks: int = field(default=5)
    
    def __post_init__(self):
        """Validar configuración de procesamiento."""
        if not (0.0 <= self.consolidation_similarity_threshold <= 1.0):
            raise ValueError("consolidation_similarity_threshold debe estar entre 0.0 y 1.0")
        if self.max_retries_per_phase < 0:
            raise ValueError("max_retries_per_phase debe ser >= 0")
        if self.max_concurrent_chunks <= 0:
            raise ValueError("max_concurrent_chunks debe ser > 0")

@dataclass
class PipelineConfig:
    """Configuración completa del pipeline de 7 fases."""
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    groq_models: GroqModelConfig = field(default_factory=GroqModelConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la configuración a diccionario para serialización."""
        return {
            "chunking": {
                "entities_threshold": self.chunking.entities_threshold,
                "chars_threshold": self.chunking.chars_threshold,
                "quotes_threshold": self.chunking.quotes_threshold,
                "data_threshold": self.chunking.data_threshold
            },
            "groq_models": {
                "default_model": self.groq_models.default_model,
                "large_model": self.groq_models.large_model,
                "token_threshold": self.groq_models.token_threshold
            },
            "processing": {
                "consolidation_similarity_threshold": self.processing.consolidation_similarity_threshold,
                "max_retries_per_phase": self.processing.max_retries_per_phase,
                "chunk_parallel_enabled": self.processing.chunk_parallel_enabled,
                "max_concurrent_chunks": self.processing.max_concurrent_chunks
            }
        }

# =============================================================================
# CARGA DE CONFIGURACIÓN DESDE VARIABLES DE ENTORNO
# =============================================================================

def load_pipeline_config() -> PipelineConfig:
    """
    Carga la configuración del pipeline desde variables de entorno.
    
    Returns:
        PipelineConfig: Configuración completa del pipeline
        
    Raises:
        ValueError: Si alguna variable de configuración es inválida
    """
    # Configuración de chunking
    chunking_config = ChunkingConfig(
        entities_threshold=_get_int_env('PIPELINE_CHUNKING_ENTITIES_THRESHOLD', 30),
        chars_threshold=_get_int_env('PIPELINE_CHUNKING_CHARS_THRESHOLD', 6000),
        quotes_threshold=_get_int_env('PIPELINE_CHUNKING_QUOTES_THRESHOLD', 30),
        data_threshold=_get_int_env('PIPELINE_CHUNKING_DATA_THRESHOLD', 30)
    )
    
    # Configuración de modelos Groq
    groq_config = GroqModelConfig(
        default_model=_get_str_env('PIPELINE_GROQ_MODEL_DEFAULT', 'llama-3.1-8b-instant'),
        large_model=_get_str_env('PIPELINE_GROQ_MODEL_LARGE', 'llama3-70b-8192'),
        token_threshold=_get_int_env('PIPELINE_GROQ_MODEL_TOKEN_THRESHOLD', 8000)
    )
    
    # Configuración de procesamiento
    processing_config = ProcessingConfig(
        consolidation_similarity_threshold=_get_float_env('PIPELINE_CONSOLIDATION_SIMILARITY_THRESHOLD', 0.85),
        max_retries_per_phase=_get_int_env('PIPELINE_MAX_RETRIES_PER_PHASE', 3),
        chunk_parallel_enabled=_get_bool_env('PIPELINE_CHUNK_PARALLEL_ENABLED', True),
        max_concurrent_chunks=_get_int_env('PIPELINE_MAX_CONCURRENT_CHUNKS', 5)
    )
    
    return PipelineConfig(
        chunking=chunking_config,
        groq_models=groq_config,
        processing=processing_config
    )

# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================

def get_chunking_config() -> ChunkingConfig:
    """Retorna solo la configuración de chunking."""
    return load_pipeline_config().chunking

def get_groq_model_config() -> GroqModelConfig:
    """Retorna solo la configuración de modelos Groq.""" 
    return load_pipeline_config().groq_models

def get_processing_config() -> ProcessingConfig:
    """Retorna solo la configuración de procesamiento."""
    return load_pipeline_config().processing

def should_use_large_model(text_length: int) -> bool:
    """
    Determina si se debe usar el modelo grande basado en la longitud del texto.
    
    Args:
        text_length: Longitud del texto en caracteres
        
    Returns:
        bool: True si se debe usar el modelo grande
    """
    config = get_groq_model_config()
    return text_length > config.token_threshold

def should_chunk_content(content_type: str, count: int, text_length: int) -> bool:
    """
    Determina si el contenido debe ser dividido en chunks.
    
    Args:
        content_type: Tipo de contenido ('entities', 'quotes', 'data', 'chars')
        count: Cantidad de elementos del tipo especificado
        text_length: Longitud del texto en caracteres
        
    Returns:
        bool: True si se debe dividir en chunks
    """
    config = get_chunking_config()
    
    if content_type == 'entities':
        return count > config.entities_threshold
    elif content_type == 'quotes':
        return count > config.quotes_threshold
    elif content_type == 'data':
        return count > config.data_threshold
    elif content_type == 'chars':
        return text_length > config.chars_threshold
    else:
        # Por defecto usar threshold de caracteres
        return text_length > config.chars_threshold

def get_chunk_parallel_settings() -> Dict[str, Any]:
    """
    Retorna configuración para procesamiento paralelo de chunks.
    
    Returns:
        Dict con configuración de paralelización
    """
    config = get_processing_config()
    
    return {
        'enabled': config.chunk_parallel_enabled,
        'max_concurrent_chunks': config.max_concurrent_chunks,
        'retry_limit': config.max_retries_per_phase
    }

def validate_pipeline_config(config: PipelineConfig) -> bool:
    """
    Valida que la configuración del pipeline sea coherente.
    
    Args:
        config: Configuración a validar
        
    Returns:
        bool: True si la configuración es válida
    """
    errors = []
    
    # Validar que los modelos sean conocidos
    known_models = [
        'llama-3.1-8b-instant',
        'llama-3.1-70b-versatile',
        'llama3-70b-8192'
    ]
    
    if config.groq_models.default_model not in known_models:
        errors.append(f"Modelo default desconocido: {config.groq_models.default_model}")
    
    if config.groq_models.large_model not in known_models:
        errors.append(f"Modelo large desconocido: {config.groq_models.large_model}")
    
    # Validar coherencia de thresholds
    if config.chunking.chars_threshold < 1000:
        errors.append("chars_threshold muy bajo, podría generar demasiados chunks")
    
    if config.processing.max_concurrent_chunks > 10:
        errors.append("max_concurrent_chunks muy alto, podría causar rate limiting")
    
    # Mostrar errores si los hay
    if errors:
        print("❌ ERRORES DE CONFIGURACIÓN DEL PIPELINE:")
        for error in errors:
            print(f"   - {error}")
        return False
    
    return True

def print_pipeline_config_summary(config: Optional[PipelineConfig] = None):
    """
    Imprime un resumen de la configuración del pipeline.
    
    Args:
        config: Configuración específica, si no se provee se carga desde env
    """
    if config is None:
        config = load_pipeline_config()
    
    print("🔧 CONFIGURACIÓN DEL PIPELINE 7 FASES")
    print("=" * 60)
    print("📊 CHUNKING THRESHOLDS:")
    print(f"  - Entidades: {config.chunking.entities_threshold}")
    print(f"  - Caracteres: {config.chunking.chars_threshold:,}")
    print(f"  - Citas: {config.chunking.quotes_threshold}")
    print(f"  - Datos: {config.chunking.data_threshold}")
    print()
    print("🤖 MODELOS GROQ:")
    print(f"  - Default: {config.groq_models.default_model}")
    print(f"  - Large: {config.groq_models.large_model}")
    print(f"  - Token threshold: {config.groq_models.token_threshold:,}")
    print()
    print("⚡ PROCESAMIENTO:")
    print(f"  - Similarity threshold: {config.processing.consolidation_similarity_threshold}")
    print(f"  - Max retries: {config.processing.max_retries_per_phase}")
    print(f"  - Parallel chunks: {config.processing.chunk_parallel_enabled}")
    print(f"  - Max concurrent: {config.processing.max_concurrent_chunks}")
    print("=" * 60)

# =============================================================================
# INSTANCIA GLOBAL DE CONFIGURACIÓN
# =============================================================================

# Cargar configuración al importar el módulo
_pipeline_config: Optional[PipelineConfig] = None

def get_pipeline_config() -> PipelineConfig:
    """
    Retorna la instancia global de configuración del pipeline.
    Se carga una sola vez y se reutiliza.
    
    Returns:
        PipelineConfig: Configuración global del pipeline
    """
    global _pipeline_config
    
    if _pipeline_config is None:
        _pipeline_config = load_pipeline_config()
        
        # Validar configuración cargada
        if not validate_pipeline_config(_pipeline_config):
            raise ValueError("Configuración del pipeline inválida")
    
    return _pipeline_config

def reload_pipeline_config() -> PipelineConfig:
    """
    Recarga la configuración del pipeline desde variables de entorno.
    Útil para testing o cambios dinámicos.
    
    Returns:
        PipelineConfig: Nueva configuración del pipeline
    """
    global _pipeline_config
    _pipeline_config = None
    return get_pipeline_config()

# =============================================================================
# MODO DE PRUEBA
# =============================================================================

if __name__ == '__main__':
    print("🧪 MODO DE PRUEBA - PIPELINE CONFIG LOADER")
    print("=" * 60)
    
    try:
        config = load_pipeline_config()
        print("✅ Configuración cargada exitosamente")
        print()
        print_pipeline_config_summary(config)
        print()
        print(f"✅ Validación: {'VÁLIDA' if validate_pipeline_config(config) else 'INVÁLIDA'}")
        
        # Pruebas de funciones utilitarias
        print()
        print("🧪 PRUEBAS DE FUNCIONES:")
        print(f"  - should_use_large_model(10000): {should_use_large_model(10000)}")
        print(f"  - should_chunk_content('chars', 0, 10000): {should_chunk_content('chars', 0, 10000)}")
        print(f"  - should_chunk_content('entities', 50, 1000): {should_chunk_content('entities', 50, 1000)}")
        
        parallel_settings = get_chunk_parallel_settings()
        print(f"  - Parallel settings: {parallel_settings}")
        
    except Exception as e:
        print(f"❌ Error cargando configuración: {e}")