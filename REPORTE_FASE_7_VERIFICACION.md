# Reporte de Verificación - Fase 7 (Normalización)

## Análisis de la Fase 7

La Fase 7 tiene dos subfases:

### 7A - Normalización de Entidades
- NO genera nuevos datos
- Solo actualiza campos existentes en `EntidadProcesada`:
  - `id_entidad_normalizada`
  - `nombre_entidad_normalizada`
  - `uri_wikidata`
  - `similitud_normalizacion`

### 7B - Detección de Relaciones
- 7B.1: Relaciones Estructurales (prompt genera `hecho_entidad` y `entidad_relacion`)
- 7B.2: Relaciones Temporales (prompt genera `hecho_relacionado` y `contradicciones`)

## Problema Identificado

**NO existen modelos Pydantic en `procesamiento.py` para las relaciones de la Fase 7B**.

Las relaciones se manejan como diccionarios y van directamente a los modelos de `persistencia.py`.

## Verificación de Modelos de Persistencia vs BD

### Tabla: hecho_entidad

BD arquitectura.md:
```
| hecho_id | bigint | NOT NULL, parte de PRIMARY KEY |
| fecha_ocurrencia_hecho | tstzrange | NOT NULL, parte de PRIMARY KEY |
| entidad_id | bigint | NOT NULL, FOREIGN KEY, parte de PRIMARY KEY |
| tipo_relacion | enum | NOT NULL, CHECK: protagonista|mencionado|afectado|declarante|ubicacion|contexto|victima|agresor|organizador|participante|otro, parte de PRIMARY KEY |
| relevancia_en_hecho | integer | NOT NULL, CHECK: 1-10 |
```

Prompt 7B.1 genera:
```json
{
  "hecho_id": 0,
  "entidad_id": 0,
  "tipo_relacion": "",
  "relevancia_en_hecho": 5
}
```

**PROBLEMA**: Falta `fecha_ocurrencia_hecho` en el prompt

### Tabla: entidad_relacion

BD arquitectura.md:
```
| entidad_origen_id | bigint | NOT NULL, FOREIGN KEY, parte de PRIMARY KEY |
| entidad_destino_id | bigint | NOT NULL, FOREIGN KEY, parte de PRIMARY KEY |
| tipo_relacion | enum | NOT NULL, CHECK: miembro_de|subsidiaria_de|aliado_con|opositor_a|sucesor_de|predecesor_de|casado_con|familiar_de|empleado_de, parte de PRIMARY KEY |
| descripcion | text | |
| fuerza_relacion | integer | NOT NULL, CHECK: 1-10 |
```

Prompt 7B.1 genera:
```json
{
  "entidad_origen_id": 0,
  "entidad_destino_id": 0,
  "tipo_relacion": "",
  "descripcion": "",
  "fecha_inicio": null,
  "fecha_fin": null,
  "fuerza_relacion": 5
}
```

**PROBLEMA**: El prompt incluye `fecha_inicio` y `fecha_fin` que NO existen en la BD

### Tabla: hecho_relacionado

BD arquitectura.md:
```
| hecho_origen_id | bigint | NOT NULL, parte de PRIMARY KEY |
| fecha_ocurrencia_origen | tstzrange | NOT NULL, parte de PRIMARY KEY |
| hecho_destino_id | bigint | NOT NULL, parte de PRIMARY KEY |
| fecha_ocurrencia_destino | tstzrange | NOT NULL, parte de PRIMARY KEY |
| tipo_relacion | enum | NOT NULL, CHECK: causa|consecuencia|contexto_historico|respuesta_a|aclaracion_de|version_alternativa|seguimiento_de, parte de PRIMARY KEY |
| fuerza_relacion | integer | NOT NULL, CHECK: 1-10 |
| descripcion_relacion | text | |
```

Prompt 7B.2 genera:
```json
{
  "hecho_origen_id": 0,
  "hecho_destino_id": 0,
  "tipo_relacion": "",
  "fuerza_relacion": 5,
  "descripcion_relacion": ""
}
```

**PROBLEMA**: Faltan `fecha_ocurrencia_origen` y `fecha_ocurrencia_destino`

### Tabla: contradicciones

BD arquitectura.md:
```
| hecho_principal_id | bigint | NOT NULL |
| fecha_ocurrencia_principal | tstzrange | NOT NULL |
| hecho_contradictorio_id | bigint | NOT NULL |
| fecha_ocurrencia_contradictoria | tstzrange | NOT NULL |
| tipo_contradiccion | enum | NOT NULL, CHECK: fecha|contenido|entidades|ubicacion|valor|completa |
| grado_contradiccion | integer | NOT NULL, CHECK: 1-5 |
| descripcion | text | |
| estado_resolucion | enum | CHECK: pendiente|analizada|resuelta|ignorada |
| fecha_deteccion | timestamptz | NOT NULL |
```

Prompt 7B.2 genera:
```json
{
  "hecho_principal_id": 0,
  "hecho_contradictorio_id": 0,
  "tipo_contradiccion": "",
  "grado_contradiccion": 3,
  "descripcion": ""
}
```

**PROBLEMA**: Faltan `fecha_ocurrencia_principal`, `fecha_ocurrencia_contradictoria`, `estado_resolucion` y `fecha_deteccion`

## Resumen de Problemas

1. **No hay modelos Pydantic en procesamiento.py para las relaciones**
2. **Los prompts NO generan todos los campos requeridos por la BD**:
   - Falta información de fechas de ocurrencia en todas las relaciones de hechos
   - El prompt de entidad_relacion genera campos que no existen en BD
   - Faltan campos obligatorios como estado_resolucion y fecha_deteccion en contradicciones

## Recomendaciones

1. Crear modelos Pydantic en `procesamiento.py` para:
   - `HechoEntidadRelacion`
   - `EntidadEntidadRelacion`
   - `HechoHechoRelacion`
   - `ContradiccionDetectada`

2. Actualizar los prompts 7B.1 y 7B.2 para:
   - Eliminar campos que no existen en BD
   - NO solicitar campos que el LLM no puede generar (como fechas de ocurrencia que vienen de otros datos)

3. La lógica de procesamiento debe:
   - Completar los campos faltantes desde los datos de hechos/entidades
   - Agregar valores por defecto para campos como estado_resolucion