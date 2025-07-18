# Diagnóstico Completo del Flujo de `id_fragmento` en el Pipeline

## Resumen Ejecutivo

El campo `id_fragmento` es crítico para mantener la trazabilidad de los fragmentos a través del pipeline. Sin embargo, existe una **desconexión entre cómo se genera/usa el ID internamente y lo que espera la capa de persistencia**, causando el error E012.

## 1. ORIGEN DEL ID_FRAGMENTO

### En controller.py (línea 185)
```python
fragmento_data = {
    "id_fragmento": str(uuid.uuid4()),  # ✅ Se genera aquí
    "texto_original": contenido,
    "id_articulo_fuente": str(articulo_id),
    # ...
}
```
**Estado**: ✅ El ID se genera correctamente como UUID string

## 2. FLUJO A TRAVÉS DE LAS FASES

### Fase 1: Triaje (fase_1_triaje.py)
```python
def ejecutar_fase_1(
    id_fragmento_original: UUID,  # ✅ Recibe el ID
    texto_original_fragmento: str,
    # ...
)
```
- **Entrada**: Recibe `id_fragmento` como UUID
- **Salida**: Retorna `ResultadoFase1Triaje` con `id_fragmento`
- **Estado**: ✅ Preserva correctamente el ID

### Fase 2: Simplificación
```python
resultado = ResultadoFase2Simplificacion(
    id_fragmento=resultado_triaje.id_fragmento,  # ✅ Propaga el ID
    # ...
)
```
- **Estado**: ✅ Propaga correctamente desde fase 1

### Fases 3-6: Entidades, Hechos, Datos, Citas
Todas las fases siguen el mismo patrón:
```python
resultado = {
    "id_fragmento": resultado_simplificacion.id_fragmento,  # ✅ Propaga
    # ...
}
```
- **Estado**: ✅ Todas propagan correctamente el ID

### Fase 7: Normalización
```python
resultado = ResultadoFase4Normalizacion(
    id_fragmento=hechos[0].id_fragmento_origen if hechos else uuid4(),  # ⚠️ PROBLEMA
    # ...
)
```
- **Estado**: ⚠️ Obtiene el ID desde los hechos, no del resultado anterior
- **Riesgo**: Si no hay hechos, genera un nuevo UUID (pérdida del ID original)

## 3. CONSTRUCCIÓN DEL PAYLOAD (controller.py línea 949)

```python
metadatos_fragmento = {
    "indice_secuencial_fragmento": fragmento.orden_en_articulo or 0,
    "titulo_seccion_fragmento": fragmento.metadata_adicional.get("titulo_seccion"),
    "contenido_texto_original_fragmento": fragmento.texto_original,
    # ❌ NO INCLUYE id_fragmento
}
```

**PROBLEMA PRINCIPAL**: El diccionario `metadatos_fragmento` NO incluye el campo `id_fragmento`.

## 4. MODELO DE PERSISTENCIA

### FragmentoPersistenciaPayload (persistencia.py)
```python
class FragmentoPersistenciaPayload(PersistenciaBaseModel):
    # Campos definidos:
    indice_secuencial_fragmento: int
    titulo_seccion_fragmento: Optional[str]
    contenido_texto_original_fragmento: str
    # ❌ NO define id_fragmento como campo
```

**PROBLEMA**: El modelo no define `id_fragmento` como campo requerido.

## 5. DIAGRAMA DE FLUJO

```
controller.py
    |
    ├─ Genera id_fragmento ✅
    |
    ├─ Fase 1: Recibe y retorna id_fragmento ✅
    |
    ├─ Fase 2-6: Propagan id_fragmento ✅
    |
    ├─ Fase 7: Obtiene de hechos (riesgo) ⚠️
    |
    └─ Construcción Payload
        |
        ├─ metadatos_fragmento (NO incluye id_fragmento) ❌
        |
        └─ PayloadBuilder → Supabase
            |
            └─ ERROR: Campo id_fragmento faltante
```

## 6. CAUSA RAÍZ DEL ERROR E012

El error ocurre porque:

1. **El ID se genera y propaga correctamente** por las fases del pipeline
2. **PERO no se incluye en el payload final** que se envía a Supabase
3. La RPC de Supabase probablemente **espera un campo `id_fragmento`** para identificar el fragmento
4. Al no encontrarlo, intenta acceder con `.get('id_fragmento')` y falla

## 7. SOLUCIÓN PROPUESTA

### Opción A: Añadir id_fragmento al payload (RECOMENDADA)
```python
# En controller.py, línea ~949
metadatos_fragmento = {
    "id_fragmento": str(fragmento.id_fragmento),  # ← AÑADIR ESTA LÍNEA
    "indice_secuencial_fragmento": fragmento.orden_en_articulo or 0,
    # ... resto de campos
}
```

### Opción B: Usar fragmento_uuid del resultado
```python
# En controller.py, después de procesar el pipeline
metadatos_fragmento = {
    "id_fragmento": resultado_pipeline.get('fragmento_uuid'),  # ← Usar el UUID del resultado
    # ... resto de campos
}
```

### Opción C: Actualizar modelo de persistencia
```python
# En persistencia.py
class FragmentoPersistenciaPayload(PersistenciaBaseModel):
    id_fragmento: str = Field(description="UUID único del fragmento")  # ← AÑADIR
    # ... resto de campos
```

## 8. VERIFICACIÓN DEL FIX

Para verificar que la solución funciona:

1. **Añadir logging** en controller.py:
```python
fragment_logger.info(f"Metadatos fragmento incluye: {list(metadatos_fragmento.keys())}")
```

2. **Verificar en Supabase RPC** que recibe el id_fragmento:
```sql
-- En la función insertar_fragmento_completo
RAISE NOTICE 'id_fragmento recibido: %', (p_fragmento_data->>'id_fragmento');
```

3. **Ejecutar test** y verificar que no aparece el error E012

## 9. IMPACTO Y CRITICIDAD

- **Criticidad**: ALTA - Impide la persistencia de fragmentos
- **Impacto**: Todos los fragmentos procesados fallan al guardarse
- **Urgencia**: Debe corregirse antes de procesar más artículos

## 10. RECOMENDACIONES

1. **Inmediato**: Implementar Opción A (añadir id_fragmento al payload)
2. **Corto plazo**: Revisar esquema de base de datos y confirmar campos requeridos
3. **Medio plazo**: Añadir validación en PayloadBuilder para campos requeridos
4. **Largo plazo**: Considerar usar tipos más estrictos para evitar estos errores

---

**Nota**: Este diagnóstico se basa en el análisis del código actual. El error E012 específicamente no aparece en los logs actuales, pero el patrón de error con `id_fragmento` es evidente en la estructura del código.