# 📥 Entrada (Input)

# Especificación de Entradas del `module_pipeline`

## 1. Tipos de Entrada

El `module_pipeline` procesa dos tipos principales de entrada:

1. **Datos de artículos (`ArticuloInItem`):** Recibidos del `module_connector`
2. **Datos de fragmentos de documentos:** Recibidos del `module_ingestion_engine`

## 2. Formato de las Entradas

### 2.1. Para Artículos
- **Formato:** Objeto JSON dentro de una solicitud HTTP POST
- **Estructura:** `{"articulo": {...}}`
- **Fuente:** `module_connector`

### 2.2. Para Fragmentos
- **Formato:** Diccionario Python pasado como argumento a función interna (actualmente `_procesar_fragmento` en `controller.py`) o potencialmente un mensaje en cola si se desacopla
- **Estructura:** Incluye el contenido del fragmento y metadatos del documento original (`documento_id`, `fragmento_id`, título, tipo, etc.)
- **Fuente:** `module_ingestion_engine`

## 3. Entrada desde `module_connector`: `ArticuloInItem`

El `module_pipeline` recibe artículos de noticias desde el `module_connector`. La estructura de datos corresponde al modelo Pydantic `ArticuloInItem`, definido en el `module_connector`. El `module_pipeline` debe estar preparado para recibir todos los campos definidos en este modelo.

### 3.1. Definición del Modelo Pydantic `ArticuloInItem`

La siguiente estructura representa el modelo Pydantic `ArticuloInItem` tal como se define en `module_connector/src/models.py`:

```python
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, validator

class ArticuloInItem(BaseModel):
    # --- Campos Principales ---
    url: Optional[str] = None
    storage_path: Optional[str] = None
    fuente: Optional[str] = None
    medio: str  # Requerido por el modelo Pydantic de module_connector
    medio_url_principal: Optional[str] = None
    pais_publicacion: str  # Requerido por el modelo Pydantic de module_connector
    tipo_medio: str  # Requerido por el modelo Pydantic de module_connector
    titular: str  # Requerido por el modelo Pydantic de module_connector
    fecha_publicacion: datetime  # Requerido por el modelo Pydantic de module_connector
    autor: Optional[str] = None
    idioma: Optional[str] = None
    seccion: Optional[str] = None
    etiquetas_fuente: Optional[List[str]] = None
    es_opinion: Optional[bool] = False
    es_oficial: Optional[bool] = False
    
    # --- Campos generados por etapas previas o por el pipeline ---
    resumen: Optional[str] = None
    categorias_asignadas: Optional[List[str]] = None
    puntuacion_relevancia: Optional[float] = None
    
    # --- Campos de Control ---
    fecha_recopilacion: Optional[datetime] = None
    fecha_procesamiento: Optional[datetime] = None
    estado_procesamiento: Optional[str] = "pendiente_connector"  # Valor por defecto en el modelo original
    error_detalle: Optional[str] = None
    
    # --- Contenido del Artículo ---
    contenido_texto: str  # Requerido por el modelo Pydantic de module_connector
    contenido_html: Optional[str] = None
    
    # --- Metadatos Adicionales ---
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        extra = "allow"
```

### 3.2. Campos Requeridos

El modelo `ArticuloInItem` especifica los siguientes campos como obligatorios:

- `medio: str`
- `pais_publicacion: str`
- `tipo_medio: str`
- `titular: str`
- `fecha_publicacion: datetime`
- `contenido_texto: str`

El `module_pipeline` debe verificar la presencia y validez de estos campos al inicio de su procesamiento.

### 3.3. Interacción del `module_pipeline` con los Campos

#### Campos de Entrada Primaria
El `module_pipeline` utilizará principalmente estos campos como base para su análisis:
- `url`, `fuente`, `medio`, `medio_url_principal`, `pais_publicacion`, `tipo_medio`
- `titular`, `fecha_publicacion`, `autor`, `idioma`, `seccion`, `etiquetas_fuente`
- `es_opinion`, `es_oficial`, `contenido_texto`, `contenido_html`, `metadata`

#### Campos Generados/Actualizados por `module_pipeline`
- `resumen`: Generado por la Fase 2. Cualquier valor de entrada será sobrescrito.
- `categorias_asignadas`: Generado por la Fase 2. Cualquier valor de entrada será sobrescrito.
- `puntuacion_relevancia`: Generado por la Fase 4.5. Cualquier valor de entrada será sobrescrito.
- `fecha_procesamiento`: Establecido al finalizar el procesamiento completo.
- `estado_procesamiento`: Actualizado para reflejar el estado a medida que avanza por las fases internas.
- `error_detalle`: Utilizado para registrar detalles de errores durante el procesamiento.

### 3.4. Ejemplo de Objeto JSON `ArticuloInItem`

```json
{
    "url": "https://www.ejemplo.com/noticia/123",
    "storage_path": "/articulos/2023/10/noticia_123.json.gz",
    "fuente": "spider_ejemplo_news",
    "medio": "Diario Ejemplo",
    "medio_url_principal": "https://www.ejemplo.com",
    "pais_publicacion": "País Ficticio",
    "tipo_medio": "Diario Digital",
    "titular": "Titular de Ejemplo para la Noticia",
    "fecha_publicacion": "2023-10-26T10:00:00Z",
    "autor": "Autor de Ejemplo",
    "idioma": "es",
    "seccion": "Actualidad",
    "etiquetas_fuente": ["ejemplo", "noticias", "ficticio"],
    "es_opinion": false,
    "es_oficial": false,
    "resumen": "Este es un resumen que podría venir del connector, pero el pipeline lo regenerará.",
    "categorias_asignadas": ["categoría_del_connector"],
    "puntuacion_relevancia": 7.5,
    "fecha_recopilacion": "2023-10-26T10:05:00Z",
    "fecha_procesamiento": null,
    "estado_procesamiento": "pendiente_pipeline", 
    "error_detalle": null,
    "contenido_texto": "Este es el contenido completo en texto plano del artículo de ejemplo que será procesado por el module_pipeline...",
    "contenido_html": "<html><body><h1>Titular de Ejemplo</h1><p>Este es el contenido HTML original...</p></body></html>",
    "metadata": {
        "palabras_clave_seo": ["ejemplo", "noticia", "desarrollo"],
        "fuente_original_id": "ext-789xyz"
    }
}
```

### 3.5. Notas para el Desarrollador

- El `module_pipeline` debe estar preparado para manejar la estructura completa de `ArticuloInItem` tal como la define el `module_connector`.
- La validación de los campos requeridos por el modelo Pydantic original ya habrá sido realizada por el `module_connector`. Sin embargo, es una buena práctica que el `module_pipeline` también verifique la presencia de los campos indispensables para su funcionamiento.
- El `module_pipeline` tiene la responsabilidad de generar o actualizar los campos específicos según su lógica interna.

## 4. Entrada desde `module_ingestion_engine`: `FragmentoProcesableItem`

El `module_pipeline` también está diseñado para procesar fragmentos de documentos extensos (informes, libros, etc.) gestionados y segmentados por el `module_ingestion_engine`.

**Nota Importante:** La siguiente estructura, denominada `FragmentoProcesableItem`, es una **definición inferida** basada en la documentación actual del `module_ingestion_engine`. Esta estructura debe considerarse una propuesta bien fundamentada, diseñada para ser lo más completa y adaptable posible. El `module_pipeline` deberá ajustarse a la estructura final que provea `module_ingestion_engine`.

### 4.1. Definición del Modelo Pydantic Inferido

```python
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class FragmentoProcesableItem(BaseModel):
    # --- Identificadores Clave ---
    documento_id: str  # ID único del documento original en la tabla `documentos_extensos`. **Esencial.**
    fragmento_id: str  # ID único del fragmento en la tabla `fragmentos_extensos`. **Esencial.**

    # --- Contenido del Fragmento ---
    texto_fragmento: str  # El contenido textual del fragmento a procesar. **Esencial.**
    numero_fragmento: int  # Número secuencial del fragmento dentro del documento. **Esencial.**
    total_fragmentos: int  # Número total de fragmentos generados para el documento original. **Esencial.**
    offset_inicio_fragmento: Optional[int] = None  # Posición de inicio del fragmento en el texto original
    offset_fin_fragmento: Optional[int] = None     # Posición de fin del fragmento en el texto original

    # --- Metadatos Heredados del Documento Original ---
    titulo_documento_original: Optional[str] = None
    tipo_documento_original: Optional[str] = None  # Ej: "informe_anual", "libro_tecnico", "articulo_investigacion"
    fuente_documento_original: Optional[str] = None  # Ej: "Organización Mundial de la Salud"
    autor_documento_original: Optional[str] = None  # Lista de autores separada por comas o campo JSON
    fecha_publicacion_documento_original: Optional[datetime] = None
    idioma_documento_original: Optional[str] = None  # Ej: "es", "en"
    storage_path_documento_original: Optional[str] = None  # Ruta en Supabase Storage del archivo original
    url_documento_original: Optional[str] = None  # URL de referencia del documento original
    metadata_documento_original: Optional[Dict[str, Any]] = None  # Metadatos específicos del documento

    # --- Campos de Control para el Procesamiento del Fragmento ---
    fecha_ingesta_fragmento: datetime  # Timestamp de preparación y envío al pipeline. **Esencial.**
    estado_procesamiento_fragmento: str = "pendiente_pipeline"  # Estado inicial para el pipeline
    error_detalle_fragmento: Optional[str] = None  # Para registrar errores específicos del procesamiento
    
    class Config:
        extra = "allow"  # Flexibilidad si `module_ingestion_engine` envía campos adicionales
```

### 4.2. Campos Esenciales

Para que el `module_pipeline` pueda procesar un fragmento de manera significativa, los siguientes campos se consideran esenciales:

- `documento_id`
- `fragmento_id`
- `texto_fragmento`
- `numero_fragmento`
- `total_fragmentos`
- `fecha_ingesta_fragmento`

### 4.3. Interacción del `module_pipeline` con los Campos

- **Contenido principal:** `texto_fragmento` es la entrada principal para las fases de análisis.
- **Identificadores y metadatos:** Los campos `documento_id`, `fragmento_id` y metadatos del documento original son cruciales para:
  - Contextualizar la información extraída
  - Permitir la vinculación de hechos y entidades tanto al fragmento específico como al documento maestro
  - Posibilitar análisis que consideren el documento completo a través de sus fragmentos
- **Campos de control:** `estado_procesamiento_fragmento` y `error_detalle_fragmento` son gestionados por el `module_pipeline` para rastrear el progreso y posibles problemas.

### 4.4. Ejemplo de Objeto JSON `FragmentoProcesableItem`

```json
{
    "documento_id": "doc_xyz_789",
    "fragmento_id": "frag_xyz_789_part_002",
    "texto_fragmento": "Este es el segundo fragmento del documento extenso. Contiene información detallada sobre las implicaciones económicas de la nueva regulación propuesta. Se espera que el pipeline extraiga los datos cuantitativos y las entidades relevantes mencionadas aquí.",
    "numero_fragmento": 2,
    "total_fragmentos": 15,
    "offset_inicio_fragmento": 4096,
    "offset_fin_fragmento": 8192,
    "titulo_documento_original": "Análisis Exhaustivo de la Nueva Regulación Económica Global",
    "tipo_documento_original": "informe_investigacion",
    "fuente_documento_original": "Instituto Internacional de Estudios Económicos",
    "autor_documento_original": "Dra. Elena Silva, Dr. Juan Pérez",
    "fecha_publicacion_documento_original": "2023-09-15T00:00:00Z",
    "idioma_documento_original": "es",
    "storage_path_documento_original": "/documentos_extensos/2023/informe_regulacion_global.pdf",
    "url_documento_original": "https://iiee.org/informes/regulacion_global_2023",
    "metadata_documento_original": {
        "isbn": "978-3-16-148410-0",
        "palabras_clave_fuente": ["economía global", "regulación", "impacto financiero"],
        "departamento_origen": "Investigación Macroeconómica"
    },
    "fecha_ingesta_fragmento": "2023-10-27T14:30:00Z",
    "estado_procesamiento_fragmento": "pendiente_pipeline",
    "error_detalle_fragmento": null
}
```

### 4.5. Notas para el Desarrollador

- Esta estructura es una propuesta. La implementación final dependerá de la salida real del `module_ingestion_engine`.
- El `module_pipeline` debe ser capaz de procesar fragmentos individualmente, pero también utilizar la información contextual del documento original para enriquecer el análisis.
- La persistencia de los datos extraídos de un fragmento deberá referenciar tanto al `fragmento_id` como al `documento_id`.
- Se debe considerar cómo se manejarán los campos resultado del procesamiento (resúmenes, categorías, relevancia) a nivel de fragmento y si/cómo se agregan a nivel de documento.
