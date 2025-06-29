"""
Performance Metrics para Spider Factory 2.0
Valida y trackea KPIs de tiempo específicos del plan
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import statistics
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class PerformanceTarget(Enum):
    """Objetivos de rendimiento según el plan"""
    RSS_TIME = 5  # segundos
    FIRST_TIME = 20  # segundos  
    CACHE_TIME = 2  # segundos
    MANUAL_TIME = 1200  # 20 minutos en segundos
    MIN_REDUCTION = 97  # 97% de reducción mínima


class PerformanceMetrics:
    """
    Sistema de métricas de rendimiento
    Valida tiempos contra KPIs del plan original
    """
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.prefix = "spider_factory:performance"
        
    async def validate_generation_time(self, strategy: str, tiempo: float) -> Tuple[bool, str]:
        """
        Valida si el tiempo cumple con los KPIs
        
        Returns:
            Tuple[bool, str]: (cumple_kpi, mensaje)
        """
        if strategy == 'rss':
            target = PerformanceTarget.RSS_TIME.value
            meets_target = tiempo < target
            status = "✓" if meets_target else "✗"
            message = f"{status} RSS: {tiempo:.2f}s (target: <{target}s)"
            
        elif strategy == 'cache':
            target = PerformanceTarget.CACHE_TIME.value
            meets_target = tiempo < target
            status = "✓" if meets_target else "✗"
            message = f"{status} Cache: {tiempo:.2f}s (target: <{target}s)"
            
        else:  # scraping, playwright (primera vez)
            target = PerformanceTarget.FIRST_TIME.value
            # Para primera vez, permitimos hasta 25s (un poco más que el target)
            meets_target = tiempo < (target * 1.25)
            status = "✓" if meets_target else "✗"
            message = f"{status} Primera vez: {tiempo:.2f}s (target: ~{target}s)"
        
        # Registrar el resultado
        await self._record_performance_validation(strategy, tiempo, meets_target)
        
        return meets_target, message
        
    async def _record_performance_validation(self, strategy: str, tiempo: float, meets_target: bool):
        """
        Registra validación de rendimiento para estadísticas
        """
        key = f"{self.prefix}:validations:{strategy}"
        validation_data = {
            "tiempo": tiempo,
            "meets_target": meets_target,
            "timestamp": datetime.now().isoformat()
        }
        
        # Agregar a lista de validaciones recientes
        await self.redis.lpush(key, str(validation_data))
        # Mantener solo las últimas 100
        await self.redis.ltrim(key, 0, 99)
        
        # Incrementar contadores
        if meets_target:
            await self.redis.incr(f"{self.prefix}:kpi_met:{strategy}")
        else:
            await self.redis.incr(f"{self.prefix}:kpi_missed:{strategy}")
            
    async def get_kpi_compliance_rate(self, strategy: str) -> float:
        """
        Obtiene tasa de cumplimiento de KPIs para una estrategia
        """
        met = int(await self.redis.get(f"{self.prefix}:kpi_met:{strategy}") or 0)
        missed = int(await self.redis.get(f"{self.prefix}:kpi_missed:{strategy}") or 0)
        
        total = met + missed
        if total == 0:
            return 100.0
            
        return (met / total) * 100
        
    async def analyze_performance_trends(self) -> Dict[str, Any]:
        """
        Analiza tendencias de rendimiento
        """
        trends = {}
        
        for strategy in ['rss', 'scraping', 'playwright', 'cache']:
            # Obtener tiempos recientes
            key = f"spider_factory:metrics:times:{strategy}_all"
            times = await self.redis.lrange(key, 0, 19)  # Últimos 20
            
            if not times:
                trends[strategy] = {
                    "average": 0,
                    "min": 0,
                    "max": 0,
                    "trend": "no_data"
                }
                continue
                
            times_float = [float(t) for t in times]
            
            # Calcular estadísticas
            avg_time = statistics.mean(times_float)
            min_time = min(times_float)
            max_time = max(times_float)
            
            # Calcular tendencia (comparar primera mitad vs segunda mitad)
            if len(times_float) >= 4:
                mid = len(times_float) // 2
                first_half = statistics.mean(times_float[:mid])
                second_half = statistics.mean(times_float[mid:])
                
                if second_half < first_half * 0.9:
                    trend = "improving"
                elif second_half > first_half * 1.1:
                    trend = "degrading"
                else:
                    trend = "stable"
            else:
                trend = "insufficient_data"
                
            trends[strategy] = {
                "average": round(avg_time, 2),
                "min": round(min_time, 2),
                "max": round(max_time, 2),
                "trend": trend,
                "kpi_compliance": round(await self.get_kpi_compliance_rate(strategy), 2)
            }
            
        return trends
        
    async def get_bottleneck_analysis(self) -> Dict[str, Any]:
        """
        Identifica cuellos de botella en el sistema
        """
        bottlenecks = []
        
        # Analizar cada estrategia
        trends = await self.analyze_performance_trends()
        
        for strategy, data in trends.items():
            if data['average'] == 0:
                continue
                
            # Determinar si es un cuello de botella
            if strategy == 'rss' and data['average'] > PerformanceTarget.RSS_TIME.value:
                bottlenecks.append({
                    "component": "RSS Parser",
                    "strategy": strategy,
                    "current_avg": data['average'],
                    "target": PerformanceTarget.RSS_TIME.value,
                    "severity": "high" if data['average'] > 10 else "medium",
                    "recommendation": "Optimizar parseo de feeds o implementar cache más agresivo"
                })
                
            elif strategy == 'cache' and data['average'] > PerformanceTarget.CACHE_TIME.value:
                bottlenecks.append({
                    "component": "Cache System",
                    "strategy": strategy,
                    "current_avg": data['average'],
                    "target": PerformanceTarget.CACHE_TIME.value,
                    "severity": "high",
                    "recommendation": "Revisar índices de Redis o implementar cache en memoria"
                })
                
            elif strategy in ['scraping', 'playwright'] and data['average'] > PerformanceTarget.FIRST_TIME.value * 1.5:
                bottlenecks.append({
                    "component": "Web Scraper" if strategy == 'scraping' else "Browser Automation",
                    "strategy": strategy,
                    "current_avg": data['average'],
                    "target": PerformanceTarget.FIRST_TIME.value,
                    "severity": "medium",
                    "recommendation": "Optimizar selectores o reducir requests innecesarios"
                })
                
        return {
            "bottlenecks": bottlenecks,
            "overall_health": "critical" if any(b['severity'] == 'high' for b in bottlenecks) else 
                            "warning" if bottlenecks else "healthy",
            "trends": trends
        }
        
    async def calculate_cost_savings(self) -> Dict[str, float]:
        """
        Calcula ahorro de costos basado en reducción de tiempo
        """
        # Obtener tiempo promedio actual
        from .metrics import Metrics
        metrics = Metrics(self.redis)
        
        avg_time = 0
        count = 0
        
        for strategy in ['rss', 'scraping', 'playwright', 'cache']:
            strategy_avg = await metrics.get_average_time(strategy)
            if strategy_avg > 0:
                avg_time += strategy_avg
                count += 1
                
        if count == 0:
            return {"error": "No hay datos suficientes"}
            
        avg_time = avg_time / count
        
        # Tiempo manual: 20 minutos
        manual_time = PerformanceTarget.MANUAL_TIME.value
        
        # Calcular reducción
        time_saved_per_spider = (manual_time - avg_time) / 60  # en minutos
        reduction_percentage = ((manual_time - avg_time) / manual_time) * 100
        
        # Proyecciones (asumiendo 200 spiders/día)
        daily_time_saved = time_saved_per_spider * 200  # minutos
        monthly_time_saved = daily_time_saved * 30  # minutos
        yearly_time_saved = daily_time_saved * 365  # minutos
        
        # Conversión a horas laborales (asumiendo $50/hora)
        hourly_rate = 50
        daily_cost_saved = (daily_time_saved / 60) * hourly_rate
        monthly_cost_saved = (monthly_time_saved / 60) * hourly_rate
        yearly_cost_saved = (yearly_time_saved / 60) * hourly_rate
        
        return {
            "time_reduction_percentage": round(reduction_percentage, 2),
            "average_time_seconds": round(avg_time, 2),
            "time_saved_per_spider_minutes": round(time_saved_per_spider, 2),
            "projections": {
                "daily": {
                    "hours_saved": round(daily_time_saved / 60, 2),
                    "cost_saved_usd": round(daily_cost_saved, 2)
                },
                "monthly": {
                    "hours_saved": round(monthly_time_saved / 60, 2),
                    "cost_saved_usd": round(monthly_cost_saved, 2)
                },
                "yearly": {
                    "hours_saved": round(yearly_time_saved / 60, 2),
                    "cost_saved_usd": round(yearly_cost_saved, 2),
                    "fte_equivalent": round((yearly_time_saved / 60) / 2080, 2)  # 2080 = horas laborales/año
                }
            },
            "meets_target": reduction_percentage >= PerformanceTarget.MIN_REDUCTION.value
        }
        
    async def get_performance_report(self) -> str:
        """
        Genera reporte completo de rendimiento
        """
        trends = await self.analyze_performance_trends()
        bottlenecks = await self.get_bottleneck_analysis()
        savings = await self.calculate_cost_savings()
        
        report = f"""
=== Reporte de Rendimiento - Spider Factory 2.0 ===

📊 TENDENCIAS DE RENDIMIENTO:
"""
        
        for strategy, data in trends.items():
            icon = "📈" if data['trend'] == 'improving' else "📉" if data['trend'] == 'degrading' else "➡️"
            report += f"\n{strategy.upper()}:"
            report += f"\n  Promedio: {data['average']}s | Min: {data['min']}s | Max: {data['max']}s"
            report += f"\n  Tendencia: {icon} {data['trend']}"
            report += f"\n  Cumplimiento KPI: {data['kpi_compliance']}%"
            
        report += f"\n\n🚨 ANÁLISIS DE CUELLOS DE BOTELLA:"
        report += f"\nEstado General: {bottlenecks['overall_health'].upper()}"
        
        if bottlenecks['bottlenecks']:
            for bottleneck in bottlenecks['bottlenecks']:
                report += f"\n\n⚠️ {bottleneck['component']}:"
                report += f"\n  Tiempo actual: {bottleneck['current_avg']}s (target: {bottleneck['target']}s)"
                report += f"\n  Severidad: {bottleneck['severity']}"
                report += f"\n  Recomendación: {bottleneck['recommendation']}"
        else:
            report += "\n✅ No se detectaron cuellos de botella significativos"
            
        if 'error' not in savings:
            report += f"\n\n💰 AHORRO DE COSTOS:"
            report += f"\nReducción de tiempo: {savings['time_reduction_percentage']}% {'✅' if savings['meets_target'] else '❌'}"
            report += f"\nTiempo promedio actual: {savings['average_time_seconds']}s"
            report += f"\nTiempo ahorrado por spider: {savings['time_saved_per_spider_minutes']} minutos"
            report += f"\n\nProyecciones de ahorro:"
            report += f"\n  Diario: {savings['projections']['daily']['hours_saved']}h = ${savings['projections']['daily']['cost_saved_usd']}"
            report += f"\n  Mensual: {savings['projections']['monthly']['hours_saved']}h = ${savings['projections']['monthly']['cost_saved_usd']}"
            report += f"\n  Anual: {savings['projections']['yearly']['hours_saved']}h = ${savings['projections']['yearly']['cost_saved_usd']}"
            report += f"\n  Equivalente FTE: {savings['projections']['yearly']['fte_equivalent']} empleados"
            
        return report


# Funciones auxiliares para integración
async def track_performance(
    performance_metrics: PerformanceMetrics,
    operation: str,
    duration: float,
    metadata: Optional[Dict] = None
) -> Tuple[bool, str]:
    """
    Trackea y valida rendimiento de una operación
    """
    # Mapear operación a estrategia
    strategy_map = {
        "analyze_rss": "rss",
        "analyze_cache": "cache",
        "analyze_scraping": "scraping",
        "analyze_playwright": "playwright",
        "generate_spider": "first"
    }
    
    strategy = strategy_map.get(operation, "first")
    meets_kpi, message = await performance_metrics.validate_generation_time(strategy, duration)
    
    if not meets_kpi:
        logger.warning(f"KPI no cumplido: {message}")
        
    return meets_kpi, message


# Ejemplo de uso
if __name__ == "__main__":
    import asyncio
    from .redis_pool import get_redis_client
    
    async def test_performance():
        """Test del sistema de métricas de rendimiento"""
        client = await get_redis_client()
        perf = PerformanceMetrics(client)
        
        # Simular algunas mediciones
        print("Validando tiempos...")
        print(await perf.validate_generation_time("rss", 3.5))  # ✓ Cumple
        print(await perf.validate_generation_time("rss", 8.2))  # ✗ No cumple
        print(await perf.validate_generation_time("cache", 1.5))  # ✓ Cumple
        print(await perf.validate_generation_time("scraping", 18.5))  # ✓ Cumple
        
        # Generar reporte
        print("\nGenerando reporte de rendimiento...")
        report = await perf.get_performance_report()
        print(report)
    
    asyncio.run(test_performance())