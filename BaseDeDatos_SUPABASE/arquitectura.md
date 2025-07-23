# Schemas JSON - Base de Datos Supabase

## Tabla: hechos (PARTICIONADA)

| Campo | Tipo | Constraints |
|-------|------|-------------|
| id | bigint | PRIMARY KEY, NOT NULL |
| contenido | text | NOT NULL |
| fecha_ocurrencia | tstzrange | NOT NULL |
| precision_temporal | enum | NOT NULL, CHECK: exacta\|dia\|semana\|mes\|trimestre\|año\|decada\|periodo\|desconocido |
| importancia | integer | NOT NULL, CHECK: 1-10 |
| tipo_hecho | enum | NOT NULL, CHECK: SUCESO\|ANUNCIO\|DECLARACION\|BIOGRAFIA\|CONCEPTO\|NORMATIVA\|EVENTO |
| pais | array | NOT NULL |
| region | array | |
| ciudad | array | |
| evaluacion_editorial | enum | CHECK: pendiente_revision_editorial\|verificado_ok_editorial\|declarado_falso_editorial |
| consenso_fuentes | enum | CHECK: pendiente_analisis_fuentes\|confirmado_multiples_fuentes\|sin_confirmacion_suficiente_fuentes\|en_disputa_por_hechos_contradictorios |
| estado_programacion | enum | CHECK: programado\|confirmado\|cancelado\|modificado\|realizado\|NULL |
| confiabilidad_programacion | integer | CHECK: 1-5 |
| etiquetas | array | |
| fecha_ingreso | timestamptz | NOT NULL |
| documento_id | bigint | FOREIGN KEY |
| fragmento_id | bigint | FOREIGN KEY |

## Tabla: entidades

| Campo | Tipo | Constraints |
|-------|------|-------------|
| id | bigint | PRIMARY KEY, NOT NULL |
| nombre | text | NOT NULL |
| tipo | text | NOT NULL |
| descripcion | text | |
| alias | array | |
| relevancia | integer | NOT NULL, CHECK: 1-10 |
| metadata | jsonb | |
| fusionada_en_id | bigint | FOREIGN KEY |

## Tabla: articulos

| Campo | Tipo | Constraints |
|-------|------|-------------|
| id | bigint | PRIMARY KEY, NOT NULL |
| storage_path | text | NOT NULL, UNIQUE, CHECK: formato específico |
| url | text | UNIQUE |
| medio | text | NOT NULL |
| tipo_medio | text | NOT NULL |
| titular | text | NOT NULL |
| fecha_publicacion | timestamptz | NOT NULL |
| autor | text | |
| pais_publicacion | text | |
| idioma | text | NOT NULL |
| es_opinion | boolean | NOT NULL |
| es_oficial | boolean | NOT NULL |
| fecha_recopilacion | timestamptz | NOT NULL |
| puntuacion_relevancia | integer | CHECK: 0-10 |
| area_geografica | text | NOT NULL |
| resumen | text | |
| categorias_asignadas | array | |
| estado_procesamiento | text | |
| fecha_procesamiento | timestamptz | |
| error_detalle | text | |

## Tabla: citas_textuales

| Campo | Tipo | Constraints |
|-------|------|-------------|
| id | bigint | PRIMARY KEY, NOT NULL |
| cita | text | NOT NULL |
| entidad_emisora_id | bigint | FOREIGN KEY |
| articulo_id | bigint | FOREIGN KEY |
| documento_id | bigint | FOREIGN KEY |
| fragmento_id | bigint | FOREIGN KEY |
| hecho_contexto_id | bigint | |
| fecha_cita | timestamptz | |
| contexto | text | |
| relevancia | integer | NOT NULL, CHECK: 1-5 |
| fecha_ingreso | timestamptz | NOT NULL |

## Tabla: datos_cuantitativos

| Campo | Tipo | Constraints |
|-------|------|-------------|
| id | bigint | PRIMARY KEY, NOT NULL |
| hecho_id | bigint | |
| articulo_id | bigint | FOREIGN KEY |
| documento_id | bigint | FOREIGN KEY |
| fragmento_id | bigint | FOREIGN KEY |
| indicador | text | NOT NULL |
| categoria | enum | NOT NULL, CHECK: económico\|demográfico\|electoral\|social\|presupuestario\|sanitario\|ambiental\|conflicto\|otro |
| valor_numerico | numeric | NOT NULL |
| unidad | text | NOT NULL |
| ambito_geografico | array | NOT NULL |
| periodo_referencia_inicio | date | |
| periodo_referencia_fin | date | |
| tipo_periodo | enum | CHECK: anual\|trimestral\|mensual\|semanal\|diario\|puntual\|acumulado\|NULL |
| tendencia | enum | CHECK: aumento\|disminución\|estable\|NULL |
| fecha_registro | timestamptz | NOT NULL |

## Tabla: contradicciones

| Campo | Tipo | Constraints |
|-------|------|-------------|
| id | bigint | PRIMARY KEY, NOT NULL |
| hecho_principal_id | bigint | NOT NULL |
| fecha_ocurrencia_principal | tstzrange | NOT NULL |
| hecho_contradictorio_id | bigint | NOT NULL |
| fecha_ocurrencia_contradictoria | tstzrange | NOT NULL |
| tipo_contradiccion | enum | NOT NULL, CHECK: fecha\|contenido\|entidades\|ubicacion\|valor\|completa |
| grado_contradiccion | integer | NOT NULL, CHECK: 1-5 |
| descripcion | text | |
| estado_resolucion | enum | CHECK: pendiente\|analizada\|resuelta\|ignorada |
| fecha_deteccion | timestamptz | NOT NULL |

**Constraint adicional**: CHECK hechos diferentes (hecho_principal_id ≠ hecho_contradictorio_id OR fecha_ocurrencia_principal ≠ fecha_ocurrencia_contradictoria)

## Tabla: hecho_entidad

| Campo | Tipo | Constraints |
|-------|------|-------------|
| hecho_id | bigint | NOT NULL, parte de PRIMARY KEY |
| fecha_ocurrencia_hecho | tstzrange | NOT NULL, parte de PRIMARY KEY |
| entidad_id | bigint | NOT NULL, FOREIGN KEY, parte de PRIMARY KEY |
| tipo_relacion | enum | NOT NULL, CHECK: protagonista\|mencionado\|afectado\|declarante\|ubicacion\|contexto\|victima\|agresor\|organizador\|participante\|otro, parte de PRIMARY KEY |
| relevancia_en_hecho | integer | NOT NULL, CHECK: 1-10 |

## Tabla: entidad_relacion

| Campo | Tipo | Constraints |
|-------|------|-------------|
| entidad_origen_id | bigint | NOT NULL, FOREIGN KEY, parte de PRIMARY KEY |
| entidad_destino_id | bigint | NOT NULL, FOREIGN KEY, parte de PRIMARY KEY |
| tipo_relacion | enum | NOT NULL, CHECK: miembro_de\|subsidiaria_de\|aliado_con\|opositor_a\|sucesor_de\|predecesor_de\|casado_con\|familiar_de\|empleado_de, parte de PRIMARY KEY |
| descripcion | text | |
| fuerza_relacion | integer | NOT NULL, CHECK: 1-10 |

**Constraint adicional**: CHECK entidades diferentes (entidad_origen_id ≠ entidad_destino_id)

## Tabla: hecho_articulo

| Campo | Tipo | Constraints |
|-------|------|-------------|
| hecho_id | bigint | NOT NULL, parte de PRIMARY KEY |
| fecha_ocurrencia_hecho | tstzrange | NOT NULL, parte de PRIMARY KEY |
| articulo_id | bigint | NOT NULL, FOREIGN KEY, parte de PRIMARY KEY |
| es_fuente_primaria | boolean | NOT NULL |
| confirma_hecho | boolean | NOT NULL |

## Tabla: hecho_relacionado

| Campo | Tipo | Constraints |
|-------|------|-------------|
| hecho_origen_id | bigint | NOT NULL, parte de PRIMARY KEY |
| fecha_ocurrencia_origen | tstzrange | NOT NULL, parte de PRIMARY KEY |
| hecho_destino_id | bigint | NOT NULL, parte de PRIMARY KEY |
| fecha_ocurrencia_destino | tstzrange | NOT NULL, parte de PRIMARY KEY |
| tipo_relacion | enum | NOT NULL, CHECK: causa\|consecuencia\|contexto_historico\|respuesta_a\|aclaracion_de\|version_alternativa\|seguimiento_de, parte de PRIMARY KEY |
| fuerza_relacion | integer | NOT NULL, CHECK: 1-10 |
| descripcion_relacion | text | |

**Constraint adicional**: CHECK hechos diferentes (hecho_origen_id ≠ hecho_destino_id OR fecha_ocurrencia_origen ≠ fecha_ocurrencia_destino)