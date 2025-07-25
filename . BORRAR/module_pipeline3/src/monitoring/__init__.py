"""
Módulo de Monitoreo y Observabilidad
===================================

Este módulo implementa el sistema de monitoreo y observabilidad
para Module Pipeline, incluyendo:

- Sistema de alertas basado en logs
- Colección de métricas
- Endpoints de observabilidad
- Dashboard JSON para visualización
"""

from .alert_manager import (
    Alert,
    AlertManager,
    AlertSeverity,
    AlertType,
    alert_manager,
    get_alert_manager,
    setup_alert_endpoints,
    test_alert_system,
)

__all__ = [
    "AlertManager",
    "Alert",
    "AlertType",
    "AlertSeverity",
    "alert_manager",
    "get_alert_manager",
    "test_alert_system",
    "setup_alert_endpoints",
]
