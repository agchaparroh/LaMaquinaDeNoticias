# Sistema de Alertas Automáticas - Documentación Completa

## 📢 Descripción General

El Sistema de Alertas Automáticas para "Máquina de Noticias" proporciona notificaciones en tiempo real a través de múltiples canales cuando se detectan problemas críticos o condiciones que requieren atención.

### Características Principales

- **Múltiples Canales**: Email, Slack, SMS, Webhooks, Microsoft Teams
- **Escalamiento Automático**: Notificaciones progresivas según gravedad y tiempo
- **Plantillas Personalizables**: Templates específicos por tipo de alerta y canal
- **Rate Limiting**: Prevención de spam de notificaciones
- **Anti-Flood**: Sistema inteligente para evitar duplicados
- **Horarios Configurables**: Notificaciones según horarios de trabajo
- **Auditoría Completa**: Historial detallado de todas las notificaciones

## 🏗️ Arquitectura del Sistema

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Alertas       │    │   Procesador     │    │   Canales de        │
│   Generadas     │───▶│   Central        │───▶│   Notificación      │
│                 │    │                  │    │                     │
│ • Umbrales      │    │ • Anti-flood     │    │ • Email (SMTP)      │
│ • Sistema       │    │ • Rate limiting  │    │ • Slack (Webhook)   │
│ • Supabase      │    │ • Escalamiento   │    │ • SMS (Twilio)      │
│ • Vistas/Jobs   │    │ • Plantillas     │    │ • Webhooks          │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Historial y    │
                       │   Auditoría      │
                       └──────────────────┘
```

## 🚀 Instalación y Configuración

### 1. Instalación de Scripts

```bash
# Ejecutar en orden
psql -f 11_automated_alerts_notification_system.sql
psql -f 12_initial_alerts_configuration.sql
```

### 2. Configuración de Canales

#### A. Configurar Email (SMTP)

```sql
-- Actualizar configuración de email
UPDATE monitoring.notification_channels 
SET configuration = jsonb_build_object(
    'recipient_email', 'tu-email@empresa.com',
    'smtp_server', 'smtp.tuempresa.com',
    'smtp_port', 587,
    'smtp_username', 'notificaciones@tuempresa.com',
    'smtp_password', 'tu_password_seguro',
    'smtp_tls', true
)
WHERE channel_name = 'admin_email';
```

#### B. Configurar Slack

```sql
-- Configurar Slack webhook
UPDATE monitoring.notification_channels 
SET configuration = jsonb_build_object(
    'webhook_url', 'https://hooks.slack.com/services/TU_WEBHOOK_URL',
    'channel_id', '#alertas-sistema',
    'username', 'MonitoringBot',
    'icon_emoji', ':warning:'
)
WHERE channel_name = 'dev_team_slack';
```

#### C. Configurar SMS (Twilio)

```sql
-- Configurar SMS con Twilio
UPDATE monitoring.notification_channels 
SET configuration = jsonb_build_object(
    'provider', 'twilio',
    'account_sid', 'TU_ACCOUNT_SID',
    'auth_token', 'TU_AUTH_TOKEN',
    'from_number', '+1234567890',
    'phone_number', '+1987654321'
)
WHERE channel_name = 'emergency_sms';
```

### 3. Personalizar Plantillas

```sql
-- Crear plantilla personalizada
INSERT INTO monitoring.notification_templates (
    template_name, alert_type, severity, channel_type,
    subject_template, body_template, format_type
) VALUES (
    'mi_plantilla_critica', 'system', 'critical', 'email',
    '[URGENTE] {{title}} - Mi Sistema',
    'Estimado equipo,\n\nSe detectó: {{description}}\nValor: {{metric_value}}\nAcción requerida inmediatamente.\n\nGracias.'
    'text'
);
```

## ⚙️ Configuración Detallada

### Canales de Notificación

#### Estructura de Configuración por Canal

**Email:**
```json
{
    "recipient_email": "admin@empresa.com",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_username": "notifications@empresa.com",
    "smtp_password": "app_password",
    "smtp_tls": true
}
```

**Slack:**
```json
{
    "webhook_url": "https://hooks.slack.com/services/...",
    "channel_id": "#alerts",
    "username": "MonitoringBot",
    "icon_emoji": ":warning:",
    "bot_token": "xoxb-optional-bot-token"
}
```

**SMS (Twilio):**
```json
{
    "provider": "twilio",
    "account_sid": "ACxxxxxxxxxxxxxxx",
    "auth_token": "your_auth_token",
    "from_number": "+1234567890",
    "phone_number": "+1987654321"
}
```

**Webhook:**
```json
{
    "webhook_url": "https://api.external.com/alerts",
    "method": "POST",
    "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer token"
    },
    "timeout_seconds": 10,
    "retry_count": 3
}
```

### Configuración de Horarios

```sql
-- Canal activo solo en horario laboral
UPDATE monitoring.notification_channels 
SET 
    active_hours_start = '08:00:00',
    active_hours_end = '18:00:00',
    active_days = ARRAY[1,2,3,4,5], -- Lunes a Viernes
    timezone = 'America/Mexico_City'
WHERE channel_name = 'business_hours_email';

-- Canal 24/7 para emergencias
UPDATE monitoring.notification_channels 
SET 
    active_hours_start = '00:00:00',
    active_hours_end = '23:59:59',
    active_days = ARRAY[1,2,3,4,5,6,7] -- Todos los días
WHERE channel_name = 'emergency_sms';
```

### Rate Limiting

```sql
-- Configurar límites por hora
UPDATE monitoring.notification_channels 
SET max_notifications_per_hour = 5  -- Máximo 5 SMS por hora
WHERE channel_type = 'sms';

UPDATE monitoring.notification_channels 
SET max_notifications_per_hour = 50 -- Máximo 50 emails por hora
WHERE channel_type = 'email';
```

## 📋 Variables de Plantillas

### Variables Disponibles

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `{{alert_id}}` | ID único de la alerta | uuid-1234-5678 |
| `{{title}}` | Título de la alerta | CPU usage critical |
| `{{description}}` | Descripción detallada | CPU usage has exceeded 95% |
| `{{severity}}` | Nivel de severidad | critical, warning, info |
| `{{metric_name}}` | Nombre de la métrica | cpu_usage_percent |
| `{{metric_value}}` | Valor actual | 96.5 |
| `{{threshold}}` | Umbral configurado | 90 |
| `{{timestamp}}` | Momento de la alerta | 2024-05-24 15:30:00 |
| `{{hours_active}}` | Horas que lleva activa | 2.5 |
| `{{database_name}}` | Nombre de la BD | maquina_noticias |
| `{{dashboard_url}}` | URL del dashboard | http://dashboard.local |
| `{{current_cpu}}` | CPU actual del sistema | 85.2 |
| `{{current_memory}}` | Memoria actual | 78.9 |
| `{{total_alerts}}` | Total de alertas activas | 3 |

### Ejemplo de Plantilla Completa

```sql
INSERT INTO monitoring.notification_templates (
    template_name, alert_type, severity, channel_type,
    subject_template, body_template, format_type
) VALUES (
    'plantilla_completa', 'system', 'critical', 'email',
    '[{{severity}}] {{title}} - {{database_name}}',
    '🚨 ALERTA DE SISTEMA 🚨

Hola equipo,

Se ha detectado una alerta en el sistema "{{database_name}}":

📊 INFORMACIÓN:
• Problema: {{title}}
• Descripción: {{description}}
• Métrica: {{metric_name}} = {{metric_value}}
• Umbral: {{threshold}}
• Tiempo activa: {{hours_active}} horas
• Severidad: {{severity}}

💻 ESTADO ACTUAL:
• CPU: {{current_cpu}}%
• Memoria: {{current_memory}}%
• Total alertas: {{total_alerts}}

🔗 ENLACES:
• Dashboard: {{dashboard_url}}
• Timestamp: {{timestamp}}

Saludos,
Sistema de Monitoreo Automático',
    'text'
);
```

## 🔄 Escalamiento Automático

### Configuración de Reglas

```sql
-- Regla de escalamiento personalizada
INSERT INTO monitoring.alert_escalation_rules (
    rule_name, description,
    alert_severity, alert_types,
    escalation_delay_minutes, max_escalation_level,
    level_1_channels, level_2_channels, level_3_channels,
    business_hours_only
) VALUES (
    'mi_escalamiento_custom',
    'Escalamiento para alertas críticas del módulo específico',
    ARRAY['critical'],
    ARRAY['system_health', 'threshold_breach'],
    15, -- Escalar cada 15 minutos
    3,
    -- Nivel 1: Equipo técnico
    ARRAY(SELECT id FROM monitoring.notification_channels WHERE channel_name IN ('dev_team_slack')),
    -- Nivel 2: Administradores
    ARRAY(SELECT id FROM monitoring.notification_channels WHERE channel_name IN ('admin_email', 'critical_slack')),
    -- Nivel 3: Emergencia
    ARRAY(SELECT id FROM monitoring.notification_channels WHERE channel_name IN ('emergency_sms')),
    FALSE -- Activo 24/7
);
```

### Niveles de Escalamiento

| Nivel | Tiempo | Destinatarios | Canales |
|-------|--------|---------------|---------|
| 1 | 0-30 min | Equipo de guardia | Slack, Email |
| 2 | 30-60 min | Administradores | Email, SMS |
| 3 | 60+ min | Gerencia/Emergencia | SMS, Llamada |

## 🔧 Funciones de Administración

### Enviar Notificación de Prueba

```sql
-- Probar canal de email
SELECT monitoring.send_test_notification(
    'admin_email', 
    'Mensaje de prueba del sistema'
);

-- Probar canal de Slack
SELECT monitoring.send_test_notification(
    'dev_team_slack',
    'Prueba de integración Slack funcionando ✅'
);
```

### Obtener Estadísticas

```sql
-- Estadísticas de los últimos 7 días
SELECT monitoring.get_notification_stats(7);

-- Ver historial de notificaciones
SELECT 
    nh.sent_at,
    nc.channel_name,
    nc.channel_type,
    a.title,
    a.severity,
    nh.status,
    nh.delivery_time_ms
FROM monitoring.notification_history nh
JOIN monitoring.notification_channels nc ON nh.channel_id = nc.id
LEFT JOIN monitoring.alerts a ON nh.alert_id = a.id
ORDER BY nh.sent_at DESC
LIMIT 50;
```

### Gestión de Canales

```sql
-- Deshabilitar temporalmente un canal
UPDATE monitoring.notification_channels 
SET enabled = FALSE 
WHERE channel_name = 'maintenance_channel';

-- Cambiar prioridad de canal
UPDATE monitoring.notification_channels 
SET priority = 1 -- Mayor prioridad
WHERE channel_name = 'critical_slack';

-- Ajustar rate limiting
UPDATE monitoring.notification_channels 
SET max_notifications_per_hour = 20
WHERE channel_type = 'email';
```

## 📊 Monitoreo del Sistema de Alertas

### Métricas Clave

```sql
-- Tasa de éxito de notificaciones
SELECT 
    nc.channel_type,
    COUNT(*) as total_sent,
    COUNT(*) FILTER (WHERE nh.status = 'sent') as successful,
    ROUND(COUNT(*) FILTER (WHERE nh.status = 'sent') * 100.0 / COUNT(*), 2) as success_rate_percent
FROM monitoring.notification_history nh
JOIN monitoring.notification_channels nc ON nh.channel_id = nc.id
WHERE nh.sent_at > NOW() - INTERVAL '7 days'
GROUP BY nc.channel_type;

-- Tiempo promedio de entrega
SELECT 
    nc.channel_type,
    ROUND(AVG(nh.delivery_time_ms)) as avg_delivery_ms,
    MAX(nh.delivery_time_ms) as max_delivery_ms
FROM monitoring.notification_history nh
JOIN monitoring.notification_channels nc ON nh.channel_id = nc.id
WHERE nh.sent_at > NOW() - INTERVAL '7 days'
AND nh.status = 'sent'
GROUP BY nc.channel_type;
```

### Alertas del Propio Sistema

```sql
-- Crear alerta para fallos en notificaciones
INSERT INTO monitoring.alert_thresholds (
    metric_name, display_name, description,
    warning_threshold, critical_threshold,
    notification_channels
) VALUES (
    'notification_failure_rate', 'Tasa de Fallo en Notificaciones',
    'Porcentaje de notificaciones que fallan al enviarse',
    10.0, 25.0, ARRAY['email']
);
```

## 🛠️ Integración con Proveedores Externos

### Configuración de SMTP

```python
# Ejemplo de configuración para diferentes proveedores
# Gmail
smtp_config = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_tls": True
}

# Outlook/Office 365
smtp_config = {
    "smtp_server": "smtp.office365.com", 
    "smtp_port": 587,
    "smtp_tls": True
}

# SendGrid
smtp_config = {
    "smtp_server": "smtp.sendgrid.net",
    "smtp_port": 587,
    "smtp_username": "apikey",
    "smtp_password": "SG.your_api_key_here"
}
```

### Webhooks de Slack

```bash
# Crear webhook en Slack:
# 1. Ir a https://api.slack.com/apps
# 2. Crear nueva app
# 3. Activar "Incoming Webhooks"
# 4. Crear webhook para el canal deseado
# 5. Copiar URL del webhook
```

### API de Twilio para SMS

```python
# Configuración de Twilio
twilio_config = {
    "account_sid": "ACxxxxxxxxxxxxxxx",
    "auth_token": "your_auth_token_here",
    "from_number": "+1234567890"  # Número de Twilio
}
```

## 🔍 Troubleshooting

### Problemas Comunes

#### 1. Notificaciones no se envían

**Diagnóstico:**
```sql
-- Verificar canales activos
SELECT channel_name, enabled, active_hours_start, active_hours_end
FROM monitoring.notification_channels
WHERE enabled = TRUE;

-- Verificar rate limiting
SELECT channel_name, current_hour_count, max_notifications_per_hour
FROM monitoring.notification_channels
WHERE current_hour_count >= max_notifications_per_hour;
```

**Solución:**
- Verificar configuración de horarios
- Revisar rate limiting
- Confirmar configuración de canales

#### 2. Notificaciones duplicadas

**Diagnóstico:**
```sql
-- Buscar notificaciones duplicadas
SELECT alert_id, COUNT(*), MIN(sent_at), MAX(sent_at)
FROM monitoring.notification_history
WHERE sent_at > NOW() - INTERVAL '1 hour'
GROUP BY alert_id
HAVING COUNT(*) > 1;
```

**Solución:**
- Verificar configuración anti-flood
- Revisar triggers automáticos
- Ajustar frecuencia de trabajos pg_cron

#### 3. Escalamiento no funciona

**Diagnóstico:**
```sql
-- Verificar reglas de escalamiento
SELECT rule_name, enabled, escalation_delay_minutes
FROM monitoring.alert_escalation_rules
WHERE enabled = TRUE;

-- Ver alertas candidatas para escalamiento
SELECT 
    a.id,
    a.title,
    a.severity,
    EXTRACT(epoch FROM (NOW() - a.timestamp)) / 60 as minutes_active
FROM monitoring.alerts a
WHERE a.status = 'active'
AND a.severity = 'critical';
```

### Comandos de Diagnóstico

```sql
-- Estado general del sistema de alertas
SELECT 
    'Canales activos' as metric,
    COUNT(*) as value
FROM monitoring.notification_channels
WHERE enabled = TRUE

UNION ALL

SELECT 
    'Plantillas disponibles',
    COUNT(*)
FROM monitoring.notification_templates
WHERE active = TRUE

UNION ALL

SELECT 
    'Reglas de escalamiento',
    COUNT(*)
FROM monitoring.alert_escalation_rules
WHERE enabled = TRUE

UNION ALL

SELECT 
    'Notificaciones última hora',
    COUNT(*)
FROM monitoring.notification_history
WHERE sent_at > NOW() - INTERVAL '1 hour';
```

## 🔐 Seguridad y Mejores Prácticas

### Configuración Segura

1. **Credenciales**:
   - Usar variables de entorno para passwords
   - Rotar tokens de API regularmente
   - Usar App Passwords para Gmail

2. **Rate Limiting**:
   - Configurar límites apropiados por canal
   - Monitorear costos de SMS
   - Implementar horarios de oficina

3. **Auditoría**:
   - Revisar logs regularmente
   - Monitorear tasas de entrega
   - Alertas sobre el propio sistema

### Recomendaciones

```sql
-- Configuración de seguridad recomendada
UPDATE monitoring.notification_channels 
SET max_notifications_per_hour = CASE 
    WHEN channel_type = 'sms' THEN 5
    WHEN channel_type = 'email' THEN 50
    WHEN channel_type = 'slack' THEN 30
    ELSE 100
END;

-- Habilitar auditoría adicional
INSERT INTO monitoring.notification_templates (
    template_name, alert_type, severity, channel_type,
    body_template
) VALUES (
    'security_audit', 'custom', 'info', 'email',
    'Reporte de seguridad: {{total_alerts}} alertas procesadas en las últimas 24h.'
);
```

## 📈 Métricas y Reportes

### Dashboard de Notificaciones

```sql
-- Crear vista para dashboard
CREATE VIEW monitoring.notifications_dashboard AS
SELECT 
    DATE(sent_at) as date,
    nc.channel_type,
    COUNT(*) as total_notifications,
    COUNT(*) FILTER (WHERE status = 'sent') as successful,
    COUNT(*) FILTER (WHERE status = 'failed') as failed,
    ROUND(AVG(delivery_time_ms)) as avg_delivery_time_ms
FROM monitoring.notification_history nh
JOIN monitoring.notification_channels nc ON nh.channel_id = nc.id
WHERE sent_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(sent_at), nc.channel_type
ORDER BY date DESC, nc.channel_type;
```

### Reporte Ejecutivo

```sql
-- Función para reporte semanal
CREATE OR REPLACE FUNCTION monitoring.weekly_notification_report()
RETURNS JSONB AS $$
DECLARE
    report JSONB;
BEGIN
    SELECT jsonb_build_object(
        'period', 'Last 7 days',
        'total_notifications', COUNT(*),
        'success_rate', ROUND(COUNT(*) FILTER (WHERE status = 'sent') * 100.0 / COUNT(*), 2),
        'avg_delivery_time_seconds', ROUND(AVG(delivery_time_ms) / 1000.0, 2),
        'cost_estimate_usd', ROUND(SUM(cost_estimate), 2),
        'by_channel', jsonb_object_agg(
            nc.channel_type,
            jsonb_build_object(
                'count', channel_counts.total,
                'success_rate', channel_counts.success_rate
            )
        )
    ) INTO report
    FROM monitoring.notification_history nh
    JOIN monitoring.notification_channels nc ON nh.channel_id = nc.id
    CROSS JOIN LATERAL (
        SELECT 
            COUNT(*) as total,
            ROUND(COUNT(*) FILTER (WHERE nh2.status = 'sent') * 100.0 / COUNT(*), 2) as success_rate
        FROM monitoring.notification_history nh2
        WHERE nh2.channel_id = nh.channel_id
        AND nh2.sent_at > NOW() - INTERVAL '7 days'
    ) channel_counts
    WHERE nh.sent_at > NOW() - INTERVAL '7 days';
    
    RETURN report;
END;
$$ LANGUAGE plpgsql;
```

---

**Sistema de Alertas Automáticas para "Máquina de Noticias"**  
*Documentación Técnica v1.0.0*

Para soporte técnico, consultar logs del sistema y funciones de diagnóstico incluidas.
