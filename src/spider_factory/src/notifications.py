"""
Sistema de Notificaciones para Spider Factory 2.0
Alertas sobre fallos repetidos y cambios de estructura
"""
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
import httpx

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """Tipos de notificación"""
    SPIDER_FAILURE = "spider_failure"
    STRUCTURE_CHANGE = "structure_change"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    PATTERN_FAILURE = "pattern_failure"
    SYSTEM_ERROR = "system_error"
    KPI_ALERT = "kpi_alert"


class NotificationPriority(str, Enum):
    """Prioridad de las notificaciones"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationSystem:
    """
    Sistema central de notificaciones y alertas
    """
    
    def __init__(self, redis_client, config: Optional[Dict] = None):
        self.redis = redis_client
        self.prefix = "spider_factory:notifications"
        self.config = config or {}
        
        # Configuración de umbrales
        self.failure_threshold = self.config.get("failure_threshold", 3)  # Fallos antes de notificar
        self.time_window = self.config.get("time_window", 3600)  # Ventana de tiempo (1 hora)
        
        # Configuración de canales
        self.slack_webhook = self.config.get("slack_webhook")
        self.email_enabled = self.config.get("email_enabled", False)
        
    async def notify_spider_failure(
        self, 
        spider_name: str, 
        medio: str,
        seccion: str,
        error: str,
        traceback: Optional[str] = None
    ):
        """
        Notifica fallos repetidos de un spider
        """
        # Registrar el fallo
        failure_key = f"{self.prefix}:failures:{spider_name}"
        
        failure_data = {
            "timestamp": datetime.now().isoformat(),
            "error": error,
            "traceback": traceback
        }
        
        # Agregar a lista de fallos recientes
        await self.redis.lpush(failure_key, json.dumps(failure_data))
        await self.redis.expire(failure_key, self.time_window)
        
        # Contar fallos en la ventana de tiempo
        failure_count = await self.redis.llen(failure_key)
        
        # Si supera el umbral, enviar notificación
        if failure_count >= self.failure_threshold:
            notification = {
                "type": NotificationType.SPIDER_FAILURE,
                "priority": NotificationPriority.HIGH if failure_count >= 5 else NotificationPriority.MEDIUM,
                "spider_name": spider_name,
                "medio": medio,
                "seccion": seccion,
                "failure_count": failure_count,
                "time_window_hours": self.time_window / 3600,
                "last_error": error,
                "timestamp": datetime.now().isoformat()
            }
            
            await self._send_notification(
                title=f"🚨 Spider Fallando: {spider_name}",
                message=f"El spider {spider_name} ha fallado {failure_count} veces en las últimas {self.time_window/3600} horas.\n\nÚltimo error: {error}",
                notification_data=notification
            )
            
            # Resetear contador después de notificar
            if failure_count >= self.failure_threshold * 2:
                await self.redis.delete(failure_key)
                
    async def notify_structure_change(
        self, 
        medio: str,
        url: str,
        cambios: Dict[str, Any]
    ):
        """
        Alerta sobre cambios detectados en la estructura de un sitio
        """
        notification = {
            "type": NotificationType.STRUCTURE_CHANGE,
            "priority": NotificationPriority.HIGH,
            "medio": medio,
            "url": url,
            "cambios": cambios,
            "timestamp": datetime.now().isoformat()
        }
        
        # Formatear mensaje con detalles de cambios
        cambios_texto = "\n".join([f"- {k}: {v}" for k, v in cambios.items()])
        
        await self._send_notification(
            title=f"🔄 Cambio de Estructura: {medio}",
            message=f"Se detectaron cambios en la estructura de {medio}:\n\n{cambios_texto}\n\nURL: {url}",
            notification_data=notification
        )
        
    async def notify_performance_degradation(
        self,
        component: str,
        current_value: float,
        threshold: float,
        metric_name: str
    ):
        """
        Notifica degradación en el rendimiento
        """
        degradation_percentage = ((current_value - threshold) / threshold) * 100
        
        notification = {
            "type": NotificationType.PERFORMANCE_DEGRADATION,
            "priority": NotificationPriority.MEDIUM if degradation_percentage < 50 else NotificationPriority.HIGH,
            "component": component,
            "metric_name": metric_name,
            "current_value": current_value,
            "threshold": threshold,
            "degradation_percentage": degradation_percentage,
            "timestamp": datetime.now().isoformat()
        }
        
        await self._send_notification(
            title=f"⚠️ Degradación de Rendimiento: {component}",
            message=f"El {metric_name} de {component} está {degradation_percentage:.1f}% por encima del umbral.\n\nValor actual: {current_value}\nUmbral: {threshold}",
            notification_data=notification
        )
        
    async def notify_kpi_alert(
        self,
        kpi_name: str,
        current_value: float,
        target_value: float,
        is_critical: bool = False
    ):
        """
        Alerta sobre KPIs no cumplidos
        """
        notification = {
            "type": NotificationType.KPI_ALERT,
            "priority": NotificationPriority.CRITICAL if is_critical else NotificationPriority.HIGH,
            "kpi_name": kpi_name,
            "current_value": current_value,
            "target_value": target_value,
            "gap_percentage": abs((current_value - target_value) / target_value * 100),
            "timestamp": datetime.now().isoformat()
        }
        
        emoji = "🔴" if is_critical else "🟡"
        
        await self._send_notification(
            title=f"{emoji} KPI No Cumplido: {kpi_name}",
            message=f"El KPI {kpi_name} está fuera del objetivo.\n\nValor actual: {current_value}\nObjetivo: {target_value}",
            notification_data=notification
        )
        
    async def check_and_notify_system_health(self, metrics: Dict[str, Any]):
        """
        Verifica la salud del sistema y notifica si hay problemas
        """
        alerts = []
        
        # Verificar KPIs críticos
        kpi_checks = [
            ("Tiempo RSS", metrics.get("tiempo_promedio_rss", 0), 5, 
             metrics.get("tiempo_promedio_rss", 0) > 10),
            ("Tiempo Cache", metrics.get("tiempo_promedio_cache", 0), 2,
             metrics.get("tiempo_promedio_cache", 0) > 5),
            ("Reducción de Tiempo", metrics.get("tiempo_reduccion", 0), 97,
             metrics.get("tiempo_reduccion", 0) < 90),
            ("Precisión Spiders", metrics.get("precision_spiders", 100), 90,
             metrics.get("precision_spiders", 100) < 80)
        ]
        
        for kpi_name, current, target, is_critical in kpi_checks:
            if (kpi_name == "Reducción de Tiempo" and current < target) or \
               (kpi_name != "Reducción de Tiempo" and current > target):
                await self.notify_kpi_alert(kpi_name, current, target, is_critical)
                alerts.append(kpi_name)
                
        return alerts
        
    async def _send_notification(
        self, 
        title: str, 
        message: str, 
        notification_data: Dict[str, Any]
    ):
        """
        Envía la notificación por los canales configurados
        """
        # Guardar en Redis para historial
        await self._save_notification_history(notification_data)
        
        # Log siempre
        priority = notification_data.get("priority", "medium")
        if priority in [NotificationPriority.HIGH, NotificationPriority.CRITICAL]:
            logger.error(f"{title}: {message}")
        else:
            logger.warning(f"{title}: {message}")
            
        # Slack si está configurado
        if self.slack_webhook:
            await self._send_slack(title, message, notification_data)
            
        # Email si está habilitado
        if self.email_enabled:
            await self._send_email(title, message, notification_data)
            
    async def _save_notification_history(self, notification_data: Dict[str, Any]):
        """
        Guarda historial de notificaciones
        """
        history_key = f"{self.prefix}:history"
        
        # Agregar a lista
        await self.redis.lpush(history_key, json.dumps(notification_data))
        
        # Mantener solo las últimas 1000 notificaciones
        await self.redis.ltrim(history_key, 0, 999)
        
        # También agregar a un set por tipo para búsquedas
        type_key = f"{self.prefix}:by_type:{notification_data['type']}"
        await self.redis.lpush(type_key, json.dumps(notification_data))
        await self.redis.ltrim(type_key, 0, 99)
        
    async def _send_slack(self, title: str, message: str, notification_data: Dict[str, Any]):
        """
        Envía notificación a Slack
        """
        if not self.slack_webhook:
            return
            
        try:
            # Formatear para Slack
            color_map = {
                NotificationPriority.LOW: "#36a64f",      # Verde
                NotificationPriority.MEDIUM: "#ff9900",   # Naranja
                NotificationPriority.HIGH: "#ff0000",     # Rojo
                NotificationPriority.CRITICAL: "#990000"  # Rojo oscuro
            }
            
            color = color_map.get(notification_data.get("priority"), "#ff9900")
            
            slack_message = {
                "attachments": [{
                    "color": color,
                    "title": title,
                    "text": message,
                    "fields": [
                        {
                            "title": "Tipo",
                            "value": notification_data.get("type", "unknown"),
                            "short": True
                        },
                        {
                            "title": "Prioridad",
                            "value": notification_data.get("priority", "medium"),
                            "short": True
                        }
                    ],
                    "footer": "Spider Factory 2.0",
                    "ts": int(datetime.now().timestamp())
                }]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.slack_webhook,
                    json=slack_message,
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Error enviando a Slack: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error enviando notificación a Slack: {e}")
            
    async def _send_email(self, title: str, message: str, notification_data: Dict[str, Any]):
        """
        Envía notificación por email (placeholder para implementación futura)
        """
        # TODO: Implementar envío de email si se requiere
        pass
        
    async def get_notification_history(
        self, 
        notification_type: Optional[NotificationType] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Obtiene historial de notificaciones
        """
        if notification_type:
            key = f"{self.prefix}:by_type:{notification_type}"
        else:
            key = f"{self.prefix}:history"
            
        # Obtener notificaciones
        notifications = await self.redis.lrange(key, 0, limit - 1)
        
        # Parsear JSON
        return [json.loads(n) for n in notifications]
        
    async def get_notification_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de notificaciones
        """
        stats = {
            "total": await self.redis.llen(f"{self.prefix}:history"),
            "by_type": {},
            "by_priority": {},
            "last_24h": 0
        }
        
        # Contar por tipo
        for notif_type in NotificationType:
            count = await self.redis.llen(f"{self.prefix}:by_type:{notif_type.value}")
            if count > 0:
                stats["by_type"][notif_type.value] = count
                
        # Obtener últimas 100 para analizar prioridad y tiempo
        recent = await self.get_notification_history(limit=100)
        
        now = datetime.now()
        for notif in recent:
            # Contar por prioridad
            priority = notif.get("priority", "medium")
            stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + 1
            
            # Contar últimas 24h
            notif_time = datetime.fromisoformat(notif["timestamp"])
            if now - notif_time <= timedelta(hours=24):
                stats["last_24h"] += 1
                
        return stats


# Funciones auxiliares para integración
async def setup_notification_handlers(redis_client, config: Optional[Dict] = None):
    """
    Configura el sistema de notificaciones
    """
    notification_config = config or {}
    
    # Agregar configuración desde environment si existe
    import os
    if os.getenv("SLACK_WEBHOOK_URL"):
        notification_config["slack_webhook"] = os.getenv("SLACK_WEBHOOK_URL")
        
    return NotificationSystem(redis_client, notification_config)


# Ejemplo de uso
if __name__ == "__main__":
    import asyncio
    from .redis_pool import get_redis_client
    
    async def test_notifications():
        """Test del sistema de notificaciones"""
        client = await get_redis_client()
        
        # Configurar con webhook de prueba (no envía realmente)
        config = {
            "slack_webhook": "https://hooks.slack.com/services/TEST/TEST/TEST",
            "failure_threshold": 2  # Bajo para pruebas
        }
        
        notifications = NotificationSystem(client, config)
        
        # Simular fallos de spider
        print("Simulando fallos de spider...")
        for i in range(3):
            await notifications.notify_spider_failure(
                "el_pais_internacional",
                "El País",
                "Internacional",
                f"Error de conexión #{i+1}"
            )
            await asyncio.sleep(0.1)
            
        # Simular cambio de estructura
        print("\nSimulando cambio de estructura...")
        await notifications.notify_structure_change(
            "La Nación",
            "https://lanacion.com.ar",
            {
                "selector_titulo": ".title → .article-title",
                "selector_contenido": ".content → .article-body",
                "nueva_estructura": "Detectado nuevo diseño responsive"
            }
        )
        
        # Simular degradación de rendimiento
        print("\nSimulando degradación de rendimiento...")
        await notifications.notify_performance_degradation(
            "RSS Parser",
            8.5,  # Valor actual
            5.0,  # Umbral
            "Tiempo de procesamiento"
        )
        
        # Obtener estadísticas
        print("\nEstadísticas de notificaciones:")
        stats = await notifications.get_notification_stats()
        print(json.dumps(stats, indent=2))
        
        # Obtener historial
        print("\nÚltimas notificaciones:")
        history = await notifications.get_notification_history(limit=5)
        for notif in history:
            print(f"- [{notif['type']}] {notif.get('priority', 'medium')}: {notif['timestamp']}")
    
    asyncio.run(test_notifications())