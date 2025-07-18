# MÉTODO DE HIPÓTESIS MÚLTIPLES - ERROR 1: ValidationError

## ERROR: Campo requerido faltante en ArticuloProcesableItem

### HIPÓTESIS GENERADAS:

**H1: El JSON de prueba tiene un formato obsoleto**
- Los archivos de prueba fueron creados antes de un cambio en el modelo
- El modelo espera "titular" pero el JSON tiene "titulo"

**H2: Hay un transformador/mapper faltante entre ArticuloInItem y ArticuloProcesableItem**
- El código debería mapear campos antes de crear ArticuloProcesableItem
- Falta lógica de transformación de campos

**H3: El modelo ArticuloInItem y ArticuloProcesableItem están desincronizados**
- ArticuloInItem acepta ciertos campos que ArticuloProcesableItem rechaza
- Incompatibilidad entre modelos de entrada y procesamiento

**H4: Error en la configuración del endpoint que no valida correctamente**
- El endpoint /procesar_articulo debería recibir ArticuloInItem
- La conversión a ArticuloProcesableItem está mal implementada

**H5: El JSON viene de un sistema externo con nomenclatura diferente**
- El scraper genera JSONs con una estructura
- El pipeline espera otra estructura

### VERIFICACIÓN DE HIPÓTESIS:

**H1: Verificando estructura del JSON vs modelo**
✓ Verificado: JSON tiene "titulo", modelo espera "titular"
✓ Verificado: JSON tiene "pais", modelo no tiene este campo
✓ Resultado: JSON y modelo incompatibles
→ Conclusión: CONFIRMADA - Hay discrepancia de campos

**H2: Verificando transformación en controller.py**
✓ Verificado: Líneas 189-232 intentan mapear campos
✓ Verificado: No hay mapeo de "titulo" a "titular"
✓ Resultado: Falta lógica de transformación
→ Conclusión: CONFIRMADA - Falta mapeo de campos

**H3: Verificando modelos ArticuloInItem vs ArticuloProcesableItem**
✓ Verificado: ArticuloInItem tiene campo "titular" (línea 21)
✓ Verificado: ArticuloProcesableItem también espera "titular"
✓ Resultado: Modelos consistentes entre sí
→ Conclusión: DESCARTADA - Modelos están alineados

**H4: Verificando endpoint en main.py**
✓ Verificado: Endpoint recibe ArticuloInItem (línea 508)
✓ Verificado: Controller convierte a dict y luego a ArticuloProcesableItem
✓ Resultado: Flujo correcto pero sin mapeo de campos
→ Conclusión: PARCIALMENTE CONFIRMADA - Flujo correcto, mapeo incompleto

**H5: Verificando origen del JSON**
✓ Verificado: JSON generado por infobae_america_latina spider
✓ Verificado: Campo "titulo" viene del scraper
✓ Resultado: Scraper usa nomenclatura diferente
→ Conclusión: CONFIRMADA - Sistema externo con campos diferentes

### SÍNTESIS FINAL:

**Causa raíz identificada**: 
1. Los JSONs de prueba vienen del scraper con campos diferentes (titulo vs titular)
2. El controller no tiene lógica de mapeo para estos campos
3. Necesitamos agregar transformación de campos en el controller

**Solución recomendada**:
Agregar mapeo de campos en el controller antes de crear ArticuloProcesableItem:
- "titulo" → "titular"
- "pais" → "area_geografica" (ya viene area_geografica en el JSON)
- Remover campos no esperados: fuente_original, medio_url_principal, contenido_html