# Hipótesis sobre Error RPC 22023 "argument 1: key must not be null"
## La Máquina de Noticias - Pipeline Module

### Error Observado
```
ERROR | SupabaseService | Error en RPC: argument 1: key must not be null. Código: 22023
```

### Contexto
- El error ocurre al llamar la función RPC `actualizar_articulo_procesado`
- Se han filtrado campos null de primer nivel (storage_path, fuente_original, etc.) pero el error persiste
- El error sugiere que algún campo clave está llegando como null dentro del payload

### HIPÓTESIS ORDENADAS POR PROBABILIDAD

## H1: Campos null en objetos anidados (85% probabilidad)
**Descripción**: El filtro actual solo elimina campos null de primer nivel, pero hay campos null en objetos anidados dentro de arrays como `entidades_autonomas`, `hechos_extraidos`, etc.

**Evidencia a favor**:
- El filtro actual muestra que elimina campos de primer nivel correctamente
- El error persiste después de filtrar campos de primer nivel
- La función SQL espera arrays de objetos con campos específicos NOT NULL

**Cómo verificar**:
- Examinar el payload completo después del filtrado
- Buscar campos null dentro de objetos en arrays

## H2: Campo crítico faltante en el payload (75% probabilidad)
**Descripción**: Un campo requerido por la función SQL no está siendo incluido en el payload, lo que PostgreSQL interpreta como null.

**Evidencia a favor**:
- La función SQL línea 334 espera `ambito_geografico` como array vacío por defecto
- Algunos campos en las tablas tienen constraints NOT NULL
- El payload podría no incluir todos los campos esperados

**Cómo verificar**:
- Comparar campos enviados vs campos esperados por la función SQL
- Verificar que todos los campos NOT NULL estén presentes

## H3: Problema con el formato JSONB (60% probabilidad)
**Descripción**: El payload no se está serializando correctamente a JSONB, causando que PostgreSQL no pueda parsear ciertos campos.

**Evidencia a favor**:
- La función SQL recibe `datos_json JSONB`
- El error menciona "argument 1" que es el parámetro JSONB
- Podría haber caracteres especiales o estructuras que rompen el parsing

**Cómo verificar**:
- Verificar la serialización JSON antes de enviar
- Buscar caracteres especiales o estructuras inválidas

## H4: IDs temporales con valor null (55% probabilidad)
**Descripción**: Los campos `id_temporal` en entidades, hechos, etc., están llegando como null, lo que rompe el mapeo interno en la función SQL.

**Evidencia a favor**:
- La función SQL usa mapeo de IDs temporales (líneas 36-37, 140-141, 223-224)
- Si un ID temporal es null, el mapeo falla
- Los IDs temporales son críticos para relacionar elementos

**Cómo verificar**:
- Revisar que todos los objetos tengan `id_temporal` válido
- Verificar el mapeo de IDs en el payload

## H5: Arrays con elementos null (45% probabilidad)
**Descripción**: Los arrays como `entidades_autonomas[]` o `hechos_extraidos[]` contienen elementos null en lugar de objetos válidos.

**Evidencia a favor**:
- La función SQL itera sobre arrays con `jsonb_array_elements`
- Un elemento null en el array causaría problemas al acceder a sus propiedades
- Los logs no muestran el contenido interno de los arrays

**Cómo verificar**:
- Inspeccionar cada array en el payload
- Verificar que no haya elementos null

## H6: Problema con campos de fecha/timestamp (40% probabilidad)
**Descripción**: Las fechas están en formato incorrecto o son null donde no deberían serlo.

**Evidencia a favor**:
- La función SQL convierte fechas a TIMESTAMPTZ (líneas 153-154, 292-294)
- Los campos de fecha son críticos para las relaciones
- El error podría ocurrir al parsear fechas inválidas

**Cómo verificar**:
- Revisar formato de todas las fechas en el payload
- Verificar que cumplan con ISO 8601

## H7: Conflicto con el campo articulo_id (35% probabilidad)
**Descripción**: El campo `articulo_id` no se está incluyendo correctamente o tiene formato incorrecto.

**Evidencia a favor**:
- La función SQL espera `articulo_id` como BIGINT (línea 42)
- El controller extrae el ID de formato "ART-1100" (líneas 599-604)
- Si la conversión falla, podría causar problemas

**Cómo verificar**:
- Verificar que articulo_id esté presente y sea numérico
- Revisar la conversión de ART-{ID} a número

## H8: Problema con valores de enums (25% probabilidad)
**Descripción**: Algunos campos tipo enum tienen valores no permitidos o null.

**Evidencia a favor**:
- Campos como `tipo_hecho`, `precision_temporal`, `categoria` tienen valores específicos permitidos
- Un valor no válido podría interpretarse como null
- Los defaults en la función SQL podrían no aplicarse correctamente

**Cómo verificar**:
- Validar todos los valores de enum contra las constraints
- Verificar que se usen los valores por defecto correctos

## H9: Problema con la conexión o permisos RPC (15% probabilidad)
**Descripción**: El error no es del payload sino de la conexión o permisos para ejecutar la RPC.

**Evidencia a favor**:
- El error es consistente
- Podría ser un problema de configuración de Supabase
- Los permisos de la función podrían estar mal configurados

**Cómo verificar**:
- Probar la RPC directamente en Supabase
- Verificar permisos de la función

## H10: Campo url faltante o inválido (10% probabilidad)
**Descripción**: El campo `url` es crítico para identificar el artículo y podría estar faltando.

**Evidencia a favor**:
- La función SQL usa url como fallback si no hay articulo_id (líneas 54-58)
- Si ambos faltan, la función retorna error
- El campo url es NOT NULL en la tabla

**Cómo verificar**:
- Confirmar que url está presente en el payload
- Verificar que no sea null o vacío

## H11: Problema con el formato de arrays PostgreSQL (8% probabilidad)
**Descripción**: Los arrays no se están convirtiendo correctamente al formato esperado por PostgreSQL.

**Evidencia a favor**:
- Muchos campos esperan arrays (alias, etiquetas, ambito_geografico)
- La conversión de JSON array a PostgreSQL array podría fallar
- Líneas como 126-129, 183-186 hacen conversiones de arrays

**Cómo verificar**:
- Revisar formato de todos los arrays en el payload
- Verificar que sean arrays JSON válidos

## H12: Valores numéricos como strings (5% probabilidad)
**Descripción**: Campos numéricos están llegando como strings y la conversión falla.

**Evidencia a favor**:
- Campos como `importancia`, `relevancia` se convierten con ::INTEGER
- Si el valor no es convertible, PostgreSQL podría interpretarlo como null
- La función hace muchas conversiones numéricas

**Cómo verificar**:
- Validar que todos los campos numéricos sean números
- Buscar strings que deberían ser números

---

### PRÓXIMOS PASOS
1. Implementar logging detallado del payload completo después del filtrado
2. Inspeccionar objetos anidados en busca de campos null
3. Validar la estructura completa contra lo esperado por la función SQL
4. Probar cada hipótesis sistemáticamente en orden de probabilidad