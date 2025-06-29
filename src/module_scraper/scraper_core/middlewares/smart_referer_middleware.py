"""
Smart Referer Middleware para navegación natural
Simula patrones de navegación humana con referers lógicos

NOTA: Este es un DOWNLOADER middleware personalizado, diferente
del RefererMiddleware de Scrapy que es un SPIDER middleware.
"""

from urllib.parse import urlparse, urljoin
from scrapy import signals
from scrapy.exceptions import NotConfigured
from scrapy.http import Request
import logging
from typing import Dict, Optional, Union

logger = logging.getLogger(__name__)


class SmartRefererMiddleware:
    """
    Downloader Middleware que maneja referers de forma inteligente
    para simular navegación natural de usuario.
    
    Características:
    - Mantiene historial de navegación por dominio
    - Simula patrones de navegación naturales
    - Maneja transiciones entre dominios
    - Cache eficiente de últimas URLs visitadas
    """
    
    def __init__(self, settings):
        self.enabled = settings.getbool('SMART_REFERER_ENABLED', True)
        if not self.enabled:
            raise NotConfigured('Smart Referer Middleware is disabled')
        
        # Cache de última URL visitada por dominio
        self.domain_history: Dict[str, str] = {}
        
        # Máximo número de dominios a recordar
        self.max_domains = settings.getint('SMART_REFERER_MAX_DOMAINS', 100)
        
        # Si usar la homepage como referer inicial
        self.use_homepage_as_initial = settings.getbool(
            'SMART_REFERER_USE_HOMEPAGE', True
        )
        
        logger.info("Smart Referer Middleware initialized")
    
    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls(crawler.settings)
        crawler.signals.connect(
            middleware.spider_opened, 
            signal=signals.spider_opened
        )
        return middleware
    
    def spider_opened(self, spider):
        logger.info(f'Smart Referer Middleware opened for spider: {spider.name}')
    
    def process_request(self, request: Request, spider) -> Optional[Request]:
        """
        Procesa cada request para añadir un referer inteligente
        """
        # Skip si ya tiene referer
        if request.headers.get('Referer'):
            return None
        
        # Skip para ciertos tipos de requests
        if request.meta.get('dont_set_referer', False):
            return None
        
        # Obtener dominio actual
        parsed_url = urlparse(request.url)
        domain = parsed_url.netloc
        
        # Determinar referer apropiado
        referer = self._get_smart_referer(domain, request.url, parsed_url)
        
        if referer:
            request.headers['Referer'] = referer.encode('utf-8')
            logger.debug(f"Set referer: {referer} -> {request.url}")
        
        # Actualizar historial
        self._update_history(domain, request.url)
        
        return None
    
    def _get_smart_referer(self, domain: str, url: str, 
                         parsed_url) -> Optional[str]:
        """
        Determina el referer más apropiado basado en el contexto
        """
        # Si tenemos historial para este dominio
        if domain in self.domain_history:
            return self.domain_history[domain]
        
        # Para primera visita a un dominio
        if self.use_homepage_as_initial:
            # Construir URL de homepage
            homepage = f"{parsed_url.scheme}://{domain}/"
            
            # Para paths profundos, simular navegación gradual
            path_parts = parsed_url.path.strip('/').split('/')
            if len(path_parts) > 1:
                # Usar la sección principal como referer
                section_url = f"{parsed_url.scheme}://{domain}/{path_parts[0]}/"
                return section_url
            
            return homepage
        
        return None
    
    def _update_history(self, domain: str, url: str):
        """
        Actualiza el historial de navegación
        """
        # Limpiar dominios antiguos si excedemos el límite
        if len(self.domain_history) >= self.max_domains:
            # Eliminar el más antiguo (FIFO)
            oldest = next(iter(self.domain_history))
            del self.domain_history[oldest]
        
        # Actualizar con la URL actual
        self.domain_history[domain] = url
    
    def process_response(self, request, response, spider):
        """
        Opcionalmente procesar responses (no necesario para referer)
        """
        return response
    
    def process_exception(self, request, exception, spider):
        """
        Manejar excepciones (no necesario para referer)
        """
        return None