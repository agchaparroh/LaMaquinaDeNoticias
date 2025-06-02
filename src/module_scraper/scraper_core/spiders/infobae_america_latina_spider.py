# -*- coding: utf-8 -*-
"""
Spider para Infobae América Latina (infobae_america_latina_spider)

Notas Esenciales:
- URL Principal Analizada: https://www.infobae.com/america/america-latina/

- Limitaciones y Comportamiento:
  - Paginación: La paginación de la sección ("MÁS NOTAS") parece ser dinámica (scroll infinito o botón que carga más contenido vía JS).
    Este spider solo procesa los artículos encontrados en la carga inicial de la página de sección.
    Para una cobertura completa de artículos más antiguos, se necesitaría investigar las llamadas XHR subyacentes o integrar
    herramientas como scrapy-playwright o scrapy-splash.
  - Contenido JavaScript: Se asume que el contenido principal de los artículos (titular, cuerpo, fecha, autor, etc.)
    no depende críticamente de la ejecución de JavaScript para renderizarse, más allá de la paginación de la sección.

- Dependencias Clave:
  - `dateparser`: Esta librería se utiliza para un manejo flexible de formatos de fecha y su normalización a ISO 8601.
    Asegúrese de que `dateparser` esté instalado en el entorno de ejecución del spider (ej. `pip install dateparser`).

- Suposiciones de Entorno:
  - Importación de Item: Se asume que el entorno de ejecución del spider está configurado para que la importación
    `from maquina_spiders_project.items import ArticuloInItem` funcione correctamente (es decir, que el directorio `src`
    que contiene `maquina_spiders_project` sea reconocible por Python como un paquete, usualmente estando en PYTHONPATH
    o ejecutando el spider desde un nivel superior que lo incluya).
"""
import scrapy
from urllib.parse import urljoin
from datetime import datetime

from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose, Join
from w3lib.html import remove_tags

# Importar desde la estructura correcta del proyecto
from scraper_core.items import ArticuloInItem
from scraper_core.itemloaders import ArticuloInItemLoader

class InfobaeAmericaLatinaSpider(scrapy.Spider):
    name = 'infobae_america_latina_spider'
    allowed_domains = ['infobae.com']
    start_urls = ['https://www.infobae.com/america/america-latina/']

    custom_settings = {
        'USER_AGENT': 'LaMaquinaDeNoticias_Spider/1.0 (+http://your-project-contact-url.com/spider-info)', # Actualizar con URL real
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'LOG_LEVEL': 'INFO',
        # 'ITEM_PIPELINES': { # Descomentar y configurar si tienes pipelines en el proyecto principal
        #    'maquina_spiders_project.pipelines.AlgunaPipeline': 300,
        # },
    }

    def parse(self, response):
        self.logger.info(f"Procesando página de sección: {response.url}")
        
        article_links = response.css('a.story-card-wrapper::attr(href), a.card-container::attr(href), a.deck-container::attr(href)').getall()
        
        if not article_links:
            self.logger.warning(f"No se encontraron enlaces a artículos en {response.url}")
            return

        self.logger.info(f"Encontrados {len(article_links)} enlaces a artículos en {response.url}")
        for link in article_links:
            full_url = response.urljoin(link)
            yield scrapy.Request(full_url, callback=self.parse_article)

        # Paginación (simplificada - no implementada para scroll infinito de Infobae)
        # next_page_button = response.css('button.infinite-scroll-button') # Ejemplo
        # if next_page_button:
        #     self.logger.info("Botón 'MÁS NOTAS' encontrado, pero la paginación dinámica no está implementada en esta versión.")

    def parse_article(self, response):
        self.logger.debug(f"Procesando artículo: {response.url}")
        
        loader = ArticuloInItemLoader(item=ArticuloInItem(), response=response)

        # Simplificar usando el ItemLoader centralizado
        loader.add_css('titular', 'h1.article-headline::text')
        loader.add_xpath('titular', '//meta[@property="og:title"]/@content')

        loader.add_css('contenido_texto', 'div.article-body p, div.article-body div[data-testid="richtext-paragraph"]')
        
        loader.add_css('fecha_publicacion', 'time.article-date::attr(datetime)')
        loader.add_xpath('fecha_publicacion', '//meta[@property="article:published_time"]/@content')

        loader.add_xpath('autor', '//meta[@property="article:author"]/@content')
        loader.add_xpath('autor', '//meta[@name="author"]/@content')

        loader.add_value('url', response.url)
        loader.add_value('fuente', self.name)
        loader.add_xpath('seccion', '//meta[@property="article:section"]/@content')

        item = loader.load_item()

        if self.validate_item(item):
            self.logger.info(f"Artículo válido extraído de {response.url}")
            yield item
        else:
            missing_fields = [field for field in ['titular', 'contenido_texto', 'fecha_publicacion', 'autor', 'url'] if not item.get(field) or not str(item.get(field, '')).strip()]
            self.logger.warning(f"Item no válido o incompleto en {response.url}. Campos faltantes/inválidos: {missing_fields}. Titular: '{item.get('titular', '')[:50]}...', Contenido: {len(item.get('contenido_texto', ''))} chars, Fecha: {item.get('fecha_publicacion')}, Autor: {item.get('autor')}")

    def validate_item(self, item):
        required_fields = ['titular', 'contenido_texto', 'fecha_publicacion', 'url', 'autor']
        for field in required_fields:
            if not item.get(field) or not str(item.get(field, '')).strip():
                self.logger.debug(f"Validación fallida: campo '{field}' está vacío o ausente.")
                return False

        if len(item.get('titular','')) < 10:
             self.logger.debug(f"Validación fallida: titular demasiado corto - '{item.get('titular')}'")
             return False
        if len(item.get('contenido_texto','')) < 50:
             self.logger.debug(f"Validación fallida: contenido_texto demasiado corto - {len(item.get('contenido_texto',''))} chars")
             return False
            
        return True
