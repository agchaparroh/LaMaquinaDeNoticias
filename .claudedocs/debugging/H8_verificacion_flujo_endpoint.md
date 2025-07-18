# H8: Verificación de Flujo desde Endpoint

## FLUJO COMPLETO IDENTIFICADO:

1. **Endpoint recibe POST** con JSON
2. **FastAPI valida** con ArticuloInItem (línea 510)
3. **Conversión a dict**: `articulo_dict = articulo.model_dump()` (línea 617)
4. **Background task**: pasa `articulo_dict` al controller (línea 677)
5. **Controller intenta procesar** el dict

### PROBLEMA CLAVE:

El `model_dump()` de ArticuloInItem genera un diccionario con los campos 
que tiene el modelo ArticuloInItem, NO con los campos del JSON original.

### Verificación de ArticuloInItem:
- Espera campo `titular` (línea 21 en models/entrada.py)
- Tiene configuración `extra = "allow"` en desarrollo

### LO QUE SUCEDE:

1. JSON tiene `titulo: "Día Internacional..."`
2. ArticuloInItem espera `titular`
3. Como `extra="allow"`, el campo `titulo` pasa como campo extra
4. `titular` queda como None o falta
5. Cuando se hace `articulo_dict['titular']` en controller → KeyError

### CONCLUSIÓN H8: ✅ CONFIRMADA

El flujo desde el endpoint tiene un problema:
- ArticuloInItem no está mapeando correctamente los campos del JSON
- El JSON tiene `titulo` pero el modelo espera `titular`
- Esto causa que el controller reciba datos incorrectos