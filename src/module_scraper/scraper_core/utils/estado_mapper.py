"""
Mapeo de estados de procesamiento para compatibilidad con el DOMAIN de la base de datos.

Este módulo resuelve la incompatibilidad entre los estados usados por diferentes
módulos del sistema y el DOMAIN estado_procesamiento_enum en la base de datos.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def map_estado_to_domain(estado: str, context: str = "scraper") -> str:
    """
    Mapea estados del módulo al DOMAIN de la base de datos.

    El DOMAIN estado_procesamiento_enum acepta:
    - 'pendiente', 'procesando', 'completado'
    - 'error_prefiltrado', 'error_relevancia', 'error_extraccion',
    - 'error_normalizacion', 'error_bd'

    Args:
        estado: Estado original del módulo
        context: Contexto del módulo ('scraper' o 'pipeline')

    Returns:
        Estado compatible con el DOMAIN de la base de datos
    """
    # Estados válidos del DOMAIN
    DOMAIN_STATES = {
        "pendiente",
        "procesando",
        "completado",
        "error_prefiltrado",
        "error_relevancia",
        "error_extraccion",
        "error_normalizacion",
        "error_bd",
    }

    # Si ya es un estado válido del DOMAIN, retornarlo sin cambios
    if estado in DOMAIN_STATES:
        return estado

    # Mapeo específico para el contexto del scraper
    if context == "scraper":
        SCRAPER_MAPPING = {
            # Estados normales pasan sin cambios
            "pendiente": "pendiente",
            "procesando": "procesando",
            "completado": "completado",
            # Errores genéricos se mapean a error_prefiltrado
            # ya que el scraper es la primera etapa del proceso
            "error": "error_prefiltrado",
            "descartado": "error_prefiltrado",
            # Otros posibles estados
            "failed": "error_prefiltrado",
            "skipped": "error_prefiltrado",
        }

        mapped_estado = SCRAPER_MAPPING.get(estado, "pendiente")

        if estado not in SCRAPER_MAPPING:
            logger.warning(
                f"Estado desconocido '{estado}' en contexto '{context}'. "
                f"Mapeando a 'pendiente' por defecto."
            )

        return mapped_estado

    # Mapeo para el contexto del pipeline (futuro)
    elif context == "pipeline":
        PIPELINE_MAPPING = {
            "pendiente_connector": "pendiente",
            "procesando_fase1": "procesando",
            "procesando_fase2": "procesando",
            "procesando_fase3": "procesando",
            "procesando_fase4": "procesando",
            "procesando_fase5": "procesando",
            "error_fase1": "error_prefiltrado",
            "error_fase2": "error_extraccion",
            "error_fase3": "error_extraccion",
            "error_fase4": "error_normalizacion",
            "error_fase5": "error_bd",
            "completado": "completado",
        }

        mapped_estado = PIPELINE_MAPPING.get(estado, "pendiente")

        if estado not in PIPELINE_MAPPING:
            logger.warning(
                f"Estado desconocido '{estado}' en contexto '{context}'. "
                f"Mapeando a 'pendiente' por defecto."
            )

        return mapped_estado

    # Contexto desconocido - usar default seguro
    logger.warning(
        f"Contexto desconocido '{context}' para estado '{estado}'. "
        f"Usando 'pendiente' por defecto."
    )
    return "pendiente"


def get_error_detail_for_estado(
    estado_original: str, error_message: Optional[str] = None
) -> str:
    """
    Genera un mensaje de error detallado basado en el estado original.

    Args:
        estado_original: El estado original antes del mapeo
        error_message: Mensaje de error adicional opcional

    Returns:
        Mensaje de error formateado para guardar en error_detalle
    """
    base_message = f"Estado original: {estado_original}"

    if error_message:
        return f"{base_message}. Detalle: {error_message}"

    return base_message


def map_tipo_medio_to_domain(tipo_medio: str) -> str:
    """
    Mapea tipos de medio al DOMAIN tipo_medio_enum de la base de datos.

    El DOMAIN tipo_medio_enum acepta:
    - 'diario', 'agencia', 'televisión', 'radio', 'digital', 'oficial', 'blog', 'otro'

    Args:
        tipo_medio: Tipo de medio original

    Returns:
        Tipo de medio compatible con el DOMAIN de la base de datos
    """
    # Tipos válidos del DOMAIN (nota: 'televisión' con tilde)
    DOMAIN_TIPOS = {
        "diario",
        "agencia",
        "televisión",
        "radio",
        "digital",
        "oficial",
        "blog",
        "otro",
    }

    # Si ya es un tipo válido del DOMAIN, retornarlo sin cambios
    if tipo_medio in DOMAIN_TIPOS:
        return tipo_medio

    # Mapeo de tipos comunes a valores del DOMAIN
    TIPO_MEDIO_MAPPING = {
        # Variaciones de agencia
        "agencia_de_noticias": "agencia",
        "agencia de noticias": "agencia",
        "news_agency": "agencia",
        # Variaciones de televisión (sin tilde)
        "television": "televisión",
        "tv": "televisión",
        # Variaciones de digital
        "online": "digital",
        "web": "digital",
        "internet": "digital",
        "portal": "digital",
        # Variaciones de periódico
        "periodico": "diario",
        "periódico": "diario",
        "newspaper": "diario",
        # Variaciones de oficial
        "gobierno": "oficial",
        "gubernamental": "oficial",
        "estatal": "oficial",
        # Otros tipos
        "revista": "otro",
        "magazine": "otro",
        "podcast": "otro",
        "institucional": "otro",
    }

    # Normalizar a minúsculas para el mapeo
    tipo_medio_lower = tipo_medio.lower().strip()

    mapped_tipo = TIPO_MEDIO_MAPPING.get(tipo_medio_lower, "otro")

    if tipo_medio_lower not in TIPO_MEDIO_MAPPING and tipo_medio not in DOMAIN_TIPOS:
        logger.warning(
            f"Tipo de medio desconocido '{tipo_medio}'. Mapeando a 'otro' por defecto."
        )

    return mapped_tipo
