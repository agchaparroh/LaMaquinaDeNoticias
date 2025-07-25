"""
Pipeline de conversión de tipos para La Máquina de Noticias.

Este pipeline convierte diccionarios a objetos ArticuloInItem,
permitiendo compatibilidad entre spiders que generan dict y
pipelines que esperan ArticuloInItem.
"""

import logging
from typing import Any, Dict

from itemadapter import ItemAdapter

from scraper_core.items import ArticuloInItem

logger = logging.getLogger(__name__)


class ItemConverterPipeline:
    """
    Convierte items de tipo dict a ArticuloInItem.

    Este pipeline debe ejecutarse PRIMERO (prioridad más baja)
    para asegurar que todos los pipelines subsiguientes reciban
    objetos ArticuloInItem correctamente tipados.
    """

    def __init__(self):
        self.converted_count = 0
        self.passed_count = 0
        self.error_count = 0
        logger.info("ItemConverterPipeline initialized")

    def open_spider(self, spider):
        """Inicializa el pipeline cuando se abre el spider."""
        logger.info(f"ItemConverterPipeline opened for spider: {spider.name}")
        self.spider_name = spider.name

    def close_spider(self, spider):
        """Cierra el pipeline y reporta estadísticas."""
        logger.info(
            f"ItemConverterPipeline closed for spider {spider.name}. "
            f"Stats: converted={self.converted_count}, "
            f"passed={self.passed_count}, errors={self.error_count}"
        )

    def process_item(self, item, spider):
        """
        Procesa cada item, convirtiéndolo a ArticuloInItem si es necesario.

        Args:
            item: El item a procesar (dict o ArticuloInItem)
            spider: El spider que generó el item

        Returns:
            ArticuloInItem: El item convertido o el original si ya era ArticuloInItem
        """
        # Si ya es ArticuloInItem, pasarlo sin cambios
        if isinstance(item, ArticuloInItem):
            self.passed_count += 1
            logger.debug(f"Item already ArticuloInItem, passing through")  # noqa: F541
            return item

        # Si es un dict, intentar convertirlo
        if isinstance(item, dict):
            try:
                # Log del item antes de conversión (sin contenido completo)
                item_preview = {
                    "url": item.get("url", "N/A"),
                    "titular": item.get("titular", "N/A")[:100],
                    "medio": item.get("medio", "N/A"),
                }
                logger.debug(f"Converting dict to ArticuloInItem: {item_preview}")

                # Mapear campos que tienen nombres diferentes
                # fecha_extraccion -> fecha_recopilacion
                if "fecha_extraccion" in item and "fecha_recopilacion" not in item:
                    item["fecha_recopilacion"] = item.pop("fecha_extraccion")

                # Remover campos que no existen en ArticuloInItem
                valid_fields = set(ArticuloInItem.fields.keys())
                item_fields = set(item.keys())
                invalid_fields = item_fields - valid_fields

                if invalid_fields:
                    logger.debug(f"Removing invalid fields: {invalid_fields}")
                    for field in invalid_fields:
                        item.pop(field, None)

                # Realizar la conversión
                articulo_item = ArticuloInItem(**item)

                self.converted_count += 1
                logger.info(
                    f"Successfully converted dict to ArticuloInItem for URL: {item.get('url', 'Unknown')}"
                )

                return articulo_item

            except Exception as e:
                self.error_count += 1
                logger.error(
                    f"Error converting dict to ArticuloInItem: {e}. "
                    f"Item URL: {item.get('url', 'Unknown')}"
                )
                # En caso de error, devolver el item original
                # para que otros pipelines puedan manejarlo o rechazarlo
                return item

        # Si no es ni dict ni ArticuloInItem, registrar y pasar
        logger.warning(
            f"Item is neither dict nor ArticuloInItem, type: {type(item)}. "
            f"Passing through unchanged."
        )
        self.passed_count += 1
        return item

    def _get_item_summary(self, item: Any) -> Dict[str, Any]:
        """
        Obtiene un resumen del item para logging.

        Args:
            item: El item a resumir

        Returns:
            Dict con información resumida del item
        """
        adapter = ItemAdapter(item)
        return {
            "type": type(item).__name__,
            "url": adapter.get("url", "N/A"),
            "titular": str(adapter.get("titular", "N/A"))[:100],
            "medio": adapter.get("medio", "N/A"),
            "has_content": bool(adapter.get("contenido_texto")),
        }
