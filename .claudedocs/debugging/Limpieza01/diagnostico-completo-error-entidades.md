# Diagnóstico Completo: Error "null value in column 'nombre' of relation 'entidades'"

## Resumen Ejecutivo
Se identificó un desajuste entre el pipeline y la RPC. El pipeline envía el campo `nombre` mientras que la RPC `actualizar_articulo_procesado` espera `nombre_entidad`.

## Evidencia Recolectada

### 1. Flujo de Procesamiento Exitoso
- Spider: ✅ Extrajo y almacenó artículo ID 1100
- Connector: ✅ Procesó y envió al pipeline
- Pipeline: ✅ Completó las 7 fases
  - 12 entidades extraídas
  - 7 hechos extraídos
  - 0 citas extraídas
- Persistencia: ❌ Error al llamar RPC

### 2. Análisis del Código

#### Pipeline (pipeline_coordinator.py líneas 654-667):
```python
entidades_data.append({
    "id": str(entidad.id_entidad),
    "nombre": entidad.nombre_entidad_normalizada or entidad.texto_entidad,  # <-- AQUÍ
    "tipo": entidad.tipo_entidad,
    ...
})
```

#### RPC SQL (actualizar_articulo_procesado.sql línea 117):
```sql
INSERT INTO entidades (nombre, tipo, ...)
VALUES (
    v_entidad->>'nombre_entidad',  -- <-- ESPERA nombre_entidad
    v_entidad->>'tipo_entidad',
    ...
)
```

#### Modelo Pydantic (persistencia.py línea 62):
```python
nombre: str = Field(description="Nombre de la entidad (coincide con columna 'nombre' en DB).")
```

### 3. Validación de Hipótesis

#### Hipótesis A: Desajuste entre modelo y RPC ✅ CONFIRMADA
- **Evidencia a favor**: 
  - Pipeline envía `"nombre"` (línea 657 pipeline_coordinator.py)
  - RPC busca `v_entidad->>'nombre_entidad'` (línea 117 actualizar_articulo_procesado.sql)
  - Error SQL menciona columna "nombre" que recibe NULL
- **Evidencia en contra**: Ninguna
- **Verificación**: Código revisado directamente
- **Conclusión**: Esta es la causa raíz del error

#### Hipótesis B: Entidad con nombre vacío ❌ DESCARTADA
- **Evidencia a favor**: Error es NOT NULL constraint
- **Evidencia en contra**: 
  - Logs muestran todas las entidades con nombres válidos
  - El problema no es el contenido sino el nombre del campo
- **Verificación**: Los logs del pipeline muestran nombres para todas las 12 entidades
- **Conclusión**: No es la causa

#### Hipótesis C: Error en transformación de datos ❌ DESCARTADA
- **Evidencia a favor**: El procesamiento fue exitoso hasta la persistencia
- **Evidencia en contra**: 
  - El payload se construye correctamente con el campo `nombre`
  - No hay transformación adicional que pueda perder el valor
- **Verificación**: El payload_builder simplemente pasa los datos
- **Conclusión**: No es la causa

#### Hipótesis D: Problema con caracteres especiales ❌ DESCARTADA
- **Evidencia a favor**: "Israe" aparece truncado en logs
- **Evidencia en contra**: 
  - El error es específicamente sobre campo NULL, no sobre caracteres
  - Otros nombres con caracteres especiales están presentes
- **Verificación**: El problema es estructural, no de contenido
- **Conclusión**: No es la causa

## Análisis de Causalidad

### Cadena de Eventos:
1. Pipeline procesa entidades correctamente
2. Pipeline_coordinator construye dict con campo `nombre`
3. Payload_builder convierte a EntidadAutonomaItem (que también espera `nombre`)
4. Controller envía payload a Supabase
5. RPC busca `nombre_entidad` en el JSON
6. Al no encontrarlo, intenta insertar NULL
7. Base de datos rechaza por constraint NOT NULL

### ¿Por qué existe este desajuste?
Posibles razones:
1. **Cambio no sincronizado**: La RPC fue actualizada para usar `nombre_entidad` pero el pipeline no
2. **Inconsistencia histórica**: Diferentes equipos usaron diferentes convenciones
3. **Modelo vs RPC**: El modelo Pydantic usa `nombre` pero la RPC espera `nombre_entidad`

## Solución Propuesta

### Opción 1: Modificar el Pipeline (RECOMENDADA)
Cambiar en `pipeline_coordinator.py` línea 657:
```python
# De:
"nombre": entidad.nombre_entidad_normalizada or entidad.texto_entidad,
# A:
"nombre_entidad": entidad.nombre_entidad_normalizada or entidad.texto_entidad,
```

**Ventajas**: 
- Cambio mínimo
- Mantiene compatibilidad con RPC existente
- No requiere cambios en base de datos

### Opción 2: Modificar la RPC
Cambiar en `actualizar_articulo_procesado.sql` línea 117:
```sql
-- De:
v_entidad->>'nombre_entidad',
-- A:
v_entidad->>'nombre',
```

**Desventajas**: 
- Requiere actualizar función en producción
- Podría romper otras integraciones

### Opción 3: Modificar ambos para usar convención consistente
Actualizar todo para usar `nombre` o `nombre_entidad` consistentemente.

**Desventajas**: 
- Cambio más invasivo
- Mayor riesgo de regresiones

## Recomendación Final
Implementar **Opción 1** modificando el pipeline_coordinator para enviar `nombre_entidad` en lugar de `nombre`. Es el cambio más seguro y directo.

## Verificación Adicional Requerida
Antes de aplicar el fix:
1. Verificar si hay otros campos con el mismo problema (tipo_entidad, etc.)
2. Revisar si hay otras RPCs que esperan formato diferente
3. Confirmar que el cambio no rompe otros flujos