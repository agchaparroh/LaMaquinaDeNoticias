# -*- coding: utf-8 -*-
"""
Spider para extraer noticias de la sección Sudamérica de Europa Press.

URL_SECCION_PRINCIPAL analizada: https://www.europapress.es/internacional/sudamerica-00407/

Hallazgos críticos del análisis inicial:
- El contenido principal y los enlaces parecen estar disponibles directamente en el HTML.
- La paginación se realiza a través de enlaces estándar.
- Las fechas de publicación están disponibles en metadatos y en el cuerpo del artículo.

Limitaciones principales del spider:
- No maneja contenido cargado dinámicamente por JavaScript si lo hubiera en otras secciones no analizadas.
- Asume que la estructura HTML de los artículos y la sección se mantiene consistente.

Dependencias externas clave no estándar:
- Requiere 'dateutil' para un parseo de fechas robusto. Asegúrate de instalarlo (`pip install python-dateutil`).

Suposiciones críticas realizadas durante el diseño:
- Se asume que la estructura de 'maquina_spiders_project.items.ArticuloInItem' es accesible
  (ej. PYTHONPATH configurado o el spider está en la estructura de proyecto adecuada).
- Se asume que el USER_AGENT genérico es suficiente, pero se recomienda personalizarlo.
"""
import scrapy
from urllib.parse import urljoin
from datetime import datetime
from dateutil import parser as dateparser # Para parseo de fechas flexible

# Se asume que esta es la ruta correcta al Item dentro del proyecto 'maquina_spiders'
# según la estructura definida en las plantillas.
from maquina_spiders_project.items import ArticuloInItem
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose, Join
from w3lib.html import remove_tags, replace_escape_chars

def limpiar_texto(texto):
    """Limpia y normaliza el texto."""
    if texto is None:
        return None
    texto = replace_escape_chars(texto)
    texto = remove_tags(texto)
    return texto.strip()

def unir_parrafos(textos):
    """Une una lista de textos (párrafos) en un solo string, limpiando cada uno."""
    return "\n".join(filter(None, [limpiar_texto(p) for p in textos if p and p.strip()])).strip()

class EuropapressSudamericaSpider(scrapy.Spider):
    name = 'europapress_sudamerica'
    allowed_domains = ['europapress.es']
    start_urls = ['https://www.europapress.es/internacional/sudamerica-00407/']

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (compatible; MaquinaDeNoticiasBot/1.0; +http://tuproyecto.com/bot-info)', # Personalizar URL de info del bot
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'LOG_LEVEL': 'INFO',
    }

    def parse(self, response):
        """
        Callback inicial que procesa la página de la sección de noticias.
        Extrae enlaces a artículos individuales y maneja la paginación.
        Este método se llama 'parse' por convención de Scrapy para los start_urls.
        """
        self.logger.info(f"Procesando sección: {response.url}")

        # Extraer enlaces a artículos
        article_links = response.css('article.noticia h2 a::attr(href)').getall()
        for link in article_links:
            full_article_url = response.urljoin(link)
            yield scrapy.Request(url=full_article_url, callback=self.parse_article)

        # Manejar paginación
        next_page_selector = 'a.button--big[href*="/internacional/sudamerica-00407/noticias-"]::attr(href)'
        next_page_link = response.css(next_page_selector).get()
        if next_page_link:
            full_next_page_url = response.urljoin(next_page_link)
            self.logger.info(f"Siguiente página de sección encontrada: {full_next_page_url}")
            yield scrapy.Request(url=full_next_page_url, callback=self.parse) # Llamada recursiva a parse para la siguiente página
        else:
            self.logger.info("No se encontró siguiente página de sección.")

    def parse_article(self, response):
        """
        Procesa la página de un artículo individual y extrae la información.
        """
        self.logger.info(f"Procesando artículo: {response.url}")

        loader = ItemLoader(item=ArticuloInItem(), response=response)

        # Selectores identificados:
        # Titular: h1.titu-width::text
        # Contenido: div.articulo-cuerpo
        # Fecha: meta[property="article:published_time"]::attr(content) o span.fecha-publicacion::text
        # Autor: div.firma::text
        # Sección: div.breadcrumb > span:nth-child(2) > a::text

        loader.add_css('titular', 'h1.titu-width::text', MapCompose(str.strip), TakeFirst())
        
        # Para contenido_texto, extraemos todos los textos dentro del div y los unimos.
        loader.add_css('contenido_texto', 'div.articulo-cuerpo ::text', MapCompose(str.strip), unir_parrafos)

        # Fecha de publicación (priorizar meta tag)
        fecha_str_meta = response.xpath('//meta[@property="article:published_time"]/@content').get()
        fecha_str_span = response.css('span.fecha-publicacion::text').get()
        
        fecha_publicacion_iso = None
        if fecha_str_meta:
            try:
                fecha_publicacion_iso = dateparser.parse(fecha_str_meta).isoformat()
            except Exception as e:
                self.logger.warning(f"No se pudo parsear fecha (meta) '{fecha_str_meta}' en {response.url}: {e}")
        elif fecha_str_span:
            try:
                # Ejemplo de formato en span: "Viernes, 31 mayo 2024 00:00" - dateparser debería manejarlo
                fecha_publicacion_iso = dateparser.parse(fecha_str_span, languages=['es']).isoformat()
            except Exception as e:
                self.logger.warning(f"No se pudo parsear fecha (span) '{fecha_str_span}' en {response.url}: {e}")
        
        if fecha_publicacion_iso:
            loader.add_value('fecha_publicacion', fecha_publicacion_iso)
        else:
            self.logger.error(f"No se pudo extraer fecha de publicación para {response.url}")
            loader.add_value('fecha_publicacion', None) # O manejar de otra forma

        # Autor
        autor_raw = response.css('div.firma::text').get()
        if autor_raw and autor_raw.strip():
            loader.add_value('autor', autor_raw.strip())
        else:
            loader.add_value('autor', 'Europa Press') # Valor por defecto

        loader.add_value('url', response.url)
        loader.add_value('fuente', self.name.split('_')[0]) # 'europapress' del nombre del spider
        
        # Sección (ej. "Internacional")
        loader.add_css('seccion', 'div.breadcrumb > span:nth-child(2) > a::text', MapCompose(str.strip), TakeFirst())

        item = loader.load_item()

        if self.validate_item(item):
            yield item
        else:
            self.logger.warning(f"Item inválido o incompleto descartado: {response.url} - Titular: {item.get('titular', 'N/A')}")

    def validate_item(self, item):
        """
        Valida si el item extraído tiene los campos mínimos requeridos.
        """
        if not item.get('titular') or len(item['titular']) < 5:
            self.logger.debug(f"Validación fallida: Titular ausente o muy corto para {item.get('url')}")
            return False
        if not item.get('contenido_texto') or len(item['contenido_texto']) < 50: # Ajustar longitud mínima si es necesario
            self.logger.debug(f"Validación fallida: Contenido ausente o muy corto para {item.get('url')}")
            return False
        if not item.get('url'):
            self.logger.debug(f"Validación fallida: URL ausente.") # Esto no debería pasar si se carga desde response.url
            return False
        if not item.get('fecha_publicacion'):
            self.logger.debug(f"Validación fallida: Fecha de publicación ausente para {item.get('url')}")
            return False
        return True
