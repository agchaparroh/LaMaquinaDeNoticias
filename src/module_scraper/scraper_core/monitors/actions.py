"""
Acciones personalizadas de Spidermon para La Máquina de Noticias
Incluye notificaciones por email, webhook y logging estructurado
"""

import json  # noqa: F401
import logging
import os
from datetime import datetime
from typing import Any, Dict, List

import requests
from spidermon import Action
from spidermon.contrib.actions.email import SendEmail

logger = logging.getLogger(__name__)


class SendEmailAlert(SendEmail):
    """
    Acción personalizada para enviar alertas por email con formato mejorado
    """

    def __init__(self, *args, **kwargs):
        # Configuración desde variables de entorno
        smtp_config = {
            "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
            "smtp_port": int(os.getenv("SMTP_PORT", 587)),
            "smtp_user": os.getenv("SMTP_USER", ""),
            "smtp_password": os.getenv("SMTP_PASSWORD", ""),
            "smtp_use_tls": True,
            "from_addr": os.getenv("SMTP_FROM", "scrapydweb@lamaquina.com"),
            "to": os.getenv("SMTP_TO", "alertas@lamaquina.com").split(","),
            "subject_prefix": "[La Máquina - Spider Alert]",
        }

        # Actualizar kwargs con configuración
        kwargs.update(smtp_config)
        super().__init__(*args, **kwargs)

    def get_subject(self) -> str:
        """Generar asunto del email con información del spider"""
        spider_name = self.data.spider.name
        status = "FAILED" if self.result.has_errors() else "WARNING"
        return f"{self.subject_prefix} {status} - Spider: {spider_name}"

    def get_body(self) -> str:
        """Generar cuerpo del email con detalles de los errores"""
        spider_name = self.data.spider.name
        stats = dict(self.data.stats) if hasattr(self.data, "stats") else {}

        # Construir el cuerpo del mensaje
        body_parts = [
            f"Spider: {spider_name}",
            f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"\n--- ERRORES DETECTADOS ---\n",  # noqa: F541
        ]

        # Agregar detalles de cada error
        for error in self.result.failures:
            monitor_name = error.get("monitor", "Unknown Monitor")
            message = error.get("message", "Sin mensaje de error")
            body_parts.append(f"• {monitor_name}: {message}")

        # Agregar estadísticas relevantes
        body_parts.extend(
            [
                f"\n--- ESTADÍSTICAS ---\n",  # noqa: F541
                f"Items extraídos: {stats.get('item_scraped_count', 0)}",
                f"Páginas descargadas: {stats.get('downloader/response_count', 0)}",
                f"Errores HTTP: {self._count_http_errors(stats)}",
                f"Tiempo de ejecución: {stats.get('elapsed_time_seconds', 0):.2f} segundos",
            ]
        )

        # Agregar recomendaciones si hay errores específicos
        recommendations = self._get_recommendations(self.result.failures)
        if recommendations:
            body_parts.extend(["\n--- RECOMENDACIONES ---\n"] + recommendations)

        return "\n".join(body_parts)

    def _count_http_errors(self, stats: Dict[str, Any]) -> int:
        """Contar total de errores HTTP"""
        error_codes = [403, 429, 500, 502, 503, 504]
        total = 0
        for code in error_codes:
            total += stats.get(f"downloader/response_status_count/{code}", 0)
        return total

    def _get_recommendations(self, failures: List[Dict[str, Any]]) -> List[str]:
        """Generar recomendaciones basadas en los errores detectados"""
        recommendations = []

        for failure in failures:
            monitor = failure.get("monitor", "")

            if "StructureChangeMonitor" in monitor:
                recommendations.append("• Revisar selectores XPath/CSS del spider")
                recommendations.append(
                    "• Verificar si el sitio web cambió su estructura HTML"
                )

            elif "HTTPErrorRateMonitor" in monitor:
                recommendations.append("• Aumentar DOWNLOAD_DELAY en configuración")
                recommendations.append("• Considerar usar proxies o rotar user agents")
                recommendations.append(
                    "• Verificar si el sitio está bloqueando las solicitudes"
                )

            elif "ResponseTimeMonitor" in monitor:
                recommendations.append("• Verificar conectividad con el sitio web")
                recommendations.append("• Considerar aumentar timeouts")
                recommendations.append(
                    "• Revisar si el sitio está experimentando problemas"
                )

        return list(set(recommendations))  # Eliminar duplicados


class SendWebhookAlert(Action):
    """
    Acción para enviar alertas a un webhook externo (integración con otros sistemas)
    """

    def run_action(self):
        """Ejecutar la acción de webhook"""
        webhook_url = os.getenv("SPIDERMON_WEBHOOK_URL")

        if not webhook_url:
            logger.warning("SPIDERMON_WEBHOOK_URL no configurada, omitiendo webhook")
            return

        # Preparar payload
        payload = self._prepare_payload()

        # Headers
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Spidermon/LaMaquina",
            "X-Spider-Name": self.data.spider.name,
            "X-Alert-Type": "spider-monitor",
        }

        try:
            # Enviar webhook
            response = requests.post(
                webhook_url, json=payload, headers=headers, timeout=10
            )
            response.raise_for_status()
            logger.info(f"Webhook enviado exitosamente a {webhook_url}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error al enviar webhook: {e}")

    def _prepare_payload(self) -> Dict[str, Any]:
        """Preparar el payload para el webhook"""
        stats = dict(self.data.stats) if hasattr(self.data, "stats") else {}

        # Extraer información relevante
        payload = {
            "timestamp": datetime.now().isoformat(),
            "spider": {
                "name": self.data.spider.name,
                "project": "lamaquina_scraper",
            },
            "status": "error" if self.result.has_errors() else "warning",
            "stats": {
                "items_scraped": stats.get("item_scraped_count", 0),
                "pages_downloaded": stats.get("downloader/response_count", 0),
                "duration_seconds": stats.get("elapsed_time_seconds", 0),
                "http_errors": self._count_http_errors(stats),
            },
            "monitors_failed": [],
            "environment": os.getenv("ENVIRONMENT", "development"),
        }

        # Agregar detalles de monitores que fallaron
        for failure in self.result.failures:
            payload["monitors_failed"].append(
                {
                    "monitor": failure.get("monitor", "Unknown"),
                    "message": failure.get("message", "No message"),
                    "severity": self._get_severity(failure),
                }
            )

        return payload

    def _count_http_errors(self, stats: Dict[str, Any]) -> Dict[str, int]:
        """Contar errores HTTP por código"""
        error_codes = [403, 429, 500, 502, 503, 504]
        errors = {}
        for code in error_codes:
            count = stats.get(f"downloader/response_status_count/{code}", 0)
            if count > 0:
                errors[str(code)] = count
        return errors

    def _get_severity(self, failure: Dict[str, Any]) -> str:
        """Determinar severidad del error"""
        monitor = failure.get("monitor", "")

        # Errores críticos
        if any(
            critical in monitor
            for critical in ["HTTPErrorRateMonitor", "StructureChangeMonitor"]
        ):
            return "critical"

        # Errores de advertencia
        elif any(
            warning in monitor
            for warning in ["ResponseTimeMonitor", "CriticalFieldsMonitor"]
        ):
            return "warning"

        # Por defecto
        return "info"


class LogStructuredAlert(Action):
    """
    Acción para registrar alertas en logs estructurados para análisis posterior
    """

    def run_action(self):
        """Ejecutar logging estructurado"""
        log_data = self._prepare_log_data()

        # Determinar nivel de log según severidad
        if self.result.has_errors():
            if self._has_critical_errors():
                logger.error(
                    "SPIDERMON_ALERT_CRITICAL", extra={"structured_data": log_data}
                )
            else:
                logger.warning(
                    "SPIDERMON_ALERT_WARNING", extra={"structured_data": log_data}
                )
        else:
            logger.info("SPIDERMON_ALERT_INFO", extra={"structured_data": log_data})

    def _prepare_log_data(self) -> Dict[str, Any]:
        """Preparar datos estructurados para el log"""
        stats = dict(self.data.stats) if hasattr(self.data, "stats") else {}

        log_data = {
            "event_type": "spidermon_alert",
            "timestamp": datetime.now().isoformat(),
            "spider_name": self.data.spider.name,
            "environment": os.getenv("ENVIRONMENT", "development"),
            "monitors_status": {
                "total": len(self.result.monitors_results),
                "passed": len([r for r in self.result.monitors_results if r.passed]),
                "failed": len(
                    [r for r in self.result.monitors_results if not r.passed]
                ),
            },
            "spider_stats": {
                "items_scraped": stats.get("item_scraped_count", 0),
                "duration_seconds": stats.get("elapsed_time_seconds", 0),
                "memory_usage_mb": stats.get("memusage/max", 0) / 1024 / 1024,
            },
            "failures": [],
        }

        # Agregar detalles de fallas
        for failure in self.result.failures:
            log_data["failures"].append(
                {
                    "monitor": failure.get("monitor", "Unknown"),
                    "message": failure.get("message", ""),
                    "severity": self._get_severity(failure),
                }
            )

        return log_data

    def _has_critical_errors(self) -> bool:
        """Verificar si hay errores críticos"""
        critical_monitors = ["HTTPErrorRateMonitor", "StructureChangeMonitor"]
        for failure in self.result.failures:
            if any(
                monitor in failure.get("monitor", "") for monitor in critical_monitors
            ):
                return True
        return False

    def _get_severity(self, failure: Dict[str, Any]) -> str:
        """Determinar severidad del error"""
        monitor = failure.get("monitor", "")

        if any(
            critical in monitor
            for critical in ["HTTPErrorRateMonitor", "StructureChangeMonitor"]
        ):
            return "critical"
        elif any(
            warning in monitor
            for warning in ["ResponseTimeMonitor", "CriticalFieldsMonitor"]
        ):
            return "warning"
        return "info"


# Acciones combinadas para uso en MonitorSuite
class SendAllAlerts(Action):
    """
    Acción compuesta que ejecuta todas las alertas configuradas
    """

    def run_action(self):
        """Ejecutar todas las acciones de alerta"""
        # Ejecutar cada tipo de alerta
        actions = [
            LogStructuredAlert,
            SendEmailAlert,
            SendWebhookAlert,
        ]

        for action_class in actions:
            try:
                action = action_class()
                action.data = self.data
                action.result = self.result
                action.run_action()
            except Exception as e:
                logger.error(f"Error ejecutando {action_class.__name__}: {e}")
