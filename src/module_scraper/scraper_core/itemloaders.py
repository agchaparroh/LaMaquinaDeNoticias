# ItemLoaders para el procesamiento de datos extraídos
#
# Define procesadores de entrada y salida para normalizar y limpiar datos

from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose, Join, Compose, Identity
from w3lib.html import remove_tags, replace_escape_chars
from datetime import datetime, timedelta
import re
from typing import Union, List, Optional
import unicodedata


def clean_text(text: str) -> str:
    """
    Limpia el texto eliminando espacios extra, caracteres especiales y normalizando.
    """
    if not text:
        return ''
    
    # Normalizar caracteres Unicode (NFD -> NFC)
    text = unicodedata.normalize('NFC', text)
    
    # Reemplazar caracteres de escape HTML
    text = replace_escape_chars(text)
    
    # Eliminar espacios múltiples
    text = re.sub(r'\s+', ' ', text)
    
    # Eliminar espacios al inicio y final
    text = text.strip()
    
    return text


def extract_text_from_html(html: str) -> str:
    """
    Extrae texto limpio de HTML eliminando todas las etiquetas.
    """
    if not html:
        return ''
    
    # Eliminar tags HTML
    text = remove_tags(html)
    
    # Limpiar el texto resultante
    text = clean_text(text)
    
    return text


def parse_and_format_date_processor(date_str_list):
    """
    Procesador para ItemLoader que parsea fechas y las formatea a ISO 8601 UTC.
    Compatible con el formato esperado por los ItemLoaders (recibe lista).
    """
    if not date_str_list:
        return None
    
    # Tomar la primera cadena de fecha si es una lista
    date_str = date_str_list[0] if isinstance(date_str_list, list) else date_str_list
    
    if not date_str:
        return None
    
    # Usar normalize_date para el procesamiento
    parsed_date = normalize_date(date_str)
    
    if parsed_date:
        # Convertir a UTC si es necesario
        from datetime import timezone
        if parsed_date.tzinfo is None or parsed_date.tzinfo.utcoffset(parsed_date) is None:
            parsed_date = parsed_date.replace(tzinfo=timezone.utc)
        else:
            parsed_date = parsed_date.astimezone(timezone.utc)
        
        # Formatear a ISO 8601 UTC
        return parsed_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    return None


def normalize_date(date_string: Union[str, datetime]) -> Optional[datetime]:
    """
    Normaliza diferentes formatos de fecha a datetime.
    Soporta múltiples formatos comunes en medios de comunicación.
    """
    if isinstance(date_string, datetime):
        return date_string
    
    if not date_string:
        return None
    
    # Limpiar el string de fecha
    original_date_str_cleaned = date_string.strip() # Keep original for standard parsing
    lower_date_str = original_date_str_cleaned.lower() # Use lowercased for relative matching

    # --- Relative date parsing ---
    now = datetime.now()

    # "ayer"
    if lower_date_str == "ayer":
        return (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

    # "hace N día(s)"
    match = re.fullmatch(r"hace\s+(\d+)\s+d[ií]a(s)?", lower_date_str)
    if match:
        days_ago = int(match.group(1))
        return (now - timedelta(days=days_ago)).replace(hour=0, minute=0, second=0, microsecond=0)

    # "hace N hora(s)"
    match = re.fullmatch(r"hace\s+(\d+)\s+hora(s)?", lower_date_str)
    if match:
        hours_ago = int(match.group(1))
        return now - timedelta(hours=hours_ago)

    # "hace N minuto(s)"
    match = re.fullmatch(r"hace\s+(\d+)\s+minuto(s)?", lower_date_str)
    if match:
        minutes_ago = int(match.group(1))
        return now - timedelta(minutes=minutes_ago)
    
    # --- Standard date format parsing ---
    # Use original_date_str_cleaned for these formats as they might be case-sensitive
    date_formats = [
        # Formatos ISO
        '%Y-%m-%dT%H:%M:%S%z', # Must be before less specific ones
        '%Y-%m-%dT%H:%M:%SZ', # With Z for UTC
        '%Y-%m-%dT%H:%M:%S',  # Without timezone
        '%Y-%m-%d %H:%M:%S',  # Space separator
        '%Y-%m-%d',           # Date only
        
        # Formatos españoles (common variations)
        '%d/%m/%Y %H:%M:%S',
        '%d/%m/%Y %H:%M',
        '%d/%m/%Y',
        '%d-%m-%Y %H:%M:%S', # Added
        '%d-%m-%Y %H:%M',   # Added
        '%d-%m-%Y',
        '%d de %B de %Y %H:%M:%S', # With time
        '%d de %B de %Y %H:%M',   # With time
        '%d de %B de %Y',         # Full month name
        '%d %B %Y',               # Full month name without "de"
        '%d/%m/%y %H:%M:%S',      # Short year with time
        '%d/%m/%y %H:%M',         # Short year with time
        '%d/%m/%y',               # Short year
        
        # Formatos en inglés (common variations)
        '%B %d, %Y %I:%M %p', # With AM/PM
        '%B %d, %Y',
        '%b %d, %Y %I:%M %p', # Short month with AM/PM
        '%b %d, %Y',
        '%m/%d/%Y %I:%M %p', # US format with AM/PM
        '%m/%d/%Y',
        '%m-%d-%Y',
        
        # Formatos con día de la semana (usually at the beginning)
        '%A, %d de %B de %Y %H:%M:%S', # Spanish full
        '%A, %d de %B de %Y',
        '%a, %d %b %Y %H:%M:%S %z', # English short with timezone
        '%a, %d %b %Y %H:%M:%S',
        '%a, %d %b %Y',
    ]
    
    for date_format in date_formats:
        try:
            # Use original_date_str_cleaned here
            return datetime.strptime(original_date_str_cleaned, date_format)
        except ValueError:
            continue
    
    # Try dateparser as a last resort if available and other methods fail
    try:
        import dateparser
        parsed_date = dateparser.parse(original_date_str_cleaned)
        if parsed_date:
            return parsed_date
    except ImportError:
        pass # dateparser not installed
    except Exception as e: # Other dateparser errors
        # Log this error if needed: logger.warning(f"Dateparser failed for '{original_date_str_cleaned}': {e}")
        pass

    # Si no se pudo parsear con formatos estándar, y no era relativo, retornar None
    return None


def normalize_url(url: str) -> str:
    """
    Normaliza URLs eliminando parámetros de tracking y asegurando formato consistente.
    """
    if not url:
        return ''
    
    url = url.strip()
    
    # Eliminar parámetros de tracking comunes
    tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 
                      'utm_term', 'fbclid', 'gclid', 'ref', 'source']
    
    for param in tracking_params:
        url = re.sub(f'[?&]{param}=[^&]*', '', url)
    
    # Limpiar múltiples signos de interrogación o ampersands
    url = re.sub(r'\?&', '?', url)
    url = re.sub(r'&&+', '&', url)
    url = re.sub(r'\?$', '', url)
    
    return url


def extract_author(author_string: str) -> str:
    """
    Extrae y normaliza nombres de autores.
    """
    if not author_string:
        return ''
    
    # Limpiar texto
    author = clean_text(author_string)
    
    # Eliminar prefijos comunes
    prefixes = ['Por', 'By', 'De', 'From', 'Autor:', 'Author:']
    for prefix in prefixes:
        if author.startswith(prefix):
            author = author[len(prefix):].strip()
    
    # Limitar longitud (campo en BD es VARCHAR(200))
    if len(author) > 200:
        author = author[:197] + '...'
    
    return author


def validate_medio_type(tipo: str) -> str:
    """
    Valida que el tipo de medio sea uno de los permitidos.
    """
    valid_types = ['diario', 'agencia', 'televisión', 'radio', 'digital', 
                   'oficial', 'blog', 'otro']
    
    tipo_lower = tipo.lower().strip() if tipo else ''
    
    # Mapear variaciones comunes
    type_mapping = {
        'newspaper': 'diario',
        'periodico': 'diario',
        'periódico': 'diario',
        'tv': 'televisión',
        'television': 'televisión',
        'agency': 'agencia',
        'web': 'digital',
        'website': 'digital',
        'government': 'oficial',
        'gobierno': 'oficial',
    }
    
    if tipo_lower in type_mapping:
        return type_mapping[tipo_lower]
    
    if tipo_lower in valid_types:
        return tipo_lower
    
    return 'otro'


def process_tags(tags: Union[str, List[str]]) -> List[str]:
    """
    Procesa y normaliza etiquetas/tags.
    """
    if isinstance(tags, str):
        # Si es string, separar por comas
        tags = [t.strip() for t in tags.split(',') if t.strip()]
    elif isinstance(tags, list):
        tags = [str(t).strip() for t in tags if t]
    else:
        return []
    
    # Eliminar duplicados manteniendo orden
    seen = set()
    unique_tags = []
    for tag in tags:
        tag_lower = tag.lower()
        if tag_lower not in seen:
            seen.add(tag_lower)
            unique_tags.append(tag)
    
    return unique_tags


def validate_language(lang: str) -> str:
    """
    Valida y normaliza códigos de idioma.
    """
    if not lang:
        return 'es'  # Default español
    
    lang = lang.lower().strip()
    
    # Mapear códigos comunes
    lang_mapping = {
        'español': 'es',
        'spanish': 'es',
        'english': 'en',
        'inglés': 'en',
        'portugués': 'pt',
        'portuguese': 'pt',
        'français': 'fr',
        'french': 'fr',
        'francés': 'fr',
    }
    
    if lang in lang_mapping:
        return lang_mapping[lang]
    
    # Si ya es código ISO de 2 caracteres
    if len(lang) == 2:
        return lang
    
    # Si es código de 3 caracteres o con región (es-ES), tomar los primeros 2
    if len(lang) >= 2:
        return lang[:2]
    
    return 'es'


def generate_storage_path(item_dict: dict) -> str:
    """
    Genera la ruta de almacenamiento en formato:
    {medio}/{año}/{mes}/{día}/{titulo_slug}.html.gz
    """
    medio = item_dict.get('medio', 'unknown')
    fecha = item_dict.get('fecha_publicacion')
    titulo = item_dict.get('titular', 'untitled')
    
    # Limpiar medio para uso en path
    medio_clean = re.sub(r'[^\w\s-]', '', medio.lower())
    medio_clean = re.sub(r'[-\s]+', '-', medio_clean)
    
    # Obtener fecha
    if isinstance(fecha, datetime):
        year = fecha.year
        month = f"{fecha.month:02d}"
        day = f"{fecha.day:02d}"
    else:
        # Si no hay fecha válida, usar fecha actual
        now = datetime.now()
        year = now.year
        month = f"{now.month:02d}"
        day = f"{now.day:02d}"
    
    # Generar slug del título
    titulo_slug = re.sub(r'[^\w\s-]', '', titulo.lower())
    titulo_slug = re.sub(r'[-\s]+', '-', titulo_slug)
    titulo_slug = titulo_slug[:100]  # Limitar longitud
    
    # Si el slug está vacío, usar timestamp
    if not titulo_slug:
        titulo_slug = str(int(datetime.now().timestamp()))
    
    return f"{medio_clean}/{year}/{month}/{day}/{titulo_slug}.html.gz"


class ArticuloInItemLoader(ItemLoader):
    """
    ItemLoader personalizado para ArticuloInItem con procesadores específicos
    para cada campo según los requerimientos del sistema.
    """
    
    # Procesador por defecto: tomar el primer valor no vacío
    default_output_processor = TakeFirst()
    
    # Procesadores de entrada (input processors)
    
    # URL: normalizar y validar
    url_in = MapCompose(normalize_url)
    
    # Titular: limpiar HTML y texto
    titular_in = MapCompose(extract_text_from_html, clean_text)
    
    # Contenido: limpiar HTML pero mantener texto completo
    contenido_texto_in = MapCompose(extract_text_from_html, clean_text)
    
    # HTML: solo limpiar espacios
    contenido_html_in = MapCompose(str.strip)
    
    # Autor: extraer y normalizar
    autor_in = MapCompose(extract_author)
    
    # Fecha: normalizar a datetime y formatear a ISO 8601
    fecha_publicacion_in = MapCompose(parse_and_format_date_processor)
    
    # Medio: limpiar texto
    medio_in = MapCompose(clean_text)
    
    # País: limpiar y capitalizar
    pais_publicacion_in = MapCompose(clean_text, str.title)
    
    # Tipo de medio: validar valores permitidos
    tipo_medio_in = MapCompose(validate_medio_type)
    
    # Idioma: validar código ISO
    idioma_in = MapCompose(validate_language)
    
    # Sección: limpiar texto
    seccion_in = MapCompose(clean_text)
    
    # Etiquetas: procesar como lista
    etiquetas_fuente_in = MapCompose(process_tags)
    etiquetas_fuente_out = Identity()  # Mantener como lista
    
    # Booleanos: asegurar tipo bool
    es_opinion_in = MapCompose(lambda x: bool(x) if x is not None else False)
    es_oficial_in = MapCompose(lambda x: bool(x) if x is not None else False)
    
    # Resumen: limpiar texto
    resumen_in = MapCompose(clean_text)
    
    # Categorías: mantener como lista
    categorias_asignadas_out = Identity()
    
    # Puntuación: asegurar entero entre 0-10
    puntuacion_relevancia_in = MapCompose(
        lambda x: int(x) if x is not None else None,
        lambda x: max(0, min(10, x)) if x is not None else None
    )
    
    # Timestamps: usar datetime actual si no se proporciona
    fecha_recopilacion_in = MapCompose(
        lambda x: x if x else datetime.now()
    )
    
    # Estado: valor por defecto
    estado_procesamiento_in = MapCompose(
        lambda x: x if x else 'pendiente'
    )
    
    # Metadata: mantener como dict/JSON
    metadata_out = Identity()
    
    def add_storage_path(self, value=None):
        """
        Genera automáticamente el storage_path basado en otros campos.
        """
        if not value:
            # Generar path basado en los datos actuales
            item_dict = dict(self.load_item())
            value = generate_storage_path(item_dict)
        
        self.add_value('storage_path', value)
        
    def load_item(self):
        """
        Sobrescribir para añadir validaciones y campos calculados.
        """
        item = super().load_item()
        
        # Generar storage_path si no existe
        if not item.get('storage_path'):
            item['storage_path'] = generate_storage_path(dict(item))
        
        # Asegurar fecha_recopilacion
        if not item.get('fecha_recopilacion'):
            item['fecha_recopilacion'] = datetime.now()
        
        # Valores por defecto
        if not item.get('idioma'):
            item['idioma'] = 'es'
        
        if not item.get('estado_procesamiento'):
            item['estado_procesamiento'] = 'pendiente'
        
        if item.get('es_opinion') is None:
            item['es_opinion'] = False
            
        if item.get('es_oficial') is None:
            item['es_oficial'] = False
        
        return item
