# Análisis de Relaciones para Texto

Estás analizando un texto que puede ser un artículo de noticias completo o un fragmento de un documento más extenso (libro, informe, ley, etc.). La información contextual (Título, Fuente, País, Fecha) te indica el origen.

Analiza el texto y los elementos ya extraídos (hechos, entidades, citas, datos) para identificar las relaciones y conexiones entre ellos. Tu objetivo es establecer una red estructurada de relaciones para enriquecer el análisis.

# CONTEXTO
Título/Documento: {{TITULO_O_DOCUMENTO}}
Fuente/Tipo: {{FUENTE_O_TIPO}}
País: {{PAIS_ORIGEN}}
Fecha: {{FECHA_FUENTE}}

# ELEMENTOS YA IDENTIFICADOS
## 1. Hechos y Entidades Normalizados
{{ELEMENTOS_BASICOS_NORMALIZADOS}}

## 2. Citas y Datos Cuantitativos
{{ELEMENTOS_COMPLEMENTARIOS}}

Identifica y establece las siguientes relaciones:

1. HECHO-ENTIDAD:
   - Para cada hecho, identifica qué entidades están involucradas y cuál es su rol
   - Tipos de rol: protagonista, mencionado, afectado, declarante, ubicacion, contexto, victima, agresor, organizador, participante, otro
   - Asigna relevancia de la entidad en cada hecho (1-10)

2. HECHO-HECHO:
   - Identifica si hay relaciones entre los hechos extraídos
   - Tipos de relación: causa, consecuencia, contexto_historico, respuesta_a, aclaracion_de, version_alternativa, seguimiento_de
   - Asigna fuerza de la relación (1-10)
   - Incluye una breve descripción de cómo se relacionan

3. ENTIDAD-ENTIDAD:
   - Identifica si hay relaciones estructurales entre las entidades
   - Tipos de relación: miembro_de, subsidiaria_de, aliado_con, opositor_a, sucesor_de, predecesor_de, casado_con, familiar_de, empleado_de
   - Asigna fuerza de la relación (1-10)
   - Incluye fechas de inicio/fin si se mencionan

4. CONTRADICCIONES:
   - Identifica si hay hechos que se contradicen entre sí
   - Tipos de contradicción: fecha, contenido, entidades, ubicacion, valor, completa
   - Asigna grado de contradicción (1-5)
   - Proporciona una descripción de la contradicción

DIRECTRICES IMPORTANTES:
- CRÍTICO: Las relaciones (Hecho-Entidad, Hecho-Hecho, Entidad-Entidad) y las contradicciones deben identificarse estrictamente dentro del conjunto de elementos (hechos, entidades) proporcionados en {{ELEMENTOS_BASICOS_NORMALIZADOS}}. No debes inferir ni crear relaciones con elementos externos no presentes en ese JSON de entrada. El análisis se limita al alcance del texto/fragmento procesado en las fases anteriores.
- Usa los IDs exactos de hechos y entidades identificados en los pasos anteriores
- Al referenciar hechos y entidades en las relaciones (`hecho_id`, `entidad_id`, `hecho_origen_id`, etc.), utiliza **exactamente** los IDs (`id`) proporcionados en `ELEMENTOS_BASICOS_NORMALIZADOS`.
- No inventes relaciones que no estén respaldadas por el texto
- Omite una sección si no hay relaciones de ese tipo

Presenta tu análisis en formato JSON siguiendo exactamente esta estructura:

```json
{
  "hecho_entidad": [
    {
      "hecho_id": 0,
      "entidad_id": 0,
      "tipo_relacion": "",
      "relevancia_en_hecho": 5
    }
  ],
  "hecho_relacionado": [
    {
      "hecho_origen_id": 0,
      "hecho_destino_id": 0,
      "tipo_relacion": "",
      "fuerza_relacion": 5,
      "descripcion_relacion": ""
    }
  ],
  "entidad_relacion": [
    {
      "entidad_origen_id": 0,
      "entidad_destino_id": 0,
      "tipo_relacion": "",
      "descripcion": "",
      "fecha_inicio": null,
      "fecha_fin": null,
      "fuerza_relacion": 5
    }
  ],
  "contradicciones": [
    {
      "hecho_principal_id": 0,
      "hecho_contradictorio_id": 0,
      "tipo_contradiccion": "",
      "grado_contradiccion": 3,
      "descripcion": ""
    }
  ]
}
```

EJEMPLO:
Para los hechos: "Pedro Sánchez anunció medidas económicas" (ID 1) y "Las medidas entrarán en vigor próximamente" (ID 2)
Y las entidades: "Pedro Sánchez" (ID 1), "PSOE" (ID 2), "Gobierno de España" (ID 3)

```json
{
  "hecho_entidad": [
    {
      "hecho_id": 1,
      "entidad_id": 1,
      "tipo_relacion": "protagonista",
      "relevancia_en_hecho": 9
    },
    {
      "hecho_id": 1,
      "entidad_id": 3,
      "tipo_relacion": "contexto",
      "relevancia_en_hecho": 6
    },
    {
      "hecho_id": 2,
      "entidad_id": 3,
      "tipo_relacion": "protagonista",
      "relevancia_en_hecho": 8
    }
  ],
  "hecho_relacionado": [
    {
      "hecho_origen_id": 1,
      "hecho_destino_id": 2,
      "tipo_relacion": "causa",
      "fuerza_relacion": 8,
      "descripcion_relacion": "El anuncio de Sánchez (hecho 1) causa directamente la futura entrada en vigor de las medidas (hecho 2)"
    }
  ],
  "entidad_relacion": [
    {
      "entidad_origen_id": 1,
      "entidad_destino_id": 2,
      "tipo_relacion": "miembro_de",
      "descripcion": "Pedro Sánchez es miembro del PSOE",
      "fecha_inicio": null,
      "fecha_fin": null,
      "fuerza_relacion": 7
    },
    {
      "entidad_origen_id": 1,
      "entidad_destino_id": 3,
      "tipo_relacion": "empleado_de",
      "descripcion": "Pedro Sánchez es el presidente del Gobierno de España",
      "fecha_inicio": null,
      "fecha_fin": null,
      "fuerza_relacion": 10
    }
  ],
  "contradicciones": []
}
```