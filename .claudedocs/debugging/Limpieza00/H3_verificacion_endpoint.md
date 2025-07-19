# H3: Verificación de Validación en Endpoint

## HALLAZGOS

El endpoint `/procesar_articulo` SÍ está validando la entrada:

```python
async def procesar_articulo(
    articulo: ArticuloInItem,  # ← VALIDACIÓN CON PYDANTIC
    background_tasks: BackgroundTasks
):
```

### Flujo de datos:
1. POST request llega con JSON
2. FastAPI intenta crear `ArticuloInItem` con el JSON
3. Si ArticuloInItem se crea exitosamente, pasa al controller
4. Controller convierte ArticuloInItem a dict y luego a ArticuloProcesableItem

### Verificación de ArticuloInItem:
El modelo ArticuloInItem (líneas 11-46 en models/entrada.py) espera:
- `titular` (no `titulo`)
- `area_geografica` 
- `tipo_medio`
- etc.

### PROBLEMA:
El JSON de prueba tiene `titulo` pero ArticuloInItem espera `titular`. 
Sin embargo, el error no ocurre en la validación del endpoint sino más adelante en el controller.

### POSIBLE EXPLICACIÓN:
ArticuloInItem tiene configuración `extra = "allow"` en modo desarrollo (línea 46), 
lo que permite campos extra. Esto explicaría por qué el JSON pasa la validación inicial
pero falla después en ArticuloProcesableItem.

### CONCLUSIÓN H3: ❌ DESCARTADA (parcialmente)

El endpoint SÍ valida con ArticuloInItem, pero la configuración permisiva en desarrollo
permite que pasen datos incorrectos que luego fallan en ArticuloProcesableItem.