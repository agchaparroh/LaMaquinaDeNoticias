# Dashboard de Monitoreo - Guía de Instalación y Configuración

## 📊 Descripción General

Este dashboard visual en tiempo real proporciona una vista completa del estado del sistema "Máquina de Noticias", incluyendo:

- **Métricas del Sistema**: CPU, memoria, almacenamiento, conexiones
- **Estado de Supabase**: Límites del plan, Edge Functions, API usage
- **Infraestructura**: Vistas materializadas, jobs pg_cron
- **Alertas en Tiempo Real**: Notificaciones priorizadas por severidad
- **Gráficos de Tendencias**: Datos históricos de las últimas 24 horas

## 🚀 Instalación Rápida

### 1. Instalar Scripts SQL

Ejecutar en orden los siguientes scripts en la base de datos:

```bash
# Scripts base del sistema de monitoreo (si no están instalados)
psql -f 01_create_monitoring_tables.sql
psql -f 02_monitoring_collection_functions.sql
psql -f 03_setup_monitoring_automation.sql

# Scripts específicos del dashboard
psql -f 09_dashboard_api_functions.sql
psql -f 10_dashboard_endpoint_configuration.sql
```

### 2. Configurar Supabase

#### A. Crear Usuario para Dashboard

```sql
-- En Supabase Dashboard, ejecutar:
CREATE USER dashboard_app WITH PASSWORD 'tu_password_seguro';
GRANT dashboard_reader TO dashboard_app;
```

#### B. Configurar Row Level Security (Opcional)

```sql
-- Habilitar RLS en tablas de monitoreo si es necesario
ALTER TABLE monitoring.system_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE monitoring.alerts ENABLE ROW LEVEL SECURITY;

-- Política para permitir lectura del dashboard
CREATE POLICY "Dashboard can read metrics" ON monitoring.system_metrics
FOR SELECT TO dashboard_reader USING (true);

CREATE POLICY "Dashboard can read alerts" ON monitoring.alerts
FOR SELECT TO dashboard_reader USING (true);
```

### 3. Configurar Dashboard HTML

#### A. Actualizar URLs de API

En el archivo `dashboard.html`, modificar la configuración:

```javascript
// Reemplazar esta línea:
const API_BASE_URL = '/rest/v1/rpc/';

// Por tu URL real de Supabase:
const API_BASE_URL = 'https://tu-proyecto.supabase.co/rest/v1/rpc/';
const SUPABASE_KEY = 'tu_anon_key_aqui';
```

#### B. Configurar Autenticación

```javascript
// Agregar headers de autenticación
const headers = {
    'Content-Type': 'application/json',
    'apikey': SUPABASE_KEY,
    'Authorization': `Bearer ${SUPABASE_KEY}`
};
```

### 4. Implementar Llamadas Reales a la API

Reemplazar la función `generateMockData()` con llamadas reales:

```javascript
async function fetchDashboardData() {
    if (isLoading) return;
    
    isLoading = true;
    
    try {
        const response = await fetch(`${API_BASE_URL}get_complete_dashboard_data`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({})
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        updateDashboard(data);
        
    } catch (error) {
        console.error('Error fetching dashboard data:', error);
        showError('Error al obtener datos del servidor: ' + error.message);
    } finally {
        isLoading = false;
    }
}
```

## 📡 Endpoints Disponibles

### Endpoints Principales

| Endpoint | Descripción | Uso Recomendado |
|----------|-------------|-----------------|
| `get_complete_dashboard_data` | Datos completos del dashboard | Dashboard principal |
| `get_system_metrics_only` | Solo métricas del sistema | Widgets específicos |
| `get_critical_alerts_only` | Solo alertas críticas | Notificaciones |
| `get_health_status_simple` | Estado de salud simple | APIs externas |

### Endpoints de Gráficos

| Endpoint | Descripción | Parámetros |
|----------|-------------|------------|
| `get_resource_usage_chart_data` | Datos para gráfico de recursos | `hours_back`, `interval_minutes` |
| `get_alerts_trend_chart_data` | Datos para gráfico de alertas | `days_back` |

### Ejemplo de Llamadas

```javascript
// Obtener datos completos
const mainData = await fetch(`${API_BASE_URL}get_complete_dashboard_data`, {
    method: 'POST',
    headers: headers
});

// Obtener solo alertas críticas
const alerts = await fetch(`${API_BASE_URL}get_critical_alerts_only`, {
    method: 'POST',
    headers: headers
});

// Obtener datos de gráfico (últimas 24 horas)
const chartData = await fetch(`${API_BASE_URL}get_resource_usage_chart_data`, {
    method: 'POST',
    headers: headers,
    body: JSON.stringify({ hours_back: 24, interval_minutes: 60 })
});
```

## ⚙️ Configuración Avanzada

### 1. Configurar Rate Limiting

El sistema incluye rate limiting automático. Para ajustar los límites:

```sql
-- Cambiar límite por hora (por defecto: 1000 requests/hora)
SELECT monitoring.check_rate_limit(
    '192.168.1.100'::inet, 
    'get_complete_dashboard_data', 
    2000  -- Nuevo límite
);
```

### 2. Configurar Logs de Acceso

Los logs se almacenan automáticamente. Para consultar:

```sql
-- Ver accesos recientes al dashboard
SELECT 
    timestamp,
    client_ip,
    endpoint_called,
    response_time_ms,
    status_code
FROM monitoring.dashboard_access_logs 
ORDER BY timestamp DESC 
LIMIT 100;
```

### 3. Personalizar Alertas del Dashboard

```sql
-- Agregar nueva configuración de alerta
INSERT INTO monitoring.alert_thresholds (
    metric_name, display_name, description,
    warning_threshold, critical_threshold,
    notification_channels
) VALUES (
    'dashboard_response_time', 'Tiempo de Respuesta Dashboard', 
    'Tiempo de respuesta del dashboard en ms',
    1000.0, 3000.0, ARRAY['email']
);
```

## 🎨 Personalización Visual

### Colores y Temas

En el CSS del dashboard, modificar las variables de color:

```css
:root {
    --primary-gradient: linear-gradient(135deg, #1e3c72, #2a5298);
    --card-background: rgba(255, 255, 255, 0.1);
    --healthy-color: #4CAF50;
    --warning-color: #FF9800;
    --critical-color: #f44336;
}
```

### Intervalos de Actualización

```javascript
// Cambiar frecuencia de actualización
const REFRESH_INTERVAL = 15000; // 15 segundos en lugar de 30
```

### Métricas Personalizadas

Agregar nuevos widgets modificando la función `updateDashboard()`:

```javascript
// Agregar nueva métrica personalizada
if (data.custom_metrics) {
    document.getElementById('customMetric').textContent = 
        data.custom_metrics.value;
}
```

## 🔧 Troubleshooting

### Errores Comunes

#### 1. Error de CORS
```
Solución: Configurar CORS en Supabase
- Ir a Settings > API
- Agregar tu dominio en "CORS origins"
```

#### 2. Error 401 Unauthorized
```
Solución: Verificar API key y permisos
- Verificar que SUPABASE_KEY sea correcta
- Confirmar que el usuario tiene rol dashboard_reader
```

#### 3. No se muestran datos
```
Solución: Verificar que el sistema de monitoreo esté funcionando
- Ejecutar: SELECT monitoring.collect_system_metrics();
- Verificar: SELECT * FROM monitoring.system_metrics ORDER BY timestamp DESC LIMIT 1;
```

#### 4. Gráficos no se actualizan
```
Solución: Verificar Chart.js
- Verificar que Chart.js se carga desde CDN
- Comprobar errores en consola del navegador
```

### Comandos de Diagnóstico

```sql
-- Verificar estado del sistema de monitoreo
SELECT monitoring.get_health_status_simple();

-- Verificar trabajos pg_cron
SELECT * FROM monitoring.get_cron_jobs_status();

-- Verificar últimas métricas recolectadas
SELECT 
    job_type,
    status,
    completed_at,
    metrics_collected,
    errors_count
FROM monitoring.collection_jobs 
ORDER BY started_at DESC 
LIMIT 10;
```

## 📊 Métricas y Rendimiento

### Métricas del Dashboard

El sistema rastrea automáticamente:
- Tiempo de respuesta de endpoints
- Número de requests por cliente
- Errores y excepciones
- Uso de recursos durante consultas

### Optimización

Para mejor rendimiento:

1. **Configurar índices específicos**:
```sql
-- Índice para consultas del dashboard
CREATE INDEX CONCURRENTLY idx_system_metrics_dashboard 
ON monitoring.system_metrics (timestamp DESC) 
WHERE timestamp > NOW() - INTERVAL '24 hours';
```

2. **Configurar limpieza automática**:
```sql
-- Ejecutar limpieza diaria
SELECT cron.schedule(
    'dashboard-optimization',
    '0 2 * * *',
    'SELECT monitoring.cleanup_dashboard_cache();'
);
```

## 🔐 Seguridad

### Recomendaciones de Seguridad

1. **Usar HTTPS**: Siempre servir el dashboard sobre HTTPS
2. **Autenticación**: Implementar autenticación de usuarios
3. **Rate Limiting**: Configurado automáticamente
4. **Logs de Auditoría**: Habilitados por defecto
5. **Principio de Menor Privilegio**: El rol `dashboard_reader` tiene permisos mínimos

### Configuración de Producción

```sql
-- Revocar permisos innecesarios
REVOKE ALL ON monitoring.collection_jobs FROM dashboard_reader;
GRANT SELECT ON monitoring.collection_jobs TO dashboard_reader;

-- Habilitar auditoría adicional
ALTER TABLE monitoring.dashboard_access_logs 
ADD COLUMN session_id TEXT,
ADD COLUMN authenticated_user TEXT;
```

## 📈 Monitoreo del Dashboard

El propio dashboard es monitoreado:

```sql
-- Ver uso del dashboard
SELECT 
    DATE(timestamp) as date,
    COUNT(*) as total_requests,
    COUNT(DISTINCT client_ip) as unique_users,
    AVG(response_time_ms) as avg_response_time
FROM monitoring.dashboard_access_logs 
GROUP BY DATE(timestamp) 
ORDER BY date DESC;
```

## 🆘 Soporte

Para problemas o preguntas:

1. **Verificar logs**: Revisar `monitoring.dashboard_access_logs`
2. **Estado del sistema**: Ejecutar `get_health_status_simple()`
3. **Documentación técnica**: Consultar comentarios en funciones SQL
4. **Regenerar datos**: Ejecutar manualmente `collect_all_metrics()`

---

**Dashboard creado para el Sistema de Monitoreo "Máquina de Noticias"**  
*Versión 1.0.0 - Dashboard en Tiempo Real*
