"""
Configuración optimizada de settings para spiders de desempeño.
"""

# Configuración base optimizada
OPTIMIZED_SPIDER_SETTINGS = {
    # === CONCURRENCIA OPTIMIZADA ===
    'CONCURRENT_REQUESTS': 16,  # Aumentado de 8
    'CONCURRENT_REQUESTS_PER_DOMAIN': 4,  # Aumentado de 2
    'REACTOR_THREADPOOL_MAXSIZE': 20,  # Para mejor manejo de I/O
    
    # === TIMEOUTS OPTIMIZADOS ===
    'DOWNLOAD_TIMEOUT': 15,  # Reducido de 30 a 15 segundos
    'DOWNLOAD_DELAY': 1,  # Reducido de 2 a 1 segundo
    'RANDOMIZE_DOWNLOAD_DELAY': True,  # 0.5 * to 1.5 * DOWNLOAD_DELAY
    
    # === AUTOTHROTTLE MEJORADO ===
    'AUTOTHROTTLE_ENABLED': True,
    'AUTOTHROTTLE_START_DELAY': 1,  # Reducido de 5 a 1
    'AUTOTHROTTLE_MAX_DELAY': 30,  # Reducido de 60 a 30
    'AUTOTHROTTLE_TARGET_CONCURRENCY': 2.0,  # Aumentado de 1.0
    'AUTOTHROTTLE_DEBUG': False,  # Solo en desarrollo
    
    # === RETRY OPTIMIZADO ===
    'RETRY_ENABLED': True,
    'RETRY_TIMES': 2,  # Reducido de 3 a 2
    'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429, 522, 524],
    'RETRY_PRIORITY_ADJUST': -1,  # Menor prioridad para retries
    
    # === MIDDLEWARE OPTIMIZADO ===
    'DOWNLOADER_MIDDLEWARES': {
        'scrapy_crawl_once.CrawlOnceMiddleware': 50,
        
        # Robots.txt optimizado
        'scrapy.downloadermiddlewares.robotstxt.RobotsTxtMiddleware': 100,
        
        # User agent rotation
        'scrapy_user_agents.middlewares.RandomUserAgentMiddleware': 400,
        
        # Rate limiting (solo para debugging)
        # 'scraper_core.middlewares.rate_limit_monitor.RateLimitMonitorMiddleware': 543,
        
        # Playwright optimizado (deshabilitado por defecto)
        'scraper_core.middlewares.playwright_optimized_middleware.PlaywrightOptimizedMiddleware': 550,
        
        # Deshabilitamos el middleware problemático
        'scraper_core.middlewares.playwright_custom_middleware.PlaywrightCustomDownloaderMiddleware': None,
    },
    
    # === CACHE INTELIGENTE ===
    'HTTPCACHE_ENABLED': True,
    'HTTPCACHE_EXPIRATION_SECS': 3600,  # 1 hora
    'HTTPCACHE_DIR': 'httpcache',
    'HTTPCACHE_IGNORE_HTTP_CODES': [404, 500, 502, 503, 504],
    'HTTPCACHE_POLICY': 'scrapy.extensions.httpcache.RFC2616Policy',
    
    # === COMPRESSION ===
    'COMPRESSION_ENABLED': True,
    
    # === PLAYWRIGHT OPTIMIZADO ===
    'ENABLE_PLAYWRIGHT_MIDDLEWARE': False,  # Deshabilitado por defecto
    'USE_PLAYWRIGHT_FOR_EMPTY_CONTENT': False,  # Solo cuando sea necesario
    'PLAYWRIGHT_MAX_RETRIES': 1,
    'PLAYWRIGHT_TIMEOUT': 15000,  # 15 segundos
    'PLAYWRIGHT_ENABLE_FALLBACK': True,
    
    # === LOGGING OPTIMIZADO ===
    'LOG_LEVEL': 'INFO',
    'LOG_SHORT_NAMES': True,  # Logs más concisos
    
    # === ESTADÍSTICAS ===
    'STATS_CLASS': 'scrapy.statscollectors.MemoryStatsCollector',
}

# Configuración específica por tipo de spider
SPIDER_TYPE_CONFIGS = {
    'news_fast': {
        **OPTIMIZED_SPIDER_SETTINGS,
        'CONCURRENT_REQUESTS': 32,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 8,
        'DOWNLOAD_DELAY': 0.5,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 4.0,
        'HTTPCACHE_EXPIRATION_SECS': 1800,  # 30 minutos
    },
    
    'news_respectful': {
        **OPTIMIZED_SPIDER_SETTINGS,
        'CONCURRENT_REQUESTS': 8,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'DOWNLOAD_DELAY': 2,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
    },
    
    'test_performance': {
        **OPTIMIZED_SPIDER_SETTINGS,
        'HTTPCACHE_ENABLED': False,
        'LOG_LEVEL': 'WARNING',
        'ITEM_PIPELINES': {},  # Sin pipelines para testing
        'STATS_CLASS': 'scrapy.statscollectors.DummyStatsCollector',
    }
}

# Configuración específica por dominio
DOMAIN_OPTIMIZATIONS = {
    'bbc.com': {
        'DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 6,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 3.0,
    },
    
    'cnn.com': {
        'DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 6,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 3.0,
    },
    
    'reuters.com': {
        'DOWNLOAD_DELAY': 1.5,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 3,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.5,
        'USE_PLAYWRIGHT_FOR_EMPTY_CONTENT': True,  # Reuters necesita JS
    },
    
    'example.com': {
        'DOWNLOAD_DELAY': 3,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'DOWNLOAD_TIMEOUT': 10,  # Más rápido para sitios de prueba
    }
}

def get_optimized_settings(spider_type='default', domains=None):
    """
    Obtiene configuración optimizada para un tipo de spider específico.
    
    Args:
        spider_type: Tipo de spider ('news_fast', 'news_respectful', 'test_performance')
        domains: Lista de dominios para aplicar optimizaciones específicas
    
    Returns:
        dict: Configuración optimizada
    """
    base_config = SPIDER_TYPE_CONFIGS.get(spider_type, OPTIMIZED_SPIDER_SETTINGS)
    
    if domains:
        # Aplicar optimizaciones por dominio
        config = base_config.copy()
        
        # Usar la configuración más restrictiva si hay múltiples dominios
        if len(domains) > 1:
            min_delay = min(DOMAIN_OPTIMIZATIONS.get(domain, {}).get('DOWNLOAD_DELAY', 1) 
                           for domain in domains if domain in DOMAIN_OPTIMIZATIONS)
            if min_delay:
                config['DOWNLOAD_DELAY'] = min_delay
        
        return config
    
    return base_config

def apply_runtime_optimizations(spider):
    """
    Aplica optimizaciones en runtime basadas en el desempeño del spider.
    
    Args:
        spider: Instancia del spider
    """
    stats = spider.crawler.stats
    
    # Obtener estadísticas actuales
    request_count = stats.get_value('downloader/request_count', 0)
    response_count = stats.get_value('downloader/response_count', 0)
    
    if request_count > 100:  # Después de 100 requests
        # Calcular tasa de éxito
        success_rate = response_count / request_count if request_count > 0 else 0
        
        # Ajustar configuración basada en el desempeño
        if success_rate > 0.95:  # Muy buena tasa de éxito
            spider.crawler.engine.downloader.delay = max(0.5, spider.crawler.engine.downloader.delay * 0.8)
            spider.logger.info(f"High success rate ({success_rate:.2%}), reducing delay")
            
        elif success_rate < 0.8:  # Tasa de éxito baja
            spider.crawler.engine.downloader.delay *= 1.5
            spider.logger.warning(f"Low success rate ({success_rate:.2%}), increasing delay")

# Configuración de monitoreo de desempeño
PERFORMANCE_MONITORING = {
    'LOG_STATS_INTERVAL': 30,  # Log cada 30 segundos
    'MONITOR_RESPONSE_TIMES': True,
    'ALERT_SLOW_RESPONSES': 10,  # Alertar si response > 10s
    'TRACK_DOMAIN_PERFORMANCE': True,
}
