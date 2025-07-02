#!/usr/bin/env python3
"""
Test script para JsonGzExportPipeline
Verifica que el pipeline funciona correctamente sin afectar el sistema actual.
"""

import os
import sys
import tempfile
import shutil
import json
import gzip
from datetime import datetime
from pathlib import Path

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Configurar variables de entorno para testing
os.environ['ENABLE_PIPELINE_EXPORT'] = 'true'
os.environ['DEVELOPMENT_MODE'] = 'true'

from scrapy import Spider
from scrapy.settings import Settings
from itemadapter import ItemAdapter

from scraper_core.items import ArticuloInItem
from scraper_core.pipelines.json_export import JsonGzExportPipeline


class TestSpider(Spider):
    """Spider de prueba para testing."""
    name = 'test_spider'


def create_test_item():
    """Crear un item de prueba."""
    item = ArticuloInItem()
    item['url'] = 'https://ejemplo.com/noticia/123'
    item['titular'] = 'Noticia de Prueba para Pipeline Export'
    item['medio'] = 'Diario de Prueba'
    item['area_geografica'] = 'España'
    item['tipo_medio'] = 'diario'
    item['fecha_publicacion'] = datetime.now()
    item['contenido_texto'] = 'Este es el contenido de prueba para verificar que el pipeline de exportación funciona correctamente.'
    item['contenido_html'] = '<p>Este es el contenido HTML de prueba.</p>'
    item['autor'] = 'Autor de Prueba'
    item['idioma'] = 'es'
    item['seccion'] = 'tecnologia'
    item['etiquetas_fuente'] = ['prueba', 'testing', 'pipeline']
    item['es_opinion'] = False
    item['es_oficial'] = False
    
    return item


def test_pipeline_disabled():
    """Test: Pipeline deshabilitado por defecto."""
    print("🧪 Test 1: Pipeline deshabilitado por defecto")
    
    # Crear settings sin habilitar export
    settings = Settings()
    settings.set('ENABLE_PIPELINE_EXPORT', False)
    
    # Crear pipeline
    pipeline = JsonGzExportPipeline.from_crawler(type('MockCrawler', (), {'settings': settings})())
    
    assert not pipeline.enabled, "Pipeline debería estar deshabilitado por defecto"
    print("✅ Pipeline correctamente deshabilitado por defecto")


def test_pipeline_enabled():
    """Test: Pipeline habilitado con variable de entorno."""
    print("\n🧪 Test 2: Pipeline habilitado con configuración")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Crear settings habilitando export
        settings = Settings()
        settings.set('ENABLE_PIPELINE_EXPORT', True)
        settings.set('EXPORT_DIRECTORY', temp_dir)
        
        # Crear pipeline
        pipeline = JsonGzExportPipeline.from_crawler(type('MockCrawler', (), {'settings': settings})())
        
        assert pipeline.enabled, "Pipeline debería estar habilitado"
        assert pipeline.export_directory == temp_dir, "Directorio de export incorrecto"
        print("✅ Pipeline correctamente habilitado")


def test_item_export():
    """Test: Exportación de item completo."""
    print("\n🧪 Test 3: Exportación de item")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Configurar pipeline
        settings = Settings()
        settings.set('ENABLE_PIPELINE_EXPORT', True)
        settings.set('EXPORT_DIRECTORY', temp_dir)
        
        pipeline = JsonGzExportPipeline.from_crawler(type('MockCrawler', (), {'settings': settings})())
        spider = TestSpider()
        
        # Abrir spider
        pipeline.open_spider(spider)
        
        # Crear y procesar item
        item = create_test_item()
        processed_item = pipeline.process_item(item, spider)
        
        # Verificar que el item se devuelve sin modificar
        assert processed_item == item, "El item no debería modificarse"
        
        # Verificar que se creó un archivo
        files = list(Path(temp_dir).glob('*.json.gz'))
        assert len(files) == 1, f"Debería haber exactamente 1 archivo, encontrados: {len(files)}"
        
        # Verificar contenido del archivo
        file_path = files[0]
        with gzip.open(file_path, 'rt', encoding='utf-8') as f:
            exported_data = json.load(f)
        
        # Verificar campos principales
        assert exported_data['titular'] == item['titular']
        assert exported_data['medio'] == item['medio']
        assert exported_data['contenido_texto'] == item['contenido_texto']
        assert 'export_metadata' in exported_data
        assert exported_data['estado_procesamiento'] == 'pendiente_connector'
        
        # Cerrar spider
        pipeline.close_spider(spider)
        
        # Verificar estadísticas
        stats = pipeline.get_export_stats()
        assert stats['total_items'] == 1
        assert stats['exported_items'] == 1
        assert stats['failed_exports'] == 0
        assert stats['success_rate'] == 100.0
        
        print(f"✅ Item exportado correctamente a {file_path.name}")
        print(f"📊 Estadísticas: {stats}")


def test_compatibility_with_existing_pipelines():
    """Test: Compatibilidad con pipelines existentes."""
    print("\n🧪 Test 4: Compatibilidad con pipelines existentes")
    
    # Importar pipelines existentes para verificar que no hay conflictos
    try:
        from scraper_core.pipelines.cleaning import DataCleaningPipeline
        from scraper_core.pipelines.validation import DataValidationPipeline
        from scraper_core.pipelines.storage import SupabaseStoragePipeline
        from scraper_core.pipelines.json_export import JsonGzExportPipeline
        
        print("✅ Todos los pipelines importados correctamente")
        
        # Verificar que están en __all__
        from scraper_core.pipelines import __all__ as pipeline_all
        expected_pipelines = [
            'DataCleaningPipeline',
            'DataValidationPipeline', 
            'SupabaseStoragePipeline',
            'JsonGzExportPipeline'
        ]
        
        for pipeline_name in expected_pipelines:
            assert pipeline_name in pipeline_all, f"Pipeline {pipeline_name} no está en __all__"
        
        print("✅ Todos los pipelines están correctamente exportados")
        
    except Exception as e:
        print(f"❌ Error importando pipelines: {e}")
        raise


def test_settings_configuration():
    """Test: Configuración en settings.py."""
    print("\n🧪 Test 5: Configuración en settings")
    
    # Simular configuración de settings
    os.environ['ENABLE_PIPELINE_EXPORT'] = 'true'
    
    # Importar settings (esto ejecutará la lógica condicional)
    import importlib
    if 'scraper_core.settings' in sys.modules:
        importlib.reload(sys.modules['scraper_core.settings'])
    
    from scraper_core import settings
    
    # Verificar que ENABLE_PIPELINE_EXPORT está correctamente detectado
    assert hasattr(settings, 'ENABLE_PIPELINE_EXPORT'), "ENABLE_PIPELINE_EXPORT no está definido"
    assert settings.ENABLE_PIPELINE_EXPORT == True, "ENABLE_PIPELINE_EXPORT no está habilitado"
    
    # Verificar que el pipeline está en ITEM_PIPELINES
    pipeline_key = 'scraper_core.pipelines.json_export.JsonGzExportPipeline'
    assert pipeline_key in settings.ITEM_PIPELINES, "JsonGzExportPipeline no está en ITEM_PIPELINES"
    assert settings.ITEM_PIPELINES[pipeline_key] == 450, "Prioridad incorrecta para JsonGzExportPipeline"
    
    print("✅ Configuración en settings correcta")
    
    # Limpiar variable de entorno
    os.environ['ENABLE_PIPELINE_EXPORT'] = 'false'


def test_default_behavior():
    """Test: Comportamiento por defecto (pipeline deshabilitado)."""
    print("\n🧪 Test 6: Comportamiento por defecto")
    
    # Asegurar que ENABLE_PIPELINE_EXPORT está en false
    os.environ['ENABLE_PIPELINE_EXPORT'] = 'false'
    
    # Recargar settings
    import importlib
    if 'scraper_core.settings' in sys.modules:
        importlib.reload(sys.modules['scraper_core.settings'])
    
    from scraper_core import settings
    
    # Verificar que el pipeline NO está en ITEM_PIPELINES
    pipeline_key = 'scraper_core.pipelines.json_export.JsonGzExportPipeline'
    assert pipeline_key not in settings.ITEM_PIPELINES, "JsonGzExportPipeline no debería estar en ITEM_PIPELINES por defecto"
    
    print("✅ Comportamiento por defecto correcto (pipeline deshabilitado)")


def main():
    """Ejecutar todos los tests."""
    print("🚀 Iniciando tests para JsonGzExportPipeline\n")
    
    try:
        test_pipeline_disabled()
        test_pipeline_enabled()
        test_item_export()
        test_compatibility_with_existing_pipelines()
        test_settings_configuration()
        test_default_behavior()
        
        print("\n🎉 ¡Todos los tests pasaron exitosamente!")
        print("\n📋 Resumen de funcionalidades verificadas:")
        print("✅ Pipeline deshabilitado por defecto")
        print("✅ Activación condicional con ENABLE_PIPELINE_EXPORT=true")
        print("✅ Exportación correcta de items a archivos .json.gz")
        print("✅ Compatibilidad con pipelines existentes")
        print("✅ Configuración automática en settings.py")
        print("✅ No afecta funcionamiento actual del sistema")
        
        print("\n🔧 Para activar el pipeline:")
        print("export ENABLE_PIPELINE_EXPORT=true")
        print("export DEVELOPMENT_MODE=true  # Para debugging")
        
    except Exception as e:
        print(f"\n❌ Test falló: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()