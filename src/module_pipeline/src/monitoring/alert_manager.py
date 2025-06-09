"""
Sistema de Alertas para Module Pipeline
======================================

Implementa sistema básico de alertas basado en logs siguiendo
los patrones de Prometheus Alertmanager pero simplificado.

Features:
- Detección de patrones críticos en logs
- Throttling para evitar spam (máximo 1 por minuto por tipo)
- Persistencia en archivo JSON (últimas 24h)
- Integración con sistema de logging existente
- Handler personalizado de loguru
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import threading
import uuid

from loguru import logger

from ..utils.error_handling import ErrorType, ErrorPhase
from ..utils.config import get_logging_config


class AlertSeverity(str, Enum):
    """Niveles de severidad de alertas."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class AlertType(str, Enum):
    """Tipos de alertas detectables."""
    ERROR_RATE = "error_rate"
    HIGH_LATENCY = "high_latency"
    GROQ_API_FAILURE = "groq_api_failure"
    SUPABASE_FAILURE = "supabase_failure"
    SERVICE_DEGRADATION = "service_degradation"


@dataclass
class Alert:
    """Estructura de una alerta."""
    id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    description: str
    timestamp: datetime
    labels: Dict[str, str]
    annotations: Dict[str, str]
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la alerta a diccionario para serialización."""
        data = asdict(self)
        # Convertir datetime a string para JSON
        data['timestamp'] = self.timestamp.isoformat()
        if self.resolved_at:
            data['resolved_at'] = self.resolved_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Alert':
        """Crea alerta desde diccionario."""
        # Convertir string a datetime
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if data.get('resolved_at'):
            data['resolved_at'] = datetime.fromisoformat(data['resolved_at'])
        return cls(**data)


class AlertManager:
    """
    Gestor de alertas basado en logs con throttling y persistencia.
    
    Detecta patrones críticos en logs y genera alertas siguiendo
    los principios de observabilidad.
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Inicializa el gestor de alertas.
        
        Args:
            config_dir: Directorio para archivos de configuración
        """
        self.config_dir = config_dir or self._get_default_config_dir()
        self.alerts_file = self.config_dir / "alerts.json"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Estado interno
        self._alerts: Dict[str, Alert] = {}
        self._throttling: Dict[AlertType, float] = {}
        self._error_counts: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self._latency_samples: deque = deque(maxlen=100)
        self._lock = threading.Lock()
        
        # Configuración
        self.throttle_minutes = 1  # Máximo 1 alerta por minuto por tipo
        self.retention_hours = 24  # Retener alertas por 24 horas
        self.error_rate_threshold = 0.10  # 10%
        self.latency_threshold_seconds = 30.0  # 30 segundos
        
        # Cargar alertas persistidas
        self._load_alerts()
        
        # Configurar handler de loguru
        self._setup_loguru_handler()
        
        logger.info(
            "AlertManager inicializado",
            extra={
                "component": "AlertManager",
                "alerts_file": str(self.alerts_file),
                "retention_hours": self.retention_hours
            }
        )
    
    def _get_default_config_dir(self) -> Path:
        """Obtiene directorio por defecto para configuración."""
        # Buscar directorio base del proyecto
        current_dir = Path(__file__).resolve()
        project_root = current_dir.parent.parent.parent  # src/monitoring -> src -> module_pipeline
        return project_root / '.alerts'
    
    def _setup_loguru_handler(self):
        """Configura handler personalizado de loguru para detectar patrones."""
        def alert_sink(message):
            """Handler personalizado que analiza logs para detectar alertas."""
            try:
                record = message.record
                self._analyze_log_record(record)
            except Exception as e:
                # Evitar bucles infinitos en el sistema de alertas
                print(f"Error en alert_sink: {e}")
        
        # Agregar handler con filtro para no capturar logs del AlertManager
        logger.add(
            alert_sink,
            level="WARNING",
            filter=lambda record: record["extra"].get("component") != "AlertManager",
            format="{message}",  # El formato no importa para nuestro análisis
            enqueue=True  # Thread-safe
        )
    
    def _analyze_log_record(self, record: Dict[str, Any]):
        """Analiza un log record para detectar patrones de alerta."""
        try:
            # Extraer información del record correctamente
            level = record.get("level").name if record.get("level") else ""
            message = record.get("message", "")
            extra = record.get("extra", {})
            
            # Detectar errores de API específicos
            self._check_api_errors(record, level, message, extra)
            
            # Detectar alta latencia
            self._check_latency(record, extra)
            
            # Detectar tasa de errores
            self._check_error_rate(record, level)
            
        except Exception as e:
            # Evitar que errores en análisis afecten la aplicación
            print(f"Error analizando log record: {e}")
    
    def _check_api_errors(self, record: Dict[str, Any], level: str, message: str, extra: Dict[str, Any]):
        """Detecta errores específicos de APIs externas."""
        if level not in ["ERROR", "CRITICAL"]:
            return
        
        # Detectar errores de Groq API
        if any(term in message.lower() for term in ["groq", "api"]):
            error_type = extra.get("error_type", "")
            if error_type == ErrorType.GROQ_API_ERROR.value or "groq" in message.lower():
                self._trigger_alert(
                    alert_type=AlertType.GROQ_API_FAILURE,
                    severity=AlertSeverity.CRITICAL,
                    title="Groq API Failure Detected",
                    description=f"Error en Groq API: {message[:200]}",
                    labels={
                        "service": "groq_api",
                        "error_type": error_type or "unknown"
                    },
                    annotations={
                        "message": message[:500],
                        "timestamp": record.get("time", datetime.now()).isoformat()
                    }
                )
        
        # Detectar errores de Supabase
        if any(term in message.lower() for term in ["supabase", "rpc", "database"]):
            error_type = extra.get("error_type", "")
            if error_type == ErrorType.SUPABASE_ERROR.value or "supabase" in message.lower():
                self._trigger_alert(
                    alert_type=AlertType.SUPABASE_FAILURE,
                    severity=AlertSeverity.CRITICAL,
                    title="Supabase Service Failure Detected",
                    description=f"Error en Supabase: {message[:200]}",
                    labels={
                        "service": "supabase",
                        "error_type": error_type or "unknown"
                    },
                    annotations={
                        "message": message[:500],
                        "rpc_name": extra.get("rpc_name", "unknown")
                    }
                )
    
    def _check_latency(self, record: Dict[str, Any], extra: Dict[str, Any]):
        """Detecta alta latencia en operaciones."""
        # Buscar métricas de tiempo en el extra
        elapsed_seconds = extra.get("elapsed_seconds")
        duration_seconds = extra.get("duration_seconds")
        span_duration_seconds = extra.get("span_duration_seconds")
        
        # Usar cualquier métrica de tiempo disponible
        latency = elapsed_seconds or duration_seconds or span_duration_seconds
        
        if latency and isinstance(latency, (int, float)):
            with self._lock:
                self._latency_samples.append((time.time(), latency))
            
            # Verificar si excede el umbral
            if latency > self.latency_threshold_seconds:
                component = extra.get("component", "unknown")
                phase = extra.get("phase", extra.get("fase", "unknown"))
                
                self._trigger_alert(
                    alert_type=AlertType.HIGH_LATENCY,
                    severity=AlertSeverity.WARNING,
                    title="High Latency Detected",
                    description=f"Operación {component}/{phase} tardó {latency:.2f}s (umbral: {self.latency_threshold_seconds}s)",
                    labels={
                        "component": component,
                        "phase": phase,
                        "latency_seconds": str(latency)
                    },
                    annotations={
                        "threshold": str(self.latency_threshold_seconds),
                        "actual_latency": str(latency),
                        "operation": extra.get("operation", "unknown")
                    }
                )
    
    def _check_error_rate(self, record: Dict[str, Any], level: str):
        """Detecta alta tasa de errores."""
        current_time = time.time()
        minute_key = str(int(current_time // 60))  # Agrupar por minuto
        
        with self._lock:
            # Agregar evento (True para error, False para éxito)
            is_error = level in ["ERROR", "CRITICAL"]
            self._error_counts[minute_key].append((current_time, is_error))
            
            # Limpiar datos antiguos (más de 10 minutos)
            cutoff_time = current_time - 600  # 10 minutos
            while (self._error_counts[minute_key] and 
                   self._error_counts[minute_key][0][0] < cutoff_time):
                self._error_counts[minute_key].popleft()
            
            # Calcular tasa de errores si tenemos suficientes datos
            if len(self._error_counts[minute_key]) >= 10:  # Mínimo 10 eventos
                total_events = len(self._error_counts[minute_key])
                error_events = sum(1 for _, is_err in self._error_counts[minute_key] if is_err)
                error_rate = error_events / total_events
                
                if error_rate > self.error_rate_threshold:
                    self._trigger_alert(
                        alert_type=AlertType.ERROR_RATE,
                        severity=AlertSeverity.CRITICAL,
                        title="High Error Rate Detected",
                        description=f"Tasa de errores: {error_rate:.1%} (umbral: {self.error_rate_threshold:.1%})",
                        labels={
                            "error_rate": f"{error_rate:.3f}",
                            "window_minutes": "10"
                        },
                        annotations={
                            "threshold": f"{self.error_rate_threshold:.3f}",
                            "total_events": str(total_events),
                            "error_events": str(error_events)
                        }
                    )
    
    def _trigger_alert(
        self, 
        alert_type: AlertType, 
        severity: AlertSeverity,
        title: str,
        description: str,
        labels: Dict[str, str],
        annotations: Dict[str, str]
    ):
        """Dispara una alerta si no está en throttling."""
        current_time = time.time()
        
        with self._lock:
            # Verificar throttling
            last_alert_time = self._throttling.get(alert_type, 0)
            if current_time - last_alert_time < (self.throttle_minutes * 60):
                return  # Alerta throttled
            
            # Crear nueva alerta
            alert = Alert(
                id=str(uuid.uuid4()),
                alert_type=alert_type,
                severity=severity,
                title=title,
                description=description,
                timestamp=datetime.now(),
                labels=labels,
                annotations=annotations
            )
            
            # Guardar alerta
            self._alerts[alert.id] = alert
            self._throttling[alert_type] = current_time
            
            # Persistir a archivo
            self._save_alerts()
            
            # Log de la alerta (sin usar AlertManager component para evitar recursión)
            logger.bind(component="AlertSystem").warning(
                f"ALERT TRIGGERED: {title}",
                alert_id=alert.id,
                alert_type=alert_type.value,
                severity=severity.value,
                description=description
            )
    
    def _load_alerts(self):
        """Carga alertas desde archivo JSON."""
        try:
            if self.alerts_file.exists():
                with open(self.alerts_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for alert_data in data.get('alerts', []):
                    alert = Alert.from_dict(alert_data)
                    self._alerts[alert.id] = alert
                    
                logger.info(
                    f"Cargadas {len(self._alerts)} alertas desde {self.alerts_file}",
                    extra={"component": "AlertManager"}
                )
        except Exception as e:
            logger.error(
                f"Error cargando alertas: {e}",
                extra={"component": "AlertManager"}
            )
    
    def _save_alerts(self):
        """Guarda alertas a archivo JSON."""
        try:
            # Limpiar alertas antiguas antes de guardar
            self._cleanup_old_alerts()
            
            data = {
                'alerts': [alert.to_dict() for alert in self._alerts.values()],
                'last_updated': datetime.now().isoformat()
            }
            
            # Escribir de forma atómica
            temp_file = self.alerts_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            temp_file.replace(self.alerts_file)
            
        except Exception as e:
            logger.error(
                f"Error guardando alertas: {e}",
                extra={"component": "AlertManager"}
            )
    
    def _cleanup_old_alerts(self):
        """Limpia alertas antiguas según retention policy."""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        
        old_alert_ids = [
            alert_id for alert_id, alert in self._alerts.items()
            if alert.timestamp < cutoff_time
        ]
        
        for alert_id in old_alert_ids:
            del self._alerts[alert_id]
        
        if old_alert_ids:
            logger.debug(
                f"Limpiadas {len(old_alert_ids)} alertas antiguas",
                extra={"component": "AlertManager"}
            )
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Obtiene alertas activas (no resueltas)."""
        with self._lock:
            return [
                alert.to_dict() 
                for alert in self._alerts.values() 
                if not alert.resolved
            ]
    
    def get_all_alerts(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Obtiene todas las alertas, ordenadas por timestamp descendente."""
        with self._lock:
            alerts = sorted(
                self._alerts.values(),
                key=lambda x: x.timestamp,
                reverse=True
            )
            
            if limit:
                alerts = alerts[:limit]
            
            return [alert.to_dict() for alert in alerts]
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Marca una alerta como resuelta."""
        with self._lock:
            if alert_id in self._alerts:
                self._alerts[alert_id].resolved = True
                self._alerts[alert_id].resolved_at = datetime.now()
                self._save_alerts()
                
                logger.info(
                    f"Alerta resuelta: {alert_id}",
                    extra={"component": "AlertManager", "alert_id": alert_id}
                )
                return True
            return False
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de alertas para dashboard."""
        with self._lock:
            active_alerts = [alert for alert in self._alerts.values() if not alert.resolved]
            
            summary = {
                "total_alerts": len(self._alerts),
                "active_alerts": len(active_alerts),
                "resolved_alerts": len(self._alerts) - len(active_alerts),
                "alerts_by_severity": defaultdict(int),
                "alerts_by_type": defaultdict(int),
                "latest_alert": None,
                "last_updated": datetime.now().isoformat()
            }
            
            for alert in active_alerts:
                summary["alerts_by_severity"][alert.severity.value] += 1
                summary["alerts_by_type"][alert.alert_type.value] += 1
            
            if active_alerts:
                latest = max(active_alerts, key=lambda x: x.timestamp)
                summary["latest_alert"] = latest.to_dict()
            
            return summary
    
    def test_alert_system(self):
        """Dispara alertas de prueba para verificar funcionamiento."""
        logger.warning(
            "Testing alert system - triggering test alerts",
            extra={"component": "AlertTest"}
        )
        
        # Simular error de Groq
        logger.error(
            "Test: Groq API connection failed",
            extra={
                "component": "TestGroq",
                "error_type": ErrorType.GROQ_API_ERROR.value
            }
        )
        
        # Simular alta latencia
        logger.info(
            "Test: High latency operation completed",
            extra={
                "component": "TestLatency",
                "phase": "test_phase",
                "elapsed_seconds": 35.5
            }
        )
        
        # Simular error de Supabase
        logger.error(
            "Test: Supabase RPC call failed",
            extra={
                "component": "TestSupabase",
                "error_type": ErrorType.SUPABASE_ERROR.value,
                "rpc_name": "test_rpc"
            }
        )
        
        logger.info(
            "Alert system test completed - check alerts endpoint",
            extra={"component": "AlertTest"}
        )


# Instancia global del gestor de alertas
alert_manager = AlertManager()


def get_alert_manager() -> AlertManager:
    """Obtiene la instancia global del gestor de alertas."""
    return alert_manager


def test_alert_system():
    """Función de conveniencia para testing."""
    get_alert_manager().test_alert_system()


# Configuración para FastAPI
def setup_alert_endpoints(app):
    """
    Configura endpoints de alertas para aplicación FastAPI.
    
    Args:
        app: Instancia de FastAPI
    """
    @app.get("/monitoring/alerts")
    async def get_alerts(active_only: bool = False, limit: int = 100):
        """Obtiene alertas del sistema."""
        manager = get_alert_manager()
        
        if active_only:
            alerts = manager.get_active_alerts()
        else:
            alerts = manager.get_all_alerts(limit=limit)
        
        return {
            "alerts": alerts,
            "total": len(alerts),
            "timestamp": datetime.now().isoformat()
        }
    
    @app.get("/monitoring/alerts/summary")
    async def get_alerts_summary():
        """Obtiene resumen de alertas para dashboard."""
        manager = get_alert_manager()
        return manager.get_alert_summary()
    
    @app.post("/monitoring/alerts/{alert_id}/resolve")
    async def resolve_alert(alert_id: str):
        """Marca una alerta como resuelta."""
        manager = get_alert_manager()
        success = manager.resolve_alert(alert_id)
        
        if success:
            return {"message": "Alert resolved successfully", "alert_id": alert_id}
        else:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Alert not found")
    
    @app.post("/monitoring/alerts/test")
    async def trigger_test_alerts():
        """Dispara alertas de prueba para testing."""
        manager = get_alert_manager()
        manager.test_alert_system()
        return {"message": "Test alerts triggered"}
    
    logger.info(
        "Alert endpoints configurados",
        extra={"component": "AlertManager"}
    )


if __name__ == "__main__":
    # Test del sistema de alertas
    print("Testing Alert Manager...")
    
    # Configurar logging para testing
    from loguru import logger
    import sys
    
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="{time} | {level} | {message}")
    
    # Crear instancia y probar
    manager = AlertManager()
    
    # Disparar alertas de prueba
    manager.test_alert_system()
    
    # Mostrar resultados
    import time
    time.sleep(1)  # Esperar a que se procesen las alertas
    
    print("\n=== Resumen de Alertas ===")
    summary = manager.get_alert_summary()
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    
    print("\n=== Alertas Activas ===")
    active = manager.get_active_alerts()
    for alert in active:
        print(f"- {alert['title']} ({alert['severity']}) - {alert['description']}")
    
    print(f"\nAlertas guardadas en: {manager.alerts_file}")
