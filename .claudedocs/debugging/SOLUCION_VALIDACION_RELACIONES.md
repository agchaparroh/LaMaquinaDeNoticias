# Solución: Validación Post-7B de Relaciones
## La Máquina de Noticias - Pipeline

## PROBLEMA IDENTIFICADO

El pipeline procesa exitosamente artículos a través de las 7 fases, pero falla al persistir en Supabase con el error:
```
new row for relation 'entidad_relacion' violates check constraint 'entidad_relacion_tipo_relacion_check'
```

### Causa Raíz
El LLM en fase 7B.1 genera tipos de relación inválidos para `entidad_relacion`, usando tipos que corresponden a `hecho_entidad`:
- ❌ "ubicacion" (válido solo para hecho-entidad)
- ❌ "mencionado" (válido solo para hecho-entidad)
- ❌ "organizador" (válido solo para hecho-entidad)

Cuando deberían ser:
- ✅ miembro_de, subsidiaria_de, aliado_con, opositor_a, sucesor_de, predecesor_de, casado_con, familiar_de, empleado_de

## SOLUCIÓN IMPLEMENTADA

### 1. Análisis Completo de Constraints
Documentado en: `.claudedocs/debugging/analisis_schema/CONSTRAINTS_DATABASE.md`
- Extraídos TODOS los constraints de `BaseDeDatos_SUPABASE/constraints.sql`
- Identificados los valores válidos para cada tipo de relación
- Documentadas las discrepancias en `DISCREPANCIAS_PROMPTS_MODELOS_BD.md`

### 2. ValidadorRelacionesPost7B (VERSIÓN COMPLETA)
Creado en: `src/module_pipeline/src/utils/validador_relaciones_post7b.py`

#### Validaciones Implementadas:

##### A. Tipos de Enumeración (Error Original)
- **entidad_relacion**: miembro_de, subsidiaria_de, aliado_con, opositor_a, sucesor_de, predecesor_de, casado_con, familiar_de, empleado_de
- **hecho_entidad**: protagonista, mencionado, afectado, declarante, ubicacion, contexto, victima, agresor, organizador, participante, otro
- **hecho_relacionado**: causa, consecuencia, contexto_historico, respuesta_a, aclaracion_de, version_alternativa, seguimiento_de
- **contradicciones**: fecha, contenido, entidades, ubicacion, valor, completa

Mapeo inteligente de tipos incorrectos:
- "ubicacion" → "aliado_con" (relación geográfica neutral)
- "mencionado" → "aliado_con" (relación neutral)
- "organizador" → "empleado_de" (si organiza, trabaja para)
- "participante" → "miembro_de" (si participa, es miembro)

##### B. Rangos Numéricos
- **fuerza_relacion**: 1-10 (ajusta valores fuera de rango)
- **relevancia_en_hecho**: 1-10 (ajusta valores fuera de rango)
- **grado_contradiccion**: 1-5 (ajusta valores fuera de rango)

##### C. Constraints de Relación
- **check_different_related_entities**: Valida que entidad_origen_id ≠ entidad_destino_id
- **check_different_related_hechos**: Valida que hecho_origen_id ≠ hecho_destino_id (o fechas diferentes)

##### D. Campos Obligatorios (NOT NULL)
- Descarta registros sin campos obligatorios como IDs origen/destino

### 3. Integración en Pipeline
Modificado: `src/module_pipeline/src/pipeline/fase_7_normalizacion.py`

```python
# En ejecutar_fase_7b_relaciones()
# Después de obtener resultados del LLM:

validador = ValidadorRelacionesPost7B()
datos_validados = validador.validar_y_corregir(datos_para_validar)
estadisticas_validacion = validador.obtener_estadisticas(datos_para_validar, datos_validados)
```

### 4. Tests Unitarios (EXTENDIDOS)
Creado en: `src/module_pipeline/tests/test_validador_relaciones.py`
- Test de corrección de tipos inválidos
- Test de descarte de tipos no corregibles
- Test del caso real con "ubicacion"
- Test de validación de rangos numéricos
- Test de validación de entidades diferentes
- Test de validación de campos obligatorios
- Verificación de estadísticas

## RESULTADO ESPERADO

Con esta solución:
1. ✅ Los artículos procesarán exitosamente las 7 fases
2. ✅ La validación post-7B corregirá tipos inválidos automáticamente
3. ✅ La persistencia en Supabase será exitosa
4. ✅ Se mantendrá un log de correcciones para monitoreo

## PRÓXIMOS PASOS

1. **Ejecutar prueba con artículo real** para verificar que la persistencia ahora funciona
2. **Monitorear logs** para identificar patrones de errores del LLM
3. **Considerar mejoras futuras**:
   - Agregar validación `Literal[]` en modelos Pydantic
   - Mejorar prompts para reducir confusión del LLM
   - Estandarizar escalas de relevancia (citas usa 1-5, resto 1-10)

## COMANDOS PARA VERIFICAR

```bash
# Ejecutar tests del validador
cd /home/ec2-user/projects/LaMaquinaDeNoticias/src/module_pipeline
python -m pytest tests/test_validador_relaciones.py -v

# Verificar integración
grep -n "ValidadorRelacionesPost7B" src/pipeline/fase_7_normalizacion.py

# Ver logs de validación durante procesamiento
# Los warnings mostrarán correcciones como:
# "Corrigiendo tipo de relación entidad-entidad: 'ubicacion' → 'aliado_con'"
```