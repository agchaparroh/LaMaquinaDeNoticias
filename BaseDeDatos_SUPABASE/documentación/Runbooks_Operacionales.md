# Runbooks Operacionales - Sistema de Monitoreo
## Máquina de Noticias

**Versión:** 1.0  
**Fecha:** Mayo 2024  
**Audiencia:** Equipo de Operaciones, SRE, Administradores de Base de Datos

---

## 🚨 RESPUESTA A INCIDENTES

### ESCALAS DE SEVERIDAD

#### 🔴 CRÍTICO (P0)
- **Definición**: Sistema de base de datos inaccesible o corrupción de datos
- **Tiempo de Respuesta**: 5 minutos
- **Escalación**: Inmediata a equipo de arquitectura

#### 🟠 ALTO (P1) 
- **Definición**: Rendimiento severamente degradado, múltiples alertas críticas
- **Tiempo de Respuesta**: 15 minutos
- **Escalación**: A supervisor técnico en 30 minutos

#### 🟡 MEDIO (P2)
- **Definición**: Alertas de warning, rendimiento degradado parcialmente
- **Tiempo de Respuesta**: 1 hora
- **Escalación**: A supervisor en 4 horas si no se resuelve

#### 🟢 BAJO (P3)
- **Definición**: Problemas menores, alertas informativas
- **Tiempo de Respuesta**: 4 horas
- **Escalación**: Revisión en próxima reunión de equipo

---

## 📋 RUNBOOK: SISTEMA INACCESIBLE

### SÍNTOMAS
- Dashboard no responde
- Alertas de conexión de base de datos
- Error 500 en endpoints de monitoreo

### INVESTIGACIÓN INICIAL (5 minutos)

```sql
-- 1. Verificar estado de conexión básica
SELECT NOW();

-- 2. Verificar procesos activos
SELECT COUNT(*) FROM pg_stat_activity;

-- 3. Verificar último registro de métricas
SELECT MAX(timestamp) FROM monitoring.system_metrics;
```

### ACCIONES INMEDIATAS

1. **Verificar Supabase Dashboard**
   - Acceder al panel de Supabase
   - Revisar estado de servicios
   - Verificar límites del plan

2. **Verificar Trabajos pg_cron**
   ```sql
   SELECT * FROM cron.job WHERE active = true;
   SELECT * FROM cron.job_run_details ORDER BY start_time DESC LIMIT 10;
   ```

3. **Verificar Espacio en Disco**
   ```sql
   SELECT monitoring.get_operational_status()->'metrics'->>'database_size_mb';
   ```

### ESCALACIÓN
- Si no se resuelve en 15 minutos: Contactar Arquitecto de Datos
- Si es problema de Supabase: Abrir ticket de soporte urgente

---

## 📋 RUNBOOK: ALERTAS CRÍTICAS MÚLTIPLES

### SÍNTOMAS
- 5+ alertas críticas activas simultáneamente
- Score de salud del sistema < 6.0
- Notificaciones de escalación activadas

### INVESTIGACIÓN (10 minutos)

```sql
-- 1. Ver alertas críticas activas
SELECT * FROM monitoring.alerts_dashboard_enhanced 
WHERE severity = 'critical' 
ORDER BY timestamp DESC;

-- 2. Verificar métricas actuales
SELECT monitoring.get_operational_status();

-- 3. Revisar trabajos fallidos
SELECT * FROM monitoring.collection_jobs 
WHERE status = 'failed' AND started_at > NOW() - INTERVAL '1 hour';
```

### ANÁLISIS POR TIPO DE ALERTA

#### CPU > 90%
```sql
-- Identificar consultas consumiendo CPU
SELECT query, calls, total_exec_time, mean_exec_time
FROM pg_stat_statements 
ORDER BY total_exec_time DESC LIMIT 10;
```

**Acciones:**
1. Identificar consultas lentas y optimizar
2. Considerar escalado vertical si es sostenido
3. Revisar procesos externos consumiendo recursos

#### Memoria > 95%
```sql
-- Verificar configuración de memoria
SELECT name, setting, unit, context 
FROM pg_settings 
WHERE name LIKE '%memory%' OR name LIKE '%buffer%';
```

**Acciones:**
1. Reiniciar conexiones idle si es necesario
2. Ajustar shared_buffers si es apropiado
3. Revisar consultas con uso excesivo de memoria

#### Conexiones > 95%
```sql
-- Ver conexiones activas por estado
SELECT state, COUNT(*) 
FROM pg_stat_activity 
GROUP BY state;
```

**Acciones:**
1. Cerrar conexiones idle_in_transaction antiguas
2. Verificar pool de conexiones de aplicación
3. Aumentar max_connections si es necesario

---

## 📋 RUNBOOK: FALLO DE SISTEMA DE ALERTAS

### SÍNTOMAS
- No se reciben alertas esperadas
- Dashboard muestra datos obsoletos
- Trabajos de recolección fallando

### INVESTIGACIÓN

```sql
-- 1. Verificar último trabajo exitoso
SELECT * FROM monitoring.collection_jobs 
WHERE status = 'completed' 
ORDER BY started_at DESC LIMIT 1;

-- 2. Verificar trabajos pg_cron
SELECT jobname, schedule, active, database 
FROM cron.job 
WHERE command LIKE '%monitoring%';

-- 3. Verificar configuración de alertas
SELECT COUNT(*) FROM monitoring.alert_thresholds WHERE enabled = true;
```

### ACCIONES DE RECUPERACIÓN

1. **Reiniciar Sistema de Monitoreo**
   ```sql
   -- Ejecutar recolección manual
   SELECT monitoring.collect_system_metrics();
   
   -- Verificar alertas manual
   SELECT monitoring.check_alert_thresholds_enhanced();
   ```

2. **Verificar Configuración**
   ```sql
   -- Verificar umbrales
   SELECT * FROM monitoring.alert_thresholds WHERE enabled = false;
   
   -- Verificar canales de notificación
   SELECT * FROM monitoring.notification_config WHERE enabled = false;
   ```

3. **Reactivar Trabajos**
   ```sql
   -- Si los trabajos están deshabilitados, reactivar
   SELECT cron.schedule('collect-system-metrics', '*/5 * * * *', 'SELECT monitoring.collect_system_metrics();');
   ```

---

## 📋 RUNBOOK: RENDIMIENTO DEGRADADO

### SÍNTOMAS
- Tiempo de respuesta > 5 segundos
- Cache hit ratio < 80%
- Consultas lentas > 50 por hora

### INVESTIGACIÓN DE RENDIMIENTO

```sql
-- 1. Análisis de consultas lentas
SELECT * FROM monitoring.get_slow_queries(1000, 20);

-- 2. Análisis de cache
SELECT 
    schemaname, tablename, 
    heap_blks_read, heap_blks_hit,
    ROUND(100.0 * heap_blks_hit / (heap_blks_hit + heap_blks_read), 2) as hit_ratio
FROM pg_statio_user_tables 
WHERE heap_blks_read > 0
ORDER BY hit_ratio ASC;

-- 3. Análisis de I/O
SELECT 
    schemaname, tablename,
    seq_scan, seq_tup_read, idx_scan, idx_tup_fetch
FROM pg_stat_user_tables
ORDER BY seq_tup_read DESC;
```

### OPTIMIZACIONES INMEDIATAS

1. **Ajustar Configuración de Memoria**
   ```sql
   -- Verificar configuración actual
   SELECT name, setting FROM pg_settings 
   WHERE name IN ('shared_buffers', 'effective_cache_size', 'work_mem');
   ```

2. **Analizar Índices Faltantes**
   ```sql
   -- Ver scans secuenciales más costosos
   SELECT schemaname, tablename, seq_scan, seq_tup_read
   FROM pg_stat_user_tables
   WHERE seq_scan > 100
   ORDER BY seq_tup_read DESC;
   ```

3. **Refresh de Vistas Materializadas**
   ```sql
   -- Refrescar vistas críticas manualmente
   REFRESH MATERIALIZED VIEW CONCURRENTLY agenda_eventos_proximos;
   REFRESH MATERIALIZED VIEW CONCURRENTLY resumen_hilos_activos;
   ```

---

## 📋 RUNBOOK: PROBLEMAS DE NOTIFICACIONES

### SÍNTOMAS
- Alertas no se envían por email/Slack
- Tasa de éxito de notificaciones < 80%
- Usuarios reportan no recibir alertas

### INVESTIGACIÓN

```sql
-- 1. Verificar historial de notificaciones
SELECT 
    channel_type, 
    status, 
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'sent') / COUNT(*), 2) as success_rate
FROM monitoring.notification_history 
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY channel_type, status
ORDER BY channel_type, status;

-- 2. Verificar configuración de canales
SELECT channel_type, channel_name, enabled, config
FROM monitoring.notification_config;

-- 3. Ver errores recientes
SELECT channel_type, error_message, COUNT(*)
FROM monitoring.notification_history 
WHERE status = 'failed' AND timestamp > NOW() - INTERVAL '6 hours'
GROUP BY channel_type, error_message;
```

### SOLUCIONES POR CANAL

#### Email
1. Verificar configuración SMTP
2. Probar conectividad al servidor de correo
3. Verificar credenciales y autenticación

#### Slack
1. Verificar webhook URL válida
2. Probar webhook manualmente
3. Verificar permisos del bot de Slack

#### SMS
1. Verificar API key del proveedor
2. Verificar formato de números telefónicos
3. Verificar créditos/límites del servicio

---

## 📋 PROCEDIMIENTOS DE MANTENIMIENTO RUTINARIO

### DIARIO (Automático - 2:00 AM)

✅ **Ejecutado por**: `monitoring.daily_maintenance()`

- Limpieza de métricas > 30 días
- Limpieza de alertas resueltas > 90 días  
- Generación de reporte diario
- Reset de contadores de notificaciones
- Verificación de salud del sistema

### SEMANAL (Manual - Lunes 9:00 AM)

```sql
-- 1. Análisis de alertas recurrentes
SELECT metric_name, COUNT(*) as alert_count
FROM monitoring.alerts 
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY metric_name
ORDER BY alert_count DESC;

-- 2. Revisión de umbrales
SELECT metric_name, warning_threshold, critical_threshold,
       (SELECT AVG(
           CASE metric_name 
               WHEN 'cpu_usage_percent' THEN cpu_usage_percent
               WHEN 'memory_usage_percent' THEN memory_usage_percent
               -- ... otros casos
           END
       ) FROM monitoring.system_metrics 
       WHERE timestamp > NOW() - INTERVAL '7 days') as avg_value
FROM monitoring.alert_thresholds;

-- 3. Verificación de trabajos pg_cron
SELECT jobname, last_run_time, next_run_time
FROM cron.job_run_details
WHERE job_name LIKE '%monitoring%'
ORDER BY last_run_time DESC;
```

### MENSUAL (Manual - Primer viernes del mes)

1. **Análisis de Tendencias**
   ```sql
   -- Ejecutar análisis de rendimiento histórico
   SELECT monitoring.generate_testing_report();
   ```

2. **Optimización de Umbrales**
   - Revisar alertas falsas positivas
   - Ajustar umbrales según datos históricos
   - Actualizar configuración según crecimiento

3. **Backup de Configuraciones**
   ```sql
   -- Exportar configuraciones críticas
   COPY (SELECT * FROM monitoring.alert_thresholds) TO '/backup/alert_thresholds.csv' CSV HEADER;
   COPY (SELECT * FROM monitoring.notification_config) TO '/backup/notification_config.csv' CSV HEADER;
   ```

---

## 🔧 COMANDOS DE EMERGENCIA

### DESHABILITAR TODAS LAS ALERTAS
```sql
-- ⚠️ USAR SOLO EN EMERGENCIAS
UPDATE monitoring.alert_thresholds SET enabled = false;
UPDATE monitoring.notification_config SET enabled = false;
```

### REACTIVAR SISTEMA COMPLETO
```sql
-- Reactivar umbrales
UPDATE monitoring.alert_thresholds SET enabled = true;

-- Reactivar notificaciones críticas
UPDATE monitoring.notification_config SET enabled = true 
WHERE severity_filter && ARRAY['critical'];

-- Forzar recolección de métricas
SELECT monitoring.collect_system_metrics();
```

### VERIFICACIÓN RÁPIDA DE ESTADO
```sql
-- Estado completo en una consulta
SELECT monitoring.get_operational_status();
```

### RESET COMPLETO DE FLOOD CONTROL
```sql
-- En caso de bloqueo masivo de alertas
DELETE FROM monitoring.alert_flood_control;
```

---

## 📞 CONTACTOS Y ESCALACIÓN

### EQUIPO PRIMARIO
- **Administrador DB**: [admin-db@empresa.com](mailto:admin-db@empresa.com) / +XX-XXXX-XXXX
- **DevOps Lead**: [devops@empresa.com](mailto:devops@empresa.com) / +XX-XXXX-XXXX
- **Arquitecto Datos**: [architect@empresa.com](mailto:architect@empresa.com) / +XX-XXXX-XXXX

### ESCALACIÓN EXTERNA
- **Supabase Support**: [support.supabase.com](https://support.supabase.com) (Incidentes P0/P1)
- **Proveedor Hosting**: [Información de contacto]

### CANALES DE COMUNICACIÓN
- **Slack**: `#alertas-criticas` (alertas automáticas)
- **Slack**: `#ops-database` (coordinación de equipo)
- **Email**: `ops-team@empresa.com` (comunicaciones oficiales)

---

**📝 Nota**: Este runbook debe revisarse mensualmente y actualizarse según la evolución del sistema y los patrones de incidentes observados.

---

*Documento parte del Sistema de Monitoreo - Máquina de Noticias v1.0*
