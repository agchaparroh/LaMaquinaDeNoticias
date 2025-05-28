"""
Ejemplo de uso de ArticuloInItem y ArticuloInItemLoader
========================================================

Este ejemplo muestra cómo usar el sistema de Items y ItemLoaders
para procesar artículos periodísticos en spiders de Scrapy.
"""

from scrapy import Spider
from scraper_core.items import ArticuloInItem
from scraper_core.itemloaders import ArticuloInItemLoader
from datetime import datetime


class ExampleSpider(Spider):
    """
    Spider de ejemplo que muestra cómo usar ArticuloInItemLoader
    """
    name = 'example_spider'
    start_urls = ['https://example-news-site.com']
    
    def parse(self, response):
        """
        Método principal de parseo
        """
        # Buscar todos los artículos en la página
        articles = response.css('article.news-item')
        
        for article in articles:
            # Crear un loader para cada artículo
            loader = ArticuloInItemLoader(item=ArticuloInItem(), selector=article)
            
            # Agregar campos usando selectores CSS
            loader.add_css('titular', 'h2.article-title::text')
            loader.add_css('url', 'a.article-link::attr(href)')
            loader.add_css('autor', 'span.author::text')
            loader.add_css('fecha_publicacion', 'time::attr(datetime)')
            loader.add_css('resumen', 'p.summary::text')
            loader.add_css('etiquetas_fuente', 'span.tag::text')  # Procesará múltiples tags
            
            # Agregar valores estáticos
            loader.add_value('medio', 'Example News')
            loader.add_value('pais_publicacion', 'España')
            loader.add_value('tipo_medio', 'digital')
            loader.add_value('idioma', 'es')
            
            # Extraer URL del artículo para seguirlo
            article_url = article.css('a.article-link::attr(href)').get()
            
            if article_url:
                # Seguir el enlace para obtener el contenido completo
                yield response.follow(
                    article_url,
                    callback=self.parse_article,
                    meta={'loader': loader}
                )
    
    def parse_article(self, response):
        """
        Parsear página individual del artículo
        """
        # Recuperar el loader del meta
        loader = response.meta['loader']
        
        # Actualizar el selector para usar el response completo
        loader.selector = response
        
        # Extraer contenido completo del artículo
        loader.add_css('contenido_texto', 'div.article-content')
        loader.add_css('contenido_html', 'div.article-content')
        
        # Extraer metadatos adicionales
        loader.add_css('seccion', 'nav.breadcrumb span:last-child::text')
        
        # Detectar si es artículo de opinión
        is_opinion = bool(response.css('section.opinion').get())
        loader.add_value('es_opinion', is_opinion)
        
        # Detectar si es fuente oficial
        is_official = 'gobierno' in response.url or 'official' in response.url
        loader.add_value('es_oficial', is_official)
        
        # Cargar y validar el item
        item = loader.load_item()
        
        # Validar antes de devolver
        if item.validate():
            yield item
        else:
            self.logger.warning(f"Item inválido para URL: {response.url}")


# Ejemplo de uso directo del loader
def example_direct_usage():
    """
    Ejemplo de uso directo del ItemLoader sin spider
    """
    # Crear loader
    loader = ArticuloInItemLoader(item=ArticuloInItem())
    
    # Agregar valores directamente
    loader.add_value('titular', '<h1>Noticia Importante sobre Economía</h1>')
    loader.add_value('contenido_texto', '''
        <p>El gobierno anunció hoy nuevas medidas económicas...</p>
        <p>Estas medidas incluyen reducciones de impuestos...</p>
    ''')
    loader.add_value('autor', 'Por María García')
    loader.add_value('fecha_publicacion', '15/01/2024 10:30')
    loader.add_value('medio', 'El Periódico Digital')
    loader.add_value('pais_publicacion', 'españa')  # Se capitalizará automáticamente
    loader.add_value('tipo_medio', 'newspaper')  # Se mapeará a 'diario'
    loader.add_value('url', 'https://example.com/noticia?utm_source=twitter&id=123')
    loader.add_value('etiquetas_fuente', 'economía, política, impuestos')
    loader.add_value('es_opinion', False)
    loader.add_value('puntuacion_relevancia', '8')
    
    # Cargar item
    item = loader.load_item()
    
    # Mostrar resultado
    print("Item procesado:")
    print(f"Titular: {item['titular']}")
    print(f"Autor: {item['autor']}")
    print(f"Fecha: {item['fecha_publicacion']}")
    print(f"URL limpia: {item['url']}")
    print(f"Storage path: {item['storage_path']}")
    print(f"Etiquetas: {item['etiquetas_fuente']}")
    print(f"Válido: {item.validate()}")
    
    return item


# Ejemplo con XPath
def example_xpath_usage(response):
    """
    Ejemplo usando selectores XPath
    """
    loader = ArticuloInItemLoader(item=ArticuloInItem(), response=response)
    
    # Usar XPath en lugar de CSS
    loader.add_xpath('titular', '//h1[@class="main-title"]/text()')
    loader.add_xpath('autor', '//div[@class="author-info"]//span[@class="name"]/text()')
    loader.add_xpath('contenido_texto', '//div[@id="article-body"]')
    loader.add_xpath('fecha_publicacion', '//meta[@property="article:published_time"]/@content')
    
    # Combinar con valores estáticos
    loader.add_value('medio', 'Example News XPath')
    loader.add_value('pais_publicacion', 'México')
    loader.add_value('tipo_medio', 'digital')
    
    return loader.load_item()


# Ejemplo de procesamiento personalizado
def example_custom_processing():
    """
    Ejemplo con procesamiento personalizado
    """
    from itemloaders.processors import MapCompose
    
    # Crear un loader con procesador personalizado
    loader = ArticuloInItemLoader(item=ArticuloInItem())
    
    # Definir procesador personalizado para metadata
    def process_metadata(value):
        """Procesar metadata personalizada"""
        return {
            'processed_at': datetime.now().isoformat(),
            'version': '1.0',
            'custom_field': value
        }
    
    # Usar el procesador
    loader.add_value('metadata', 'valor_custom', process_metadata)
    
    # Agregar otros campos requeridos
    loader.add_value('titular', 'Artículo con Metadata')
    loader.add_value('medio', 'Test Media')
    loader.add_value('pais_publicacion', 'España')
    loader.add_value('tipo_medio', 'blog')
    loader.add_value('contenido_texto', 'Contenido del artículo...')
    loader.add_value('fecha_publicacion', '2024-01-15')
    
    item = loader.load_item()
    print(f"Metadata: {item['metadata']}")
    
    return item


if __name__ == '__main__':
    # Ejecutar ejemplo directo
    print("=== Ejemplo de uso directo ===")
    example_direct_usage()
    
    print("\n=== Ejemplo con procesamiento personalizado ===")
    example_custom_processing()
