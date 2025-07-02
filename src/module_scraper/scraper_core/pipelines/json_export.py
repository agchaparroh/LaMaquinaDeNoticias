# JSON Export Pipeline
"""
Pipeline for exporting scraped articles as JSON.gz files for module_connector.
Handles compression and export to monitored directory for further LLM processing.
"""

import os
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from itemadapter import ItemAdapter
from scrapy import Spider

from scraper_core.items import ArticuloInItem
from ..utils.compression import compress_html
from .exceptions import CleaningError

logger = logging.getLogger(__name__)


class JsonGzExportPipeline:
    """
    Exports scraped articles as compressed JSON files for module_connector.
    
    This pipeline:
    - Converts ArticuloInItem to JSON format compatible with module_connector
    - Compresses content using gzip
    - Saves files in directory monitored by module_connector
    - Only active when ENABLE_PIPELINE_EXPORT=true
    - Respects DEVELOPMENT_MODE for debugging
    """
    
    def __init__(self):
        self.export_stats = {
            'total_items': 0,
            'exported_items': 0,
            'failed_exports': 0,
            'total_size_bytes': 0,
            'compressed_size_bytes': 0
        }
        
    @classmethod
    def from_crawler(cls, crawler):
        """Initialize from crawler with custom settings."""
        instance = cls()
        
        # Load export configuration
        instance.enabled = crawler.settings.getbool('ENABLE_PIPELINE_EXPORT', False)
        instance.development_mode = os.getenv('DEVELOPMENT_MODE', 'false').lower() == 'true'
        
        # Export directory configuration
        instance.export_directory = crawler.settings.get(
            'EXPORT_DIRECTORY', 
            os.getenv('SCRAPER_OUTPUT_DIR', '/data/scrapy_output/pending')
        )
        
        # Compression settings
        instance.compression_level = crawler.settings.getint('EXPORT_COMPRESSION_LEVEL', 6)
        instance.include_html = crawler.settings.getbool('EXPORT_INCLUDE_HTML', True)
        
        # File naming settings
        instance.filename_prefix = crawler.settings.get('EXPORT_FILENAME_PREFIX', 'article')
        instance.max_filename_length = crawler.settings.getint('EXPORT_MAX_FILENAME_LENGTH', 100)
        
        # Create export directory if it doesn't exist
        if instance.enabled:
            try:
                os.makedirs(instance.export_directory, exist_ok=True)
                logger.info(f"JsonGzExportPipeline export directory ready: {instance.export_directory}")
            except Exception as e:
                logger.error(f"Failed to create export directory {instance.export_directory}: {e}")
                instance.enabled = False
        
        logger.info(
            f"JsonGzExportPipeline initialized: enabled={instance.enabled}, "
            f"development_mode={instance.development_mode}, "
            f"export_dir={instance.export_directory}"
        )
        
        return instance
    
    def open_spider(self, spider: Spider):
        """Called when spider opens."""
        if self.enabled:
            logger.info(f"JsonGzExportPipeline opened for spider: {spider.name}")
            self.spider_name = spider.name
            self.spider_start_time = datetime.utcnow()
        else:
            logger.debug(f"JsonGzExportPipeline disabled for spider: {spider.name}")
    
    def close_spider(self, spider: Spider):
        """Called when spider closes. Log export statistics."""
        if self.enabled:
            compression_ratio = 0
            if self.export_stats['total_size_bytes'] > 0:
                compression_ratio = (
                    1 - self.export_stats['compressed_size_bytes'] / self.export_stats['total_size_bytes']
                ) * 100
            
            logger.info(
                f"JsonGzExportPipeline closed for spider: {spider.name}. "
                f"Stats: {self.export_stats}, compression: {compression_ratio:.1f}%"
            )
    
    def process_item(self, item, spider: Spider):
        """Main processing method that exports each item."""
        # Skip if pipeline is disabled
        if not self.enabled:
            return item
            
        if not isinstance(item, ArticuloInItem):
            logger.debug(f"Item is not ArticuloInItem, skipping export: {type(item)}")
            return item
        
        adapter = ItemAdapter(item)
        item_url = adapter.get('url', 'Unknown URL')
        
        self.export_stats['total_items'] += 1
        
        try:
            # Convert item to export format
            export_data = self._prepare_export_data(adapter, spider)
            
            # Generate unique filename
            filename = self._generate_filename(adapter, spider)
            file_path = os.path.join(self.export_directory, filename)
            
            # Export to compressed JSON file
            success = self._export_to_file(export_data, file_path, item_url)
            
            if success:
                self.export_stats['exported_items'] += 1
                if self.development_mode:
                    logger.info(f"🧪 DEV: Exported {item_url} to {filename}")
                else:
                    logger.debug(f"Exported article to {filename}")
            else:
                self.export_stats['failed_exports'] += 1
                
        except Exception as e:
            self.export_stats['failed_exports'] += 1
            logger.error(f"Export failed for {item_url}: {e}", exc_info=True)
            
            # Add export error to item but don't drop it
            adapter['error_detalle'] = f"Export error: {e}; {adapter.get('error_detalle', '')}"
        
        return item
    
    def _prepare_export_data(self, adapter: ItemAdapter, spider: Spider) -> Dict[str, Any]:
        """Prepare item data for export to module_connector format."""
        # Start with all item data
        export_data = adapter.asdict()
        
        # Add export metadata
        export_data['export_metadata'] = {
            'exported_at': datetime.utcnow().isoformat(),
            'spider_name': spider.name,
            'export_pipeline_version': '1.0',
            'development_mode': self.development_mode
        }
        
        # Ensure required fields for module_connector
        if not export_data.get('fuente'):
            export_data['fuente'] = spider.name
            
        # Set estado_procesamiento for connector tracking
        export_data['estado_procesamiento'] = 'pendiente_connector'
        
        # Ensure datetime fields are ISO strings
        date_fields = ['fecha_publicacion', 'fecha_recopilacion', 'fecha_procesamiento']
        for field in date_fields:
            if field in export_data and export_data[field]:
                value = export_data[field]
                if hasattr(value, 'isoformat'):
                    export_data[field] = value.isoformat()
        
        # Handle HTML content based on settings
        if not self.include_html and 'contenido_html' in export_data:
            # Remove HTML to reduce file size if not needed
            del export_data['contenido_html']
        
        # Clean up any None values to reduce file size
        export_data = {k: v for k, v in export_data.items() if v is not None}
        
        return export_data
    
    def _generate_filename(self, adapter: ItemAdapter, spider: Spider) -> str:
        """Generate unique filename for exported article."""
        # Get article details for filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        
        # Try to create meaningful filename from title or URL
        title_part = ""
        if adapter.get('titular'):
            title = adapter['titular']
            # Clean title for filename
            title_clean = ''.join(c for c in title if c.isalnum() or c in '-_').lower()
            title_part = title_clean[:30] if title_clean else ""
        
        # Construct filename parts
        parts = [self.filename_prefix, spider.name, timestamp]
        if title_part:
            parts.append(title_part)
        parts.append(unique_id)
        
        # Join and add extension
        filename = '_'.join(parts) + '.json.gz'
        
        # Ensure filename isn't too long
        if len(filename) > self.max_filename_length:
            # Truncate middle parts, keep prefix, spider, timestamp and unique_id
            filename = f"{self.filename_prefix}_{spider.name}_{timestamp}_{unique_id}.json.gz"
        
        return filename
    
    def _export_to_file(self, data: Dict[str, Any], file_path: str, item_url: str) -> bool:
        """Export data to compressed JSON file."""
        try:
            # Convert to JSON string
            json_content = json.dumps(data, ensure_ascii=False, indent=None, separators=(',', ':'))
            
            # Track original size
            original_size = len(json_content.encode('utf-8'))
            self.export_stats['total_size_bytes'] += original_size
            
            # Compress the JSON content
            compressed_content = compress_html(
                json_content, 
                compression_level=self.compression_level,
                encoding='utf-8'
            )
            
            # Track compressed size
            compressed_size = len(compressed_content)
            self.export_stats['compressed_size_bytes'] += compressed_size
            
            # Write to file
            with open(file_path, 'wb') as f:
                f.write(compressed_content)
            
            # Log success with compression info
            compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
            logger.debug(
                f"Exported {item_url}: {original_size}B -> {compressed_size}B "
                f"({compression_ratio:.1f}% compression)"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to export {item_url} to {file_path}: {e}")
            
            # Clean up partial file if it exists
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
            
            return False
    
    def get_export_stats(self) -> Dict[str, Any]:
        """Get current export statistics."""
        stats = self.export_stats.copy()
        
        # Add computed metrics
        if stats['total_items'] > 0:
            stats['success_rate'] = (stats['exported_items'] / stats['total_items']) * 100
        else:
            stats['success_rate'] = 0
            
        if stats['total_size_bytes'] > 0:
            stats['compression_ratio'] = (
                1 - stats['compressed_size_bytes'] / stats['total_size_bytes']
            ) * 100
        else:
            stats['compression_ratio'] = 0
            
        return stats