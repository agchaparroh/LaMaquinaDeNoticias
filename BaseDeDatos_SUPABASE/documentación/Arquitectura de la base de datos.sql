-- 0001_initial_schema.sql
-- Esquema completo v3.3 para la Máquina de Noticias
-- Se asume la existencia de las extensiones `vector` (pgvector) y `pg_trgm`

-- Activar extensiones requeridas como se especifica en la sección 3.5 del documento maestro
CREATE EXTENSION IF NOT EXISTS vector;     -- pgvector para embeddings
CREATE EXTENSION IF NOT EXISTS pg_trgm;    -- Búsqueda por similitud de texto
CREATE EXTENSION IF NOT EXISTS pg_cron;    -- Programación de tareas

-- 1. Tipos Enumerados
-- PostgreSQL no tiene ENUMs nativos fáciles de modificar, por lo que se utilizan VARCHAR con CHECK constraints

-- 3. Tablas para Documentos Extensos (Ingesta Manual)
-- Crear tablas primero por referencia en otras tablas

-- 3.1. Documentos Extensos
CREATE TABLE documentos_extensos (
    id BIGSERIAL PRIMARY KEY,
    titulo VARCHAR(300) NOT NULL,
    autor VARCHAR(200),
    fecha_publicacion DATE,
    tipo_documento VARCHAR(50) NOT NULL CHECK (tipo_documento IN ('libro', 'paper', 'ley', 'tratado', 'informe', 'manual', 'otro')),
    isbn VARCHAR(20),
    editorial VARCHAR(100),
    num_paginas INTEGER,
    storage_path TEXT UNIQUE NOT NULL, -- Ruta al archivo en Supabase Storage
    fecha_ingesta TIMESTAMP WITH TIME ZONE DEFAULT now(),
    procesado BOOLEAN DEFAULT false
);

ALTER TABLE documentos_extensos ALTER COLUMN titulo SET STORAGE EXTENDED;
CREATE INDEX idx_doc_ext_titulo_trgm ON documentos_extensos USING gin(titulo gin_trgm_ops);
CREATE INDEX idx_doc_ext_autor_trgm ON documentos_extensos USING gin(autor gin_trgm_ops);

-- 3.2. Fragmentos Extensos
CREATE TABLE fragmentos_extensos (
    id BIGSERIAL PRIMARY KEY,
    documento_id BIGINT REFERENCES documentos_extensos(id) ON DELETE CASCADE,
    indice_secuencial INTEGER NOT NULL, -- Orden del fragmento dentro del documento
    titulo_seccion VARCHAR(255),
    contenido TEXT NOT NULL,
    num_pagina_inicio INTEGER,
    num_pagina_fin INTEGER,
    embedding vector(384), -- Embedding del fragmento
    CONSTRAINT uq_fragmento UNIQUE (documento_id, indice_secuencial)
);

ALTER TABLE fragmentos_extensos ALTER COLUMN contenido SET STORAGE EXTENDED;
CREATE INDEX idx_fragmentos_documento_id ON fragmentos_extensos(documento_id);
CREATE INDEX idx_fragmentos_embedding_ivfflat ON fragmentos_extensos USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100); -- Ajustar listas

-- 2. Tablas Principales

-- 2.1. Hechos (Particionada por Año)
CREATE TABLE hechos (
    id BIGSERIAL, -- Usar BIGSERIAL para tablas grandes
    contenido TEXT NOT NULL,
    fecha_ocurrencia TSTZRANGE NOT NULL,
    precision_temporal VARCHAR(20) NOT NULL CHECK (precision_temporal IN ('exacta', 'dia', 'semana', 'mes', 'trimestre', 'año', 'decada', 'periodo')),
    importancia INTEGER NOT NULL CHECK (importancia BETWEEN 1 AND 10) DEFAULT 5, -- (CP-004) Valor asignado por Fase de Evaluación de Importancia Contextual
    tipo_hecho VARCHAR(50) NOT NULL CHECK (tipo_hecho IN ('SUCESO', 'ANUNCIO', 'DECLARACION', 'BIOGRAFIA', 'CONCEPTO', 'NORMATIVA', 'EVENTO')),
    pais VARCHAR(100)[] NOT NULL, -- Lista de países relevantes
    region VARCHAR(100)[],
    ciudad VARCHAR(100)[],
    etiquetas TEXT[], -- Lista flexible de etiquetas temáticas/entidades que se puebla con content_tagger.py
    frecuencia_citacion INTEGER DEFAULT 0,
    medios_principales INTEGER DEFAULT 0,
    total_menciones INTEGER DEFAULT 0,
    menciones_confirmatorias INTEGER DEFAULT 0,
    -- mencion_contradictorias INTEGER DEFAULT 0, -- Eliminado (CP-005)
    fecha_ingreso TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    evaluacion_editorial VARCHAR(30) DEFAULT 'pendiente_revision_editorial' CHECK (evaluacion_editorial IN ('pendiente_revision_editorial', 'verificado_ok_editorial', 'declarado_falso_editorial')), -- Modificado (CP-005)
    editor_evaluador VARCHAR(100), -- Renombrado (CP-005)
    fecha_evaluacion_editorial TIMESTAMP WITH TIME ZONE, -- Renombrado (CP-005)
    justificacion_evaluacion_editorial TEXT, -- Añadido (CP-005)
    consenso_fuentes VARCHAR(40) DEFAULT 'pendiente_analisis_fuentes' CHECK (consenso_fuentes IN ('pendiente_analisis_fuentes', 'confirmado_multiples_fuentes', 'sin_confirmacion_suficiente_fuentes', 'en_disputa_por_hechos_contradictorios')), -- Añadido (CP-005)
    -- notas_editoriales TEXT, -- Eliminado (CP-001)
    embedding vector(384), -- Para búsqueda semántica (ajustar dimensión si es necesario)
    -- Campos para eventos programados
    es_evento_futuro BOOLEAN DEFAULT false,
    estado_programacion VARCHAR(50) CHECK (estado_programacion IN ('programado', 'confirmado', 'cancelado', 'modificado', 'realizado', NULL)),
    confiabilidad_programacion INTEGER CHECK (confiabilidad_programacion BETWEEN 1 AND 5),
    alerta_proximidad BOOLEAN DEFAULT false,
    metadata JSONB, -- Para almacenar información complementaria (ej. de hechos fusionados)
    -- Campos para manejo de duplicados (IA Nocturna)
    duplicado_de_hecho_id BIGINT DEFAULT NULL, -- Referencia al ID del hecho principal si este es un duplicado
    complementado_en_hecho_id BIGINT DEFAULT NULL, -- Referencia al ID del hecho principal si este complementó a otro
    -- Campos para vincular a documentos extensos
    documento_id BIGINT REFERENCES documentos_extensos(id) ON DELETE SET NULL,
    fragmento_id BIGINT REFERENCES fragmentos_extensos(id) ON DELETE SET NULL,
    -- Constraints
    CONSTRAINT hechos_pkey PRIMARY KEY (id, fecha_ocurrencia) -- Clave primaria compuesta para particionamiento
) PARTITION BY RANGE (lower(fecha_ocurrencia));

-- Crear particiones (Ejemplo inicial, añadir más según necesidad)
CREATE TABLE hechos_pre_2020 PARTITION OF hechos
    FOR VALUES FROM (MINVALUE) TO ('2020-01-01 00:00:00+00');
CREATE TABLE hechos_2020 PARTITION OF hechos
    FOR VALUES FROM ('2020-01-01 00:00:00+00') TO ('2021-01-01 00:00:00+00');
CREATE TABLE hechos_2021 PARTITION OF hechos
    FOR VALUES FROM ('2021-01-01 00:00:00+00') TO ('2022-01-01 00:00:00+00');
CREATE TABLE hechos_2022 PARTITION OF hechos
    FOR VALUES FROM ('2022-01-01 00:00:00+00') TO ('2023-01-01 00:00:00+00');
CREATE TABLE hechos_2023 PARTITION OF hechos
    FOR VALUES FROM ('2023-01-01 00:00:00+00') TO ('2024-01-01 00:00:00+00');
CREATE TABLE hechos_2024 PARTITION OF hechos
    FOR VALUES FROM ('2024-01-01 00:00:00+00') TO ('2025-01-01 00:00:00+00');
CREATE TABLE hechos_2025 PARTITION OF hechos
    FOR VALUES FROM ('2025-01-01 00:00:00+00') TO ('2026-01-01 00:00:00+00');
-- Crear partición para el futuro / por defecto
CREATE TABLE hechos_futuros PARTITION OF hechos DEFAULT;

-- 2.2. Entidades
CREATE TABLE entidades (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(300) NOT NULL, -- Aumentado para nombres largos con siglas
    tipo VARCHAR(50) NOT NULL CHECK (tipo IN ('PERSONA', 'ORGANIZACION', 'INSTITUCION', 'LUGAR', 'EVENTO', 'NORMATIVA', 'CONCEPTO')),
    descripcion TEXT,
    alias TEXT[], -- Nombres alternativos, siglas
    fecha_nacimiento TSTZRANGE, -- Para personas o inicio de eventos/organizaciones
    fecha_disolucion TSTZRANGE, -- Para fin de eventos/organizaciones
    wikidata_id VARCHAR(20), -- (CP-008) Confirmar existencia, no añadir más campos de Wikidata aquí
    relevancia INTEGER NOT NULL CHECK (relevancia BETWEEN 1 AND 10) DEFAULT 5,
    metadata JSONB, -- Para detalles específicos del tipo
    embedding vector(384),
    -- Campo para fusión de entidades (IA Nocturna)
    fusionada_en_id BIGINT REFERENCES entidades(id) ON DELETE SET NULL
    -- Nota: Se permiten potenciales duplicados que la lógica de Fase 4 intentará resolver
);

-- 2.3. Artículos (Fuentes)
CREATE TABLE articulos (
    id BIGSERIAL PRIMARY KEY,
    url TEXT UNIQUE, -- URL debe ser única si está presente
    storage_path TEXT NOT NULL UNIQUE, -- Ruta al archivo en Supabase Storage, debe ser única
    medio VARCHAR(100) NOT NULL,
    pais_publicacion VARCHAR(50) NOT NULL,
    tipo_medio VARCHAR(50) NOT NULL CHECK (tipo_medio IN ('diario', 'agencia', 'televisión', 'radio', 'digital', 'oficial', 'blog', 'otro')),
    titular TEXT NOT NULL,
    fecha_publicacion TIMESTAMP WITH TIME ZONE NOT NULL,
    autor VARCHAR(200), -- Aumentado para múltiples autores
    idioma VARCHAR(10) NOT NULL DEFAULT 'es',
    seccion VARCHAR(100),
    etiquetas_fuente TEXT[],
    es_opinion BOOLEAN NOT NULL DEFAULT false,
    es_oficial BOOLEAN NOT NULL DEFAULT false,
    resumen TEXT, -- Resumen generado en Fase 2
    categorias_asignadas TEXT[], -- Categorías asignadas en Fase 2
    puntuacion_relevancia INTEGER CHECK (puntuacion_relevancia BETWEEN 0 AND 10), -- Asignada en Fase 2
    fecha_recopilacion TIMESTAMP WITH TIME ZONE NOT NULL,
    fecha_procesamiento TIMESTAMP WITH TIME ZONE, -- Timestamp de fin de Fase 5
    estado_procesamiento VARCHAR(50) DEFAULT 'pendiente' CHECK (estado_procesamiento IN ('pendiente', 'procesando', 'completado', 'error_prefiltrado', 'error_relevancia', 'error_extraccion', 'error_normalizacion', 'error_bd')),
    error_detalle TEXT,
    -- Validación de formato de storage_path
    CONSTRAINT check_storage_path_format CHECK (storage_path ~ '^[^/]+/\d{4}/\d{2}/\d{2}/[^/]+\.(html|txt)\.gz$')
    -- No almacenamos contenido_texto aquí, está en Storage.
);

-- Optimización para textos largos
ALTER TABLE articulos ALTER COLUMN titular SET STORAGE EXTENDED;
ALTER TABLE articulos ALTER COLUMN resumen SET STORAGE EXTENDED;

-- 2.4. Hilos Narrativos
CREATE TABLE hilos_narrativos (
    id SERIAL PRIMARY KEY, -- SERIAL normal puede ser suficiente aquí
    titulo VARCHAR(255) NOT NULL UNIQUE,
    descripcion TEXT,
    -- Campos nuevos para el modelo de tres memorias
    descripcion_hilo_curada TEXT, -- Ángulo editorial que guía la narrativa
    criterios_consulta_estructurados JSONB, -- (CP-003) Parámetros para query_tools del module_chat_interface, usados por hilo_updater.py
    lista_elementos_ids_actualizada JSONB, -- Lista dinámica de IDs de elementos relevantes
    puntos_clave_novedades TEXT, -- Resumen de cambios significativos
    -- Campos originales
    fecha_inicio_seguimiento DATE NOT NULL DEFAULT CURRENT_DATE,
    fecha_ultimo_hecho DATE, -- Actualizado por Trigger o Job
    estado VARCHAR(50) NOT NULL DEFAULT 'activo' CHECK (estado IN ('activo', 'inactivo', 'resuelto', 'historico')),
    paises_principales VARCHAR(100)[],
    etiquetas_principales TEXT[],
    relevancia_editorial INTEGER NOT NULL CHECK (relevancia_editorial BETWEEN 1 AND 10) DEFAULT 5,
    embedding vector(384) -- Embedding del título/descripción para buscar hilos similares
);

-- 2.5. Citas Textuales
CREATE TABLE citas_textuales (
    id BIGSERIAL PRIMARY KEY,
    cita TEXT NOT NULL,
    entidad_emisora_id BIGINT REFERENCES entidades(id) ON DELETE SET NULL, -- Vinculado en Fase 4/5
    articulo_id BIGINT REFERENCES articulos(id) ON DELETE CASCADE,
    hecho_contexto_id BIGINT, -- Hecho donde apareció la cita (opcional)
    fecha_cita TIMESTAMP WITH TIME ZONE, -- Fecha específica de la cita, si se conoce
    contexto TEXT, -- Contexto breve de la cita
    etiquetas TEXT[], -- Lista flexible de etiquetas temáticas/entidades que se puebla con content_tagger.py
    relevancia INTEGER NOT NULL CHECK (relevancia BETWEEN 1 AND 5) DEFAULT 3,
    fecha_ingreso TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    embedding vector(384), -- Embedding de la cita
    documento_id BIGINT REFERENCES documentos_extensos(id) ON DELETE SET NULL,
    fragmento_id BIGINT REFERENCES fragmentos_extensos(id) ON DELETE SET NULL
);

-- 2.6. Datos Cuantitativos
CREATE TABLE datos_cuantitativos (
    id BIGSERIAL PRIMARY KEY,
    hecho_id BIGINT, -- Hecho donde se mencionó el dato
    articulo_id BIGINT REFERENCES articulos(id) ON DELETE CASCADE,
    indicador VARCHAR(200) NOT NULL,
    categoria VARCHAR(50) NOT NULL CHECK (categoria IN ('económico', 'demográfico', 'electoral', 'social', 'presupuestario', 'sanitario', 'ambiental', 'conflicto', 'otro')),
    valor_numerico NUMERIC NOT NULL,
    unidad VARCHAR(50) NOT NULL,
    ambito_geografico VARCHAR(100)[] NOT NULL, -- País, Región, Ciudad
    periodo_referencia_inicio DATE,
    periodo_referencia_fin DATE,
    tipo_periodo VARCHAR(50) CHECK (tipo_periodo IN ('anual', 'trimestral', 'mensual', 'semanal', 'diario', 'puntual', 'acumulado', NULL)),
    valor_anterior NUMERIC,
    variacion_absoluta NUMERIC,
    variacion_porcentual NUMERIC,
    tendencia VARCHAR(20) CHECK (tendencia IN ('aumento', 'disminución', 'estable', NULL)),
    fuente_especifica VARCHAR(150), -- Fuente del dato (INE, BCV, FMI, etc.)
    segmento_poblacion VARCHAR(100), -- Si aplica a un grupo específico
    notas TEXT, -- Notas aclaratorias o sobre posibles contradicciones
    fecha_registro TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    embedding vector(384), -- Embedding del indicador + contexto
    documento_id BIGINT REFERENCES documentos_extensos(id) ON DELETE SET NULL,
    fragmento_id BIGINT REFERENCES fragmentos_extensos(id) ON DELETE SET NULL
);

-- 2.7. Contradicciones (entre Hechos)
CREATE TABLE contradicciones (
    id SERIAL PRIMARY KEY,
    hecho_principal_id BIGINT NOT NULL, -- No podemos usar FK directo por particionamiento fácil
    fecha_ocurrencia_principal TSTZRANGE NOT NULL, -- Necesario para buscar el hecho principal
    hecho_contradictorio_id BIGINT NOT NULL,
    fecha_ocurrencia_contradictoria TSTZRANGE NOT NULL,
    tipo_contradiccion VARCHAR(50) NOT NULL CHECK (tipo_contradiccion IN ('fecha', 'contenido', 'entidades', 'ubicacion', 'valor', 'completa')),
    grado_contradiccion INTEGER NOT NULL CHECK (grado_contradiccion BETWEEN 1 AND 5),
    descripcion TEXT,
    fecha_deteccion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    ultimo_analisis TIMESTAMP WITH TIME ZONE DEFAULT now(),
    estado_resolucion VARCHAR(50) DEFAULT 'pendiente' CHECK (estado_resolucion IN ('pendiente', 'analizada', 'resuelta', 'ignorada')),
    -- Constraint para evitar auto-contradicción
    CONSTRAINT check_different_hechos CHECK (hecho_principal_id <> hecho_contradictorio_id OR fecha_ocurrencia_principal <> fecha_ocurrencia_contradictoria)
    -- Nota: Se necesitarán funciones o lógica aplicativa para referenciar correctamente los hechos particionados.
);

-- 2.8. Eventos Programados (Vinculada a Hechos)
CREATE TABLE eventos_programados (
    hecho_id BIGINT NOT NULL, -- Clave primaria y foránea
    fecha_ocurrencia_hecho TSTZRANGE NOT NULL, -- Necesario para buscar el hecho
    fecha_programada TSTZRANGE NOT NULL, -- Puede ser más precisa que la del hecho
    estado VARCHAR(50) NOT NULL DEFAULT 'programado' CHECK (estado IN ('programado', 'confirmado', 'cancelado', 'modificado', 'realizado')),
    recordatorio_dias INTEGER[] DEFAULT '{1, 7, 30}',
    fuentes_oficiales TEXT[],
    url_evento TEXT,
    notas_seguimiento TEXT,
    ultima_verificacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    responsable_seguimiento VARCHAR(100),
    prioridad_cobertura INTEGER NOT NULL CHECK (prioridad_cobertura BETWEEN 1 AND 5) DEFAULT 3,
    -- Constraints
    CONSTRAINT eventos_programados_pkey PRIMARY KEY (hecho_id, fecha_ocurrencia_hecho)
    -- FK a hechos es implícita por la lógica de triggers/aplicación
);

-- 2.9. Caché de Entidades (Para Fase 4)
CREATE TABLE cache_entidades (
    id BIGINT PRIMARY KEY, -- Mismo ID que en la tabla entidades
    nombre VARCHAR(300) NOT NULL,
    alias TEXT[],
    tipo VARCHAR(50) NOT NULL
    -- No incluir descripción, metadata, etc. para mantenerla ligera.
);

-- 2.10. Consultas Guardadas (Para Módulo de Consulta)
CREATE TABLE consultas_guardadas (
    id SERIAL PRIMARY KEY,
    nombre_consulta VARCHAR(255) NOT NULL UNIQUE,
    descripcion TEXT,
    parametros_json JSONB NOT NULL, -- Criterios de búsqueda guardados
    -- usuario_id INTEGER, -- Si hubiera multiusuario
    fecha_creacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    ultima_ejecucion TIMESTAMP WITH TIME ZONE,
    frecuencia_uso INTEGER DEFAULT 0
);

-- 4. Tablas de Relaciones

-- 4.1. Hecho ↔ Entidad
CREATE TABLE hecho_entidad (
    hecho_id BIGINT NOT NULL,
    fecha_ocurrencia_hecho TSTZRANGE NOT NULL, -- Para FK a tabla particionada
    entidad_id BIGINT NOT NULL REFERENCES entidades(id) ON DELETE CASCADE,
    tipo_relacion VARCHAR(50) NOT NULL CHECK (tipo_relacion IN ('protagonista', 'mencionado', 'afectado', 'declarante', 'ubicacion', 'contexto', 'victima', 'agresor', 'organizador', 'participante', 'otro')),
    relevancia_en_hecho INTEGER NOT NULL CHECK (relevancia_en_hecho BETWEEN 1 AND 10) DEFAULT 5,
    -- Clave primaria compuesta
    PRIMARY KEY (hecho_id, fecha_ocurrencia_hecho, entidad_id, tipo_relacion)
    -- FK a hechos es implícita
);

-- 4.2. Hecho ↔ Artículo (Fuente)
CREATE TABLE hecho_articulo (
    hecho_id BIGINT NOT NULL,
    fecha_ocurrencia_hecho TSTZRANGE NOT NULL, -- Para FK a tabla particionada
    articulo_id BIGINT NOT NULL REFERENCES articulos(id) ON DELETE CASCADE,
    texto_citado TEXT, -- Fragmento específico del artículo (opcional)
    posicion_en_articulo INTEGER, -- Posición aproximada (ej. número de párrafo) (opcional)
    es_fuente_primaria BOOLEAN NOT NULL DEFAULT false, -- ¿El artículo es la primera fuente conocida?
    confirma_hecho BOOLEAN NOT NULL DEFAULT true, -- ¿Esta fuente confirma o contradice el hecho?
    -- Clave primaria compuesta
    PRIMARY KEY (hecho_id, fecha_ocurrencia_hecho, articulo_id)
    -- FK a hechos es implícita
);

-- 4.3. Hecho ↔ Hecho (Relaciones entre hechos)
CREATE TABLE hecho_relacionado (
    hecho_origen_id BIGINT NOT NULL,
    fecha_ocurrencia_origen TSTZRANGE NOT NULL,
    hecho_destino_id BIGINT NOT NULL,
    fecha_ocurrencia_destino TSTZRANGE NOT NULL,
    tipo_relacion VARCHAR(50) NOT NULL CHECK (tipo_relacion IN ('causa', 'consecuencia', 'contexto_historico', 'respuesta_a', 'aclaracion_de', 'version_alternativa', 'seguimiento_de')),
    fuerza_relacion INTEGER NOT NULL CHECK (fuerza_relacion BETWEEN 1 AND 10) DEFAULT 5,
    descripcion_relacion TEXT,
    fecha_deteccion TIMESTAMP WITH TIME ZONE DEFAULT now(),
    -- Clave primaria
    PRIMARY KEY (hecho_origen_id, fecha_ocurrencia_origen, hecho_destino_id, fecha_ocurrencia_destino, tipo_relacion),
    -- Evitar auto-relaciones directas (aunque una versión alternativa sí podría ser el mismo ID base)
    CONSTRAINT check_different_related_hechos CHECK (hecho_origen_id <> hecho_destino_id OR fecha_ocurrencia_origen <> fecha_ocurrencia_destino)
);

-- 4.4. Hecho ↔ Hilo Narrativo
CREATE TABLE hecho_hilo (
    hecho_id BIGINT NOT NULL,
    fecha_ocurrencia_hecho TSTZRANGE NOT NULL, -- Para FK a tabla particionada
    hilo_id INTEGER NOT NULL REFERENCES hilos_narrativos(id) ON DELETE CASCADE,
    relevancia_en_hilo INTEGER NOT NULL CHECK (relevancia_en_hilo BETWEEN 1 AND 10) DEFAULT 5,
    es_hito_clave BOOLEAN NOT NULL DEFAULT false,
    -- Clave primaria compuesta
    PRIMARY KEY (hecho_id, fecha_ocurrencia_hecho, hilo_id)
    -- FK a hechos es implícita
);

-- 4.5. Entidad ↔ Entidad (Relaciones estructurales)
CREATE TABLE entidad_relacion (
    entidad_origen_id BIGINT NOT NULL REFERENCES entidades(id) ON DELETE CASCADE,
    entidad_destino_id BIGINT NOT NULL REFERENCES entidades(id) ON DELETE CASCADE,
    tipo_relacion VARCHAR(50) NOT NULL CHECK (tipo_relacion IN ('miembro_de', 'subsidiaria_de', 'aliado_con', 'opositor_a', 'sucesor_de', 'predecesor_de', 'casado_con', 'familiar_de', 'empleado_de')),
    descripcion TEXT,
    fecha_inicio TIMESTAMP WITH TIME ZONE,
    fecha_fin TIMESTAMP WITH TIME ZONE,
    fuerza_relacion INTEGER NOT NULL CHECK (fuerza_relacion BETWEEN 1 AND 10) DEFAULT 5,
    -- Clave primaria
    PRIMARY KEY (entidad_origen_id, entidad_destino_id, tipo_relacion),
    -- Evitar auto-relaciones
    CONSTRAINT check_different_related_entities CHECK (entidad_origen_id <> entidad_destino_id)
);

-- 4.6. Entidad ↔ Fragmento (Nueva relación para Modelo de Tres Memorias)
CREATE TABLE entidad_fragmento (
    entidad_id BIGINT NOT NULL REFERENCES entidades(id) ON DELETE CASCADE,
    fragmento_id BIGINT NOT NULL REFERENCES fragmentos_extensos(id) ON DELETE CASCADE,
    documento_id BIGINT NOT NULL REFERENCES documentos_extensos(id) ON DELETE CASCADE,
    PRIMARY KEY (entidad_id, fragmento_id, documento_id)
);

CREATE INDEX idx_entidad_fragmento_entidad_id ON entidad_fragmento(entidad_id);
CREATE INDEX idx_entidad_fragmento_fragmento_id ON entidad_fragmento(fragmento_id);
CREATE INDEX idx_entidad_fragmento_documento_id ON entidad_fragmento(documento_id);

-- 5. Tablas de Soporte

-- 5.1. Dimensión Temporal
CREATE TABLE dimension_tiempo (
    id SERIAL PRIMARY KEY,
    fecha DATE UNIQUE NOT NULL,
    anio INTEGER NOT NULL,
    trimestre INTEGER,
    mes INTEGER NOT NULL,
    semana INTEGER,
    dia INTEGER NOT NULL,
    dia_semana INTEGER, -- 0 = Domingo, 1 = Lunes, ..., 6 = Sábado
    es_feriado BOOLEAN DEFAULT false,
    siglo INTEGER,
    decada VARCHAR(10),
    periodo_historico VARCHAR(100)[] -- Ej: {'Guerra Fría', 'Dictaduras Cono Sur'}
);
-- Poblar esta tabla con un script o función para el rango deseado (ej. 1950-2050)

-- 5.2. Feedback del Usuario (Para Módulo de Consulta)
CREATE TABLE consultas_usuario (
    id BIGSERIAL PRIMARY KEY,
    consulta_original TEXT NOT NULL,
    consulta_sql_generada TEXT, -- SQL generado por MCP/LLM
    parametros_json JSONB, -- Parámetros usados en herramientas MCP
    tipo_consulta VARCHAR(50),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    duracion_procesamiento_ms INTEGER,
    total_resultados INTEGER,
    calificacion_usuario INTEGER CHECK (calificacion_usuario BETWEEN 1 AND 5),
    comentario_usuario TEXT,
    consulta_exitosa BOOLEAN DEFAULT true NOT NULL,
    error_detalle TEXT
    -- usuario_id INTEGER -- Si hubiera multiusuario
);

CREATE TABLE sugerencias_mejora (
    id SERIAL PRIMARY KEY,
    consulta_id BIGINT REFERENCES consultas_usuario(id) ON DELETE SET NULL,
    tipo_sugerencia VARCHAR(50) NOT NULL CHECK (tipo_sugerencia IN ('correccion_hecho', 'correccion_entidad', 'nueva_fuente', 'conexion_faltante', 'hilo_nuevo', 'otro')),
    referencia_id BIGINT, -- ID del hecho, entidad, etc. al que se refiere
    referencia_tabla VARCHAR(50),
    contenido TEXT NOT NULL,
    procesada BOOLEAN NOT NULL DEFAULT false,
    fecha_sugerencia TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
    -- usuario_id INTEGER
);

-- INICIO DE MODIFICACIÓN: Añadir tablas sugerencias_hilos_nuevos y analisis_narrativo_historico

-- 5.3. Tabla para Sugerencias de Nuevos Hilos Narrativos (IA Nocturna / Dashboard)
CREATE TABLE sugerencias_hilos_nuevos (
    id SERIAL PRIMARY KEY,
    titulo_sugerido VARCHAR(255) NOT NULL,
    descripcion_curada_sugerida TEXT,
    criterios_consulta_sugeridos JSONB, -- Borrador de parámetros para query_tools
    justificacion TEXT, -- Por qué es notable/novedoso
    score_potencial FLOAT, -- Puntuación de interés/novedad
    hechos_fundamentan_ids BIGINT[], -- IDs de hechos que llevaron a la sugerencia
    entidades_fundamentan_ids BIGINT[], -- IDs de entidades clave
    fecha_sugerencia TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    estado_revision VARCHAR(50) NOT NULL DEFAULT 'pendiente_revision' CHECK (estado_revision IN ('pendiente_revision', 'aceptado', 'descartado', 'fusionado')),
    revisado_por VARCHAR(100), -- ID o nombre del usuario que revisó
    fecha_revision TIMESTAMP WITH TIME ZONE,
    notas_revision TEXT
);

CREATE INDEX idx_sug_hilos_estado ON sugerencias_hilos_nuevos(estado_revision);
CREATE INDEX idx_sug_hilos_fecha ON sugerencias_hilos_nuevos(fecha_sugerencia DESC);
CREATE INDEX idx_sug_hilos_score ON sugerencias_hilos_nuevos(score_potencial DESC NULLS LAST);

-- 5.4. Tabla para Historial de Análisis Narrativo (Memoria IA Nocturna)
CREATE TABLE analisis_narrativo_historico (
    id BIGSERIAL PRIMARY KEY,
    fecha_analisis DATE NOT NULL DEFAULT CURRENT_DATE,
    tipo_analisis VARCHAR(100) NOT NULL, -- Ej: 'cluster_semantico_hechos_recientes', 'centralidad_entidades_periodo', 'conexion_serendipia_detectada'
    parametros_analisis JSONB, -- Parámetros usados para el análisis
    resultado_analisis JSONB, -- Resumen del resultado (ej. IDs de clusters, entidades centrales, descripción de conexión)
    elementos_implicados_ids JSONB, -- {'hechos': [id1, id2], 'entidades': [id3, id4]}
    observaciones TEXT, -- Notas adicionales sobre el análisis
    hash_config_resultado TEXT UNIQUE -- Para evitar duplicar análisis idénticos si los datos no cambian
);

CREATE INDEX idx_analisis_narr_fecha_tipo ON analisis_narrativo_historico(fecha_analisis DESC, tipo_analisis);

-- FIN DE MODIFICACIÓN

-- INICIO NUEVAS TABLAS (CP-004)
-- Tabla para registrar el feedback editorial sobre la importancia de los hechos (CP-004)
CREATE TABLE feedback_importancia_hechos (
    id BIGSERIAL PRIMARY KEY,
    hecho_id BIGINT NOT NULL,
    fecha_ocurrencia_hecho TSTZRANGE NOT NULL, -- Para FK a hechos particionados
    importancia_asignada_sistema INTEGER, -- Importancia asignada por el modelo de ML del pipeline
    importancia_editor_final INTEGER,    -- Importancia final tras revisión/confirmación editorial
    usuario_id_editor VARCHAR(100),
    timestamp_feedback TIMESTAMP WITH TIME ZONE DEFAULT now(),
    CONSTRAINT fk_hecho_feedback_imp FOREIGN KEY (hecho_id, fecha_ocurrencia_hecho) REFERENCES hechos(id, fecha_ocurrencia) ON DELETE CASCADE
);
CREATE INDEX idx_feedback_imp_hecho_id_ref ON feedback_importancia_hechos(hecho_id, fecha_ocurrencia_hecho);
CREATE INDEX idx_feedback_imp_ts ON feedback_importancia_hechos(timestamp_feedback);

-- Tabla para almacenar el contexto de tendencias diario procesado por la IA Nocturna (CP-004)
CREATE TABLE tendencias_contexto_diario (
    id SERIAL PRIMARY KEY,
    fecha_contexto DATE UNIQUE NOT NULL, -- Para qué día es este contexto
    etiquetas_tendencia JSONB,         -- Ej: {"tema1": {"score": 0.9, "cambio_pct": 20}, ...}
    entidades_tendencia JSONB,         -- Ej: {"entidad_id_X": {"score_relevancia": 8.5}, ...}
    eventos_proximos_relevantes JSONB, -- Ej: [{"hecho_id": 123, "prioridad": 5, ...}]
    hilos_activos_calientes JSONB,     -- Ej: [{"hilo_id": 42, "actividad": "alta", ...}]
    combinaciones_clave_importantes JSONB, -- Ej: [{"paises": ["A","B"], "tema": "X", "importancia_ctx": "alta"}]
    -- Otros campos JSONB según se definan los análisis de tendencias
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT now()
);
CREATE INDEX idx_tendencias_ctx_fecha ON tendencias_contexto_diario(fecha_contexto DESC);
-- FIN NUEVAS TABLAS (CP-004)

-- INICIO NUEVA TABLA (CP-009)
-- Tabla para Eventos Recurrentes Anuales (Efemérides, Celebraciones) (CP-009)
CREATE TABLE eventos_recurrentes_anuales (
    id SERIAL PRIMARY KEY,
    dia SMALLINT NOT NULL CHECK (dia BETWEEN 1 AND 31),
    mes SMALLINT NOT NULL CHECK (mes BETWEEN 1 AND 12),
    titulo_evento VARCHAR(255) NOT NULL,
    descripcion TEXT,
    tipo_evento VARCHAR(50) NOT NULL CHECK (tipo_evento IN ('efemeride_historica', 'celebracion_cultural', 'dia_internacional', 'aniversario_hito_local', 'otro')),
    año_origen INTEGER, -- Opcional, para calcular aniversarios exactos
    ambito VARCHAR(100), -- Ej: 'Global', 'Nacional (España)'
    relevancia_editorial INTEGER CHECK (relevancia_editorial BETWEEN 1 AND 5) DEFAULT 3,
    enlaces_referencia TEXT[],
    ultima_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT now(),
    CONSTRAINT uq_evento_recurrente_dia_mes_titulo UNIQUE (dia, mes, titulo_evento)
);

CREATE INDEX idx_eventos_rec_dia_mes ON eventos_recurrentes_anuales(mes, dia);
CREATE INDEX idx_eventos_rec_tipo ON eventos_recurrentes_anuales(tipo_evento);
-- FIN NUEVA TABLA (CP-009)


-- 6. Tablas para Monitorización (Interfaz Desarrollador)

-- 6.1. Estado del Sistema
CREATE TABLE system_status (
    component_name VARCHAR(100) PRIMARY KEY,
    status VARCHAR(10) NOT NULL CHECK (status IN ('OK', 'WARN', 'ERROR', 'INIT', 'STOPPED')),
    last_heartbeat TIMESTAMP WITH TIME ZONE NOT NULL,
    message TEXT,
    metrics JSONB,
    threshold_values JSONB DEFAULT NULL -- Umbrales para detección proactiva
);
CREATE INDEX idx_system_status_status ON system_status(status);
CREATE INDEX idx_system_status_last_heartbeat ON system_status(last_heartbeat DESC);

-- 6.2. Snapshots Históricos
CREATE TABLE system_status_daily_snapshot (
    snapshot_date DATE PRIMARY KEY,
    components_ok INTEGER NOT NULL,
    components_warn INTEGER NOT NULL,
    components_error INTEGER NOT NULL,
    notable_events JSONB -- Solo eventos importantes del día
);

-- 6.3. Alertas Pendientes
CREATE TABLE alert_inbox (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    component_name VARCHAR(100) NOT NULL, -- No FK directa para evitar bloqueo si se borra el componente
    alert_type VARCHAR(50) NOT NULL, -- Ej: 'status_change_to_error', 'metric_threshold_exceeded'
    message TEXT NOT NULL,
    acknowledged BOOLEAN NOT NULL DEFAULT false,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    severity VARCHAR(10) DEFAULT 'WARN' CHECK (severity IN ('INFO', 'WARN', 'ERROR', 'CRITICAL')) -- Añadir severidad
);
CREATE INDEX idx_alert_inbox_acknowledged_severity ON alert_inbox(acknowledged, severity DESC, created_at DESC) WHERE NOT acknowledged;

-- 7. Gestión de Errores Persistentes
CREATE TABLE articulos_error_persistente (
    id SERIAL PRIMARY KEY,
    articulo_id BIGINT NOT NULL REFERENCES articulos(id) ON DELETE CASCADE,
    componente VARCHAR(100) NOT NULL, -- Componente donde ocurrió el último error
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL,
    primer_error_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    ultimo_error_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    proximo_reintento TIMESTAMP WITH TIME ZONE,
    error_history JSONB NOT NULL DEFAULT '[]', -- Array JSON: {timestamp, componente, tipo_error, mensaje}
    severidad VARCHAR(20) NOT NULL DEFAULT 'media' CHECK (severidad IN ('baja', 'media', 'alta', 'critica')),
    estado VARCHAR(30) NOT NULL DEFAULT 'en_reintentos' CHECK (estado IN ('en_reintentos', 'intervencion_requerida', 'en_diagnostico', 'resuelto', 'descartado')),
    requiere_intervencion BOOLEAN NOT NULL DEFAULT false,
    intervencion_asignado_a VARCHAR(100),
    intervencion_timestamp TIMESTAMP WITH TIME ZONE,
    intervencion_accion VARCHAR(50),
    intervencion_notas TEXT
);

-- Índices Clave
CREATE INDEX idx_articulos_error_estado_severidad ON articulos_error_persistente(estado, severidad);
CREATE INDEX idx_articulos_error_reintento_idx ON articulos_error_persistente(proximo_reintento) WHERE estado = 'en_reintentos' AND proximo_reintento IS NOT NULL;
CREATE INDEX idx_articulos_error_articulo_id ON articulos_error_persistente(articulo_id);
CREATE INDEX idx_articulos_error_componente ON articulos_error_persistente(componente);

-- 8. Detección de Duplicados de Hechos
CREATE TABLE posibles_duplicados_hechos (
    id SERIAL PRIMARY KEY,
    hecho_nuevo_id BIGINT NOT NULL, -- Referencia al hecho que activó la posible detección
    fecha_ocurrencia_nuevo TSTZRANGE NOT NULL, -- Para buscarlo en particiones
    hecho_existente_id BIGINT NOT NULL, -- Referencia al hecho existente con el que podría ser duplicado
    fecha_ocurrencia_existente TSTZRANGE NOT NULL, -- Para buscarlo en particiones
    fecha_deteccion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    procesado_por_ia BOOLEAN DEFAULT false,
    resultado_ia VARCHAR(50), -- Ej: 'EQUIVALENTE', 'COMPLEMENTARIO', 'CONTRADICTORIO', 'RELACIONADO', 'DISTINTO'
    fecha_procesamiento_ia TIMESTAMP WITH TIME ZONE,
    score_similitud FLOAT, -- Puntuación calculada por la IA Nocturna
    notas TEXT
);
CREATE INDEX idx_posibles_duplicados_procesado ON posibles_duplicados_hechos(procesado_por_ia) WHERE procesado_por_ia = false;

-- 9. Índices Estratégicos

-- 9.1. Índices para Tabla Hechos
CREATE INDEX idx_hechos_contenido_gin ON hechos USING gin(to_tsvector('spanish', contenido));
CREATE INDEX idx_hechos_fecha_gist ON hechos USING gist(fecha_ocurrencia);
CREATE INDEX idx_hechos_tipo ON hechos(tipo_hecho);
CREATE INDEX idx_hechos_pais_gin ON hechos USING gin(pais);
CREATE INDEX idx_hechos_etiquetas_gin ON hechos USING gin(etiquetas);
CREATE INDEX idx_hechos_importancia ON hechos(importancia DESC);
CREATE INDEX idx_hechos_fecha_ingreso ON hechos(fecha_ingreso DESC);
CREATE INDEX idx_hechos_embedding_ivfflat ON hechos USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100); -- Ajustar listas
CREATE INDEX idx_hechos_documento_id ON hechos(documento_id);
CREATE INDEX idx_hechos_fragmento_id ON hechos(fragmento_id);
CREATE INDEX idx_hechos_evaluacion_editorial ON hechos(evaluacion_editorial); -- (CP-005)
CREATE INDEX idx_hechos_consenso_fuentes ON hechos(consenso_fuentes); -- (CP-005)


-- 9.2. Índices para Tabla Entidades
CREATE INDEX idx_entidades_nombre_trgm ON entidades USING gin(nombre gin_trgm_ops); -- Para búsqueda por similitud
CREATE INDEX idx_entidades_alias_gin ON entidades USING gin(alias);
CREATE INDEX idx_entidades_tipo ON entidades(tipo);
CREATE INDEX idx_entidades_embedding_ivfflat ON entidades USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_entidades_fusionada_en_id ON entidades(fusionada_en_id); -- Para búsqueda de entidades fusionadas

-- 9.3. Índices para Tabla Artículos
CREATE INDEX idx_articulos_fecha_pub ON articulos(fecha_publicacion DESC);
CREATE INDEX idx_articulos_medio ON articulos(medio);
CREATE INDEX idx_articulos_pais_pub ON articulos(pais_publicacion);
CREATE INDEX idx_articulos_storage_path ON articulos(storage_path);

-- 9.4. Índices para Tabla Hilos Narrativos
CREATE INDEX idx_hilos_titulo_trgm ON hilos_narrativos USING gin(titulo gin_trgm_ops);
CREATE INDEX idx_hilos_estado ON hilos_narrativos(estado);
CREATE INDEX idx_hilos_fecha_ultimo ON hilos_narrativos(fecha_ultimo_hecho DESC NULLS LAST);
CREATE INDEX idx_hilos_etiquetas_gin ON hilos_narrativos USING gin(etiquetas_principales);
CREATE INDEX idx_hilos_embedding_ivfflat ON hilos_narrativos USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_hilos_criterios_consulta ON hilos_narrativos USING gin(criterios_consulta_estructurados); -- (CP-003)

-- 9.5. Índices para Tabla Citas Textuales
CREATE INDEX idx_citas_entidad_id ON citas_textuales(entidad_emisora_id);
CREATE INDEX idx_citas_articulo_id ON citas_textuales(articulo_id);
CREATE INDEX idx_citas_hecho_id ON citas_textuales(hecho_contexto_id); -- Si se usa
CREATE INDEX idx_citas_cita_gin ON citas_textuales USING gin(to_tsvector('spanish', cita));
CREATE INDEX idx_citas_embedding_ivfflat ON citas_textuales USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_citas_etiquetas_gin ON citas_textuales USING gin(etiquetas);
CREATE INDEX idx_citas_documento_id ON citas_textuales(documento_id);
CREATE INDEX idx_citas_fragmento_id ON citas_textuales(fragmento_id);

-- 9.6. Índices para Tabla Datos Cuantitativos
CREATE INDEX idx_datos_hecho_id ON datos_cuantitativos(hecho_id);
CREATE INDEX idx_datos_indicador_trgm ON datos_cuantitativos USING gin(indicador gin_trgm_ops);
CREATE INDEX idx_datos_categoria ON datos_cuantitativos(categoria);
CREATE INDEX idx_datos_ambito_gin ON datos_cuantitativos USING gin(ambito_geografico);
CREATE INDEX idx_datos_periodo ON datos_cuantitativos(periodo_referencia_inicio, periodo_referencia_fin);
CREATE INDEX idx_datos_embedding_ivfflat ON datos_cuantitativos USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_datos_documento_id ON datos_cuantitativos(documento_id);
CREATE INDEX idx_datos_fragmento_id ON datos_cuantitativos(fragmento_id);

-- 9.7. Índices para Tabla Cache Entidades
-- Índice GIN/Trigram para búsqueda rápida por similitud de nombre (esencial Fase 4)
CREATE INDEX idx_cache_entidades_nombre_trgm ON cache_entidades USING gin(nombre gin_trgm_ops);

-- Índice GIN para búsqueda eficiente en el array de alias (esencial Fase 4)
CREATE INDEX idx_cache_entidades_alias_gin ON cache_entidades USING gin(alias);

-- Índice B-Tree estándar para filtrar por tipo
CREATE INDEX idx_cache_entidades_tipo ON cache_entidades(tipo);

-- 9.8. Índices para Tablas de Relación
CREATE INDEX idx_hecho_entidad_entidad_id ON hecho_entidad(entidad_id);
CREATE INDEX idx_hecho_articulo_articulo_id ON hecho_articulo(articulo_id);
CREATE INDEX idx_hecho_hilo_hilo_id ON hecho_hilo(hilo_id);

-- 9.9. Índices para Tablas de Soporte
CREATE INDEX idx_dimension_tiempo_anio_mes_dia ON dimension_tiempo(anio, mes, dia);
CREATE INDEX idx_dimension_tiempo_periodo_gin ON dimension_tiempo USING gin(periodo_historico);