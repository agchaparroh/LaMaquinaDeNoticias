"""
Configuración central para Spider Factory 2.0
Maneja conexiones a Redis y configuraciones del sistema

Basado en la documentación oficial de Redis y redis-py
"""
import os
from typing import Optional, Dict, Any
import redis
from redis import ConnectionPool
from dataclasses import dataclass
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class RedisConfig:
    """
    Configuración para conexión a Redis
    Basado en la documentación oficial de redis-py para connection pooling
    """
    host: str = os.getenv("REDIS_HOST", "localhost")
    port: int = int(os.getenv("REDIS_PORT", "6379"))
    db: int = int(os.getenv("REDIS_DB", "0"))
    password: Optional[str] = os.getenv("REDIS_PASSWORD")
    decode_responses: bool = True  # Para trabajar con strings en lugar de bytes
    max_connections: int = int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))
    socket_timeout: int = int(os.getenv("REDIS_SOCKET_TIMEOUT", "5"))
    socket_connect_timeout: int = int(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", "5"))
    retry_on_timeout: bool = True
    health_check_interval: int = 30


@dataclass
class SpiderFactoryConfig:
    """Configuración general de Spider Factory"""
    # API Configuration
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8005"))
    api_reload: bool = os.getenv("API_RELOAD", "true").lower() == "true"
    
    # Firecrawl Configuration
    firecrawl_api_key: str = os.getenv("FIRECRAWL_API_KEY", "")
    firecrawl_base_url: str = os.getenv("FIRECRAWL_BASE_URL", "https://api.firecrawl.dev/v1")
    firecrawl_timeout: int = int(os.getenv("FIRECRAWL_TIMEOUT", "30"))
    
    # Cache Configuration (TTL en segundos)
    cache_ttl_analysis: int = int(os.getenv("CACHE_TTL_ANALYSIS", "86400"))  # 24 horas
    cache_ttl_patterns: int = int(os.getenv("CACHE_TTL_PATTERNS", "604800"))  # 7 días
    cache_ttl_spiders: int = int(os.getenv("CACHE_TTL_SPIDERS", "2592000"))  # 30 días
    
    # Cache TTL en días (para compatibilidad)
    CACHE_TTL_DAYS: int = 7
    CACHE_TTL_SECONDS: int = 7 * 86400  # 604800 segundos
    
    # Spider Generation
    spider_output_dir: str = os.getenv(
        "SPIDER_OUTPUT_DIR", 
        "/app/generated_spiders"
    )
    SPIDER_OUTPUT_PATH: str = spider_output_dir  # Alias para compatibilidad
    
    spider_template_dir: str = os.getenv(
        "SPIDER_TEMPLATE_DIR", 
        "/app/templates"
    )
    
    # Batch Processing
    max_urls_per_analysis: int = int(os.getenv("MAX_URLS_PER_ANALYSIS", "10"))
    max_batch_size: int = int(os.getenv("MAX_BATCH_SIZE", "100"))
    MAX_BATCH_SIZE: int = max_batch_size  # Alias para compatibilidad
    CONCURRENT_REQUESTS: int = int(os.getenv("CONCURRENT_REQUESTS", "10"))
    BATCH_TIMEOUT: int = int(os.getenv("BATCH_TIMEOUT", "300"))  # 5 minutos
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # segundos
    
    # Redis Connection Pool
    REDIS_MAX_CONNECTIONS: int = int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))
    
    # Redis connection settings (para redis_pool.py)
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    
    def validate_config(self):
        """Valida configuración al iniciar"""
        from pathlib import Path
        
        # Verificar API key de Firecrawl
        if not self.firecrawl_api_key:
            logger.warning("Firecrawl API key no configurada")
        
        # Verificar directorio de salida
        output_path = Path(self.SPIDER_OUTPUT_PATH)
        if not output_path.exists():
            logger.error(f"Directorio de spiders no existe: {self.SPIDER_OUTPUT_PATH}")
            # Intentar crear el directorio
            try:
                output_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Directorio creado: {self.SPIDER_OUTPUT_PATH}")
            except Exception as e:
                logger.error(f"No se pudo crear el directorio: {e}")
        
        # Verificar Redis
        try:
            redis_client = get_redis_client()
            redis_client.ping()
            logger.info("Conexión a Redis verificada")
        except Exception as e:
            logger.error(f"No se puede conectar a Redis: {e}")
        
        # Verificar directorio de templates
        template_path = Path(self.spider_template_dir)
        if not template_path.exists():
            logger.error(f"Directorio de templates no existe: {self.spider_template_dir}")
        
        logger.info("Validación de configuración completada")


class RedisManager:
    """
    Gestor de conexiones Redis con pooling
    Implementa patrón Singleton para reutilizar el pool de conexiones
    """
    
    _instance: Optional['RedisManager'] = None
    _pool: Optional[ConnectionPool] = None
    
    def __new__(cls) -> 'RedisManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._pool is None:
            config = RedisConfig()
            # Crear pool de conexiones según documentación oficial
            self._pool = ConnectionPool(
                host=config.host,
                port=config.port,
                db=config.db,
                password=config.password,
                decode_responses=config.decode_responses,
                max_connections=config.max_connections,
                socket_timeout=config.socket_timeout,
                socket_connect_timeout=config.socket_connect_timeout,
                retry_on_timeout=config.retry_on_timeout,
                health_check_interval=config.health_check_interval
            )
            logger.info(f"Redis connection pool creado: {config.host}:{config.port}")
    
    def get_client(self) -> redis.Redis:
        """
        Obtiene un cliente Redis del pool
        El cliente usa automáticamente el pool para gestionar conexiones
        """
        return redis.Redis(connection_pool=self._pool)
    
    def health_check(self) -> bool:
        """Verifica la salud de la conexión Redis"""
        try:
            client = self.get_client()
            return client.ping()
        except Exception as e:
            logger.error(f"Redis health check falló: {e}")
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """Obtiene información del servidor Redis"""
        try:
            client = self.get_client()
            info = client.info()
            return {
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "total_connections_received": info.get("total_connections_received"),
                "total_commands_processed": info.get("total_commands_processed"),
            }
        except Exception as e:
            logger.error(f"Error obteniendo info de Redis: {e}")
            return {}


# Estructura de claves Redis para el sistema
class RedisKeys:
    """
    Define la estructura de claves para Redis siguiendo las mejores prácticas
    Usa nomenclatura consistente con prefijos y separadores
    """
    
    # Prefijos principales
    PREFIX = "spider_factory"
    
    # Análisis de sitios
    ANALYSIS_PREFIX = f"{PREFIX}:analysis"
    ANALYSIS_KEY = f"{ANALYSIS_PREFIX}:{{domain}}"
    ANALYSIS_LOCK = f"{ANALYSIS_PREFIX}:lock:{{domain}}"
    
    # Patrones detectados (usando hash para eficiencia)
    PATTERNS_PREFIX = f"{PREFIX}:patterns"
    PATTERN_KEY = f"{PATTERNS_PREFIX}:{{domain}}:{{section}}"
    PATTERNS_BY_DOMAIN = f"{PATTERNS_PREFIX}:domain:{{domain}}"
    PATTERN_CONFIDENCE = f"{PATTERNS_PREFIX}:confidence:{{pattern_id}}"
    
    # Spiders generados
    SPIDERS_PREFIX = f"{PREFIX}:spiders"
    SPIDER_KEY = f"{SPIDERS_PREFIX}:{{spider_name}}"
    SPIDER_BY_DOMAIN = f"{SPIDERS_PREFIX}:domain:{{domain}}"
    SPIDER_METADATA = f"{SPIDERS_PREFIX}:metadata:{{spider_name}}"
    
    # Estadísticas y métricas (usando sorted sets para rankings)
    STATS_PREFIX = f"{PREFIX}:stats"
    STATS_ANALYSIS_COUNT = f"{STATS_PREFIX}:analysis:count"
    STATS_SPIDER_COUNT = f"{STATS_PREFIX}:spider:count"
    STATS_PATTERN_COUNT = f"{STATS_PREFIX}:pattern:count"
    STATS_PATTERN_USAGE = f"{STATS_PREFIX}:pattern:usage"  # Sorted set
    STATS_DAILY_USAGE = f"{STATS_PREFIX}:usage:{{date}}"
    
    # Colas y trabajos (usando lists para FIFO)
    QUEUE_PREFIX = f"{PREFIX}:queue"
    QUEUE_ANALYSIS = f"{QUEUE_PREFIX}:analysis"
    QUEUE_GENERATION = f"{QUEUE_PREFIX}:generation"
    
    # Cache de resultados
    CACHE_PREFIX = f"{PREFIX}:cache"
    CACHE_RSS_CHECK = f"{CACHE_PREFIX}:rss:{{url}}"
    CACHE_SELECTORS = f"{CACHE_PREFIX}:selectors:{{domain}}"
    
    # Batch jobs (usando hash para estado)
    BATCH_PREFIX = f"{PREFIX}:batch"
    BATCH_JOB = f"{BATCH_PREFIX}:{{batch_id}}"
    
    @classmethod
    def format_key(cls, template: str, **kwargs) -> str:
        """Formatea una clave con los parámetros dados"""
        return template.format(**kwargs)


# Lista de áreas geográficas válidas según el plan
AREAS_GEOGRAFICAS_VALIDAS = [
    'HISPANIDAD', 'HISPANOAMERICA', 'CENTROAMERICA', 'CARIBE_HISPANO',
    'SUDAMERICA', 'TERRITORIOS_OCUPADOS', 'DIASPORA_HISPANA_USA',
    'GLOBAL', 'PAISES_NO_HISPANOS',
    'ARGENTINA', 'BOLIVIA', 'CHILE', 'COLOMBIA', 'COSTA_RICA',
    'CUBA', 'ECUADOR', 'EL_SALVADOR', 'ESPAÑA', 'FILIPINAS',
    'GUATEMALA', 'GUINEA_ECUATORIAL', 'HONDURAS', 'MÉXICO',
    'NICARAGUA', 'PANAMÁ', 'PARAGUAY', 'PERÚ', 'PUERTO_RICO',
    'REPÚBLICA_DOMINICANA', 'SAHARA_OCCIDENTAL', 'URUGUAY', 'VENEZUELA'
]

# Headers HTTP realistas para evasión
STEALTH_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8,en-US;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Pragma": "no-cache",
}

# Configuración base para todos los spiders generados
BASE_SPIDER_SETTINGS = {
    'DEFAULT_REQUEST_HEADERS': STEALTH_HEADERS,
    'REFERER_ENABLED': True,
    'SMART_REFERER_ENABLED': True,
}

# Instancia global de configuración
settings = SpiderFactoryConfig()
redis_manager = RedisManager()


def get_redis_client() -> redis.Redis:
    """Función de conveniencia para obtener cliente Redis"""
    return redis_manager.get_client()


def check_system_health() -> Dict[str, Any]:
    """Verifica la salud general del sistema"""
    return {
        "redis_healthy": redis_manager.health_check(),
        "redis_info": redis_manager.get_info(),
        "config": {
            "api_host": settings.api_host,
            "api_port": settings.api_port,
            "firecrawl_configured": bool(settings.firecrawl_api_key),
            "spider_output_dir": settings.spider_output_dir,
            "log_level": settings.log_level
        }
    }


if __name__ == "__main__":
    # Test de configuración
    print("=== Spider Factory 2.0 - Configuración ===")
    print(f"Redis Config: {RedisConfig()}")
    print(f"Spider Factory Config: {settings}")
    print(f"\nHealth Check: {check_system_health()}")
    
    # Test de claves
    print(f"\nEjemplo de claves Redis:")
    print(f"Analysis: {RedisKeys.format_key(RedisKeys.ANALYSIS_KEY, domain='example.com')}")
    print(f"Pattern: {RedisKeys.format_key(RedisKeys.PATTERN_KEY, domain='example.com', section='news')}")
    print(f"Spider: {RedisKeys.format_key(RedisKeys.SPIDER_KEY, spider_name='example_spider')}")
    print(f"Batch Job: {RedisKeys.format_key(RedisKeys.BATCH_JOB, batch_id='uuid-123')}")
    
    # Test de operaciones básicas
    try:
        client = get_redis_client()
        # Test SET/GET
        client.set("test:key", "test_value", ex=60)  # Expira en 60 segundos
        value = client.get("test:key")
        print(f"\nTest Redis SET/GET: {value}")
        
        # Limpiar
        client.delete("test:key")
        print("Test completado exitosamente")
    except Exception as e:
        print(f"Error en test: {e}")