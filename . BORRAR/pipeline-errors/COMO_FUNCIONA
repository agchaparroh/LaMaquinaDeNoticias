 # 📊 Flujo Completo del Artículo

  1. 🕷️ Extracción (module_scraper)

  - Spider ejecuta y extrae el artículo del sitio web
  - Se genera un ID único para el artículo
  - División en dos caminos:
    - Camino 1: HTML completo → Supabase Storage (preservación)
    - Camino 2: Datos estructurados → Pipeline de procesamiento

  2. 🔗 Transferencia (module_connector)

  - Recibe el artículo del scraper
  - Actúa como worker asíncrono entre scraper y pipeline
  - Transfiere los datos al pipeline para procesamiento

  3. ⚙️ Procesamiento Pipeline (module_pipeline)

  El pipeline ejecuta 7 fases secuenciales de procesamiento con IA:

  Fase 1 - Triaje

  - Clasificación inicial del artículo
  - Determinación de relevancia y categoría

  Fase 2 - Simplificación

  - Limpieza y normalización del texto
  - Eliminación de elementos no relevantes

  Fase 3 - Entidades

  - Extracción de personas, organizaciones, lugares
  - Identificación con spaCy + LLMs

  Fase 4 - Hechos

  - Extracción de eventos y afirmaciones clave
  - Estructuración de información factual

  Fase 5 - Datos

  - Extracción de cifras, estadísticas
  
  Fase 6 - Citas

  - Identificación de declaraciones textuales
  
  Fase 7 - Normalización

  - Normalización de entidades
  - Generación de relaciones
  - Consolidación final de todos los elementos
  - Preparación para persistencia

  4. 💾 Persistencia (Supabase)

  Los elementos extraídos se guardan en tablas específicas:
  - articulos - Metadatos del artículo
  - entidades - Personas, organizaciones, lugares
  - hechos - Eventos y afirmaciones
  - datos - Cifras y estadísticas
  - citas - Declaraciones textuales
  - relaciones - Conexiones entre elementos

  El sistema utiliza Groq/Anthropic para el procesamiento con IA y PostgreSQL + pgvector para
  almacenamiento estructurado con capacidades de búsqueda semántica.


  ## En producción con docker-compose.yml