# ESPECIFICACIÓN: Función RPC insertar_articulo_completo

## FUNCIÓN
```sql
CREATE OR REPLACE FUNCTION insertar_articulo_completo(datos_json JSONB)
```

## PARÁMETRO ESPERADO
Un único objeto JSON con la siguiente estructura:

```json
{
  "articulo_metadata": {
    "url": "string",
    "storage_path": "string con formato: {medio}/{año}/{mes}/{dia}/{hash}.{ext}.gz",
    "medio": "string",
    "area_geografica": "string", 
    "tipo_medio": "string",
    "titular": "string",
    "fecha_publicacion": "timestamptz",
    "autor": "string",
    "idioma": "string",
    "seccion": "string",
    "etiquetas_fuente": ["array", "de", "strings"],
    "es_opinion": boolean,
    "es_oficial": boolean,
    "resumen": "string",
    "categorias_asignadas": ["array", "de", "strings"],
    "puntuacion_relevancia": integer,
    "fecha_recopilacion": "timestamptz"
  },
  "entidades": [
    {
      "id": "string",
      "nombre": "string",
      "tipo": "string",
      "descripcion": "string",
      "alias": ["array", "de", "strings"],
      "db_id": bigint,
      "fecha_nacimiento": "tstzrange",
      "fecha_disolucion": "tstzrange",
      "relevancia": integer,
      "metadata": {}
    }
  ],
  "hechos": [
    {
      "id": "string",
      "contenido": "string",
      "fecha": {
        "inicio": "timestamptz",
        "fin": "timestamptz"
      },
      "precision_temporal": "string",
      "tipo_hecho": "string",
      "pais": ["array", "de", "strings"],
      "region": ["array", "de", "strings"],
      "ciudad": ["array", "de", "strings"],
      "etiquetas": ["array", "de", "strings"],
      "es_futuro": boolean,
      "estado_programacion": "string",
      "importancia": integer
    }
  ],
  "citas_textuales": [
    {
      "cita": "string",
      "entidad_id": "string",
      "hecho_id": "string",
      "fecha": "timestamptz",
      "contexto": "string",
      "relevancia": integer
    }
  ],
  "datos_cuantitativos": [
    {
      "hecho_id": "string",
      "indicador": "string",
      "categoria": "string",
      "valor": numeric,
      "unidad": "string",
      "ambito_geografico": ["array", "de", "strings"],
      "periodo": {
        "inicio": "date",
        "fin": "date"
      },
      "tipo_periodo": "string",
      "valor_anterior": numeric,
      "variacion_absoluta": numeric,
      "variacion_porcentual": numeric,
      "tendencia": "string"
    }
  ],
  "relaciones": {
    "hecho_entidad": [
      {
        "hecho_id": "string",
        "entidad_id": "string",
        "tipo_relacion": "string",
        "relevancia_en_hecho": integer
      }
    ],
    "hecho_relacionado": [
      {
        "hecho_origen_id": "string",
        "hecho_destino_id": "string",
        "tipo_relacion": "string",
        "fuerza_relacion": integer,
        "descripcion_relacion": "string"
      }
    ],
    "entidad_relacion": [
      {
        "entidad_origen_id": "string",
        "entidad_destino_id": "string",
        "tipo_relacion": "string",
        "descripcion": "string",
        "fecha_inicio": "timestamptz",
        "fecha_fin": "timestamptz",
        "fuerza_relacion": integer
      }
    ],
    "contradicciones": [
      {
        "hecho_principal_id": "string",
        "hecho_contradictorio_id": "string",
        "tipo_contradiccion": "string",
        "grado_contradiccion": integer,
        "descripcion": "string"
      }
    ]
  },
  "posibles_duplicados": {
    "{id_temporal_hecho}": [array_de_ids_existentes]
  }
}
```

## VALIDACIONES EN LA FUNCIÓN

1. **storage_path**: Debe cumplir con el patrón regex:
   ```
   ^[^/]+/\d{4}/\d{2}/\d{2}/[^/]+\.(html|txt)\.gz$
   ```

2. **Acceso a campos**: La función accede a los campos usando:
   - `datos_json->'articulo_metadata'->>'campo'`
   - `datos_json->'entidades'`
   - `datos_json->'hechos'`
   - `datos_json->'citas_textuales'`
   - `datos_json->'datos_cuantitativos'`
   - `datos_json->'relaciones'->'hecho_entidad'`
   - `datos_json->'relaciones'->'hecho_relacionado'`
   - `datos_json->'relaciones'->'entidad_relacion'`
   - `datos_json->'relaciones'->'contradicciones'`
   - `datos_json->'posibles_duplicados'`

## RESPUESTA DE LA FUNCIÓN

En caso de éxito:
```json
{
  "status": "exito",
  "articulo_id": bigint,
  "num_hechos_insertados": integer,
  "num_entidades_procesadas": integer,
  "num_entidades_nuevas": integer,
  "num_citas_insertadas": integer,
  "num_datos_insertados": integer,
  "num_rel_he_insertadas": integer,
  "num_rel_hh_insertadas": integer,
  "num_rel_ee_insertadas": integer,
  "num_contradicciones_insertadas": integer,
  "num_duplicados_registrados": integer
}
```

En caso de error:
```json
{
  "status": "error",
  "mensaje": "string con descripción del error",
  "codigo_sql": "código SQL del error",
  "articulo_id_parcial": bigint (si se alcanzó a insertar)
}
```