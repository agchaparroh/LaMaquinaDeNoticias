"""
Supabase Storage Pipeline for Scrapy
====================================

This pipeline handles storing extracted articles in Supabase:
- Stores article metadata in the 'articulos' table
- Compresses and stores HTML content in Supabase Storage
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import re
import os

from scrapy import Spider
from scrapy.crawler import Crawler
from scrapy.exceptions import DropItem

from ..items import ArticuloInItem, ArticuloAdapter
from ..utils.supabase_client import get_supabase_client, SupabaseClient
from ..utils.compression import compress_html

logger = logging.getLogger(__name__)


class SupabaseStoragePipeline:
    """
    Pipeline for storing articles in Supabase database and storage.
    
    Features:
    - Validates required fields
    - Stores article metadata in database
    - Compresses and stores HTML in storage bucket
    - Handles errors gracefully with detailed logging
    """
    
    def __init__(self, supabase_client: Optional[SupabaseClient] = None):
        """Initialize the pipeline with optional client injection for testing."""
        self.supabase_client = supabase_client or get_supabase_client()
        self.storage_bucket = os.getenv('SUPABASE_STORAGE_BUCKET', 'articulos-html')
        self.stats = {
            'items_processed': 0,
            'items_stored': 0,
            'items_failed': 0,
            'storage_errors': 0,
            'db_errors': 0
        }
    
    @classmethod
    def from_crawler(cls, crawler: Crawler):
        """Create pipeline instance from crawler."""
        # Get settings
        settings = crawler.settings
        
        # Create pipeline instance
        pipeline = cls()
        
        # Override bucket name if specified in settings
        if settings.get('SUPABASE_STORAGE_BUCKET'):
            pipeline.storage_bucket = settings.get('SUPABASE_STORAGE_BUCKET')
        
        # Ensure bucket exists
        try:
            pipeline.supabase_client.create_bucket_if_not_exists(
                pipeline.storage_bucket, 
                public=False
            )
        except Exception as e:
            logger.error(f"Failed to ensure bucket exists: {e}")
        
        return pipeline
    
    def process_item(self, item: ArticuloInItem, spider: Spider) -> ArticuloInItem:
        """
        Process an article item through the pipeline.
        
        Args:
            item: The ArticuloInItem to process
            spider: The spider that extracted the item
            
        Returns:
            The processed item with additional metadata
        """
        self.stats['items_processed'] += 1
        
        try:
            # Create adapter and validate
            adapter = ArticuloAdapter(item)
            
            # Validate required fields
            try:
                adapter.validate_required_fields()
            except ValueError as e:
                logger.error(f"Item validation failed: {e}")
                item['error_detalle'] = str(e)
                self.stats['items_failed'] += 1
                return item  # Return item with error instead of dropping
            
            # Store HTML if present
            if item.get('contenido_html'):
                try:
                    storage_path = self._store_html_content(
                        item['contenido_html'],
                        item['url'],
                        item['medio']
                    )
                    adapter['storage_path'] = storage_path
                    item['storage_path'] = storage_path
                except Exception as e:
                    logger.error(f"Failed to store HTML content: {e}")
                    adapter['error_detalle'] = f"Storage error: {str(e)}"
                    item['error_detalle'] = adapter['error_detalle']
                    self.stats['storage_errors'] += 1
                    # Continue even if storage fails
            
            # Store in database
            try:
                # Upsert the article (update if exists, insert if not)
                result = self.supabase_client.upsert_articulo(adapter)
                logger.info(f"Successfully stored article: {item['url']}")
                self.stats['items_stored'] += 1
            except Exception as e:
                logger.error(f"Failed to store article in database: {e}")
                item['error_detalle'] = f"Database error: {str(e)}"
                self.stats['db_errors'] += 1
                self.stats['items_failed'] += 1
            
        except Exception as e:
            logger.error(f"Unexpected error processing item: {e}")
            item['error_detalle'] = f"Processing error: {str(e)}"
            self.stats['items_failed'] += 1
        
        return item
    
    def _store_html_content(self, html_content: str, url: str, medio: str) -> str:
        """
        Compress and store HTML content in Supabase Storage.
        
        Args:
            html_content: The HTML content to store
            url: The article URL (for generating filename)
            medio: The media source name
            
        Returns:
            The storage path of the uploaded file
        """
        # Generate a safe filename from URL
        url_hash = self._generate_url_hash(url)
        medio_slug = self._slugify(medio)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create storage path: medio/YYYYMMDD/hash_timestamp.html.gz
        date_folder = datetime.now().strftime("%Y%m%d")
        filename = f"{url_hash}_{timestamp}.html.gz"
        storage_path = f"{medio_slug}/{date_folder}/{filename}"
        
        # Compress HTML
        compressed_content = compress_html(html_content)
        
        # Upload to storage
        self.supabase_client.upload_to_storage(
            bucket_name=self.storage_bucket,
            file_path=storage_path,
            file_content=compressed_content,
            content_type='application/gzip'
        )
        
        logger.debug(f"Stored HTML at: {storage_path}")
        return storage_path
    
    def _generate_url_hash(self, url: str) -> str:
        """Generate a short hash from URL for filename."""
        import hashlib
        return hashlib.md5(url.encode()).hexdigest()[:8]
    
    def _slugify(self, text: str) -> str:
        """Convert text to a safe slug for file paths."""
        # Remove special characters and spaces
        text = re.sub(r'[^\w\s-]', '', text.lower())
        text = re.sub(r'[-\s]+', '-', text)
        return text.strip('-')[:50]  # Limit length
    
    def close_spider(self, spider: Spider):
        """Log statistics when spider closes."""
        logger.info(f"Pipeline statistics for {spider.name}:")
        logger.info(f"  Items processed: {self.stats['items_processed']}")
        logger.info(f"  Items stored: {self.stats['items_stored']}")
        logger.info(f"  Items failed: {self.stats['items_failed']}")
        logger.info(f"  Storage errors: {self.stats['storage_errors']}")
        logger.info(f"  Database errors: {self.stats['db_errors']}")
