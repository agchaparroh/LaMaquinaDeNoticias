# -*- coding: utf-8 -*-
import scrapy
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose
from w3lib.html import remove_tags

# Importar desde la estructura correcta del proyecto
from scraper_core.items import ArticuloInItem
from scraper_core.itemloaders import ArticuloInItemLoader

class ElpaisLatinoamericaSpider(scrapy.Spider):
    """
    Spider para extraer noticias de la sección Latinoamérica del diario El País (elpais.com).
    Se encarga de navegar la sección, seguir los enlaces a los artículos individuales,
    extraer la información relevante y manejar la paginación.
    """
    name = 'elpais_latinoamerica'
    allowed_domains = ['elpais.com']
    start_urls = ['https://elpais.com/noticias/latinoamerica/']

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (compatible; LaMaquinaDeNoticiasBot/1.0; +http://www.lamaquinadenoticias.example.com/bot-info.html)', # Actualizar example.com con la URL real de info del bot
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        # 'AUTOTHROTTLE_ENABLED': True, # Considerar activar para ajuste dinámico
        # 'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        # 'LOG_LEVEL': 'INFO', # Ajustar según necesidad de depuración
    }

    def parse(self, response):
        """
        Procesa la página de sección (y páginas de paginación).
        Extrae enlaces a artículos individuales y los envía a `parse_article`.
        Maneja la navegación a la página siguiente.
        """
        self.logger.info(f'Procesando página de sección: {response.url}')

        # Selector principal para los contenedores de cada artículo en la página de sección.
        article_containers = response.css('article.c-d')

        if not article_containers:
            self.logger.warning(f"No se encontraron contenedores de artículos en {response.url} usando 'article.c-d'")
            return

        self.logger.info(f'Encontrados {len(article_containers)} posibles artículos en {response.url}')

        for article_selector in article_containers:
            # Selector para la URL relativa del artículo dentro de su contenedor.
            article_url_relative = article_selector.css('h2.c_t a::attr(href)').get()
            
            if article_url_relative:
                article_url_absolute = response.urljoin(article_url_relative)
                
                meta_data = {
                    'fuente': 'El País',
                    'seccion': 'Latinoamérica',
                }
                yield response.follow(article_url_absolute, callback=self.parse_article, meta=meta_data)
            else:
                self.logger.warning(f"No se encontró URL de artículo en un contenedor dentro de {response.url}: {article_selector.get()[:200]}...")

        # Paginación
        # Selector para el enlace a la página siguiente (paginación).
        next_page_relative = response.css('div.w_pag a.w_pag_l-s::attr(href)').get()
        if next_page_relative:
            next_page_absolute = response.urljoin(next_page_relative)
            self.logger.info(f'Siguiendo a la página siguiente: {next_page_absolute}')
            yield response.follow(next_page_absolute, callback=self.parse)

    def parse_article(self, response):
        """
        Procesa la página de un artículo individual para extraer datos detallados
        utilizando ItemLoader.
        """
        self.logger.info(f'Parseando artículo: {response.url}')

        loader = ArticuloInItemLoader(item=ArticuloInItem(), response=response)

        # Titular: usar selectores múltiples, el ItemLoader manejará la limpieza
        loader.add_css('titular', 'h1.a_t::text')
        loader.add_xpath('titular', '//h1[contains(@class, "a_t")]/text()')
        loader.add_css('titular', 'h1[itemprop="headline"]::text')

        # Contenido_texto: el ItemLoader unirá y limpiará automáticamente
        loader.add_css('contenido_texto', 'div.a_c.clearfix p')
        loader.add_xpath('contenido_texto', '//div[contains(@class, "a_c")]//p')
        loader.add_css('contenido_texto', 'div[itemprop="articleBody"] p')

        # Fecha_publicacion: el ItemLoader parseara las fechas automáticamente
        loader.add_css('fecha_publicacion', 'div.a_md_f a time::attr(datetime)')
        loader.add_css('fecha_publicacion', 'span.a_ti._df.a_ti_df time::attr(datetime)')
        loader.add_xpath('fecha_publicacion', '//meta[@property="article:published_time"]/@content')
        loader.add_xpath('fecha_publicacion', '//meta[@name="date"]/@content')
        loader.add_css('fecha_publicacion', 'time[itemprop="datePublished"]::attr(datetime)')

        # Autor: el ItemLoader limpiará automáticamente
        loader.add_css('autor', 'div.a_a_txt span.a_a_n a::text')
        loader.add_css('autor', 'div.a_a_txt span.a_a_n::text')
        loader.add_xpath('autor', '//meta[@name="author"]/@content')
        loader.add_css('autor', 'span[itemprop="name"]::text')

        loader.add_value('url', response.url)
        loader.add_value('fuente', response.meta.get('fuente', self.name))
        loader.add_value('seccion', response.meta.get('seccion', 'Desconocida'))

        item = loader.load_item()

        if self.validate_item(item):
            self.logger.info(f"Artículo válido extraído de {response.url}")
            yield item
        else:
            self.logger.debug(f"Item no superó la validación para {response.url}. Item: {dict(item)}")

    def validate_item(self, item):
        """
        Valida que el ítem extraído contenga los campos obligatorios 
        (titular, contenido_texto, fecha_publicacion, autor, url)
        y que estos cumplan con criterios mínimos de calidad (no vacíos, longitud mínima).
        """
        obligatorios = ['titular', 'contenido_texto', 'fecha_publicacion', 'autor', 'url']
        for campo in obligatorios:
            valor = item.get(campo)
            if not valor:
                self.logger.warning(f"Item inválido: Falta campo obligatorio '{campo}'. URL: {item.get('url')}")
                return False
            if isinstance(valor, str) and not valor.strip():
                 self.logger.warning(f"Item inválido: Campo obligatorio '{campo}' está vacío o solo espacios. URL: {item.get('url')}")
                 return False
        
        if len(item.get('titular','')) < 5:
            self.logger.warning(f"Item inválido: Titular '{item.get('titular','')}' demasiado corto. URL: {item.get('url')}")
            return False
        if len(item.get('contenido_texto','')) < 50:
            self.logger.warning(f"Item inválido: Contenido_texto demasiado corto ({len(item.get('contenido_texto',''))} caracteres). URL: {item.get('url')}")
            return False
            
        return True
