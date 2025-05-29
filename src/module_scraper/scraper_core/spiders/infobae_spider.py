# -*- coding: utf-8 -*-
import logging
from typing import Iterator, Dict, Any

from scrapy.http import Response

from scraper_core.items import ArticuloInItem
from scraper_core.spiders.base.base_article import BaseArticleSpider

logger = logging.getLogger(__name__)


class InfobaeSpider(BaseArticleSpider):
    name = 'infobae'
    allowed_domains = ['infobae.com']
    start_urls = [
        'https://www.infobae.com/america/america-latina/2025/05/27/fiscales-brasilenos-demandaron-a-la-china-byd-por-condiciones-laborales-esclavistas/',
        'https://www.infobae.com/america/america-latina/2025/05/27/varios-sectores-de-bolivia-anuncian-marchas-contra-el-alza-de-precios-y-la-escasez-de-combustible/',
        'https://www.infobae.com/america/america-latina/2025/05/27/polemica-en-chile-por-venta-de-productos-con-imagenes-de-augusto-pinochet-en-la-escuela-militar/'
    ]

    # custom_settings = {
    # 'DOWNLOAD_DELAY': 2,
    # 'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
    # }

    def parse(self, response: Response) -> Iterator[Dict[str, Any]]:
        """ 
        Método principal para parsear las respuestas de las URLs de Infobae.
        Debe extraer los datos del artículo y devolver un item o un diccionario.
        """
        self.logger.info(f"Parseando URL: {response.url}")

        # Usar extractores específicos de Infobae con fallback a la clase base
        title = self.extract_article_title(response)
        content = self.extract_article_content(response)
        publication_date = self.extract_publication_date(response)
        author = self.extract_author(response)
        metadata = self.extract_article_metadata(response)

        self.logger.debug(f"Título extraído: {title}")
        self.logger.debug(f"Autor extraído: {author}")
        self.logger.debug(f"Fecha extraída: {publication_date}")
        self.logger.debug(f"Contenido extraído: {len(content) if content else 0} caracteres")

        # Crear y llenar el Item de Scrapy
        item = ArticuloInItem()

        item['url'] = response.url
        item['fuente'] = self.name
        item['medio'] = 'Infobae'  # Nombre oficial del medio
        item['pais_publicacion'] = self._detect_country(response.url)
        item['tipo_medio'] = 'diario'
        item['titular'] = title
        item['fecha_publicacion'] = publication_date
        item['autor'] = author
        item['contenido_texto'] = content
        item['contenido_html'] = response.text  # HTML original completo
        item['idioma'] = 'es'
        item['seccion'] = self._extract_section(response)
        item['etiquetas_fuente'] = metadata.get('keywords', [])
        item['es_opinion'] = self._is_opinion(response)
        item['es_oficial'] = False  # Infobae no es medio oficial
        
        # Metadata adicional
        item['metadata'] = {
            'description': metadata.get('description'),
            'image': metadata.get('image'),
            'language': metadata.get('language', 'es'),
        }
        
        # Validación antes de yield
        if self.validate_article_data(dict(item)):
            self.successful_urls.append(response.url)
            yield item
        else:
            self.logger.warning(f"Artículo inválido en {response.url}, descartando")

    def extract_article_title(self, response: Response) -> Optional[str]:
        """
        Extrae el título con selectores específicos de Infobae.
        """
        # Selectores específicos de Infobae
        infobae_selectors = [
            'h1.article-headline::text',
            'h1.article-title::text',
            'h1.d23-article-title::text',
            'h1[class*="article-headline"]::text',
            '.article-header h1::text',
            'h1.entry-title::text',
        ]
        
        for selector in infobae_selectors:
            title = response.css(selector).get()
            if title and title.strip():
                return title.strip()
        
        # Si no funciona, usar el método de la clase base
        return super().extract_article_title(response)

    def extract_article_content(self, response: Response) -> Optional[str]:
        """
        Extrae el contenido con selectores específicos de Infobae.
        """
        # Contenedores específicos de Infobae
        content_containers = [
            'div.article-body',
            'div.article-content',
            'div.d23-article-content',
            'div[class*="article-body"]',
            'div.entry-content',
            'section.article-body',
        ]
        
        for container in content_containers:
            # Intentar obtener párrafos
            paragraphs = response.css(f'{container} p::text').getall()
            if paragraphs:
                content = ' '.join(p.strip() for p in paragraphs if p.strip())
                if len(content) > 200:
                    return content
            
            # Intentar obtener todo el texto del contenedor
            all_text = response.css(f'{container} ::text').getall()
            if all_text:
                # Filtrar contenido no deseado
                filtered_text = []
                for text in all_text:
                    text = text.strip()
                    # Saltar elementos de script, publicidad, etc.
                    if text and len(text) > 2 and not any(skip in text.lower() for skip in ['advertisement', 'publicidad', 'suscribite']):
                        filtered_text.append(text)
                
                content = ' '.join(filtered_text)
                if len(content) > 200:
                    return content
        
        # Fallback a la clase base
        return super().extract_article_content(response)

    def extract_publication_date(self, response: Response) -> Optional[datetime]:
        """
        Extrae la fecha con selectores específicos de Infobae.
        """
        from .base.utils import parse_date_string
        
        # Selectores específicos de Infobae para fecha
        date_selectors = [
            'time[datetime]::attr(datetime)',
            'time.date::attr(datetime)',
            'span.article-date::text',
            'span.d23-article-date::text',
            'div.article-date::text',
            '.article-header time::text',
            '.byline time::text',
            'meta[property="article:published_time"]::attr(content)',
        ]
        
        for selector in date_selectors:
            date_str = response.css(selector).get()
            if date_str:
                parsed_date = parse_date_string(date_str)
                if parsed_date:
                    return parsed_date
        
        # Fallback a la clase base
        return super().extract_publication_date(response)

    def extract_author(self, response: Response) -> Optional[str]:
        """
        Extrae el autor con selectores específicos de Infobae.
        """
        # Selectores específicos de Infobae
        author_selectors = [
            'span.author-name::text',
            'span.article-author::text',
            'div.author a::text',
            '.byline a::text',
            '.byline-author::text',
            'p.author::text',
            'div[class*="author-name"]::text',
        ]
        
        for selector in author_selectors:
            authors = response.css(selector).getall()
            if authors:
                # Limpiar y unir autores
                clean_authors = []
                for author in authors:
                    author = author.strip()
                    if author and len(author) > 2 and author not in ['Por', 'By', '|', '-']:
                        # Limpiar prefijos comunes
                        for prefix in ['Por ', 'By ']:
                            if author.startswith(prefix):
                                author = author[len(prefix):]
                        clean_authors.append(author.strip())
                
                if clean_authors:
                    return ', '.join(clean_authors)
        
        # Fallback a la clase base
        return super().extract_author(response)

    def _detect_country(self, url: str) -> str:
        """
        Detecta el país basándose en la URL de Infobae.
        """
        if '/america/colombia/' in url:
            return 'Colombia'
        elif '/america/mexico/' in url:
            return 'México'
        elif '/america/peru/' in url:
            return 'Perú'
        elif '/america/venezuela/' in url:
            return 'Venezuela'
        elif '/america/eeuu/' in url or '/america/usa/' in url:
            return 'Estados Unidos'
        elif '/america/america-latina/' in url:
            return 'América Latina'  # Región, no país específico
        elif '/espana/' in url:
            return 'España'
        else:
            return 'Argentina'  # Por defecto

    def _extract_section(self, response: Response) -> Optional[str]:
        """
        Extrae la sección del artículo.
        """
        # Intentar obtener de la URL
        url_parts = response.url.split('/')
        if len(url_parts) > 3:
            # Típicamente: https://www.infobae.com/seccion/...
            section = url_parts[3]
            if section and section not in ['www.infobae.com', 'infobae.com']:
                return section.replace('-', ' ').title()
        
        # Intentar obtener de breadcrumb
        breadcrumb = response.css('nav.breadcrumb a::text').getall()
        if len(breadcrumb) > 1:
            return breadcrumb[1].strip()
        
        # Intentar obtener de meta tags
        section = response.css('meta[property="article:section"]::attr(content)').get()
        if section:
            return section.strip()
        
        return None

    def _is_opinion(self, response: Response) -> bool:
        """
        Detecta si es un artículo de opinión.
        """
        # Revisar URL
        if '/opinion/' in response.url or '/columnistas/' in response.url:
            return True
        
        # Revisar sección
        section = self._extract_section(response)
        if section and 'opinión' in section.lower():
            return True
        
        # Revisar clases CSS
        opinion_indicators = response.css('.opinion-article, .column-article, .editorial').get()
        if opinion_indicators:
            return True
        
        return False
