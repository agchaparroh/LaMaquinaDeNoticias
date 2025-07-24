"""
Pipeline de exportación JSON simplificado para textos brutos.
Guarda los artículos como JSON sin comprimir.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from itemadapter import ItemAdapter
from scrapy import signals
from scrapy.exceptions import DropItem

from scraper_core.items import ArticuloInItem

logger = logging.getLogger(__name__)


class JsonWriterTextoBrutoPipeline:
    """
    Exporta ArticuloInItem a archivos JSON sin comprimir.
    Versión simplificada para extracción de textos brutos.
    """
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.exported_count = 0
        self.error_count = 0
        self.skipped_count = 0
        
        logger.info(f"JsonWriterTextoBrutoPipeline initialized. Output directory: {self.output_dir}")
    
    @classmethod
    def from_crawler(cls, crawler):
        # Obtener directorio de salida
        output_dir = crawler.settings.get('SCRAPY_OUTPUT_DIR', '/output')
        
        # Crear instancia
        instance = cls(output_dir)
        
        # Conectar señales
        crawler.signals.connect(instance.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(instance.spider_closed, signal=signals.spider_closed)
        
        return instance
    
    def spider_opened(self, spider):
        """Se ejecuta cuando el spider se abre."""
        # Crear directorio si no existe
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"JsonWriterTextoBrutoPipeline ready for spider {spider.name}")
    
    def spider_closed(self, spider):
        """Se ejecuta cuando el spider se cierra."""
        logger.info(
            f"JsonWriterTextoBrutoPipeline closed for spider {spider.name}. "
            f"Stats: exported={self.exported_count}, skipped={self.skipped_count}, errors={self.error_count}"
        )
    
    def process_item(self, item, spider):
        """Procesa cada item y lo guarda como JSON."""
        # Aceptar tanto ArticuloInItem como diccionarios
        if not (isinstance(item, ArticuloInItem) or isinstance(item, dict)):
            logger.debug(f"Item is not ArticuloInItem or dict, skipping: {type(item)}")
            self.skipped_count += 1
            return item
        
        try:
            # Convertir item a dict
            adapter = ItemAdapter(item)
            item_dict = adapter.asdict()
            
            # Convertir datetime a ISO format
            item_dict = self._convert_datetime_to_iso(item_dict)
            
            # Generar nombre de archivo simple
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{spider.name}_{timestamp}_{self.exported_count:04d}.json"
            filepath = self.output_dir / filename
            
            # Guardar JSON sin comprimir
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(item_dict, f, ensure_ascii=False, indent=2, sort_keys=True)
            
            self.exported_count += 1
            
            logger.info(f"Exported article to {filename}")
            
            return item
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error exporting item: {e}", exc_info=True)
            # No dropear el item, dejar que otros pipelines lo procesen
            return item
    
    def _convert_datetime_to_iso(self, obj):
        """Convierte objetos datetime a string ISO recursivamente."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._convert_datetime_to_iso(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_datetime_to_iso(v) for v in obj]
        return obj