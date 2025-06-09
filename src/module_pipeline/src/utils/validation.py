"""
Módulo Central de Validación para Module Pipeline
=================================================

Este módulo proporciona funciones de sanitización y validadores Pydantic
reutilizables para asegurar la integridad y seguridad de los datos a lo
largo del pipeline de procesamiento.

Principios:
- Simplicidad sobre complejidad
- Validación robusta pero no invasiva
- Reutilización de patrones existentes
"""

import html
import re
import unicodedata
from typing import Any, Optional

from pydantic import AfterValidator, BeforeValidator, field_validator
from pydantic_core import PydanticCustomError
from typing import Annotated

from .error_handling import ValidationError


# ============================================================================
# FUNCIONES DE SANITIZACIÓN BÁSICAS
# ============================================================================

def escape_html(text: str) -> str:
    """
    Escapa caracteres HTML peligrosos para prevenir inyección.
    
    Args:
        text: Texto a sanitizar
        
    Returns:
        Texto con caracteres HTML escapados
    """
    if not isinstance(text, str):
        return str(text)
    
    # Usar html.escape que escapa: < > & " '
    return html.escape(text, quote=True)


def clean_text(text: str, preserve_newlines: bool = False) -> str:
    """
    Limpia texto de caracteres no deseados.
    
    Args:
        text: Texto a limpiar
        preserve_newlines: Si preservar saltos de línea
        
    Returns:
        Texto limpio
    """
    if not isinstance(text, str):
        return str(text)
    
    # Reemplazar caracteres de control con espacios (excepto los permitidos)
    allowed_chars = ['\t', '\n', '\r'] if preserve_newlines else ['\t']
    cleaned = ''
    for char in text:
        if char in allowed_chars:
            # Mantener caracteres permitidos
            cleaned += char
        elif unicodedata.category(char).startswith('C'):
            # Reemplazar caracteres de control con espacio
            cleaned += ' '
        else:
            # Mantener caracteres normales
            cleaned += char
    
    # Remover espacios múltiples (pero preservar newlines si se indica)
    if preserve_newlines:
        # Limpiar espacios múltiples en cada línea
        lines = cleaned.split('\n')
        cleaned_lines = [' '.join(line.split()) for line in lines]
        cleaned = '\n'.join(cleaned_lines)
    else:
        cleaned = ' '.join(cleaned.split())
    
    return cleaned.strip()


def normalize_whitespace(text: str) -> str:
    """
    Normaliza espacios en blanco en el texto.
    
    Convierte todos los tipos de espacios en blanco (tabs, newlines, etc.)
    a espacios simples y elimina espacios múltiples.
    
    Args:
        text: Texto a normalizar
        
    Returns:
        Texto con espacios normalizados
    """
    if not isinstance(text, str):
        return str(text)
    
    # Reemplazar todos los tipos de whitespace con espacio simple
    normalized = re.sub(r'\s+', ' ', text)
    
    # Eliminar espacios al inicio y final
    return normalized.strip()


# ============================================================================
# VALIDADORES PYDANTIC REUTILIZABLES
# ============================================================================

def _validate_non_empty_string(value: Any) -> str:
    """
    Validador interno para strings no vacíos.
    
    Args:
        value: Valor a validar
        
    Returns:
        String validado
        
    Raises:
        PydanticCustomError: Si el string está vacío después de strip
    """
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            raise PydanticCustomError(
                'empty_string',
                'String no puede estar vacío',
                {}
            )
        return stripped
    
    # Si no es string, dejar que Pydantic maneje el error de tipo
    return value


def _validate_safe_html_string(value: Any) -> str:
    """
    Validador interno para strings seguros contra HTML injection.
    
    Escapa automáticamente caracteres HTML peligrosos.
    
    Args:
        value: Valor a validar
        
    Returns:
        String escapado y seguro
    """
    if isinstance(value, str):
        # Primero validar que no esté vacío
        value = _validate_non_empty_string(value)
        # Luego escapar HTML
        return escape_html(value)
    
    return value


# Tipos reutilizables con validadores
NonEmptyString = Annotated[str, AfterValidator(_validate_non_empty_string)]
SafeHtmlString = Annotated[str, AfterValidator(_validate_safe_html_string)]


# ============================================================================
# FUNCIÓN DE VALIDACIÓN INICIAL
# ============================================================================

def validate_input_data(
    data: dict[str, Any],
    required_fields: Optional[list[str]] = None
) -> dict[str, Any]:
    """
    Realiza validación inicial básica de datos de entrada.
    
    Esta función proporciona una capa de validación preliminar antes
    de que los datos sean procesados por modelos Pydantic específicos.
    
    Args:
        data: Diccionario con datos a validar
        required_fields: Lista opcional de campos requeridos
        
    Returns:
        Diccionario con datos validados
        
    Raises:
        ValidationError: Si la validación falla
    """
    validation_errors = []
    
    # Verificar que data sea un diccionario
    if not isinstance(data, dict):
        raise ValidationError(
            message="Los datos de entrada deben ser un diccionario",
            validation_errors=[{
                "field": "data",
                "message": f"Se esperaba dict, se recibió {type(data).__name__}"
            }]
        )
    
    # Verificar campos requeridos si se especifican
    if required_fields:
        missing_fields = []
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
            elif data[field] is None:
                validation_errors.append({
                    "field": field,
                    "message": f"El campo '{field}' no puede ser None"
                })
            elif isinstance(data[field], str) and not data[field].strip():
                validation_errors.append({
                    "field": field,
                    "message": f"El campo '{field}' no puede estar vacío"
                })
        
        if missing_fields:
            validation_errors.append({
                "field": "required_fields",
                "message": f"Campos requeridos faltantes: {', '.join(missing_fields)}"
            })
    
    # Sanitización básica de strings en el primer nivel
    sanitized_data = {}
    for key, value in data.items():
        if isinstance(value, str):
            # Aplicar limpieza básica pero no escapar HTML aquí
            # El escape se hace en los validadores específicos
            sanitized_data[key] = clean_text(value, preserve_newlines=True)
        else:
            sanitized_data[key] = value
    
    # Si hay errores, lanzar excepción
    if validation_errors:
        raise ValidationError(
            message="Error en la validación de datos de entrada",
            validation_errors=validation_errors
        )
    
    return sanitized_data


# ============================================================================
# VALIDADORES PARA MODELOS ESPECÍFICOS
# ============================================================================

def create_field_validator_non_empty(field_names: list[str]):
    """
    Factory para crear validadores de campos no vacíos.
    
    Args:
        field_names: Lista de nombres de campos a validar
        
    Returns:
        Decorador field_validator configurado
    """
    @field_validator(*field_names, mode='after')
    @classmethod
    def validate_non_empty(cls, value: Any) -> Any:
        if isinstance(value, str):
            return _validate_non_empty_string(value)
        return value
    
    return validate_non_empty


def create_field_validator_safe_html(field_names: list[str]):
    """
    Factory para crear validadores de campos seguros contra HTML.
    
    Args:
        field_names: Lista de nombres de campos a validar
        
    Returns:
        Decorador field_validator configurado
    """
    @field_validator(*field_names, mode='after')
    @classmethod
    def validate_safe_html(cls, value: Any) -> Any:
        if isinstance(value, str):
            return _validate_safe_html_string(value)
        return value
    
    return validate_safe_html


# ============================================================================
# UTILIDADES DE VALIDACIÓN ESPECÍFICAS DEL DOMINIO
# ============================================================================

def validate_confidence_score(value: float) -> float:
    """
    Valida que un score de confianza esté en el rango [0, 1].
    
    Args:
        value: Valor a validar
        
    Returns:
        Valor validado
        
    Raises:
        ValueError: Si el valor está fuera del rango
    """
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"Score de confianza debe estar entre 0 y 1, recibido: {value}")
    return value


def validate_offset_range(start: Optional[int], end: Optional[int]) -> tuple[Optional[int], Optional[int]]:
    """
    Valida que un rango de offsets sea coherente.
    
    Args:
        start: Offset inicial
        end: Offset final
        
    Returns:
        Tupla con offsets validados
        
    Raises:
        ValueError: Si el rango es inválido
    """
    if start is not None and end is not None:
        if start < 0:
            raise ValueError(f"Offset inicial no puede ser negativo: {start}")
        if end < 0:
            raise ValueError(f"Offset final no puede ser negativo: {end}")
        if end < start:
            raise ValueError(f"Offset final ({end}) no puede ser menor que el inicial ({start})")
    
    return start, end


def validate_url(url: str) -> str:
    """
    Valida que una string sea una URL válida.
    
    Args:
        url: URL a validar
        
    Returns:
        URL validada
        
    Raises:
        ValueError: Si la URL es inválida
    """
    # Patrón básico para URLs
    url_pattern = re.compile(
        r'^https?://'  # http:// o https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # dominio
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # puerto opcional
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not url_pattern.match(url):
        raise ValueError(f"URL inválida: {url}")
    
    return url


def validate_date_format(date_str: str, format: str = "%Y-%m-%d") -> str:
    """
    Valida que una string tenga un formato de fecha válido.
    
    Args:
        date_str: String de fecha a validar
        format: Formato esperado (default: YYYY-MM-DD)
        
    Returns:
        String de fecha validada
        
    Raises:
        ValueError: Si el formato es inválido
    """
    from datetime import datetime
    
    try:
        datetime.strptime(date_str, format)
        return date_str
    except ValueError as e:
        raise ValueError(f"Formato de fecha inválido: {date_str}. Esperado: {format}") from e


def validate_wikidata_uri(uri: str) -> str:
    """
    Valida que una URI de Wikidata sea válida.
    
    Args:
        uri: URI de Wikidata a validar
        
    Returns:
        URI validada
        
    Raises:
        ValueError: Si la URI es inválida
    """
    # Patrón para URIs de Wikidata
    wikidata_pattern = re.compile(
        r'^https?://(?:www\.)?wikidata\.org/(?:wiki|entity)/Q\d+$',
        re.IGNORECASE
    )
    
    if not wikidata_pattern.match(uri):
        raise ValueError(f"URI de Wikidata inválida: {uri}. Debe seguir el formato https://www.wikidata.org/wiki/Qxxxxx")
    
    return uri


def sanitize_entity_name(name: str) -> str:
    """
    Sanitiza nombres de entidades normalizadas.
    
    Normaliza caracteres Unicode y elimina caracteres especiales
    manteniendo la legibilidad del nombre.
    
    Args:
        name: Nombre de entidad a sanitizar
        
    Returns:
        Nombre sanitizado
    """
    if not isinstance(name, str):
        return str(name)
    
    # Normalizar Unicode a forma NFKD (compatibilidad decomposed)
    normalized = unicodedata.normalize('NFKD', name)
    
    # Filtrar solo caracteres ASCII y algunos símbolos permitidos
    # Mantener letras, números, espacios, guiones y algunos símbolos comunes
    allowed_chars = [
        'á', 'é', 'í', 'ó', 'ú', 'ñ', 'ü',  # Español con tildes
        'Á', 'É', 'Í', 'Ó', 'Ú', 'Ñ', 'Ü',
        'à', 'è', 'ì', 'ò', 'ù',  # Otros idiomas
        'ç', 'Ç'
    ]
    
    sanitized = ''.join(
        char for char in normalized
        if char.isalnum() or char.isspace() or char in ['-', '_', '.', ',', "'", '"'] or char in allowed_chars
    )
    
    # Normalizar espacios múltiples
    sanitized = ' '.join(sanitized.split())
    
    # Escape HTML para prevenir inyección
    return escape_html(sanitized.strip())


def validate_numeric_value(value: Any, min_value: Optional[float] = None, max_value: Optional[float] = None) -> float:
    """
    Valida que un valor sea numérico y opcionalmente esté en un rango.
    
    Args:
        value: Valor a validar
        min_value: Valor mínimo permitido (opcional)
        max_value: Valor máximo permitido (opcional)
        
    Returns:
        Valor numérico validado
        
    Raises:
        ValueError: Si el valor no es numérico o está fuera del rango
    """
    try:
        numeric_value = float(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Valor no numérico: {value}") from e
    
    if min_value is not None and numeric_value < min_value:
        raise ValueError(f"Valor {numeric_value} es menor que el mínimo permitido {min_value}")
    
    if max_value is not None and numeric_value > max_value:
        raise ValueError(f"Valor {numeric_value} es mayor que el máximo permitido {max_value}")
    
    return numeric_value


def validate_date_optional(date_str: Optional[str], format: str = "%Y-%m-%d") -> Optional[str]:
    """
    Valida una fecha opcional (puede ser None o string vacío).
    
    Args:
        date_str: String de fecha a validar (puede ser None)
        format: Formato esperado (default: YYYY-MM-DD)
        
    Returns:
        String de fecha validada o None
        
    Raises:
        ValueError: Si el formato es inválido cuando hay fecha
    """
    if not date_str or date_str.strip() == "":
        return None
    
    return validate_date_format(date_str.strip(), format)
