Estás analizando un texto que puede ser un artículo de noticias completo o un fragmento de un documento más extenso (libro, informe, ley, etc.). La información contextual (Título, Fuente, País, Fecha) te indica el origen.

Basándote en el texto y en los elementos ya identificados, extrae y clasifica:

# TEXTO A ANALIZAR
Título/Documento: {{TITULO_O_DOCUMENTO}}
Fuente/Tipo: {{FUENTE_O_TIPO}}
Fecha Fuente: {{FECHA_FUENTE}}

CONTENIDO:
{{CONTENIDO}}

# ELEMENTOS IDENTIFICADOS PREVIAMENTE
{{JSON_PASO_1}}

1. CITAS TEXTUALES:
   - Texto exacto de la cita
   - ID de la entidad emisora
   - ID del hecho al que pertenece o contextualiza
   - Fecha de la cita (si se menciona)
   - Contexto en que se hizo la declaración
   - Relevancia de la cita (1-5)

2. DATOS CUANTITATIVOS:
   - ID del hecho relacionado
   - Indicador o concepto medido
   - Categoría (económico, demográfico, electoral, social, presupuestario, sanitario, ambiental, conflicto, otro)
   - Valor numérico exacto
   - Unidad de medida
   - Ámbito geográfico
   - Periodo de referencia (fecha inicio-fin)
   - Tipo de periodo (anual, trimestral, mensual, semanal, diario, puntual, acumulado)
   - Valores comparativos si se mencionan (anterior, variación)
   - Tendencia si se menciona (aumento, disminución, estable)

DIRECTRICES IMPORTANTES:
- La extracción de citas y datos cuantitativos debe basarse exclusivamente en el texto proporcionado en CONTENIDO.
- IMPORTANTE: Utiliza exactamente los mismos IDs de la etapa anterior. No reasignes IDs.
- Al referenciar entidades y hechos en `entidad_id` y `hecho_id`, utiliza **exactamente** los IDs (`id`) proporcionados en el `JSON_PASO_1`.
- Si no puedes determinar con certeza un campo, usa null en vez de inventar información
- Asume que "ahora" es la fecha de publicación del texto
- Para fechas relativas como "ayer" o "la semana pasada", calcula la fecha basándote en la fecha de publicación
- Extrae las citas exactamente como aparecen en el texto, sin parafrasear

Presenta esta información en formato JSON siguiendo exactamente esta estructura:

```json
{
  "citas_textuales": [
    {
      "id": 1,
      "cita": "",
      "entidad_id": 0,
      "hecho_id": 0,
      "fecha": "",
      "contexto": "",
      "relevancia": 3
    }
  ],
  "datos_cuantitativos": [
    {
      "id": 1,
      "hecho_id": 0,
      "indicador": "",
      "categoria": "",
      "valor": 0,
      "unidad": "",
      "ambito_geografico": [],
      "periodo": {
        "inicio": "",
        "fin": ""
      },
      "tipo_periodo": "",
      "valor_anterior": null,
      "variacion_absoluta": null,
      "variacion_porcentual": null,
      "tendencia": null
    }
  ]
}
```

EJEMPLO:
Para un texto publicado el 15/03/2023 que incluye: "Según datos del INE, el PIB creció un 3,5% en 2022, frente al 5,1% del año anterior. 'Estamos viendo una desaceleración, pero aún mantenemos un crecimiento sólido', declaró ayer la ministra de Economía en rueda de prensa."

```json
{
  "citas_textuales": [
    {
      "id": 1,
      "cita": "Estamos viendo una desaceleración, pero aún mantenemos un crecimiento sólido",
      "entidad_id": 3,
      "hecho_id": 2,
      "fecha": "2023-03-14",
      "contexto": "Declarado en rueda de prensa al comentar los datos de crecimiento del PIB",
      "relevancia": 4
    }
  ],
  "datos_cuantitativos": [
    {
      "id": 1,
      "hecho_id": 2,
      "indicador": "Crecimiento del PIB",
      "categoria": "económico",
      "valor": 3.5,
      "unidad": "porcentaje",
      "ambito_geografico": ["España"],
      "periodo": {
        "inicio": "2022-01-01",
        "fin": "2022-12-31"
      },
      "tipo_periodo": "anual",
      "valor_anterior": 5.1,
      "variacion_absoluta": -1.6,
      "variacion_porcentual": null,
      "tendencia": "disminución"
    }
  ]
}
```

Utiliza solo los valores permitidos para campos enumerados. Asigna IDs únicos y referencia correctamente las entidades y hechos usando los IDs asignados previamente. No inventes información que no esté presente en el texto.