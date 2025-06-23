# -*- coding: utf-8 -*-
"""
Spider simplificado para Sudamérica de Europa Press
Generado para La Máquina de Noticias

Este spider evita problemas con el logger y funciona directamente con Scrapy.
"""
import logging
from typing import Iterator, Optional
from datetime import datetime
import re

import scrapy
from scrapy.http import Response

from scraper_core.items import ArticuloInItem


class EuropapressSudamericaSimpleSpider(scrapy.Spider):
    """
    Spider para la sección Sudamérica de Europa Press.
    """
    
    name = 'europapress_sudamerica_simple'
    allowed_domains = ['europapress.es']
    start_urls = ['https://www.europapress.es/internacional/sudamerica-00407/']
    
    # Información del medio
    medio_nombre = 'Europa Press'
    pais = 'España'
    tipo_medio = 'agencia'
    target_section = 'sudamerica'
    
    # Patrón para filtrar URLs
    section_pattern = re.compile(r'/internacional/noticia-')
    
    # Configuración
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 3.0,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'CLOSESPIDER_ITEMCOUNT': 30,
        'CLOSESPIDER_TIMEOUT': 1800,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    def parse(self, response: Response) -> Iterator[scrapy.Request]:
        """Parsear la página principal y extraer enlaces a artículos."""
        self.logger.info(f"Parseando página de sección: {response.url}")
        
        # Extraer enlaces de artículos
        article_links = []
        
        # Buscar artículos en la estructura de Europa Press
        articles = response.css('article.ep-articleStandard')
        
        for article in articles:
            link = article.css('h2.articulo-titulo a::attr(href)').get()
            if link:
                article_links.append(link)
        
        # Eliminar duplicados
        article_links = list(set(article_links))
        
        self.logger.info(f"Encontrados {len(article_links)} artículos")
        
        # Procesar enlaces
        for link in article_links[:30]:  # Limitar a 30
            if self._is_valid_article_url(link):
                yield response.follow(link, self.parse_article)
    
    def parse_article(self, response: Response) -> Optional[ArticuloInItem]:
        """Parsear un artículo individual."""
        self.logger.debug(f"Parseando artículo: {response.url}")
        
        # Crear item
        item = ArticuloInItem()
        
        # Extraer datos básicos
        item['url'] = response.url
        item['fuente'] = self.name
        
        # Título
        title = response.css('h1::text').get()
        if not title:
            self.logger.warning(f"No se encontró título en {response.url}")
            return None
        item['titular'] = title.strip()
        
        # Contenido
        paragraphs = response.css('div.texto_noticia p::text, div.article-content p::text').getall()
        if not paragraphs:
            # Intentar selector alternativo
            paragraphs = response.css('div[itemprop="articleBody"] p::text').getall()
        
        if paragraphs:
            content = '\n\n'.join(p.strip() for p in paragraphs if p.strip())
            item['contenido_texto'] = content
        else:
            self.logger.warning(f"No se encontró contenido en {response.url}")
            return None
        
        # HTML completo
        item['contenido_html'] = response.text
        
        # Información del medio
        item['medio'] = self.medio_nombre
        item['medio_url_principal'] = f"https://{self.allowed_domains[0]}"
        item['pais_publicacion'] = self.pais
        item['tipo_medio'] = self.tipo_medio
        item['seccion'] = self.target_section
        
        # Fecha de publicación
        date_str = response.css('time[datetime]::attr(datetime)').get()
        if date_str:
            try:
                item['fecha_publicacion'] = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                item['fecha_publicacion'] = datetime.utcnow()
        else:
            item['fecha_publicacion'] = datetime.utcnow()
        
        # Autor
        author = response.css('span.autor::text, meta[name="author"]::attr(content)').get()
        item['autor'] = author.strip() if author else 'Europa Press'
        
        # Etiquetas del medio (tags/keywords)
        keywords = response.css('meta[name="keywords"]::attr(content)').get()
        if keywords:
            item['etiquetas_fuente'] = keywords.split(',')
        else:
            item['etiquetas_fuente'] = []
        
        # Metadatos
        item['idioma'] = 'es'
        item['es_opinion'] = self._is_opinion(response.url)
        item['es_oficial'] = False
        item['fecha_recopilacion'] = datetime.utcnow()
        
        # Metadata adicional
        metadata = {
            'spider_type': 'scraping',
            'section_filter': 'strict'
        }
        
        # Keywords
        keywords = response.css('meta[name="keywords"]::attr(content)').get()
        if keywords:
            metadata['keywords'] = keywords
        
        item['metadata'] = metadata
        
        return item
    
    def _is_valid_article_url(self, url: str) -> bool:
        """Verificar si la URL es válida para procesar."""
        if not url:
            return False
        
        # Debe ser de internacional
        if not self.section_pattern.search(url):
            return False
        
        # Excluir tipos no deseados
        exclude_patterns = ['/archivo/', '/video/', '/galeria/', '/tags/']
        for pattern in exclude_patterns:
            if pattern in url.lower():
                return False
        
        return True
    
    def _is_opinion(self, url: str) -> bool:
        """Detectar si es artículo de opinión."""
        opinion_patterns = ['/opinion/', '/columna/', '/tribuna/']
        return any(pattern in url.lower() for pattern in opinion_patterns)