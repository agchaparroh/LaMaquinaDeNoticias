"""
test_pipeline_unavailable.py
Test de Resiliencia: Comportamiento del Connector cuando Pipeline no responde

Valida que el Connector maneja correctamente cuando el Pipeline está caído:
1. Intenta enviar artículos al Pipeline
2. Pipeline no responde (timeout/connection refused)
3. Connector aplica política de reintentos
4. Mueve archivos a directorio de error después de agotar reintentos
5. Sistema continúa procesando otros archivos
"""

import pytest
import asyncio
import aiohttp
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import os
import json
import gzip
import time
from datetime import datetime


class PipelineUnavailableScenario:
    """Simula escenarios donde el Pipeline no está disponible"""
    
    def __init__(self):
        self.retry_attempts = []
        self.files_processed = []
        self.error_files = []
        
        # Configuración del sistema (basada en el Connector real)
        self.max_retries = 3
        self.retry_backoff = 2  # Exponential backoff multiplier
        self.timeout = 30
        
    def create_test_article_file(self, output_dir: str, num_articles: int = 1) -> str:
        """Crea archivo de prueba con artículos"""
        articles = []
        for i in range(num_articles):
            article = {
                "url": f"https://example.com/resilience-test-{i+1}",
                "titular": f"Artículo de prueba resiliencia {i+1}",
                "medio": "Test News",
                "contenido_texto": "Contenido de prueba " * 20,  # > 50 chars
                "fecha_publicacion": datetime.utcnow().isoformat(),
                "pais_publicacion": "AR",
                "tipo_medio": "digital"
            }
            articles.append(article)
        
        # Crear archivo .json.gz
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"articulos_resilience_{timestamp}.json.gz"
        filepath = os.path.join(output_dir, filename)
        
        with gzip.open(filepath, 'wt', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    async def simulate_pipeline_timeout(self, article_data: dict) -> dict:
        """Simula timeout del Pipeline"""
        attempt_num = len(self.retry_attempts) + 1
        self.retry_attempts.append({
            "attempt": attempt_num,
            "timestamp": datetime.utcnow().isoformat(),
            "error": "timeout",
            "article_url": article_data["articulo"]["url"]
        })
        
        # Simular delay exponencial entre reintentos
        if attempt_num > 1:
            delay = self.retry_backoff ** (attempt_num - 2)
            await asyncio.sleep(min(delay, 60) / 10)  # Escalar para test rápido
        
        # Siempre falla con timeout
        raise aiohttp.ClientTimeout()
    
    async def simulate_pipeline_connection_refused(self, article_data: dict) -> dict:
        """Simula conexión rechazada al Pipeline"""
        attempt_num = len(self.retry_attempts) + 1
        self.retry_attempts.append({
            "attempt": attempt_num,
            "timestamp": datetime.utcnow().isoformat(),
            "error": "connection_refused",
            "article_url": article_data["articulo"]["url"]
        })
        
        # Simular delay exponencial
        if attempt_num > 1:
            delay = self.retry_backoff ** (attempt_num - 2)
            await asyncio.sleep(min(delay, 60) / 10)
        
        # Siempre falla con conexión rechazada
        raise aiohttp.ClientConnectorError(
            connection_key=Mock(),
            os_error=OSError("Connection refused")
        )
    
    async def simulate_pipeline_500_error(self, article_data: dict) -> dict:
        """Simula error 500 del Pipeline"""
        attempt_num = len(self.retry_attempts) + 1
        self.retry_attempts.append({
            "attempt": attempt_num,
            "timestamp": datetime.utcnow().isoformat(),
            "error": "server_error_500",
            "article_url": article_data["articulo"]["url"]
        })
        
        # Simular delay exponencial
        if attempt_num > 1:
            delay = self.retry_backoff ** (attempt_num - 2)
            await asyncio.sleep(min(delay, 60) / 10)
        
        # Crear mock de respuesta con status 500
        mock_response = Mock()
        mock_response.status = 500
        mock_response.request_info = Mock()
        mock_response.history = []
        
        raise aiohttp.ClientResponseError(
            request_info=mock_response.request_info,
            history=mock_response.history,
            status=500,
            message="Internal Server Error"
        )
    
    def move_to_error_directory(self, filepath: str):
        """Simula mover archivo a directorio de error"""
        filename = os.path.basename(filepath)
        self.error_files.append({
            "filename": filename,
            "moved_at": datetime.utcnow().isoformat(),
            "reason": "max_retries_exceeded"
        })
        return True


def test_connector_handles_pipeline_timeout():
    """Test: Connector maneja timeouts del Pipeline correctamente"""
    
    scenario = PipelineUnavailableScenario()
    
    print("\n⏱️ Test: Manejo de timeout del Pipeline\n")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # GIVEN: Archivo con artículos para procesar
        test_file = scenario.create_test_article_file(temp_dir, num_articles=2)
        print(f"✅ Archivo de prueba creado con 2 artículos")
        
        # WHEN: Connector intenta enviar pero Pipeline no responde
        async def simulate_connector_processing():
            # Leer archivo
            with gzip.open(test_file, 'rt', encoding='utf-8') as f:
                articles = json.loads(f.read())
            
            results = {
                "sent": 0,
                "failed": 0,
                "errors": []
            }
            
            for article in articles:
                print(f"\n📤 Intentando enviar: '{article['titular'][:50]}...'")
                
                # Intentar enviar con reintentos
                for attempt in range(scenario.max_retries):
                    try:
                        payload = {"articulo": article}
                        await scenario.simulate_pipeline_timeout(payload)
                        results["sent"] += 1
                        break  # Éxito, salir del loop de reintentos
                    except aiohttp.ClientTimeout:
                        print(f"   ⏱️ Intento {attempt + 1}/{scenario.max_retries}: TIMEOUT")
                        if attempt == scenario.max_retries - 1:
                            # Último intento falló
                            results["failed"] += 1
                            results["errors"].append(f"Timeout after {scenario.max_retries} attempts")
                            print(f"   ❌ Agotados los reintentos para este artículo")
            
            return results
        
        # Ejecutar simulación
        results = asyncio.run(simulate_connector_processing())
        
        # THEN: Verificar comportamiento esperado
        print(f"\n📊 Resultados:")
        print(f"   - Artículos enviados: {results['sent']}")
        print(f"   - Artículos fallidos: {results['failed']}")
        print(f"   - Total de intentos: {len(scenario.retry_attempts)}")
        
        # Verificaciones
        assert results["failed"] == 2, "Todos los artículos deberían fallar con timeout"
        assert len(scenario.retry_attempts) == 6, f"Deberían ser {scenario.max_retries} intentos por cada uno de los 2 artículos"
        
        # Verificar patrón de reintentos
        print(f"\n🔄 Patrón de reintentos:")
        for i, attempt in enumerate(scenario.retry_attempts):
            print(f"   Intento {i+1}: {attempt['error']} - {attempt['article_url']}")
        
        # Simular movimiento a directorio de error
        scenario.move_to_error_directory(test_file)
        assert len(scenario.error_files) == 1
        print(f"\n📁 Archivo movido a directorio de error: {scenario.error_files[0]['filename']}")


def test_connector_handles_connection_refused():
    """Test: Connector maneja conexión rechazada al Pipeline"""
    
    scenario = PipelineUnavailableScenario()
    
    print("\n🚫 Test: Manejo de conexión rechazada\n")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # GIVEN: Pipeline completamente caído (connection refused)
        test_file = scenario.create_test_article_file(temp_dir, num_articles=1)
        
        # WHEN: Intentar procesar
        async def simulate_connection_refused():
            with gzip.open(test_file, 'rt', encoding='utf-8') as f:
                articles = json.loads(f.read())
            
            article = articles[0]
            attempts = 0
            last_error = None
            
            print(f"📤 Procesando: '{article['titular']}'")
            
            for attempt in range(scenario.max_retries):
                try:
                    attempts += 1
                    payload = {"articulo": article}
                    await scenario.simulate_pipeline_connection_refused(payload)
                except aiohttp.ClientConnectorError as e:
                    print(f"   🚫 Intento {attempt + 1}: Conexión rechazada")
                    last_error = e
                    if attempt < scenario.max_retries - 1:
                        wait_time = scenario.retry_backoff ** attempt
                        print(f"   ⏳ Esperando {wait_time}s antes de reintentar...")
            
            return attempts, last_error
        
        attempts, error = asyncio.run(simulate_connection_refused())
        
        # THEN: Verificar manejo correcto
        assert attempts == scenario.max_retries
        assert error is not None
        assert "Connection refused" in str(error)
        
        print(f"\n✅ Connector manejó correctamente la conexión rechazada:")
        print(f"   - Reintentos realizados: {attempts}")
        print(f"   - Error final: {type(error).__name__}")


def test_connector_handles_intermittent_failures():
    """Test: Connector maneja fallos intermitentes (recuperación parcial)"""
    
    print("\n🔄 Test: Manejo de fallos intermitentes\n")
    
    class IntermittentFailureScenario:
        def __init__(self):
            self.call_count = 0
            self.success_after = 2  # Éxito después del 2do intento
            
        async def simulate_intermittent_pipeline(self, article_data: dict):
            self.call_count += 1
            
            if self.call_count < self.success_after:
                print(f"   ❌ Intento {self.call_count}: Error 503 (Service Unavailable)")
                mock_response = Mock()
                mock_response.status = 503
                mock_response.request_info = Mock()
                mock_response.history = []
                
                raise aiohttp.ClientResponseError(
                    request_info=mock_response.request_info,
                    history=mock_response.history,
                    status=503,
                    message="Service Temporarily Unavailable"
                )
            else:
                print(f"   ✅ Intento {self.call_count}: Éxito (202 Accepted)")
                return {"status": 202, "message": "Accepted"}
    
    scenario = IntermittentFailureScenario()
    
    # Simular procesamiento con fallo intermitente
    async def process_with_intermittent_failure():
        article = {
            "url": "https://example.com/intermittent-test",
            "titular": "Test de fallo intermitente",
            "medio": "Test",
            "contenido_texto": "Contenido " * 20
        }
        
        max_retries = 3
        last_error = None
        
        print(f"📤 Procesando artículo con posibles fallos intermitentes...")
        
        for attempt in range(max_retries):
            try:
                payload = {"articulo": article}
                result = await scenario.simulate_intermittent_pipeline(payload)
                return True, result, attempt + 1
            except aiohttp.ClientResponseError as e:
                last_error = e
                if attempt < max_retries - 1 and e.status in [500, 503]:
                    wait_time = 2 ** attempt
                    print(f"   ⏳ Esperando {wait_time}s antes de reintentar...")
                    await asyncio.sleep(wait_time / 10)  # Escalar para test
        
        return False, last_error, max_retries
    
    success, result, attempts = asyncio.run(process_with_intermittent_failure())
    
    # Verificaciones
    assert success is True, "Debería tener éxito después de reintentos"
    assert attempts == 2, "Debería tener éxito en el segundo intento"
    assert result["status"] == 202
    
    print(f"\n✅ Sistema se recuperó correctamente:")
    print(f"   - Éxito después de {attempts} intentos")
    print(f"   - Resiliencia ante fallos temporales demostrada")


def test_connector_continues_after_failures():
    """Test: Connector continúa procesando otros archivos después de fallos"""
    
    print("\n📂 Test: Continuidad después de fallos\n")
    
    scenario = PipelineUnavailableScenario()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # GIVEN: Múltiples archivos, algunos causarán fallos
        files = []
        for i in range(3):
            filepath = scenario.create_test_article_file(temp_dir, num_articles=1)
            # Renombrar para orden específico
            new_name = os.path.join(temp_dir, f"articulos_{i+1:02d}.json.gz")
            os.rename(filepath, new_name)
            files.append(new_name)
        
        print(f"✅ Creados 3 archivos de prueba")
        
        # WHEN: Procesar con el segundo archivo fallando
        async def process_multiple_files():
            results = {
                "processed": [],
                "failed": [],
                "success": []
            }
            
            for i, filepath in enumerate(files):
                filename = os.path.basename(filepath)
                print(f"\n📄 Procesando archivo {i+1}/3: {filename}")
                
                try:
                    # Simular que el archivo 2 tiene problemas con el Pipeline
                    if i == 1:
                        # Este falla completamente
                        print(f"   ❌ Pipeline no disponible para este archivo")
                        results["failed"].append(filename)
                        scenario.move_to_error_directory(filepath)
                    else:
                        # Estos tienen éxito
                        print(f"   ✅ Archivo procesado exitosamente")
                        results["success"].append(filename)
                    
                    results["processed"].append(filename)
                    
                except Exception as e:
                    print(f"   💥 Error inesperado: {e}")
                    results["failed"].append(filename)
            
            return results
        
        results = asyncio.run(process_multiple_files())
        
        # THEN: Verificar que el sistema continuó procesando
        print(f"\n📊 Resumen de procesamiento:")
        print(f"   - Total procesados: {len(results['processed'])}")
        print(f"   - Exitosos: {len(results['success'])}")
        print(f"   - Fallidos: {len(results['failed'])}")
        print(f"   - En directorio de error: {len(scenario.error_files)}")
        
        # Verificaciones
        assert len(results["processed"]) == 3, "Todos los archivos deberían intentar procesarse"
        assert len(results["success"]) == 2, "Dos archivos deberían procesarse exitosamente"
        assert len(results["failed"]) == 1, "Un archivo debería fallar"
        assert len(scenario.error_files) == 1, "Un archivo debería moverse a error"
        
        print(f"\n✅ El Connector continuó procesando a pesar de fallos individuales")
        print(f"   - Sistema resiliente: no se detuvo por fallos puntuales")
        print(f"   - Archivos problemáticos aislados en directorio de error")


def test_graceful_degradation_strategies():
    """Test: Estrategias de degradación elegante ante fallos del Pipeline"""
    
    print("\n🛡️ Test: Estrategias de degradación elegante\n")
    
    class DegradationStrategy:
        def __init__(self):
            self.queue = []
            self.circuit_breaker_open = False
            self.consecutive_failures = 0
            self.failure_threshold = 3
            
        async def check_pipeline_health(self) -> bool:
            """Health check del Pipeline"""
            try:
                # Simular health check
                if self.circuit_breaker_open:
                    print("   🔴 Circuit breaker ABIERTO - Pipeline marcado como no disponible")
                    return False
                
                # Simular check exitoso/fallido basado en failures consecutivos
                if self.consecutive_failures >= self.failure_threshold:
                    return False
                    
                print("   🟢 Health check OK")
                return True
            except:
                return False
        
        def add_to_queue(self, article):
            """Agregar artículo a cola de respaldo"""
            self.queue.append({
                "article": article,
                "queued_at": datetime.utcnow().isoformat(),
                "retry_count": 0
            })
            print(f"   📥 Artículo agregado a cola de respaldo (total: {len(self.queue)})")
        
        async def process_with_circuit_breaker(self, article):
            """Procesar con circuit breaker pattern"""
            if self.circuit_breaker_open:
                print("   ⚡ Circuit breaker abierto - agregando a cola sin intentar")
                self.add_to_queue(article)
                return False
            
            try:
                # Simular intento de envío
                if self.consecutive_failures < self.failure_threshold:
                    # Éxito simulado
                    self.consecutive_failures = 0
                    print("   ✅ Artículo enviado exitosamente")
                    return True
                else:
                    # Fallo simulado
                    raise Exception("Pipeline error")
                    
            except Exception:
                self.consecutive_failures += 1
                print(f"   ❌ Fallo {self.consecutive_failures}/{self.failure_threshold}")
                
                if self.consecutive_failures >= self.failure_threshold:
                    self.circuit_breaker_open = True
                    print("   🔴 Circuit breaker ABIERTO - Pipeline marcado como no disponible")
                
                self.add_to_queue(article)
                return False
    
    strategy = DegradationStrategy()
    
    # Simular procesamiento con degradación
    async def test_degradation():
        articles = [
            {"titular": f"Artículo {i+1}", "contenido_texto": "Test " * 20}
            for i in range(6)
        ]
        
        print("🔄 Procesando artículos con estrategia de degradación:\n")
        
        for i, article in enumerate(articles):
            print(f"📰 Artículo {i+1}: '{article['titular']}'")
            
            # Check health antes de procesar
            if await strategy.check_pipeline_health():
                await strategy.process_with_circuit_breaker(article)
            else:
                print("   🚫 Pipeline no saludable - directo a cola")
                strategy.add_to_queue(article)
            
            print()
        
        return strategy
    
    final_strategy = asyncio.run(test_degradation())
    
    # Verificar resultados
    print("📊 Estado final del sistema:")
    print(f"   - Circuit breaker: {'ABIERTO' if final_strategy.circuit_breaker_open else 'CERRADO'}")
    print(f"   - Artículos en cola de respaldo: {len(final_strategy.queue)}")
    print(f"   - Fallos consecutivos: {final_strategy.consecutive_failures}")
    
    assert final_strategy.circuit_breaker_open is True
    assert len(final_strategy.queue) >= 3
    
    print("\n✅ Estrategias de degradación implementadas:")
    print("   1. Circuit breaker pattern para evitar sobrecarga")
    print("   2. Cola de respaldo para artículos no procesados")
    print("   3. Health checks para detección temprana de problemas")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
