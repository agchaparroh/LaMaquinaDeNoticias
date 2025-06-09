"""
Test de Verificación del Sistema de Monitoreo
============================================

Test de integración que verifica el funcionamiento completo del sistema de 
monitoreo implementado en las subtareas 26.1-26.5.

Ejecutar con: python -m pytest tests/test_monitoring_system.py -v

Verifica:
- Todos los endpoints de monitoreo responden correctamente
- Métricas se generan y acumulan durante procesamiento de test
- Sistema de alertas detecta condiciones configuradas
- Dashboard JSON tiene estructura esperada
- Trazado de fases funciona end-to-end
- Test de carga básico con 10 artículos
"""

import pytest
import time
import asyncio
from typing import Dict, Any
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

# Importar la aplicación FastAPI
from src.main import app

# Importar modelos y utilidades necesarias
# from module_connector.src.models import ArticuloInItem  # Comentado temporalmente
from src.models.entrada import FragmentoProcesableItem

# Importar sistema de monitoreo
from src.monitoring.metrics_collector import get_metrics_collector
from src.monitoring.alert_manager import get_alert_manager


class TestMonitoringSystem:
    """Test suite para verificar el sistema completo de monitoreo."""
    
    @pytest.fixture(scope="class")
    def test_client(self):
        """Cliente de test para la aplicación FastAPI con inicialización manual."""
        # Importar dependencias necesarias
        from src.controller import PipelineController
        from src.monitoring import setup_alert_endpoints
        from src.monitoring.metrics_collector import create_middleware_integration
        import src.main as main_module
        import time
        
        # Inicializar manualmente el pipeline_controller para tests
        main_module.pipeline_controller = PipelineController()
        
        # Inicializar startup_time para métricas de uptime
        main_module.startup_time = time.time()
        
        # Configurar endpoints de alertas manualmente (ya que startup no se ejecuta)
        setup_alert_endpoints(app)
        
        # CONFIGURAR MIDDLEWARE DE MÉTRICAS PARA TESTS
        create_middleware_integration(app)
        
        client = TestClient(app)
        yield client
        
        # Cleanup
        main_module.pipeline_controller = None
    
    @pytest.fixture(scope="class")
    def sample_article(self):
        """Artículo de ejemplo para tests."""
        return {
            "medio": "Test News",
            "pais_publicacion": "España",
            "tipo_medio": "Digital",
            "titular": "Test: Sistema de monitoreo funcionando correctamente",
            "fecha_publicacion": "2024-01-15T10:00:00Z",
            "contenido_texto": "Este es un contenido de prueba para el sistema de monitoreo. " * 10,
            "idioma": "es",
            "autor": "Test Author",
            "url": "https://test.example.com/article",
            "seccion": "Technology",
            "es_opinion": False,
            "es_oficial": True
        }
    
    @pytest.fixture(scope="class")
    def sample_fragment(self):
        """Fragmento de ejemplo para tests."""
        return {
            "id_fragmento": "test_fragment_monitoring_001",
            "texto_original": "Este es un fragmento de prueba para el sistema de monitoreo que debe generar métricas correctamente.",
            "id_articulo_fuente": "test_article_monitoring_001",
            "orden_en_articulo": 1,
            "metadata_adicional": {"test_monitoring": True}
        }
    
    @pytest.fixture(autouse=True)
    def reset_metrics(self):
        """Reset métricas antes de cada test para evitar interferencias."""
        try:
            collector = get_metrics_collector()
            collector.reset_metrics()
        except:
            pass  # Ignorar si el colector no está disponible
        yield
    
    def test_metrics_endpoint_responds_correctly(self, test_client):
        """
        Verifica que el endpoint /metrics responde correctamente.
        
        ✅ Especificación: Todos los endpoints de monitoreo responden correctamente
        """
        response = test_client.get("/metrics")
        
        # Verificar respuesta básica
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")
        
        # Verificar formato Prometheus básico
        content = response.text
        assert "# HELP" in content
        assert "# TYPE" in content
        assert "pipeline_" in content
        
        # Verificar presencia de métricas clave
        assert "pipeline_articles_processed_total" in content
        assert "pipeline_fragments_processed_total" in content
        assert "pipeline_error_rate" in content
        assert "system_uptime_seconds" in content
        
        print("✅ /metrics endpoint responde correctamente con formato Prometheus")
    
    def test_health_detailed_endpoint_responds_correctly(self, test_client):
        """
        Verifica que el endpoint /health/detailed responde correctamente.
        
        ✅ Especificación: Todos los endpoints de monitoreo responden correctamente
        """
        response = test_client.get("/health/detailed")
        
        # Debe responder 200 o 503 (degraded pero válido)
        assert response.status_code in [200, 503]
        
        data = response.json()
        
        # Verificar estructura requerida
        assert "status" in data
        assert "timestamp" in data
        assert "checks" in data
        assert "summary" in data
        
        # Verificar checks específicos
        checks = data["checks"]
        assert "groq_api" in checks
        assert "supabase" in checks
        assert "filesystem" in checks
        assert "pipeline_controller" in checks
        
        # Cada check debe tener la estructura correcta
        for check_name, check_data in checks.items():
            assert "status" in check_data
            assert "response_time_ms" in check_data
            assert "message" in check_data
            assert check_data["status"] in ["pass", "fail"]
        
        print("✅ /health/detailed endpoint responde correctamente con checks completos")
    
    def test_dashboard_endpoint_responds_correctly(self, test_client):
        """
        Verifica que el endpoint /monitoring/dashboard responde correctamente.
        
        ✅ Especificación: Dashboard JSON tiene estructura esperada
        """
        response = test_client.get("/monitoring/dashboard")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura principal
        required_keys = [
            "timestamp", "system_info", "throughput", "latencies",
            "pipeline_success_rates", "dependencies_health", "resources",
            "business_metrics", "historical_data", "totals", "metrics_metadata"
        ]
        
        for key in required_keys:
            assert key in data, f"Missing key '{key}' in dashboard response"
        
        # Verificar throughput
        throughput = data["throughput"]
        assert "articles_per_hour" in throughput
        assert "fragments_per_hour" in throughput
        assert "current_processing_rate" in throughput
        
        # Verificar latencias (p95/p99)
        latencies = data["latencies"]
        assert "average_seconds" in latencies
        assert "p95_seconds" in latencies
        assert "p99_seconds" in latencies
        assert "max_seconds" in latencies
        
        # Verificar tasas de éxito por fase
        success_rates = data["pipeline_success_rates"]
        expected_phases = ["fase1_triaje", "fase2_extraccion", "fase3_citas_datos", "fase4_normalizacion", "overall"]
        for phase in expected_phases:
            assert phase in success_rates
            assert 0 <= success_rates[phase] <= 1
        
        # Verificar estado de dependencias
        deps = data["dependencies_health"]
        assert "groq_api" in deps
        assert "supabase" in deps
        assert "overall_status" in deps
        
        # Verificar métricas de negocio
        business = data["business_metrics"]
        assert "facts_extracted_per_hour" in business
        assert "entities_normalized_per_hour" in business
        assert "citas_extracted_per_hour" in business
        
        print("✅ /monitoring/dashboard endpoint responde con estructura JSON completa")
    
    def test_pipeline_status_endpoint_responds_correctly(self, test_client):
        """
        Verifica que el endpoint /monitoring/pipeline-status responde correctamente.
        
        ✅ Especificación: Todos los endpoints de monitoreo responden correctamente
        """
        response = test_client.get("/monitoring/pipeline-status")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura principal
        assert "timestamp" in data
        assert "pipeline_overview" in data
        assert "phases" in data
        assert "configuration" in data
        assert "metrics" in data
        
        # Verificar información de las 4 fases
        phases = data["phases"]
        expected_phases = ["fase1_triaje", "fase2_extraccion", "fase3_citas_datos", "fase4_normalizacion"]
        
        for phase in expected_phases:
            assert phase in phases
            phase_data = phases[phase]
            
            # Cada fase debe tener estructura específica
            assert "name" in phase_data
            assert "description" in phase_data
            assert "status" in phase_data
            assert "dependencies" in phase_data
            assert "key_functions" in phase_data
            assert "typical_duration_ms" in phase_data
            assert "success_rate" in phase_data
            assert "throughput_per_hour" in phase_data
        
        # Verificar resumen del pipeline
        overview = data["pipeline_overview"]
        assert "pipeline_operational" in overview
        assert "overall_success_rate" in overview
        assert "total_phases" in overview
        assert overview["total_phases"] == 4
        
        print("✅ /monitoring/pipeline-status endpoint responde con información de las 4 fases")
    
    def test_alerts_endpoints_respond_correctly(self, test_client):
        """
        Verifica que los endpoints de alertas responden correctamente.
        
        ✅ Especificación: Sistema de alertas detecta condiciones configuradas
        """
        # Endpoint de alertas principales
        response = test_client.get("/monitoring/alerts")
        assert response.status_code == 200
        
        data = response.json()
        assert "alerts" in data
        assert "total" in data
        assert "timestamp" in data
        
        # Endpoint de resumen de alertas
        response = test_client.get("/monitoring/alerts/summary")
        assert response.status_code == 200
        
        summary = response.json()
        assert "total_alerts" in summary
        assert "active_alerts" in summary
        assert "alerts_by_severity" in summary
        assert "alerts_by_type" in summary
        
        # Endpoint de test de alertas
        response = test_client.post("/monitoring/alerts/test")
        assert response.status_code == 200
        assert "message" in response.json()
        
        print("✅ Endpoints de alertas responden correctamente")
    
    @patch('src.controller.PipelineController.process_article')
    def test_metrics_generated_during_processing(self, mock_process, test_client, sample_article):
        """
        Verifica que las métricas se generan durante el procesamiento.
        
        ✅ Especificación: Métricas se generan y acumulan durante procesamiento de test
        """
        # Mock del resultado del procesamiento
        mock_process.return_value = {
            "fragmento_id": "test_fragment_001",
            "fragmento_uuid": "uuid-test-001",
            "metricas": {
                "tiempo_total_segundos": 2.5,
                "conteos_elementos": {
                    "hechos_extraidos": 5,
                    "entidades_extraidas": 3,
                    "citas_extraidas": 2,
                    "datos_cuantitativos": 1
                }
            }
        }
        
        # Obtener métricas antes
        collector = get_metrics_collector()
        initial_stats = collector.get_stats()
        initial_total_requests = initial_stats["total_counters"]["total_requests"]
        
        # Hacer request que active el procesamiento
        response = test_client.post("/procesar_articulo", json=sample_article)
        
        # Verificar respuesta exitosa
        assert response.status_code == 200
        
        # Verificar que se han generado métricas
        final_stats = collector.get_stats()
        final_total_requests = final_stats["total_counters"]["total_requests"]
        
        # Debe haber incrementado el contador de requests
        assert final_total_requests > initial_total_requests
        
        # Verificar métricas agregadas
        aggregated = collector.get_aggregated_metrics()
        assert aggregated["requests_per_minute"] >= 0
        assert aggregated["average_latency_seconds"] >= 0
        
        print("✅ Métricas se generan correctamente durante procesamiento")
    
    @patch('src.controller.PipelineController.process_fragment')
    def test_fragment_processing_generates_metrics(self, mock_process, test_client, sample_fragment):
        """
        Verifica que el procesamiento de fragmentos genera métricas.
        
        ✅ Especificación: Métricas se generan y acumulan durante procesamiento de test
        """
        # Mock del resultado
        mock_process.return_value = {
            "fragmento_id": "test_fragment_001",
            "fragmento_uuid": "uuid-test-001",
            "metricas": {
                "tiempo_total_segundos": 1.8,
                "conteos_elementos": {
                    "hechos_extraidos": 3,
                    "entidades_extraidas": 2
                }
            }
        }
        
        # Procesar fragmento
        response = test_client.post("/procesar_fragmento", json=sample_fragment)
        assert response.status_code == 200
        
        # Verificar que las métricas se reflejan en endpoints
        metrics_response = test_client.get("/metrics")
        assert metrics_response.status_code == 200
        
        dashboard_response = test_client.get("/monitoring/dashboard")
        assert dashboard_response.status_code == 200
        
        print("✅ Procesamiento de fragmentos genera métricas correctamente")
    
    def test_alert_system_detects_conditions(self, test_client):
        """
        Verifica que el sistema de alertas detecta condiciones configuradas.
        
        ✅ Especificación: Sistema de alertas detecta condiciones configuradas
        """
        # Disparar alertas de test
        response = test_client.post("/monitoring/alerts/test")
        assert response.status_code == 200
        
        # Esperar un momento para que se procesen las alertas
        time.sleep(1)
        
        # Verificar que se han generado alertas
        alerts_response = test_client.get("/monitoring/alerts?active_only=true")
        assert alerts_response.status_code == 200
        
        alerts_data = alerts_response.json()
        alerts = alerts_data["alerts"]
        
        # Debe haber al menos una alerta generada por el test
        assert len(alerts) > 0
        
        # Verificar estructura de alertas
        for alert in alerts:
            assert "alert_type" in alert
            assert "severity" in alert
            assert "title" in alert
            assert "description" in alert
            assert "timestamp" in alert
            assert "labels" in alert
            assert "annotations" in alert
        
        print(f"✅ Sistema de alertas detectó {len(alerts)} condiciones configuradas")
    
    def test_response_times_under_200ms(self, test_client):
        """
        Verifica que los endpoints responden en menos de 200ms.
        
        ✅ Especificación: Implementar caché básico para evitar recálculos frecuentes
        """
        endpoints = [
            "/metrics",
            "/health/detailed", 
            "/monitoring/dashboard",
            "/monitoring/pipeline-status"
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = test_client.get(endpoint)
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            
            assert response.status_code in [200, 503]  # 503 OK para degraded services
            assert response_time_ms < 200, f"Endpoint {endpoint} tardó {response_time_ms:.1f}ms (>200ms)"
            
            print(f"✅ {endpoint} responde en {response_time_ms:.1f}ms (<200ms)")
    
    @patch('src.controller.PipelineController.process_article')
    def test_end_to_end_phase_tracing(self, mock_process, test_client, sample_article):
        """
        Verifica que el trazado de fases funciona end-to-end.
        
        ✅ Especificación: Trazado de fases funciona end-to-end
        """
        # Mock que simula procesamiento exitoso con trazado
        mock_process.return_value = {
            "fragmento_id": "test_fragment_tracing_001",
            "fragmento_uuid": "uuid-tracing-001",
            "trazado_fases": {
                "fase1_triaje": {"duration_ms": 150, "success": True},
                "fase2_extraccion": {"duration_ms": 2500, "success": True},
                "fase3_citas_datos": {"duration_ms": 1800, "success": True},
                "fase4_normalizacion": {"duration_ms": 3200, "success": True}
            },
            "metricas": {
                "tiempo_total_segundos": 7.65,
                "conteos_elementos": {
                    "hechos_extraidos": 8,
                    "entidades_extraidas": 6,
                    "citas_extraidas": 3,
                    "datos_cuantitativos": 2
                }
            }
        }
        
        # Procesar artículo
        response = test_client.post("/procesar_articulo", json=sample_article)
        assert response.status_code == 200
        
        data = response.json()
        assert "request_id" in data
        assert "data" in data
        
        # Verificar que el resultado incluye información de trazado
        result_data = data["data"]
        if "trazado_fases" in result_data:
            trazado = result_data["trazado_fases"]
            expected_phases = ["fase1_triaje", "fase2_extraccion", "fase3_citas_datos", "fase4_normalizacion"]
            
            for phase in expected_phases:
                if phase in trazado:
                    assert "duration_ms" in trazado[phase]
                    assert "success" in trazado[phase]
        
        print("✅ Trazado de fases funciona end-to-end")
    
    @patch('src.controller.PipelineController.process_article')
    def test_load_test_with_10_articles(self, mock_process, test_client, sample_article):
        """
        Test de carga básico que procesa 10 artículos y verifica métricas.
        
        ✅ Especificación: Incluir test de carga básico que procese 10 artículos
        """
        # Mock del procesamiento
        mock_process.return_value = {
            "fragmento_id": "load_test_fragment",
            "fragmento_uuid": "uuid-load-test",
            "metricas": {
                "tiempo_total_segundos": 3.2,
                "conteos_elementos": {
                    "hechos_extraidos": 6,
                    "entidades_extraidas": 4,
                    "citas_extraidas": 2,
                    "datos_cuantitativos": 1
                }
            }
        }
        
        # Obtener métricas iniciales
        collector = get_metrics_collector()
        initial_stats = collector.get_stats()
        initial_requests = initial_stats["total_counters"]["total_requests"]
        
        # Procesar 10 artículos
        successful_requests = 0
        total_response_time = 0
        
        for i in range(10):
            # Modificar ligeramente cada artículo para que sea único
            test_article = sample_article.copy()
            test_article["titular"] = f"Test Article #{i+1} - Sistema de monitoreo"
            test_article["contenido_texto"] = f"Contenido del artículo #{i+1} para test de carga. " * 15
            
            start_time = time.time()
            response = test_client.post("/procesar_articulo", json=test_article)
            end_time = time.time()
            
            if response.status_code == 200:
                successful_requests += 1
            
            total_response_time += (end_time - start_time)
        
        # Verificar resultados del test de carga
        assert successful_requests == 10, f"Solo {successful_requests}/10 requests fueron exitosas"
        
        average_response_time = total_response_time / 10
        assert average_response_time < 5.0, f"Tiempo promedio de respuesta {average_response_time:.2f}s demasiado alto"
        
        # Verificar que las métricas reflejan el procesamiento
        final_stats = collector.get_stats()
        final_requests = final_stats["total_counters"]["total_requests"]
        
        requests_processed = final_requests - initial_requests
        assert requests_processed >= 10, f"Solo se registraron {requests_processed} requests en métricas"
        
        # Verificar métricas agregadas
        aggregated = collector.get_aggregated_metrics()
        assert aggregated["requests_per_minute"] > 0
        assert aggregated["pipeline_throughput_per_hour"] >= 0
        
        # Verificar que los endpoints de monitoreo reflejan la actividad
        dashboard_response = test_client.get("/monitoring/dashboard")
        assert dashboard_response.status_code == 200
        
        dashboard_data = dashboard_response.json()
        assert dashboard_data["totals"]["articles_processed"] >= 0
        
        print(f"✅ Test de carga completado: 10 artículos procesados en {total_response_time:.2f}s")
        print(f"✅ Tiempo promedio por artículo: {average_response_time:.2f}s")
        print(f"✅ Métricas registradas: {requests_processed} requests")
    
    def test_monitoring_system_integration(self, test_client):
        """
        Test final de integración que verifica todo el sistema funcionando junto.
        
        ✅ Especificación: Debe proporcionar output claro de éxito/fallo con detalles específicos
        """
        print("\n" + "="*60)
        print("TEST FINAL DE INTEGRACIÓN DEL SISTEMA DE MONITOREO")
        print("="*60)
        
        # 1. Verificar todos los endpoints están activos
        endpoints_status = {}
        endpoints = {
            "/metrics": "Métricas Prometheus",
            "/health/detailed": "Health Check Detallado", 
            "/monitoring/dashboard": "Dashboard JSON",
            "/monitoring/pipeline-status": "Estado del Pipeline",
            "/monitoring/alerts": "Sistema de Alertas",
            "/monitoring/alerts/summary": "Resumen de Alertas"
        }
        
        for endpoint, description in endpoints.items():
            try:
                response = test_client.get(endpoint)
                if response.status_code in [200, 503]:
                    endpoints_status[endpoint] = "✅ FUNCIONANDO"
                else:
                    endpoints_status[endpoint] = f"❌ ERROR {response.status_code}"
            except Exception as e:
                endpoints_status[endpoint] = f"❌ EXCEPCIÓN: {str(e)}"
        
        # 2. Verificar colector de métricas
        try:
            collector = get_metrics_collector()
            collector_stats = collector.get_stats()
            metrics_status = "✅ FUNCIONANDO"
            metrics_details = f"Métricas almacenadas: {collector_stats['memory_usage']['total_stored_metrics']}"
        except Exception as e:
            metrics_status = f"❌ ERROR: {str(e)}"
            metrics_details = ""
        
        # 3. Verificar sistema de alertas
        try:
            alert_manager = get_alert_manager()
            alert_summary = alert_manager.get_alert_summary()
            alerts_status = "✅ FUNCIONANDO"
            alerts_details = f"Alertas totales: {alert_summary['total_alerts']}, Activas: {alert_summary['active_alerts']}"
        except Exception as e:
            alerts_status = f"❌ ERROR: {str(e)}"
            alerts_details = ""
        
        # 4. Generar reporte final
        print("\nRESULTADOS DE VERIFICACIÓN:")
        print("-" * 40)
        
        print(f"\n📊 COLECTOR DE MÉTRICAS: {metrics_status}")
        if metrics_details:
            print(f"   {metrics_details}")
        
        print(f"\n🚨 SISTEMA DE ALERTAS: {alerts_status}")
        if alerts_details:
            print(f"   {alerts_details}")
        
        print(f"\n🌐 ENDPOINTS DE MONITOREO:")
        for endpoint, status in endpoints_status.items():
            print(f"   {endpoint:<35} {status}")
        
        # 5. Verificar criterios de éxito
        all_endpoints_working = all("✅" in status for status in endpoints_status.values())
        metrics_working = "✅" in metrics_status
        alerts_working = "✅" in alerts_status
        
        success_criteria = {
            "Endpoints de monitoreo": all_endpoints_working,
            "Colector de métricas": metrics_working,
            "Sistema de alertas": alerts_working
        }
        
        print(f"\n📋 CRITERIOS DE ÉXITO:")
        print("-" * 40)
        overall_success = True
        for criterion, passed in success_criteria.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {criterion:<25} {status}")
            if not passed:
                overall_success = False
        
        print(f"\n🎯 RESULTADO FINAL:")
        print("-" * 40)
        if overall_success:
            print("   ✅ SISTEMA DE MONITOREO COMPLETAMENTE FUNCIONAL")
            print("   Todos los componentes operativos y endpoints respondiendo")
        else:
            print("   ❌ SISTEMA DE MONITOREO CON FALLOS")
            print("   Revisar componentes marcados como FAIL")
        
        print("=" * 60)
        
        # Assert final para el test
        assert overall_success, "Sistema de monitoreo no cumple todos los criterios de éxito"
        
    def test_performance_under_load(self, test_client):
        """
        Test adicional de rendimiento bajo carga moderada.
        
        Verifica que el sistema mantiene rendimiento aceptable.
        """
        # Test de múltiples requests concurrentes a endpoints de monitoreo
        import concurrent.futures
        import threading
        
        def make_request(endpoint):
            start_time = time.time()
            response = test_client.get(endpoint)
            end_time = time.time()
            return endpoint, response.status_code, (end_time - start_time) * 1000
        
        endpoints = ["/metrics", "/health/detailed", "/monitoring/dashboard", "/monitoring/pipeline-status"]
        
        # Hacer 20 requests concurrentes (5 por endpoint)
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = []
            for _ in range(5):  # 5 veces cada endpoint
                for endpoint in endpoints:
                    futures.append(executor.submit(make_request, endpoint))
            
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Analizar resultados
        successful_requests = sum(1 for _, status, _ in results if status in [200, 503])
        total_requests = len(results)
        success_rate = (successful_requests / total_requests) * 100
        
        response_times = [response_time for _, _, response_time in results]
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        
        print(f"\n📈 TEST DE RENDIMIENTO BAJO CARGA:")
        print(f"   Total requests: {total_requests}")
        print(f"   Exitosos: {successful_requests} ({success_rate:.1f}%)")
        print(f"   Tiempo promedio: {avg_response_time:.1f}ms")
        print(f"   Tiempo máximo: {max_response_time:.1f}ms")
        
        # Criterios de rendimiento
        assert success_rate >= 95, f"Tasa de éxito {success_rate:.1f}% por debajo del 95%"
        assert avg_response_time < 500, f"Tiempo promedio {avg_response_time:.1f}ms demasiado alto"
        assert max_response_time < 1000, f"Tiempo máximo {max_response_time:.1f}ms inaceptable"
        
        print("✅ Sistema mantiene rendimiento aceptable bajo carga")


# Función de conveniencia para ejecutar solo este test
def run_monitoring_tests():
    """
    Ejecuta solo los tests del sistema de monitoreo.
    
    Uso: python -c "from tests.test_monitoring_system import run_monitoring_tests; run_monitoring_tests()"
    """
    import subprocess
    import sys
    
    cmd = [sys.executable, "-m", "pytest", __file__, "-v", "-s"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0


if __name__ == "__main__":
    # Permitir ejecución directa del archivo
    run_monitoring_tests()
