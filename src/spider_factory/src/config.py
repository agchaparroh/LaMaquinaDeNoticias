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
    
    # Spider Generation
    spider_output_dir: str = os.getenv(
        "SPIDER_OUTPUT_DIR", 
        "/mnt/c/Users/DELL/Desktop/PruebaWindsurfAI/LaMaquinaDeNoticias/src/module_scraper/scraper_core/spiders"
    )
    spider_template_dir: str = os.getenv(
        "SPIDER_TEMPLATE_DIR", 
        "/mnt/c/Users/DELL/Desktop/PruebaWindsurfAI/LaMaquinaDeNoticias/src/spider_factory/templates"
    )
    
    # Limits
    max_urls_per_analysis: int = int(os.getenv("MAX_URLS_PER_ANALYSIS", "10"))
    max_batch_size: int = int(os.getenv("MAX_BATCH_SIZE", "100"))
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"


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


# Instancia global de configuración
config = SpiderFactoryConfig()
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
            "api_host": config.api_host,
            "api_port": config.api_port,
            "firecrawl_configured": bool(config.firecrawl_api_key),
            "spider_output_dir": config.spider_output_dir,
            "log_level": config.log_level
        }
    }


if __name__ == "__main__":
    # Test de configuración
    print("=== Spider Factory 2.0 - Configuración ===")
    print(f"Redis Config: {RedisConfig()}")
    print(f"Spider Factory Config: {config}")
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