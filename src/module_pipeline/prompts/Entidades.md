# TAREA: Extracción Estructurada de Hechos y Entidades

Analiza el siguiente `CONTENIDO` de un artículo o documento. Extrae **Entidades Mencionadas**.

## **CONTEXTO DEL TEXTO:**

*   Título: `{{TITULO}}`
*   Fuente: `{{FUENTE}}`
*   País: `{{PAIS}}`
*   Fecha de publicación: `{{FECHA_FUENTE}}` (Usa esta fecha para resolver referencias temporales relativas como "ayer" o "próximo mes").

## **CONTENIDO A ANALIZAR:**

{{CONTENIDO}}


## **INSTRUCCIONES DE EXTRACCIÓN DE ENTIDADES:**

Identifica todas las entidades mencionados en el `CONTENIDO` y proporciona la siguiente información:

*  `id` (único secuencial, distinto de los IDs de hechos)
* `nombre` (canónico/principal)
* `alias` (array de strings)
* `tipo` 
	* `PERSONA`
	* `ORGANIZACION` (Empresas, partidos políticos, ONGs, grupos informales con nombre, grupos criminales, etc)
	* `INSTITUCION`(Entidades gubernamentales, académicas, judiciales, culturales con carácter formal o público, etc.)
	* `LUGAR`(Geográficos: ciudades, países, regiones. Estructuras: edificios, monumentos, instalaciones)
	* `EVENTO` (Eventos puntuales o procesos CON NOMBRE PROPIO: elecciones, cumbres, desastres, acuerdos, crisis, etc.)
	* `NORMATIVA`
	*  `CONCEPTO` (Temas, ideas, doctrinas, fenómenos económicos, políticos o sociales que están explícitamente definidos o explicados)
* `descripcion` (TEXTO PLANO: captura EXHAUSTIVAMENTE los atributos, características inherentes, roles definitorios o clasificaciones de la entidad mencionados EXPLÍCITAMENTE en el `CONTENIDO`, usando guiones `-` para cada pieza de información distinta.)
*  `fecha_nacimiento` (YYYY-MM-DD o `null`)
* `fecha_disolucion` (YYYY-MM-DD o `null`)


## **DIRECTRICES GENERALES IMPORTANTES:**

*   Basa la extracción **estrictamente** en el `CONTENIDO` proporcionado. No inventes ni infieras más allá de lo explícito.
*   Si un campo opcional no tiene información, usa `null` para campos individuales o `[]` para arrays.
*   El campo `descripcion` de la entidad es **CRÍTICO**: debe ser un texto plano con guiones, acumulando toda la información textual sobre la entidad. No uses JSON anidado dentro de la `descripcion`.

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

  "entidades": [
    {
      "id": 1,
      "nombre": "Nicolás Maduro",
      "alias": [],
      "tipo": "PERSONA",
      "descripcion": "- presidente de Venezuela",
      "fecha_nacimiento": null,
      "fecha_disolucion": null
    },
    {
      "id": 2,
      "nombre": "Venezuela",
      "alias": [],
      "tipo": "LUGAR",
      "descripcion": null,
      "fecha_nacimiento": null,
      "fecha_disolucion": null
    },
    {
      "id": 3,
      "nombre": "La Guaira",
      "alias": ["estado La Guaira"],
      "tipo": "LUGAR",
      "descripcion": "- estado",
      "fecha_nacimiento": null,
      "fecha_disolucion": null
    },
    {
      "id": 4,
      "nombre": "Elecciones Presidenciales del 28 de julio",
      "alias": [],
      "tipo": "EVENTO",
      "descripcion": "- presidenciales",
      "fecha_nacimiento": null,
      "fecha_disolucion": null
    },
    {
      "id": 5,
      "nombre": "Caracas",
      "alias": [],
      "tipo": "LUGAR",
      "descripcion": null,
      "fecha_nacimiento": null,
      "fecha_disolucion": null
    }
  ]
  
```