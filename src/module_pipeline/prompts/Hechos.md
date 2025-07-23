# TAREA: Extracción Estructurada de Hechos y Entidades

Analiza el siguiente `CONTENIDO` de un artículo o documento. Extrae **Hechos Principales**.

## **CONTEXTO DEL TEXTO:**

*   Título: `{{TITULO}}`
*   Fuente: `{{FUENTE}}`
*   País: `{{PAIS}}`
*   Fecha de publicación: `{{FECHA_FUENTE}}` (Usa esta fecha para resolver referencias temporales relativas como "ayer" o "próximo mes").

## **CONTENIDO A ANALIZAR:**

{{CONTENIDO}}


## **INSTRUCCIONES DE EXTRACCIÓN DE HECHOS:**

Identifica eventos, sucesos, declaraciones o anuncios significativos.  Para cada hecho, proporciona: 
+ `id` (único secuencial)
+ `contenido` (descripción completa del hecho), 
+ `fecha_inicio` (string YYYY-MM-DD para el inicio del hecho), 
+ `fecha_fin` (string YYYY-MM-DD para el fin del hecho, igual a fecha_inicio si es puntual), 
+ `precision_temporal` (`exacta`, `dia`, `semana`, `mes`, `trimestre`, `año`, `decada`, `periodo`), 
+ `tipo_hecho` (`SUCESO`, `ANUNCIO`, `DECLARACION`, `BIOGRAFIA`, `CONCEPTO`, `NORMATIVA`, `EVENTO`), 
+ `importancia` (integer del 1 al 10, donde 1=muy baja importancia, 10=máxima importancia),
+ `pais` (array de strings), 
+ `region` (array de strings, o `[]` si no aplica), 
+ `ciudad` (array de strings, o `[]` si no aplica), 
+ `es_futuro` (boolean), 
+ `estado_programacion` (`programado`, `confirmado`, `cancelado`, `modificado`, o `null` si no es futuro o no se especifica).


## **DIRECTRICES GENERALES IMPORTANTES:**

*   Basa la extracción **estrictamente** en el `CONTENIDO` proporcionado. No inventes ni infieras más allá de lo explícito.
*   Si un campo opcional no tiene información, usa `null` para campos individuales o `[]` para arrays.

## **FORMATO DE SALIDA JSON CON UN EJEMPLO:**

### **Si el `CONTEXTO DEL TEXTO` fuera:**

*   Título: `Anuncio Presidencial`
*   Fuente: `Agencia Estatal de Noticias`
*   País: `Venezuela`
*   Fecha de publicación: `2024-05-15`

### **Y el `CONTENIDO A ANALIZAR` fuera:**

Caracas – El presidente de Venezuela, Nicolás Maduro, anunció anoche la captura de más de 50 mercenarios en el estado La Guaira que, según él, pretendían realizar un atentado en la víspera de las elecciones presidenciales del 28 de julio.


### **La SALIDA JSON esperada sería:**

```json

  "hechos": [
    {
      "id": 1,
      "contenido": "El presidente de Venezuela, Nicolás Maduro, anunció la captura de más de 50 mercenarios en el estado La Guaira.",
      "fecha_inicio": "2024-05-14",
      "fecha_fin": "2024-05-14",
      "precision_temporal": "dia",
      "tipo_hecho": "ANUNCIO",
      "importancia": 8,
      "pais": ["Venezuela"],
      "region": ["La Guaira"],
      "ciudad": ["Caracas"],
      "es_futuro": false,
      "estado_programacion": null
    },
    {
      "id": 2,
      "contenido": "Según Nicolás Maduro, los mercenarios capturados pretendían realizar un atentado en la víspera de las elecciones presidenciales del 28 de julio.",
      "fecha_inicio": "2024-05-14",
      "fecha_fin": "2024-05-14",
      "precision_temporal": "dia",
      "tipo_hecho": "DECLARACION",
      "importancia": 7,
      "pais": ["Venezuela"],
      "region": [],
      "ciudad": ["Caracas"],
      "es_futuro": false,
      "estado_programacion": null
    },
    {
      "id": 3,
      "contenido": "Las elecciones presidenciales están programadas para el 28 de julio.",
      "fecha_inicio": "2024-07-28",
      "fecha_fin": "2024-07-28",
      "precision_temporal": "exacta",
      "tipo_hecho": "EVENTO",
      "importancia": 9,
      "pais": ["Venezuela"],
      "region": [],
      "ciudad": [],
      "es_futuro": true,
      "estado_programacion": "programado"
    }
  ]

```