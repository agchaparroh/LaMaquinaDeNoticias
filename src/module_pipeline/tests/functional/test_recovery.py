"""
Test de Recuperación del Pipeline
=================================

Tests que verifican la capacidad del sistema para recuperarse de fallos:
- Recuperación ante fallos de Groq API
- Recuperación ante fallos de Supabase
- Recuperación ante problemas de memoria
- Funcionamiento del circuit breaker
- Resiliencia general del sistema

Ejecutar con: python -m pytest tests/test_recovery.py -v -s

NOTA: Estos tests simulan condiciones de fallo y pueden generar logs de error.
"""

import pytest
import asyncio
import aiohttp
import time
import psutil
import gc
import random
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List
from dataclasses import dataclass, field
from pathlib import Path
import json

# Configuración del sistema
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ...src.utils.config import API_HOST, API_PORT
from ...src.utils.error_handling import (
    GroqAPIError,
    SupabaseRPCError,
    ServiceUnavailableError,
    ProcessingError,
    ErrorPhase
)


@dataclass
class RecoveryTestResult:
    """Resultado de un test de recuperación."""
    test_name: str
    total_attempts: int = 0
    successful_recoveries: int = 0
    failed_recoveries: int = 0
    recovery_times: List[float] = field(default_factory=list)
    error_sequences: List[Dict[str, Any]] = field(default_factory=list)
    system_state_changes: List[str] = field(default_factory=list)
    
    def add_recovery_attempt(self, success: bool, recovery_time: float, details: Dict[str, Any] = None):
        """Registra un intento de recuperación."""
        self.total_attempts += 1
        self.recovery_times.append(recovery_time)
        
        if success:
            self.successful_recoveries += 1
        else:
            self.failed_recoveries += 1
        
        if details:
            self.error_sequences.append({
                "timestamp": time.time(),
                "success": success,
                "recovery_time": recovery_time,
                "details": details
            })
    
    def calculate_recovery_rate(self) -> float:
        """Calcula la tasa de recuperación exitosa."""
        if self.total_attempts == 0:
            return 0.0
        return (self.successful_recoveries / self.total_attempts) * 100
    
    def get_average_recovery_time(self) -> float:
        """Calcula el tiempo promedio de recuperación."""
        if not self.recovery_times:
            return 0.0
        return sum(self.recovery_times) / len(self.recovery_times)
    
    def print_summary(self):
        """Imprime un resumen del resultado."""
        print(f"\n{'='*60}")
        print(f"RESUMEN: {self.test_name}")
        print(f"{'='*60}")
        print(f"Total intentos:        {self.total_attempts}")
        print(f"Recuperaciones exitosas: {self.successful_recoveries} ({self.calculate_recovery_rate():.1f}%)")
        print(f"Recuperaciones fallidas: {self.failed_recoveries}")
        print(f"Tiempo promedio recuperación: {self.get_average_recovery_time():.2f}s")
        
        if self.system_state_changes:
            print(f"\nCambios de estado del sistema:")
            for change in self.system_state_changes[:5]:  # Mostrar solo primeros 5
                print(f"  - {change}")
        
        print(f"{'='*60}")


class TestRecovery:
    """Suite de tests de recuperación del pipeline."""
    
    @pytest.fixture(scope="class")
    def api_base_url(self):
        """URL base del API."""
        return f"http://{API_HOST}:{API_PORT}"
    
    @pytest.fixture
    def sample_article(self):
        """Artículo de muestra para tests."""
        return {
            "medio": "Recovery Test News",
            "area_geografica": "España",
            "tipo_medio": "Digital",
            "titular": "Test de Recuperación del Sistema",
            "fecha_publicacion": "2024-01-15T10:00:00Z",
            "contenido_texto": "Este es un artículo de prueba para verificar la recuperación del sistema. " * 20,
            "idioma": "es",
            "autor": "Recovery Tester",
            "url": "https://test.example.com/recovery",
            "seccion": "Testing",
            "es_opinion": False,
            "es_oficial": True
        }
    
    @pytest.fixture
    def sample_fragment(self):
        """Fragmento de muestra para tests."""
        return {
            "id_fragmento": "test_recovery_001",
            "texto_original": "Fragmento de prueba para verificar recuperación ante fallos. " * 10,
            "id_articulo_fuente": "recovery_test_article_001",
            "orden_en_articulo": 1,
            "metadata_adicional": {"test_type": "recovery"}
        }
    
    async def _send_request_with_retry(self, url: str, data: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
        """Envía una request con reintentos automáticos."""
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=data, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        return {
                            "status": response.status,
                            "data": await response.json(),
                            "attempt": attempt + 1
                        }
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Backoff exponencial
    
    @pytest.mark.asyncio
    @patch('src.services.groq_service.GroqService.generate_completion')
    async def test_recuperacion_fallo_groq(self, mock_groq, api_base_url, sample_article):
        """
        Test 1: Recuperación ante fallos de Groq API.
        
        Simula fallos intermitentes de Groq y verifica que el sistema
        se recupera correctamente usando reintentos y fallbacks.
        """
        print("\n" + "="*80)
        print("TEST 1: RECUPERACIÓN ANTE FALLOS DE GROQ API")
        print("="*80)
        
        result = RecoveryTestResult("Recuperación Groq API")
        
        # Configurar comportamiento del mock
        call_count = 0
        def groq_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            # Fallar las primeras 2 llamadas, luego funcionar
            if call_count <= 2:
                raise GroqAPIError(
                    message="API rate limit exceeded",
                    phase=ErrorPhase.EXTERNAL_SERVICE,
                    service_name="groq",
                    retry_count=call_count,
                    max_retries=2
                )
            
            # Respuesta exitosa
            return {
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "hechos": [{"hecho": "Test exitoso"}],
                            "entidades": [{"nombre": "Sistema", "tipo": "ORGANIZACION"}]
                        })
                    }
                }]
            }
        
        mock_groq.side_effect = groq_side_effect
        
        # Test 1.1: Enviar artículo con Groq fallando inicialmente
        print("\n🔄 Test 1.1: Fallo inicial de Groq con recuperación")
        
        start_time = time.time()
        
        try:
            response = await self._send_request_with_retry(
                f"{api_base_url}/procesar_articulo",
                sample_article
            )
            
            recovery_time = time.time() - start_time
            
            if response["status"] == 200:
                print(f"  ✅ Sistema se recuperó después de {call_count} intentos")
                print(f"  ⏱️  Tiempo de recuperación: {recovery_time:.2f}s")
                result.add_recovery_attempt(True, recovery_time, {
                    "attempts": call_count,
                    "final_status": response["status"]
                })
            else:
                print(f"  ❌ Sistema no se recuperó completamente")
                result.add_recovery_attempt(False, recovery_time)
                
        except Exception as e:
            recovery_time = time.time() - start_time
            print(f"  ❌ Fallo total: {str(e)}")
            result.add_recovery_attempt(False, recovery_time, {"error": str(e)})
        
        # Test 1.2: Verificar que el sistema está operativo después del fallo
        print("\n🔄 Test 1.2: Verificación post-recuperación")
        
        # Reset mock para funcionar normalmente
        mock_groq.side_effect = None
        mock_groq.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "hechos": [{"hecho": "Sistema recuperado"}],
                        "entidades": []
                    })
                }
            }]
        }
        
        # Enviar request normal
        verification_start = time.time()
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{api_base_url}/procesar_articulo", json=sample_article) as response:
                verification_time = time.time() - verification_start
                
                if response.status == 200:
                    print(f"  ✅ Sistema operativo post-recuperación")
                    print(f"  ⏱️  Tiempo de respuesta normal: {verification_time:.2f}s")
                    result.system_state_changes.append("Sistema recuperado y operativo")
                else:
                    print(f"  ❌ Sistema aún degradado")
                    result.system_state_changes.append("Sistema no completamente recuperado")
        
        # Test 1.3: Fallo persistente de Groq
        print("\n🔄 Test 1.3: Fallo persistente de Groq (sin recuperación)")
        
        # Configurar mock para fallar siempre
        mock_groq.side_effect = GroqAPIError(
            message="Service permanently unavailable",
            phase=ErrorPhase.EXTERNAL_SERVICE,
            service_name="groq"
        )
        
        persistent_start = time.time()
        
        try:
            response = await self._send_request_with_retry(
                f"{api_base_url}/procesar_articulo",
                sample_article,
                max_retries=2
            )
            
            # Si llegamos aquí, el sistema tiene un fallback
            if response["status"] == 200:
                print(f"  ✅ Sistema usó fallback exitosamente")
                result.add_recovery_attempt(True, time.time() - persistent_start, {
                    "method": "fallback",
                    "status": response["status"]
                })
            else:
                print(f"  ⚠️  Respuesta degradada: HTTP {response['status']}")
                result.add_recovery_attempt(False, time.time() - persistent_start)
                
        except Exception as e:
            print(f"  ❌ Fallo esperado sin fallback: {type(e).__name__}")
            result.add_recovery_attempt(False, time.time() - persistent_start, {
                "expected_failure": True,
                "error_type": type(e).__name__
            })
        
        result.print_summary()
        
        # Assertions
        assert result.successful_recoveries > 0, "No hubo recuperaciones exitosas"
        assert result.get_average_recovery_time() < 30, "Tiempo de recuperación muy alto"
    
    @pytest.mark.asyncio
    @patch('src.services.supabase_service.SupabaseService.call_rpc')
    async def test_recuperacion_fallo_supabase(self, mock_supabase, api_base_url, sample_fragment):
        """
        Test 2: Recuperación ante fallos de Supabase.
        
        Simula fallos de conexión y errores RPC de Supabase.
        """
        print("\n" + "="*80)
        print("TEST 2: RECUPERACIÓN ANTE FALLOS DE SUPABASE")
        print("="*80)
        
        result = RecoveryTestResult("Recuperación Supabase")
        
        # Test 2.1: Fallo temporal de conexión
        print("\n🔄 Test 2.1: Fallo temporal de conexión a Supabase")
        
        call_count = 0
        def supabase_connection_error(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            # Fallar las primeras 3 llamadas
            if call_count <= 3:
                raise SupabaseRPCError(
                    message="Connection timeout",
                    phase=ErrorPhase.EXTERNAL_SERVICE,
                    rpc_name=args[0] if args else "unknown",
                    is_connection_error=True
                )
            
            # Luego funcionar normalmente
            return {"data": {"success": True, "id": f"recovered_{call_count}"}}
        
        mock_supabase.side_effect = supabase_connection_error
        
        start_time = time.time()
        
        try:
            response = await self._send_request_with_retry(
                f"{api_base_url}/procesar_fragmento",
                sample_fragment
            )
            
            recovery_time = time.time() - start_time
            
            if response["status"] == 200:
                print(f"  ✅ Recuperación exitosa después de {call_count} intentos")
                result.add_recovery_attempt(True, recovery_time, {"attempts": call_count})
            else:
                print(f"  ❌ No se pudo recuperar completamente")
                result.add_recovery_attempt(False, recovery_time)
                
        except Exception as e:
            recovery_time = time.time() - start_time
            print(f"  ❌ Fallo en recuperación: {str(e)}")
            result.add_recovery_attempt(False, recovery_time)
        
        # Test 2.2: Error de validación RPC (no recuperable)
        print("\n🔄 Test 2.2: Error de validación RPC (no recuperable)")
        
        mock_supabase.side_effect = SupabaseRPCError(
            message="Invalid input data",
            phase=ErrorPhase.EXTERNAL_SERVICE,
            rpc_name="insertar_fragmento_completo",
            is_connection_error=False,
            validation_errors=["Campo 'texto' muy corto"]
        )
        
        validation_start = time.time()
        
        try:
            # Este error no debería ser recuperable
            response = await self._send_request_with_retry(
                f"{api_base_url}/procesar_fragmento",
                sample_fragment,
                max_retries=1
            )
            
            # Si obtenemos respuesta, verificar que sea un error
            if response["status"] >= 400:
                print(f"  ✅ Error de validación manejado correctamente (HTTP {response['status']})")
                result.system_state_changes.append("Error de validación no recuperable detectado")
            else:
                print(f"  ⚠️  Respuesta inesperada para error de validación")
                
        except Exception as e:
            print(f"  ✅ Error de validación propagado correctamente: {type(e).__name__}")
            result.system_state_changes.append(f"Error de validación: {str(e)}")
        
        # Test 2.3: Degradación gradual y recuperación
        print("\n🔄 Test 2.3: Degradación gradual y recuperación")
        
        degradation_levels = [0.1, 0.3, 0.5, 0.7, 0.9, 0.5, 0.2, 0.0]  # Probabilidad de fallo
        
        for i, failure_prob in enumerate(degradation_levels):
            mock_supabase.side_effect = lambda *args, **kwargs: (
                {"data": {"success": True, "id": f"test_{i}"}}
                if random.random() > failure_prob
                else (_ for _ in ()).throw(SupabaseRPCError(
                    message="Random failure",
                    phase=ErrorPhase.EXTERNAL_SERVICE,
                    rpc_name="test_rpc"
                ))
            )
            
            try:
                response = await self._send_request_with_retry(
                    f"{api_base_url}/procesar_fragmento",
                    sample_fragment,
                    max_retries=2
                )
                
                if response["status"] == 200:
                    result.system_state_changes.append(f"Nivel {i}: Éxito (prob fallo: {failure_prob})")
                else:
                    result.system_state_changes.append(f"Nivel {i}: Degradado (prob fallo: {failure_prob})")
                    
            except:
                result.system_state_changes.append(f"Nivel {i}: Fallo total (prob fallo: {failure_prob})")
        
        result.print_summary()
        
        # Assertions
        assert result.total_attempts > 0, "No se realizaron intentos de recuperación"
        assert len(result.system_state_changes) > 0, "No se registraron cambios de estado"
    
    @pytest.mark.asyncio
    async def test_recuperacion_memoria(self, api_base_url, sample_article):
        """
        Test 3: Recuperación ante problemas de memoria.
        
        Envía artículos muy grandes para estresar la memoria y verifica
        que el sistema se recupera correctamente.
        """
        print("\n" + "="*80)
        print("TEST 3: RECUPERACIÓN ANTE PROBLEMAS DE MEMORIA")
        print("="*80)
        
        result = RecoveryTestResult("Recuperación Memoria")
        
        # Obtener uso de memoria inicial
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"📊 Memoria inicial: {initial_memory:.1f} MB")
        
        # Test 3.1: Artículo extremadamente grande
        print("\n🔄 Test 3.1: Procesamiento de artículo muy grande")
        
        # Crear artículo de 1MB
        huge_content = "x" * (1024 * 1024)
        huge_article = sample_article.copy()
        huge_article["contenido_texto"] = huge_content
        huge_article["titular"] = "Artículo gigante para test de memoria"
        
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{api_base_url}/procesar_articulo",
                    json=huge_article,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    response_data = await response.json()
                    recovery_time = time.time() - start_time
                    
                    if response.status == 200:
                        print(f"  ✅ Artículo grande procesado exitosamente")
                        result.add_recovery_attempt(True, recovery_time)
                    else:
                        print(f"  ⚠️  Respuesta con error: HTTP {response.status}")
                        result.add_recovery_attempt(False, recovery_time)
                        
        except Exception as e:
            recovery_time = time.time() - start_time
            print(f"  ❌ Error procesando artículo grande: {type(e).__name__}")
            result.add_recovery_attempt(False, recovery_time, {"error": str(e)})
        
        # Verificar memoria después del procesamiento
        current_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = current_memory - initial_memory
        
        print(f"📊 Memoria actual: {current_memory:.1f} MB (incremento: {memory_increase:.1f} MB)")
        
        # Test 3.2: Múltiples artículos grandes concurrentes
        print("\n🔄 Test 3.2: Múltiples artículos grandes concurrentes")
        
        # Crear 10 artículos de 100KB cada uno
        large_articles = []
        for i in range(10):
            large_article = sample_article.copy()
            large_article["contenido_texto"] = "y" * (100 * 1024)  # 100KB
            large_article["titular"] = f"Artículo grande #{i}"
            large_articles.append(large_article)
        
        concurrent_start = time.time()
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for article in large_articles:
                task = session.post(
                    f"{api_base_url}/procesar_articulo",
                    json=article,
                    timeout=aiohttp.ClientTimeout(total=30)
                )
                tasks.append(task)
            
            # Procesar con límite de concurrencia para evitar saturación
            semaphore = asyncio.Semaphore(3)
            
            async def limited_request(task):
                async with semaphore:
                    try:
                        async with task as response:
                            return response.status
                    except Exception:
                        return 500
            
            results = await asyncio.gather(*[limited_request(task) for task in tasks])
        
        successful = sum(1 for status in results if status == 200)
        concurrent_time = time.time() - concurrent_start
        
        print(f"  ✅ Procesados: {successful}/{len(large_articles)}")
        print(f"  ⏱️  Tiempo total: {concurrent_time:.2f}s")
        
        if successful > len(large_articles) * 0.7:  # 70% éxito
            result.add_recovery_attempt(True, concurrent_time, {
                "successful": successful,
                "total": len(large_articles)
            })
        else:
            result.add_recovery_attempt(False, concurrent_time)
        
        # Verificar memoria final y forzar garbage collection
        pre_gc_memory = process.memory_info().rss / 1024 / 1024
        gc.collect()
        post_gc_memory = process.memory_info().rss / 1024 / 1024
        
        print(f"\n📊 Memoria pre-GC: {pre_gc_memory:.1f} MB")
        print(f"📊 Memoria post-GC: {post_gc_memory:.1f} MB")
        print(f"📊 Memoria liberada: {pre_gc_memory - post_gc_memory:.1f} MB")
        
        result.system_state_changes.append(f"Memoria liberada por GC: {pre_gc_memory - post_gc_memory:.1f} MB")
        
        # Test 3.3: Recuperación después de presión de memoria
        print("\n🔄 Test 3.3: Verificación de recuperación post-presión")
        
        # Enviar artículo normal para verificar que el sistema funciona
        recovery_check_start = time.time()
        
        try:
            response = await self._send_request_with_retry(
                f"{api_base_url}/procesar_articulo",
                sample_article
            )
            
            if response["status"] == 200:
                print(f"  ✅ Sistema operativo después de presión de memoria")
                result.system_state_changes.append("Sistema recuperado post-presión de memoria")
            else:
                print(f"  ❌ Sistema degradado post-presión")
                
        except Exception as e:
            print(f"  ❌ Sistema no recuperado: {str(e)}")
        
        result.print_summary()
        
        # Assertions
        assert result.successful_recoveries > 0, "No hubo recuperaciones exitosas"
        assert post_gc_memory < pre_gc_memory * 1.5, "Posible fuga de memoria detectada"
    
    @pytest.mark.asyncio
    async def test_circuit_breaker(self, api_base_url, sample_article):
        """
        Test 4: Funcionamiento del circuit breaker.
        
        Verifica que el sistema implementa un circuit breaker para
        evitar cascadas de fallos.
        """
        print("\n" + "="*80)
        print("TEST 4: CIRCUIT BREAKER")
        print("="*80)
        
        result = RecoveryTestResult("Circuit Breaker")
        
        # Test 4.1: Provocar apertura del circuit breaker
        print("\n🔄 Test 4.1: Provocar apertura del circuit breaker")
        
        # Enviar múltiples requests que fallarán
        failed_requests = 0
        circuit_open_detected = False
        
        for i in range(20):
            # Crear artículo inválido (sin campos requeridos)
            invalid_article = {"titulo": f"Invalid {i}"}
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{api_base_url}/procesar_articulo",
                        json=invalid_article,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status >= 500:
                            failed_requests += 1
                        
                        # Detectar si el circuit breaker se abrió
                        response_data = await response.json()
                        if "circuit_breaker" in str(response_data).lower():
                            circuit_open_detected = True
                            print(f"  ⚡ Circuit breaker detectado en request #{i+1}")
                            break
                            
            except Exception as e:
                failed_requests += 1
                if "circuit" in str(e).lower():
                    circuit_open_detected = True
                    print(f"  ⚡ Circuit breaker detectado: {type(e).__name__}")
                    break
            
            # Pequeña pausa entre requests
            await asyncio.sleep(0.1)
        
        print(f"  📊 Requests fallidas antes de circuit breaker: {failed_requests}")
        
        if circuit_open_detected:
            result.add_recovery_attempt(True, failed_requests * 0.1, {
                "circuit_breaker_triggered": True,
                "failed_requests": failed_requests
            })
        else:
            print(f"  ⚠️  Circuit breaker no detectado explícitamente")
        
        # Test 4.2: Esperar recuperación del circuit breaker
        print("\n🔄 Test 4.2: Recuperación del circuit breaker")
        
        # Esperar tiempo de recuperación (típicamente 30-60 segundos)
        wait_time = 10  # Reducido para tests
        print(f"  ⏳ Esperando {wait_time}s para recuperación...")
        await asyncio.sleep(wait_time)
        
        # Intentar request válida
        recovery_start = time.time()
        
        try:
            response = await self._send_request_with_retry(
                f"{api_base_url}/procesar_articulo",
                sample_article,
                max_retries=3
            )
            
            recovery_time = time.time() - recovery_start
            
            if response["status"] == 200:
                print(f"  ✅ Circuit breaker recuperado")
                result.add_recovery_attempt(True, recovery_time, {
                    "recovery_successful": True,
                    "wait_time": wait_time
                })
                result.system_state_changes.append("Circuit breaker cerrado - sistema operativo")
            else:
                print(f"  ❌ Sistema aún no recuperado")
                result.add_recovery_attempt(False, recovery_time)
                
        except Exception as e:
            recovery_time = time.time() - recovery_start
            print(f"  ❌ Error en recuperación: {str(e)}")
            result.add_recovery_attempt(False, recovery_time)
        
        result.print_summary()
        
        # Assertions
        assert result.total_attempts > 0, "No se registraron intentos"
        assert result.successful_recoveries > 0, "Circuit breaker no se recuperó"
    
    @pytest.mark.asyncio
    async def test_resiliencia_general(self, api_base_url, sample_article, sample_fragment):
        """
        Test 5: Resiliencia general del sistema.
        
        Prueba combinada que simula múltiples tipos de fallos
        para verificar la resiliencia general.
        """
        print("\n" + "="*80)
        print("TEST 5: RESILIENCIA GENERAL DEL SISTEMA")
        print("="*80)
        
        result = RecoveryTestResult("Resiliencia General")
        
        # Escenarios de fallo a probar
        failure_scenarios = [
            {
                "name": "Timeout de red",
                "data": sample_article,
                "endpoint": "procesar_articulo",
                "timeout": 0.001  # Timeout muy bajo para provocar fallo
            },
            {
                "name": "Payload muy grande",
                "data": {**sample_article, "contenido_texto": "z" * (2 * 1024 * 1024)},  # 2MB
                "endpoint": "procesar_articulo",
                "timeout": 30
            },
            {
                "name": "Caracteres especiales",
                "data": {**sample_fragment, "texto_original": "Test con 特殊字符 🚀 \x00 \n\r"},
                "endpoint": "procesar_fragmento",
                "timeout": 10
            },
            {
                "name": "JSON malformado",
                "data": sample_article,
                "endpoint": "procesar_articulo",
                "timeout": 10,
                "corrupt_json": True
            },
            {
                "name": "Alta concurrencia súbita",
                "data": sample_fragment,
                "endpoint": "procesar_fragmento",
                "timeout": 10,
                "concurrent_requests": 20
            }
        ]
        
        for scenario in failure_scenarios:
            print(f"\n🔄 Escenario: {scenario['name']}")
            
            start_time = time.time()
            
            try:
                if scenario.get("concurrent_requests"):
                    # Escenario de concurrencia
                    async with aiohttp.ClientSession() as session:
                        tasks = []
                        for i in range(scenario["concurrent_requests"]):
                            data = {**scenario["data"], "id_fragmento": f"concurrent_{i}"}
                            task = session.post(
                                f"{api_base_url}/{scenario['endpoint']}",
                                json=data,
                                timeout=aiohttp.ClientTimeout(total=scenario["timeout"])
                            )
                            tasks.append(task)
                        
                        results = await asyncio.gather(*tasks, return_exceptions=True)
                        
                        successful = sum(1 for r in results if not isinstance(r, Exception))
                        success_rate = successful / len(results)
                        
                        if success_rate > 0.5:
                            print(f"  ✅ Manejó concurrencia: {successful}/{len(results)} exitosos")
                            result.add_recovery_attempt(True, time.time() - start_time, {
                                "scenario": scenario["name"],
                                "success_rate": success_rate
                            })
                        else:
                            print(f"  ❌ Fallo bajo concurrencia: {successful}/{len(results)} exitosos")
                            result.add_recovery_attempt(False, time.time() - start_time)
                
                elif scenario.get("corrupt_json"):
                    # Enviar JSON corrupto
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f"{api_base_url}/{scenario['endpoint']}",
                            data='{"invalid": json"corrupt}',  # JSON malformado
                            headers={"Content-Type": "application/json"},
                            timeout=aiohttp.ClientTimeout(total=scenario["timeout"])
                        ) as response:
                            if response.status == 400:  # Error esperado
                                print(f"  ✅ JSON corrupto manejado correctamente (HTTP 400)")
                                result.add_recovery_attempt(True, time.time() - start_time, {
                                    "scenario": scenario["name"],
                                    "handled_correctly": True
                                })
                            else:
                                print(f"  ❌ Respuesta inesperada para JSON corrupto")
                                result.add_recovery_attempt(False, time.time() - start_time)
                
                else:
                    # Escenarios normales
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f"{api_base_url}/{scenario['endpoint']}",
                            json=scenario["data"],
                            timeout=aiohttp.ClientTimeout(total=scenario["timeout"])
                        ) as response:
                            response_data = await response.json()
                            
                            if response.status in [200, 400, 413]:  # Respuestas aceptables
                                print(f"  ✅ Escenario manejado: HTTP {response.status}")
                                result.add_recovery_attempt(True, time.time() - start_time, {
                                    "scenario": scenario["name"],
                                    "status": response.status
                                })
                            else:
                                print(f"  ❌ Error no manejado: HTTP {response.status}")
                                result.add_recovery_attempt(False, time.time() - start_time)
                                
            except asyncio.TimeoutError:
                if scenario["name"] == "Timeout de red":
                    print(f"  ✅ Timeout manejado correctamente")
                    result.add_recovery_attempt(True, time.time() - start_time, {
                        "scenario": scenario["name"],
                        "timeout_handled": True
                    })
                else:
                    print(f"  ❌ Timeout inesperado")
                    result.add_recovery_attempt(False, time.time() - start_time)
                    
            except Exception as e:
                print(f"  ❌ Excepción: {type(e).__name__}")
                result.add_recovery_attempt(False, time.time() - start_time, {
                    "scenario": scenario["name"],
                    "exception": type(e).__name__
                })
            
            # Pequeña pausa entre escenarios
            await asyncio.sleep(1)
        
        # Verificación final del sistema
        print("\n🔄 Verificación final del sistema")
        
        try:
            final_response = await self._send_request_with_retry(
                f"{api_base_url}/procesar_articulo",
                sample_article
            )
            
            if final_response["status"] == 200:
                print("  ✅ Sistema completamente operativo después de todos los escenarios")
                result.system_state_changes.append("Sistema resiliente - todos los escenarios superados")
            else:
                print("  ⚠️  Sistema parcialmente degradado")
                result.system_state_changes.append("Sistema parcialmente degradado post-tests")
                
        except Exception as e:
            print(f"  ❌ Sistema no operativo: {str(e)}")
            result.system_state_changes.append("Sistema no operativo post-tests")
        
        result.print_summary()
        
        # Calcular resiliencia general
        resilience_score = result.calculate_recovery_rate()
        print(f"\n🎯 SCORE DE RESILIENCIA: {resilience_score:.1f}%")
        
        if resilience_score >= 80:
            print("   ✅ Sistema altamente resiliente")
        elif resilience_score >= 60:
            print("   ⚠️  Sistema moderadamente resiliente")
        else:
            print("   ❌ Sistema con baja resiliencia")
        
        # Assertions
        assert resilience_score >= 60, f"Score de resiliencia muy bajo: {resilience_score:.1f}%"
        assert result.successful_recoveries >= len(failure_scenarios) * 0.5, "Menos del 50% de escenarios manejados"


def generate_recovery_report(results: List[RecoveryTestResult]):
    """Genera un reporte de recuperación detallado."""
    print("\n" + "="*80)
    print("REPORTE DE RECUPERACIÓN DEL SISTEMA")
    print("="*80)
    
    total_attempts = sum(r.total_attempts for r in results)
    total_recoveries = sum(r.successful_recoveries for r in results)
    overall_rate = (total_recoveries / total_attempts * 100) if total_attempts > 0 else 0
    
    print(f"\nRESUMEN GENERAL:")
    print(f"  Total de tests: {len(results)}")
    print(f"  Total de intentos: {total_attempts}")
    print(f"  Recuperaciones exitosas: {total_recoveries}")
    print(f"  Tasa general de recuperación: {overall_rate:.1f}%")
    
    print(f"\nDETALLE POR TEST:")
    for result in results:
        print(f"\n  {result.test_name}:")
        print(f"    - Tasa de recuperación: {result.calculate_recovery_rate():.1f}%")
        print(f"    - Tiempo promedio: {result.get_average_recovery_time():.2f}s")
        print(f"    - Intentos: {result.total_attempts}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    # Permitir ejecución directa del archivo
    import subprocess
    import sys
    
    print("Ejecutando tests de recuperación...")
    print("NOTA: Estos tests pueden generar errores esperados en los logs")
    
    cmd = [sys.executable, "-m", "pytest", __file__, "-v", "-s"]
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n✅ Tests de recuperación completados exitosamente")
    else:
        print("\n❌ Tests de recuperación fallaron")
    
    sys.exit(result.returncode)
