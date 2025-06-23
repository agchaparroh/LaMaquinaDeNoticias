# -*- coding: utf-8 -*-
"""
Spider v2 para Sudamérica de Europa Press
Versión mejorada con validación completa de campos

Este spider incluye todos los campos requeridos y validación.
"""
import logging
from typing import Iterator, Optional
from datetime import datetime
import re

import scrapy
from scrapy.http import Response

from scraper_core.items import ArticuloInItem


class EuropapressSudamericaV2Spider(scrapy.Spider):
    """
    Spider mejorado para la sección Sudamérica de Europa Press.
    Incluye validación completa de campos requeridos.
    """
    
    name = 'europapress_sudamerica_v2'
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
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        # Desactivar pipelines problemáticos temporalmente
        'ITEM_PIPELINES': {}
    }
    
    def parse(self, response: Response) -> Iterator[scrapy.Request]:
        """Parsear la página principal y extraer enlaces a artículos."""
        self.logger.info(f"Parseando página de sección: {response.url}")
        
        # Verificar si estamos en una página de captcha
        if 'captcha' in response.url.lower():
            self.logger.warning(f"Bloqueado por captcha: {response.url}")
            return
        
        # Extraer enlaces de artículos
        article_links = []
        
        # Buscar artículos en la estructura de Europa Press
        articles = response.css('article.ep-articleStandard')
        
        for article in articles:
            link = article.css('h2.articulo-titulo a::attr(href)').get()
            if link:
                article_links.append(link)
        
        # También buscar enlaces directos
        additional_links = response.css('a[href*="/internacional/noticia-"]::attr(href)').getall()
        article_links.extend(additional_links)
        
        # Eliminar duplicados
        article_links = list(set(article_links))
        
        self.logger.info(f"Encontrados {len(article_links)} artículos únicos")
        
        # Procesar enlaces
        count = 0
        for link in article_links:
            if self._is_valid_article_url(link) and count < 30:
                count += 1
                yield response.follow(link, self.parse_article)
    
    def parse_article(self, response: Response) -> Optional[ArticuloInItem]:
        """Parsear un artículo individual con validación completa."""
        self.logger.debug(f"Parseando artículo: {response.url}")
        
        # Verificar captcha
        if 'captcha' in response.url.lower():
            self.logger.warning(f"Artículo bloqueado por captcha: {response.url}")
            return None
        
        # Crear item
        item = ArticuloInItem()
        
        try:
            # === CAMPOS OBLIGATORIOS ===
            
            # URL y fuente
            item['url'] = response.url
            item['fuente'] = self.name
            
            # Título (requerido)
            title = response.css('h1::text').get()
            if not title:
                # Intentar selector alternativo
                title = response.css('h1.titulo-noticia::text, h1.article-title::text').get()
            
            if not title:
                self.logger.warning(f"No se encontró título en {response.url}")
                return None
            
            item['titular'] = title.strip()
            
            # Contenido (requerido)
            paragraphs = response.css('div.texto_noticia p::text').getall()
            if not paragraphs:
                # Intentar selectores alternativos
                paragraphs = response.css('div.article-content p::text, div[itemprop="articleBody"] p::text').getall()
            
            if not paragraphs:
                # Último intento: buscar cualquier div con clase que contenga "text" o "content"
                paragraphs = response.css('div[class*="text"] p::text, div[class*="content"] p::text').getall()
            
            if paragraphs:
                content = '\n\n'.join(p.strip() for p in paragraphs if p.strip())
                if len(content) < 50:  # Contenido muy corto probablemente es error
                    self.logger.warning(f"Contenido muy corto en {response.url}")
                    return None
                item['contenido_texto'] = content
            else:
                self.logger.warning(f"No se encontró contenido en {response.url}")
                return None
            
            # HTML completo
            item['contenido_html'] = response.text
            
            # Información del medio (requerida)
            item['medio'] = self.medio_nombre
            item['pais_publicacion'] = self.pais
            item['tipo_medio'] = self.tipo_medio
            
            # Fecha de publicación (requerida)
            fecha = self._extract_date(response)
            if not fecha:
                # Si no encontramos fecha, usar la actual
                fecha = datetime.utcnow()
                self.logger.warning(f"No se encontró fecha, usando fecha actual para {response.url}")
            
            item['fecha_publicacion'] = fecha
            
            # === CAMPOS OPCIONALES ===
            
            # URL principal del medio
            item['medio_url_principal'] = f"https://{self.allowed_domains[0]}"
            
            # Autor
            author = response.css('span.autor::text, div.author::text').get()
            if not author:
                author = response.css('meta[name="author"]::attr(content)').get()
            item['autor'] = author.strip() if author else 'Europa Press'
            
            # Idioma
            item['idioma'] = 'es'
            
            # Sección
            item['seccion'] = self.target_section
            
            # Etiquetas
            keywords = response.css('meta[name="keywords"]::attr(content)').get()
            if keywords:
                item['etiquetas_fuente'] = [tag.strip() for tag in keywords.split(',') if tag.strip()]
            else:
                # Intentar extraer tags del artículo
                tags = response.css('a.tag::text, a.etiqueta::text, div.tags a::text').getall()
                item['etiquetas_fuente'] = [tag.strip() for tag in tags if tag.strip()]
            
            # Clasificación
            item['es_opinion'] = self._is_opinion(response)
            item['es_oficial'] = False
            
            # Timestamps
            item['fecha_recopilacion'] = datetime.utcnow()
            
            # Estado inicial
            item['estado_procesamiento'] = 'pendiente'
            
            # Metadata adicional
            metadata = {
                'spider_type': 'scraping',
                'spider_version': 'v2',
                'section_filter': 'strict',
                'url_original': response.url
            }
            
            # Imagen principal si existe
            og_image = response.css('meta[property="og:image"]::attr(content)').get()
            if og_image:
                metadata['imagen_principal'] = og_image
            
            # Cantidad de párrafos
            metadata['num_parrafos'] = len(paragraphs)
            
            item['metadata'] = metadata
            
            # Validar antes de retornar
            if self._validate_item(item):
                self.logger.info(f"Artículo válido extraído: {item['titular'][:50]}...")
                return item
            else:
                self.logger.warning(f"Artículo no pasó validación: {response.url}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error procesando artículo {response.url}: {str(e)}")
            return None
    
    def _extract_date(self, response: Response) -> Optional[datetime]:
        """Extraer fecha de publicación con múltiples estrategias."""
        # Estrategia 1: time tag con datetime
        date_str = response.css('time[datetime]::attr(datetime)').get()
        if date_str:
            try:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                pass
        
        # Estrategia 2: meta property article:published_time
        date_str = response.css('meta[property="article:published_time"]::attr(content)').get()
        if date_str:
            try:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                pass
        
        # Estrategia 3: buscar en el texto
        date_text = response.css('span.fecha::text, div.fecha::text, p.fecha::text').get()
        if date_text:
            # Aquí se podría implementar un parser de fecha en español
            # Por ahora retornamos None
            pass
        
        return None
    
    def _is_valid_article_url(self, url: str) -> bool:
        """Verificar si la URL es válida para procesar."""
        if not url:
            return False
        
        # Debe ser de internacional
        if not self.section_pattern.search(url):
            return False
        
        # Excluir tipos no deseados
        exclude_patterns = [
            '/archivo/', '/video/', '/galeria/', '/tags/',
            '/especiales/', '/temas/', '/podcast/'
        ]
        for pattern in exclude_patterns:
            if pattern in url.lower():
                return False
        
        return True
    
    def _is_opinion(self, response: Response) -> bool:
        """Detectar si es artículo de opinión."""
        # Por URL
        opinion_patterns = ['/opinion/', '/columna/', '/tribuna/', '/editorial/']
        url_lower = response.url.lower()
        if any(pattern in url_lower for pattern in opinion_patterns):
            return True
        
        # Por sección
        section = response.css('span.seccion::text, div.section::text').get()
        if section and 'opinión' in section.lower():
            return True
        
        return False
    
    def _validate_item(self, item: ArticuloInItem) -> bool:
        """Validar que el item tenga todos los campos requeridos."""
        required_fields = ['titular', 'medio', 'pais_publicacion', 'tipo_medio', 
                          'fecha_publicacion', 'contenido_texto']
        
        for field in required_fields:
            if not item.get(field):
                self.logger.warning(f"Campo requerido faltante: {field}")
                return False
        
        # Validaciones adicionales
        if len(item.get('titular', '')) < 10:
            self.logger.warning("Título demasiado corto")
            return False
        
        if len(item.get('contenido_texto', '')) < 100:
            self.logger.warning("Contenido demasiado corto")
            return False
        
        return True