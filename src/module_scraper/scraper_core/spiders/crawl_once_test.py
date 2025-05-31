import scrapy
import json
from datetime import datetime


class CrawlOnceTestSpider(scrapy.Spider):
    """
    Spider de prueba para verificar la funcionalidad de scrapy-crawl-once.
    
    Este spider hace múltiples requests al mismo endpoint para verificar
    que los duplicados son correctamente prevenidos cuando se usa
    request.meta['crawl_once'] = True.
    """
    name = 'crawl_once_test'
    allowed_domains = ['httpbin.org']
    
    # URLs de prueba - repetimos para simular crawling con duplicados
    test_urls = [
        'https://httpbin.org/json',
        'https://httpbin.org/ip',
        'https://httpbin.org/user-agent',
        'https://httpbin.org/headers',
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.first_run_items = []
        self.second_run_items = []
        self.request_count = 0
        
        # Determinar si es el primer o segundo run
        self.is_second_run = kwargs.get('second_run', 'false').lower() == 'true'
        
    def start_requests(self):
        """
        Generar requests con y sin crawl_once activado para testing.
        """
        requests = []
        
        for i, url in enumerate(self.test_urls):
            # Request normal (será procesado siempre)
            requests.append(scrapy.Request(
                url=url,
                callback=self.parse_normal,
                meta={
                    'test_type': 'normal',
                    'url_index': i,
                    'test_url': url
                },
                dont_filter=True
            ))
            
            # Request con crawl_once (será procesado solo la primera vez)
            requests.append(scrapy.Request(
                url=url,
                callback=self.parse_crawl_once,
                meta={
                    'crawl_once': True,
                    'test_type': 'crawl_once',
                    'url_index': i,
                    'test_url': url
                },
                dont_filter=True
            ))
        
        self.logger.info(f"Generated {len(requests)} requests for testing")
        return requests
    
    def parse_normal(self, response):
        """Procesar responses normales (sin crawl_once)"""
        self.request_count += 1
        
        item = {
            'url': response.url,
            'test_type': response.meta['test_type'],
            'url_index': response.meta['url_index'],
            'status': response.status,
            'timestamp': datetime.now().isoformat(),
            'is_second_run': self.is_second_run,
            'request_count': self.request_count,
            'content_length': len(response.text)
        }
        
        if self.is_second_run:
            self.second_run_items.append(item)
        else:
            self.first_run_items.append(item)
        
        self.logger.info(f"Normal request processed: {response.url} (run: {'2nd' if self.is_second_run else '1st'})")
        
        yield item
    
    def parse_crawl_once(self, response):
        """Procesar responses con crawl_once activado"""
        self.request_count += 1
        
        item = {
            'url': response.url,
            'test_type': response.meta['test_type'],
            'url_index': response.meta['url_index'],
            'status': response.status,
            'timestamp': datetime.now().isoformat(),
            'is_second_run': self.is_second_run,
            'request_count': self.request_count,
            'content_length': len(response.text),
            'crawl_once_active': True
        }
        
        if self.is_second_run:
            self.second_run_items.append(item)
        else:
            self.first_run_items.append(item)
        
        self.logger.info(f"Crawl-once request processed: {response.url} (run: {'2nd' if self.is_second_run else '1st'})")
        
        yield item
    
    def closed(self, reason):
        """
        Método llamado cuando el spider termina.
        Genera un reporte del comportamiento de crawl_once.
        """
        self.logger.info("=" * 60)
        self.logger.info("SCRAPY-CRAWL-ONCE TEST REPORT")
        self.logger.info("=" * 60)
        
        run_type = "SECOND RUN" if self.is_second_run else "FIRST RUN"
        self.logger.info(f"Test type: {run_type}")
        
        current_items = self.second_run_items if self.is_second_run else self.first_run_items
        
        # Contar items por tipo
        normal_items = [item for item in current_items if item['test_type'] == 'normal']
        crawl_once_items = [item for item in current_items if item['test_type'] == 'crawl_once']
        
        self.logger.info(f"Total items processed: {len(current_items)}")
        self.logger.info(f"Normal requests processed: {len(normal_items)}")
        self.logger.info(f"Crawl-once requests processed: {len(crawl_once_items)}")
        
        if self.is_second_run:
            # En el segundo run, deberíamos tener:
            # - Todos los requests normales (no bloqueados)
            # - Ningún request crawl_once (bloqueados por middleware)
            
            expected_normal = len(self.test_urls)
            expected_crawl_once = 0
            
            self.logger.info(f"\\nExpected results for SECOND RUN:")
            self.logger.info(f"  Normal requests: {expected_normal} (should always be processed)")
            self.logger.info(f"  Crawl-once requests: {expected_crawl_once} (should be blocked)")
            
            if len(normal_items) == expected_normal and len(crawl_once_items) == expected_crawl_once:
                self.logger.info(f"\\n✅ SUCCESS: scrapy-crawl-once is working correctly!")
                self.logger.info(f"   Normal requests were processed ({len(normal_items)}/{expected_normal})")
                self.logger.info(f"   Crawl-once requests were blocked ({len(crawl_once_items)}/{expected_crawl_once})")
            else:
                self.logger.error(f"\\n❌ FAILURE: scrapy-crawl-once is not working as expected!")
                self.logger.error(f"   Normal requests: {len(normal_items)}/{expected_normal}")
                self.logger.error(f"   Crawl-once requests: {len(crawl_once_items)}/{expected_crawl_once}")
        else:
            # En el primer run, deberíamos tener todos los requests procesados
            expected_total = len(self.test_urls) * 2  # normal + crawl_once para cada URL
            
            self.logger.info(f"\\nExpected results for FIRST RUN:")
            self.logger.info(f"  Total requests: {expected_total} (all should be processed)")
            
            if len(current_items) == expected_total:
                self.logger.info(f"\\n✅ FIRST RUN SUCCESSFUL: All requests processed ({len(current_items)}/{expected_total})")
                self.logger.info(f"   Run the spider again with second_run=true to test blocking")
            else:
                self.logger.warning(f"\\n⚠️  FIRST RUN INCOMPLETE: {len(current_items)}/{expected_total} requests processed")
        
        # Mostrar detalles de items procesados
        self.logger.info("\\nDetailed results:")
        for item in current_items:
            req_type = item['test_type']
            url_idx = item['url_index']
            self.logger.info(f"  [{req_type}] URL {url_idx}: {item['url']}")
        
        self.logger.info("=" * 60)
