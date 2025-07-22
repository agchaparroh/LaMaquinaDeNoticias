# INVENTARIO DE MISMATCHES EN SCHEMAS DE RELACIONES
*Fecha: 2025-07-21*
*Actualizado: 2025-07-21 - Verificación con archivos reales*

## RESUMEN EJECUTIVO

Este documento identifica TODOS los mismatches **CONFIRMADOS** entre:
1. Los modelos Pydantic en `persistencia.py`
2. Lo que espera el RPC `actualizar_articulo_procesado.sql`
3. Lo que se genera en el pipeline
4. Los tipos permitidos en prompts vs BD

## 1. RELACIÓN HECHO_ENTIDAD (entidades_del_hecho)

### 1.1 MISMATCH DE CAMPO ID ✅ CONFIRMADO
| Componente | Campo actual | Campo esperado |
|------------|--------------|----------------|
| Modelo `EntidadEnHechoItem` (línea 21) | `id_temporal_entidad` | Debe ser `id_temporal` |
| RPC busca (línea 233) | `id_temporal` | ✅ Correcto |
| pipeline_coordinator.py (línea 848) | `id_temporal_entidad` | Usa el campo del modelo |

### 1.2 CAMPOS NO UTILIZADOS ✅ CONFIRMADO
El modelo `EntidadEnHechoItem` define campos que el RPC NO usa:
- `nombre_entidad` (línea 22) - NO usado por RPC
- `tipo_entidad` (línea 23) - NO usado por RPC  
- `rol_en_hecho` (línea 24) - NO usado por RPC

El RPC solo usa: `id_temporal`, `tipo_relacion`, `relevancia_en_hecho`

### 1.3 FLUJO ROTO ✅ CONFIRMADO
- Las relaciones se detectan en Fase 7B.1 pero NO se asignan a `vinculado_a_entidades`
- `pipeline_coordinator.py` (líneas 846-853) genera datos hardcodeados:
  - `nombre`: "Entidad_{ent_id}"
  - `tipo`: "MENCIONADA"
  - `rol_en_hecho`: "relacionada"
- Se pierde información crítica (tipo real de relación, relevancia real)

## 2. RELACIÓN HECHO_RELACIONADO

### 2.1 MISMATCH DE CAMPOS ID ✅ CONFIRMADO
| Componente | Campo actual | Campo esperado por RPC |
|------------|--------------|------------------------|
| Modelo `RelacionHechosItem` (línea 136) | `hecho_origen_id_temporal` | RPC busca `id_hecho_origen` |
| Modelo `RelacionHechosItem` (línea 137) | `hecho_destino_id_temporal` | RPC busca `id_hecho_destino` |
| RPC (líneas 367-368) | - | `id_hecho_origen`, `id_hecho_destino` |

### 2.2 TIPOS DE RELACIÓN ✅ CONFIRMADO (en descripción del modelo línea 138)
| Modelo define | BD/Prompt esperan |
|--------------|-------------------|
| `causa-efecto` | `causa` |
| `temporal_secuencial` | `seguimiento_de` |
| `aclaracion` | `aclaracion_de` |

BD acepta: `causa`, `consecuencia`, `contexto_historico`, `respuesta_a`, `aclaracion_de`, `version_alternativa`, `seguimiento_de`

### 2.3 TODO NO IMPLEMENTADO ✅ CONFIRMADO
```python
# pipeline_coordinator.py línea 941
relaciones_hechos=None,  # TODO: Implementar cuando estén disponibles
```
Las relaciones ESTÁN disponibles en `resultado_fase7.metadata_normalizacion` pero nunca se extraen.

## 3. RELACIÓN ENTIDAD_RELACION

### 3.1 MISMATCH DE CAMPOS ID ✅ CONFIRMADO
| Componente | Campo actual | Campo esperado por RPC |
|------------|--------------|------------------------|
| Modelo `RelacionEntidadesItem` (línea 150) | `entidad_origen_id_temporal` | RPC busca `id_entidad_origen` |
| Modelo `RelacionEntidadesItem` (línea 151) | `entidad_destino_id_temporal` | RPC busca `id_entidad_destino` |
| RPC (líneas 414-415) | - | `id_entidad_origen`, `id_entidad_destino` |

### 3.2 MISMATCH DE CAMPO DESCRIPCIÓN ✅ CONFIRMADO
| Componente | Campo | Nota |
|------------|-------|------|
| Modelo define (línea 153) | `descripcion_relacion` | ✅ |
| RPC busca (línea 431) | `descripcion` | Sin sufijo "_relacion" |
| BD inserta en | `descripcion` | ✅ |

### 3.3 CAMPOS NO PROCESADOS ✅ CONFIRMADO
El modelo define pero RPC NO procesa:
- `fecha_inicio_relacion` (línea 155)
- `fecha_fin_relacion` (línea 156)
- `contexto_relacion` (línea 154)

### 3.4 TODO NO IMPLEMENTADO ✅ CONFIRMADO
```python
# pipeline_coordinator.py línea 942
relaciones_entidades=None,  # TODO: Implementar cuando estén disponibles
```

## 4. CONTRADICCIONES

### 4.1 MISMATCH DE CAMPOS ID ✅ CONFIRMADO
| Componente | Campo actual | Campo esperado por RPC |
|------------|--------------|------------------------|
| Modelo `ContradiccionDetectadaItem` (línea 164) | `hecho_principal_id_temporal` | RPC busca `id_hecho_principal` |
| Modelo `ContradiccionDetectadaItem` (línea 165) | `hecho_contradictorio_id_temporal` | RPC busca `id_hecho_contradictorio` |
| RPC (líneas 454-455) | - | `id_hecho_principal`, `id_hecho_contradictorio` |

### 4.2 MISMATCH DE CAMPO DESCRIPCIÓN ✅ CONFIRMADO
| Componente | Campo | Nota |
|------------|-------|------|
| Modelo define (línea 168) | `descripcion_contradiccion` | ✅ |
| RPC busca (línea 482) | `descripcion` | Sin sufijo "_contradiccion" |
| BD inserta en | `descripcion` | ✅ |

### 4.3 TIPOS DE CONTRADICCIÓN ✅ CONFIRMADO (en descripción del modelo línea 166)
| Modelo define | BD/Prompt esperan |
|--------------|-------------------|
| `temporal` | `fecha` |
| `logica` | `contenido` |
| `factual` | `valor` |

BD acepta: `fecha`, `contenido`, `entidades`, `ubicacion`, `valor`, `completa`

### 4.4 TODO NO IMPLEMENTADO ✅ CONFIRMADO
```python
# pipeline_coordinator.py línea 943
contradicciones_detectadas=None  # TODO: Implementar cuando estén disponibles
```

## 5. RESUMEN DE ACCIONES REQUERIDAS

### 5.1 Cambios en Modelos (persistencia.py)
1. **EntidadEnHechoItem**: Cambiar `id_temporal_entidad` → `id_temporal`
2. **RelacionHechosItem**: Cambiar campos de ID para quitar sufijo `_temporal`
3. **RelacionEntidadesItem**: Cambiar campos de ID para quitar sufijo `_temporal`
4. **ContradiccionDetectadaItem**: Cambiar campos de ID para quitar sufijo `_temporal`

### 5.2 Cambios en campos de descripción
1. **RelacionEntidadesItem**: `descripcion_relacion` → `descripcion`
2. **ContradiccionDetectadaItem**: `descripcion_contradiccion` → `descripcion`

### 5.3 Implementar TODOs en pipeline_coordinator.py (líneas 941-943)
1. Extraer relaciones de `resultado_fase7.metadata_normalizacion`
2. Implementar asignación de relaciones hecho_entidad a `vinculado_a_entidades`

### 5.4 Mapeo de Tipos
1. Crear funciones de mapeo para tipos de relación hecho-hecho
2. Crear funciones de mapeo para tipos de contradicción

### 5.5 Alternativa: Modificar RPC
En lugar de cambiar los modelos, se podría modificar el RPC para buscar los campos con los nombres actuales, pero esto requeriría cambios en la función SQL de Supabase.

## 6. IMPACTO ACTUAL ✅ CONFIRMADO

**TODAS las tablas de relaciones están VACÍAS** en producción debido a:
1. TODOs no implementados en pipeline_coordinator.py
2. Mismatches de nombres de campos entre modelos y RPC
3. Flujo roto de asignación de relaciones hecho_entidad

Esto representa una pérdida total de información relacional que el sistema detecta correctamente pero nunca persiste.