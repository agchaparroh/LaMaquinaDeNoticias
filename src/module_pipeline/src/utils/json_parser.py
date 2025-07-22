"""
Módulo de Parseo JSON Robusto para Respuestas LLM
==================================================

Este módulo proporciona funciones para parsear respuestas JSON de modelos LLM
con manejo robusto de diferentes formatos y casos de error.

Maneja:
- JSON puro
- JSON envuelto en markdown code blocks (```json...```)
- JSON truncado por límite de tokens
- Respuestas con múltiples bloques de código
- Detección automática de problemas comunes
"""

import json
import re
from typing import Dict, Any, Optional, Tuple
from .logging_config import get_logger

# Configurar logger para este módulo
logger = get_logger("JSONParser")


class LLMJSONParseError(Exception):
    """Excepción específica para errores de parseo de JSON de LLM."""
    def __init__(self, message: str, original_response: str = "", cleaned_response: str = ""):
        super().__init__(message)
        self.original_response = original_response
        self.cleaned_response = cleaned_response


def detect_markdown_blocks(text: str) -> list[tuple[int, int, str]]:
    """
    Detecta bloques de código markdown en el texto.
    
    Args:
        text: Texto a analizar
        
    Returns:
        Lista de tuplas (inicio, fin, lenguaje) para cada bloque encontrado
    """
    blocks = []
    
    # Patrón para detectar bloques de código con o sin especificador de lenguaje
    # Maneja: ```json, ```JSON, ```, etc.
    pattern = r'```(\w*)\n(.*?)\n```'
    
    for match in re.finditer(pattern, text, re.DOTALL):
        language = match.group(1).lower() if match.group(1) else ""
        start = match.start()
        end = match.end()
        blocks.append((start, end, language))
        
    return blocks


def clean_markdown_wrapper(text: str) -> str:
    """
    Limpia el texto removiendo wrappers de markdown code blocks.
    
    Args:
        text: Texto posiblemente envuelto en markdown
        
    Returns:
        Texto limpio sin markdown
    """
    if not text:
        return text
        
    # Eliminar espacios en blanco al inicio y final
    text = text.strip()
    
    # Detectar y remover markdown code blocks
    blocks = detect_markdown_blocks(text)
    
    if blocks:
        # Si hay bloques, extraer el contenido del primero
        # Preferir bloques marcados como 'json'
        json_blocks = [b for b in blocks if b[2] == 'json']
        if json_blocks:
            start, end, _ = json_blocks[0]
            # Extraer solo el contenido del bloque
            block_match = re.search(r'```(?:json|JSON)?\n(.*?)\n```', text[start:end], re.DOTALL)
            if block_match:
                return block_match.group(1).strip()
        elif blocks:
            # Si no hay bloques json específicos, usar el primero
            start, end, _ = blocks[0]
            block_match = re.search(r'```\w*\n(.*?)\n```', text[start:end], re.DOTALL)
            if block_match:
                return block_match.group(1).strip()
    
    # Caso alternativo: detectar patrones simples de markdown
    # Por si el regex principal falla
    if text.startswith('```') and '```' in text[3:]:
        # Encontrar el primer cierre
        first_newline = text.find('\n')
        last_backticks = text.rfind('```')
        
        if first_newline > 0 and last_backticks > first_newline:
            # Extraer contenido entre los backticks
            content = text[first_newline + 1:last_backticks].strip()
            return content
    
    # Si no se detectó markdown, devolver el texto original
    return text


def detect_truncation(text: str) -> Tuple[bool, str]:
    """
    Detecta si el JSON parece estar truncado.
    
    Args:
        text: Texto JSON a analizar
        
    Returns:
        Tupla (está_truncado, razón)
    """
    if not text:
        return False, ""
    
    text = text.strip()
    
    # Contar llaves y corchetes
    open_braces = text.count('{')
    close_braces = text.count('}')
    open_brackets = text.count('[')
    close_brackets = text.count(']')
    
    # Verificar balance
    if open_braces > close_braces:
        return True, f"Llaves desbalanceadas: {open_braces} abiertas vs {close_braces} cerradas"
    
    if open_brackets > close_brackets:
        return True, f"Corchetes desbalanceados: {open_brackets} abiertos vs {close_brackets} cerrados"
    
    # Verificar si termina abruptamente
    # JSON válido debe terminar con }, ], o " (para strings)
    if text and not text.rstrip().endswith(('}', ']', '"')):
        # Verificar si termina en medio de un string o valor
        last_chars = text[-20:] if len(text) > 20 else text
        if any(char in last_chars for char in [',', ':', '[']):
            return True, "JSON termina abruptamente en medio de una estructura"
    
    # Buscar patrones comunes de truncamiento
    if text.endswith(('...', '…')):
        return True, "JSON termina con elipsis indicando truncamiento"
    
    # Verificar strings sin cerrar
    # Contar comillas que no estén escapadas
    quote_count = 0
    i = 0
    while i < len(text):
        if text[i] == '"' and (i == 0 or text[i-1] != '\\'):
            quote_count += 1
        i += 1
    
    if quote_count % 2 != 0:
        return True, "Número impar de comillas, posible string sin cerrar"
    
    return False, ""


def attempt_json_repair(text: str) -> Optional[str]:
    """
    Intenta reparar JSON truncado o con errores menores.
    
    Args:
        text: JSON posiblemente dañado
        
    Returns:
        JSON reparado o None si no se puede reparar
    """
    if not text:
        return None
        
    text = text.strip()
    
    # Si está vacío después de limpiar, no hay nada que reparar
    if not text:
        return None
    
    # Intentar cerrar estructuras abiertas
    repaired = text
    
    # Contar estructuras abiertas
    open_braces = repaired.count('{')
    close_braces = repaired.count('}')
    open_brackets = repaired.count('[')
    close_brackets = repaired.count(']')
    
    # Cerrar strings abiertos primero
    quote_count = 0
    i = 0
    while i < len(repaired):
        if repaired[i] == '"' and (i == 0 or repaired[i-1] != '\\'):
            quote_count += 1
        i += 1
    
    if quote_count % 2 != 0:
        # Hay un string sin cerrar, cerrarlo
        repaired += '"'
    
    # Verificar si necesitamos cerrar arrays u objetos
    # Buscar la última coma para ver si estamos en medio de una lista
    if repaired.rstrip().endswith(','):
        # Remover la coma final
        repaired = repaired.rstrip()[:-1]
    
    # Cerrar corchetes faltantes
    while open_brackets > close_brackets:
        repaired += ']'
        close_brackets += 1
    
    # Cerrar llaves faltantes
    while open_braces > close_braces:
        repaired += '}'
        close_braces += 1
    
    # Verificar que el JSON reparado sea válido
    try:
        json.loads(repaired)
        return repaired
    except json.JSONDecodeError:
        # Si aún no es válido, no podemos repararlo
        return None


def parse_llm_json_response(
    raw_response: str,
    attempt_repair: bool = True,
    strict: bool = False
) -> Dict[str, Any]:
    """
    Parsea una respuesta JSON de un LLM con manejo robusto de formatos.
    
    Args:
        raw_response: Respuesta cruda del LLM
        attempt_repair: Si intentar reparar JSON truncado
        strict: Si lanzar excepción en caso de fallo (False = devuelve dict vacío)
        
    Returns:
        Diccionario con el JSON parseado
        
    Raises:
        LLMJSONParseError: Si strict=True y no se puede parsear
    """
    if not raw_response:
        if strict:
            raise LLMJSONParseError("Respuesta vacía del LLM", raw_response)
        logger.warning("Respuesta vacía del LLM, devolviendo diccionario vacío")
        return {}
    
    # Registrar información sobre la respuesta original
    original_length = len(raw_response)
    logger.debug(f"Parseando respuesta LLM de {original_length} caracteres")
    
    # Paso 1: Limpiar markdown si existe
    cleaned_response = clean_markdown_wrapper(raw_response)
    
    if cleaned_response != raw_response:
        logger.info(f"Markdown detectado y limpiado. Longitud: {len(raw_response)} -> {len(cleaned_response)}")
    
    # Paso 2: Intentar parsear el JSON limpio
    try:
        result = json.loads(cleaned_response)
        logger.debug("JSON parseado exitosamente sin necesidad de reparación")
        return result
    except json.JSONDecodeError as e:
        logger.debug(f"Primer intento de parseo falló: {e}")
    
    # Paso 3: Detectar si está truncado
    is_truncated, truncation_reason = detect_truncation(cleaned_response)
    if is_truncated:
        logger.warning(f"JSON parece estar truncado: {truncation_reason}")
    
    # Paso 4: Intentar reparación si está habilitada
    if attempt_repair and is_truncated:
        logger.info("Intentando reparar JSON truncado...")
        repaired = attempt_json_repair(cleaned_response)
        
        if repaired:
            try:
                result = json.loads(repaired)
                logger.warning(
                    f"JSON reparado exitosamente. Advertencia: datos pueden estar incompletos. "
                    f"Longitud original: {len(cleaned_response)}, reparado: {len(repaired)}"
                )
                return result
            except json.JSONDecodeError as e:
                logger.debug(f"Reparación falló: {e}")
    
    # Paso 5: Si llegamos aquí, no pudimos parsear
    error_msg = f"No se pudo parsear la respuesta JSON del LLM"
    if is_truncated:
        error_msg += f" (truncado: {truncation_reason})"
    
    # Logging detallado para debugging
    logger.error(error_msg)
    logger.debug(f"Primeros 200 chars de respuesta original: {raw_response[:200]}")
    logger.debug(f"Últimos 200 chars de respuesta original: {raw_response[-200:]}")
    logger.debug(f"Primeros 200 chars después de limpieza: {cleaned_response[:200]}")
    
    if strict:
        raise LLMJSONParseError(error_msg, raw_response, cleaned_response)
    
    # En modo no estricto, devolver diccionario vacío
    logger.warning("Devolviendo diccionario vacío como fallback")
    return {}


# Funciones de utilidad adicionales para análisis

def analyze_llm_response_format(raw_response: str) -> Dict[str, Any]:
    """
    Analiza el formato de una respuesta LLM para métricas y debugging.
    
    Args:
        raw_response: Respuesta cruda del LLM
        
    Returns:
        Diccionario con métricas sobre el formato
    """
    metrics = {
        "length": len(raw_response),
        "has_markdown": False,
        "markdown_blocks": 0,
        "is_truncated": False,
        "truncation_reason": "",
        "starts_with_json": False,
        "ends_properly": False,
        "estimated_tokens": len(raw_response) // 4  # Aproximación burda
    }
    
    if not raw_response:
        return metrics
    
    # Detectar markdown
    blocks = detect_markdown_blocks(raw_response)
    metrics["has_markdown"] = len(blocks) > 0
    metrics["markdown_blocks"] = len(blocks)
    
    # Detectar truncamiento
    cleaned = clean_markdown_wrapper(raw_response)
    is_truncated, reason = detect_truncation(cleaned)
    metrics["is_truncated"] = is_truncated
    metrics["truncation_reason"] = reason
    
    # Verificar formato
    stripped = raw_response.strip()
    metrics["starts_with_json"] = stripped.startswith('{') or stripped.startswith('[')
    metrics["ends_properly"] = stripped.endswith('}') or stripped.endswith(']')
    
    return metrics