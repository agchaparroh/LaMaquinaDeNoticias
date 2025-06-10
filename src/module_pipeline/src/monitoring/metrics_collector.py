"""
Colector de Métricas Interno para Module Pipeline
================================================

Implementa un sistema singleton de colección de métricas que aprovecha datos del
controller y logs existentes para proporcionar observabilidad del pipeline.

Características:
- Patrón Singleton para instancia única
- Métricas del pipeline (requests/min, latencias, errores)
- Métricas por fase (tiempo fase1, éxito fase2, etc.)
- Ventana deslizante de 24h para evitar memory leaks
- Integración con middleware de logging existente
- Thread-safety garantizado
"""

import threading
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import deque, defaultdict
import time

# Importar utilidades de logging existentes
from ..utils.logging_config import get_logger


class MetricsCollector:
    """
    Colector singleton de métricas del pipeline.
    
    Agrega métricas del pipeline aprovechando datos del controller y el
    sistema de logging existente. Mantiene ventana deslizante de 24h.
    
    Attributes:
        _instance: Instancia única del colector
        _lock: Lock para thread-safety
        _metrics_data: Almacenamiento de métricas agregadas
        _time_window_hours: Ventana de retención (24h)
    """
    
    _instance: Optional['MetricsCollector'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'MetricsCollector':
        """
        Implementación del patrón Singleton.
        
        Returns:
            Instancia única de MetricsCollector
        """
        if cls._instance is None:
            with cls._lock:
                # Double-check locking pattern
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        Inicializa el colector de métricas.
        
        Solo se ejecuta una vez gracias al patrón Singleton.
        """
        # Evitar re-inicialización
        if not hasattr(self, '_initialized'):
            # Logger con contexto
            self.logger = get_logger("MetricsCollector")
            
            # Lock para operaciones thread-safe
            self._operation_lock = threading.Lock()
            
            # Configuración de ventana deslizante
            self._time_window_hours = 24
            self._cleanup_interval_minutes = 60  # Limpiar cada hora
            self._last_cleanup = time.time()
            
            # Almacenamiento de métricas con ventana deslizante
            # Cada entrada: (timestamp, metric_data)
            self._request_metrics = deque()  # Métricas de requests HTTP
            self._pipeline_metrics = deque()  # Métricas de procesamiento pipeline
            self._phase_metrics = deque()  # Métricas por fase individual
            self._error_metrics = deque()  # Métricas de errores
            
            # Métricas agregadas actuales (calculadas on-demand)
            self._aggregated_metrics = {
                "requests_per_minute": 0.0,
                "average_latency_seconds": 0.0,
                "error_rate_percent": 0.0,
                "pipeline_throughput_per_hour": 0.0,
                "phase_success_rates": {},
                "phase_average_times": {}
            }
            
            # Contadores totales (desde inicio del servicio)
            self._total_counters = {
                "total_requests": 0,
                "total_pipeline_processes": 0,
                "total_errors": 0,
                "uptime_start": datetime.utcnow()
            }
            
            # Flag de inicialización
            self._initialized = True
            
            self.logger.info(
                "MetricsCollector inicializado",
                time_window_hours=self._time_window_hours,
                cleanup_interval_minutes=self._cleanup_interval_minutes
            )
    
    def record_request_metric(
        self, 
        method: str, 
        path: str, 
        status_code: int, 
        duration_seconds: float,
        request_id: Optional[str] = None
    ):
        """
        Registra métricas de un request HTTP.
        
        Aprovecha datos del middleware de logging existente.
        
        Args:
            method: Método HTTP (GET, POST, etc.)
            path: Path del endpoint
            status_code: Código de estado HTTP
            duration_seconds: Tiempo de procesamiento
            request_id: ID del request opcional
        """
        timestamp = time.time()
        
        metric_data = {
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_seconds": duration_seconds,
            "request_id": request_id,
            "is_error": status_code >= 400
        }
        
        with self._operation_lock:
            self._request_metrics.append((timestamp, metric_data))
            self._total_counters["total_requests"] += 1
            
            if metric_data["is_error"]:
                self._error_metrics.append((timestamp, {
                    "type": "http_error",
                    "status_code": status_code,
                    "path": path,
                    "request_id": request_id
                }))
                self._total_counters["total_errors"] += 1
            
            # Auto-cleanup si es necesario
            self._auto_cleanup_if_needed()
        
        self.logger.debug(
            f"Request metric recorded",
            method=method,
            path=path,
            status_code=status_code,
            duration_seconds=duration_seconds
        )
    
    def record_pipeline_metric(
        self, 
        pipeline_type: str, 
        duration_seconds: float, 
        success: bool,
        elements_processed: Dict[str, int],
        request_id: Optional[str] = None
    ):
        """
        Registra métricas de procesamiento del pipeline.
        
        Aprovecha datos del controller existente.
        
        Args:
            pipeline_type: Tipo de pipeline ("article" o "fragment")
            duration_seconds: Tiempo total de procesamiento
            success: Si el procesamiento fue exitoso
            elements_processed: Conteo de elementos procesados
            request_id: ID del request opcional
        """
        timestamp = time.time()
        
        metric_data = {
            "pipeline_type": pipeline_type,
            "duration_seconds": duration_seconds,
            "success": success,
            "elements_processed": elements_processed,
            "request_id": request_id
        }
        
        with self._operation_lock:
            self._pipeline_metrics.append((timestamp, metric_data))
            self._total_counters["total_pipeline_processes"] += 1
            
            if not success:
                self._error_metrics.append((timestamp, {
                    "type": "pipeline_error",
                    "pipeline_type": pipeline_type,
                    "request_id": request_id
                }))
                self._total_counters["total_errors"] += 1
            
            # Auto-cleanup si es necesario
            self._auto_cleanup_if_needed()
        
        self.logger.debug(
            f"Pipeline metric recorded",
            pipeline_type=pipeline_type,
            duration_seconds=duration_seconds,
            success=success,
            elements_count=sum(elements_processed.values())
        )
    
    def record_phase_metric(
        self, 
        phase_name: str, 
        duration_seconds: float, 
        success: bool,
        request_id: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """
        Registra métricas de una fase individual del pipeline.
        
        Aprovecha logs del sistema de fases existente.
        
        Args:
            phase_name: Nombre de la fase (ej: "Fase1_Triaje")
            duration_seconds: Tiempo de ejecución de la fase
            success: Si la fase fue exitosa
            request_id: ID del request opcional
            additional_data: Datos adicionales de la fase
        """
        timestamp = time.time()
        
        metric_data = {
            "phase_name": phase_name,
            "duration_seconds": duration_seconds,
            "success": success,
            "request_id": request_id,
            "additional_data": additional_data or {}
        }
        
        with self._operation_lock:
            self._phase_metrics.append((timestamp, metric_data))
            
            if not success:
                self._error_metrics.append((timestamp, {
                    "type": "phase_error",
                    "phase_name": phase_name,
                    "request_id": request_id
                }))
                self._total_counters["total_errors"] += 1
            
            # Auto-cleanup si es necesario
            self._auto_cleanup_if_needed()
        
        self.logger.debug(
            f"Phase metric recorded",
            phase_name=phase_name,
            duration_seconds=duration_seconds,
            success=success
        )
    
    def get_aggregated_metrics(self) -> Dict[str, Any]:
        """
        Calcula y retorna métricas agregadas del pipeline.
        
        Returns:
            Diccionario con métricas agregadas actualizadas
        """
        with self._operation_lock:
            # Forzar cleanup antes de calcular métricas
            self._cleanup_old_metrics()
            
            now = time.time()
            cutoff_time = now - (self._time_window_hours * 3600)
            
            # Filtrar métricas dentro de la ventana de tiempo
            recent_requests = [(t, m) for t, m in self._request_metrics if t > cutoff_time]
            recent_pipeline = [(t, m) for t, m in self._pipeline_metrics if t > cutoff_time]
            recent_phases = [(t, m) for t, m in self._phase_metrics if t > cutoff_time]
            recent_errors = [(t, m) for t, m in self._error_metrics if t > cutoff_time]
            
            # Calcular requests per minute
            if recent_requests:
                time_span_minutes = (now - min(t for t, _ in recent_requests)) / 60
                requests_per_minute = len(recent_requests) / max(time_span_minutes, 1)
            else:
                requests_per_minute = 0.0
            
            # Calcular latencia promedio
            if recent_requests:
                total_duration = sum(m["duration_seconds"] for _, m in recent_requests)
                average_latency = total_duration / len(recent_requests)
            else:
                average_latency = 0.0
            
            # Calcular tasa de error
            total_operations = len(recent_requests) + len(recent_pipeline)
            error_rate = (len(recent_errors) / max(total_operations, 1)) * 100
            
            # Calcular throughput de pipeline
            if recent_pipeline:
                time_span_hours = (now - min(t for t, _ in recent_pipeline)) / 3600
                pipeline_throughput = len(recent_pipeline) / max(time_span_hours, 1)
            else:
                pipeline_throughput = 0.0
            
            # Calcular tasas de éxito por fase
            phase_stats = defaultdict(lambda: {"success": 0, "total": 0, "total_time": 0.0})
            for _, metric in recent_phases:
                phase = metric["phase_name"]
                phase_stats[phase]["total"] += 1
                phase_stats[phase]["total_time"] += metric["duration_seconds"]
                if metric["success"]:
                    phase_stats[phase]["success"] += 1
            
            phase_success_rates = {}
            phase_average_times = {}
            for phase, stats in phase_stats.items():
                phase_success_rates[phase] = (stats["success"] / max(stats["total"], 1)) * 100
                phase_average_times[phase] = stats["total_time"] / max(stats["total"], 1)
            
            # Actualizar métricas agregadas
            self._aggregated_metrics = {
                "requests_per_minute": round(requests_per_minute, 2),
                "average_latency_seconds": round(average_latency, 3),
                "error_rate_percent": round(error_rate, 2),
                "pipeline_throughput_per_hour": round(pipeline_throughput, 2),
                "phase_success_rates": phase_success_rates,
                "phase_average_times": phase_average_times,
                "window_stats": {
                    "time_window_hours": self._time_window_hours,
                    "recent_requests_count": len(recent_requests),
                    "recent_pipeline_count": len(recent_pipeline),
                    "recent_errors_count": len(recent_errors),
                    "total_operations_in_window": total_operations
                },
                "totals": self._total_counters.copy(),
                "last_updated": datetime.utcnow().isoformat() + "Z"
            }
            
            return self._aggregated_metrics.copy()
    
    def get_controller_integration_metrics(self, controller) -> Dict[str, Any]:
        """
        Integra con las métricas del PipelineController existente.
        
        Args:
            controller: Instancia del PipelineController
            
        Returns:
            Métricas combinadas del controller y colector
        """
        # Obtener métricas del controller
        controller_metrics = controller.get_metrics()
        
        # Obtener métricas agregadas del colector
        collector_metrics = self.get_aggregated_metrics()
        
        # Combinar métricas
        combined_metrics = {
            "controller_metrics": controller_metrics,
            "collector_metrics": collector_metrics,
            "integration_stats": {
                "metrics_sources": ["controller", "collector"],
                "data_consistency_check": {
                    "controller_fragments": controller_metrics.get("fragmentos_procesados", 0),
                    "collector_pipeline": collector_metrics["totals"]["total_pipeline_processes"],
                    "difference": abs(
                        controller_metrics.get("fragmentos_procesados", 0) - 
                        collector_metrics["totals"]["total_pipeline_processes"]
                    )
                }
            }
        }
        
        return combined_metrics
    
    def _auto_cleanup_if_needed(self):
        """
        Ejecuta cleanup automático si ha pasado el intervalo configurado.
        
        Método interno para evitar memory leaks.
        """
        current_time = time.time()
        if current_time - self._last_cleanup > (self._cleanup_interval_minutes * 60):
            self._cleanup_old_metrics()
            self._last_cleanup = current_time
    
    def _cleanup_old_metrics(self):
        """
        Limpia métricas fuera de la ventana de tiempo.
        
        Método interno para mantener ventana deslizante de 24h.
        """
        cutoff_time = time.time() - (self._time_window_hours * 3600)
        
        # Limpiar cada deque manteniendo solo métricas recientes
        self._request_metrics = deque(
            (t, m) for t, m in self._request_metrics if t > cutoff_time
        )
        self._pipeline_metrics = deque(
            (t, m) for t, m in self._pipeline_metrics if t > cutoff_time
        )
        self._phase_metrics = deque(
            (t, m) for t, m in self._phase_metrics if t > cutoff_time
        )
        self._error_metrics = deque(
            (t, m) for t, m in self._error_metrics if t > cutoff_time
        )
        
        self.logger.debug(
            f"Metrics cleanup completed",
            cutoff_hours_ago=self._time_window_hours,
            remaining_requests=len(self._request_metrics),
            remaining_pipeline=len(self._pipeline_metrics),
            remaining_phases=len(self._phase_metrics),
            remaining_errors=len(self._error_metrics)
        )
    
    def reset_metrics(self):
        """
        Reset completo de todas las métricas.
        
        Útil para testing o restart del sistema.
        """
        with self._operation_lock:
            self._request_metrics.clear()
            self._pipeline_metrics.clear()
            self._phase_metrics.clear()
            self._error_metrics.clear()
            
            # Reset contadores totales pero mantener uptime_start
            uptime_start = self._total_counters["uptime_start"]
            self._total_counters = {
                "total_requests": 0,
                "total_pipeline_processes": 0,
                "total_errors": 0,
                "uptime_start": uptime_start
            }
            
            # Reset métricas agregadas
            self._aggregated_metrics = {
                "requests_per_minute": 0.0,
                "average_latency_seconds": 0.0,
                "error_rate_percent": 0.0,
                "pipeline_throughput_per_hour": 0.0,
                "phase_success_rates": {},
                "phase_average_times": {}
            }
            
            self.logger.info("All metrics reset completed")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del colector de métricas.
        
        Returns:
            Diccionario con estadísticas del colector
        """
        with self._operation_lock:
            uptime_seconds = (datetime.utcnow() - self._total_counters["uptime_start"]).total_seconds()
            
            return {
                "collector_status": "active",
                "time_window_hours": self._time_window_hours,
                "cleanup_interval_minutes": self._cleanup_interval_minutes,
                "uptime_seconds": round(uptime_seconds, 1),
                "memory_usage": {
                    "request_metrics_count": len(self._request_metrics),
                    "pipeline_metrics_count": len(self._pipeline_metrics),
                    "phase_metrics_count": len(self._phase_metrics),
                    "error_metrics_count": len(self._error_metrics),
                    "total_stored_metrics": (
                        len(self._request_metrics) + 
                        len(self._pipeline_metrics) + 
                        len(self._phase_metrics) + 
                        len(self._error_metrics)
                    )
                },
                "last_cleanup_ago_minutes": round((time.time() - self._last_cleanup) / 60, 1),
                "total_counters": self._total_counters.copy()
            }


# Función helper para obtener la instancia singleton
def get_metrics_collector() -> MetricsCollector:
    """
    Obtiene la instancia singleton del colector de métricas.
    
    Returns:
        Instancia única de MetricsCollector
    """
    return MetricsCollector()


# Funciones de integración con middleware existente
def create_middleware_integration(app):
    """
    Crea middleware para integrar automáticamente con el sistema de logging.
    
    Se integra con el middleware de logging existente para capturar datos HTTP.
    
    Args:
        app: Instancia de FastAPI
    """
    from fastapi import Request
    import time
    
    collector = get_metrics_collector()
    
    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        """Middleware para capturar métricas de requests HTTP."""
        start_time = time.time()
        
        # Obtener request_id del estado si existe (del middleware de logging)
        request_id = getattr(request.state, 'request_id', None)
        
        try:
            response = await call_next(request)
            
            # Calcular duración
            duration = time.time() - start_time
            
            # Registrar métrica
            collector.record_request_metric(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_seconds=duration,
                request_id=request_id
            )
            
            return response
            
        except Exception as e:
            # En caso de error, registrar como error 500
            duration = time.time() - start_time
            
            collector.record_request_metric(
                method=request.method,
                path=request.url.path,
                status_code=500,
                duration_seconds=duration,
                request_id=request_id
            )
            
            raise


# Prueba del módulo si se ejecuta directamente
if __name__ == '__main__':
    import random
    import threading
    
    print("=== Prueba de MetricsCollector ===\n")
    
    # Obtener colector
    collector = get_metrics_collector()
    
    # Test 1: Métricas de requests
    print("1. Registrando métricas de requests...")
    for i in range(10):
        collector.record_request_metric(
            method="GET",
            path=f"/test/{i}",
            status_code=200 if i < 8 else 500,
            duration_seconds=random.uniform(0.1, 0.5),
            request_id=f"req-{i}"
        )
    
    # Test 2: Métricas de pipeline
    print("2. Registrando métricas de pipeline...")
    for i in range(5):
        collector.record_pipeline_metric(
            pipeline_type="fragment",
            duration_seconds=random.uniform(1.0, 3.0),
            success=i < 4,
            elements_processed={"hechos": random.randint(1, 10), "entidades": random.randint(1, 5)},
            request_id=f"pipeline-{i}"
        )
    
    # Test 3: Métricas por fase
    print("3. Registrando métricas por fase...")
    phases = ["Fase1_Triaje", "Fase2_Extraccion", "Fase3_CitasDatos", "Fase4_Normalizacion"]
    for phase in phases:
        for i in range(3):
            collector.record_phase_metric(
                phase_name=phase,
                duration_seconds=random.uniform(0.5, 2.0),
                success=random.choice([True, True, True, False]),  # 75% éxito
                request_id=f"phase-{phase}-{i}"
            )
    
    # Test 4: Obtener métricas agregadas
    print("4. Obteniendo métricas agregadas...")
    metrics = collector.get_aggregated_metrics()
    print(f"   Requests per minute: {metrics['requests_per_minute']}")
    print(f"   Average latency: {metrics['average_latency_seconds']}s")
    print(f"   Error rate: {metrics['error_rate_percent']}%")
    print(f"   Pipeline throughput: {metrics['pipeline_throughput_per_hour']}/hour")
    
    # Test 5: Estadísticas del colector
    print("5. Obteniendo estadísticas del colector...")
    stats = collector.get_stats()
    print(f"   Total stored metrics: {stats['memory_usage']['total_stored_metrics']}")
    print(f"   Uptime: {stats['uptime_seconds']}s")
    
    # Test 6: Thread safety
    print("6. Probando thread-safety...")
    def concurrent_metrics():
        for i in range(5):
            collector.record_request_metric("POST", "/concurrent", 200, 0.1)
    
    threads = []
    for i in range(3):
        t = threading.Thread(target=concurrent_metrics)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    final_stats = collector.get_stats()
    print(f"   Final total requests: {final_stats['total_counters']['total_requests']}")
    
    print("\n=== Prueba completada ===")
