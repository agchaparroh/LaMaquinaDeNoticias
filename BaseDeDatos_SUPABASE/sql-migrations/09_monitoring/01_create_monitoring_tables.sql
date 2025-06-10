-- =====================================================
-- SISTEMA DE MONITOREO - TABLAS BASE
-- Archivo: 01_create_monitoring_tables.sql
-- Descripción: Crear tablas para almacenar métricas del sistema
-- =====================================================

-- Crear esquema específico para monitoreo si no existe
CREATE SCHEMA IF NOT EXISTS monitoring;

-- =====================================================
-- TABLA PRINCIPAL DE MÉTRICAS DEL SISTEMA
-- =====================================================

CREATE TABLE IF NOT EXISTS monitoring.system_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Métricas de CPU y Sistema
    cpu_usage_percent DECIMAL(5,2),
    load_average_1m DECIMAL(10,2),
    load_average_5m DECIMAL(10,2),
    load_average_15m DECIMAL(10,2),
    
    -- Métricas de Memoria
    memory_total_mb BIGINT,
    memory_used_mb BIGINT,
    memory_free_mb BIGINT,
    memory_usage_percent DECIMAL(5,2),
    
    -- Métricas de Almacenamiento
    storage_total_mb BIGINT,
    storage_used_mb BIGINT,
    storage_free_mb BIGINT,
    storage_usage_percent DECIMAL(5,2),
    
    -- Métricas de Conexiones de BD
    total_connections INTEGER,
    active_connections INTEGER,
    idle_connections INTEGER,
    max_connections INTEGER,
    connection_usage_percent DECIMAL(5,2),
    
    -- Métricas de I/O de Base de Datos
    total_reads BIGINT,
    total_writes BIGINT,
    reads_per_second DECIMAL(10,2),
    writes_per_second DECIMAL(10,2),
    
    -- Métricas de Transacciones
    transactions_committed BIGINT,
    transactions_rolled_back BIGINT,
    transactions_per_second DECIMAL(10,2),
    
    -- Métricas de Cache y Buffer
    cache_hit_ratio DECIMAL(5,2),
    buffer_cache_hit_ratio DECIMAL(5,2),
    
    -- Métricas de Locks y Deadlocks
    current_locks INTEGER,
    deadlocks_total INTEGER,
    
    -- Consultas Lentas
    slow_queries_count INTEGER,
    avg_query_time_ms DECIMAL(10,2),
    
    -- Información adicional
    database_size_mb BIGINT,
    replication_lag_ms DECIMAL(10,2),
    
    -- Metadatos
    collection_time_ms INTEGER,
    collector_version TEXT DEFAULT '1.0.0',
    
    CONSTRAINT valid_percentages CHECK (
        cpu_usage_percent BETWEEN 0 AND 100 AND
        memory_usage_percent BETWEEN 0 AND 100 AND
        storage_usage_percent BETWEEN 0 AND 100 AND
        connection_usage_percent BETWEEN 0 AND 100 AND
        cache_hit_ratio BETWEEN 0 AND 100 AND
        buffer_cache_hit_ratio BETWEEN 0 AND 100
    )
);

-- Crear particionado por fecha para optimizar rendimiento
CREATE TABLE IF NOT EXISTS monitoring.system_metrics_y2024m01 
PARTITION OF monitoring.system_metrics 
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE IF NOT EXISTS monitoring.system_metrics_y2024m02 
PARTITION OF monitoring.system_metrics 
FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

CREATE TABLE IF NOT EXISTS monitoring.system_metrics_y2024m03 
PARTITION OF monitoring.system_metrics 
FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');

CREATE TABLE IF NOT EXISTS monitoring.system_metrics_y2024m04 
PARTITION OF monitoring.system_metrics 
FOR VALUES FROM ('2024-04-01') TO ('2024-05-01');

CREATE TABLE IF NOT EXISTS monitoring.system_metrics_y2024m05 
PARTITION OF monitoring.system_metrics 
FOR VALUES FROM ('2024-05-01') TO ('2024-06-01');

CREATE TABLE IF NOT EXISTS monitoring.system_metrics_y2024m06 
PARTITION OF monitoring.system_metrics 
FOR VALUES FROM ('2024-06-01') TO ('2024-07-01');

-- =====================================================
-- TABLA DE ALERTAS GENERADAS
-- =====================================================

CREATE TABLE IF NOT EXISTS monitoring.alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Información de la alerta
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('info', 'warning', 'critical')),
    metric_name TEXT NOT NULL,
    metric_value DECIMAL(15,2),
    threshold_value DECIMAL(15,2),
    
    -- Detalles
    title TEXT NOT NULL,
    description TEXT,
    source_table TEXT,
    source_query TEXT,
    
    -- Estado de la alerta
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'resolved', 'suppressed')),
    resolved_at TIMESTAMPTZ,
    resolved_by TEXT,
    
    -- Información de notificación
    notification_sent BOOLEAN DEFAULT FALSE,
    notification_channels TEXT[], -- ['email', 'slack', 'sms']
    notification_sent_at TIMESTAMPTZ,
    
    -- Metadatos
    created_by TEXT DEFAULT 'system',
    tags JSONB DEFAULT '{}'::jsonb
);

-- =====================================================
-- TABLA DE CONFIGURACIÓN DE UMBRALES
-- =====================================================

CREATE TABLE IF NOT EXISTS monitoring.alert_thresholds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Identificación del umbral
    metric_name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    description TEXT,
    
    -- Umbrales
    warning_threshold DECIMAL(15,2),
    critical_threshold DECIMAL(15,2),
    
    -- Configuración
    enabled BOOLEAN DEFAULT TRUE,
    check_frequency_minutes INTEGER DEFAULT 5,
    notification_channels TEXT[] DEFAULT ARRAY['email'],
    
    -- Opciones avanzadas
    require_consecutive_breaches INTEGER DEFAULT 1,
    auto_resolve BOOLEAN DEFAULT TRUE,
    auto_resolve_after_minutes INTEGER DEFAULT 60,
    
    -- Metadatos
    category TEXT DEFAULT 'system',
    tags JSONB DEFAULT '{}'::jsonb
);

-- =====================================================
-- TABLA DE HISTORIAL DE TRABAJOS DE MONITOREO
-- =====================================================

CREATE TABLE IF NOT EXISTS monitoring.collection_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    
    -- Información del trabajo
    job_type TEXT NOT NULL, -- 'system_metrics', 'supabase_metrics', 'custom'
    status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed')),
    
    -- Resultados
    metrics_collected INTEGER DEFAULT 0,
    alerts_generated INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    
    -- Rendimiento
    execution_time_ms INTEGER,
    memory_used_mb DECIMAL(10,2),
    
    -- Errores
    error_message TEXT,
    error_details JSONB,
    
    -- Metadatos
    collector_version TEXT DEFAULT '1.0.0',
    configuration_hash TEXT
);

-- =====================================================
-- ÍNDICES PARA OPTIMIZACIÓN
-- =====================================================

-- Índices para system_metrics
CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON monitoring.system_metrics (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_system_metrics_cpu_usage ON monitoring.system_metrics (cpu_usage_percent) WHERE cpu_usage_percent > 80;
CREATE INDEX IF NOT EXISTS idx_system_metrics_memory_usage ON monitoring.system_metrics (memory_usage_percent) WHERE memory_usage_percent > 80;
CREATE INDEX IF NOT EXISTS idx_system_metrics_connections ON monitoring.system_metrics (connection_usage_percent) WHERE connection_usage_percent > 80;

-- Índices para alerts
CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON monitoring.alerts (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON monitoring.alerts (status);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON monitoring.alerts (severity);
CREATE INDEX IF NOT EXISTS idx_alerts_metric_name ON monitoring.alerts (metric_name);

-- Índices para alert_thresholds
CREATE INDEX IF NOT EXISTS idx_alert_thresholds_enabled ON monitoring.alert_thresholds (enabled) WHERE enabled = TRUE;
CREATE INDEX IF NOT EXISTS idx_alert_thresholds_category ON monitoring.alert_thresholds (category);

-- Índices para collection_jobs
CREATE INDEX IF NOT EXISTS idx_collection_jobs_started_at ON monitoring.collection_jobs (started_at DESC);
CREATE INDEX IF NOT EXISTS idx_collection_jobs_status ON monitoring.collection_jobs (status);
CREATE INDEX IF NOT EXISTS idx_collection_jobs_type ON monitoring.collection_jobs (job_type);

-- =====================================================
-- TRIGGERS PARA AUDITORÍA
-- =====================================================

-- Función para actualizar timestamp de updated_at
CREATE OR REPLACE FUNCTION monitoring.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para alert_thresholds
CREATE TRIGGER trigger_alert_thresholds_updated_at
    BEFORE UPDATE ON monitoring.alert_thresholds
    FOR EACH ROW
    EXECUTE FUNCTION monitoring.update_updated_at_column();

-- =====================================================
-- CONFIGURACIONES INICIALES
-- =====================================================

-- Insertar umbrales por defecto
INSERT INTO monitoring.alert_thresholds (
    metric_name, display_name, description, 
    warning_threshold, critical_threshold, 
    category, notification_channels
) VALUES 
    ('cpu_usage_percent', 'Uso de CPU', 'Porcentaje de uso de CPU', 75.0, 90.0, 'system', ARRAY['email']),
    ('memory_usage_percent', 'Uso de Memoria', 'Porcentaje de uso de memoria', 80.0, 95.0, 'system', ARRAY['email']),
    ('storage_usage_percent', 'Uso de Almacenamiento', 'Porcentaje de uso de disco', 85.0, 95.0, 'system', ARRAY['email', 'slack']),
    ('connection_usage_percent', 'Uso de Conexiones', 'Porcentaje de conexiones utilizadas', 80.0, 95.0, 'database', ARRAY['email']),
    ('cache_hit_ratio', 'Ratio de Cache Hit', 'Porcentaje de aciertos en cache (alerta cuando es BAJO)', 90.0, 80.0, 'database', ARRAY['email']),
    ('avg_query_time_ms', 'Tiempo Promedio de Consultas', 'Tiempo promedio de ejecución de consultas en ms', 1000.0, 5000.0, 'database', ARRAY['email']),
    ('slow_queries_count', 'Consultas Lentas', 'Número de consultas lentas por período', 10.0, 50.0, 'database', ARRAY['email']),
    ('deadlocks_total', 'Deadlocks Totales', 'Número total de deadlocks', 1.0, 5.0, 'database', ARRAY['email'])
ON CONFLICT (metric_name) DO NOTHING;

-- Comentarios para documentación
COMMENT ON SCHEMA monitoring IS 'Esquema dedicado para el sistema de monitoreo de la base de datos';
COMMENT ON TABLE monitoring.system_metrics IS 'Tabla principal que almacena métricas del sistema recolectadas cada 5 minutos';
COMMENT ON TABLE monitoring.alerts IS 'Registro de todas las alertas generadas por el sistema de monitoreo';
COMMENT ON TABLE monitoring.alert_thresholds IS 'Configuración de umbrales para generar alertas automáticas';
COMMENT ON TABLE monitoring.collection_jobs IS 'Historial de trabajos de recolección de métricas para auditoría';

-- Verificación final
DO $$
BEGIN
    RAISE NOTICE 'Sistema de tablas de monitoreo creado exitosamente';
    RAISE NOTICE 'Esquema: monitoring';
    RAISE NOTICE 'Tablas creadas: system_metrics, alerts, alert_thresholds, collection_jobs';
    RAISE NOTICE 'Particiones creadas: 6 meses para system_metrics';
    RAISE NOTICE 'Umbrales por defecto: 8 métricas configuradas';
END $$;
