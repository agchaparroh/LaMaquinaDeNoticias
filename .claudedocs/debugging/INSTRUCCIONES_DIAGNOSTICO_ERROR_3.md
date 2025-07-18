# INSTRUCCIONES PARA DIAGNOSTICAR ERROR 3: NameError 'fragmento'

## RESUMEN EJECUTIVO

**Error**: `name 'fragmento' is not defined` en pipeline_coordinator.py:462
**Impacto**: Pipeline procesa correctamente pero no puede persistir en Supabase
**Síntoma**: Variable 'fragmento' se usa pero no existe en contexto de artículos

## PASOS DE DIAGNÓSTICO OBLIGATORIOS

### PASO 1: Obtener contexto del error
```bash
# Ver líneas alrededor del error
sed -n '440,480p' /path/to/pipeline_coordinator.py

# Buscar todas las referencias a 'fragmento'
grep -n "fragmento" /path/to/pipeline_coordinator.py
```

### PASO 2: Verificar definición de variable
Buscar dónde y cómo se define `fragmento`:
- ¿Está dentro de un if para FragmentoProcesableItem?
- ¿Se define solo en ciertos casos?
- ¿Cuál es su scope?

### PASO 3: Identificar tipo de contenido
Verificar qué tipo de objeto es `contenido`:
- ¿Es ArticuloProcesableItem o FragmentoProcesableItem?
- ¿Cómo se determina esto en el código?

### PASO 4: Revisar método _generar_payload_persistencia
- ¿Qué parámetros espera?
- ¿Puede manejar artículos o solo fragmentos?
- ¿Cuál es su firma?

## HIPÓTESIS PRIORIZADAS

### 🔴 H1: Variable fragmento solo existe para FragmentoProcesableItem (70% probabilidad)
**Verificar**:
- La variable se asigna dentro de `if isinstance(contenido, FragmentoProcesableItem)`
- En línea 462 se usa sin verificar el tipo
- No hay rama else para ArticuloProcesableItem

### 🟡 H6: Refactoring incompleto de fragmentos a artículos (20% probabilidad)
**Verificar**:
- Buscar TODOs o comentarios sobre migración
- Comparar con manejo en otras partes del código
- Ver si hay código legacy mezclado

### 🟢 H7: Método espera siempre fragmento (10% probabilidad)
**Verificar**:
- La firma del método requiere fragmento
- No tiene sobrecarga para artículos

## EVIDENCIA NECESARIA

1. **Código exacto** de líneas 440-480 de pipeline_coordinator.py
2. **Todas las asignaciones** de la variable `fragmento`
3. **Tipo de contenido** en el momento del error
4. **Firma del método** _generar_payload_persistencia

## SOLUCIÓN ESPERADA (NO IMPLEMENTAR AÚN)

Basado en el diagnóstico, la solución probablemente será:
1. Agregar lógica para manejar ArticuloProcesableItem
2. Definir variable apropiada según el tipo
3. Actualizar _generar_payload_persistencia para aceptar ambos tipos

## CHECKLIST DE VERIFICACIÓN

- [ ] Obtuve el código de líneas 440-480
- [ ] Identifiqué todas las referencias a 'fragmento'
- [ ] Confirmé el tipo de 'contenido'
- [ ] Revisé la firma de _generar_payload_persistencia
- [ ] Verifiqué al menos 3 hipótesis
- [ ] Tengo evidencia clara de la causa raíz

## ADVERTENCIA

⚠️ **NO MODIFICAR CÓDIGO** hasta completar TODO el diagnóstico
⚠️ **DOCUMENTAR** cada hallazgo con evidencia
⚠️ **VERIFICAR** múltiples hipótesis, no asumir la primera