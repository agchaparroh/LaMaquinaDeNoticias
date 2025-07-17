
# TAREA: Extracción Estructurada de Datos Cuantitativos

Analiza el siguiente `CONTENIDO` de un artículo o documento. Extrae **Datos cuantitativos**.

## **CONTEXTO DEL TEXTO:**

*   Título: `{{TITULO}}`
*   Fuente: `{{FUENTE}}`
*   Fecha de publicación: `{{FECHA_FUENTE}}` (Usa esta fecha para resolver referencias temporales relativas como "ayer" o "próximo mes").

## **CONTENIDO A ANALIZAR:**

{{CONTENIDO}}

**Hechos identificados:**
{{Fase4_Hechos}}

**Entidades identidicadas:**
{{Fase3_Entidades}}

# Extraer Datos Cuantitativos:

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
- La extracción de datos cuantitativos debe basarse exclusivamente en el texto proporcionado en CONTENIDO.
- IMPORTANTE: Utiliza exactamente los mismos IDs de la etapa anterior. No reasignes IDs.
- Al referenciar entidades y hechos en `entidad_id` y `hecho_id`, utiliza **exactamente** los IDs (`id`) proporcionados en el `JSON_PASO_1`.
- Si no puedes determinar con certeza un campo, usa null en vez de inventar información
- Asume que "ahora" es la fecha de publicación del texto
- Para fechas relativas como "ayer" o "la semana pasada", calcula la fecha basándote en la fecha de publicación

Presenta esta información en formato JSON siguiendo exactamente esta estructura:

```json

  "datos_cuantitativos": [
    {
      "id": 1,
      "hecho_id": 0,
      "indicador": "",
      "categoria": "",
      "valor": 0,
      "unidad": "",
      "ambito_geografico": [],
      "periodo_inicio": "",
      "periodo_fin": "",
      "tipo_periodo": "",
      "valor_anterior": null,
      "variacion_absoluta": null,
      "variacion_porcentual": null,
      "tendencia": null
    }
  ]

```
## EJEMPLO:

Para un texto publicado el 15/03/2023 que dice:

  *Según datos del INE, el PIB creció un 3,5% en 2022, frente al 5,1% del año anterior. "Estamos viendo una desaceleración, pero aún mantenemos un crecimiento sólido", declaró ayer la ministra de Economía en rueda de prensa.*


```json

"datos_cuantitativos": [
    {
      "id": 1,
      "hecho_id": 2,
      "indicador": "Crecimiento del PIB",
      "categoria": "económico",
      "valor": 3.5,
      "unidad": "porcentaje",
      "ambito_geografico": ["España"],
      "periodo_inicio": "2022-01-01",
      "periodo_fin": "2022-12-31",
      "tipo_periodo": "anual",
      "valor_anterior": 5.1,
      "variacion_absoluta": -1.6,
      "variacion_porcentual": null,
      "tendencia": "disminución"
    }
  ]

```

Utiliza solo los valores permitidos para campos enumerados. Asigna IDs únicos y referencia correctamente las entidades y hechos usando los IDs asignados previamente. No inventes información que no esté presente en el texto.