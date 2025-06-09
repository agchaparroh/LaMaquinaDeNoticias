# Correcciones para los Tests de Integración

## Análisis de los errores encontrados

### 1. Error de `datetime` no definida
**Ubicación**: `src/controller.py`, línea ~380-381
**Error**: `local variable 'datetime' referenced before assignment`
**Causa**: En la creación del fallback para la fase 2, se intenta usar `datetime` pero no está importada en ese scope.

### 2. Error de campo requerido `id_fragmento_origen`
**Error**: `Field required [type=missing, input_value={'id_hecho': 1, ...}, input_type=dict]`
**Causa**: Al crear `HechoProcesado` en el fallback, falta el campo `id_fragmento_origen`.

### 3. Error de formato en logging
**Error**: `KeyError: "'id_hecho'"`
**Causa**: En `logging_config.py`, hay un problema con el formato de string cuando ocurre una excepción durante la creación de hechos fallback.

### 4. Error en modelo `ResultadoFase2Extraccion`
**Error**: `confianza_extraccion - Extra inputs are not permitted`
**Causa**: El modelo `ResultadoFase2Extraccion` no tiene el campo `confianza_extraccion`.

### 5. Error en métricas
**Error**: `KeyError: 'hechos_generados'`
**Causa**: El `processor_stats` usa diferentes nombres de campos que los esperados en el test.

## Soluciones propuestas

### 1. Importar datetime correctamente
En `src/controller.py`, asegurar que `datetime` esté importada al inicio del archivo.

### 2. Corregir creación de HechoProcesado en fallback
Agregar el campo `id_fragmento_origen` al crear los hechos fallback.

### 3. Corregir el formato de logging
En `logging_config.py`, manejar mejor las excepciones durante el formateo.

### 4. Remover campo no existente del test
En el test, no usar `confianza_extraccion` en `ResultadoFase2Extraccion`.

### 5. Ajustar nombres de campos en las métricas
Verificar que los nombres de campos coincidan entre el código y los tests.

## Archivos a modificar

1. `src/controller.py`
2. `src/utils/logging_config.py` 
3. `tests/test_controller_integration.py`
