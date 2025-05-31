# scraper_core/middlewares/playwright_custom_middleware.py
from scrapy import signals
from scrapy.http import HtmlResponse, Request

class PlaywrightCustomDownloaderMiddleware:
    """
    Middleware personalizado para detectar respuestas con contenido vacío y reintentar
    la solicitud utilizando Playwright para el renderizado de JavaScript.
    """

    # Nota: scrapy-playwright ya proporciona su propio DownloaderHandler.
    # Este middleware es más para lógica *adicional* o *personalizada*
    # sobre cuándo y cómo se usa Playwright, si la configuración por defecto
    # de scrapy-playwright (activada por DOWNLOAD_HANDLERS) no es suficiente
    # o si se quiere un control más granular antes de que la petición llegue al handler.

    # Por ejemplo, podrías usar este middleware para:
    # 1. Marcar dinámicamente las peticiones que deben usar Playwright
    #    basado en lógica compleja (request.meta['playwright'] = True).
    # 2. Realizar acciones específicas con Playwright *antes* o *después* de la navegación principal,
    #    aunque esto es más avanzado y a menudo se maneja mejor dentro de la araña
    #    usando las capacidades de scrapy-playwright.

    # Para la mayoría de los casos de "usar Playwright para esta URL",
    # simplemente enviar un Request con `meta={'playwright': True}` desde la araña
    # es suficiente y scrapy-playwright lo manejará automáticamente
    # gracias a la configuración en DOWNLOAD_HANDLERS.

    # Por ahora, este middleware será un placeholder.
    # La funcionalidad principal de scrapy-playwright se activa a través de
    # Request(url, meta={'playwright': True}) en tus spiders.

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        # Si necesitas manejar el cierre del navegador de forma explícita,
        # podrías conectar a spider_closed, pero scrapy-playwright debería manejarlo.
        return middleware

    def spider_opened(self, spider):
        spider.logger.info(f'{self.__class__.__name__} opened for spider {spider.name}')

    # process_request podría usarse para decidir si activar Playwright para una solicitud
    # que no lo tiene activado, o para modificar las opciones de Playwright.
    # def process_request(self, request, spider):
    #     if self._should_use_playwright(request, spider):
    #         request.meta['playwright'] = True
    #         request.meta['playwright_include_page'] = True # Para obtener el objeto page en la respuesta
    #         # Puedes añadir más configuraciones de Playwright aquí si es necesario
    #         # request.meta['playwright_page_coroutines'] = [ ... ]
    #     return None # Devuelve None para que Scrapy continúe procesando la solicitud

    # def _should_use_playwright(self, request, spider):
    #     # Lógica para decidir si usar Playwright
    #     # Ejemplo: return "render_js" in request.url or request.meta.get("render_js_flag")
    #     return False # Por defecto, no fuerces Playwright aquí

    async def process_response(self, request, response, spider):
        # Solo procesar respuestas HTML
        if not isinstance(response, HtmlResponse):
            return response

        # Condición 1: La respuesta actual NO fue generada por una solicitud de Playwright
        # (evita bucles si Playwright también devuelve contenido vacío)
        is_playwright_request = request.meta.get('playwright')

        # Condición 2: El cuerpo de la respuesta está vacío después de quitar espacios en blanco.
        body_is_empty = not response.body.strip()

        if not is_playwright_request and body_is_empty:
            spider.logger.info(
                f"Respuesta vacía (o solo espacios en blanco) detectada para {response.url}. "
                f"Reintentando con Playwright."
            )
            
            # Crear una nueva solicitud para la misma URL, pero forzando Playwright
            new_meta = request.meta.copy()
            new_meta['playwright'] = True
            # Opcional: puedes añadir otras configuraciones de Playwright aquí si es necesario, como:
            # new_meta['playwright_include_page'] = True 
            # new_meta['playwright_page_coroutines'] = [ page.wait_for_load_state('networkidle') ]

            return Request(
                response.url,
                callback=request.callback,
                errback=request.errback,
                priority=request.priority, # Mantener la prioridad original
                meta=new_meta,
                dont_filter=True # Importante para permitir que la misma URL sea solicitada de nuevo
            )

        return response

    # Si no necesitas lógica personalizada en un middleware separado,
    # la configuración de DOWNLOAD_HANDLERS y el uso de meta={'playwright': True}
    # en las arañas es la forma principal de usar scrapy-playwright.