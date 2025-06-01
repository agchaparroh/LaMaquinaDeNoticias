# -*- coding: utf-8 -*-
import scrapy
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose
from w3lib.html import remove_tags

# Asumiendo que items.py está en maquina_spiders_project, como indica la plantilla base
# y la memoria del proyecto.
from maquina_spiders_project.items import ArticuloInItem

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

        loader = ItemLoader(item=ArticuloInItem(), response=response)

        # Procesadores comunes
        # Ayudante para limpiar HTML, espacios y tomar el primer elemento no vacío.
        def limpiar_texto_y_tomar_primero(value):
            if isinstance(value, list):
                value = ' '.join(value) # Unir si es una lista de segmentos de texto
            cleaned_value = remove_tags(str(value)).strip()
            return cleaned_value if cleaned_value else None

        # Ayudante para limpiar párrafos de HTML, espacios, y unirlos con doble salto de línea.
        def limpiar_parrafos_y_unir(values):
            cleaned_paragraphs = [remove_tags(p).strip() for p in values if remove_tags(p).strip()]
            return '\n\n'.join(cleaned_paragraphs) if cleaned_paragraphs else None

        # Titular
        # Titular: Selector principal 'h1.a_t::text'
        loader.add_css('titular', 'h1.a_t::text', MapCompose(limpiar_texto_y_tomar_primero), TakeFirst())
        loader.add_xpath('titular', '//h1[contains(@class, "a_t")]/text()', MapCompose(limpiar_texto_y_tomar_primero), TakeFirst()) # Fallback
        loader.add_css('titular', 'h1[itemprop="headline"]::text', MapCompose(limpiar_texto_y_tomar_primero), TakeFirst()) # Otro fallback

        # Contenido_texto
        # Contenido_texto: Selector principal 'div.a_c.clearfix p' para los párrafos del cuerpo.
        loader.add_css('contenido_texto', 'div.a_c.clearfix p', limpiar_parrafos_y_unir)
        loader.add_xpath('contenido_texto', '//div[contains(@class, "a_c")]//p', limpiar_parrafos_y_unir) # Fallback
        loader.add_css('contenido_texto', 'div[itemprop="articleBody"] p', limpiar_parrafos_y_unir) # Otro fallback

        # Fecha_publicacion
        # Fecha_publicacion: Selector principal 'div.a_md_f a time::attr(datetime)' para el timestamp.
        loader.add_css('fecha_publicacion', 'div.a_md_f a time::attr(datetime)', MapCompose(str.strip, lambda x: x if x else None), TakeFirst())
        loader.add_css('fecha_publicacion', 'span.a_ti._df.a_ti_df time::attr(datetime)', MapCompose(str.strip, lambda x: x if x else None), TakeFirst()) 
        loader.add_xpath('fecha_publicacion', '//meta[@property="article:published_time"]/@content', MapCompose(str.strip, lambda x: x if x else None), TakeFirst())
        loader.add_xpath('fecha_publicacion', '//meta[@name="date"]/@content', MapCompose(str.strip, lambda x: x if x else None), TakeFirst())
        loader.add_css('fecha_publicacion', 'time[itemprop="datePublished"]::attr(datetime)', MapCompose(str.strip, lambda x: x if x else None), TakeFirst())

        # Autor
        # Autor: Selector principal 'div.a_a_txt span.a_a_n a::text' para el nombre del autor.
        loader.add_css('autor', 'div.a_a_txt span.a_a_n a::text', MapCompose(limpiar_texto_y_tomar_primero), TakeFirst())
        loader.add_css('autor', 'div.a_a_txt span.a_a_n::text', MapCompose(limpiar_texto_y_tomar_primero), TakeFirst()) # Si no es un enlace
        loader.add_xpath('autor', '//meta[@name="author"]/@content', MapCompose(limpiar_texto_y_tomar_primero), TakeFirst())
        loader.add_css('autor', 'span[itemprop="name"]::text', MapCompose(limpiar_texto_y_tomar_primero), TakeFirst()) # Microdatos

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
