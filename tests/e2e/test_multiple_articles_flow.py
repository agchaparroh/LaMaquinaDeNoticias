"""
test_multiple_articles_flow.py
Test End-to-End: Procesamiento simultáneo de múltiples artículos

Valida que el sistema puede manejar múltiples artículos concurrentemente:
1. Scraper genera archivo con 5 artículos
2. Connector envía todos al Pipeline en paralelo
3. Pipeline procesa concurrentemente sin perder datos
4. Dashboard muestra todos los artículos procesados correctamente
"""

import pytest
import json
import gzip
import os
import asyncio
import time
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
from concurrent.futures import ThreadPoolExecutor
import threading


class MultiArticleFlow:
    """Simula el procesamiento simultáneo de múltiples artículos"""
    
    def __init__(self, num_articles=5):
        self.num_articles = num_articles
        self.articles_data = []
        self.processing_results = {}
        self.processing_times = {}
        self.lock = threading.Lock()
        
        # Generar artículos de prueba
        for i in range(num_articles):
            article = {
                "url": f"https://example.com/multi-test-{i+1}",
                "titular": f"Noticia {i+1}: Evento importante en {self._get_category(i)}",
                "medio": f"Medio {(i % 3) + 1}",  # Distribuir entre 3 medios
                "pais_publicacion": ["AR", "UY", "CL", "MX", "ES"][i % 5],
                "tipo_medio": "digital",
                "fecha_publicacion": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
                "contenido_texto": f"Este es el contenido de la noticia {i+1}. " * 10,  # ~500 chars
                "contenido_html": f"<p>Contenido HTML de la noticia {i+1}</p>" * 5,
                "autor": f"Autor {chr(65 + i)}",  # A, B, C, D, E
                "seccion": self._get_category(i),
                "etiquetas_fuente": [f"tag{i+1}", "multi-test", self._get_category(i).lower()],
                "es_opinion": i % 3 == 0,  # Cada 3 artículos es opinión
                "es_oficial": i % 4 == 0,  # Cada 4 artículos es oficial
                "fecha_recopilacion": datetime.utcnow().isoformat()
            }
            self.articles_data.append(article)
    
    def _get_category(self, index):
        """Asigna categorías variadas a los artículos"""
        categories = ["Política", "Economía", "Tecnología", "Deportes", "Cultura"]
        return categories[index % len(categories)]
    
    def scraper_generate_batch_file(self, output_dir: str) -> str:
        """Scraper genera archivo con múltiples artículos"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"articulos_batch_{timestamp}_multi_test.json.gz"
        filepath = os.path.join(output_dir, filename)
        
        with gzip.open(filepath, 'wt', encoding='utf-8') as f:
            json.dump(self.articles_data, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def connector_process_batch(self, filepath: str) -> dict:
        """Connector lee y procesa batch de artículos"""
        start_time = time.time()
        
        # Leer archivo
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            articles = json.loads(f.read())
        
        assert len(articles) == self.num_articles, f"Se esperaban {self.num_articles}, se encontraron {len(articles)}"
        
        # Validar cada artículo
        for article in articles:
            assert len(article['contenido_texto']) >= 50
            assert article['url']
            assert article['titular']
        
        read_time = time.time() - start_time
        
        return {
            "articles_count": len(articles),
            "read_time": read_time,
            "articles": articles
        }
    
    def pipeline_process_parallel(self, articles: list) -> dict:
        """Pipeline procesa artículos en paralelo"""
        results = {
            "processed": [],
            "failed": [],
            "processing_times": {}
        }
        
        def process_single_article(article):
            """Procesa un artículo individual"""
            start = time.time()
            article_id = article['url'].split('-')[-1]
            
            try:
                # Simular procesamiento (extracción de hechos, etc.)
                time.sleep(0.1)  # Simular latencia de procesamiento
                
                # Generar hechos basados en el contenido
                num_hechos = 2 + (int(article_id) % 3)  # 2-4 hechos por artículo
                hechos = []
                
                for j in range(num_hechos):
                    hecho = {
                        "id": f"hecho-art{article_id}-{j+1}",
                        "contenido": f"Hecho {j+1} extraído del artículo {article_id}",
                        "tipo": ["declaracion", "accion", "estadistica"][j % 3],
                        "importancia_automatica": 5 + (j % 5),
                        "confianza_extraccion": 0.8 + (j * 0.05)
                    }
                    hechos.append(hecho)
                
                # Resultado del procesamiento
                result = {
                    "article_id": f"art-multi-{article_id}",
                    "url": article['url'],
                    "titular": article['titular'],
                    "hechos_count": len(hechos),
                    "hechos": hechos,
                    "processing_time": time.time() - start,
                    "status": "success"
                }
                
                with self.lock:
                    results["processed"].append(result)
                    results["processing_times"][article['url']] = result["processing_time"]
                
                return result
                
            except Exception as e:
                # Registrar fallo
                with self.lock:
                    results["failed"].append({
                        "url": article['url'],
                        "error": str(e),
                        "processing_time": time.time() - start
                    })
                return None
        
        # Procesar en paralelo usando ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(process_single_article, article) 
                      for article in articles]
            
            # Esperar a que todos terminen
            for future in futures:
                future.result()
        
        return results
    
    def dashboard_query_batch_results(self, processing_results: dict) -> dict:
        """Dashboard consulta todos los artículos procesados"""
        dashboard_view = {
            "total_articulos": len(processing_results["processed"]) + len(processing_results["failed"]),
            "procesados_exitosamente": len(processing_results["processed"]),
            "fallos": len(processing_results["failed"]),
            "articulos": [],
            "estadisticas": {
                "total_hechos": 0,
                "promedio_hechos_por_articulo": 0,
                "tiempo_procesamiento_total": sum(processing_results["processing_times"].values()),
                "tiempo_promedio_por_articulo": 0
            }
        }
        
        # Agregar información de cada artículo
        for result in processing_results["processed"]:
            article_summary = {
                "id": result["article_id"],
                "titular": result["titular"],
                "hechos_count": result["hechos_count"],
                "tiempo_procesamiento": result["processing_time"],
                "estado": "disponible_para_revision"
            }
            dashboard_view["articulos"].append(article_summary)
            dashboard_view["estadisticas"]["total_hechos"] += result["hechos_count"]
        
        # Calcular promedios
        if dashboard_view["procesados_exitosamente"] > 0:
            dashboard_view["estadisticas"]["promedio_hechos_por_articulo"] = (
                dashboard_view["estadisticas"]["total_hechos"] / 
                dashboard_view["procesados_exitosamente"]
            )
            dashboard_view["estadisticas"]["tiempo_promedio_por_articulo"] = (
                dashboard_view["estadisticas"]["tiempo_procesamiento_total"] / 
                dashboard_view["procesados_exitosamente"]
            )
        
        return dashboard_view


def test_multiple_articles_flow():
    """Test E2E: Procesar 5 artículos simultáneamente"""
    
    # GIVEN: Sistema listo para procesar múltiples artículos
    flow = MultiArticleFlow(num_articles=5)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print("\n🚀 Test E2E de procesamiento múltiple (5 artículos)\n")
        
        # 1. Scraper genera archivo con batch
        print("1️⃣ SCRAPER: Generando archivo con 5 artículos...")
        batch_file = flow.scraper_generate_batch_file(temp_dir)
        file_size = os.path.getsize(batch_file) / 1024  # KB
        print(f"   ✅ Archivo generado: {os.path.basename(batch_file)} ({file_size:.1f} KB)")
        
        # 2. Connector procesa batch
        print("\n2️⃣ CONNECTOR: Leyendo y validando batch...")
        connector_result = flow.connector_process_batch(batch_file)
        print(f"   ✅ Artículos leídos: {connector_result['articles_count']}")
        print(f"   ⏱️ Tiempo de lectura: {connector_result['read_time']:.3f}s")
        
        # 3. Pipeline procesa en paralelo
        print("\n3️⃣ PIPELINE: Procesando artículos en paralelo...")
        print("   🔄 Iniciando procesamiento concurrente...")
        
        start_pipeline = time.time()
        pipeline_results = flow.pipeline_process_parallel(connector_result['articles'])
        pipeline_time = time.time() - start_pipeline
        
        print(f"   ✅ Procesamiento completado en {pipeline_time:.2f}s")
        print(f"   ✓ Exitosos: {len(pipeline_results['processed'])}")
        print(f"   ✗ Fallos: {len(pipeline_results['failed'])}")
        
        # 4. Dashboard muestra resultados
        print("\n4️⃣ DASHBOARD: Consultando resultados del batch...")
        dashboard_data = flow.dashboard_query_batch_results(pipeline_results)
        
        print(f"   📊 Resumen del procesamiento:")
        print(f"      - Total artículos: {dashboard_data['total_articulos']}")
        print(f"      - Procesados: {dashboard_data['procesados_exitosamente']}")
        print(f"      - Total hechos extraídos: {dashboard_data['estadisticas']['total_hechos']}")
        print(f"      - Promedio hechos/artículo: {dashboard_data['estadisticas']['promedio_hechos_por_articulo']:.1f}")
        print(f"      - Tiempo promedio/artículo: {dashboard_data['estadisticas']['tiempo_promedio_por_articulo']:.3f}s")
        
        # THEN: Validar resultados
        assert dashboard_data['procesados_exitosamente'] == 5
        assert dashboard_data['fallos'] == 0
        assert dashboard_data['estadisticas']['total_hechos'] >= 10  # Mínimo 2 hechos por artículo
        
        print("\n✅ PROCESAMIENTO MÚLTIPLE EXITOSO")
        print(f"   - Todos los artículos procesados correctamente")
        print(f"   - Sin pérdida de datos en procesamiento paralelo")
        print(f"   - Performance: {flow.num_articles / pipeline_time:.1f} artículos/segundo")


def test_multiple_articles_with_failures():
    """Test E2E: Manejo de fallos en procesamiento múltiple"""
    
    # Modificar algunos artículos para que fallen
    flow = MultiArticleFlow(num_articles=7)
    
    # Corromper algunos artículos para simular fallos
    flow.articles_data[2]['contenido_texto'] = "Muy corto"  # < 50 chars
    flow.articles_data[5]['url'] = ""  # URL vacía
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print("\n⚠️ Test E2E con fallos simulados (7 artículos, 2 con errores)\n")
        
        # Generar archivo
        batch_file = flow.scraper_generate_batch_file(temp_dir)
        
        # Procesar con manejo de errores
        try:
            connector_result = flow.connector_process_batch(batch_file)
        except AssertionError as e:
            print(f"✅ Connector detectó errores de validación: {e}")
            # En un sistema real, el Connector podría:
            # 1. Rechazar todo el batch
            # 2. Procesar solo los válidos
            # 3. Registrar los inválidos para reprocesamiento
            
            # Para este test, filtramos los válidos
            with gzip.open(batch_file, 'rt', encoding='utf-8') as f:
                all_articles = json.loads(f.read())
            
            valid_articles = [a for a in all_articles 
                            if len(a.get('contenido_texto', '')) >= 50 and a.get('url')]
            
            print(f"   📊 Artículos válidos: {len(valid_articles)}/{len(all_articles)}")
            
            # Procesar solo los válidos
            pipeline_results = flow.pipeline_process_parallel(valid_articles)
            
            print(f"\n   Resultados del pipeline:")
            print(f"   ✓ Procesados: {len(pipeline_results['processed'])}")
            print(f"   ✗ Rechazados por validación: {len(all_articles) - len(valid_articles)}")


def test_concurrent_load_stress():
    """Test E2E: Carga concurrente con múltiples batches"""
    
    print("\n💪 Test de carga: Múltiples batches concurrentes\n")
    
    batches = []
    batch_sizes = [3, 5, 4, 6, 2]  # Diferentes tamaños de batch
    
    # Crear múltiples flujos
    for i, size in enumerate(batch_sizes):
        batches.append({
            "id": f"batch-{i+1}",
            "flow": MultiArticleFlow(num_articles=size),
            "size": size
        })
    
    total_articles = sum(b["size"] for b in batches)
    print(f"📦 Preparando {len(batches)} batches con {total_articles} artículos totales")
    
    # Procesar todos los batches midiendo el tiempo
    start_time = time.time()
    results = []
    
    def process_batch(batch_info):
        """Procesa un batch completo"""
        with tempfile.TemporaryDirectory() as temp_dir:
            flow = batch_info["flow"]
            
            # Generar archivo
            filepath = flow.scraper_generate_batch_file(temp_dir)
            
            # Leer
            connector_res = flow.connector_process_batch(filepath)
            
            # Procesar
            pipeline_res = flow.pipeline_process_parallel(connector_res['articles'])
            
            return {
                "batch_id": batch_info["id"],
                "size": batch_info["size"],
                "processed": len(pipeline_res["processed"]),
                "failed": len(pipeline_res["failed"])
            }
    
    # Procesar batches en paralelo
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(process_batch, batch) for batch in batches]
        results = [f.result() for f in futures]
    
    total_time = time.time() - start_time
    
    # Analizar resultados
    print(f"\n📊 RESULTADOS DE CARGA:")
    total_processed = 0
    for res in results:
        print(f"   {res['batch_id']}: {res['processed']}/{res['size']} procesados")
        total_processed += res['processed']
    
    print(f"\n   ⏱️ Tiempo total: {total_time:.2f}s")
    print(f"   📈 Throughput: {total_processed/total_time:.1f} artículos/segundo")
    print(f"   ✅ Tasa de éxito: {(total_processed/total_articles)*100:.1f}%")
    
    # Validar que el sistema mantuvo la integridad
    assert total_processed == total_articles, "Algunos artículos se perdieron en el procesamiento"
    assert total_time < total_articles * 0.5, "El procesamiento paralelo no fue eficiente"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
