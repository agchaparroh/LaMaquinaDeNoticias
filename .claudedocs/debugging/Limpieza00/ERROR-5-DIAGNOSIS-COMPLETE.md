# ERROR 5: Diagnóstico Completo - Fallo en Persistencia de Artículos

## Descripción del Error
```
ERROR: Campos requeridos faltantes en payload articulo
```

El pipeline procesa exitosamente las 7 fases pero falla al intentar persistir el resultado en Supabase.

## Método de Hipótesis Múltiples Aplicado

### Hipótesis Verificadas

#### H1: Pipeline genera payload de fragmento en vez de artículo ✅ CONFIRMADA
**Evidencia:**
- Línea 626 en `pipeline_coordinator.py`:
```python
return self.payload_builder.construir_payload_fragmento(
```
- NUNCA se llama a `construir_payload_articulo_from_model` o `construir_payload_articulo`
- El pipeline SIEMPRE genera payloads de fragmento, independientemente del tipo de contenido

#### H2: Campos de artículo se pierden durante la conversión ✅ CONFIRMADA
**Evidencia:**
- En la línea 114-120 de `pipeline_coordinator.py`:
```python
fragmento_unificado = FragmentoProcesableItem(
    id_fragmento=fragmento_id_str,
    texto_original=texto_original,
    id_articulo_fuente=id_articulo_fuente,
    orden_en_articulo=orden_en_articulo,
    metadata_adicional=contenido.metadata_adicional or {}
)
```
- Solo se copian 5 campos básicos
- Se pierden campos críticos: url, titular, fecha_publicacion, medio, etc.

#### H3: Incompatibilidad de nombres de campos ✅ CONFIRMADA
**Evidencia:**
- Campos requeridos para artículo (línea 145 de `supabase_service.py`):
  - url
  - titular
  - contenido_texto_original
  - fecha_procesamiento_pipeline
  - estado_procesamiento_final

- Campos generados por fragmento:
  - contenido_texto_original_fragmento (con sufijo)
  - fecha_procesamiento_pipeline_fragmento (con sufijo)
  - estado_procesamiento_final_fragmento (con sufijo)
  - NO incluye url ni titular

#### H4: Método construir_payload_articulo_from_model tiene bugs ✅ CONFIRMADA
**Evidencia:**
- Línea 312 de `payload_builder.py` accede a `articulo_model.titulo`:
```python
"titular": articulo_model.titulo,
```
- Pero `ArticuloProcesableItem` tiene el campo como `titular`, no `titulo`
- Este método nunca se usa, por lo que el bug no se ha manifestado

#### H5: Metadata no preserva campos de artículo ✅ PARCIALMENTE CONFIRMADA
**Evidencia:**
- Los campos del artículo se agregan a metadata_adicional en `to_fragmento_procesable()` (línea 278-294)
- Pero el payload builder no extrae estos campos de metadata para reconstruir el artículo

#### H6: Validación de Supabase rechaza el payload ✅ CONFIRMADA
**Evidencia:**
- Logs muestran: "Campos requeridos faltantes en payload articulo"
- La validación ocurre en `_validar_estructura_payload` antes de enviar a Supabase
- El error es correcto: faltan campos requeridos

#### H7: Mapeo incorrecto de ArticuloProcesableItem ✅ CONFIRMADA
**Evidencia:**
- `ArticuloProcesableItem` tiene los campos necesarios (url, titular, etc.)
- Pero se convierte a `FragmentoProcesableItem` perdiendo estos campos
- No hay mecanismo para recuperar los campos originales del artículo

## Flujo del Error Detallado

1. **Controller recibe ArticuloInItem** con todos los campos
2. **Convierte a ArticuloProcesableItem** preservando campos
3. **Pipeline convierte a FragmentoProcesableItem** (línea 114-120) - **PÉRDIDA DE DATOS**
4. **Pipeline procesa como fragmento** en las 7 fases
5. **Pipeline genera payload de fragmento** (línea 626) - **PAYLOAD INCORRECTO**
6. **Controller detecta que es artículo** (línea 585)
7. **Controller intenta persistir como artículo** (línea 612)
8. **Supabase valida y rechaza** - faltan campos requeridos

## Solución Propuesta

### Opción A: Modificar pipeline para generar payload correcto (RECOMENDADA)
1. En `pipeline_coordinator.py`, detectar si es artículo completo
2. Si es artículo, llamar a `construir_payload_articulo_from_model`
3. Preservar el ArticuloProcesableItem original hasta el final
4. Corregir el bug en `construir_payload_articulo_from_model` (titulo → titular)

### Opción B: Transformar payload fragmento a artículo en controller
1. En el controller, antes de persistir, transformar campos:
   - contenido_texto_original_fragmento → contenido_texto_original
   - fecha_procesamiento_pipeline_fragmento → fecha_procesamiento_pipeline
   - Extraer url, titular, etc. de metadata_adicional
2. Más complejo y propenso a errores

### Opción C: Modificar Supabase RPC para aceptar ambos formatos
1. Cambiar la RPC para detectar formato de payload
2. Normalizar internamente
3. Requiere cambios en base de datos

## Impacto
- **Crítico**: Impide la persistencia de TODOS los artículos
- **Sin workaround**: No hay forma de evitar el error sin modificar código
- **Afecta producción**: El pipeline no puede guardar resultados

## Próximos Pasos
1. Implementar la solución A (modificar pipeline)
2. Probar con artículos de diferentes tamaños
3. Verificar persistencia en Supabase
4. Actualizar Docker con la corrección