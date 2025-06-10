# -*- coding: utf-8 -*-
import scrapy
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose, Join
from w3lib.html import remove_tags
# Importar el Item desde la estructura correcta del proyecto
from scraper_core.items import ArticuloInItem
from scraper_core.itemloaders import ArticuloInItemLoader, parse_and_format_date_processor

class ElnacionalLatinoamericaSpider(scrapy.Spider):
    """
    Spider para extraer noticias de la sección Latinoamérica del diario El Nacional (elnacional.com).
    Navega la sección, sigue enlaces a artículos, extrae datos y maneja paginación.
    """
    name = 'elnacional_latinoamerica'
    allowed_domains = ['elnacional.com']
    start_urls = ['https://www.elnacional.com/latinoamerica/']

    custom_settings = {
        'USER_AGENT': 'LaMaquinaDeNoticiasBot/1.0 (+http://www.lamaquinadenoticias.example.com/bot-info.html)', # IMPORTANTE: Actualizar example.com con la URL real de información de tu bot
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        # 'LOG_LEVEL': 'INFO', # Ajustar según necesidad para depuración
    }

    def parse(self, response):
        """
        Procesa la página de sección y las páginas de paginación.
        Extrae enlaces a artículos individuales y los envía a `parse_article`.
        Maneja la navegación a la página siguiente.
        """
        self.logger.info(f'Procesando página de sección: {response.url}')

        # Selector para los contenedores de cada artículo en la página de sección.
        article_containers = response.css('article.c-d')

        if not article_containers:
            self.logger.warning(f"No se encontraron contenedores de artículos en {response.url} usando 'article.c-d'")
        else:
            self.logger.info(f'Encontrados {len(article_containers)} posibles artículos en {response.url}')

        for article_selector in article_containers:
            article_url_relative = article_selector.css('h2.c_t a::attr(href)').get()
            
            if article_url_relative:
                article_url_absolute = response.urljoin(article_url_relative)
                self.logger.debug(f'Encontrado enlace a artículo: {article_url_absolute}')
                
                meta_data = {
                    'fuente': 'El Nacional',
                    'seccion': 'Latinoamérica',
                }
                yield response.follow(article_url_absolute, callback=self.parse_article, meta=meta_data)
            else:
                self.logger.debug(f"No se encontró URL de artículo en un contenedor en {response.url} usando 'h2.c_t a::attr(href)'")

        # Paginación
        next_page_selectors = [
            'a.next.page-numbers::attr(href)',
            'a.nextpostslink::attr(href)',
            'li.pagination-next a::attr(href)',
            '//a[contains(text(), "Siguiente") or contains(translate(text(), "SIGUIENTE", "siguiente"), "siguiente")]/@href',
            '//a[contains(@class, "next") and contains(@class, "page") and not(contains(@class, "disabled"))]/@href'
        ]
        next_page_url = None
        for selector in next_page_selectors:
            if selector.startswith("//"):
                 next_page_url = response.xpath(selector).get()
            else:
                 next_page_url = response.css(selector).get()
            if next_page_url:
                break
        
        if next_page_url:
            next_page_absolute_url = response.urljoin(next_page_url)
            self.logger.info(f'Siguiendo a la página siguiente: {next_page_absolute_url}')
            yield response.follow(next_page_absolute_url, callback=self.parse)
        else:
            self.logger.info(f'No se encontró enlace a la página siguiente en {response.url}')

    def parse_article(self, response):
        """
        Procesa la página de un artículo individual y extrae los datos usando ItemLoader.
        """
        self.logger.info(f'Parseando artículo: {response.url}')

        loader = ArticuloInItemLoader(item=ArticuloInItem(), response=response)

        loader.default_input_processor = MapCompose(str.strip) # Limpieza básica para todos los campos
        loader.default_output_processor = TakeFirst() # Tomar el primer valor no nulo

        loader.add_css('titular', 
                       ['h1.title::text', 
                        'h1.s-title::text', 
                        'h1.tdb-title-text::text',
                        'meta[property="og:title"]::attr(content)',
                        'h1::text'])
        
        loader.add_css('contenido_texto', 
                       ['div.s-text p', 
                        'div.tdb-block-inner.td-fix-index p',
                        'div.td-post-content p',
                        'article.post-content p',
                        'div.entry-content p',
                        'div.content-modules p'], # Añadido por si acaso
                       MapCompose(remove_tags, str.strip), Join('\n'))

        # Para la fecha, usar el procesador centralizado del ItemLoader
        loader.add_css('fecha_publicacion', 
                       ['meta[property="article:published_time"]::attr(content)',
                        'time.s-post-time::attr(datetime)',
                        'time.entry-date::attr(datetime)',
                        'span.date::text',
                        'span.s-post-date::text',
                        'div.date-simple::text']) # El procesador ya está definido en ArticuloInItemLoader

        loader.add_css('autor', 
                       ['meta[name="author"]::attr(content)',
                        'span.author-name a::text', 
                        'div.td-post-author-name a::text',
                        'a.author-url::text',
                        'span.autor_nota a::text',
                        'div.author-box span.name a::text',
                        'p.author a::text',
                        'div.author_name::text'])
        
        loader.add_value('url', response.url)
        loader.add_value('fuente', response.meta.get('fuente', 'El Nacional'))
        loader.add_value('seccion', response.meta.get('seccion', 'Latinoamérica'))

        item = loader.load_item()

        if self.validate_item(item):
            self.logger.info(f"Artículo válido extraído de {response.url}")
            yield item
        else:
            self.logger.warning(f"Item no válido o incompleto en {response.url}. Titular: '{item.get('titular')}', Contenido: {len(item.get('contenido_texto', ''))} chars, Fecha: '{item.get('fecha_publicacion')}'")

    def validate_item(self, item):
        """
        Valida que los campos obligatorios del item estén presentes y cumplan criterios mínimos.
        Según prompt_generador_spider.md.
        Nota: items_template.py marca 'autor' como OBLIGATORIO, pero la función de validación
        del prompt original no lo incluye. Se sigue la validación del prompt.
        """
        titular_ok = item.get('titular') and len(item['titular']) > 5
        contenido_ok = item.get('contenido_texto') and len(item['contenido_texto']) > 50
        url_ok = item.get('url')
        fecha_ok = item.get('fecha_publicacion')
        
        # Logging de depuración para cada campo que falla la validación
        if not titular_ok:
            self.logger.debug(f"Validación fallida (titular): '{item.get('titular')}' para {item.get('url')}")
        if not contenido_ok:
            self.logger.debug(f"Validación fallida (contenido_texto): longitud {len(item.get('contenido_texto', ''))} para {item.get('url')}")
        if not url_ok:
             self.logger.debug(f"Validación fallida (url): URL falta para un item.")
        if not fecha_ok:
            self.logger.debug(f"Validación fallida (fecha_publicacion): '{item.get('fecha_publicacion')}' para {item.get('url')}")
            
        return titular_ok and contenido_ok and url_ok and fecha_ok
