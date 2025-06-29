"""
SpiderGenerator - Generador de spiders usando templates Jinja2

Convierte los resultados del análisis en spiders funcionales de Scrapy,
aplicando templates específicos según la estrategia detectada.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import re

from jinja2 import Environment, FileSystemLoader, select_autoescape, Template

try:
    import black
    HAS_BLACK = True
except ImportError:
    HAS_BLACK = False
    
from .analyzer import AnalysisResult, AnalysisStrategy
from .patterns import Pattern
from .config import settings


logger = logging.getLogger(__name__)


class SpiderGenerator:
    """
    Genera spiders de Scrapy basados en análisis y templates
    """
    
    def get_evasion_config(self, protection_level: str) -> Dict[str, Any]:
        """
        Retorna configuración de evasión según nivel de protección detectado.
        Basado en best practices de Scrapy para custom_settings.
        
        Args:
            protection_level: 'basic', 'medium', 'high'
            
        Returns:
            Dict con configuración específica para el nivel
        """
        from .config import STEALTH_HEADERS
        
        if protection_level == 'high':
            return {
                'custom_headers': STEALTH_HEADERS,
                'download_delay': 3,
                'concurrent_requests': 1,
                'randomize_download_delay': True,
                'download_timeout': 60,
                'referer_enabled': True,
                'use_stealth_mode': True
            }
        elif protection_level == 'medium':
            return {
                'custom_headers': STEALTH_HEADERS,
                'download_delay': 2,
                'concurrent_requests': 2,
                'randomize_download_delay': True,
                'referer_enabled': True,
                'use_stealth_mode': True
            }
        else:  # basic
            return {
                'download_delay': 1,
                'concurrent_requests': 3,
                'use_stealth_mode': False
            }
    
    def __init__(self, templates_dir: Optional[str] = None):
        """
        Inicializa el generador con Jinja2
        
        Args:
            templates_dir: Directorio de templates (default: ./templates)
        """
        if templates_dir is None:
            templates_dir = Path(__file__).parent / "templates"
        
        self.templates_dir = Path(templates_dir)
        
        # Configurar Jinja2 Environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )
        
        # Registrar filtros personalizados
        self.env.filters['snake_case'] = self._to_snake_case
        self.env.filters['camel_case'] = self._to_camel_case
        self.env.filters['escape_quotes'] = self._escape_quotes
        
        # Configuración de Black para formateo
        if HAS_BLACK:
            self.black_mode = black.Mode(
                target_versions={black.TargetVersion.PY38},
                line_length=88,
                string_normalization=True,
                is_pyi=False,
            )
        else:
            self.black_mode = None
        
        logger.info(f"SpiderGenerator inicializado con templates en: {self.templates_dir}")
    
    def generate_spider(
        self,
        analysis: AnalysisResult,
        medio: str,
        seccion: str,
        area_geografica: str,
        tipo_medio: str,
        frecuencia_minutos: int = 60,
        additional_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Genera código de spider basado en el análisis
        
        Args:
            analysis: Resultado del análisis del sitio
            medio: Nombre del medio
            seccion: Sección del medio
            area_geografica: Área geográfica del medio
            tipo_medio: Tipo de medio (diario, revista, agencia)
            frecuencia_minutos: Frecuencia de actualización en minutos
            additional_config: Configuración adicional opcional
            
        Returns:
            Código Python del spider generado
        """
        # Generar spider_name automáticamente
        spider_name = f"{medio}_{seccion}".lower().replace(' ', '_')
        try:
            # Seleccionar template según estrategia
            template_name = self._get_template_name(analysis.strategy)
            template = self.env.get_template(template_name)
            
            # Preparar contexto para el template
            context = self._build_template_context(
                analysis,
                spider_name,
                medio,
                seccion,
                area_geografica,
                tipo_medio,
                frecuencia_minutos,
                additional_config or {}
            )
            
            # Renderizar template
            spider_code = template.render(**context)
            
            # Formatear con Black si está disponible
            if HAS_BLACK and self.black_mode:
                try:
                    spider_code = black.format_str(spider_code, mode=self.black_mode)
                except Exception as e:
                    logger.warning(f"No se pudo formatear con Black: {e}")
            else:
                logger.debug("Black no disponible, código sin formatear")
            
            logger.info(
                f"Spider generado: {spider_name} "
                f"(estrategia: {analysis.strategy.value})"
            )
            
            return spider_code
            
        except Exception as e:
            logger.error(f"Error generando spider: {e}")
            raise
    
    def save_spider(
        self,
        spider_code: str,
        spider_name: str,
        output_dir: str = "/src/module_scraper/scraper_core/spiders/",
        overwrite: bool = False
    ) -> Path:
        """
        Guarda el spider generado en un archivo
        
        Args:
            spider_code: Código del spider
            spider_name: Nombre del spider
            output_dir: Directorio de salida
            overwrite: Si sobrescribir archivo existente
            
        Returns:
            Path al archivo guardado
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        file_path = output_path / f"{spider_name}.py"
        
        if file_path.exists() and not overwrite:
            raise FileExistsError(
                f"El archivo {file_path} ya existe. "
                "Usa overwrite=True para sobrescribir."
            )
        
        file_path.write_text(spider_code, encoding='utf-8')
        logger.info(f"Spider guardado en: {file_path}")
        
        return file_path
    
    def generate_from_pattern(
        self,
        pattern: Pattern,
        medio: str,
        seccion: str,
        area_geografica: str,
        tipo_medio: str,
        frecuencia_minutos: int = 60,
        additional_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Genera spider desde un patrón existente
        
        Args:
            pattern: Patrón almacenado
            medio: Nombre del medio
            seccion: Sección del medio
            area_geografica: Área geográfica del medio
            tipo_medio: Tipo de medio (diario, revista, agencia)
            frecuencia_minutos: Frecuencia de actualización en minutos
            additional_config: Config adicional
            
        Returns:
            Código del spider
        """
        # Convertir patrón a AnalysisResult compatible
        analysis = AnalysisResult(
            url=f"https://{pattern.domain}/{pattern.section}",
            domain=pattern.domain,
            strategy=pattern.strategy,
            confidence=pattern.confidence,
            selectors=pattern.selectors,
            needs_javascript=pattern.needs_javascript,
            from_cache=True,
            pattern_id=pattern.id
        )
        
        return self.generate_spider(
            analysis,
            medio,
            seccion,
            area_geografica,
            tipo_medio,
            frecuencia_minutos,
            additional_config
        )
    
    def _get_template_name(self, strategy: AnalysisStrategy) -> str:
        """Obtiene nombre del template según estrategia"""
        template_map = {
            AnalysisStrategy.RSS: "rss_spider.j2",
            AnalysisStrategy.SCRAPING: "scraping_spider.j2",
            AnalysisStrategy.PLAYWRIGHT: "playwright_spider.j2",
            AnalysisStrategy.API: "api_spider.j2"
        }
        
        return template_map.get(strategy, "scraping_spider.j2")
    
    def _build_template_context(
        self,
        analysis: AnalysisResult,
        spider_name: str,
        medio: str,
        seccion: str,
        area_geografica: str,
        tipo_medio: str,
        frecuencia_minutos: int,
        additional_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Construye contexto para renderizar template
        """
        # Contexto base
        context = {
            # Metadata
            "spider_name": spider_name,
            "spider_class": self._to_camel_case(spider_name),
            "medio": medio,
            "seccion": seccion,
            "area_geografica": area_geografica,
            "tipo_medio": tipo_medio,
            "frecuencia_minutos": frecuencia_minutos,
            "domain": analysis.domain,
            "base_url": str(analysis.url),
            "generation_date": datetime.now().isoformat(),
            
            # Análisis
            "strategy": analysis.strategy.value,
            "confidence": analysis.confidence,
            "needs_javascript": analysis.needs_javascript,
            "from_pattern": analysis.from_cache,
            
            # Selectores
            "selectors": analysis.selectors.dict() if analysis.selectors else {},
            
            # RSS específico
            "rss_url": analysis.rss_url if hasattr(analysis, 'rss_url') else None,
            
            # Configuración adicional
            "excluded_urls": additional_config.get('excluded_urls', []),
            "follow_pagination": additional_config.get('follow_pagination', True),
            "max_pages": additional_config.get('max_pages', 100),
            "custom_settings": additional_config.get('custom_settings', {}),
            
            # Campos obligatorios del Item
            "item_fields": self._get_item_fields(),
            
            # Helpers
            "has_selector": lambda x: x in analysis.selectors.__dict__ and getattr(analysis.selectors, x),
            "get_selector": lambda x: getattr(analysis.selectors, x, None)
        }
        
        # Aplicar configuración de evasión basada en nivel de protección
        protection_level = analysis.protection_level if hasattr(analysis, 'protection_level') else 'basic'
        if protection_level != 'basic':
            evasion_config = self.get_evasion_config(protection_level)
            context.update(evasion_config)
            logger.info(f"Applied evasion config for {protection_level} protection level")
        
        # Agregar config específica
        context.update(additional_config)
        
        return context
    
    def _get_item_fields(self) -> List[Dict[str, str]]:
        """
        Obtiene campos obligatorios del Item de Scrapy
        """
        return [
            {"name": "titular", "type": "str", "required": True},
            {"name": "medio_url_principal", "type": "str", "required": True},
            {"name": "seccion", "type": "str", "required": False},
            {"name": "fecha_publicacion", "type": "str", "required": False},
            {"name": "fecha_extraccion", "type": "str", "required": True},
            {"name": "contenido", "type": "str", "required": False},
            {"name": "autor", "type": "str", "required": False},
            {"name": "url_imagen_principal", "type": "str", "required": False},
            {"name": "etiquetas", "type": "list", "required": False},
            {"name": "resumen", "type": "str", "required": False},
            {"name": "categoria", "type": "str", "required": False},
            {"name": "subcategoria", "type": "str", "required": False},
            {"name": "ubicacion_geografica", "type": "str", "required": False},
            {"name": "idioma", "type": "str", "required": False},
            {"name": "fuente_original", "type": "str", "required": False},
            {"name": "tipo_contenido", "type": "str", "required": False},
            {"name": "palabras_clave", "type": "list", "required": False},
            {"name": "multimedia", "type": "list", "required": False},
            {"name": "enlaces_relacionados", "type": "list", "required": False},
            {"name": "metadata_adicional", "type": "dict", "required": False}
        ]
    
    def _to_snake_case(self, text: str) -> str:
        """Convierte texto a snake_case"""
        # Reemplazar caracteres especiales
        text = re.sub(r'[^\w\s]', '', text)
        # Convertir a minúsculas y reemplazar espacios
        text = text.lower().replace(' ', '_')
        # Eliminar guiones bajos múltiples
        text = re.sub(r'_+', '_', text)
        return text.strip('_')
    
    def _to_camel_case(self, text: str) -> str:
        """Convierte texto a CamelCase"""
        # Primero convertir a snake_case
        snake = self._to_snake_case(text)
        # Luego a CamelCase
        components = snake.split('_')
        return ''.join(x.title() for x in components)
    
    def _escape_quotes(self, text: str) -> str:
        """Escapa comillas para uso en strings Python"""
        return text.replace('"', '\\"').replace("'", "\\'")
    
    def validate_spider(self, spider_code: str) -> bool:
        """
        Valida que el código del spider sea sintácticamente correcto
        
        Args:
            spider_code: Código a validar
            
        Returns:
            True si es válido
        """
        try:
            compile(spider_code, '<spider>', 'exec')
            return True
        except SyntaxError as e:
            logger.error(f"Error de sintaxis en spider: {e}")
            return False
    
    def get_available_templates(self) -> List[str]:
        """
        Lista templates disponibles
        
        Returns:
            Lista de nombres de templates
        """
        templates = []
        
        if self.templates_dir.exists():
            for file in self.templates_dir.glob("*.j2"):
                templates.append(file.stem)
        
        return sorted(templates)
    
    def preview_spider(
        self,
        analysis: AnalysisResult,
        medio: str,
        seccion: str,
        area_geografica: str,
        tipo_medio: str,
        frecuencia_minutos: int = 60,
        max_lines: int = 50
    ) -> str:
        """
        Genera preview del spider (primeras N líneas)
        
        Args:
            analysis: Resultado del análisis
            medio: Nombre del medio
            seccion: Sección del medio
            area_geografica: Área geográfica del medio
            tipo_medio: Tipo de medio (diario, revista, agencia)
            frecuencia_minutos: Frecuencia de actualización en minutos
            max_lines: Número máximo de líneas
            
        Returns:
            Preview del código
        """
        full_code = self.generate_spider(
            analysis, medio, seccion, area_geografica, 
            tipo_medio, frecuencia_minutos
        )
        lines = full_code.split('\n')
        
        if len(lines) <= max_lines:
            return full_code
        
        preview = '\n'.join(lines[:max_lines])
        preview += f"\n\n# ... ({len(lines) - max_lines} líneas más) ..."
        
        return preview


# Función auxiliar para testing
def test_generator():
    """Test básico del generador"""
    from .analyzer import SiteSelectors
    
    # Crear análisis de prueba
    test_analysis = AnalysisResult(
        url="https://example.com/news",
        domain="example.com",
        strategy=AnalysisStrategy.SCRAPING,
        confidence=0.85,
        selectors=SiteSelectors(
            title="h1.article-title",
            content="div.article-content",
            date="time.published",
            author="span.author"
        ),
        needs_javascript=False
    )
    
    # Crear generador
    generator = SpiderGenerator()
    
    # Generar spider
    print("Generando spider de prueba...")
    spider_code = generator.generate_spider(
        test_analysis,
        medio="Example News",
        seccion="Politics",
        area_geografica="ESPAÑA",
        tipo_medio="diario",
        frecuencia_minutos=60,
        additional_config={
            "excluded_urls": ["*/tags/*", "*/author/*"]
        }
    )
    
    # Mostrar preview
    print("\nPreview del spider:")
    print("=" * 80)
    print(generator.preview_spider(
        test_analysis,
        medio="Example News",
        seccion="Politics",
        area_geografica="ESPAÑA",
        tipo_medio="diario",
        frecuencia_minutos=60,
        max_lines=30
    ))
    
    # Validar
    is_valid = generator.validate_spider(spider_code)
    print(f"\nSpider válido: {is_valid}")
    
    # Listar templates
    print(f"\nTemplates disponibles: {generator.get_available_templates()}")


if __name__ == "__main__":
    test_generator()