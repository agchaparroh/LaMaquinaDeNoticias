# Data Cleaning Pipeline
"""
Pipeline for cleaning and normalizing extracted data.
Handles HTML stripping, text normalization, and date standardization.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

from itemadapter import ItemAdapter
from scrapy import Spider
from bs4 import BeautifulSoup
import unicodedata

from ..items import ArticuloInItem
from .exceptions import CleaningError

logger = logging.getLogger(__name__)


class DataCleaningPipeline:
    """
    Cleans and normalizes scraped article data.
    
    This pipeline performs:
    - HTML tag stripping from content fields
    - Text normalization (whitespace, special characters)
    - Date standardization
    - URL normalization
    - Author name cleaning
    - Tag/category normalization
    """
    
    # Fields that should have HTML stripped
    HTML_STRIP_FIELDS = [
        'titular',
        'contenido_texto',
        'resumen',
        'autor'
    ]
    
    # Fields that need text normalization
    TEXT_NORMALIZE_FIELDS = [
        'titular',
        'contenido_texto',
        'resumen',
        'autor',
        'medio',
        'seccion'
    ]
    
    # Fields that contain lists and need normalization
    LIST_FIELDS = [
        'etiquetas_fuente',
        'categorias_asignadas'
    ]
    
    def __init__(self):
        self.cleaning_stats = {
            'total_items': 0,
            'items_cleaned': 0,
            'html_stripped': 0,
            'text_normalized': 0,
            'dates_standardized': 0,
            'urls_normalized': 0
        }
    
    @classmethod
    def from_crawler(cls, crawler):
        """Initialize from crawler with custom settings."""
        instance = cls()
        
        # Load settings
        instance.strip_html = crawler.settings.getbool('CLEANING_STRIP_HTML', True)
        instance.normalize_whitespace = crawler.settings.getbool('CLEANING_NORMALIZE_WHITESPACE', True)
        instance.remove_empty_lines = crawler.settings.getbool('CLEANING_REMOVE_EMPTY_LINES', True)
        instance.standardize_quotes = crawler.settings.getbool('CLEANING_STANDARDIZE_QUOTES', True)
        instance.preserve_html_content = crawler.settings.getbool('CLEANING_PRESERVE_HTML_CONTENT', True)
        
        logger.info(
            f"DataCleaningPipeline initialized with settings: "
            f"strip_html={instance.strip_html}, "
            f"normalize_whitespace={instance.normalize_whitespace}, "
            f"remove_empty_lines={instance.remove_empty_lines}"
        )
        
        return instance
    
    def open_spider(self, spider: Spider):
        """Called when spider opens."""
        logger.info(f"DataCleaningPipeline opened for spider: {spider.name}")
        self.spider_name = spider.name
    
    def close_spider(self, spider: Spider):
        """Called when spider closes. Log cleaning statistics."""
        logger.info(
            f"DataCleaningPipeline closed for spider: {spider.name}. "
            f"Stats: {self.cleaning_stats}"
        )
    
    def process_item(self, item, spider: Spider):
        """Main processing method that cleans each item."""
        if not isinstance(item, ArticuloInItem):
            logger.debug(f"Item is not ArticuloInItem, skipping cleaning: {type(item)}")
            return item
        
        adapter = ItemAdapter(item)
        item_url = adapter.get('url', 'Unknown URL')
        
        self.cleaning_stats['total_items'] += 1
        
        try:
            # Perform all cleaning operations
            if self.strip_html:
                self._strip_html_from_fields(adapter, item_url)
            
            if self.normalize_whitespace:
                self._normalize_text_fields(adapter, item_url)
            
            self._clean_urls(adapter, item_url)
            self._standardize_dates(adapter, item_url)
            self._clean_author_names(adapter, item_url)
            self._normalize_lists(adapter, item_url)
            
            # Clean and preserve HTML content separately
            if self.preserve_html_content:
                self._clean_html_content(adapter, item_url)
            
            self.cleaning_stats['items_cleaned'] += 1
            logger.debug(f"Item cleaned successfully: {item_url}")
            
        except CleaningError as e:
            logger.error(f"Cleaning error for {item_url}: {e}")
            # Add error but don't drop item - cleaning errors are non-fatal
            adapter['error_detalle'] = f"Cleaning error: {e}; {adapter.get('error_detalle', '')}"
        except Exception as e:
            logger.error(f"Unexpected cleaning error for {item_url}: {e}", exc_info=True)
            adapter['error_detalle'] = f"Unexpected cleaning error: {e}; {adapter.get('error_detalle', '')}"
        
        return item
    
    def _strip_html_from_fields(self, adapter: ItemAdapter, item_url: str):
        """Remove HTML tags from specified fields."""
        for field in self.HTML_STRIP_FIELDS:
            value = adapter.get(field)
            if not value or not isinstance(value, str):
                continue
            
            try:
                # Use BeautifulSoup to properly parse and extract text
                soup = BeautifulSoup(value, 'html.parser')
                
                # Remove script and style elements
                for script in soup(['script', 'style']):
                    script.decompose()
                
                # Get text and normalize whitespace
                text = soup.get_text(separator=' ', strip=True)
                
                # Clean up extra whitespace
                text = ' '.join(text.split())
                
                adapter[field] = text
                self.cleaning_stats['html_stripped'] += 1
                
            except Exception as e:
                logger.warning(f"Failed to strip HTML from field '{field}' for {item_url}: {e}")
    
    def _normalize_text_fields(self, adapter: ItemAdapter, item_url: str):
        """Normalize text in specified fields."""
        for field in self.TEXT_NORMALIZE_FIELDS:
            value = adapter.get(field)
            if not value or not isinstance(value, str):
                continue
            
            try:
                # Original text for comparison
                original = value
                
                # Normalize unicode characters
                value = unicodedata.normalize('NFKC', value)
                
                # Replace multiple spaces with single space
                value = re.sub(r'\s+', ' ', value)
                
                # Remove leading/trailing whitespace from lines
                if self.remove_empty_lines:
                    lines = [line.strip() for line in value.split('\n')]
                    lines = [line for line in lines if line]
                    value = '\n'.join(lines)
                
                # Standardize quotes if enabled
                if self.standardize_quotes:
                    # Replace various quote types with standard ones
                    value = re.sub(r'["""]', '"', value)
                    value = re.sub(r"'''", "'", value)
                
                # Remove zero-width characters
                value = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', value)
                
                # Fix common encoding issues
                value = value.replace('Ã¡', 'á').replace('Ã©', 'é').replace('Ã­', 'í')
                value = value.replace('Ã³', 'ó').replace('Ãº', 'ú').replace('Ã±', 'ñ')
                
                # Strip final result
                value = value.strip()
                
                if value != original:
                    adapter[field] = value
                    self.cleaning_stats['text_normalized'] += 1
                
            except Exception as e:
                logger.warning(f"Failed to normalize text in field '{field}' for {item_url}: {e}")
    
    def _clean_urls(self, adapter: ItemAdapter, item_url: str):
        """Clean and normalize URLs."""
        url = adapter.get('url')
        if not url:
            return
        
        try:
            # Remove URL fragments
            parsed = urlparse(url)
            clean_url = parsed._replace(fragment='').geturl()
            
            # Remove trailing slashes
            clean_url = clean_url.rstrip('/')
            
            # Remove common tracking parameters
            tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term']
            if parsed.query:
                # Parse query string and filter out tracking params
                from urllib.parse import parse_qs, urlencode
                params = parse_qs(parsed.query, keep_blank_values=True)
                filtered_params = {k: v for k, v in params.items() if k not in tracking_params}
                if filtered_params != params:
                    clean_query = urlencode(filtered_params, doseq=True)
                    clean_url = parsed._replace(query=clean_query).geturl()
            
            if clean_url != url:
                adapter['url'] = clean_url
                self.cleaning_stats['urls_normalized'] += 1
                
        except Exception as e:
            logger.warning(f"Failed to clean URL for {item_url}: {e}")
    
    def _standardize_dates(self, adapter: ItemAdapter, item_url: str):
        """Ensure all dates are in ISO format."""
        date_fields = ['fecha_publicacion', 'fecha_recopilacion', 'fecha_procesamiento']
        
        for field in date_fields:
            value = adapter.get(field)
            if not value:
                continue
            
            try:
                # If it's already a datetime object, convert to ISO
                if isinstance(value, datetime):
                    adapter[field] = value.isoformat()
                    self.cleaning_stats['dates_standardized'] += 1
                # If it's a string, try to parse and standardize
                elif isinstance(value, str):
                    # Check if already in ISO format
                    iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
                    if not re.match(iso_pattern, value):
                        # Try to parse with dateutil for flexibility
                        from dateutil import parser
                        dt = parser.parse(value)
                        adapter[field] = dt.isoformat()
                        self.cleaning_stats['dates_standardized'] += 1
                        
            except Exception as e:
                logger.warning(f"Failed to standardize date in field '{field}' for {item_url}: {e}")
    
    def _clean_author_names(self, adapter: ItemAdapter, item_url: str):
        """Clean and normalize author names."""
        autor = adapter.get('autor')
        if not autor or not isinstance(autor, str):
            return
        
        try:
            original = autor
            
            # Remove common prefixes
            prefixes_to_remove = ['Por ', 'By ', 'De ', 'From ']
            for prefix in prefixes_to_remove:
                if autor.startswith(prefix):
                    autor = autor[len(prefix):]
            
            # Handle multiple authors
            # Common separators: 'y', 'and', '&', ',', ';'
            if any(sep in autor for sep in [' y ', ' and ', ' & ', ', ', '; ']):
                # Split by various separators
                authors = re.split(r'\s+y\s+|\s+and\s+|\s*&\s*|,\s*|;\s*', autor)
                # Clean each author name
                authors = [self._clean_single_author(a) for a in authors if a.strip()]
                # Rejoin with consistent separator
                autor = ', '.join(authors)
            else:
                autor = self._clean_single_author(autor)
            
            # Remove extra spaces
            autor = ' '.join(autor.split())
            
            if autor != original:
                adapter['autor'] = autor
                
        except Exception as e:
            logger.warning(f"Failed to clean author name for {item_url}: {e}")
    
    def _clean_single_author(self, author: str) -> str:
        """Clean a single author name."""
        # Remove titles and suffixes
        titles = ['Dr.', 'Prof.', 'Sr.', 'Sra.', 'Mr.', 'Mrs.', 'Ms.']
        for title in titles:
            author = author.replace(title + ' ', '').replace(title, '')
        
        # Remove email addresses or social media handles
        author = re.sub(r'\S+@\S+', '', author)  # Email
        author = re.sub(r'@\w+', '', author)     # Twitter handle
        
        # Normalize case (Title Case)
        author = author.title()
        
        return author.strip()
    
    def _normalize_lists(self, adapter: ItemAdapter, item_url: str):
        """Normalize list fields (tags, categories)."""
        for field in self.LIST_FIELDS:
            value = adapter.get(field)
            if not value:
                continue
            
            try:
                # Convert string to list if needed
                if isinstance(value, str):
                    # Split by common separators
                    value = re.split(r'[,;|]', value)
                
                if isinstance(value, list):
                    # Clean each item
                    cleaned = []
                    for item in value:
                        if isinstance(item, str):
                            item = item.strip()
                            # Remove quotes
                            item = item.strip('"\'')
                            # Normalize case
                            item = item.lower()
                            # Remove duplicates
                            if item and item not in cleaned:
                                cleaned.append(item)
                    
                    adapter[field] = cleaned
                    
            except Exception as e:
                logger.warning(f"Failed to normalize list field '{field}' for {item_url}: {e}")
    
    def _clean_html_content(self, adapter: ItemAdapter, item_url: str):
        """Clean HTML content while preserving structure."""
        html_content = adapter.get('contenido_html')
        if not html_content or not isinstance(html_content, str):
            return
        
        try:
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove unwanted tags
            unwanted_tags = ['script', 'style', 'iframe', 'noscript', 'svg']
            for tag in unwanted_tags:
                for element in soup.find_all(tag):
                    element.decompose()
            
            # Remove comments
            for comment in soup.find_all(text=lambda text: isinstance(text, type(soup.new_string('')))):
                if str(comment).strip().startswith('<!--'):
                    comment.extract()
            
            # Remove empty tags
            for tag in soup.find_all():
                if not tag.get_text(strip=True) and tag.name not in ['img', 'br', 'hr']:
                    tag.decompose()
            
            # Clean attributes (remove style, onclick, etc.)
            allowed_attrs = {
                'a': ['href', 'title'],
                'img': ['src', 'alt', 'title'],
                'blockquote': ['cite'],
                'q': ['cite']
            }
            
            for tag in soup.find_all():
                attrs = dict(tag.attrs)
                for attr in attrs:
                    if tag.name in allowed_attrs and attr in allowed_attrs[tag.name]:
                        continue
                    del tag[attr]
            
            # Convert back to string
            cleaned_html = str(soup)
            
            # Minify HTML by removing unnecessary whitespace
            cleaned_html = re.sub(r'>\s+<', '><', cleaned_html)
            cleaned_html = re.sub(r'\s+', ' ', cleaned_html)
            
            adapter['contenido_html'] = cleaned_html
            
        except Exception as e:
            logger.warning(f"Failed to clean HTML content for {item_url}: {e}")
