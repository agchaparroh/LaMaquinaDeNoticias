# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from datetime import datetime  # noqa: F401
from typing import Optional  # noqa: F401

import scrapy


class ArticuloInItem(scrapy.Item):
    """
    Item para almacenar artículos periodísticos extraídos.
    Mapea directamente a la tabla 'articulos' en la base de datos.
    """

    # ID del artículo en la base de datos (propagado después del upsert)
    articulo_id = scrapy.Field()  # ID del artículo en la BD

    # Campos principales
    url = scrapy.Field()  # URL original del artículo
    storage_path = scrapy.Field()  # Ruta en Supabase Storage
    fuente = scrapy.Field()  # Nombre/identificador del spider que lo extrajo
    medio = scrapy.Field()  # Nombre del medio (ej: "El País")
    medio_url_principal = (
        scrapy.Field()
    )  # URL principal del medio (ej: https://elpais.com)
    area_geografica = (
        scrapy.Field()
    )  # Área geográfica (ej: "España", "Internacional", "América")
    tipo_medio = scrapy.Field()  # Tipo: diario, agencia, televisión, etc.
    titular = scrapy.Field()  # Título del artículo
    fecha_publicacion = scrapy.Field()  # Fecha de publicación
    autor = scrapy.Field()  # Autor(es) del artículo
    idioma = scrapy.Field()  # Idioma del artículo
    seccion = scrapy.Field()  # Sección del medio
    etiquetas_fuente = scrapy.Field()  # Etiquetas del medio original
    es_opinion = scrapy.Field()  # Boolean: ¿Es artículo de opinión?
    es_oficial = scrapy.Field()  # Boolean: ¿Es fuente oficial?

    # Campos generados por el pipeline
    resumen = scrapy.Field()  # Resumen generado en Fase 2
    categorias_asignadas = scrapy.Field()  # Categorías asignadas en Fase 2
    puntuacion_relevancia = scrapy.Field()  # Puntuación 0-10 asignada en Fase 2

    # Campos de control
    fecha_recopilacion = scrapy.Field()  # Timestamp de scraping
    fecha_procesamiento = scrapy.Field()  # Timestamp de fin de Fase 5
    estado_procesamiento = scrapy.Field()  # Estado: pendiente, procesando, etc.
    error_detalle = scrapy.Field()  # Detalle del error si lo hay

    # Contenido extraído
    contenido_texto = scrapy.Field()  # Texto completo del artículo
    contenido_html = scrapy.Field()  # HTML original del artículo

    # Metadatos adicionales
    metadata = scrapy.Field()  # JSONB para datos adicionales

    # Validación de campos requeridos
    def validate(self) -> bool:
        """Valida que los campos requeridos estén presentes"""
        required_fields = [
            "titular",
            "medio",
            "area_geografica",
            "tipo_medio",
            "fecha_publicacion",
            "contenido_texto",
        ]
        for field in required_fields:
            if not self.get(field):
                return False
        return True
