"""
Sistema de Métricas para Spider Factory 2.0
Trackea KPIs definidos en el plan original
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Tipos de métricas"""
    SPIDER_GENERATED = "spider_generated"
    GENERATION_TIME = "generation_time"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    ANALYSIS_TIME = "analysis_time"
    ERROR = "error"
    PATTERN_USAGE = "pattern_usage"
    
    
class Metrics:
    """
    Sistema central de métricas
    Almacena y calcula KPIs del sistema
    """
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.prefix = "spider_factory:metrics"
        
    async def increment_spider_generated(
        self, 
        medio: str, 
        seccion: str, 
        strategy: str,
        tiempo_generacion: float
    ):
        """
        Registra la generación exitosa de un spider
        """
        # Incrementar contador total
        await self.redis.incr(f"{self.prefix}:spiders:total")
        
        # Incrementar por estrategia
        await self.redis.incr(f"{self.prefix}:spiders:by_strategy:{strategy}")
        
        # Incrementar por medio
        await self.redis.incr(f"{self.prefix}:spiders:by_medio:{medio}")
        
        # Registrar en el día actual
        today = datetime.now().strftime("%Y-%m-%d")
        await self.redis.incr(f"{self.prefix}:spiders:daily:{today}")
        
        # Guardar tiempo de generación
        await self.record_generation_time(strategy, tiempo_generacion)
        
        # Log para tracking
        logger.info(f"Spider generado: {medio}_{seccion} | Estrategia: {strategy} | Tiempo: {tiempo_generacion:.2f}s")
        
    async def record_generation_time(self, strategy: str, tiempo: float):
        """
        Registra tiempo de generación para calcular promedios
        """
        # Agregar a lista de tiempos por estrategia
        key = f"{self.prefix}:times:{strategy}"
        await self.redis.lpush(key, tiempo)
        
        # Mantener solo los últimos 100 registros
        await self.redis.ltrim(key, 0, 99)
        
        # También registrar en estadísticas generales
        if strategy == "rss":
            await self.redis.lpush(f"{self.prefix}:times:rss_all", tiempo)
            await self.redis.ltrim(f"{self.prefix}:times:rss_all", 0, 99)
        elif strategy == "cache":
            await self.redis.lpush(f"{self.prefix}:times:cache_all", tiempo)
            await self.redis.ltrim(f"{self.prefix}:times:cache_all", 0, 99)
        else:  # scraping, playwright
            await self.redis.lpush(f"{self.prefix}:times:first_all", tiempo)
            await self.redis.ltrim(f"{self.prefix}:times:first_all", 0, 99)
            
    async def record_cache_hit(self, hit: bool):
        """
        Registra hit/miss de cache
        """
        if hit:
            await self.redis.incr(f"{self.prefix}:cache:hits")
        else:
            await self.redis.incr(f"{self.prefix}:cache:misses")
            
    async def record_error(self, error_type: str, details: Dict[str, Any]):
        """
        Registra errores para análisis
        """
        error_data = {
            "type": error_type,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        
        # Agregar a lista de errores recientes
        await self.redis.lpush(
            f"{self.prefix}:errors:recent",
            json.dumps(error_data)
        )
        
        # Mantener solo los últimos 100 errores
        await self.redis.ltrim(f"{self.prefix}:errors:recent", 0, 99)
        
        # Incrementar contador por tipo
        await self.redis.incr(f"{self.prefix}:errors:by_type:{error_type}")
        
    async def get_average_time(self, strategy: str) -> float:
        """
        Calcula tiempo promedio para una estrategia
        """
        key = f"{self.prefix}:times:{strategy}_all"
        times = await self.redis.lrange(key, 0, -1)
        
        if not times:
            return 0.0
            
        # Convertir a float y calcular promedio
        times_float = [float(t) for t in times]
        return sum(times_float) / len(times_float)
        
    async def get_cache_hit_rate(self) -> float:
        """
        Calcula tasa de aciertos de cache
        """
        hits = int(await self.redis.get(f"{self.prefix}:cache:hits") or 0)
        misses = int(await self.redis.get(f"{self.prefix}:cache:misses") or 0)
        
        total = hits + misses
        if total == 0:
            return 0.0
            
        return (hits / total) * 100
        
    async def get_daily_spider_count(self, days: int = 1) -> int:
        """
        Obtiene cantidad de spiders generados en los últimos días
        """
        total = 0
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            count = await self.redis.get(f"{self.prefix}:spiders:daily:{date}")
            if count:
                total += int(count)
                
        return total
        
    async def get_spider_success_rate(self) -> float:
        """
        Calcula tasa de éxito de spiders (basado en errores)
        """
        total_spiders = int(await self.redis.get(f"{self.prefix}:spiders:total") or 0)
        total_errors = int(await self.redis.get(f"{self.prefix}:errors:by_type:spider_generation") or 0)
        
        if total_spiders == 0:
            return 100.0
            
        success = total_spiders - total_errors
        return (success / total_spiders) * 100
        
    async def calculate_time_reduction(self) -> float:
        """
        Calcula reducción de tiempo vs proceso manual (20 minutos)
        """
        # Obtener tiempos promedio de todas las estrategias
        avg_rss = await self.get_average_time("rss")
        avg_first = await self.get_average_time("first")
        avg_cache = await self.get_average_time("cache")
        
        # Calcular promedio ponderado (asumiendo distribución típica)
        # 30% RSS, 50% primera vez, 20% cache
        if avg_rss == 0 and avg_first == 0 and avg_cache == 0:
            return 0.0
            
        avg_time = (avg_rss * 0.3) + (avg_first * 0.5) + (avg_cache * 0.2)
        
        # Tiempo manual: 20 minutos
        manual_time = 20 * 60  # 1200 segundos
        
        if avg_time == 0:
            return 0.0
            
        return ((manual_time - avg_time) / manual_time) * 100
        
    async def get_request_reduction(self) -> float:
        """
        Calcula reducción de requests HTTP (por uso de cache y patrones)
        """
        # Por cada hit de cache, ahorramos requests
        cache_hits = int(await self.redis.get(f"{self.prefix}:cache:hits") or 0)
        total_analyses = cache_hits + int(await self.redis.get(f"{self.prefix}:cache:misses") or 0)
        
        if total_analyses == 0:
            return 0.0
            
        # Asumiendo que cada análisis sin cache hace ~10 requests
        # y con cache hace 0 requests
        requests_saved = cache_hits * 10
        requests_total = total_analyses * 10
        
        return (requests_saved / requests_total) * 100
        
    async def get_adoption_rate(self) -> float:
        """
        Calcula tasa de adopción (basado en uso diario)
        """
        # Verificar uso en los últimos 7 días
        days_with_usage = 0
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            count = await self.redis.get(f"{self.prefix}:spiders:daily:{date}")
            if count and int(count) > 0:
                days_with_usage += 1
                
        # Porcentaje de días con uso
        return (days_with_usage / 7) * 100
        
    async def get_system_metrics(self) -> Dict[str, Any]:
        """
        Obtiene todas las métricas del sistema según el plan original
        """
        return {
            # Tiempo de generación
            "tiempo_reduccion": round(await self.calculate_time_reduction(), 2),  # Target: 97%
            "tiempo_promedio_rss": round(await self.get_average_time("rss"), 2),  # Target: <5s
            "tiempo_promedio_primera_vez": round(await self.get_average_time("first"), 2),  # Target: ~20s
            "tiempo_promedio_cache": round(await self.get_average_time("cache"), 2),  # Target: <2s
            
            # Precisión
            "precision_spiders": round(await self.get_spider_success_rate(), 2),  # Target: >90%
            
            # Eficiencia
            "reduccion_requests": round(await self.get_request_reduction(), 2),  # Target: 70%
            "cache_hit_rate": round(await self.get_cache_hit_rate(), 2),
            
            # Throughput
            "spiders_por_dia": await self.get_daily_spider_count(),  # Target: 200+
            "spiders_total": int(await self.redis.get(f"{self.prefix}:spiders:total") or 0),
            
            # Adopción
            "porcentaje_adopcion": round(await self.get_adoption_rate(), 2),  # Target: >80%
            
            # Desglose por estrategia
            "spiders_por_estrategia": {
                "rss": int(await self.redis.get(f"{self.prefix}:spiders:by_strategy:rss") or 0),
                "scraping": int(await self.redis.get(f"{self.prefix}:spiders:by_strategy:scraping") or 0),
                "playwright": int(await self.redis.get(f"{self.prefix}:spiders:by_strategy:playwright") or 0),
            },
            
            # Timestamp
            "timestamp": datetime.now().isoformat(),
            
            # KPIs cumplidos
            "kpis_status": {
                "tiempo_rss_ok": await self.get_average_time("rss") < 5,
                "tiempo_primera_ok": await self.get_average_time("first") < 20,
                "tiempo_cache_ok": await self.get_average_time("cache") < 2,
                "reduccion_tiempo_ok": await self.calculate_time_reduction() > 95,
                "precision_ok": await self.get_spider_success_rate() > 90,
                "throughput_ok": await self.get_daily_spider_count() > 200,
            }
        }
        
    async def get_metrics_summary(self) -> str:
        """
        Obtiene resumen de métricas en formato texto
        """
        metrics = await self.get_system_metrics()
        
        summary = f"""
=== Métricas Spider Factory 2.0 ===
Tiempo de Reducción: {metrics['tiempo_reduccion']}% (Target: 97%)
Tiempos Promedio:
  - RSS: {metrics['tiempo_promedio_rss']}s (Target: <5s)
  - Primera vez: {metrics['tiempo_promedio_primera_vez']}s (Target: ~20s)
  - Cache: {metrics['tiempo_promedio_cache']}s (Target: <2s)

Eficiencia:
  - Precisión: {metrics['precision_spiders']}% (Target: >90%)
  - Cache Hit Rate: {metrics['cache_hit_rate']}%
  - Reducción Requests: {metrics['reduccion_requests']}% (Target: 70%)

Throughput:
  - Spiders/día: {metrics['spiders_por_dia']} (Target: 200+)
  - Total generados: {metrics['spiders_total']}

Adopción: {metrics['porcentaje_adopcion']}% (Target: >80%)
"""
        return summary
        

# Funciones de utilidad para logging de métricas
async def log_spider_metrics(
    metrics: Metrics,
    spider_name: str,
    medio: str,
    seccion: str,
    strategy: str,
    generation_time: float,
    success: bool = True,
    error: Optional[str] = None
):
    """
    Registra métricas completas de generación de spider
    """
    if success:
        await metrics.increment_spider_generated(medio, seccion, strategy, generation_time)
    else:
        await metrics.record_error("spider_generation", {
            "spider_name": spider_name,
            "medio": medio,
            "seccion": seccion,
            "strategy": strategy,
            "error": error
        })
        

async def log_analysis_metrics(
    metrics: Metrics,
    url: str,
    strategy: str,
    analysis_time: float,
    from_cache: bool
):
    """
    Registra métricas de análisis
    """
    await metrics.record_generation_time(strategy, analysis_time)
    await metrics.record_cache_hit(from_cache)
    
    
# Ejemplo de uso
if __name__ == "__main__":
    import asyncio
    from .redis_pool import get_redis_client
    
    async def test_metrics():
        """Test del sistema de métricas"""
        client = await get_redis_client()
        metrics = Metrics(client)
        
        # Simular algunas métricas
        await metrics.increment_spider_generated("El País", "Internacional", "rss", 3.5)
        await metrics.increment_spider_generated("La Nación", "Economía", "scraping", 18.2)
        await metrics.record_cache_hit(True)
        await metrics.record_cache_hit(False)
        
        # Obtener resumen
        summary = await metrics.get_metrics_summary()
        print(summary)
        
        # Obtener métricas completas
        all_metrics = await metrics.get_system_metrics()
        print(f"\nMétricas JSON: {json.dumps(all_metrics, indent=2)}")
    
    asyncio.run(test_metrics())