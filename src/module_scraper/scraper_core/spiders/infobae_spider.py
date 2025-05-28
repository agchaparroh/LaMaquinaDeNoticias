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

        # Intentamos usar los extractores de la clase base primero
        title = self.extract_article_title(response)
        content = self.extract_article_content(response)
        publication_date = self.extract_publication_date(response)
        author = self.extract_author(response)
        # metadata = self.extract_article_metadata(response) # Commented out as metadata is not used

        self.logger.info(f"Título extraído (base): {title}")
        self.logger.info(f"Autor extraído (base): {author}")
        self.logger.info(f"Fecha extraída (base): {publication_date}")
        # self.logger.info(f"Contenido extraído (base): {content[:200]}...") # Descomentar para ver contenido

        # Aquí es donde crearías y llenarías tu Item de Scrapy
        item = ArticuloInItem()
        self.logger.info(f"Campos definidos en ArticuloInItem al instanciar: {ArticuloInItem.fields}")

        item['url'] = response.url
        # item['raw_html_path'] = '' # Opcional, se llenaría en un pipeline si guardas HTML
        item['fuente'] = self.name # El campo 'fuente' en el Item se refiere al spider
        item['medio'] = self.name  # El campo 'medio' es requerido por la validación
        item['pais_publicacion'] = 'AR' # Asumimos Argentina para Infobae, ajustar si es necesario y se puede determinar
        item['tipo_medio'] = 'diario' # Asignamos 'diario' según lo definido en la pipeline
        item['titular'] = title
        # item['subtitulo'] = metadata.get('description', '') # Opcional
        item['fecha_publicacion'] = publication_date
        item['autor'] = author
        item['contenido_texto'] = content # Asumiendo que 'content' es texto plano limpio desde BaseArticleSpider
        # item['tags'] = metadata.get('keywords', []) # Opcional
        # item['url_imagen_principal'] = metadata.get('image', '') # Opcional
        # item['metadata_adicional'] = metadata # Opcional
        
        # Validación básica antes de ceder el item a las pipelines.
        # La DataValidationPipeline hará una validación más exhaustiva.
        if item.get('titular') and item.get('contenido_texto') and item.get('fecha_publicacion') and item.get('medio') and item.get('pais_publicacion') and item.get('tipo_medio'):
            yield item
        else:
            missing_fields = [k for k, v in item.items() if v is None and k in ['titular', 'contenido_texto', 'fecha_publicacion', 'medio', 'pais_publicacion', 'tipo_medio']]
            self.logger.warning(f"Datos esenciales faltantes ({', '.join(missing_fields)}) para {response.url}, descartando item antes de pipeline.")

        # Se comenta el yield del diccionario de previsualización
        # article_data_preview = {
        #     'url': response.url,
        #     'title_base': title,
        #     'author_base': author,
        #     'publication_date_base': publication_date,
        #     'content_preview_base': content[:200] if content else None, # Solo una muestra
        #     'metadata_base': metadata
        # }
        # yield article_data_preview

    # --- Sobrescribir métodos de extracción si es necesario ---
    # Ejemplo:
    # def extract_article_title(self, response: Response) -> Optional[str]:
    #     title = response.css('h1.article-title::text').get()
    #     if title:
    #         return title.strip()
    #     return super().extract_article_title(response) # O llamar al de la base como fallback

    # def extract_article_content(self, response: Response) -> Optional[str]:
    #     # Lógica específica para Infobae
    #     pass

    # def extract_publication_date(self, response: Response) -> Optional[datetime]:
    #     # Lógica específica para Infobae
    #     pass

    # def extract_author(self, response: Response) -> Optional[str]:
    #     # Lógica específica para Infobae
    #     pass

    # def extract_article_metadata(self, response: Response) -> Dict[str, Any]:
    #     # Lógica específica para Infobae
    #     metadata = super().extract_article_metadata(response)
    #     # ... añadir o modificar metadatos específicos de Infobae ...
    #     return metadata
