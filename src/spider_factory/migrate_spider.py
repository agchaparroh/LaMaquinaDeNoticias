"""
Script para adaptar spiders generados al formato de module_scraper
Convierte spiders de Scrapy estándar a BaseArticleSpider
"""
import os
import re
import sys
import shutil
from pathlib import Path
from datetime import datetime
import argparse
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SpiderMigrator:
    """Migra spiders generados al formato de module_scraper"""
    
    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        # Crear directorio de salida si no existe
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Directorio de backup
        self.backup_dir = self.output_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
    
    def migrate_spider(self, spider_file: Path) -> bool:
        """
        Migra un spider individual al formato BaseArticleSpider
        
        Args:
            spider_file: Path al archivo del spider
            
        Returns:
            bool: True si la migración fue exitosa
        """
        try:
            logger.info(f"Migrando spider: {spider_file.name}")
            
            # Leer contenido original
            with open(spider_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Guardar backup
            backup_path = self.backup_dir / f"{spider_file.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
            shutil.copy2(spider_file, backup_path)
            logger.info(f"Backup guardado en: {backup_path}")
            
            # Aplicar transformaciones
            migrated_content = self._apply_migrations(content, spider_file.stem)
            
            # Guardar spider migrado
            output_path = self.output_dir / spider_file.name
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(migrated_content)
            
            logger.info(f"✅ Spider migrado exitosamente: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error migrando {spider_file.name}: {str(e)}")
            return False
    
    def _apply_migrations(self, content: str, spider_name: str) -> str:
        """Aplica todas las transformaciones necesarias"""
        
        # 1. Cambiar imports
        content = self._migrate_imports(content)
        
        # 2. Cambiar clase base
        content = self._migrate_class_definition(content)
        
        # 3. Actualizar custom_settings
        content = self._migrate_custom_settings(content)
        
        # 4. Adaptar métodos parse
        content = self._migrate_parse_methods(content)
        
        # 5. Agregar campos requeridos
        content = self._add_required_fields(content, spider_name)
        
        return content
    
    def _migrate_imports(self, content: str) -> str:
        """Migra los imports al formato de module_scraper"""
        
        # Cambiar import de Spider base
        content = re.sub(
            r'from scrapy import Spider',
            'from module_scraper.spiders.base_article_spider import BaseArticleSpider',
            content
        )
        
        # Agregar imports necesarios si no existen
        if 'from module_scraper.items import ArticuloItem' not in content:
            # Buscar donde insertar después de los imports de scrapy
            import_pattern = r'(import scrapy.*?\n)'
            content = re.sub(
                import_pattern,
                r'\1from module_scraper.items import ArticuloItem, ArticuloLoader\n',
                content,
                flags=re.MULTILINE
            )
        
        return content
    
    def _migrate_class_definition(self, content: str) -> str:
        """Cambia la clase base de Spider a BaseArticleSpider"""
        
        # Cambiar herencia de clase
        content = re.sub(
            r'class (\w+)\(Spider\)',
            r'class \1(BaseArticleSpider)',
            content
        )
        
        return content
    
    def _migrate_custom_settings(self, content: str) -> str:
        """Actualiza custom_settings para incluir pipelines de Supabase"""
        
        # Buscar custom_settings existente
        settings_pattern = r'custom_settings\s*=\s*{([^}]*)}'
        
        def replace_settings(match):
            existing_settings = match.group(1)
            
            # Si no tiene ITEM_PIPELINES, agregarlo
            if 'ITEM_PIPELINES' not in existing_settings:
                # Agregar pipelines de Supabase
                new_pipelines = """
        'ITEM_PIPELINES': {
            'module_scraper.pipelines.ValidationPipeline': 100,
            'module_scraper.pipelines.CleaningPipeline': 200,
            'module_scraper.pipelines.SupabasePipeline': 300,
        },"""
                
                # Insertar al inicio del diccionario
                return f"custom_settings = {{{new_pipelines}\n        {existing_settings.strip()}\n    }}"
            
            return match.group(0)
        
        content = re.sub(settings_pattern, replace_settings, content, flags=re.DOTALL)
        
        # Si no existe custom_settings, agregarlo después de la definición de clase
        if 'custom_settings' not in content:
            class_pattern = r'(class \w+\(BaseArticleSpider\):\s*\n)'
            settings_block = '''    
    custom_settings = {
        'ITEM_PIPELINES': {
            'module_scraper.pipelines.ValidationPipeline': 100,
            'module_scraper.pipelines.CleaningPipeline': 200,
            'module_scraper.pipelines.SupabasePipeline': 300,
        },
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 1,
        'ROBOTSTXT_OBEY': True,
    }
    
'''
            content = re.sub(class_pattern, r'\1' + settings_block, content)
        
        return content
    
    def _migrate_parse_methods(self, content: str) -> str:
        """Adapta los métodos parse para usar ArticuloItem"""
        
        # Cambiar yield de diccionarios a ArticuloItem
        dict_yield_pattern = r'yield\s*{\s*([^}]+)\s*}'
        
        def replace_yield(match):
            fields = match.group(1)
            
            # Convertir a ArticuloItem
            item_code = "loader = ArticuloLoader(item=ArticuloItem(), response=response)\n"
            
            # Parsear campos del diccionario
            field_lines = []
            for line in fields.strip().split('\n'):
                if ':' in line:
                    # Extraer clave y valor
                    key_value = line.strip().rstrip(',')
                    if key_value:
                        parts = key_value.split(':', 1)
                        if len(parts) == 2:
                            key = parts[0].strip().strip('"\'')
                            value = parts[1].strip()
                            
                            # Mapear campos a ArticuloItem
                            field_mapping = {
                                'title': 'titular',
                                'titulo': 'titular',
                                'content': 'contenido',
                                'contenido': 'contenido',
                                'url': 'link',
                                'link': 'link',
                                'date': 'fecha_publicacion',
                                'fecha': 'fecha_publicacion',
                                'author': 'autor',
                                'autor': 'autor'
                            }
                            
                            mapped_field = field_mapping.get(key, key)
                            field_lines.append(f"        loader.add_value('{mapped_field}', {value})")
            
            # Agregar campos requeridos
            field_lines.append("        loader.add_value('medio_url', response.url)")
            field_lines.append("        loader.add_value('seccion', getattr(self, 'section_name', 'general'))")
            
            return f"        {item_code}        " + '\n        '.join(field_lines) + "\n        yield loader.load_item()"
        
        content = re.sub(dict_yield_pattern, replace_yield, content, flags=re.DOTALL)
        
        return content
    
    def _add_required_fields(self, content: str, spider_name: str) -> str:
        """Agrega campos requeridos por BaseArticleSpider si no existen"""
        
        # Verificar si tiene allowed_domains
        if 'allowed_domains' not in content:
            # Extraer dominio del nombre del spider
            domain_match = re.search(r'start_urls\s*=\s*\[(.*?)\]', content, re.DOTALL)
            if domain_match:
                urls = domain_match.group(1)
                # Extraer primer URL
                url_match = re.search(r'["\']https?://([^/"\']+)', urls)
                if url_match:
                    domain = url_match.group(1)
                    # Insertar allowed_domains después de name
                    content = re.sub(
                        r'(name\s*=\s*["\'][^"\']+["\'])',
                        f'\\1\n    allowed_domains = ["{domain}"]',
                        content
                    )
        
        # Agregar medio_url si no existe
        if 'medio_url' not in content:
            class_pattern = r'(class \w+\(BaseArticleSpider\):\s*\n)'
            content = re.sub(
                class_pattern,
                r'\1    medio_url = None  # Se establecerá dinámicamente\n',
                content
            )
        
        return content
    
    def migrate_all(self) -> dict:
        """Migra todos los spiders en el directorio de entrada"""
        
        results = {
            'successful': [],
            'failed': [],
            'total': 0
        }
        
        # Buscar archivos Python
        spider_files = list(self.input_dir.glob('*.py'))
        results['total'] = len(spider_files)
        
        if not spider_files:
            logger.warning(f"No se encontraron spiders en: {self.input_dir}")
            return results
        
        logger.info(f"Encontrados {len(spider_files)} spiders para migrar")
        
        for spider_file in spider_files:
            if self.migrate_spider(spider_file):
                results['successful'].append(spider_file.name)
            else:
                results['failed'].append(spider_file.name)
        
        return results


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Migra spiders de Spider Factory al formato de module_scraper'
    )
    
    parser.add_argument(
        '--input',
        '-i',
        default='./generated_spiders',
        help='Directorio con spiders generados (default: ./generated_spiders)'
    )
    
    parser.add_argument(
        '--output',
        '-o',
        default='../module_scraper/scraper_core/spiders',
        help='Directorio de salida para spiders migrados'
    )
    
    parser.add_argument(
        '--spider',
        '-s',
        help='Migrar solo un spider específico'
    )
    
    args = parser.parse_args()
    
    # Crear migrador
    migrator = SpiderMigrator(args.input, args.output)
    
    if args.spider:
        # Migrar spider específico
        spider_path = Path(args.input) / args.spider
        if not spider_path.exists():
            logger.error(f"Spider no encontrado: {spider_path}")
            return 1
        
        success = migrator.migrate_spider(spider_path)
        return 0 if success else 1
    else:
        # Migrar todos
        results = migrator.migrate_all()
        
        # Mostrar resumen
        print("\n" + "=" * 50)
        print("📊 RESUMEN DE MIGRACIÓN")
        print("=" * 50)
        print(f"Total spiders: {results['total']}")
        print(f"✅ Exitosos: {len(results['successful'])}")
        print(f"❌ Fallidos: {len(results['failed'])}")
        
        if results['failed']:
            print("\nSpiders con errores:")
            for spider in results['failed']:
                print(f"  - {spider}")
        
        return 0 if not results['failed'] else 1


if __name__ == "__main__":
    sys.exit(main())