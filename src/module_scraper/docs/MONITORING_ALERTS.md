# Sistema de Monitoreo y Alertas - Spidermon

Este documento detalla el sistema de monitoreo automático implementado con Spidermon para detectar y alertar sobre problemas en la extracción de noticias.

## 📋 Índice
1. [Visión General del Sistema](#visión-general-del-sistema)
2. [Monitores Implementados](#monitores-implementados)
3. [Configuración de Alertas](#configuración-de-alertas)
4. [Interpretación de Alertas](#interpretación-de-alertas)
5. [Personalización y Ajustes](#personalización-y-ajustes)
6. [Ejemplos de Alertas](#ejemplos-de-alertas)

---

## 🎯 Visión General del Sistema

### ¿Qué es Spidermon?

Spidermon es un sistema de monitoreo inteligente que:
- **Vigila** automáticamente cada spider cuando termina
- **Detecta** problemas comunes sin intervención humana
- **Alerta** por múltiples canales cuando algo va mal
- **Recomienda** acciones para resolver problemas

### Arquitectura del Sistema de Alertas

```
Spider Finaliza
       │
       ▼
┌──────────────┐
│  Spidermon   │
│  Extension   │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────┐
│        Ejecuta Monitores         │
├──────────────────────────────────┤
│ • StructureChangeMonitor         │
│ • CriticalFieldsMonitor          │
│ • ResponseTimeMonitor            │
│ • HTTPErrorRateMonitor           │
└──────────────┬───────────────────┘
               │
               ▼
        ¿Errores Detectados?
              /│\
             / │ \
            /  │  \
           ▼   ▼   ▼
      Email Webhook Logs
```

---

## 🔍 Monitores Implementados

### 1. Monitor de Cambios Estructurales (StructureChangeMonitor)

**¿Qué detecta?**
Cuando un sitio web cambia su HTML y los selectores dejan de funcionar.

**¿Por qué es importante?**
Si el sitio cambia su estructura, el spider puede estar extrayendo datos vacíos o incorrectos.

**Configuración:**
```python
# Campos que vigila
critical_fields = ['titulo', 'contenido_texto', 'url', 'medio']

# Umbral de alerta
threshold = 0.1  # 10% máximo de campos vacíos
```

**Ejemplo de alerta:**
```
ALERTA: Structure Change Monitor
Spider: elpais_spider
Problema: 25% de artículos sin titulo. Posible cambio en estructura HTML del sitio.
Acción: Revisar selectores XPath/CSS del spider
```

### 2. Monitor de Campos Críticos (CriticalFieldsMonitor)

**¿Qué detecta?**
Campos obligatorios que están vacíos o inválidos.

**¿Por qué es importante?**
Garantiza la calidad mínima de los datos extraídos.

**Umbrales por campo:**
| Campo | Máximo % Vacío | Criticidad |
|-------|----------------|------------|
| url | 0% | Crítico |
| titulo | 5% | Alto |
| contenido_texto | 5% | Alto |
| medio | 0% | Crítico |
| fecha_recopilacion | 0% | Crítico |

**Ejemplo de alerta:**
```
ALERTA: Critical Fields Monitor
Spider: elmundo_spider
Problema: Campo crítico 'contenido_texto': 8.5% con problemas (vacío o inválido)
Máximo permitido: 5%
```

### 3. Monitor de Tiempo de Respuesta (ResponseTimeMonitor)

**¿Qué detecta?**
- Sitios web lentos
- Problemas de conectividad
- Sobrecarga del servidor

**¿Por qué es importante?**
Tiempos altos pueden indicar que el sitio está bloqueando las peticiones o hay problemas de red.

**Configuración:**
```python
# Tiempo máximo aceptable (milisegundos)
MAX_RESPONSE_TIME = 5000  # 5 segundos
```

**Ejemplo de alerta:**
```
ALERTA: Response Time Monitor
Spider: lavanguardia_spider
Problema: Tiempo de respuesta promedio: 7500ms (máximo aceptable: 5000ms)
El sitio puede estar lento o hay problemas de red.
Acción: Considerar aumentar DOWNLOAD_DELAY
```

### 4. Monitor de Errores HTTP (HTTPErrorRateMonitor)

**¿Qué detecta?**
Tasas altas de errores HTTP que indican problemas de acceso.

**Códigos monitoreados:**
| Código | Significado | Acción Sugerida |
|--------|-------------|-----------------|
| 403 | Forbidden | Posible bloqueo, revisar headers |
| 429 | Too Many Requests | Reducir velocidad |
| 500 | Server Error | Problema del servidor |
| 502 | Bad Gateway | Problema temporal |
| 503 | Service Unavailable | Sitio sobrecargado |
| 504 | Gateway Timeout | Aumentar timeout |

**Umbrales:**
- Tasa general de error: máximo 10%
- Bloqueos (403/429): máximo 5%

**Ejemplo de alerta:**
```
ALERTA: HTTP Error Rate Monitor
Spider: abc_spider
Problema: Tasa de error HTTP: 15% 
Detalles: 403 Forbidden: 45, 429 Too Many Requests: 12
Acción: Considere usar proxies o ajustar DOWNLOAD_DELAY
```

---

## 🔔 Configuración de Alertas

### 1. Alertas por Email

**Configuración en `.env`:**
```env
# Servidor SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=alertas@tuempresa.com
SMTP_PASSWORD=contraseña-aplicacion  # NO usar contraseña normal
SMTP_FROM=lamaquina-alertas@tuempresa.com
SMTP_TO=admin@tuempresa.com,equipo@tuempresa.com  # Múltiples con comas
```

**Formato del email:**
```
Asunto: [La Máquina - Spider Alert] FAILED - Spider: elpais_spider

Spider: elpais_spider
Fecha: 2024-01-20 14:30:45

--- ERRORES DETECTADOS ---
• StructureChangeMonitor: 25% de artículos sin titulo
• HTTPErrorRateMonitor: Tasa de error HTTP: 12%

--- ESTADÍSTICAS ---
Items extraídos: 45
Páginas descargadas: 120
Errores HTTP: 14
Tiempo de ejecución: 245.32 segundos

--- RECOMENDACIONES ---
• Revisar selectores XPath/CSS del spider
• Verificar si el sitio web cambió su estructura HTML
• Considerar usar proxies o rotar user agents
```

### 2. Alertas por Webhook

**Configuración:**
```env
SPIDERMON_WEBHOOK_URL=https://hooks.slack.com/services/TU/WEBHOOK/URL
```

**Payload JSON enviado:**
```json
{
  "timestamp": "2024-01-20T14:30:45Z",
  "spider": {
    "name": "elpais_spider",
    "project": "lamaquina_scraper"
  },
  "status": "error",
  "stats": {
    "items_scraped": 45,
    "pages_downloaded": 120,
    "duration_seconds": 245.32,
    "http_errors": {
      "403": 8,
      "429": 6
    }
  },
  "monitors_failed": [
    {
      "monitor": "StructureChangeMonitor",
      "message": "25% de artículos sin titulo",
      "severity": "critical"
    }
  ],
  "environment": "production"
}
```

### 3. Logs Estructurados

**Formato de log:**
```json
{
  "event_type": "spidermon_alert",
  "timestamp": "2024-01-20T14:30:45Z",
  "spider_name": "elpais_spider",
  "environment": "production",
  "monitors_status": {
    "total": 4,
    "passed": 2,
    "failed": 2
  },
  "spider_stats": {
    "items_scraped": 45,
    "duration_seconds": 245.32,
    "memory_usage_mb": 156.4
  },
  "failures": [
    {
      "monitor": "StructureChangeMonitor",
      "message": "25% de artículos sin titulo",
      "severity": "critical"
    }
  ]
}
```

---

## 📊 Interpretación de Alertas

### Niveles de Severidad

| Nivel | Icono | Significado | Acción Requerida |
|-------|-------|-------------|------------------|
| **INFO** | ℹ️ | Informativo | No requiere acción |
| **WARNING** | ⚠️ | Advertencia | Revisar cuando sea posible |
| **CRITICAL** | 🚨 | Crítico | Acción inmediata necesaria |

### Guía de Interpretación por Monitor

#### Alerta: "Posible cambio en estructura HTML"
**Significa:** El sitio web probablemente cambió su diseño
**Verificar:**
1. Visitar el sitio web manualmente
2. Comparar con capturas anteriores
3. Revisar selectores en el código del spider

**Solución:**
- Actualizar selectores XPath/CSS
- Considerar selectores más robustos
- Implementar múltiples estrategias de extracción

#### Alerta: "Tasa de error HTTP alta"
**Significa:** Muchas peticiones están fallando
**Verificar:**
1. Códigos de error específicos
2. Patrones temporales
3. IPs bloqueadas

**Solución según código:**
- **403/429**: Reducir velocidad, usar proxies
- **500-504**: Esperar y reintentar más tarde
- **Timeout**: Aumentar DOWNLOAD_TIMEOUT

#### Alerta: "Campos críticos vacíos"
**Significa:** Datos importantes no se están extrayendo
**Verificar:**
1. Si es problema generalizado o casos específicos
2. Logs del spider para ver errores
3. Ejemplos de páginas problemáticas

**Solución:**
- Ajustar selectores
- Manejar casos especiales
- Implementar valores por defecto

---

## ⚙️ Personalización y Ajustes

### Ajustar Umbrales Globales

En `.env`:
```env
# Número mínimo de items esperados
SPIDERMON_MIN_ITEMS_SCRAPED=10

# Errores críticos máximos permitidos
SPIDERMON_MAX_CRITICAL_ERRORS=0

# Mensajes de error máximos
SPIDERMON_MAX_ERROR_MESSAGES=5

# Tiempo de respuesta máximo (ms)
SPIDERMON_MAX_RESPONSE_TIME=5000
```

### Personalizar por Spider

En el spider específico:
```python
class ElPaisSpider(BaseSpider):
    custom_settings = {
        'SPIDERMON_MIN_ITEMS_SCRAPED': 50,  # Este spider debe extraer más
        'SPIDERMON_MAX_RESPONSE_TIME': 8000,  # Sitio conocido por ser lento
    }
```

### Desactivar Monitores Específicos

Para desactivar temporalmente un monitor:
```python
# En settings.py
SPIDERMON_SPIDER_CLOSE_MONITORS = [
    'scraper_core.monitors.spider_monitors.SpiderCloseMonitorSuite',
]

# O crear suite personalizada sin ciertos monitores
class CustomMonitorSuite(MonitorSuite):
    monitors = [
        BasicStatsMonitor,
        # HTTPErrorRateMonitor,  # Comentado para desactivar
        CriticalFieldsMonitor,
    ]
```

### Agregar Campos al Monitoreo

Para monitorear campos adicionales:
```python
# En spider_monitors.py
critical_fields = ['titulo', 'contenido_texto', 'url', 'medio', 'autor']  # Agregado 'autor'
```

---

## 📧 Ejemplos de Alertas

### Ejemplo 1: Sitio Bloqueando Requests

```
ASUNTO: [La Máquina - Spider Alert] FAILED - Spider: abc_spider

--- ERRORES DETECTADOS ---
• HTTPErrorRateMonitor: Posible bloqueo detectado: 45% de respuestas son 403 Forbidden (234) o 429 Rate Limit (89). Considere usar proxies o ajustar DOWNLOAD_DELAY.

--- RECOMENDACIONES ---
• Aumentar DOWNLOAD_DELAY en configuración
• Considerar usar proxies o rotar user agents
• Verificar si el sitio está bloqueando las solicitudes
```

### Ejemplo 2: Cambio en Estructura del Sitio

```
ASUNTO: [La Máquina - Spider Alert] WARNING - Spider: elmundo_spider

--- ERRORES DETECTADOS ---
• StructureChangeMonitor: 35.2% de artículos sin contenido_texto. Posible cambio en estructura HTML del sitio.
• CriticalFieldsMonitor: Campo crítico contenido_texto: 35.2% con problemas (vacío o inválido). Máximo permitido: 5.0%

--- RECOMENDACIONES ---
• Revisar selectores XPath/CSS del spider
• Verificar si el sitio web cambió su estructura HTML
```

### Ejemplo 3: Problemas de Rendimiento

```
ASUNTO: [La Máquina - Spider Alert] WARNING - Spider: lavanguardia_spider

--- ERRORES DETECTADOS ---
• ResponseTimeMonitor: Tiempo de respuesta promedio: 8234ms (máximo aceptable: 5000ms). El sitio puede estar lento o hay problemas de red.

--- ESTADÍSTICAS ---
Items extraídos: 23
Páginas descargadas: 89
Tiempo de ejecución: 732.45 segundos

--- RECOMENDACIONES ---
• Verificar conectividad con el sitio web
• Considerar aumentar timeouts
• Revisar si el sitio está experimentando problemas
```

---

## 🛠️ Solución Rápida de Problemas Comunes

| Alerta Frecuente | Causa Probable | Solución Rápida |
|------------------|----------------|-----------------|
| "0 items extraídos" | Selectores rotos | Actualizar XPath/CSS |
| "403 Forbidden alto" | IP bloqueada | Usar proxies |
| "Timeout frecuentes" | Sitio lento | Aumentar DOWNLOAD_TIMEOUT |
| "Campos vacíos" | Cambio en HTML | Revisar estructura |
| "429 Too Many Requests" | Rate limiting | Aumentar DOWNLOAD_DELAY |

---

📖 **Siguiente**: [Guía de Solución de Problemas](TROUBLESHOOTING.md) - Resolución detallada de problemas