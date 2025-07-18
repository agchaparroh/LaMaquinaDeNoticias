# ERROR 3: NameError 'fragmento' en Persistencia - DIAGNÓSTICO COMPLETO

## DESCRIPCIÓN DEL ERROR

### Mensaje de Error:
```
ERROR | req_5ea49311b4ca | PipelineCoordinator | src.pipeline.pipeline_coordinator:ejecutar_pipeline_completo:462 | Error en pipeline: name 'fragmento' is not defined
```

### Contexto:
- **Ubicación**: `src/pipeline/pipeline_coordinator.py`, línea 462
- **Momento**: Al generar payload final para persistencia
- **Impacto**: Pipeline procesa todas las fases correctamente pero falla al persistir

### Comportamiento Observado:
1. Todas las fases del pipeline (1-7) se ejecutan exitosamente
2. Se extraen 48 entidades y 9 hechos correctamente
3. Se detectan 43 relaciones
4. Al intentar generar el payload para persistencia → NameError

## GENERACIÓN DE HIPÓTESIS MÚLTIPLES

### H1: Variable 'fragmento' no definida en flujo de artículos
- El código espera una variable `fragmento` que solo existe cuando se procesan fragmentos
- Al procesar artículos completos, esta variable no se define
- Posible código legacy que asume siempre hay fragmentos

### H2: Confusión entre ArticuloProcesableItem y FragmentoProcesableItem
- El pipeline coordinator no distingue correctamente entre procesamiento de artículos y fragmentos
- Intenta acceder a propiedades de fragmento cuando tiene un artículo

### H3: Error en la lógica condicional del payload generator
- Hay un if/else mal estructurado que no cubre el caso de artículos
- El código cae en una rama que asume fragmentos

### H4: Problema con el tipo de contenido pasado al coordinator
- El tipo de `contenido` no se está identificando correctamente
- El coordinator piensa que está procesando un fragmento cuando es un artículo

### H5: Falta de inicialización de variable en el scope correcto
- La variable `fragmento` se define dentro de un bloque condicional
- Se intenta usar fuera de ese bloque donde no existe

### H6: Error de refactoring incompleto
- Hubo un cambio de arquitectura de fragmentos a artículos
- El código de persistencia no se actualizó completamente

### H7: Problema con el método _generar_payload_persistencia
- El método espera siempre un fragmento como parámetro
- No tiene lógica para manejar artículos directamente

### H8: Mezcla de nomenclaturas en el código
- Algunas partes usan 'articulo', otras 'fragmento'
- En línea 462 se usa la nomenclatura incorrecta

## PLAN DE VERIFICACIÓN SISTEMÁTICA

### Verificación H1: Variable no definida
1. Buscar dónde se define `fragmento` en el archivo
2. Ver si está dentro de un condicional específico para fragmentos
3. Verificar si hay lógica para artículos

### Verificación H2: Confusión de tipos
1. Revisar cómo se determina el tipo de contenido
2. Ver si hay isinstance() checks
3. Buscar dónde se diferencia entre artículo y fragmento

### Verificación H3: Lógica condicional
1. Revisar la estructura if/else alrededor de línea 462
2. Ver todas las ramas posibles
3. Identificar casos no cubiertos

### Verificación H4: Tipo de contenido
1. Rastrear el parámetro `contenido` desde el inicio
2. Ver qué tipo es (ArticuloProcesableItem vs FragmentoProcesableItem)
3. Verificar cómo se usa en el método

### Verificación H5: Scope de variable
1. Buscar todas las asignaciones de `fragmento`
2. Ver el scope donde se definen
3. Verificar dónde se intentan usar

### Verificación H6: Refactoring incompleto
1. Buscar comentarios sobre cambios recientes
2. Ver si hay TODOs relacionados
3. Comparar con versiones anteriores si es posible

### Verificación H7: Método _generar_payload_persistencia
1. Revisar la firma del método
2. Ver qué parámetros espera
3. Verificar si puede manejar artículos

### Verificación H8: Nomenclatura mezclada
1. Buscar todos los usos de 'fragmento' vs 'articulo'
2. Ver si hay inconsistencias
3. Identificar el patrón correcto

## INFORMACIÓN NECESARIA PARA EL DIAGNÓSTICO

### 1. Código alrededor de línea 462
- Las 20 líneas antes y después
- La estructura completa del método

### 2. Definición de la variable fragmento
- Dónde se asigna
- En qué condiciones
- Su scope

### 3. Flujo de datos
- Cómo llega `contenido` al coordinator
- Qué tipo es
- Cómo se transforma

### 4. Método _generar_payload_persistencia
- Firma completa
- Parámetros esperados
- Lógica interna

### 5. Diferenciación artículo/fragmento
- Cómo el código distingue entre ambos
- Qué rutas de código toma cada uno

## DATOS ADICIONALES A RECOPILAR

1. **Logs completos del pipeline** cuando procesa un artículo
2. **Stack trace completo** del error
3. **Tipo exacto** de `contenido` en el momento del error
4. **Valores de variables** en el contexto del error

## CRITERIOS PARA CONFIRMAR HIPÓTESIS

### Para confirmar H1 (más probable):
- Encontrar que `fragmento` solo se define en ramas para FragmentoProcesableItem
- Ver que línea 462 intenta usar `fragmento` sin verificar el tipo

### Para confirmar H6 (segunda más probable):
- Encontrar comentarios o TODOs sobre migración de fragmentos a artículos
- Ver código legacy mezclado con código nuevo

### Para confirmar H7:
- Ver que _generar_payload_persistencia tiene firma rígida
- No acepta artículos como parámetro válido

## NOTAS IMPORTANTES

1. **NO modificar código** hasta completar todas las verificaciones
2. **El error ocurre DESPUÉS** de procesar exitosamente todas las fases
3. **Solo falla** en el paso final de persistencia
4. **El problema es específico** al procesar artículos (no fragmentos)

## COMANDO CLAVE PARA DIAGNÓSTICO

Para obtener el contexto exacto del error:
```bash
grep -n -B 20 -A 20 "fragmento" pipeline_coordinator.py | grep -E "(461|462|463)"
```

Este diagnóstico proporciona un marco completo para identificar la causa raíz sin ejecutar cambios prematuros.