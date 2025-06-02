-- 014_indices_vectoriales_iniciales.sql
-- Configuración inicial de índices vectoriales pgvector
-- Implementado el 24 de Mayo de 2025
-- Tarea 14: Configurar Índices Vectoriales Iniciales

-- ============================================================================
-- CONFIGURACIÓN INICIAL DE ÍNDICES VECTORIALES IVFFLAT
-- ============================================================================

-- Parámetros de configuración:
-- - Algoritmo: IVFFLAT (Inverted File with Flat compression)
-- - Operador: vector_cosine_ops (distancia de coseno)
-- - Lists: 100 (configuración conservadora inicial)
-- - Probes: 10 (balance entre velocidad y precisión)

-- ============================================================================
-- 1. CONFIGURACIÓN DE PARÁMETROS GLOBALES
-- ============================================================================

-- Configurar número de probes para búsquedas vectoriales
SET ivfflat.probes = 10;

-- ============================================================================
-- 2. ÍNDICES VECTORIALES PARA CONTENIDO TEXTUAL
-- ============================================================================

-- Índices para particiones de hechos (tabla particionada)
CREATE INDEX IF NOT EXISTS idx_hechos_pre_2020_embedding_ivfflat 
ON hechos_pre_2020 USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_hechos_2020_embedding_ivfflat 
ON hechos_2020 USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_hechos_2021_embedding_ivfflat 
ON hechos_2021 USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_hechos_2022_embedding_ivfflat 
ON hechos_2022 USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_hechos_2023_embedding_ivfflat 
ON hechos_2023 USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_hechos_2024_embedding_ivfflat 
ON hechos_2024 USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_hechos_2025_embedding_ivfflat 
ON hechos_2025 USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_hechos_2026_embedding_ivfflat 
ON hechos_2026 USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_hechos_futuros_embedding_ivfflat 
ON hechos_futuros USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Índices para citas textuales y datos cuantitativos (ya existían)
-- idx_citas_embedding_ivfflat ON citas_textuales ✓
-- idx_datos_embedding_ivfflat ON datos_cuantitativos ✓

-- ============================================================================
-- 3. ÍNDICES VECTORIALES PARA ENTIDADES Y HILOS NARRATIVOS
-- ============================================================================

-- Índice vectorial para entidades
CREATE INDEX IF NOT EXISTS idx_entidades_embedding_ivfflat 
ON entidades USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Índice vectorial para hilos narrativos
CREATE INDEX IF NOT EXISTS idx_hilos_embedding_ivfflat 
ON hilos_narrativos USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================================================
-- 4. ÍNDICES VECTORIALES PARA DOCUMENTOS EXTENSOS
-- ============================================================================

-- Índice vectorial para fragmentos de documentos extensos
CREATE INDEX IF NOT EXISTS idx_fragmentos_embedding_ivfflat 
ON fragmentos_extensos USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================================================
-- 5. VERIFICACIÓN DE CONFIGURACIÓN
-- ============================================================================

-- Verificar que todos los índices vectoriales estén creados
DO $$
DECLARE
    index_count INTEGER;
    expected_count INTEGER := 14; -- Total de índices vectoriales esperados
BEGIN
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes 
    WHERE indexdef ILIKE '%ivfflat%' AND indexdef ILIKE '%vector_cosine_ops%';
    
    RAISE NOTICE 'Índices vectoriales creados: % de % esperados', index_count, expected_count;
    
    IF index_count < expected_count THEN
        RAISE WARNING 'Faltan índices vectoriales. Revisar configuración.';
    ELSE
        RAISE NOTICE 'Configuración de índices vectoriales completada exitosamente.';
    END IF;
END $$;

-- Verificar configuración de probes
SHOW ivfflat.probes;

-- ============================================================================
-- NOTAS PARA OPTIMIZACIÓN FUTURA (Tarea 18)
-- ============================================================================

/*
CONFIGURACIÓN ACTUAL (Conservadora para inicio):
- lists = 100: Apropiado para tablas pequeñas/medianas
- probes = 10: Balance entre velocidad y precisión

OPTIMIZACIONES PENDIENTES CON DATOS REALES:
1. Ajustar 'lists' basándose en el tamaño de cada tabla:
   - Regla general: lists = rows / 1000 (mínimo 10, máximo 32768)
   - Para > 1M registros: considerar HNSW en lugar de IVFFLAT
   
2. Ajustar 'probes' basándose en requirements de precisión vs velocidad:
   - Más probes = mayor precisión, menor velocidad
   - Probar valores entre 5-50 según uso específico
   
3. Considerar índices HNSW para consultas de alta frecuencia:
   - Mejor para consultas en tiempo real
   - Mayor uso de memoria pero búsquedas más rápidas
   
4. Monitorear métricas de rendimiento:
   - Tiempo de respuesta de consultas vectoriales
   - Precisión de resultados (recall@k)
   - Uso de memoria de índices
*/

-- ============================================================================
-- EJEMPLOS DE USO
-- ============================================================================

/*
-- Búsqueda de similaridad en hechos (ejemplo)
SELECT id, contenido, embedding <=> '[0.1,0.2,0.3,...]'::vector AS distance
FROM hechos_2024 
WHERE embedding IS NOT NULL
ORDER BY embedding <=> '[0.1,0.2,0.3,...]'::vector
LIMIT 10;

-- Búsqueda de entidades similares (ejemplo)
SELECT id, nombre, embedding <=> '[0.1,0.2,0.3,...]'::vector AS distance
FROM entidades 
WHERE embedding IS NOT NULL
ORDER BY embedding <=> '[0.1,0.2,0.3,...]'::vector
LIMIT 5;

-- Verificar que un índice se está usando (ejemplo)
EXPLAIN ANALYZE 
SELECT id, contenido 
FROM hechos_2024 
WHERE embedding IS NOT NULL
ORDER BY embedding <=> '[0.1,0.2,0.3,...]'::vector 
LIMIT 10;
*/
