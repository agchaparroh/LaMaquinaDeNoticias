# TAREA: Extracción Estructurada de Hechos y Entidades

Analiza el siguiente `CONTENIDO` de un artículo o documento. Extrae **Hechos Principales** y **Entidades Mencionadas**.

## **CONTEXTO DEL TEXTO:**

*   Título/Documento Origen: `{{TITULO_O_DOCUMENTO}}`
*   Fuente/Tipo Documento: `{{FUENTE_O_TIPO}}`
*   País Origen Texto: `{{PAIS_ORIGEN}}`
*   Fecha Fuente Texto: `{{FECHA_FUENTE}}` (Usa esta fecha para resolver referencias temporales relativas como "ayer" o "próximo mes").

## **CONTENIDO A ANALIZAR:**

{{CONTENIDO}}


## **INSTRUCCIONES DE EXTRACCIÓN:**

### 1º. **ENTIDADES MENCIONADAS:**

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

### 2º. **HECHOS PRINCIPALES:**

Identifica eventos, sucesos, declaraciones o anuncios significativos.  Para cada hecho, proporciona: 
+ `id` (único secuencial)
+ `contenido` (descripción completa del hecho), 
+ `fecha` (objeto con `inicio` y `fin` en formato YYYY-MM-DD), 
+ `precision_temporal` (`exacta`, `dia`, `semana`, `mes`, `trimestre`, `año`, `decada`, `periodo`), 
+ `tipo_hecho` (`SUCESO`, `ANUNCIO`, `DECLARACION`, `BIOGRAFIA`, `CONCEPTO`, `NORMATIVA`, `EVENTO`), 
+ `pais` (array de strings), 
+ `region` (array de strings, o `[]` si no aplica), 
+ `ciudad` (array de strings, o `[]` si no aplica), 
+ `es_futuro` (boolean), 
+ `estado_programacion` (`programado`, `confirmado`, `cancelado`, `modificado`, o `null` si no es futuro o no se especifica).


## **DIRECTRICES GENERALES IMPORTANTES:**

*   Basa la extracción **estrictamente** en el `CONTENIDO` proporcionado. No inventes ni infieras más allá de lo explícito.
*   Si un campo opcional no tiene información, usa `null` para campos individuales o `[]` para arrays.
*   El campo `descripcion` de la entidad es **CRÍTICO**: debe ser un texto plano con guiones, acumulando toda la información textual sobre la entidad. No uses JSON anidado dentro de la `descripcion`.

## **FORMATO DE SALIDA JSON CON UN EJEMPLO:**

### **Si el `CONTEXTO DEL TEXTO` fuera:**

*   Título/Documento Origen: `Anuncio Presidencial`
*   Fuente/Tipo Documento: `Agencia Estatal de Noticias`
*   País Origen Texto: `Venezuela`
*   Fecha Fuente Texto: `2024-05-15`

### **Y el `CONTENIDO A ANALIZAR` fuera:**

Caracas – El presidente de Venezuela, Nicolás Maduro, anunció anoche la captura de más de 50 mercenarios en el estado La Guaira que, según él, pretendían realizar un atentado en la víspera de las elecciones presidenciales del 28 de julio.


### **La SALIDA JSON esperada sería:**

```json
{
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
      "id": 4,
      "nombre": "La Guaira",
      "alias": ["estado La Guaira"],
      "tipo": "LUGAR",
      "descripcion": "- estado",
      "fecha_nacimiento": null,
      "fecha_disolucion": null
    },
    {
      "id": 5,
      "nombre": "Elecciones Presidenciales del 28 de julio",
      "alias": [],
      "tipo": "EVENTO",
      "descripcion": "- presidenciales",
      "fecha_nacimiento": null,
      "fecha_disolucion": null
    },
    {
      "id": 6,
      "nombre": "Caracas",
      "alias": [],
      "tipo": "LUGAR",
      "descripcion": null,
      "fecha_nacimiento": null,
      "fecha_disolucion": null
    }
  ],
  "hechos": [
    {
      "id": 1,
      "contenido": "El presidente de Venezuela, Nicolás Maduro, anunció la captura de más de 50 mercenarios en el estado La Guaira.",
      "fecha": {
        "inicio": "2024-05-14",
        "fin": "2024-05-14"
      },
      "precision_temporal": "dia",
      "tipo_hecho": "ANUNCIO",
      "pais": ["Venezuela"],
      "region": ["La Guaira"],
      "ciudad": ["Caracas"],
      "es_futuro": false,
      "estado_programacion": null
    },
    {
      "id": 2,
      "contenido": "Según Nicolás Maduro, los mercenarios capturados pretendían realizar un atentado en la víspera de las elecciones presidenciales del 28 de julio.",
      "fecha": {
        "inicio": "2024-05-14", 
        "fin": "2024-05-14"
      },
      "precision_temporal": "dia",
      "tipo_hecho": "DECLARACION",
      "pais": ["Venezuela"],
      "region": [],
      "ciudad": ["Caracas"],
      "es_futuro": false,
      "estado_programacion": null
    },
    {
      "id": 3,
      "contenido": "Las elecciones presidenciales están programadas para el 28 de julio.",
      "fecha": {
        "inicio": "2024-07-28",
        "fin": "2024-07-28"
      },
      "precision_temporal": "exacta",
      "tipo_hecho": "EVENTO",
      "pais": ["Venezuela"],
      "region": [],
      "ciudad": [],
      "es_futuro": true,
      "estado_programacion": "programado"
    }
  ]
}
```