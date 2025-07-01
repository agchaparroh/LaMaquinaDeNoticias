"""
Spider generado automáticamente por Spider Factory 2.0
Medio: articulo66
Sección: politica
Fecha: 2025-07-01T03:33:20.258637
Estrategia: rss

GENERADO AUTOMÁTICAMENTE - NO EDITAR MANUALMENTE
Los cambios manuales se perderán en la próxima generación
"""

import re
import scrapy
from scrapy import signals
from scrapy.exceptions import CloseSpider
import feedparser
from datetime import datetime
import logging
from typing import Dict, Any, Optional, Iterator
import asyncio
from playwright.async_api import async_playwright
import requests
import json


class Articulo66PoliticaSpider(scrapy.Spider):
    """
    Spider RSS para articulo66 - politica

    Utiliza feeds RSS para obtener artículos de noticias.
    Área geográfica: VENEZUELA
    Tipo de medio: revista
    """

    name = "articulo66_politica"
    allowed_domains = ["articulo66.com"]

    # Configuración
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "ROBOTSTXT_OBEY": False,  # Desactivado para evitar problemas con Cloudflare
        "CONCURRENT_REQUESTS": 1,  # Muy conservador para evitar detección
        "DOWNLOAD_DELAY": 5,  # Delay mayor para parecer más humano
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "COOKIES_ENABLED": True,
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "DNT": "1",
        },
        # Scrapy-crawl-once configuration
        "CRAWL_ONCE_ENABLED": True,
        "CRAWL_ONCE_PATH": f".scrapy/crawl_once/articulo66_politica",
        "CRAWL_ONCE_DEFAULT": False,
        # Configuración de encoding
        "FEED_EXPORT_ENCODING": "utf-8",
        # SCRAPYD CONFIGURATION:
        # Schedule: Every 120 minutes
        # Project: lamaquina
        # Spider: articulo66_politica
        # Arguments: -a max_items=100
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rss_url = "https://www.articulo66.com/categorias/politica/feed/"
        self.articles_scraped = 0
        self.max_articles = int(kwargs.get("max_items", 100))

        # Información del medio
        self.medio_info = {
            "medio": "articulo66",
            "seccion": "politica",
            "area_geografica": "VENEZUELA",
            "tipo_medio": "revista",
            "medio_url_principal": "https://www.articulo66.com/",
            "frecuencia_minutos": 120,
        }

    def get_rss_with_flaresolverr_cookies(self, url: str) -> str:
        """
        Obtiene RSS usando FlareSolverr para obtener cookies válidas y luego requests normal
        
        Método alternativo recomendado por ScrapeOps: usar FlareSolverr solo para cookies
        y luego continuar con HTTP client normal (más eficiente)
        
        Args:
            url: URL del feed RSS
            
        Returns:
            str: Contenido del RSS como texto
        """
        self.logger.info("🍪 Iniciando FlareSolverr COOKIES method...")
        
        flaresolverr_url = "http://flaresolverr:8191/v1"
        
        # Primera fase: obtener cookies válidas
        cookie_request = {
            "cmd": "request.get",
            "url": url,
            "maxTimeout": 90000,  # 90 segundos para obtener cookies
            "returnOnlyCookies": True,  # Solo queremos las cookies
        }
        
        try:
            self.logger.info(f"🍪 Fase 1: Obteniendo cookies de Cloudflare...")
            
            response = requests.post(
                flaresolverr_url,
                headers={'Content-Type': 'application/json'},
                json=cookie_request,
                timeout=100
            )
            response.raise_for_status()
            
            json_response = response.json()
            
            if json_response.get('status') == 'ok':
                cookies = json_response.get('solution', {}).get('cookies', [])
                user_agent = json_response.get('solution', {}).get('userAgent', '')
                
                self.logger.info(f"🍪 Cookies obtenidas: {len(cookies)} items")
                
                # Segunda fase: usar cookies con requests normal
                self.logger.info(f"🍪 Fase 2: Request con cookies válidas...")
                
                # Convertir cookies a formato requests
                cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
                
                headers = {
                    'User-Agent': user_agent or 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                    'Accept': 'application/rss+xml, application/xml, text/xml',
                    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Cache-Control': 'no-cache'
                }
                
                resp = requests.get(url, headers=headers, cookies=cookie_dict, timeout=30)
                resp.raise_for_status()
                
                self.logger.info(f"🍪 SUCCESS! Content length: {len(resp.text)} chars")
                return resp.text
                
            else:
                raise Exception(f"Cookie extraction failed: {json_response.get('message')}")
                
        except Exception as e:
            self.logger.error(f"🍪 Cookie method ERROR: {e}")
            raise

    def get_rss_with_flaresolverr(self, url: str) -> str:
        """
        Obtiene RSS usando FlareSolverr para bypass Cloudflare avanzado
        
        FlareSolverr es la solución más recomendada por ScrapeOps para Cloudflare
        Usa Selenium con undetected-chromedriver en un servidor proxy
        
        Args:
            url: URL del feed RSS
            
        Returns:
            str: Contenido del RSS como texto
        """
        self.logger.info("🔥 Iniciando FlareSolverr (método EXPERT ScrapeOps)...")
        
        # Usar red interna Docker para comunicación robusta
        flaresolverr_url = "http://flaresolverr:8191/v1"
        
        # Configuración para FlareSolverr (configuración agresiva anti-Cloudflare)
        post_body = {
            "cmd": "request.get",
            "url": url,
            "maxTimeout": 120000,  # 120 segundos - timeout extendido para Cloudflare difícil
            "returnOnlyCookies": False,  # Queremos el contenido completo
            "proxy": None,  # Sin proxy inicial
            "headers": {
                "Accept": "application/rss+xml, application/xml, text/xml",
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
                "Cache-Control": "no-cache"
            }
        }
        
        try:
            self.logger.info(f"🔥 Enviando request a FlareSolverr: {url}")
            
            # Enviar request a FlareSolverr
            response = requests.post(
                flaresolverr_url,
                headers={'Content-Type': 'application/json'},
                json=post_body,
                timeout=130  # Un poco más que maxTimeout (120s)
            )
            response.raise_for_status()
            
            json_response = response.json()
            self.logger.info(f"🔥 FlareSolverr response status: {json_response.get('status')}")
            
            if json_response.get('status') == 'ok':
                solution = json_response.get('solution', {})
                content = solution.get('response', '')
                
                if content and len(content) > 100:  # Verificar que tenemos contenido útil
                    self.logger.info(f"🔥 FlareSolverr SUCCESS! Content length: {len(content)} chars")
                    self.logger.info(f"🔥 Response URL: {solution.get('url')}")
                    self.logger.info(f"🔥 HTTP Status: {solution.get('status')}")
                    
                    # Log cookies para debug
                    cookies = solution.get('cookies', [])
                    self.logger.info(f"🔥 Cookies received: {len(cookies)} items")
                    
                    return content
                else:
                    raise Exception(f"Contenido vacío o inválido: {len(content) if content else 0} chars")
            else:
                message = json_response.get('message', 'Unknown error')
                raise Exception(f"FlareSolverr failed: {message}")
                
        except requests.exceptions.ConnectionError:
            self.logger.error("🔥 FlareSolverr no está accesible en red Docker")
            self.logger.error("🔥 Verificar: docker-compose ps flaresolverr")
            self.logger.error("🔥 Levantar: docker-compose up -d flaresolverr")
            raise Exception("FlareSolverr server not available")
        except Exception as e:
            self.logger.error(f"🔥 FlareSolverr ERROR: {e}")
            raise

    async def get_rss_with_stealth(self, url: str) -> str:
        """
        Obtiene RSS usando Playwright con stealth para bypass Cloudflare
        
        Args:
            url: URL del feed RSS
            
        Returns:
            str: Contenido del RSS como texto
        """
        self.logger.info("🎭 Iniciando Playwright con stealth...")
        
        async with async_playwright() as p:
            # Configuración de browser con stealth
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            
            # Aplicar stealth manual (más efectivo que playwright-stealth)
            await self._apply_stealth_scripts(page)
            
            # Headers adicionales para RSS
            await page.set_extra_http_headers({
                'Accept': 'application/rss+xml, application/xml, text/xml, text/html;q=0.9,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'no-cache',
                'DNT': '1'
            })
            
            try:
                self.logger.info(f"🎭 Navegando a: {url}")
                
                # Timeout generoso para Cloudflare
                response = await page.goto(url, wait_until='networkidle', timeout=60000)
                
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")
                
                # Obtener contenido
                content = await page.content()
                
                self.logger.info(f"🎭 Stealth SUCCESS! Content length: {len(content)} chars")
                self.logger.info(f"🎭 Response status: {response.status}")
                
                await browser.close()
                return content
                
            except Exception as e:
                self.logger.error(f"🎭 Stealth ERROR: {e}")
                await browser.close()
                raise

    async def _apply_stealth_scripts(self, page):
        """
        Aplica scripts de stealth manual para evadir detección de Cloudflare
        """
        # Script principal de stealth anti-detección
        stealth_script = """
        // Eliminar webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Sobrescribir plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {
                    description: "Portable Document Format",
                    filename: "internal-pdf-viewer",
                    length: 1,
                    name: "Chrome PDF Plugin"
                }
            ]
        });
        
        // Sobrescribir languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['es-ES', 'es', 'en-US', 'en']
        });
        
        // Eliminar chrome runtime
        if (window.chrome) {
            delete window.chrome.runtime;
        }
        
        // Permissions API
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
        );
        
        // Eliminar automation traces
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        
        // Mock canvas fingerprinting
        const getContext = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function(type) {
            if (type === '2d') {
                const context = getContext.apply(this, arguments);
                const getImageData = context.getImageData;
                context.getImageData = function(x, y, w, h) {
                    const imageData = getImageData.apply(this, arguments);
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        imageData.data[i] += Math.floor(Math.random() * 10) - 5;
                        imageData.data[i + 1] += Math.floor(Math.random() * 10) - 5; 
                        imageData.data[i + 2] += Math.floor(Math.random() * 10) - 5;
                    }
                    return imageData;
                };
                return context;
            }
            return getContext.apply(this, arguments);
        };
        
        // Screen resolution randomization
        Object.defineProperty(window.screen, 'width', {
            get: () => 1920 + Math.floor(Math.random() * 100)
        });
        Object.defineProperty(window.screen, 'height', {
            get: () => 1080 + Math.floor(Math.random() * 100)
        });
        """
        
        # Aplicar el script antes de la navegación
        await page.add_init_script(stealth_script)
        self.logger.info("🎭 Scripts de stealth manual aplicados")

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def start_requests(self):
        """Inicia el scraping desde el feed RSS"""
        self.logger.info(f"Iniciando scraping de RSS: {self.rss_url}")

        # Headers adicionales específicos para RSS y Cloudflare bypass
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/rss+xml, application/xml, text/xml, application/xhtml+xml, text/html;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "DNT": "1",
            "Pragma": "no-cache",
        }

        # Usar scrapy para descargar el RSS con headers optimizados
        yield scrapy.Request(
            url=self.rss_url,
            callback=self.parse_rss,
            errback=self.handle_error,
            headers=headers,
            meta={
                "handle_httpstatus_all": True,
                "dont_cache": True,  # No usar caché para evitar problemas
            },
        )

    def parse_rss(self, response):
        """Parsea el feed RSS y genera requests para cada artículo"""
        if response.status != 200:
            self.logger.error(f"Error descargando RSS: {response.status}")
            # Intentar con cloudscraper para bypass Cloudflare
            try:
                import cloudscraper
                
                self.logger.info("Usando cloudscraper para bypass Cloudflare...")
                
                # Crear scraper con configuración avanzada para Cloudflare bypass
                scraper = cloudscraper.create_scraper(
                    browser={
                        'browser': 'chrome',
                        'platform': 'windows',
                        'mobile': False
                    },
                    delay=10,  # Delay conservador para evitar detección
                    doubleDown=True,  # Activar bypass avanzado
                    disableCloudflareV1=False,  # Mantener compatibilidad con V1
                    debug=True  # Para debug en caso de problemas
                )
                
                # Headers realistas para simular navegador humano
                headers = {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Cache-Control': 'max-age=0',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'DNT': '1',
                }
                
                # Primer intento con cloudscraper
                try:
                    resp = scraper.get(self.rss_url, headers=headers, timeout=30)
                    resp.raise_for_status()
                except Exception as first_error:
                    self.logger.warning(f"Primer intento falló: {first_error}")
                    
                    # Segundo intento con configuración más agresiva
                    self.logger.info("Segundo intento con configuración más agresiva...")
                    scraper2 = cloudscraper.create_scraper(
                        browser={
                            'browser': 'firefox',
                            'platform': 'windows',
                            'mobile': False
                        },
                        delay=15,
                        doubleDown=True,
                        disableCloudflareV1=True
                    )
                    
                    # Headers simplificados para segundo intento
                    simple_headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
                        'Accept': 'application/rss+xml, application/xml, text/xml, */*',
                        'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                    }
                    
                    resp = scraper2.get(self.rss_url, headers=simple_headers, timeout=45)
                    resp.raise_for_status()
                    
                    self.logger.info(f"Cloudscraper response: {resp.status_code}")
                    self.logger.info(f"Content-Type: {resp.headers.get('Content-Type')}")
                    
                    # Usar el contenido de cloudscraper
                    content_str = resp.text
                    self.logger.info(f"Cloudscraper success! Text length: {len(content_str)} chars")
                    
                    # Parsear RSS con feedparser
                    feed = feedparser.parse(content_str)
                    
                    if feed.bozo:
                        self.logger.warning(f"RSS mal formado: {feed.bozo_exception}")
                    else:
                        self.logger.info("RSS parseado correctamente con cloudscraper")
                        
            except Exception as cloudscraper_error:
                self.logger.warning(f"Cloudscraper también falló: {cloudscraper_error}")
                
                # TERCER INTENTO: FlareSolverr Cookies (recomendación ScrapeOps experts)
                try:
                    self.logger.info("🍪 Iniciando TERCER intento con FlareSolverr Cookies...")
                    
                    content_str = self.get_rss_with_flaresolverr_cookies(self.rss_url)
                    self.logger.info(f"🍪 FlareSolverr Cookies SUCCESS! Content length: {len(content_str)} chars")
                    
                    # Parsear RSS con feedparser
                    feed = feedparser.parse(content_str)
                    
                    if feed.bozo:
                        self.logger.warning(f"RSS mal formado: {feed.bozo_exception}")
                    else:
                        self.logger.info("🍪 RSS parseado correctamente con FlareSolverr Cookies!")
                        
                except Exception as flaresolverr_cookies_error:
                    self.logger.warning(f"🍪 FlareSolverr Cookies falló: {flaresolverr_cookies_error}")
                    
                    # CUARTO INTENTO: FlareSolverr Full (contenido completo)
                    try:
                        self.logger.info("🔥 Iniciando CUARTO intento con FlareSolverr Full...")
                        
                        content_str = self.get_rss_with_flaresolverr(self.rss_url)
                        self.logger.info(f"🔥 FlareSolverr SUCCESS! Content length: {len(content_str)} chars")
                        
                        # Parsear RSS con feedparser
                        feed = feedparser.parse(content_str)
                        
                        if feed.bozo:
                            self.logger.warning(f"RSS mal formado: {feed.bozo_exception}")
                        else:
                            self.logger.info("🔥 RSS parseado correctamente con FlareSolverr!")
                            
                    except Exception as flaresolverr_error:
                        self.logger.warning(f"🔥 FlareSolverr también falló: {flaresolverr_error}")
                        
                        # QUINTO INTENTO: Playwright con stealth (último recurso)
                        try:
                            self.logger.info("🎭 Iniciando QUINTO intento con Playwright Stealth...")
                            
                            # Ejecutar función async en event loop
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            
                            try:
                                content_str = loop.run_until_complete(
                                    self.get_rss_with_stealth(self.rss_url)
                                )
                            finally:
                                loop.close()
                            
                            self.logger.info(f"🎭 Playwright SUCCESS! Content length: {len(content_str)} chars")
                            
                            # Parsear RSS con feedparser
                            feed = feedparser.parse(content_str)
                            
                            if feed.bozo:
                                self.logger.warning(f"RSS mal formado: {feed.bozo_exception}")
                            else:
                                self.logger.info("🎭 RSS parseado correctamente con Playwright Stealth!")
                                
                        except Exception as stealth_error:
                            self.logger.error(f"🎭 Playwright Stealth FALLÓ: {stealth_error}")
                            self.logger.error("❌ TODOS los métodos de bypass fallaron (5 intentos)")
                            return
        else:
            # Parsear RSS con feedparser
            feed = feedparser.parse(response.text)

        if feed.bozo:
            self.logger.warning(f"RSS mal formado: {feed.bozo_exception}")

        self.logger.info(f"Encontrados {len(feed.entries)} artículos en RSS")

        try:
            # Contadores para estadísticas
            articles_processed = 0
            articles_accepted = 0

            # Procesar cada entrada del feed
            for entry in feed.entries[: self.max_articles]:
                articles_processed += 1

                # Verificar si el artículo pertenece a la sección
                if self._belongs_to_section(entry):
                    articles_accepted += 1
                    article_data = self.extract_rss_data(entry)

                    # Agregar información de filtrado a metadata
                    article_data["metadata"]["section_filter"] = "accepted"
                    article_data["metadata"]["filter_reason"] = self._get_filter_reason(
                        entry
                    )

                    if article_data.get("url"):
                        yield scrapy.Request(
                            url=article_data["url"],
                            callback=self.parse_article,
                            errback=self.handle_error,
                            meta={"article_data": article_data},
                        )
                    else:
                        # Si no hay link, yield directo los datos del RSS
                        yield article_data
                else:
                    # Log de artículos rechazados para debugging
                    self.logger.debug(
                        f"Artículo rechazado: {getattr(entry, 'title', 'Sin título')} - "
                        f"Razón: {self._get_rejection_reason(entry)}"
                    )

            # Log de estadísticas de filtrado
            filter_rate = (
                (articles_accepted / articles_processed * 100)
                if articles_processed > 0
                else 0
            )
            self.logger.info(
                f"Filtrado RSS: {articles_accepted}/{articles_processed} artículos aceptados "
                f"({filter_rate:.1f}%) para sección 'politica'"
            )

        except Exception as e:
            self.logger.error(f"Error parseando RSS: {e}")

    def _get_filter_reason(self, entry) -> str:
        """Determina por qué se aceptó un artículo (para debugging)"""
        target_section = "politica"

        # Verificar categorías
        if hasattr(entry, "tags") and entry.tags:
            categories = [
                tag.term.lower().strip() for tag in entry.tags if hasattr(tag, "term")
            ]
            if target_section in categories:
                return "categoria_exacta"
            for category in categories:
                if target_section in category or category in target_section:
                    return "categoria_parcial"

        # Verificar URL
        if hasattr(entry, "link") and entry.link:
            if self._is_section_article(entry.link):
                return "url_pattern"

        return "inclusion_por_defecto"

    def _get_rejection_reason(self, entry) -> str:
        """Determina por qué se rechazó un artículo (para debugging)"""
        if not hasattr(entry, "link") or not entry.link:
            return "sin_url"

        # Este método solo se llama si _belongs_to_section devuelve False
        # Que en el código actual solo ocurre si _is_section_article devuelve False
        # Ya que _belongs_to_section devuelve True por defecto
        return "url_no_coincide_con_seccion"

    def _belongs_to_section(self, entry) -> bool:
        """
        Verifica si la entrada RSS pertenece a la sección objetivo.

        Criterios de filtrado:
        1. Categorías RSS (tags) - primera prioridad
        2. Patrones de URL - segunda prioridad
        3. Inclusión por defecto si no se puede determinar

        Args:
            entry: Entrada del feed RSS parseada por feedparser

        Returns:
            bool: True si la entrada pertenece a la sección
        """
        target_section = "politica"

        # Criterio 1: Verificar por categorías RSS
        if hasattr(entry, "tags") and entry.tags:
            categories = [
                tag.term.lower().strip() for tag in entry.tags if hasattr(tag, "term")
            ]

            # Buscar coincidencia exacta primero
            if target_section in categories:
                self.logger.debug(
                    f"Artículo aceptado por categoría exacta: {target_section}"
                )
                return True

            # Buscar coincidencia parcial en categorías
            for category in categories:
                if target_section in category or category in target_section:
                    self.logger.debug(
                        f"Artículo aceptado por categoría parcial: {category}"
                    )
                    return True

        # Criterio 2: Verificar por URL si hay link
        if hasattr(entry, "link") and entry.link:
            url_matches = self._is_section_article(entry.link)
            if url_matches:
                self.logger.debug(f"Artículo aceptado por URL: {entry.link}")
                return url_matches

        # Criterio 3: Por defecto incluir si no podemos determinar sección
        # Esto evita perder contenido válido de feeds mal configurados
        self.logger.debug(f"Artículo incluido por defecto (sin información de sección)")
        return True

    def _is_section_article(self, url: str) -> bool:
        """
        Valida si la URL del artículo pertenece a la sección objetivo.

        Filtros aplicados:
        1. Exclusión de contenido no deseado (archivos, multimedia, etc.)
        2. Verificación de patrones de sección en la URL

        Args:
            url: URL del artículo a verificar

        Returns:
            bool: True si la URL pertenece a la sección objetivo
        """
        if not url:
            return False

        # Patrones a excluir (contenido no deseado)
        excluded_patterns = [
            r"/archivo/",  # Archivos/hemeroteca
            r"/hemeroteca/",  # Archivo histórico
            r"/newsletter/",  # Boletines
            r"/multimedia/",  # Contenido multimedia
            r"/video[s]?/",  # Videos
            r"/podcast[s]?/",  # Podcasts
            r"/audio[s]?/",  # Audio
            r"/galeria[s]?/",  # Galerías de fotos
            r"/foto[s]?/",  # Fotos
            r"/infografia[s]?/",  # Infografías
            r"/tags?/",  # Páginas de tags
            r"/etiqueta[s]?/",  # Etiquetas (español)
            r"/autor[es]?/",  # Páginas de autor
            r"/busca[rd]?/",  # Búsquedas
            r"/search/",  # Búsquedas (inglés)
            r"/categoria[s]?/",  # Páginas de categoría
            r"/archivo-por-fecha/",  # Archivo por fecha
            r"/rss/",  # Feeds RSS
            r"/feed/",  # Feeds
            r"/sitemap/",  # Sitemaps
        ]

        # Verificar exclusiones
        for pattern in excluded_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                self.logger.debug(f"URL excluida por patrón {pattern}: {url}")
                return False

        # Crear patrón de sección (flexible para espacios, guiones, guiones bajos)
        target_section = "politica"
        section_patterns = [
            rf"/{target_section}/",  # /politica/
            rf"/{target_section}\.html",  # /politica.html
            rf"/{target_section}-",  # /politica-algo
            rf"/{target_section}_",  # /politica_algo
            rf"-{target_section}-",  # algo-politica-algo
            rf"_{target_section}_",  # algo_politica_algo
        ]

        # Verificar que pertenece a la sección
        for pattern in section_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                self.logger.debug(f"URL aceptada por patrón {pattern}: {url}")
                return True

        # Si no encuentra patrón específico, rechazar para ser conservador
        self.logger.debug(
            f"URL no contiene patrón de sección '{target_section}': {url}"
        )
        return False

    def extract_rss_data(self, entry) -> Dict[str, Any]:
        """Extrae datos estructurados de una entrada RSS con campos obligatorios"""
        # Extraer fecha de publicación
        fecha_pub = None
        if hasattr(entry, "published_parsed"):
            fecha_pub = datetime(*entry.published_parsed[:6])
        elif hasattr(entry, "updated_parsed"):
            fecha_pub = datetime(*entry.updated_parsed[:6])

        # Extraer contenido
        contenido = ""
        if hasattr(entry, "summary"):
            contenido = entry.summary
        elif hasattr(entry, "description"):
            contenido = entry.description

        # Crear item con TODOS los campos obligatorios
        article_data = {
            # Campos obligatorios
            "url": getattr(entry, "link", ""),
            "titular": getattr(entry, "title", ""),  # IMPORTANTE: 'titular' no 'titulo'
            "medio": self.medio_info["medio"],
            "medio_url_principal": self.medio_info["medio_url_principal"],
            "area_geografica": self.medio_info["area_geografica"],
            "tipo_medio": self.medio_info["tipo_medio"],
            "seccion": self.medio_info["seccion"],
            "fecha_publicacion": fecha_pub.isoformat() if fecha_pub else None,
            "contenido_texto": contenido,
            "contenido_html": contenido,  # RSS normalmente no tiene HTML separado
            "fuente": self.name,
            "fecha_extraccion": datetime.now().isoformat(),
            # Metadata adicional
            "metadata": {
                "spider_type": "rss",
                "extraction_method": "feedparser",
                "section_filter": "pending",  # Se actualiza en parse_rss
                "rss_guid": getattr(entry, "id", None),
                "from_rss": True,
                "rss_url": self.rss_url,
                "spider_name": self.name,
                "generation_date": "2025-07-01T03:33:20.258637",
                "frecuencia_minutos": 120,
            },
        }

        # Campos opcionales
        if hasattr(entry, "author"):
            article_data["autor"] = entry.author

        # Categorías/Tags
        if hasattr(entry, "tags"):
            article_data["metadata"]["categorias"] = [tag.term for tag in entry.tags]

        # Media/Imágenes
        if hasattr(entry, "media_content"):
            article_data["metadata"]["media"] = [
                {"url": media.get("url"), "type": media.get("type")}
                for media in entry.media_content
            ]

        return article_data

    def parse_article(self, response):
        """Parsea la página del artículo para extraer contenido completo"""
        if response.status != 200:
            self.logger.warning(
                f"Error accediendo artículo: {response.status} - {response.url}"
            )
            # Devolver solo datos del RSS
            yield response.meta["article_data"]
            return

        article_data = response.meta["article_data"]
        article_data["url"] = response.url  # Actualizar con URL final (redirects)
        article_data["metadata"]["http_status"] = response.status

        try:
            # Extraer contenido usando selectores
            # Selectores genéricos si no hay específicos
            content = self.extract_generic_content(response)
            if content:
                article_data["contenido_texto"] = content
                article_data["contenido_html"] = (
                    response.css("article").get()
                    or response.css("main").get()
                    or response.css('[role="main"]').get()
                )

            # Extraer metadata adicional
            self.extract_metadata(response, article_data)

            # Actualizar fecha si se encontró en la página
            fecha = self._extract_date(response)
            if fecha:
                article_data["fecha_publicacion"] = fecha.isoformat()

        except Exception as e:
            self.logger.error(f"Error extrayendo contenido de {response.url}: {e}")

        self.articles_scraped += 1
        self.logger.info(
            f"Artículo {self.articles_scraped} extraído: {article_data.get('titular', 'Sin título')}"
        )

        yield article_data

    def extract_generic_content(self, response) -> str:
        """Extracción genérica de contenido cuando no hay selectores específicos"""
        # Intentar encontrar el contenido principal
        content_selectors = [
            "article",
            "main",
            '[role="main"]',
            ".post-content",
            ".entry-content",
            ".article-body",
            ".story-body",
            "#content",
        ]

        for selector in content_selectors:
            content = response.css(f"{selector} ::text").getall()
            if content:
                return " ".join(content).strip()

        # Fallback: extraer todos los párrafos
        paragraphs = response.css("p::text").getall()
        return " ".join(paragraphs).strip()

    def _extract_date(self, response) -> Optional[datetime]:
        """Intenta extraer la fecha de publicación del artículo"""
        # Buscar en meta tags comunes
        date_selectors = [
            'meta[property="article:published_time"]::attr(content)',
            'meta[name="publish_date"]::attr(content)',
            'meta[name="DC.date.issued"]::attr(content)',
            "time[datetime]::attr(datetime)",
            "time[pubdate]::attr(datetime)",
        ]

        for selector in date_selectors:
            date_str = response.css(selector).get()
            if date_str:
                try:
                    # Intentar parsear ISO format
                    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except:
                    try:
                        # Intentar otros formatos comunes
                        return datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")
                    except:
                        pass

        return None

    def extract_metadata(self, response, article_data: Dict[str, Any]):
        """Extrae metadata adicional de la página"""
        # Open Graph
        og_mappings = {
            "og_title": 'meta[property="og:title"]::attr(content)',
            "og_description": 'meta[property="og:description"]::attr(content)',
            "og_image": 'meta[property="og:image"]::attr(content)',
            "og_type": 'meta[property="og:type"]::attr(content)',
        }

        for key, selector in og_mappings.items():
            value = response.css(selector).get()
            if value:
                article_data["metadata"][key] = value

        # Si no hay imagen principal, usar og:image
        if (
            "imagen_principal" not in article_data
            and "og_image" in article_data["metadata"]
        ):
            article_data["imagen_principal"] = article_data["metadata"]["og_image"]

        # Schema.org/JSON-LD
        json_ld = response.css('script[type="application/ld+json"]::text').getall()
        if json_ld:
            article_data["metadata"]["structured_data"] = json_ld

    def handle_error(self, failure):
        """Maneja errores durante el scraping"""
        self.logger.error(f"Error en request: {failure.value}")

        # Log del tipo de error
        from scrapy.spidermiddlewares.httperror import HttpError
        from twisted.internet.error import DNSLookupError, TimeoutError

        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error(f"HTTP Error {response.status} en {response.url}")
        elif failure.check(DNSLookupError):
            self.logger.error(f"DNS Error: {failure.request.url}")
        elif failure.check(TimeoutError):
            self.logger.error(f"Timeout: {failure.request.url}")

    def spider_closed(self, spider):
        """Llamado cuando el spider termina"""
        stats = spider.crawler.stats.get_stats()

        self.logger.info(
            f"""
        ========== RESUMEN DE SCRAPING RSS ==========
        Spider: {spider.name}
        Medio: {self.medio_info['medio']}
        Sección: {self.medio_info['seccion']}
        RSS URL: {self.rss_url}
        Artículos extraídos: {self.articles_scraped}
        Duración: {stats.get('elapsed_time_seconds', 0):.2f} segundos
        Requests exitosos: {stats.get('downloader/response_status_count/200', 0)}
        Requests fallidos: {stats.get('downloader/response_status_count/404', 0) + stats.get('downloader/response_status_count/500', 0)}
        Errores de red: {stats.get('downloader/exception_count', 0)}
        Items generados: {stats.get('item_scraped_count', 0)}
        ============================================
        """
        )