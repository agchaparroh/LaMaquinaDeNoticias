"""
SmartAnalyzer - El cerebro del sistema Spider Factory 2.0

Analiza medios y determina la mejor estrategia de extracción siguiendo el proceso:
1. ¿Tiene RSS? → No necesita análisis, estrategia RSS directa
2. ¿Ya fue analizado antes? → Usa información del cache (0 requests)
3. ¿Es un patrón conocido? → Aplica patrón existente (0 requests)
4. ¿Es nuevo? → Hace 1 análisis inteligente con Firecrawl
"""
import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, Optional, List, Tuple
from enum import Enum
from urllib.parse import urlparse, urljoin
import re

import httpx
from pydantic import BaseModel, HttpUrl, Field, validator
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import (
    get_redis_client, 
    RedisKeys, 
    settings,
    SpiderFactoryConfig
)

logger = logging.getLogger(__name__)


class AnalysisStrategy(str, Enum):
    """Estrategias de extracción disponibles"""
    RSS = "rss"
    SCRAPING = "scraping"
    PLAYWRIGHT = "playwright"  # Para sitios con JavaScript


class AnalysisConfidence(float, Enum):
    """Niveles de confianza en el análisis"""
    HIGH = 0.9      # RSS o patrón conocido con múltiples usos exitosos
    MEDIUM = 0.7    # Patrón conocido con pocos usos o análisis nuevo
    LOW = 0.5       # Análisis incierto o sitio complejo


class SiteSelectors(BaseModel):
    """Selectores detectados para un sitio"""
    title: Optional[str] = Field(None, description="Selector CSS/XPath para título")
    content: Optional[str] = Field(None, description="Selector para contenido")
    date: Optional[str] = Field(None, description="Selector para fecha")
    author: Optional[str] = Field(None, description="Selector para autor")
    links: Optional[str] = Field(None, description="Selector para enlaces de artículos")
    
    class Config:
        json_encoders = {
            str: lambda v: v if v else None
        }


class AnalysisResult(BaseModel):
    """Resultado del análisis de un sitio"""
    url: HttpUrl
    domain: str
    strategy: AnalysisStrategy
    confidence: float = Field(ge=0.0, le=1.0)
    selectors: Optional[SiteSelectors] = None
    rss_url: Optional[HttpUrl] = None
    needs_javascript: bool = False
    sample_articles: List[Dict[str, str]] = Field(default_factory=list)
    analysis_timestamp: datetime = Field(default_factory=datetime.now)
    from_cache: bool = False
    pattern_id: Optional[str] = None
    notes: Optional[str] = None
    
    # Nuevos campos obligatorios del medio
    medio: str = Field(..., description="Nombre del medio")
    seccion: str = Field(..., description="Sección del medio")
    area_geografica: str = Field(..., description="Área geográfica del medio")
    tipo_medio: str = Field(..., description="Tipo de medio: diario, revista, agencia")
    comentarios: Optional[str] = Field(None, description="Comentarios adicionales")
    frecuencia_minutos: int = Field(60, description="Frecuencia de actualización en minutos")
    
    @validator('confidence')
    def validate_confidence(cls, v):
        return round(v, 2)


class SiteAnalysisRequest(BaseModel):
    """Request para analizar un sitio"""
    url: HttpUrl
    medio: str
    seccion: str
    area_geografica: str
    tipo_medio: str
    frecuencia_minutos: int = 60
    comentarios: Optional[str] = None
    rss_url: Optional[HttpUrl] = None
    force_analysis: bool = False  # Ignorar cache y forzar nuevo análisis
    check_rss: bool = True  # Verificar si tiene RSS


class SmartAnalyzer:
    """
    Componente inteligente que decide la mejor estrategia de extracción
    """
    
    def __init__(self):
        self.redis = get_redis_client()
        self.config = settings
        self._http_client = None
        
        # Firmas específicas de protección anti-bot (basado en Context7)
        self.protection_signatures = {
            'cloudflare': {
                'headers': ['cf-ray', 'cf-cache-status', '__cf_bm', 'cf-request-id'],
                'server_patterns': ['cloudflare'],
                'content_patterns': ['checking your browser', 'cloudflare ray id']
            },
            'recaptcha': {
                'content_patterns': ['g-recaptcha', 'grecaptcha', 'recaptcha-element'],
                'script_patterns': ['google.com/recaptcha', 'recaptcha/api.js']
            },
            'rate_limiting': {
                'headers': ['x-ratelimit-limit', 'x-ratelimit-remaining', 'retry-after'],
                'status_codes': [429, 503]
            }
        }
        
    @property
    def http_client(self) -> httpx.AsyncClient:
        """Cliente HTTP con configuración optimizada"""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; SpiderFactory/2.0; +https://lamaquinadenoticias.com)"
                }
            )
        return self._http_client
    
    async def analyze(self, request: SiteAnalysisRequest) -> AnalysisResult:
        """
        Analiza un sitio siguiendo el flujo de decisión inteligente:
        1. ¿Tiene RSS? → Estrategia RSS directa
        2. ¿Está en cache? → Usar cache (0 requests)
        3. ¿Hay patrón conocido? → Aplicar patrón (0 requests)
        4. Si no → Análisis con Firecrawl (1 request)
        """
        logger.info(f"Analizando {request.url} para {request.medio}/{request.seccion}")
        
        # Extraer dominio
        parsed_url = urlparse(str(request.url))
        domain = parsed_url.netloc.lower().replace('www.', '')
        
        # 1. Si ya tiene RSS URL proporcionada, usar directamente
        if request.rss_url:
            logger.info(f"RSS proporcionado para {domain}: {request.rss_url}")
            return AnalysisResult(
                url=request.url,
                domain=domain,
                strategy=AnalysisStrategy.RSS,
                confidence=AnalysisConfidence.HIGH,
                rss_url=request.rss_url,
                from_cache=False,
                notes="RSS proporcionado por el usuario",
                # Campos obligatorios del medio
                medio=request.medio,
                seccion=request.seccion,
                area_geografica=request.area_geografica,
                tipo_medio=request.tipo_medio,
                comentarios=request.comentarios,
                frecuencia_minutos=request.frecuencia_minutos
            )
        
        # 2. Verificar si tiene RSS (si está habilitado)
        if request.check_rss and not request.force_analysis:
            rss_result = await self._check_rss(request.url, domain)
            if rss_result:
                logger.info(f"RSS detectado para {domain}: {rss_result}")
                return AnalysisResult(
                    url=request.url,
                    domain=domain,
                    strategy=AnalysisStrategy.RSS,
                    confidence=AnalysisConfidence.HIGH,
                    rss_url=rss_result,
                    from_cache=False,
                    notes="RSS detectado automáticamente",
                    # Campos obligatorios del medio
                    medio=request.medio,
                    seccion=request.seccion,
                    area_geografica=request.area_geografica,
                    tipo_medio=request.tipo_medio,
                    comentarios=request.comentarios,
                    frecuencia_minutos=request.frecuencia_minutos
                )
        
        # 3. Buscar en cache (análisis previo)
        if not request.force_analysis:
            cached_result = await self._get_cached_analysis(request.url, request.medio, request.seccion)
            if cached_result:
                logger.info(f"Usando análisis cacheado para {request.url}")
                cached_result.from_cache = True
                # Actualizar campos que podrían haber cambiado
                cached_result.medio = request.medio
                cached_result.seccion = request.seccion
                cached_result.area_geografica = request.area_geografica
                cached_result.tipo_medio = request.tipo_medio
                cached_result.comentarios = request.comentarios
                cached_result.frecuencia_minutos = request.frecuencia_minutos
                return cached_result
        
        # 4. Buscar patrón conocido para este dominio/sección
        if not request.force_analysis:
            pattern_result = await self._get_known_pattern(domain, request.seccion)
            if pattern_result:
                logger.info(f"Aplicando patrón conocido para {domain}/{request.seccion}")
                pattern_result.url = request.url
                pattern_result.from_cache = True
                # Agregar campos obligatorios del medio
                pattern_result.medio = request.medio
                pattern_result.seccion = request.seccion
                pattern_result.area_geografica = request.area_geografica
                pattern_result.tipo_medio = request.tipo_medio
                pattern_result.comentarios = request.comentarios
                pattern_result.frecuencia_minutos = request.frecuencia_minutos
                return pattern_result
        
        # 5. Análisis nuevo con Firecrawl
        logger.info(f"Ejecutando análisis nuevo para {request.url}")
        analysis_result = await self._analyze_with_firecrawl(
            request.url, 
            domain,
            request.medio,
            request.seccion,
            request.area_geografica,
            request.tipo_medio,
            request.comentarios,
            request.frecuencia_minutos
        )
        
        # Guardar en cache con TTL de 7 días
        await self._cache_analysis(request.url, analysis_result)
        
        # Si el análisis fue exitoso, guardar como patrón
        if analysis_result.confidence >= AnalysisConfidence.MEDIUM:
            await self._save_pattern(domain, request.seccion, analysis_result)
        
        return analysis_result
    
    async def _check_rss(self, url: HttpUrl, domain: str) -> Optional[HttpUrl]:
        """Verifica si el sitio tiene RSS"""
        # Primero verificar en cache
        cache_key = RedisKeys.format_key(RedisKeys.CACHE_RSS_CHECK, url=str(url))
        cached = self.redis.get(cache_key)
        
        if cached:
            data = json.loads(cached)
            if data.get('has_rss'):
                return HttpUrl(data['feed_url'])
            return None
        
        # URLs comunes de RSS para probar
        rss_paths = [
            '/rss', '/feed', '/feeds/rss', '/rss.xml', '/feed.xml',
            '/index.xml', '/atom.xml', '/feeds', '/.rss',
            f'/{domain}/rss', f'/{domain}/feed'
        ]
        
        base_url = f"{urlparse(str(url)).scheme}://{urlparse(str(url)).netloc}"
        
        try:
            # Intentar detectar RSS en la página principal
            response = await self.http_client.get(str(url))
            if response.status_code == 200:
                content = response.text.lower()
                
                # Buscar enlaces RSS en el HTML
                rss_pattern = re.compile(
                    r'<link[^>]+type=["\']application/(rss|atom)\+xml["\'][^>]+href=["\']([^"\']+)["\']',
                    re.IGNORECASE
                )
                matches = rss_pattern.findall(response.text)
                
                if matches:
                    feed_url = urljoin(base_url, matches[0][1])
                    # Verificar que el feed es válido
                    feed_response = await self.http_client.get(feed_url)
                    if feed_response.status_code == 200 and 'xml' in feed_response.headers.get('content-type', ''):
                        # Cachear resultado positivo
                        self.redis.setex(
                            cache_key,
                            self.config.cache_ttl_analysis,
                            json.dumps({"has_rss": True, "feed_url": feed_url})
                        )
                        return HttpUrl(feed_url)
            
            # Probar URLs comunes de RSS
            for rss_path in rss_paths:
                feed_url = urljoin(base_url, rss_path)
                try:
                    response = await self.http_client.get(feed_url)
                    if response.status_code == 200:
                        content_type = response.headers.get('content-type', '').lower()
                        if 'xml' in content_type or 'rss' in content_type:
                            # Cachear resultado positivo
                            self.redis.setex(
                                cache_key,
                                self.config.cache_ttl_analysis,
                                json.dumps({"has_rss": True, "feed_url": feed_url})
                            )
                            return HttpUrl(feed_url)
                except:
                    continue
            
            # Cachear resultado negativo (menos tiempo)
            self.redis.setex(
                cache_key,
                3600,  # 1 hora para resultados negativos
                json.dumps({"has_rss": False})
            )
            
        except Exception as e:
            logger.error(f"Error verificando RSS para {url}: {e}")
        
        return None
    
    async def _get_cached_analysis(self, url: HttpUrl, medio: str, seccion: str) -> Optional[AnalysisResult]:
        """Busca análisis previo en cache"""
        # Generar hash único basado en URL, medio y sección
        cache_str = f"{str(url)}:{medio}:{seccion}"
        url_hash = hashlib.md5(cache_str.encode()).hexdigest()
        cache_key = f"analysis:{url_hash}"
        
        cached_data = self.redis.get(cache_key)
        if cached_data:
            try:
                data = json.loads(cached_data)
                return AnalysisResult(**data)
            except Exception as e:
                logger.error(f"Error deserializando cache: {e}")
        
        return None
    
    async def _get_known_pattern(self, domain: str, section: str) -> Optional[AnalysisResult]:
        """
        Busca un patrón conocido para el dominio/sección
        Nueva estructura Redis:
        patterns:{dominio} → {
            "seccion": '{"strategy": "scraping", "selectors": {...}}',
            "area_geografica": "ESPAÑA",
            "tipo_medio": "diario",
            ...
        }
        """
        # Clave del dominio completo
        pattern_key = f"patterns:{domain}"
        
        # Obtener todos los datos del dominio
        domain_data = self.redis.hgetall(pattern_key)
        
        if domain_data and section.encode() in domain_data:
            try:
                # Incrementar contador de uso
                usage_key = "pattern_usage"
                self.redis.zincrby(usage_key, 1, f"{domain}:{section}")
                
                # Obtener patrón de la sección
                section_pattern = json.loads(domain_data[section.encode()].decode())
                
                # Construir selectores si existen
                selectors = None
                if section_pattern.get('selectors'):
                    selectors = SiteSelectors(**section_pattern['selectors'])
                
                # Crear resultado con los datos del patrón
                # Nota: Los campos obligatorios del medio se agregarán en el método analyze()
                return AnalysisResult(
                    url=HttpUrl("https://placeholder.com"),  # Se sobrescribirá
                    domain=domain,
                    strategy=AnalysisStrategy(section_pattern['strategy']),
                    confidence=float(section_pattern.get('confidence', 0.7)),
                    selectors=selectors,
                    needs_javascript=section_pattern.get('needs_javascript', False),
                    pattern_id=f"{domain}:{section}",
                    notes=f"Patrón conocido aplicado",
                    # Campos placeholder que se actualizarán en analyze()
                    medio="",
                    seccion=section,
                    area_geografica="",
                    tipo_medio="",
                    frecuencia_minutos=60
                )
            except Exception as e:
                logger.error(f"Error cargando patrón para {domain}/{section}: {e}")
        
        return None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _analyze_with_firecrawl(
        self, 
        url: HttpUrl, 
        domain: str,
        medio: str,
        seccion: str,
        area_geografica: str,
        tipo_medio: str,
        comentarios: Optional[str],
        frecuencia_minutos: int
    ) -> AnalysisResult:
        """
        Analiza el sitio usando Firecrawl API
        Detecta selectores y determina la mejor estrategia
        Obtiene HTML, Markdown y screenshot en 1 request
        """
        if not self.config.firecrawl_api_key:
            logger.warning("Firecrawl API key no configurada, usando análisis básico")
            return await self._basic_analysis(url, domain)
        
        try:
            # Llamar a Firecrawl API
            firecrawl_url = f"{self.config.firecrawl_base_url}/scrape"
            headers = {"Authorization": f"Bearer {self.config.firecrawl_api_key}"}
            
            payload = {
                "url": str(url),
                "formats": ["markdown", "html", "screenshot"],
                "waitFor": 2000,  # Esperar 2 segundos para JavaScript
                "onlyMainContent": True
            }
            
            response = await self.http_client.post(
                firecrawl_url,
                json=payload,
                headers=headers,
                timeout=self.config.firecrawl_timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Analizar respuesta de Firecrawl
                html_content = data.get("data", {}).get("html", "")
                markdown_content = data.get("data", {}).get("markdown", "")
                
                # Detectar si necesita JavaScript
                needs_js = self._detect_javascript_requirement(html_content)
                
                # Extraer selectores y artículos de muestra
                selectors, sample_articles = self._extract_selectors_from_content(
                    html_content, 
                    str(url)
                )
                
                # Determinar estrategia y confianza
                strategy = AnalysisStrategy.PLAYWRIGHT if needs_js else AnalysisStrategy.SCRAPING
                confidence = self._calculate_confidence(selectors, sample_articles)
                
                return AnalysisResult(
                    url=url,
                    domain=domain,
                    strategy=strategy,
                    confidence=confidence,
                    selectors=selectors,
                    needs_javascript=needs_js,
                    sample_articles=sample_articles[:5],  # Máximo 5 ejemplos
                    notes="Análisis completo con Firecrawl",
                    # Campos obligatorios del medio
                    medio=medio,
                    seccion=seccion,
                    area_geografica=area_geografica,
                    tipo_medio=tipo_medio,
                    comentarios=comentarios,
                    frecuencia_minutos=frecuencia_minutos
                )
            else:
                logger.error(f"Firecrawl API error: {response.status_code}")
                return await self._basic_analysis(
                    url, domain, medio, seccion, area_geografica, 
                    tipo_medio, comentarios, frecuencia_minutos
                )
                
        except Exception as e:
            logger.error(f"Error en análisis con Firecrawl: {e}")
            return await self._basic_analysis(url, domain)
    
    async def _basic_analysis(
        self, 
        url: HttpUrl, 
        domain: str,
        medio: str,
        seccion: str,
        area_geografica: str,
        tipo_medio: str,
        comentarios: Optional[str],
        frecuencia_minutos: int
    ) -> AnalysisResult:
        """Análisis básico sin Firecrawl"""
        try:
            response = await self.http_client.get(str(url))
            if response.status_code == 200:
                content = response.text
                
                # Análisis muy básico
                needs_js = bool(re.search(r'<script.*?(react|vue|angular)', content, re.IGNORECASE))
                
                # Selectores genéricos comunes
                selectors = SiteSelectors(
                    title="h1, h2, .title, .headline",
                    content="article, .content, .article-body, .post-content",
                    date="time, .date, .published",
                    links="a[href*='/20'], a[href*='/articulo'], a[href*='/news']"
                )
                
                return AnalysisResult(
                    url=url,
                    domain=domain,
                    strategy=AnalysisStrategy.PLAYWRIGHT if needs_js else AnalysisStrategy.SCRAPING,
                    confidence=AnalysisConfidence.LOW,
                    selectors=selectors,
                    needs_javascript=needs_js,
                    notes="Análisis básico sin Firecrawl",
                    # Campos obligatorios del medio
                    medio=medio,
                    seccion=seccion,
                    area_geografica=area_geografica,
                    tipo_medio=tipo_medio,
                    comentarios=comentarios,
                    frecuencia_minutos=frecuencia_minutos
                )
        except Exception as e:
            logger.error(f"Error en análisis básico: {e}")
        
        # Fallback
        return AnalysisResult(
            url=url,
            domain=domain,
            strategy=AnalysisStrategy.SCRAPING,
            confidence=AnalysisConfidence.LOW,
            selectors=SiteSelectors(),
            notes="Análisis fallido, usando valores por defecto",
            # Campos obligatorios del medio
            medio=medio,
            seccion=seccion,
            area_geografica=area_geografica,
            tipo_medio=tipo_medio,
            comentarios=comentarios,
            frecuencia_minutos=frecuencia_minutos
        )
    
    def _detect_javascript_requirement(self, html_content: str) -> bool:
        """Detecta si el sitio requiere JavaScript para renderizar contenido"""
        js_indicators = [
            r'<div[^>]+id="root"[^>]*>\s*</div>',  # React típico
            r'<div[^>]+id="app"[^>]*>\s*</div>',   # Vue típico
            r'ng-app',                              # Angular
            r'__NEXT_DATA__',                       # Next.js
            r'window\.__INITIAL_STATE__',           # SSR común
            r'<noscript>.*necesita.*javascript',   # Aviso explícito
        ]
        
        for pattern in js_indicators:
            if re.search(pattern, html_content, re.IGNORECASE):
                return True
        
        # Verificar si hay muy poco contenido visible (posible SPA)
        text_content = re.sub(r'<[^>]+>', '', html_content)
        if len(text_content.strip()) < 500:
            return True
        
        return False
    
    def _extract_selectors_from_content(
        self, 
        html_content: str, 
        base_url: str
    ) -> Tuple[SiteSelectors, List[Dict[str, str]]]:
        """
        Extrae selectores inteligentemente del contenido HTML
        Retorna selectores detectados y artículos de muestra
        """
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html_content, 'html.parser')
        selectors = SiteSelectors()
        sample_articles = []
        
        # Patrones comunes de selectores
        title_candidates = [
            'h1.title', 'h1.headline', 'h2.title', 'h2.headline',
            '.article-title', '.post-title', '.entry-title',
            'h1[itemprop="headline"]', '[class*="title"]'
        ]
        
        content_candidates = [
            'article', '.article-content', '.article-body', 
            '.post-content', '.entry-content', '[itemprop="articleBody"]',
            '.content', 'main', '[class*="content"]'
        ]
        
        date_candidates = [
            'time', '.date', '.published', '.post-date',
            '[datetime]', '[itemprop="datePublished"]',
            '[class*="date"]', '[class*="time"]'
        ]
        
        link_candidates = [
            'a[href*="/article"]', 'a[href*="/news"]', 
            'a[href*="/post"]', 'a[href*="/20"]',  # URLs con año
            '.article-link', 'h2 a', 'h3 a'
        ]
        
        # Detectar selectores probando candidatos
        for selector in title_candidates:
            elements = soup.select(selector)
            if elements:
                selectors.title = selector
                break
        
        for selector in content_candidates:
            elements = soup.select(selector)
            if elements and len(elements[0].get_text(strip=True)) > 100:
                selectors.content = selector
                break
        
        for selector in date_candidates:
            elements = soup.select(selector)
            if elements:
                selectors.date = selector
                break
        
        # Detectar enlaces de artículos y extraer muestras
        for selector in link_candidates:
            links = soup.select(selector)
            if len(links) >= 3:  # Al menos 3 enlaces para ser válido
                selectors.links = selector
                
                # Extraer artículos de muestra
                for link in links[:5]:
                    href = link.get('href', '')
                    if href:
                        full_url = urljoin(base_url, href)
                        title = link.get_text(strip=True)
                        if title and len(title) > 10:
                            sample_articles.append({
                                "url": full_url,
                                "title": title
                            })
                break
        
        return selectors, sample_articles
    
    def detect_protection_level(self, response_data: Dict[str, Any]) -> str:
        """
        Detecta nivel de protección basándose en headers, status y contenido.
        Implementación basada en documentación oficial de Scrapy.
        
        Args:
            response_data: Dict con 'headers', 'status_code', 'content'
            
        Returns:
            str: 'basic', 'medium', 'high'
        """
        headers = response_data.get('headers', {})
        status_code = response_data.get('status_code', 200)
        content = response_data.get('content', '')
        
        protection_score = 0
        detected_systems = []
        
        # Normalizar headers para comparación case-insensitive
        headers_lower = {k.lower(): str(v).lower() for k, v in headers.items()}
        content_lower = content.lower()
        
        # Verificar firmas específicas
        for system, signatures in self.protection_signatures.items():
            system_detected = False
            
            # Check headers
            for header in signatures.get('headers', []):
                if header.lower() in headers_lower:
                    protection_score += 3
                    system_detected = True
                    break
            
            # Check server patterns
            server_header = headers_lower.get('server', '')
            for pattern in signatures.get('server_patterns', []):
                if pattern in server_header:
                    protection_score += 3
                    system_detected = True
                    break
            
            # Check content patterns
            for pattern in signatures.get('content_patterns', []):
                if pattern in content_lower:
                    protection_score += 2
                    system_detected = True
                    break
            
            # Check status codes
            if status_code in signatures.get('status_codes', []):
                protection_score += 4
                system_detected = True
            
            if system_detected:
                detected_systems.append(system)
        
        # Determinar nivel basado en score y sistemas detectados
        if protection_score >= 6 or 'cloudflare' in detected_systems:
            level = 'high'
        elif protection_score >= 3 or 'rate_limiting' in detected_systems:
            level = 'medium'
        else:
            level = 'basic'
        
        if detected_systems:
            logger.info(f"Protection systems detected: {', '.join(detected_systems)}")
        
        logger.info(f"Protection level: {level} (score: {protection_score})")
        return level
    
    def _calculate_confidence(
        self, 
        selectors: SiteSelectors, 
        sample_articles: List[Dict[str, str]]
    ) -> float:
        """Calcula la confianza basada en los selectores encontrados"""
        confidence = 0.5  # Base
        
        # Aumentar confianza por cada selector encontrado
        if selectors.title:
            confidence += 0.1
        if selectors.content:
            confidence += 0.15
        if selectors.date:
            confidence += 0.05
        if selectors.links:
            confidence += 0.1
        
        # Bonus por artículos de muestra
        if len(sample_articles) >= 3:
            confidence += 0.1
        
        return min(confidence, 0.95)  # Máximo 0.95 para análisis nuevos
    
    async def _cache_analysis(self, url: HttpUrl, result: AnalysisResult):
        """Guarda el análisis en cache con TTL de 7 días"""
        # Generar hash único basado en URL, medio y sección
        cache_str = f"{str(url)}:{result.medio}:{result.seccion}"
        url_hash = hashlib.md5(cache_str.encode()).hexdigest()
        
        # Nueva estructura de cache según plan
        cache_key = f"analysis:{url_hash}"
        
        # Serializar resultado
        data = result.dict()
        data['analysis_timestamp'] = data['analysis_timestamp'].isoformat()
        if data.get('url'):
            data['url'] = str(data['url'])
        if data.get('rss_url'):
            data['rss_url'] = str(data['rss_url'])
        
        # TTL de 7 días (604800 segundos)
        TTL_7_DAYS = 604800
        
        self.redis.setex(
            cache_key,
            TTL_7_DAYS,
            json.dumps(data)
        )
        logger.info(f"Análisis cacheado para {url} con TTL de 7 días")
    
    async def _save_pattern(
        self, 
        domain: str, 
        section: str, 
        result: AnalysisResult
    ):
        """
        Guarda un patrón exitoso para reutilización futura
        Nueva estructura:
        patterns:{dominio} → {
            "seccion": '{"strategy": "scraping", "selectors": {...}}',
            "area_geografica": "ESPAÑA",
            "tipo_medio": "diario",
            ...
        }
        """
        # Clave del dominio
        pattern_key = f"patterns:{domain}"
        
        # Datos del patrón de la sección
        section_pattern = {
            "strategy": result.strategy.value,
            "confidence": result.confidence,
            "needs_javascript": result.needs_javascript,
            "last_used": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat()
        }
        
        if result.selectors:
            section_pattern["selectors"] = result.selectors.dict()
        
        # Guardar patrón de la sección
        self.redis.hset(pattern_key, section, json.dumps(section_pattern))
        
        # Guardar metadata del dominio si no existe
        existing_data = self.redis.hgetall(pattern_key)
        if b'area_geografica' not in existing_data:
            # Guardar metadata del medio
            metadata = {
                "area_geografica": result.area_geografica,
                "tipo_medio": result.tipo_medio,
                "comentarios": result.comentarios or ""
            }
            for key, value in metadata.items():
                self.redis.hset(pattern_key, key, value)
        
        # Inicializar contador de uso
        usage_key = "pattern_usage"
        self.redis.zadd(usage_key, {f"{domain}:{section}": 1})
        
        logger.info(f"Patrón guardado para {domain}/{section}")
    
    async def close(self):
        """Cierra recursos"""
        if self._http_client:
            await self._http_client.aclose()


# Función auxiliar para testing
async def test_analyzer():
    """Función de test para el analyzer"""
    analyzer = SmartAnalyzer()
    
    try:
        # Test con un sitio de ejemplo
        request = SiteAnalysisRequest(
            url="https://elpais.com/internacional",
            section_name="internacional"
        )
        
        result = await analyzer.analyze(request)
        print(f"Análisis completado:")
        print(f"- Estrategia: {result.strategy}")
        print(f"- Confianza: {result.confidence}")
        print(f"- Necesita JS: {result.needs_javascript}")
        print(f"- Desde cache: {result.from_cache}")
        
        if result.selectors:
            print(f"- Selectores encontrados: {result.selectors.dict()}")
        
        if result.sample_articles:
            print(f"- Artículos de muestra: {len(result.sample_articles)}")
            
    finally:
        await analyzer.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_analyzer())