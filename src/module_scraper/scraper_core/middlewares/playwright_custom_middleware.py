# scraper_core/middlewares/playwright_custom_middleware.py
from scrapy import signals
from scrapy.http import HtmlResponse
from playwright.async_api import async_playwright

class PlaywrightCustomDownloaderMiddleware:
    """
    Middleware personalizado para decidir cuándo usar Playwright para una solicitud
    y para manejar la representación de la página.
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

    # process_response podría usarse para interactuar con la página de Playwright
    # si 'playwright_include_page' fue True.
    # async def process_response(self, request, response, spider):
    #     if request.meta.get('playwright_include_page') and hasattr(response, 'playwright_page'):
    #         page = response.playwright_page
    #         # Aquí puedes interactuar con la página, por ejemplo, tomar una captura de pantalla
    #         # await page.screenshot(path=f"screenshot_{spider.name}.png")
    #         await page.close() # Importante cerrar la página si la incluiste
    #     return response

    # Si no necesitas lógica personalizada en un middleware separado,
    # la configuración de DOWNLOAD_HANDLERS y el uso de meta={'playwright': True}
    # en las arañas es la forma principal de usar scrapy-playwright.