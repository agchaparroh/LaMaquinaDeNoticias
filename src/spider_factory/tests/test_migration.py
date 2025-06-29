#!/usr/bin/env python3
"""
Test para verificar que los scripts de migración funcionan correctamente
"""
import sys
import tempfile
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.migrate_spider import SpiderMigrator
from src.validate_spiders import SpiderValidator


def create_test_spider():
    """Crea un spider de prueba antiguo (sin campos nuevos)"""
    content = '''# -*- coding: utf-8 -*-
import scrapy
from scrapy.spiders import Spider

class ElPaisNewsSpider(Spider):
    name = "elpais-news"
    allowed_domains = ["elpais.com"]
    start_urls = ["https://elpais.com/internacional/"]
    
    def parse(self, response):
        articles = response.css("article")
        
        for article in articles:
            item = {}
            item['titulo'] = article.css("h2::text").get()
            item['url'] = article.css("a::attr(href)").get()
            item['fecha'] = article.css("time::attr(datetime)").get()
            
            yield item
'''
    return content


def test_migration():
    """Prueba el proceso de migración"""
    print("=== TEST DE MIGRACIÓN DE SPIDERS ===\n")
    
    # Crear directorio temporal
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Crear spider de prueba
        test_spider_path = tmpdir / "test_spider.py"
        test_spider_path.write_text(create_test_spider())
        print(f"✅ Spider de prueba creado: {test_spider_path.name}")
        
        # Validar antes de migrar
        validator = SpiderValidator()
        pre_validation = validator.validate_spider_file(test_spider_path)
        
        print("\n📋 Validación PRE-migración:")
        print(f"   Válido: {'✅' if pre_validation['valid'] else '❌'}")
        if pre_validation['errors']:
            print("   Errores encontrados:")
            for error in pre_validation['errors'][:5]:
                print(f"     - {error}")
                
        # Migrar
        print("\n🔄 Ejecutando migración...")
        migrator = SpiderMigrator(backup_dir=str(tmpdir / "backups"))
        
        # Detectar tipo
        spider_type, metadata = migrator.detect_spider_type(test_spider_path)
        print(f"   Tipo detectado: {spider_type}")
        print(f"   Metadata: {metadata}")
        
        # Migrar
        metadata['medio'] = 'El País'
        metadata['seccion'] = 'Internacional'
        success = migrator.migrate_to_v2(test_spider_path, metadata, dry_run=False)
        
        if success:
            print("   ✅ Migración completada")
            
            # Validar después de migrar
            post_validation = migrator.validate_migration(test_spider_path)
            
            print("\n📋 Validación POST-migración:")
            all_valid = True
            for check, passed in post_validation.items():
                status = "✅" if passed else "❌"
                print(f"   {status} {check}")
                if not passed:
                    all_valid = False
                    
            # Mostrar contenido migrado
            print("\n📄 Contenido migrado (primeras 30 líneas):")
            print("-" * 60)
            migrated_content = test_spider_path.read_text()
            lines = migrated_content.split('\n')[:30]
            for i, line in enumerate(lines, 1):
                print(f"{i:3d} | {line}")
            if len(migrated_content.split('\n')) > 30:
                print("     | ... (contenido truncado)")
            print("-" * 60)
            
            if all_valid:
                print("\n✅ TEST EXITOSO: El spider fue migrado correctamente")
                return True
            else:
                print("\n⚠️  TEST PARCIAL: El spider fue migrado pero hay validaciones pendientes")
                return False
        else:
            print("   ❌ Error en la migración")
            return False


def test_validation_only():
    """Prueba solo la validación"""
    print("\n=== TEST DE VALIDACIÓN ===\n")
    
    # Crear spider válido
    valid_spider = '''# -*- coding: utf-8 -*-
import scrapy

class ElPaisInternacionalSpider(scrapy.Spider):
    name = "el_pais_internacional"
    medio = "El País"
    seccion = "Internacional"
    area_geografica = "ESPAÑA"
    tipo_medio = "diario"
    
    custom_settings = {
        'CRAWL_ONCE_ENABLED': True,
        'CRAWL_ONCE_PATH': f'.scrapy/crawl_once/el_pais_internacional',
        'CRAWL_ONCE_DEFAULT': False,
    }
    
    def parse(self, response):
        item = {}
        item['titular'] = response.css("h1::text").get()
        item['medio'] = self.medio
        item['seccion'] = self.seccion
        item['area_geografica'] = self.area_geografica
        item['tipo_medio'] = self.tipo_medio
        item['medio_url_principal'] = response.url
        item['fecha_publicacion'] = response.css("time::text").get()
        item['contenido_texto'] = response.css("p::text").getall()
        item['contenido_html'] = response.css("article").get()
        item['fuente'] = 'spider_factory_2.0'
        item['metadata'] = {
            'spider_type': 'scraping',
            'extraction_method': 'css',
            'section_filter': True
        }
        yield item
'''
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        valid_path = tmpdir / "valid_spider.py"
        valid_path.write_text(valid_spider)
        
        validator = SpiderValidator()
        result = validator.validate_spider_file(valid_path)
        
        print(f"Spider válido: {'✅' if result['valid'] else '❌'}")
        if result['errors']:
            print("Errores:")
            for error in result['errors']:
                print(f"  - {error}")
                
        return result['valid']


if __name__ == "__main__":
    print("Ejecutando tests de migración y validación...\n")
    
    # Test 1: Migración
    migration_ok = test_migration()
    
    # Test 2: Validación
    validation_ok = test_validation_only()
    
    # Resumen
    print("\n" + "="*60)
    print("RESUMEN DE TESTS")
    print("="*60)
    print(f"Test de migración: {'✅ PASÓ' if migration_ok else '❌ FALLÓ'}")
    print(f"Test de validación: {'✅ PASÓ' if validation_ok else '❌ FALLÓ'}")
    
    if migration_ok and validation_ok:
        print("\n✅ TODOS LOS TESTS PASARON")
        sys.exit(0)
    else:
        print("\n❌ ALGUNOS TESTS FALLARON")
        sys.exit(1)