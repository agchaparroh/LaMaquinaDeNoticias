
# TAREA: Extracción Estructurada de Citas Textuales

Analiza el siguiente `CONTENIDO` de un artículo o documento. Extrae **Citas textuales**.

## **CONTEXTO DEL TEXTO:**

*   Título: `{{TITULO}}`
*   Fuente: `{{FUENTE}}`
*   Fecha de publicación: `{{FECHA_FUENTE}}` (Usa esta fecha para resolver referencias temporales relativas como "ayer" o "próximo mes").

## **CONTENIDO A ANALIZAR:**

{{CONTENIDO}}

**Hechos identificados:**
{{Fase6_Hechos}}

**Entidades identidicadas:**
{{Fase5_Entidades}}

# Extraer Citas Textuales:

   - Texto exacto de la cita
   - ID de la entidad emisora
   - ID del hecho al que pertenece o contextualiza
   - Fecha de la cita (si se menciona)
   - Contexto en que se hizo la declaración
   - Relevancia de la cita (1-5)

## DIRECTRICES IMPORTANTES:
- La extracción de citas debe basarse exclusivamente en el texto proporcionado en CONTENIDO.
- IMPORTANTE: Utiliza exactamente los mismos IDs de la etapa anterior. No reasignes IDs.
- Al referenciar entidades y hechos en `entidad_id` y `hecho_id`, utiliza **exactamente** los IDs (`id`) proporcionados en el `JSON_PASO_1`.
- Si no puedes determinar con certeza un campo, usa null en vez de inventar información
- Extrae las citas exactamente como aparecen en el texto, sin parafrasear

Presenta esta información en formato JSON siguiendo exactamente esta estructura:

```json

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
  ]

```

## EJEMPLO:

Para un texto publicado el 15/03/2023 que dice:

  *Según datos del INE, el PIB creció un 3,5% en 2022, frente al 5,1% del año anterior. "Estamos viendo una desaceleración, pero aún mantenemos un crecimiento sólido", declaró ayer la ministra de Economía en rueda de prensa.*

```json

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
  ]

```

Utiliza solo los valores permitidos para campos enumerados. Asigna IDs únicos y referencia correctamente las entidades y hechos usando los IDs asignados previamente. No inventes información que no esté presente en el texto.