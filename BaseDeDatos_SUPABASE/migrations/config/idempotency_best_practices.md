# Guía de Mejores Prácticas para Scripts Idempotentes

## 🎯 Principios Fundamentales

### 1. Definición de Idempotencia
Un script idempotente puede ejecutarse múltiples veces sin producir efectos secundarios o cambios no deseados. El resultado final debe ser el mismo independientemente de cuántas veces se ejecute.

### 2. Beneficios de la Idempotencia
- **Recuperación ante errores**: Poder re-ejecutar desde donde falló
- **Deployments seguros**: Eliminar el miedo a ejecutar scripts múltiples veces
- **Mantenimiento simplificado**: Facilita actualizaciones y patches
- **Testing confiable**: Permite pruebas repetibles

## 🛠️ Patrones de Implementación

### Patrón 1: Verificación de Existencia con IF NOT EXISTS

```sql
-- ✅ CORRECTO: Verificar antes de crear
CREATE TABLE IF NOT EXISTS mi_tabla (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255)
);

-- ❌ INCORRECTO: Crear sin verificar
CREATE TABLE mi_tabla (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255)
);
```

### Patrón 2: Verificación Manual con Bloques DO

```sql
-- ✅ CORRECTO: Control granular
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'usuarios' AND column_name = 'email'
    ) THEN
        ALTER TABLE usuarios ADD COLUMN email VARCHAR(255);
    END IF;
END
$$;
```

### Patrón 3: Manejo de Excepciones

```sql
-- ✅ CORRECTO: Capturar excepciones específicas
DO $$
BEGIN
    CREATE UNIQUE INDEX idx_usuario_email ON usuarios(email);
EXCEPTION WHEN duplicate_table THEN
    -- El índice ya existe, continuar silenciosamente
    NULL;
END
$$;
```

### Patrón 4: Upsert para Datos

```sql
-- ✅ CORRECTO: INSERT con ON CONFLICT
INSERT INTO configuracion (clave, valor)
VALUES ('version', '1.0')
ON CONFLICT (clave) 
DO UPDATE SET 
    valor = EXCLUDED.valor,
    updated_at = NOW();
```

### Patrón 5: Verificación de Estado Antes de Cambios

```sql
-- ✅ CORRECTO: Solo aplicar si es necesario
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'check_edad_positiva'
    ) THEN
        ALTER TABLE usuarios 
        ADD CONSTRAINT check_edad_positiva 
        CHECK (edad > 0);
    END IF;
END
$$;
```

## 🔧 Herramientas y Funciones Útiles

### Funciones de Verificación Incorporadas

```sql
-- Verificar existencia de tabla
SELECT EXISTS (
    SELECT 1 FROM information_schema.tables 
    WHERE table_name = 'mi_tabla'
);

-- Verificar existencia de columna
SELECT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'mi_tabla' AND column_name = 'mi_columna'
);

-- Verificar existencia de índice
SELECT EXISTS (
    SELECT 1 FROM pg_indexes 
    WHERE indexname = 'mi_indice'
);

-- Verificar existencia de función
SELECT EXISTS (
    SELECT 1 FROM information_schema.routines 
    WHERE routine_name = 'mi_funcion'
);

-- Verificar existencia de trigger
SELECT EXISTS (
    SELECT 1 FROM information_schema.triggers 
    WHERE trigger_name = 'mi_trigger'
);
```

### Funciones Auxiliares Personalizadas

```sql
-- Función para verificar si una columna existe
CREATE OR REPLACE FUNCTION column_exists(
    table_name TEXT, 
    column_name TEXT, 
    schema_name TEXT DEFAULT 'public'
) RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = schema_name 
        AND table_name = $1 
        AND column_name = $2
    );
END;
$$ LANGUAGE plpgsql;

-- Función para agregar columna de forma idempotente
CREATE OR REPLACE FUNCTION add_column_if_not_exists(
    table_name TEXT,
    column_name TEXT,
    column_definition TEXT,
    schema_name TEXT DEFAULT 'public'
) RETURNS BOOLEAN AS $$
BEGIN
    IF NOT column_exists(table_name, column_name, schema_name) THEN
        EXECUTE format('ALTER TABLE %I.%I ADD COLUMN %I %s', 
                      schema_name, table_name, column_name, column_definition);
        RETURN TRUE;
    END IF;
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;
```

## ⚠️ Errores Comunes a Evitar

### 1. No Verificar Existencia

```sql
-- ❌ MAL: Causará error si ya existe
CREATE INDEX idx_usuarios_email ON usuarios(email);

-- ✅ BIEN: Verificar primero
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);
```

### 2. Asumir Estado Inicial

```sql
-- ❌ MAL: Asumir que la tabla está vacía
INSERT INTO configuracion VALUES (1, 'admin', 'Administrator');

-- ✅ BIEN: Verificar antes de insertar
INSERT INTO configuracion (id, key, value)
SELECT 1, 'admin', 'Administrator'
WHERE NOT EXISTS (SELECT 1 FROM configuracion WHERE key = 'admin');
```

### 3. No Manejar Dependencias

```sql
-- ❌ MAL: No verificar dependencias
ALTER TABLE pedidos ADD CONSTRAINT fk_usuario 
FOREIGN KEY (usuario_id) REFERENCES usuarios(id);

-- ✅ BIEN: Verificar dependencias
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'usuarios')
    AND NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_usuario'
    ) THEN
        ALTER TABLE pedidos ADD CONSTRAINT fk_usuario 
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id);
    END IF;
END
$$;
```

### 4. Transacciones Incorrectas

```sql
-- ❌ MAL: No usar transacciones
CREATE TABLE tabla1 (...);
CREATE TABLE tabla2 (...);
INSERT INTO tabla1 VALUES (...);

-- ✅ BIEN: Usar transacciones apropiadas
BEGIN;
CREATE TABLE IF NOT EXISTS tabla1 (...);
CREATE TABLE IF NOT EXISTS tabla2 (...);
INSERT INTO tabla1 
SELECT ... WHERE NOT EXISTS (SELECT 1 FROM tabla1 WHERE id = ...);
COMMIT;
```

## 🧪 Testing de Idempotencia

### Script de Prueba Básico

```sql
-- Ejecutar el script 3 veces y verificar que no hay errores
\set ON_ERROR_STOP on

-- Primera ejecución
\i mi_script_idempotente.sql

-- Segunda ejecución (debería ser silenciosa)
\i mi_script_idempotente.sql

-- Tercera ejecución (debería ser silenciosa)
\i mi_script_idempotente.sql

-- Verificar que el estado final es correcto
SELECT 'Test pasado' WHERE (
    -- Verificaciones específicas aquí
    EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'mi_tabla')
    AND
    EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'mi_indice')
);
```

### Checklist de Validación

- [ ] El script puede ejecutarse múltiples veces sin errores
- [ ] El resultado final es idéntico en cada ejecución
- [ ] Los mensajes de log son apropiados (informativos, no repetitivos)
- [ ] Las transacciones son atómicas
- [ ] Se manejan apropiadamente las excepciones
- [ ] Se verifican todas las dependencias
- [ ] Se registra la ejecución en migration_history

## 📊 Monitoreo y Logging

### Logging Estándar

```sql
-- Inicio del script
RAISE NOTICE 'Iniciando script: % a las %', script_name, clock_timestamp();

-- Progreso intermedio
RAISE NOTICE '✓ Tabla % creada exitosamente', tabla_name;
RAISE NOTICE '⚠ Índice % ya existe, saltando...', indice_name;

-- Finalización
RAISE NOTICE '✅ Script % completado en % ms', script_name, execution_time;
```

### Métricas de Rendimiento

```sql
-- Medir tiempo de ejecución
DECLARE
    start_time TIMESTAMP := clock_timestamp();
    execution_time INTEGER;
BEGIN
    -- Lógica del script aquí...
    
    execution_time := EXTRACT(epoch FROM (clock_timestamp() - start_time)) * 1000;
    RAISE NOTICE 'Tiempo de ejecución: % ms', execution_time;
END;
```

## 🎯 Recomendaciones Finales

1. **Empezar Simple**: Implementar idempotencia básica primero
2. **Documentar Asunciones**: Explicar qué condiciones se asumen
3. **Probar Exhaustivamente**: Ejecutar múltiples veces en desarrollo
4. **Usar Transacciones**: Mantener atomicidad de operaciones
5. **Logging Apropiado**: Informar sin ser verboso
6. **Manejar Dependencias**: Verificar prerrequisitos siempre
7. **Planificar Rollbacks**: Cada script debe ser reversible

## 📚 Recursos Adicionales

- `config/idempotent_template.sql` - Plantilla base para nuevos scripts
- `validations/validate_idempotency.sql` - Script de validación automática
- `migrations/examples/` - Ejemplos de patrones comunes
- PostgreSQL Documentation: [DDL Commands](https://postgresql.org/docs/current/ddl.html)

---

**Recuerda**: La idempotencia no es opcional en un sistema de migración robusto. Es la diferencia entre un deployment confiable y una pesadilla operacional.
