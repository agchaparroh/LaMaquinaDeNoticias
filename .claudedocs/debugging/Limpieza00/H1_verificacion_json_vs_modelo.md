# Verificación de Incompatibilidad: JSON vs ArticuloProcesableItem

## Fecha de análisis: 2025-07-18

## Resumen de hallazgos

Se encontraron diferencias significativas entre el JSON de entrada y el modelo ArticuloProcesableItem que explican los errores de validación.

## Tabla Comparativa de Campos

### 1. Campos en JSON pero NO en el modelo ArticuloProcesableItem

| Campo en JSON | Valor de ejemplo | Observación |
|---------------|------------------|-------------|
| articulo_id | 1166 | En el modelo se mapea a `id_articulo_fuente` |
| contenido_html | "<article>..." | No existe en el modelo |
| fuente | "infobae_america_latina" | En el modelo se espera como `medio` |
| medio_url_principal | "https://www.infobae.com/america/america-latina/" | No existe en el modelo |
| metadata | {...} | En el modelo se llama `metadata_adicional` |
| storage_path | "infobae/2025/07/09/..." | No existe en el modelo |

### 2. Campos en el modelo pero NO en el JSON

| Campo en modelo | Tipo | Requerido | Observación |
|-----------------|------|-----------|-------------|
| id_articulo | str | Sí | Se genera internamente en `from_articulo_in_item()` |
| id_articulo_fuente | int | No | Corresponde a `articulo_id` del JSON |
| etiquetas_fuente | List[str] | No | Tiene default factory |

### 3. Campos con nombres diferentes

| Campo en JSON | Campo en modelo | Tipo | Observación |
|---------------|-----------------|------|-------------|
| titular | titular | str | ✅ Coincide |
| contenido_texto | contenido_texto | str | ✅ Coincide |
| metadata | metadata_adicional | Dict | ❌ Nombres diferentes |
| articulo_id | id_articulo_fuente | int | ❌ Nombres diferentes |
| fuente | medio* | str | ❌ Posible confusión con "medio" |

*Nota: El JSON tiene tanto "fuente" como "medio", pero parecen representar conceptos diferentes.

## Problemas identificados

1. **Nomenclatura inconsistente**: 
   - JSON usa `metadata` mientras el modelo espera `metadata_adicional`
   - JSON usa `articulo_id` mientras el modelo lo mapea a `id_articulo_fuente`

2. **Campos faltantes en el modelo**:
   - `contenido_html`: El JSON incluye contenido HTML que no se procesa en el modelo
   - `storage_path`: Ruta de almacenamiento no contemplada en el modelo
   - `medio_url_principal`: URL principal del medio no incluida

3. **Ambigüedad de campos**:
   - El JSON tiene tanto `fuente` ("infobae_america_latina") como `medio` ("Infobae")
   - El modelo solo tiene `medio`

## Recomendaciones

1. **Actualizar el mapeo en `from_articulo_in_item()`** para manejar correctamente:
   - `metadata` → `metadata_adicional`
   - Verificar si `fuente` debe mapearse a algún campo

2. **Considerar agregar campos opcionales** al modelo para:
   - `contenido_html` (si se necesita preservar)
   - `storage_path` (para trazabilidad)
   - `medio_url_principal` (información del medio)

3. **Revisar el modelo ArticuloInItem** (líneas 10-47) que es el modelo temporal usado para la conversión, ya que podría tener discrepancias similares.

## Conclusión

La incompatibilidad principal está en la diferencia de nombres de campos (`metadata` vs `metadata_adicional`) y en campos presentes en el JSON que no tienen equivalente directo en el modelo. Esto requiere ajustar el proceso de conversión o actualizar los modelos para mantener consistencia.