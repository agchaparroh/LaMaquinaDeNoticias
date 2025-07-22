# Mapeo de Campos RPC → Tablas Supabase

## ENTIDADES
**Tabla: `entidades`**

| Campo Actual en RPC | Campo en Tabla | Cambiar? |
|-------------------|----------------|----------|
| `nombre_entidad` | `nombre` | ✅ SÍ |
| `tipo_entidad` | `tipo` | ✅ SÍ |
| `descripcion_entidad` | `descripcion` | ✅ SÍ |
| `alias` | `alias` | ✅ OK |
| `relevancia_entidad` | `relevancia` | ✅ SÍ |
| `metadata_entidad` | `metadata` | ✅ SÍ |
| `id_temporal_entidad` | - | Interno |
| `id_entidad_normalizada` | - | Interno |

## HECHOS
**Tabla: `hechos`**

| Campo Actual en RPC | Campo en Tabla | Cambiar? |
|-------------------|----------------|----------|
| `descripcion_hecho` | `contenido` | ✅ SÍ |
| `tipo_hecho` | `tipo_hecho` | ✅ OK |
| `relevancia_hecho` | `importancia` | ✅ SÍ |
| `precision_temporal` | `precision_temporal` | ✅ OK |
| `fecha_ocurrencia_hecho_inicio` | - | Construye `fecha_ocurrencia` |
| `fecha_ocurrencia_hecho_fin` | - | Construye `fecha_ocurrencia` |
| `metadata_hecho.pais` | `pais` | ✅ OK |
| `metadata_hecho.region` | `region` | ✅ OK |
| `metadata_hecho.ciudad` | `ciudad` | ✅ OK |
| `metadata_hecho.etiquetas` | `etiquetas` | ✅ OK |
| `id_temporal_hecho` | - | Interno |

## CITAS TEXTUALES
**Tabla: `citas_textuales`**

| Campo Actual en RPC | Campo en Tabla | Cambiar? |
|-------------------|----------------|----------|
| `texto_cita` | `cita` | ✅ SÍ |
| `contexto_cita` | `contexto` | ✅ SÍ |
| `relevancia_cita` | `relevancia` | ✅ SÍ |
| `fecha_cita` | `fecha_cita` | ✅ OK |
| `id_temporal_entidad_emisora` | - | Mapea a `entidad_emisora_id` |
| `id_temporal_hecho_principal` | - | Mapea a `hecho_contexto_id` |

## DATOS CUANTITATIVOS
**Tabla: `datos_cuantitativos`**

| Campo Actual en RPC | Campo en Tabla | Cambiar? |
|-------------------|----------------|----------|
| `indicador_dato` | `indicador` | ✅ SÍ |
| `categoria_dato` | `categoria` | ✅ SÍ |
| `valor_dato` | `valor_numerico` | ✅ SÍ |
| `unidad_dato` | `unidad` | ✅ SÍ |
| `tendencia_dato` | `tendencia` | ✅ SÍ |
| `ambito_geografico` | `ambito_geografico` | ✅ OK |
| `periodo_inicio` | `periodo_referencia_inicio` | ✅ OK |
| `periodo_fin` | `periodo_referencia_fin` | ✅ OK |
| `id_temporal_hecho_principal` | - | Mapea a `hecho_id` |

## ARTICULOS (Update)
**Tabla: `articulos`**

| Campo Actual en RPC | Campo en Tabla | Cambiar? |
|-------------------|----------------|----------|
| `resumen_generado_pipeline` | `resumen` | ✅ SÍ |
| `categorias_asignadas_ia` | `categorias_asignadas` | ✅ SÍ |
| `score_relevancia` | `puntuacion_relevancia` | ✅ SÍ |
| `area_geografica` | `area_geografica` | ✅ OK |

## RELACIONES

### entidad_relacion
| Campo Actual en RPC | Campo en Tabla | Cambiar? |
|-------------------|----------------|----------|
| `descripcion_relacion` | `descripcion` | ✅ SÍ |
| `fuerza_relacion` | `fuerza_relacion` | ✅ OK |
| `tipo_relacion` | `tipo_relacion` | ✅ OK |

### contradicciones
| Campo Actual en RPC | Campo en Tabla | Cambiar? |
|-------------------|----------------|----------|
| `descripcion_contradiccion` | `descripcion` | ✅ SÍ |
| `grado_contradiccion` | `grado_contradiccion` | ✅ OK |
| `tipo_contradiccion` | `tipo_contradiccion` | ✅ OK |

## Resumen de cambios necesarios:
1. Eliminar sufijos redundantes (_entidad, _hecho, _cita, _dato)
2. Usar nombres que coincidan directamente con columnas
3. Mantener coherencia: si la columna se llama `contenido`, el JSON debe usar `contenido`