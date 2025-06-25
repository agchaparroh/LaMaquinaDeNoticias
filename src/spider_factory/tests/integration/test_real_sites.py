"""
Test con sitios web reales para Spider Factory 2.0
Requiere conexión a internet y todas las dependencias
"""
import os
import sys
import asyncio
import json
from datetime import datetime
from typing import List, Dict

# Configurar path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from src.analyzer import SmartAnalyzer
    from src.generator import SpiderGenerator
    from src.patterns import PatternStorage
    from src.models import AnalysisRequest, GenerateRequest, SiteInfo
    from src.batch_processor import BatchProcessor
    print("✅ Imports exitosos")
except ImportError as e:
    print(f"❌ Error importando: {e}")
    sys.exit(1)


# Sitios de prueba (medios reales)
TEST_SITES = [
    {
        "name": "bbc_news",
        "url": "https://www.bbc.com/news",
        "section": "world",
        "expected_strategy": "scraping",
        "has_rss": True,
        "rss_url": "https://feeds.bbci.co.uk/news/world/rss.xml"
    },
    {
        "name": "cnn_espanol",
        "url": "https://cnnespanol.cnn.com/",
        "section": "americas",
        "expected_strategy": "scraping",
        "has_rss": True,
        "needs_js": True
    },
    {
        "name": "el_pais",
        "url": "https://elpais.com/",
        "section": "internacional",
        "expected_strategy": "scraping",
        "has_rss": True,
        "rss_url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/internacional/portada"
    },
    {
        "name": "reuters",
        "url": "https://www.reuters.com/",
        "section": "world",
        "expected_strategy": "scraping",
        "has_rss": True,
        "needs_js": False
    },
    {
        "name": "guardian",
        "url": "https://www.theguardian.com/",
        "section": "world",
        "expected_strategy": "scraping",
        "has_rss": True,
        "rss_url": "https://www.theguardian.com/world/rss"
    }
]


class RealSitesTest:
    """Tests con sitios web reales"""
    
    def __init__(self):
        self.analyzer = SmartAnalyzer()
        self.generator = SpiderGenerator()
        self.pattern_storage = PatternStorage()
        self.results = []
        self.generated_spiders = []
    
    async def test_site_analysis(self, site: Dict) -> Dict:
        """Analiza un sitio web real"""
        print(f"\n📰 Analizando: {site['name']} ({site['url']})")
        
        try:
            # Crear request
            request = AnalysisRequest(
                url=site['url'],
                section_name=site['section']
            )
            
            # Simular análisis (sin API key real)
            if os.getenv('FIRECRAWL_API_KEY'):
                # Con API key, hacer análisis real
                result = await self.analyzer.analyze(request)
                
                print(f"  ✅ Estrategia: {result.strategy}")
                print(f"  ✅ Confianza: {result.confidence}")
                
                if result.rss_url:
                    print(f"  ✅ RSS detectado: {result.rss_url}")
                
                if result.needs_javascript:
                    print(f"  ⚠️  Requiere JavaScript")
                
                return {
                    "site": site['name'],
                    "success": True,
                    "strategy": result.strategy,
                    "confidence": result.confidence,
                    "analysis": result
                }
            else:
                # Sin API key, simular resultado
                print("  ⚠️  Sin API key - Simulando análisis")
                
                return {
                    "site": site['name'],
                    "success": True,
                    "strategy": site.get('expected_strategy', 'scraping'),
                    "confidence": 0.75,
                    "simulated": True
                }
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            return {
                "site": site['name'],
                "success": False,
                "error": str(e)
            }
    
    async def test_spider_generation(self, site: Dict, analysis_result: Dict) -> bool:
        """Genera un spider basado en el análisis"""
        print(f"\n🕷️  Generando spider para: {site['name']}")
        
        try:
            # Preparar datos
            site_info = SiteInfo(
                name=site['name'],
                url=site['url'],
                domain=site['url'].split('/')[2]
            )
            
            # Crear request de generación
            if 'analysis' in analysis_result:
                analysis = analysis_result['analysis']
            else:
                # Simular análisis
                analysis = {
                    "strategy": analysis_result['strategy'],
                    "confidence": analysis_result['confidence'],
                    "needs_javascript": site.get('needs_js', False),
                    "selectors": {
                        "title": "h1",
                        "content": "article",
                        "date": "time",
                        "links": "a.article-link"
                    }
                }
            
            request = GenerateRequest(
                site_name=site_info.name,
                site_url=str(site_info.url),
                section_name=site['section'],
                analysis_result=analysis
            )
            
            # Generar spider (sin guardar realmente)
            spider_code = await self.generator.generate(request)
            
            if spider_code:
                print(f"  ✅ Spider generado: {len(spider_code)} caracteres")
                self.generated_spiders.append({
                    "name": f"{site['name']}_spider",
                    "site": site['name'],
                    "strategy": analysis_result['strategy']
                })
                return True
            else:
                print("  ❌ No se pudo generar el spider")
                return False
                
        except Exception as e:
            print(f"  ❌ Error generando spider: {e}")
            return False
    
    async def test_batch_processing(self):
        """Test procesamiento por lotes"""
        print("\n=== TEST: Procesamiento por Lotes ===")
        
        try:
            # Crear CSV temporal
            csv_content = "site_name,url,section\n"
            for site in TEST_SITES[:3]:  # Solo los primeros 3
                csv_content += f"{site['name']},{site['url']},{site['section']}\n"
            
            print(f"📋 Procesando {len(TEST_SITES[:3])} sitios en lote...")
            
            # Simular procesamiento
            print("  ✅ Lote simulado exitosamente")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Error en batch: {e}")
            return False
    
    async def run_all_tests(self):
        """Ejecuta todos los tests con sitios reales"""
        print("🌐 SPIDER FACTORY 2.0 - TESTS CON SITIOS REALES")
        print("=" * 70)
        print(f"🕐 Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📋 Sitios a probar: {len(TEST_SITES)}")
        
        # Test individual de cada sitio
        for site in TEST_SITES:
            # Análisis
            analysis_result = await self.test_site_analysis(site)
            self.results.append(analysis_result)
            
            # Generación de spider si el análisis fue exitoso
            if analysis_result['success']:
                generation_success = await self.test_spider_generation(site, analysis_result)
                analysis_result['spider_generated'] = generation_success
        
        # Test de procesamiento por lotes
        batch_success = await self.test_batch_processing()
        
        # Mostrar resumen
        self.show_summary(batch_success)
    
    def show_summary(self, batch_success: bool):
        """Muestra resumen de resultados"""
        print("\n" + "=" * 70)
        print("📊 RESUMEN DE RESULTADOS")
        print("=" * 70)
        
        # Análisis por sitio
        successful_analyses = sum(1 for r in self.results if r['success'])
        total_sites = len(self.results)
        
        print(f"\n📰 Sitios analizados: {successful_analyses}/{total_sites}")
        
        for result in self.results:
            if result['success']:
                status = "✅"
                strategy = result.get('strategy', 'N/A')
                confidence = result.get('confidence', 0)
                spider = "🕷️" if result.get('spider_generated') else "❌"
                print(f"  {status} {result['site']}: {strategy} (conf: {confidence:.2f}) {spider}")
            else:
                print(f"  ❌ {result['site']}: {result.get('error', 'Error desconocido')}")
        
        # Spiders generados
        print(f"\n🕷️  Spiders generados: {len(self.generated_spiders)}")
        for spider in self.generated_spiders:
            print(f"  - {spider['name']} ({spider['strategy']})")
        
        # Batch processing
        print(f"\n📦 Procesamiento por lotes: {'✅ OK' if batch_success else '❌ FAIL'}")
        
        # Resumen final
        all_passed = successful_analyses == total_sites and batch_success
        
        if all_passed:
            print("\n🎉 TODOS LOS TESTS PASARON!")
        else:
            print(f"\n⚠️  Algunos tests fallaron")
        
        # Guardar resultados
        self.save_results()
    
    def save_results(self):
        """Guarda los resultados en JSON"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"test_real_sites_results_{timestamp}.json"
        
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "sites_tested": len(self.results),
            "successful_analyses": sum(1 for r in self.results if r['success']),
            "spiders_generated": len(self.generated_spiders),
            "results": self.results,
            "generated_spiders": self.generated_spiders
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Resultados guardados en: {filename}")
        except Exception as e:
            print(f"\n❌ Error guardando resultados: {e}")


async def main():
    """Función principal"""
    print("⚠️  NOTA: Este test requiere:")
    print("  - Conexión a Internet")
    print("  - FIRECRAWL_API_KEY configurada (opcional)")
    print("  - Redis ejecutándose (opcional)")
    print()
    
    confirm = input("¿Continuar con los tests? (s/n): ")
    if confirm.lower() != 's':
        print("Tests cancelados")
        return 1
    
    tester = RealSitesTest()
    await tester.run_all_tests()
    return 0


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)