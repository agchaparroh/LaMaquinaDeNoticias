Este documento detalla cada una de las herramientas de consulta (funciones Python) disponibles para el Modelo de Lenguaje Grande (LLM) dentro del module_chat_interface. Estas herramientas permiten al LLM interactuar con la Memoria Relacional (Base de Datos Supabase/PostgreSQL) para obtener información específica y responder a las preguntas de los periodistas.

Cada herramienta devuelve datos estructurados y, crucialmente, información sobre las fuentes de los datos recuperados para asegurar la trazabilidad y permitir la citación. Los parámetros de entrada para cada herramienta están definidos y validados por modelos Pydantic específicos que se encuentran en el archivo VIII.models_queries.py.

---

### 0.1. I. Herramientas Granulares (Acceso y Análisis Específico)

Estas herramientas realizan tareas de búsqueda o recuperación muy específicas y enfocadas.

---

1. **consultar_cronologia**
    
    - **Explicación:** Busca y recupera una secuencia de **hechos** ordenados cronológicamente o por importancia editorial. Es fundamental para construir líneas de tiempo, entender la secuencia de eventos relacionados con un tema, o ver la actividad de entidades en un período. Permite filtros por hilos narrativos, IDs de entidades involucradas, palabras clave en el contenido de los hechos, países de ocurrencia, y un rango de fechas (inicio y fin). Puede obtener hechos originados tanto en artículos de noticias como en fragmentos de documentos extensos (si incluir_documentos es True).
        
    - **Parámetros:** Definidos por CronologiaParams (incluye hilo_id, entidades_ids, palabras_clave, paises, fecha_inicio, fecha_fin, max_resultados, pagina, orden, fuente_origen, documento_id, incluir_documentos).
        
    - **Ejemplo de Uso (Conceptual):** "Muéstrame los eventos clave relacionados con 'Acuerdo Climático Global' en 'Europa' durante 2023, ordenados por importancia."
        
    - **Información Clave que Devuelve:** Lista de objetos Hecho (con contenido, fecha, tipo, país, importancia, etiquetas, fuente), metadatos de paginación, y lista de fuentes consultadas.
        
2. **consultar_perfil_entidad**
    
    - **Explicación:** Obtiene un perfil completo y detallado de una **entidad** específica (identificada por su ID o por nombre y tipo). El perfil incluye sus datos básicos (nombre, tipo, descripción, alias, fechas relevantes), los hechos más significativos en los que ha estado involucrada, las citas textuales que ha emitido, y sus relaciones directas con otras entidades. Útil para obtener una comprensión profunda de un actor o concepto.
        
        - **Enriquecimiento con Wikidata (CP-008):** Si la entidad recuperada de la base de datos posee un wikidata_id y el parámetro enriquecer_con_wikidata es true (o si el nivel de detalle solicitado es alto), la herramienta puede realizar una consulta en tiempo real a la API de Wikidata para obtener información adicional como la descripción actualizada, URL de la imagen principal, y sitio web oficial. Estos datos se incorporarán a la respuesta final.
            
    - **Parámetros:** Definidos por PerfilParams (incluye entidad_id, nombre, tipo, incluir_relaciones, incluir_hechos, incluir_citas, max_hechos, max_citas, enriquecer_con_wikidata: bool = False (CP-008)).
        
    - **Ejemplo de Uso (Conceptual):** "Dame el perfil completo de la organización 'Banco Central Europeo', incluyendo sus últimos hechos y relaciones, y enriquécelo con Wikidata."
        
    - **Información Clave que Devuelve:** Objeto con datos_basicos de la entidad (potencialmente enriquecidos desde Wikidata), y listas opcionales de hechos, citas, y relaciones (tanto como origen como destino), junto con las fuentes.
        
3. **busqueda_semantica**
    
    - **Explicación:** Realiza una búsqueda basada en la **similitud conceptual** utilizando los embeddings vectoriales almacenados para hechos, entidades, y fragmentos de documentos. Encuentra contenido que es semánticamente similar a la consulta textual del usuario, incluso si no comparten las mismas palabras clave exactas. Es útil para exploraciones temáticas amplias o para encontrar información relacionada de forma no obvia. Permite filtrar por tipo de resultado (hecho, entidad, fragmento, cita, dato), origen de la fuente (artículo/documento), un documento_id específico, y un umbral de similitud para ajustar la relevancia.
        
    - **Parámetros:** Definidos por BusquedaSemanticaParams (incluye consulta, filtro_tipo, umbral_similitud, fuente_origen, documento_id, max_resultados, pagina, incluir_contexto).
        
    - **Ejemplo de Uso (Conceptual):** "Encuentra información sobre las consecuencias económicas de la inteligencia artificial en el sector laboral."
        
    - **Información Clave que Devuelve:** Lista de resultados (cada uno con id, tipo, score de similitud, texto_principal, importancia, y fuente), metadatos de paginación, y lista de fuentes.
        
4. **buscar_hilos_narrativos**
    
    - **Explicación:** Busca y lista **hilos narrativos** existentes en el sistema. Permite filtrar por palabras en el título del hilo, estado del hilo (ej. 'activo'), etiquetas asociadas, o países principales cubiertos por el hilo. El objetivo principal de esta herramienta es ayudar al usuario a descubrir o identificar hilos de interés para consultas posteriores más detalladas (que usarían obtener_info_hilo).
        
    - **Parámetros:** Definidos por HilosParams (incluye titulo, estado, etiquetas, paises, orden, max_resultados, pagina).
        
    - **Ejemplo de Uso (Conceptual):** "¿Qué hilos narrativos activos hay sobre 'crisis migratoria' en 'América Latina'?"
        
    - **Información Clave que Devuelve:** Lista de objetos HiloNarrativo (con id, titulo, descripcion, estado, relevancia_editorial, fecha_ultimo_hecho, y métricas como total_hechos si se usa la vista materializada), y metadatos de paginación.
        
5. **obtener_info_hilo**
    
    - **Explicación:** Recupera toda la información detallada y relevante asociada a un **hilo narrativo específico**, identificado por su hilo_id. Esta herramienta es fundamental para que el LLM pueda construir una explicación narrativa del hilo. Devuelve:
        
        - El título del hilo.
            
        - La **descripción curada del hilo** (el ángulo/tesis editorial que guía la narrativa).
            
        - La **lista actualizada de IDs de elementos relevantes** (hechos, entidades, citas) que actualmente cumplen los criterios del hilo.
            
        - Los **detalles completos** de esos elementos relevantes (ej. contenido del hecho, nombre de la entidad, texto de la cita, con sus respectivas fuentes individuales).
            
        - Los **puntos clave de novedades recientes** (si fueron generados por la IA Nocturna).
            
        - Otros metadatos del hilo como fecha_ultimo_hecho y métricas agregadas (posiblemente desde la vista resumen_hilos_activos).
            
    - **Parámetros:** hilo_id: int, incluir_detalles_elementos: bool = True (para controlar si se traen los detalles completos o solo los IDs), max_elementos_detalle: int = 50. (Este modelo Pydantic necesitaría crearse en VIII.models_queries.py).
        
    - **Ejemplo de Uso (Conceptual):** (LLM internamente) "Necesito los detalles del hilo con ID 42 para explicar su evolución."
        
    - **Información Clave que Devuelve:** Un objeto detallado del hilo con su descripción, la lista de elementos (con sus detalles) y novedades.
        
6. **buscar_entidades**
    
    - **Explicación:** Busca y lista **entidades** por su nombre (puede ser una búsqueda parcial o por similitud) y/o por su tipo (PERSONA, ORGANIZACION, LUGAR, CONCEPTO, NORMATIVA, etc.). Permite encontrar entidades específicas o explorar qué entidades de un tipo particular están registradas o relacionadas con un tema.
        
    - **Parámetros:** Definidos por EntidadesParams (incluye nombre, tipo, relacionado_a_tema, relacionado_a_hecho_id, relacionado_a_hilo_id, limite, pagina, incluir_conceptos, incluir_normativas).
        
    - **Ejemplo de Uso (Conceptual):** "¿Qué organizaciones de derechos humanos están registradas en Colombia?"
        
    - **Información Clave que Devuelve:** Lista de objetos Entidad (con id, nombre, tipo, descripcion, relevancia, estadísticas de menciones), y metadatos de total.
        
7. **obtener_datos_cuantitativos**
    
    - **Explicación:** Recupera **datos numéricos estructurados** (estadísticas, cifras, porcentajes) de la base de datos. Se puede filtrar por el nombre del indicador (ej. "Tasa de desempleo"), categoría (económico, demográfico, etc.), ámbito geográfico (país), y período de referencia.
        
    - **Parámetros:** Definidos por DatosCuantitativosParams (incluye indicador, categoria, pais, ambito_geografico, periodo_inicio, periodo_fin, tipo_periodo, fuente_origen, documento_id, limite, pagina).
        
    - **Ejemplo de Uso (Conceptual):** "Busca la inflación interanual de Argentina para el último trimestre."
        
    - **Información Clave que Devuelve:** Lista de objetos DatoCuantitativo (con indicador, valor, unidad, ámbito, periodo, fuente), y metadatos de paginación.
        
8. **ejecutar_consulta_guardada**
    
    - **Explicación:** Ejecuta una **consulta predefinida y guardada** en la tabla consultas_guardadas por su nombre. Estas son búsquedas que los periodistas han marcado como frecuentes o útiles. Permite pasar parámetros adicionales para particularizar la ejecución de la consulta guardada.
        
    - **Parámetros:** Definidos por ConsultaGuardadaParams (incluye nombre_consulta, parametros_adicionales).
        
    - **Ejemplo de Uso (Conceptual):** "Ejecuta la consulta guardada 'Impacto Sequía Cultivos Cono Sur' para el año 2023."
        
    - **Información Clave que Devuelve:** El resultado de la consulta guardada, que puede variar en estructura (lista de hechos, entidades, etc.), y las fuentes.
        
9. **health_check**
    
    - **Explicación:** Verifica el estado operativo del servidor del module_chat_interface y su capacidad para conectarse a la base de datos. Principalmente una herramienta de diagnóstico técnico, no para respuestas directas al usuario sobre contenido.
        
    - **Parámetros:** Ninguno.
        
    - **Ejemplo de Uso (Conceptual):** (LLM internamente si sospecha un problema técnico) "Verificar estado del sistema de consulta."
        
    - **Información Clave que Devuelve:** Objeto con el estado (status: "ok" o "error"), timestamp, y estado de la conexión a la BD.
        
10. **buscar_relaciones_entidad**
    
    - **Explicación:** Busca y describe las **conexiones o relaciones directas** entre dos entidades específicas, o todas las relaciones directas de una entidad dada si solo se proporciona una. Identifica el tipo_relacion (ej. "miembro_de", "aliado_con", "empleado_de"), la descripción de la relación, fechas y su fuerza_relacion.
        
    - **Parámetros:** Definidos por BuscarRelacionesEntidadParams (incluye entidad_id (obligatorio), entidad_id2 (opcional), tipo_relacion, incluir_indirectas (aunque el foco es directo), profundidad_max, limite, pagina).
        
    - **Ejemplo de Uso (Conceptual):** "¿Cuál es la relación entre 'Empresa X' y 'Político Y'?"
        
    - **Información Clave que Devuelve:** Lista de objetos RelacionEntidad (detallando origen, destino, tipo, descripción, fuerza), y las entidades involucradas como fuentes.
        
11. **buscar_relaciones_hecho**
    
    - **Explicación:** Encuentra y describe las **conexiones directas entre dos hechos** específicos, o todos los hechos directamente relacionados con un hecho dado. Muestra tipo_relacion como "causa", "consecuencia", "contexto_historico", "respuesta_a", etc., junto con una descripción y fuerza_relacion.
        
    - **Parámetros:** Definidos por BuscarRelacionesHechoParams (incluye hecho_id (obligatorio), fecha_ocurrencia (del hecho_id), hecho_id2 (opcional), fecha_ocurrencia2, tipo_relacion, incluir_indirectas, profundidad_max, limite).
        
    - **Ejemplo de Uso (Conceptual):** "El evento A, ¿fue causa del evento B?"
        
    - **Información Clave que Devuelve:** Lista de objetos RelacionHecho (detallando origen, destino, tipo, descripción, fuerza), y los hechos involucrados como fuentes.
        
12. **buscar_contradicciones**
    
    - **Explicación:** Identifica y recupera **contradicciones explícitamente registradas** en la tabla contradicciones de la base de datos. Estas contradicciones vinculan dos hechos que presentan información inconsistente. Permite filtrar por un hecho_id específico (para ver si tiene contradicciones), entidades_ids involucradas en los hechos contradictorios, o palabras_clave.
        
    - **Parámetros:** Definidos por BuscarContradiccionesParams (incluye hecho_id, fecha_ocurrencia, entidades_ids, palabras_clave, tipo_contradiccion, grado_minimo, limite, pagina).
        
    - **Ejemplo de Uso (Conceptual):** "¿Hay alguna contradicción registrada sobre las cifras de inflación de este mes?"
        
    - **Información Clave que Devuelve:** Lista de objetos Contradiccion (detallando los dos hechos, tipo y grado de contradicción, descripción), y los hechos involucrados como fuentes.
        
13. **buscar_citas**
    
    - **Explicación:** Recupera **declaraciones textuales (citas)** de la tabla citas_textuales. Permite filtrar por la entidad_emisora_id (quién dijo la cita), palabras_clave dentro del texto de la cita, un rango de fecha_cita, y la fuente de origen (artículo o documento/fragmento, o un articulo_id o documento_id/fragmento_id específico).
        
    - **Parámetros:** Definidos por BuscarCitasParams (incluye entidad_emisora_id, palabras_clave, fecha_inicio, fecha_fin, fuente_origen, articulo_id, documento_id, fragmento_id, max_resultados, pagina, orden).
        
    - **Ejemplo de Uso (Conceptual):** "¿Qué dijo el Ministro de Economía sobre los subsidios la semana pasada?"
        
    - **Información Clave que Devuelve:** Lista de objetos CitaTextual (con texto de la cita, emisor, fecha, contexto, relevancia, fuente), metadatos de paginación, y lista de fuentes.
        
14. **buscar_documentos**
    
    - **Explicación:** Encuentra **documentos extensos** (libros, informes, leyes, etc.) almacenados en la tabla documentos_extensos. Permite buscar por titulo, autor, tipo_documento, o palabras_clave_contenido (que buscaría en los fragmentos_extensos asociados).
        
    - **Parámetros:** Definidos por BuscarDocumentosParams (incluye titulo, autor, tipo_documento, palabras_clave_contenido, fecha_publicacion_inicio, fecha_publicacion_fin, max_resultados, pagina, orden).
        
    - **Ejemplo de Uso (Conceptual):** "Encuentra informes sobre cambio climático publicados por la ONU en 2023."
        
    - **Información Clave que Devuelve:** Lista de objetos DocumentoExtenso (con metadatos del documento, y opcionalmente fragmentos de muestra si se buscó por contenido), y metadatos de paginación.
        
15. **obtener_fuentes**
    
    - **Explicación:** Recupera la información detallada de las **fuentes originales** (artículos o documentos/fragmentos) asociadas a un elemento de datos específico como un hecho, una cita o un dato cuantitativo. Es crucial para la trazabilidad y permitir al periodista verificar la información en su contexto original.
        
    - **Parámetros:** Definidos por ObtenerFuentesParams (incluye elemento_id, tipo_elemento (hecho, cita, dato), incluir_contenido (para fragmentos)).
        
    - **Ejemplo de Uso (Conceptual):** (LLM internamente después de recuperar un hecho) "Necesito los detalles de la fuente del Hecho ID 789."
        
    - **Información Clave que Devuelve:** Un objeto (o lista si hay múltiples fuentes para un hecho) que describe la fuente, ya sea un artículo (medio, titular, URL, fecha) o un documento (título, autor, tipo) con detalles del fragmento (índice, título de sección, páginas, y opcionalmente contenido o extracto).
        
16. **consultar_efemerides (Nueva Herramienta - CP-009)**
    
    - **Explicación:** Consulta la tabla eventos_recurrentes_anuales para encontrar efemérides, celebraciones o aniversarios para una fecha específica (día y mes) o para un rango de fechas.
        
    - **Parámetros:** Definidos por ConsultarEfemeridesParams (modelo Pydantic a crear, incluye dia: Optional[int], mes: Optional[int], fecha_especifica: Optional[date], rango_dias_proximos: Optional[int], tipo_evento: Optional[str], ambito: Optional[str]).
        
    - **Ejemplo de Uso (Conceptual):** "¿Qué efemérides hay para el 1 de mayo?" o "¿Cuáles son los días internacionales de la próxima semana?"
        
    - **Información Clave que Devuelve:** Lista de objetos EventoRecurrenteAnual (cada uno con titulo_evento, descripcion, tipo_evento, ambito, relevancia_editorial, y si año_origen está presente, podría incluir "años transcurridos" si la consulta es para el año actual).
        

---

### 0.2. II. Herramientas Meta (Orquestación y Síntesis de Información)

Estas herramientas típicamente llaman a una o más herramientas granulares (incluyendo obtener_info_hilo) para construir una respuesta más elaborada o un análisis más complejo.

---

1. **explicar_elemento**
    
    - **Explicación:** Proporciona un **resumen contextualizado y conciso** de un elemento específico de la base de datos (puede ser una entidad, un hecho, un documento, un hilo narrativo, una cita, etc.), con diferentes niveles de profundidad (básico, medio, completo). Internamente, llama a herramientas granulares relevantes (ej. consultar_perfil_entidad si es una entidad, obtener_info_hilo si es un hilo, obtener_fuentes para un hecho) y luego el LLM sintetiza la información para crear una explicación coherente.
        
        - **Enriquecimiento con Wikidata (CP-008, si el tipo es 'entidad'):** Si el elemento a explicar es una entidad, esta herramienta internamente puede pasar el parámetro enriquecer_con_wikidata: true a consultar_perfil_entidad para obtener información adicional de Wikidata.
            
    - **Parámetros:** Definidos por ExplicarElementoParams (incluye identificador (ID o nombre), tipo del elemento, profundidad, incluir_fuentes, max_contexto, enriquecer_con_wikidata: bool = False (CP-008, aplicable si tipo es entidad)).
        
    - **Ejemplo de Uso (Conceptual):** "Explícame brevemente qué es el 'Tratado de Lisboa'." o "Dame un resumen completo del Hilo Narrativo 'Elecciones Presidenciales País Z', incluyendo datos de Wikidata para las entidades principales."
        
    - **Información Clave que Devuelve:** Texto explicativo generado por el LLM, junto con una lista de las fuentes principales consultadas por las herramientas subyacentes.
        
2. **dossier_diario**
    
    - **Explicación:** Recopila y estructura los **hechos más relevantes** ocurridos en un período de tiempo específico (ej. últimas 24h, última semana), típicamente ordenados por importancia. Permite filtrar por pais y tema (palabras clave). Puede incluir opcionalmente hechos de fuentes de opinión o solo de fuentes oficiales. Puede devolver un resumen o la lista de hechos.
        
    - **Parámetros:** Definidos por DossierDiarioParams (incluye periodo, pais, tema, max_resultados, min_importancia, incluir_opiniones, incluir_fuentes_oficiales, formato_resumen).
        
    - **Ejemplo de Uso (Conceptual):** "Prepárame un dossier con los eventos más importantes en Venezuela de las últimas 48 horas sobre política."
        
    - **Información Clave que Devuelve:** Lista de hechos relevantes (o un resumen textual si formato_resumen es true), filtros aplicados, y lista de fuentes.
        
3. **comparar_elementos**
    
    - **Explicación:** Analiza y presenta las **similitudes y diferencias clave** entre dos elementos de la base de datos. Los elementos pueden ser del mismo tipo (ej. dos entidades, dos hechos) o de tipos diferentes (ej. una entidad y un hilo narrativo). El usuario puede especificar los aspectos a comparar (ej. postura sobre un tema, cronología de eventos relacionados, impacto económico).
        
    - **Parámetros:** Definidos por CompararElementosParams (incluye identificador1, tipo1, identificador2, tipo2, aspectos, nivel_detalle, incluir_cronologia, max_elementos_contexto).
        
    - **Ejemplo de Uso (Conceptual):** "Compara la postura de 'Político A' y 'Político B' sobre la reforma educativa."
        
    - **Información Clave que Devuelve:** Un análisis comparativo textual generado por el LLM, basado en datos recuperados para ambos elementos, y las fuentes de dichos datos.
        
4. **todo_sobre**
    
    - **Explicación:** Genera un **informe exhaustivo y multifacético** sobre un tema, entidad o **hilo narrativo** específico. Recopila una amplia gama de información disponible en la base de datos, incluyendo cronología de hechos, opiniones relevantes (citas a favor y en contra si aplica), datos cuantitativos relacionados, documentos asociados, relaciones clave, etc. Si el elemento es un hilo, usa obtener_info_hilo como punto de partida principal.
        
    - **Parámetros:** Definidos por TodoSobreParams (incluye identificador, tipo, incluir_cronologia, incluir_opiniones, incluir_datos_cuantitativos, incluir_documentos_completos (fragmentos), desde_fecha, hasta_fecha, max_resultados_por_seccion).
        
    - **Ejemplo de Uso (Conceptual):** "Dame toda la información disponible sobre la 'Ley de Inteligencia Artificial de la UE'."
        
    - **Información Clave que Devuelve:** Un informe estructurado (posiblemente en markdown o JSON con secciones) generado por el LLM, conteniendo la compilación de la información y las fuentes.
        
5. **detectar_cambio_narrativa**
    
    - **Explicación:** Analiza cómo ha **evolucionado la narrativa, el enfoque o el sentimiento** sobre un tema o entidad_id específico, comparando la información (principalmente hechos y citas) entre dos períodos de tiempo definidos (periodo1_inicio/fin y periodo2_inicio/fin). Identifica cambios relevantes en el tipo de hechos reportados, las entidades que emiten declaraciones, el tono de las citas, etc.
        
    - **Parámetros:** Definidos por DetectarCambioNarrativaParams (incluye tema, entidad_id, periodo1_inicio, periodo1_fin, periodo2_inicio, periodo2_fin, fuentes_incluidas, excluir_fuentes, umbral_cambio, max_elementos_contexto).
        
    - **Ejemplo de Uso (Conceptual):** "Analiza cómo cambió la cobertura mediática sobre la 'vacunación COVID' entre el primer semestre de 2021 y el primer semestre de 2022."
        
    - **Información Clave que Devuelve:** Un análisis textual de los cambios detectados, métricas comparativas de los dos periodos (ej. volumen de hechos, tipos de hechos predominantes, sentimiento general de las citas), y ejemplos de hechos/citas que ilustran el cambio, junto con las fuentes.
        
6. **generar_contexto_geopolitico**
    
    - **Explicación:** Construye un **panorama geopolítico contextualizado** para un pais y un tema específico durante un periodo determinado. Intenta incluir hechos recientes relevantes en el país sobre el tema, relaciones internacionales clave del país (con otros países u organizaciones), información sobre países vecinos (si se solicita y es pertinente al tema), y datos cuantitativos relevantes (económicos, sociales, de conflicto) para ofrecer una visión integral.
        
    - **Parámetros:** Definidos por GenerarContextoGeoParams (incluye pais, tema, periodo, incluir_paises_vecinos, incluir_relaciones_internacionales, incluir_datos_cuantitativos, max_hechos_por_categoria, nivel_detalle).
        
    - **Ejemplo de Uso (Conceptual):** "Genérame el contexto geopolítico de 'Ucrania' en relación con la 'seguridad energética europea' durante los últimos 6 meses."
        
    - **Información Clave que Devuelve:** Un informe estructurado con secciones para cada aspecto (hechos internos, relaciones, vecinos, datos), generado por el LLM, y las fuentes de la información.
        
7. **validar_afirmacion**
    
    - **Explicación:** Intenta **verificar o refutar una afirmacion específica** hecha por el usuario, buscando evidencia en la base de datos. Presenta información encontrada que apoya la afirmación, información que la contradice (si incluir_contraejemplos es true), y cualquier contradicción explícita registrada. Puede considerar un contexto_temporal o contexto_geografico para acotar la búsqueda.
        
    - **Parámetros:** Definidos por ValidarAfirmacionParams (incluye afirmacion, umbral_confianza (para búsqueda semántica), max_fuentes_verificacion, incluir_contraejemplos, contexto_temporal, contexto_geografico).
        
    - **Ejemplo de Uso (Conceptual):** "Valida la afirmación: 'La inversión extranjera directa en México aumentó en el último año'."
        
    - **Información Clave que Devuelve:** Un análisis de la afirmación con secciones de evidencia a favor, evidencia en contra, contradicciones relevantes, y un posible score de confianza o resumen de la validación, junto con las fuentes.