# Generación de Embeddings Vectoriales - Tarea 26

Este directorio contiene los scripts para generar embeddings vectoriales para todos los datos existentes en la base de datos de la Máquina de Noticias.

## 📋 Estado Actual

**PROBLEMA DETECTADO:** Los datos estructurados están poblados (202 hechos, 19 entidades, 7 hilos narrativos, etc.) pero las columnas de embeddings están completamente vacías, haciendo que los índices vectoriales sean inútiles.

## 🎯 Objetivo

Generar embeddings vectoriales de 384 dimensiones para todas las tablas que los requieren:

- **hechos**: 202 registros sin embeddings
- **entidades**: 19 registros sin embeddings  
- **hilos_narrativos**: 7 registros sin embeddings
- **fragmentos_extensos**: 1 registro sin embeddings
- **citas_textuales**: 1 registro sin embeddings
- **datos_cuantitativos**: 0 registros

## 🛠️ Configuración

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar Variables de Entorno

```bash
# Linux/Mac
export SUPABASE_PASSWORD='tu_password_de_supabase'

# Windows
set SUPABASE_PASSWORD=tu_password_de_supabase
```

### 3. Validar Configuración

```bash
# Probar modelo de embeddings
python embedding_config.py

# Probar conexión a base de datos
python database_config.py
```

## 📁 Archivos

### `embedding_config.py`
- Configuración del modelo de embeddings (all-MiniLM-L6-v2)
- Validación de dimensiones (384)
- Preprocesamiento de texto
- Pruebas de calidad

### `database_config.py`
- Conexión a Supabase/PostgreSQL
- Estadísticas de embeddings actuales
- Utilidades para consultas batch

### `requirements.txt`
- Dependencias necesarias
- sentence-transformers, numpy, psycopg2, etc.

## 🔧 Próximos Pasos

Una vez validada la configuración, se procederá a:

1. **Subtarea 26.2**: Implementar framework de procesamiento batch
2. **Subtarea 26.3**: Generar embeddings para tabla 'hechos' (202 registros)
3. **Subtarea 26.4**: Generar embeddings para tabla 'entidades' (19 registros)
4. **Subtarea 26.5**: Generar embeddings para tablas menores
5. **Subtarea 26.6**: Validar calidad y completitud

## ⚠️ Notas Importantes

- **Modelo**: all-MiniLM-L6-v2 (384 dimensiones)
- **Preprocesamiento**: Limpieza de texto, normalización, truncado
- **Batch Size**: 32 registros por lote
- **Error Handling**: Fallback individual en caso de errores de lote
- **Idempotencia**: Se puede reejecutar sin problemas

## 🧪 Validaciones

El sistema incluye validaciones para:
- ✅ Dimensiones exactas (384)
- ✅ Ausencia de valores NaN/infinitos
- ✅ Detección de vectores de ceros
- ✅ Estadísticas básicas (media, desviación, norma)
- ✅ Similitud semántica

## 📊 Métricas de Progreso

Usar `database_config.py` para monitorear progreso:
- Total de registros por tabla
- Registros con embeddings generados
- Porcentaje de completitud
- Registros pendientes

## 🚀 Ejecutar

```bash
# Validar todo el setup
python embedding_config.py && python database_config.py
```

Si ambos scripts se ejecutan exitosamente, la configuración está lista para proceder con la generación masiva de embeddings.
