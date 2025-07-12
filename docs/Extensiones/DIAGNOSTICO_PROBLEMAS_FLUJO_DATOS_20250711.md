# Diagnóstico de Problemas en el Flujo de Datos - La Máquina de Noticias

**Fecha**: 11 de Julio de 2025  
**Contexto**: Análisis exhaustivo del sistema tras implementar arquitectura híbrida de persistencia

## Resumen Ejecutivo

El sistema presenta una implementación parcial de la arquitectura híbrida diseñada. Mientras que la generación y exportación de archivos JSON funciona correctamente, existen múltiples puntos de fallo en el procesamiento posterior y la persistencia a Supabase.

## 1. Estado del Flujo de Datos

### 1.1 Componentes Funcionales

- **Scraper (module_scraper)**: Operativo. Genera correctamente archivos JSON.gz con artículos completos
- **ItemConverterPipeline**: Funcional. Convierte dict → ArticuloInItem exitosamente
- **JsonWriterPipeline**: Funcional. Exporta 22+ archivos a `/data/scrapy_output/pending/`
- **Connector (module_connector)**: Parcialmente funcional. Detecta archivos pero los mueve a `/error/`

### 1.2 Puntos de Interrupción

El flujo se interrumpe en múltiples puntos:

1. **Pipeline API (puerto 8003)**: Estado "unhealthy", no responde a health checks
2. **Persistencia a Supabase**: Falla con errores de esquema y buckets no encontrados
3. **Procesamiento de artículos**: Connector mueve mayoría de archivos a directorio de error

## 2. Errores de Base de Datos

### 2.1 Error "area_geografica column not found"

**Diagnóstico**: Falso positivo
- El campo `area_geografica` SÍ existe en el esquema (confirmado en arquitectura)
- Los archivos JSON generados contienen correctamente este campo
- Error reportado: `{'code': 'PGRST204', 'message': "Could not find the 'area_geografica' column"}`

**Causa probable**: Problema de caché del esquema en Supabase o desincronización de permisos

### 2.2 Error "Bucket not found"

**Error específico**: 
```
Error uploading file to articulos_html_beta/infobae/2025-07-09/[uuid].html.gz: 
{'statusCode': 400, 'error': 'Bucket not found', 'message': 'Bucket not found'}
```

**Diagnóstico**: El bucket 'articulos_html_beta' no existe en Supabase Storage

## 3. Problemas del Pipeline API

### 3.1 Error de Importación Crítico

**Ubicación**: `src/module_pipeline/src/persistence/payload_builder.py`
**Error**: `No module named 'utils'` (línea 8)
**Impacto**: Impide que la Fase 5 de persistencia funcione correctamente

### 3.2 Respuestas LLM Truncadas

**Síntomas observados**:
- "Llaves desbalanceadas: 168 abiertas vs 166 cerradas"
- Parser JSON devuelve diccionario vacío como fallback
- Múltiples reintentos con Groq API

**Diagnóstico**: Las respuestas del LLM exceden límites de tokens o timeouts configurados

### 3.3 Health Check Timeout

**Síntoma**: `curl http://localhost:8003/health` → timeout después de 2 minutos
**Estado Docker**: Container marcado como "unhealthy"

## 4. Análisis de Validación de Datos

### 4.1 Campo "titulo" reportado como faltante

**Observación paradójica**:
- Los archivos JSON SÍ contienen el campo `titulo` (verificado en múltiples archivos)
- El error de validación reporta: "Required field 'titulo' is missing or empty"

**Diagnóstico**: Posible discrepancia entre el nombre del campo en el spider (`titulo`) y lo esperado por el validador

## 5. Estado de la Arquitectura Híbrida

### 5.1 Flujo Directo (Scraper → Supabase)

**Estado**: Parcialmente implementado pero fallando
- SupabaseStoragePipeline está activo (prioridad 400)
- Intenta guardar pero falla por errores de esquema/buckets

### 5.2 Flujo por Archivos (Scraper → JSON → Connector → Pipeline)

**Estado**: Parcialmente funcional
- Generación de archivos: ✅ Funcional
- Detección por connector: ✅ Funcional
- Envío a Pipeline API: ❌ Falla (API unhealthy)
- Procesamiento: ❌ Falla (errores de importación)

## 6. Logs Críticos Identificados

### 6.1 Scraper
```
Article https://[url] processed with errors: DB upsert failed after retries: 
RetryError[<Future at 0x7fddbde11600 state=finished raised SupabaseAPIError>]
```

### 6.2 Connector
```
ERROR | ❌ Unexpected error sending article art_142447 to pipeline:
```

### 6.3 Pipeline
```
ERROR | src.pipeline.fase_2_extraccion:ejecutar_fase_2:608 | 
Error inesperado durante extracción para [uuid]: 
Respuesta LLM no es JSON válido
```

## 7. Diagnóstico de Configuración

### 7.1 Variables de Entorno

Las variables críticas parecen estar configuradas:
- `GROQ_API_KEY`: Presente (LLM responde pero con errores)
- `SUPABASE_*`: Configuradas (conexión establecida pero con errores de esquema)

### 7.2 Volúmenes Docker

**Configuración correcta**:
- Volume `shared_data` creado y montado en `/data` para scraper y connector
- Archivos se comparten exitosamente entre contenedores

## 8. ACTUALIZACIÓN: Problemas Resueltos y Nuevos Hallazgos

### 8.1 Problemas Resueltos (11 Jul 2025 15:00)

✅ **Error de importación en payload_builder.py**: 
- **Solución aplicada**: Corregido import `from utils.validation` → `from ..utils.validation`
- **Estado**: Pipeline API health check responde correctamente

✅ **Columna area_geografica faltante**:
- **Diagnóstico confirmado**: La columna NO existía en el esquema real de Supabase
- **Solución aplicada**: `ALTER TABLE articulos ADD COLUMN area_geografica VARCHAR(50) NOT NULL DEFAULT 'HISPANOAMERICA'`
- **Estado**: Columna agregada exitosamente via Supabase Dashboard

✅ **Bucket articulos-html-beta inexistente**:
- **Solución aplicada**: Bucket creado via API de Supabase Storage
- **Estado**: Bucket disponible y funcional

### 8.2 Nuevos Problemas Identificados

❌ **Pipeline API Request Timeout**:
- **Síntoma**: Health check OK, pero requests reales a `/procesar_articulo` fallan con timeout
- **Impacto**: Connector no puede enviar artículos para procesamiento
- **Evidencia**: `curl -X POST /procesar_articulo` → timeout después de 2 minutos
- **Estado**: 🔍 **EN ANÁLISIS**

❌ **Base de Datos Vacía**:
- **Confirmado**: 0 registros en tabla `articulos` a pesar del procesamiento activo
- **Causa probable**: Artículos no llegan al pipeline por timeouts de comunicación
- **Estado**: `SELECT COUNT(*) FROM articulos` → 0

❌ **Arquitectura Híbrida Interrumpida**:
- **Flujo Scraper→JSON**: ✅ Funcional (22+ archivos generados)
- **Flujo JSON→Connector**: ✅ Funcional (archivos detectados y procesados)
- **Flujo Connector→Pipeline**: ❌ Timeout en comunicación HTTP
- **Flujo Pipeline→Supabase**: ❌ No ejecuta por falta de datos de entrada

❌ **Validación de Título Falla Incorrectamente**:
- **Síntoma**: Error "Required field 'titulo' is missing or empty" aunque campo existe en JSON
- **Archivos afectados**: Múltiples archivos JSON verificados manualmente
- **Evidencia**: Campo `titular` presente en JSONs pero validación reporta falta de `titulo`
- **Causa probable**: Discrepancia en nombres de campos (titular vs titulo)

❌ **Respuestas LLM Truncadas y JSON Malformado**:
- **Síntoma**: "Llaves desbalanceadas: 168 abiertas vs 166 cerradas" en logs pipeline
- **Impacto**: Parser JSON devuelve diccionario vacío como fallback
- **Evidencia**: Múltiples reintentos con Groq API sin éxito
- **Causa probable**: Límites de tokens o timeouts en respuestas LLM

❌ **Request Timeout en Pipeline POST /procesar_articulo**:
- **Síntoma específico**: Timeout de 90 segundos configurado en connector se agota
- **Configuración actual**: ClientTimeout(total=90) en línea 335 de main.py
- **Evidencia**: Todos los archivos movidos a directorio error por timeout
- **Red**: Containers en misma red Docker, health check funciona
- **Estado**: Problema crítico bloqueando flujo completo

## 9. Resumen de Problemas Críticos Actuales

1. ~~**Error de importación en módulo de persistencia**~~ - ✅ **RESUELTO**
2. ~~**Pipeline API en estado unhealthy**~~ - ✅ **RESUELTO** 
3. ~~**Bucket de Supabase Storage inexistente**~~ - ✅ **RESUELTO**
4. ~~**Posible problema de caché/permisos en Supabase**~~ - ✅ **RESUELTO**
5. **Respuestas LLM exceden límites** - ⚠️ **PERSISTE** (JSON truncado, procesamiento incompleto)
6. **Pipeline API timeout en requests reales** - ❌ **NUEVO PROBLEMA CRÍTICO**
7. **Connector mueve 100% archivos a error** - ❌ **AGRAVADO** (por problema #6)

## 9. Evidencia de Funcionamiento Parcial

A pesar de los errores, el sistema demuestra capacidad parcial:
- 22+ archivos JSON generados correctamente
- Estructura de datos completa en archivos exportados
- Connector activo y monitoreando directorio
- Pipeline intentando procesar (aunque con errores)

---

**Nota**: Este diagnóstico se basa en logs y análisis del estado actual del sistema. No incluye propuestas de solución según lo solicitado.