"""
Pipeline de exportación JSON para La Máquina de Noticias.

Este pipeline guarda los ArticuloInItem procesados como archivos
JSON comprimidos (.json.gz) para ser consumidos por el module_connector.
"""

import os
import json
import gzip
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from itemadapter import ItemAdapter
from scrapy import signals
from scrapy.exceptions import DropItem

from scraper_core.items import ArticuloInItem

logger = logging.getLogger(__name__)


class JsonWriterPipeline:
    """
    Exporta ArticuloInItem a archivos JSON comprimidos.
    
    Los archivos se guardan en el directorio configurado en SCRAPY_OUTPUT_DIR
    con el formato: {medio}_{fecha}_{titulo_slug}_{hash}.json.gz
    
    Este pipeline debe ejecutarse AL FINAL (prioridad alta) después
    de todos los pipelines de procesamiento y validación.
    """
    
    def __init__(self, output_dir: str):
        """
        Inicializa el pipeline.
        
        Args:
            output_dir: Directorio donde se guardarán los archivos
        """
        self.output_dir = Path(output_dir)
        self.exported_count = 0
        self.error_count = 0
        self.skipped_count = 0
        
        logger.info(f"JsonWriterPipeline initialized. Output directory: {self.output_dir}")
    
    @classmethod
    def from_crawler(cls, crawler):
        """
        Crea una instancia del pipeline desde el crawler.
        
        Args:
            crawler: Instancia del crawler de Scrapy
            
        Returns:
            Instancia configurada del pipeline
        """
        # Obtener directorio de salida de settings
        output_dir = crawler.settings.get(
            'SCRAPY_OUTPUT_DIR',
            '/data/scrapy_output/pending'
        )
        
        # Crear instancia
        instance = cls(output_dir)
        
        # Conectar señales si es necesario
        crawler.signals.connect(instance.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(instance.spider_closed, signal=signals.spider_closed)
        
        return instance
    
    def spider_opened(self, spider):
        """Se ejecuta cuando se abre el spider."""
        logger.info(f"JsonWriterPipeline opened for spider: {spider.name}")
        
        # Crear directorio de salida si no existe
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Output directory verified: {self.output_dir}")
        except Exception as e:
            logger.error(f"Error creating output directory: {e}")
            raise
    
    def spider_closed(self, spider):
        """Se ejecuta cuando se cierra el spider."""
        logger.info(
            f"JsonWriterPipeline closed for spider {spider.name}. "
            f"Stats: exported={self.exported_count}, "
            f"skipped={self.skipped_count}, errors={self.error_count}"
        )
    
    def process_item(self, item, spider):
        """
        Procesa cada item, exportándolo a JSON si es válido.
        
        Args:
            item: El item a procesar (debe ser ArticuloInItem)
            spider: El spider que generó el item
            
        Returns:
            El item sin modificar (para que otros pipelines lo procesen)
            
        Raises:
            DropItem: Si hay un error crítico al exportar
        """
        # Solo procesar ArticuloInItem
        if not isinstance(item, ArticuloInItem):
            logger.debug(f"Item is not ArticuloInItem, skipping JSON export: {type(item)}")
            self.skipped_count += 1
            return item
        
        try:
            # Convertir item a dict
            adapter = ItemAdapter(item)
            item_dict = adapter.asdict()
            
            # Convertir datetime a ISO format para JSON
            item_dict = self._convert_datetime_to_iso(item_dict)
            
            # Generar nombre de archivo
            filename = self._generate_filename(item_dict)
            filepath = self.output_dir / filename
            
            # Serializar a JSON con indentación para legibilidad
            json_content = json.dumps(
                item_dict,
                ensure_ascii=False,
                indent=2,
                sort_keys=True
            )
            
            # Comprimir y guardar
            with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                f.write(json_content)
            
            self.exported_count += 1
            
            # Log resumido (sin contenido completo)
            logger.info(
                f"Exported article to {filename}. "
                f"URL: {item_dict.get('url', 'Unknown')}, "
                f"Size: {len(json_content)} chars"
            )
            
            return item
            
        except Exception as e:
            self.error_count += 1
            logger.error(
                f"Error exporting item to JSON: {e}. "
                f"URL: {item.url if hasattr(item, 'url') else 'Unknown'}"
            )
            # No dropear el item, permitir que otros pipelines lo procesen
            return item
    
    def _generate_filename(self, item_dict: Dict[str, Any]) -> str:
        """
        Genera un nombre de archivo único para el item.
        
        Args:
            item_dict: Diccionario con los datos del artículo
            
        Returns:
            Nombre del archivo con extensión .json.gz
        """
        # Componentes del nombre
        medio = self._slugify(item_dict.get('medio', 'unknown'))
        
        # Fecha de publicación o actual
        fecha_str = item_dict.get('fecha_publicacion', '')
        if fecha_str:
            try:
                fecha = datetime.fromisoformat(fecha_str.replace('Z', '+00:00'))
                fecha_part = fecha.strftime('%Y%m%d_%H%M%S')
            except:
                fecha_part = datetime.now().strftime('%Y%m%d_%H%M%S')
        else:
            fecha_part = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Título truncado y slugificado
        titulo = item_dict.get('titular', 'sin_titulo')
        titulo_slug = self._slugify(titulo)[:50]  # Limitar longitud
        
        # Hash único basado en URL para evitar colisiones
        url = item_dict.get('url', '')
        if url:
            import hashlib
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        else:
            # Usar timestamp si no hay URL
            url_hash = str(int(datetime.now().timestamp()))[-8:]
        
        # Construir nombre: medio_fecha_titulo_hash.json.gz
        filename = f"article_{medio}_{fecha_part}_{titulo_slug}_{url_hash}.json.gz"
        
        return filename
    
    def _slugify(self, text: str) -> str:
        """
        Convierte texto a formato slug (URL-friendly).
        
        Args:
            text: Texto a convertir
            
        Returns:
            Texto en formato slug
        """
        import re
        
        # Convertir a minúsculas
        text = text.lower()
        
        # Reemplazar caracteres especiales y acentos comunes
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ñ': 'n', 'ü': 'u', 'à': 'a', 'è': 'e', 'ì': 'i',
            'ò': 'o', 'ù': 'u'
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Reemplazar caracteres no alfanuméricos con guiones
        text = re.sub(r'[^a-z0-9]+', '-', text)
        
        # Eliminar guiones al inicio y final
        text = text.strip('-')
        
        # Reemplazar múltiples guiones con uno solo
        text = re.sub(r'-+', '-', text)
        
        return text or 'unnamed'
    
    def _convert_datetime_to_iso(self, obj: Any) -> Any:
        """
        Convierte recursivamente objetos datetime a strings ISO.
        
        Args:
            obj: Objeto a convertir
            
        Returns:
            Objeto con datetimes convertidos
        """
        if hasattr(obj, 'isoformat'):
            # Es un objeto datetime
            return obj.isoformat()
        elif isinstance(obj, dict):
            # Recursivamente procesar diccionarios
            return {k: self._convert_datetime_to_iso(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            # Recursivamente procesar listas
            return [self._convert_datetime_to_iso(item) for item in obj]
        elif isinstance(obj, tuple):
            # Convertir tuplas a listas para JSON
            return [self._convert_datetime_to_iso(item) for item in obj]
        else:
            # Devolver sin cambios
            return obj