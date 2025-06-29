#!/usr/bin/env python3
"""
Test de verificación para TASK-001: Actualización de Modelos
Verifica que los modelos tengan los campos obligatorios correctos
"""
import sys
sys.path.insert(0, '/mnt/c/Users/DELL/Desktop/PruebaWindsurfAI/LaMaquinaDeNoticias/src/spider_factory')

# Importar solo lo necesario para evitar dependencias
from pydantic import BaseModel, ValidationError
import importlib.util

# Cargar models.py directamente
spec = importlib.util.spec_from_file_location(
    "models", 
    "/mnt/c/Users/DELL/Desktop/PruebaWindsurfAI/LaMaquinaDeNoticias/src/spider_factory/src/models.py"
)
models = importlib.util.module_from_spec(spec)

# Simular las dependencias necesarias
sys.modules['src.analyzer'] = type(sys)('analyzer')
sys.modules['src.analyzer'].AnalysisStrategy = type('AnalysisStrategy', (), {'RSS': 'rss', 'STATIC': 'static'})
sys.modules['src.analyzer'].AnalysisConfidence = float
sys.modules['src.config'] = type(sys)('config')
sys.modules['src.config'].AREAS_GEOGRAFICAS_VALIDAS = [
    'ESPAÑA', 'ARGENTINA', 'MÉXICO', 'COLOMBIA', 'CHILE', 'PERÚ', 'VENEZUELA',
    'ECUADOR', 'BOLIVIA', 'PARAGUAY', 'URUGUAY', 'GLOBAL', 'HISPANOAMERICA'
]

# Cargar el módulo
spec.loader.exec_module(models)

def test_duplicate_check_request():
    """Test DuplicateCheckRequest con nuevos campos"""
    print("\n=== Test DuplicateCheckRequest ===")
    
    # Test válido
    try:
        req = models.DuplicateCheckRequest(
            medio="El País",
            seccion="Política"
        )
        print(f"✓ Creación exitosa")
        print(f"  - medio: {req.medio}")
        print(f"  - seccion: {req.seccion}")
        print(f"  - spider_name: {req.spider_name}")
        assert req.spider_name == "el_pais_politica"
        print("✓ Nombre de spider generado correctamente")
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    return True

def test_analysis_request():
    """Test AnalysisRequest con nuevos campos obligatorios"""
    print("\n=== Test AnalysisRequest ===")
    
    # Test con campos faltantes (debe fallar)
    try:
        req = models.AnalysisRequest(
            url="https://example.com"
        )
        print("✗ No debería permitir crear sin campos obligatorios")
        return False
    except ValidationError as e:
        print("✓ Validación correcta: rechaza request sin campos obligatorios")
    
    # Test válido
    try:
        req = models.AnalysisRequest(
            url="https://example.com/news",
            medio="Example News",
            seccion="política",
            area_geografica="ESPAÑA",
            tipo_medio="diario"
        )
        print("✓ Creación exitosa con todos los campos obligatorios")
        print(f"  - medio: {req.medio}")
        print(f"  - seccion: {req.seccion}")
        print(f"  - area_geografica: {req.area_geografica}")
        print(f"  - tipo_medio: {req.tipo_medio}")
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    # Test área geográfica inválida
    try:
        req = models.AnalysisRequest(
            url="https://example.com",
            medio="Test",
            seccion="test",
            area_geografica="INVALIDA",
            tipo_medio="diario"
        )
        print("✗ No debería permitir área geográfica inválida")
        return False
    except ValidationError as e:
        print("✓ Validación correcta: rechaza área geográfica inválida")
    
    return True

def test_generate_spider_request():
    """Test GenerateSpiderRequest con nuevos campos"""
    print("\n=== Test GenerateSpiderRequest ===")
    
    # Test sin campos obligatorios (debe fallar)
    try:
        req = models.GenerateSpiderRequest(
            analysis_url="https://example.com"
        )
        print("✗ No debería permitir crear sin campos obligatorios")
        return False
    except ValidationError as e:
        print("✓ Validación correcta: rechaza request sin campos obligatorios")
    
    # Test válido
    try:
        req = models.GenerateSpiderRequest(
            analysis_url="https://example.com/news",
            medio="el_mundo",
            seccion="deportes",
            area_geografica="ESPAÑA",
            tipo_medio="diario",
            frecuencia_minutos=30,
            comentarios="Sección principal de deportes"
        )
        print("✓ Creación exitosa con todos los campos")
        print(f"  - medio: {req.medio}")
        print(f"  - seccion: {req.seccion}")
        print(f"  - spider_name (generado): {req.spider_name}")
        print(f"  - media_name (compatibilidad): {req.media_name}")
        print(f"  - area_geografica: {req.area_geografica}")
        print(f"  - tipo_medio: {req.tipo_medio}")
        print(f"  - frecuencia_minutos: {req.frecuencia_minutos}")
        
        assert req.spider_name == "el_mundo_deportes"
        assert req.media_name == "El Mundo"
        print("✓ Propiedades calculadas correctamente")
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    # Test tipo_medio inválido
    try:
        req = models.GenerateSpiderRequest(
            analysis_url="https://example.com",
            medio="test",
            seccion="test", 
            area_geografica="ESPAÑA",
            tipo_medio="blog"  # Inválido
        )
        print("✗ No debería permitir tipo_medio inválido")
        return False
    except ValidationError as e:
        print("✓ Validación correcta: rechaza tipo_medio inválido")
    
    return True

def test_batch_site():
    """Test BatchSite del batch_processor"""
    print("\n=== Test BatchSite ===")
    
    # Cargar batch_processor
    spec_batch = importlib.util.spec_from_file_location(
        "batch_processor",
        "/mnt/c/Users/DELL/Desktop/PruebaWindsurfAI/LaMaquinaDeNoticias/src/spider_factory/src/batch_processor.py"
    )
    batch_processor = importlib.util.module_from_spec(spec_batch)
    
    # Simular más dependencias
    sys.modules['src.websocket_manager'] = type(sys)('websocket_manager')
    sys.modules['src.generator'] = type(sys)('generator')
    
    spec_batch.loader.exec_module(batch_processor)
    
    # Test válido
    try:
        site = batch_processor.BatchSite(
            medio="la_nacion",
            seccion="economia",
            url="https://lanacion.com/economia",
            area_geografica="ARGENTINA",
            tipo_medio="diario",
            frecuencia_minutos=45,
            rss_url="https://lanacion.com/economia/rss",
            comentarios="Sección economía del diario"
        )
        print("✓ BatchSite creado correctamente")
        print(f"  - medio: {site.medio}")
        print(f"  - seccion: {site.seccion}")
        print(f"  - tipo_medio: {site.tipo_medio}")
        print(f"  - frecuencia_minutos: {site.frecuencia_minutos}")
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    return True

def main():
    """Ejecutar todos los tests"""
    print("=== TASK-001: Verificación de Modelos Actualizados ===")
    
    tests = [
        test_duplicate_check_request,
        test_analysis_request,
        test_generate_spider_request,
        test_batch_site
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"\n✗ Error ejecutando {test.__name__}: {e}")
            results.append(False)
    
    print("\n=== RESUMEN ===")
    passed = sum(results)
    total = len(results)
    print(f"Tests pasados: {passed}/{total}")
    
    if passed == total:
        print("\n✅ TASK-001 completada exitosamente!")
        print("\nCriterios cumplidos:")
        print("✓ GenerateSpiderRequest incluye campos obligatorios")
        print("✓ Spider name se genera como {medio}_{seccion}")
        print("✓ BatchSite redefinido con estructura completa")
        print("✓ Validación de area_geografica funciona")
        print("✓ Validación de tipo_medio funciona")
        print("✓ DuplicateCheckRequest creado correctamente")
        print("✓ Compatibilidad mantenida con media_name y spider_name")
    else:
        print("\n❌ Algunos tests fallaron. Revisar implementación.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)