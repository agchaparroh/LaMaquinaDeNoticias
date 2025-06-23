# -*- coding: utf-8 -*-
"""
Spider para Sudamérica de Europa Press
Generado para La Máquina de Noticias

Tipo: scraping
Frecuencia recomendada: cada 60 minutos
Items por ejecución: 30
"""
import logging
from typing import Iterator, Dict, Any, Optional
from datetime import datetime
import re

from scrapy.http import Response, Request

from scraper_core.items import ArticuloInItem
from scraper_core.spiders.base.base_article import BaseArticleSpider
from scraper_core.spiders.base.utils import parse_date_string

# logger = logging.getLogger(__name__)  # Comentado - usar self.logger de Scrapy


class EuropapressSudamericaSpider(BaseArticleSpider):
    """
    Spider especializado para Sudamérica de Europa Press.
    
    Hereda de BaseArticleSpider que proporciona:
    - Rotación de user agents
    - Manejo de errores
    - Métodos de extracción
    - Validación básica
    
    URL objetivo: https://www.europapress.es/internacional/sudamerica-00407/
    Filtrado estricto: Solo artículos de la sección sudamerica-00407
    """
    
    name = 'europapress_sudamerica'
    allowed_domains = ['europapress.es']
    start_urls = ['https://www.europapress.es/internacional/sudamerica-00407/']
    
    # Información del medio (obligatorio)
    medio_nombre = 'Europa Press'
    pais = 'España'
    tipo_medio = 'agencia'  # diario/agencia/revista
    target_section = 'sudamerica'
    
    # Patrón para filtrar URLs de la sección
    section_pattern = re.compile(r'/internacional/noticia-')
    
    # Configuración específica
    custom_settings = {
        **BaseArticleSpider.custom_settings,
        'DOWNLOAD_DELAY': 3.0,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'CLOSESPIDER_ITEMCOUNT': 30,
        'CLOSESPIDER_TIMEOUT': 1800,
        'DUPEFILTER_CLASS': 'scrapy.dupefilters.RFPDupeFilter',
        'JOBDIR': f'./crawl_state_{name}',
        
        # Pipelines del proyecto
        'ITEM_PIPELINES': {
            'scraper_core.pipelines.validation.DataValidationPipeline': 100,
            'scraper_core.pipelines.cleaning.DataCleaningPipeline': 200,
            'scraper_core.pipelines.storage.SupabaseStoragePipeline': 300,
        }
    }
    
    def start_requests(self) -> Iterator[Request]:
        """Generar las solicitudes iniciales."""
        for url in self.start_urls:
            yield self.make_request(url, self.parse_article_list)
    
    def parse_article_list(self, response: Response) -> Iterator[Request]:
        """Extraer enlaces de artículos de la sección."""
        self.logger.info(f"Parseando página de sección: {response.url}")
        
        # Extraer enlaces de artículos usando selectores específicos de Europa Press
        article_links = []
        
        # Selector principal: artículos con clase ep-articleStandard
        articles = response.css('article.ep-articleStandard')
        
        for article in articles:
            # Extraer el enlace del título
            link = article.css('h2.articulo-titulo a::attr(href)').get()
            if link:
                article_links.append(link)
        
        # También buscar enlaces en otros posibles contenedores
        additional_links = response.css('a[href*="/internacional/noticia-"]::attr(href)').getall()
        article_links.extend(additional_links)
        
        # Eliminar duplicados manteniendo orden
        seen = set()
        unique_links = []
        for link in article_links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)
        
        self.logger.info(f"Encontrados {len(unique_links)} enlaces únicos de artículos")
        
        # Procesar cada enlace
        for link in unique_links[:self.custom_settings['CLOSESPIDER_ITEMCOUNT']]:
            if self._is_section_article(link):
                yield response.follow(link, self.parse_article)
    
    def parse_article(self, response: Response) -> Optional[ArticuloInItem]:
        """Extraer datos del artículo usando BaseArticleSpider."""
        self.logger.debug(f"Parseando artículo: {response.url}")
        
        # Verificar que es un artículo válido
        if not self._is_valid_article_page(response):
            self.logger.warning(f"Página no válida como artículo: {response.url}")
            return None
        
        # Usar métodos heredados para extracción básica
        title = self.extract_article_title(response)
        content = self.extract_article_content(response)
        
        if not title or not content:
            self.logger.warning(f"No se pudo extraer título o contenido de: {response.url}")
            return None
        
        # Crear y validar item
        item = self._create_article_item(response, title, content)
        
        if self.validate_article_data(dict(item)):
            return item
        return None
    
    def _is_section_article(self, url: str) -> bool:
        """
        Verificar que la URL pertenece a la sección objetivo.
        Filtrado estricto para emular comportamiento RSS.
        """
        # Debe contener el patrón de artículos internacionales
        if not self.section_pattern.search(url):
            self.logger.debug(f"URL filtrada (no es artículo de internacional): {url}")
            return False
        
        # Excluir patrones no deseados
        exclude_patterns = [
            '/archivo/', '/hemeroteca/', '/newsletter/',
            '/video/', '/galeria/', '/podcast/', '/tags/',
            '/temas/', '/especiales/'
        ]
        
        url_lower = url.lower()
        for pattern in exclude_patterns:
            if pattern in url_lower:
                self.logger.debug(f"URL excluida por patrón {pattern}: {url}")
                return False
        
        # Verificar que contiene "sudamerica" o es de la región
        # Nota: No todos los artículos de la sección tienen "sudamerica" en la URL
        # pero aparecen en la página de la sección
        return True
    
    def _is_valid_article_page(self, response: Response) -> bool:
        """Verificar que la página es un artículo válido."""
        # Verificar que tiene estructura de artículo
        has_title = bool(response.css('h1').get())
        has_content = bool(response.css('div.texto_noticia, div.article-content, div.noticia-texto').get())
        
        return has_title and has_content
    
    def _create_article_item(self, response: Response, title: str, 
                            content: str) -> ArticuloInItem:
        """
        Crear item con todos los campos requeridos.
        """
        item = ArticuloInItem()
        
        # Campos obligatorios
        item['url'] = response.url
        item['fuente'] = self.name
        item['titular'] = title
        item['contenido_texto'] = content
        item['contenido_html'] = response.text
        
        # Información del medio
        item['medio'] = self.medio_nombre
        item['medio_url_principal'] = f"https://{self.allowed_domains[0]}"
        item['pais_publicacion'] = self.pais
        item['tipo_medio'] = self.tipo_medio
        
        # Extraer metadata específica de Europa Press
        item['fecha_publicacion'] = self._extract_europapress_date(response)
        item['autor'] = self._extract_europapress_author(response)
        item['idioma'] = 'es'
        item['seccion'] = self.target_section
        
        # Extraer etiquetas/keywords
        keywords = response.css('meta[name="keywords"]::attr(content)').get()
        if keywords:
            item['etiquetas_fuente'] = [tag.strip() for tag in keywords.split(',')]
        else:
            item['etiquetas_fuente'] = []
        
        # Clasificación
        item['es_opinion'] = self._is_opinion(response)
        item['es_oficial'] = False
        
        # Timestamps
        item['fecha_recopilacion'] = datetime.utcnow()
        
        # Metadata adicional
        metadata = self._extract_metadata(response)
        metadata.update({
            'spider_type': 'scraping',
            'section_filter': 'strict',
            'execution_number': self.crawler.stats.get_value('item_scraped_count', 0) + 1 if hasattr(self, 'crawler') else 0
        })
        item['metadata'] = metadata
        
        return item
    
    def _extract_europapress_date(self, response: Response) -> Optional[datetime]:
        """Extraer fecha específica de Europa Press."""
        # Intentar varios selectores
        date_selectors = [
            'time[datetime]::attr(datetime)',
            'meta[property="article:published_time"]::attr(content)',
            'span.fecha::text',
            'div.fecha-publicacion::text'
        ]
        
        for selector in date_selectors:
            date_str = response.css(selector).get()
            if date_str:
                try:
                    # Europa Press usa formato ISO en datetime
                    if 'T' in date_str:
                        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    else:
                        # Intentar parsear otros formatos
                        return parse_date_string(date_str)
                except Exception as e:
                    self.logger.debug(f"Error parseando fecha {date_str}: {e}")
        
        # Si no se encuentra, usar el método base
        return self.extract_publication_date(response)
    
    def _extract_europapress_author(self, response: Response) -> str:
        """Extraer autor específico de Europa Press."""
        # Europa Press suele usar "Europa Press" como autor genérico
        author_selectors = [
            'span.autor::text',
            'div.author::text',
            'meta[name="author"]::attr(content)'
        ]
        
        for selector in author_selectors:
            author = response.css(selector).get()
            if author:
                return author.strip()
        
        # Por defecto para agencia
        return 'Europa Press'
    
    def _is_opinion(self, response: Response) -> bool:
        """Detectar si es artículo de opinión."""
        indicators = ['/opinion/', '/columna/', '/editorial/', '/tribuna/', '/analisis/']
        url_lower = response.url.lower()
        
        # Verificar en URL
        if any(ind in url_lower for ind in indicators):
            return True
        
        # Verificar en sección
        section = response.css('span.seccion::text, div.section::text').get()
        if section and 'opinión' in section.lower():
            return True
        
        return False
    
    def _extract_metadata(self, response: Response) -> Dict[str, Any]:
        """Extraer metadata adicional del artículo."""
        metadata = {}
        
        # Tags/keywords
        keywords = response.css('meta[name="keywords"]::attr(content)').get()
        if keywords:
            metadata['keywords'] = keywords
        
        # Categorías/tags del artículo
        tags = response.css('a.tag::text, a.etiqueta::text').getall()
        if tags:
            metadata['tags'] = tags
        
        # Imagen principal
        main_image = response.css('meta[property="og:image"]::attr(content)').get()
        if main_image:
            metadata['main_image'] = main_image
        
        # Número de párrafos
        paragraphs = response.css('div.texto_noticia p, div.article-content p').getall()
        metadata['paragraph_count'] = len(paragraphs)
        
        return metadata