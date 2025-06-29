"""
Redis Connection Pool para Spider Factory 2.0
Implementa connection pooling asíncrono con límite de 50 conexiones
"""
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool
from typing import Optional
import logging
from .config import settings

logger = logging.getLogger(__name__)


class RedisConnectionPool:
    """
    Gestor de pool de conexiones Redis asíncrono
    Implementa patrón Singleton para reutilizar el pool
    """
    _instance: Optional['RedisConnectionPool'] = None
    _pool: Optional[ConnectionPool] = None
    
    def __new__(cls) -> 'RedisConnectionPool':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def get_pool(self) -> ConnectionPool:
        """
        Obtiene o crea el pool de conexiones
        Configurado con máximo 50 conexiones según requerimientos
        """
        if self._pool is None:
            # Usar configuración desde settings
            redis_host = getattr(settings, 'REDIS_HOST', 'localhost')
            redis_port = getattr(settings, 'REDIS_PORT', 6379)
            redis_db = getattr(settings, 'REDIS_DB', 0)
            redis_password = getattr(settings, 'REDIS_PASSWORD', None)
            
            self._pool = ConnectionPool(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                max_connections=50,  # Límite de 50 conexiones
                decode_responses=True,
                socket_keepalive=True,
                socket_keepalive_options={
                    1: 1,  # TCP_KEEPIDLE
                    2: 2,  # TCP_KEEPINTVL
                    3: 3,  # TCP_KEEPCNT
                },
                health_check_interval=30
            )
            logger.info("Redis connection pool creado con máximo 50 conexiones")
        
        return self._pool
    
    async def get_client(self) -> redis.Redis:
        """
        Obtiene un cliente Redis del pool
        El cliente reutiliza conexiones del pool automáticamente
        """
        pool = await self.get_pool()
        return redis.Redis(connection_pool=pool)
    
    async def close(self):
        """
        Cierra el pool de conexiones
        Debe llamarse al cerrar la aplicación
        """
        if self._pool:
            await self._pool.disconnect()
            logger.info("Redis connection pool cerrado")
            self._pool = None
    
    async def get_pool_stats(self) -> dict:
        """
        Obtiene estadísticas del pool de conexiones
        """
        if not self._pool:
            return {"status": "not_initialized"}
        
        return {
            "created_connections": self._pool.created_connections,
            "available_connections": len(self._pool._available_connections),
            "in_use_connections": len(self._pool._in_use_connections),
            "max_connections": 50,
            "status": "healthy"
        }
    
    async def health_check(self) -> bool:
        """
        Verifica la salud del pool y Redis
        """
        try:
            client = await self.get_client()
            await client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check falló: {e}")
            return False


# Instancia global del pool
redis_pool = RedisConnectionPool()


async def get_redis_client() -> redis.Redis:
    """
    Función de conveniencia para obtener un cliente Redis
    """
    return await redis_pool.get_client()


# Ejemplo de uso
if __name__ == "__main__":
    import asyncio
    
    async def test_pool():
        """Test del pool de conexiones"""
        # Obtener cliente
        client = await get_redis_client()
        
        # Test básico
        await client.set("test:key", "test_value", ex=60)
        value = await client.get("test:key")
        print(f"Test Redis: {value}")
        
        # Estadísticas del pool
        stats = await redis_pool.get_pool_stats()
        print(f"Pool stats: {stats}")
        
        # Health check
        health = await redis_pool.health_check()
        print(f"Health check: {'OK' if health else 'FAILED'}")
        
        # Limpiar
        await client.delete("test:key")
        await redis_pool.close()
    
    asyncio.run(test_pool())