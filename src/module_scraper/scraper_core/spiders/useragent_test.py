import scrapy
import json
from collections import defaultdict


class UserAgentTestSpider(scrapy.Spider):
    """
    Spider de prueba para verificar la rotación de user agents
    usando scrapy-user-agents middleware.
    
    Este spider hace múltiples requests a httpbin.org/user-agent
    para verificar que diferentes user agents están siendo utilizados.
    """
    name = 'useragent_test'
    allowed_domains = ['httpbin.org']
    
    # URLs de prueba que devuelven el user agent utilizado
    start_urls = [
        'https://httpbin.org/user-agent'
    ] * 15  # Repetimos la URL 15 veces para hacer múltiples requests
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_agents_collected = []
        self.request_count = 0
    
    def start_requests(self):
        """Generar requests con números secuenciales para tracking"""
        for i, url in enumerate(self.start_urls):
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={'request_number': i + 1},
                dont_filter=True  # Permitir requests duplicados
            )
    
    def parse(self, response):
        """Procesar la respuesta y extraer el user agent utilizado"""
        self.request_count += 1
        request_number = response.meta.get('request_number', self.request_count)
        
        try:
            # httpbin.org/user-agent devuelve JSON con el user agent
            data = json.loads(response.text)
            user_agent = data.get('user-agent', 'Unknown')
            
            # Almacenar información del user agent
            ua_info = {
                'request_number': request_number,
                'user_agent': user_agent,
                'url': response.url
            }
            
            self.user_agents_collected.append(ua_info)
            
            self.logger.info(f"Request #{request_number}: User-Agent = {user_agent}")
            
            yield {
                'request_number': request_number,
                'user_agent': user_agent,
                'url': response.url,
                'response_status': response.status
            }
            
        except json.JSONDecodeError:
            self.logger.error(f"Request #{request_number}: Failed to parse JSON response")
            yield {
                'request_number': request_number,
                'user_agent': 'PARSE_ERROR',
                'url': response.url,
                'response_status': response.status,
                'error': 'JSON parse error'
            }
    
    def closed(self, reason):
        """
        Método llamado cuando el spider termina.
        Genera un reporte de la rotación de user agents.
        """
        self.logger.info("=" * 60)
        self.logger.info("USER AGENT ROTATION TEST REPORT")
        self.logger.info("=" * 60)
        
        if not self.user_agents_collected:
            self.logger.error("No user agents were collected!")
            return
        
        # Contar user agents únicos
        unique_user_agents = set(ua['user_agent'] for ua in self.user_agents_collected)
        
        self.logger.info(f"Total requests made: {len(self.user_agents_collected)}")
        self.logger.info(f"Unique user agents used: {len(unique_user_agents)}")
        self.logger.info(f"Rotation effectiveness: {len(unique_user_agents)}/{len(self.user_agents_collected)} = {(len(unique_user_agents)/len(self.user_agents_collected)*100):.1f}%")
        
        # Mostrar frecuencia de cada user agent
        ua_frequency = defaultdict(int)
        for ua_info in self.user_agents_collected:
            ua_frequency[ua_info['user_agent']] += 1
        
        self.logger.info("\\nUser Agent Frequency:")
        for ua, count in ua_frequency.items():
            self.logger.info(f"  {count}x: {ua}")
        
        # Verificar si la rotación es efectiva
        if len(unique_user_agents) >= 3:
            self.logger.info("\\n✅ SUCCESS: User agent rotation is working effectively!")
            self.logger.info(f"   Multiple different user agents ({len(unique_user_agents)}) were used.")
        elif len(unique_user_agents) == 1:
            self.logger.error("\\n❌ FAILURE: No user agent rotation detected!")
            self.logger.error("   Only one user agent was used for all requests.")
        else:
            self.logger.warning(f"\\n⚠️  WARNING: Limited user agent rotation detected!")
            self.logger.warning(f"   Only {len(unique_user_agents)} different user agents were used.")
        
        # Mostrar detalles de cada request
        self.logger.info("\\nDetailed Request Log:")
        for ua_info in self.user_agents_collected:
            self.logger.info(f"  Request #{ua_info['request_number']}: {ua_info['user_agent']}")
        
        self.logger.info("=" * 60)
