"""
Test de Concurrencia del Pipeline
=================================

Tests exhaustivos que verifican el comportamiento del sistema bajo condiciones
de alta concurrencia, incluyendo:
- Race conditions en métricas compartidas
- Procesamiento paralelo masivo
- Límites de concurrencia del sistema
- Integridad de datos bajo concurrencia

Ejecutar con: python -m pytest tests/test_concurrency.py -v -s

ADVERTENCIA: Estos tests generan alta carga en el sistema.
"""

import asyncio
import multiprocessing  # noqa: F401
import random

# Configuración del sistema
import sys
import threading  # noqa: F401
import time
import uuid  # noqa: F401
from collections import Counter, defaultdict  # noqa: F401
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor  # noqa: F401
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Set

import aiohttp
import pytest

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.controller import PipelineController  # noqa: E402, F401
from src.monitoring.metrics_collector import get_metrics_collector  # noqa: E402, F401
from src.services.job_tracker_service import (  # noqa: E402, F401
    JobStatus,
    get_job_tracker_service,
)
from src.utils.config import API_HOST, API_PORT  # noqa: E402


@dataclass
class ConcurrencyTestResult:
    """Resultado de un test de concurrencia."""

    test_name: str
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    race_conditions_detected: int = 0
    data_inconsistencies: List[str] = field(default_factory=list)
    duplicate_ids: Set[str] = field(default_factory=set)
    missing_data: List[str] = field(default_factory=list)
    response_times: List[float] = field(default_factory=list)
    errors: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def add_error(self, error_type: str):
        """Registra un tipo de error."""
        self.errors[error_type] += 1

    def calculate_success_rate(self) -> float:
        """Calcula la tasa de éxito."""
        if self.total_operations == 0:
            return 0.0
        return (self.successful_operations / self.total_operations) * 100

    def print_summary(self):
        """Imprime un resumen del resultado."""
        print(f"\n{'=' * 60}")
        print(f"RESUMEN: {self.test_name}")
        print(f"{'=' * 60}")
        print(f"Total operaciones:      {self.total_operations}")
        print(
            f"Exitosas:              {self.successful_operations} ({self.calculate_success_rate():.1f}%)"
        )
        print(f"Fallidas:              {self.failed_operations}")
        print(f"Race conditions:       {self.race_conditions_detected}")
        print(f"Inconsistencias:       {len(self.data_inconsistencies)}")
        print(f"IDs duplicados:        {len(self.duplicate_ids)}")
        print(f"Datos faltantes:       {len(self.missing_data)}")

        if self.errors:
            print(f"\nErrores por tipo:")  # noqa: F541
            for error_type, count in self.errors.items():
                print(f"  {error_type}: {count}")

        if self.response_times:
            avg_time = sum(self.response_times) / len(self.response_times)
            print(f"\nTiempo respuesta promedio: {avg_time * 1000:.1f}ms")

        print(f"{'=' * 60}")


class TestConcurrency:
    """Suite de tests de concurrencia del pipeline."""

    @pytest.fixture(scope="class")
    def api_base_url(self):
        """URL base del API."""
        return f"http://{API_HOST}:{API_PORT}"

    @pytest.fixture(scope="class")
    def sample_article_factory(self):
        """Factory para generar artículos únicos."""

        def create_article(article_id: str, size: int = 5000) -> Dict[str, Any]:
            content = f"Artículo de prueba #{article_id}. " * (size // 30)
            return {
                "medio": f"Test News {article_id}",
                "area_geografica": "España",
                "tipo_medio": "Digital",
                "titular": f"Test Concurrencia - Artículo {article_id}",
                "fecha_publicacion": "2024-01-15T10:00:00Z",
                "contenido_texto": content[:size],
                "idioma": "es",
                "autor": f"Tester {article_id}",
                "url": f"https://test.example.com/concurrent-{article_id}",
                "seccion": "Testing",
                "es_opinion": False,
                "es_oficial": True,
                "metadata": {"test_id": article_id, "test_type": "concurrency"},
            }

        return create_article

    @pytest.fixture(scope="class")
    def sample_fragment_factory(self):
        """Factory para generar fragmentos únicos."""

        def create_fragment(fragment_id: str, size: int = 1000) -> Dict[str, Any]:
            content = f"Fragmento de prueba #{fragment_id}. " * (size // 30)
            return {
                "id_fragmento": f"test_concurrent_{fragment_id}",
                "texto_original": content[:size],
                "id_articulo_fuente": f"concurrent_article_{fragment_id}",
                "orden_en_articulo": 1,
                "metadata_adicional": {
                    "test_id": fragment_id,
                    "test_type": "concurrency",
                },
            }

        return create_fragment

    async def _send_request(
        self, session: aiohttp.ClientSession, endpoint: str, data: Dict[str, Any]
    ):
        """Envía una request y retorna (response_time, status_code, response_data)."""
        start_time = time.time()
        try:
            async with session.post(
                endpoint, json=data, timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                response_time = time.time() - start_time
                response_data = await response.json()
                return response_time, response.status, response_data
        except asyncio.TimeoutError:
            return time.time() - start_time, 504, {"error": "timeout"}
        except Exception as e:
            return time.time() - start_time, 500, {"error": str(e)}

    async def _send_article(
        self, session: aiohttp.ClientSession, endpoint: str, article: Dict[str, Any]
    ):
        """Envía un artículo y retorna la respuesta."""
        return await self._send_request(session, endpoint, article)

    async def _get_metrics(self, base_url: str) -> str:
        """Obtiene las métricas del sistema."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/metrics") as response:
                return await response.text()

    def _extract_metric_value(self, metrics_text: str, metric_name: str) -> float:
        """Extrae el valor de una métrica específica del texto Prometheus."""
        lines = metrics_text.split("\n")
        for line in lines:
            if line.startswith(metric_name) and not line.startswith("#"):
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        return float(parts[1])
                    except ValueError:
                        pass
        return 0.0

    @pytest.mark.asyncio
    async def test_race_condition_metrics(self, api_base_url, sample_article_factory):
        """
        Test 1: Detecta race conditions en el sistema de métricas.

        Según CONCURRENCY_ANALYSIS.md, hay un problema identificado en
        PipelineController.metrics que no está sincronizado.
        """
        print("\n" + "=" * 80)
        print("TEST 1: RACE CONDITIONS EN MÉTRICAS")
        print("=" * 80)

        result = ConcurrencyTestResult("Race Conditions en Métricas")

        # Obtener métricas iniciales
        initial_metrics_response = await self._get_metrics(api_base_url)
        initial_articles = self._extract_metric_value(
            initial_metrics_response, "pipeline_articles_processed_total"
        )

        print(f"📊 Métricas iniciales: {initial_articles} artículos procesados")

        # Enviar múltiples requests concurrentemente
        num_concurrent_requests = 50
        articles = [
            sample_article_factory(str(i)) for i in range(num_concurrent_requests)
        ]

        print(f"\n🚀 Enviando {num_concurrent_requests} requests concurrentes...")

        async with aiohttp.ClientSession() as session:
            tasks = []
            for article in articles:
                task = self._send_article(
                    session, f"{api_base_url}/procesar_articulo", article
                )
                tasks.append(task)

            # Ejecutar todas las tareas concurrentemente
            responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Analizar respuestas
        successful_requests = 0
        for i, response in enumerate(responses):
            result.total_operations += 1

            if isinstance(response, Exception):
                result.failed_operations += 1
                result.add_error(type(response).__name__)
            elif response[1] == 200:  # status_code
                result.successful_operations += 1
                successful_requests += 1
            else:
                result.failed_operations += 1
                result.add_error(f"HTTP_{response[1]}")

        # Esperar un momento para que se actualicen las métricas
        await asyncio.sleep(2)

        # Obtener métricas finales
        final_metrics_response = await self._get_metrics(api_base_url)
        final_articles = self._extract_metric_value(
            final_metrics_response, "pipeline_articles_processed_total"
        )

        # Calcular diferencia
        articles_processed = final_articles - initial_articles

        print(f"\n📊 Métricas finales: {final_articles} artículos procesados")
        print(f"📊 Diferencia: {articles_processed} artículos")
        print(f"✅ Requests exitosas: {successful_requests}")

        # Detectar race condition
        if articles_processed != successful_requests and successful_requests > 0:
            result.race_conditions_detected = abs(
                articles_processed - successful_requests
            )
            result.data_inconsistencies.append(
                f"Métricas reportan {articles_processed} artículos pero hubo {successful_requests} exitosos"
            )
            print(f"\n⚠️  RACE CONDITION DETECTADA!")  # noqa: F541
            print(f"   Diferencia: {result.race_conditions_detected} artículos")
        else:
            print(f"\n✅ No se detectaron race conditions en métricas")  # noqa: F541

        # Verificar también las métricas de fragmentos y errores
        total_errors = self._extract_metric_value(
            final_metrics_response, "pipeline_errors_total"
        )
        if total_errors < result.failed_operations:
            result.data_inconsistencies.append(
                f"Métricas reportan {total_errors} errores pero hubo {result.failed_operations} fallos"
            )

        result.print_summary()

        # Assertion suave - esperamos encontrar la race condition documentada
        if result.race_conditions_detected > 0:
            print("\n⚠️  Race condition confirmada (esperada según documentación)")

        assert result.successful_operations > 0, (
            "No se procesó ningún artículo exitosamente"
        )

    @pytest.mark.asyncio
    async def test_procesamiento_paralelo_masivo(
        self, api_base_url, sample_article_factory, sample_fragment_factory
    ):
        """
        Test 2: Procesamiento paralelo masivo con artículos y fragmentos.

        Evalúa la capacidad del sistema para manejar cientos de requests
        simultáneas sin perder datos o generar duplicados.
        """
        print("\n" + "=" * 80)
        print("TEST 2: PROCESAMIENTO PARALELO MASIVO")
        print("=" * 80)

        result = ConcurrencyTestResult("Procesamiento Paralelo Masivo")

        # Configuración del test
        num_articles = 100
        num_fragments = 100
        max_concurrent = 50  # Limitar concurrencia para no saturar

        print(f"📋 Configuración:")  # noqa: F541
        print(f"   - Artículos: {num_articles}")
        print(f"   - Fragmentos: {num_fragments}")
        print(f"   - Concurrencia máxima: {max_concurrent}")

        # Generar datos únicos
        articles = [sample_article_factory(f"massive_{i}") for i in range(num_articles)]
        fragments = [
            sample_fragment_factory(f"massive_{i}") for i in range(num_fragments)
        ]

        # Rastrear IDs esperados
        expected_article_ids = set()  # noqa: F841
        expected_fragment_ids = {
            f"test_concurrent_massive_{i}" for i in range(num_fragments)
        }

        # Mezclar artículos y fragmentos
        all_requests = []
        for i, article in enumerate(articles):
            all_requests.append(("article", article, i))
        for i, fragment in enumerate(fragments):
            all_requests.append(("fragment", fragment, i))

        # Aleatorizar orden
        random.shuffle(all_requests)

        print(f"\n🚀 Iniciando procesamiento masivo...")  # noqa: F541
        start_time = time.time()

        # Procesar con límite de concurrencia
        semaphore = asyncio.Semaphore(max_concurrent)
        received_ids = set()  # noqa: F841
        received_fragment_ids = set()

        async def process_item(session, item_type, data, index):
            async with semaphore:
                if item_type == "article":
                    endpoint = f"{api_base_url}/procesar_articulo"
                else:
                    endpoint = f"{api_base_url}/procesar_fragmento"

                response_time, status_code, response_data = await self._send_request(
                    session, endpoint, data
                )

                return item_type, index, response_time, status_code, response_data

        async with aiohttp.ClientSession() as session:
            tasks = []
            for item_type, data, index in all_requests:
                task = process_item(session, item_type, data, index)
                tasks.append(task)

            # Procesar todas las tareas
            responses = await asyncio.gather(*tasks, return_exceptions=True)

        total_time = time.time() - start_time

        # Analizar respuestas
        for response in responses:
            if isinstance(response, Exception):
                result.failed_operations += 1
                result.add_error(type(response).__name__)
                continue

            item_type, index, response_time, status_code, response_data = response
            result.total_operations += 1
            result.response_times.append(response_time)

            if status_code == 200:
                result.successful_operations += 1

                # Rastrear IDs recibidos
                if item_type == "fragment" and "data" in response_data:
                    frag_id = response_data["data"].get("fragmento_id")
                    if frag_id:
                        if frag_id in received_fragment_ids:
                            result.duplicate_ids.add(frag_id)
                        received_fragment_ids.add(frag_id)
            else:
                result.failed_operations += 1
                result.add_error(f"HTTP_{status_code}")

        # Verificar integridad de datos
        missing_fragments = expected_fragment_ids - received_fragment_ids
        for missing_id in missing_fragments:
            result.missing_data.append(f"Fragment ID: {missing_id}")

        # Estadísticas
        print(f"\n📊 Procesamiento completado en {total_time:.2f} segundos")
        print(f"📊 Throughput: {result.total_operations / total_time:.2f} ops/segundo")

        if result.duplicate_ids:
            print(f"\n⚠️  Se encontraron {len(result.duplicate_ids)} IDs duplicados:")
            for dup_id in list(result.duplicate_ids)[:5]:  # Mostrar solo primeros 5
                print(f"   - {dup_id}")

        if result.missing_data:
            print(f"\n⚠️  Faltan {len(result.missing_data)} elementos:")
            for missing in result.missing_data[:5]:  # Mostrar solo primeros 5
                print(f"   - {missing}")

        result.print_summary()

        # Assertions
        assert result.calculate_success_rate() > 90, (
            f"Tasa de éxito muy baja: {result.calculate_success_rate():.1f}%"
        )
        assert len(result.duplicate_ids) == 0, (
            f"Se encontraron {len(result.duplicate_ids)} IDs duplicados"
        )

    @pytest.mark.asyncio
    async def test_limites_concurrencia_sistema(
        self, api_base_url, sample_article_factory
    ):
        """
        Test 3: Encuentra los límites de concurrencia del sistema.

        Incrementa gradualmente la concurrencia hasta encontrar el punto
        donde el sistema comienza a rechazar conexiones o degradarse.
        """
        print("\n" + "=" * 80)
        print("TEST 3: LÍMITES DE CONCURRENCIA DEL SISTEMA")
        print("=" * 80)

        result = ConcurrencyTestResult("Límites de Concurrencia")

        # Configuración
        initial_concurrency = 10
        max_concurrency = 200
        increment = 10
        test_duration = 10  # segundos por nivel

        print(f"📋 Configuración:")  # noqa: F541
        print(f"   - Concurrencia inicial: {initial_concurrency}")
        print(f"   - Concurrencia máxima: {max_concurrency}")
        print(f"   - Incremento: {increment}")

        current_concurrency = initial_concurrency
        concurrency_results = []

        while current_concurrency <= max_concurrency:
            print(f"\n🔄 Probando con {current_concurrency} conexiones concurrentes...")

            level_result = {
                "concurrency": current_concurrency,
                "successful": 0,
                "failed": 0,
                "errors": defaultdict(int),
                "avg_response_time": 0,
            }

            # Crear workers concurrentes
            async def worker(worker_id: int, session: aiohttp.ClientSession):
                worker_successful = 0
                worker_failed = 0
                worker_times = []

                end_time = time.time() + test_duration

                while time.time() < end_time:
                    article = sample_article_factory(
                        f"limit_{worker_id}_{int(time.time())}"
                    )

                    try:
                        response_time, status_code, _ = await self._send_request(
                            session, f"{api_base_url}/procesar_articulo", article
                        )

                        worker_times.append(response_time)

                        if status_code == 200:
                            worker_successful += 1
                        else:
                            worker_failed += 1
                            level_result["errors"][f"HTTP_{status_code}"] += 1
                    except Exception as e:
                        worker_failed += 1
                        level_result["errors"][type(e).__name__] += 1

                    # Pequeña pausa entre requests
                    await asyncio.sleep(0.1)

                return worker_successful, worker_failed, worker_times

            # Ejecutar workers
            connector = aiohttp.TCPConnector(limit=current_concurrency)
            async with aiohttp.ClientSession(connector=connector) as session:
                workers = [worker(i, session) for i in range(current_concurrency)]
                results = await asyncio.gather(*workers, return_exceptions=True)

            # Analizar resultados del nivel
            all_response_times = []
            for worker_result in results:
                if isinstance(worker_result, Exception):
                    level_result["errors"][type(worker_result).__name__] += 1
                else:
                    successful, failed, times = worker_result
                    level_result["successful"] += successful
                    level_result["failed"] += failed
                    all_response_times.extend(times)

            if all_response_times:
                level_result["avg_response_time"] = sum(all_response_times) / len(
                    all_response_times
                )

            # Calcular tasa de éxito
            total = level_result["successful"] + level_result["failed"]
            success_rate = (
                (level_result["successful"] / total * 100) if total > 0 else 0
            )

            print(f"  ✅ Exitosas: {level_result['successful']}")
            print(f"  ❌ Fallidas: {level_result['failed']}")
            print(f"  📊 Tasa éxito: {success_rate:.1f}%")
            print(
                f"  ⏱️  Tiempo respuesta promedio: {level_result['avg_response_time'] * 1000:.1f}ms"
            )

            concurrency_results.append(level_result)

            # Si la tasa de éxito cae por debajo del 80%, hemos encontrado el límite
            if success_rate < 80:
                print(
                    f"\n⚠️  Límite encontrado en {current_concurrency} conexiones concurrentes"
                )
                break

            current_concurrency += increment

        # Análisis de resultados
        print("\n📊 RESUMEN DE LÍMITES DE CONCURRENCIA:")
        print("-" * 70)
        print(
            f"{'Concurrencia':<15} {'Exitosas':<10} {'Fallidas':<10} {'Tasa Éxito':<15} {'Tiempo Avg':<15}"
        )
        print("-" * 70)

        optimal_concurrency = initial_concurrency
        for level in concurrency_results:
            total = level["successful"] + level["failed"]
            success_rate = (level["successful"] / total * 100) if total > 0 else 0

            print(
                f"{level['concurrency']:<15} {level['successful']:<10} {level['failed']:<10} "
                f"{success_rate:<15.1f}% {level['avg_response_time'] * 1000:<15.1f}ms"
            )

            # Encontrar concurrencia óptima (última con >95% éxito)
            if success_rate >= 95:
                optimal_concurrency = level["concurrency"]

        print("-" * 70)
        print(f"\n🎯 Concurrencia óptima recomendada: {optimal_concurrency} conexiones")

        result.print_summary()

        assert optimal_concurrency >= 20, (
            f"Sistema soporta muy poca concurrencia: {optimal_concurrency}"
        )

    @pytest.mark.asyncio
    async def test_integridad_datos_concurrencia(
        self, api_base_url, sample_fragment_factory
    ):
        """
        Test 4: Verifica la integridad de datos bajo alta concurrencia.

        Envía fragmentos con IDs secuenciales y verifica que todos sean
        procesados correctamente sin pérdidas o duplicaciones.
        """
        print("\n" + "=" * 80)
        print("TEST 4: INTEGRIDAD DE DATOS BAJO CONCURRENCIA")
        print("=" * 80)

        result = ConcurrencyTestResult("Integridad de Datos")

        # Configuración
        num_fragments = 200
        batch_size = 50

        print(f"📋 Configuración:")  # noqa: F541
        print(f"   - Total fragmentos: {num_fragments}")
        print(f"   - Tamaño de batch: {batch_size}")

        # Generar fragmentos con IDs secuenciales
        fragments = []
        for i in range(num_fragments):
            fragment = sample_fragment_factory(f"integrity_{i:04d}", size=500)
            fragments.append(fragment)

        # Dividir en batches
        batches = [
            fragments[i : i + batch_size] for i in range(0, len(fragments), batch_size)
        ]

        # Procesar cada batch concurrentemente
        all_received_ids = set()
        all_job_ids = set()

        for batch_num, batch in enumerate(batches):
            print(f"\n🔄 Procesando batch {batch_num + 1}/{len(batches)}...")

            async with aiohttp.ClientSession() as session:
                tasks = []
                for fragment in batch:
                    endpoint = f"{api_base_url}/procesar_fragmento"
                    task = self._send_request(session, endpoint, fragment)
                    tasks.append(task)

                responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Analizar respuestas del batch
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    result.failed_operations += 1
                    result.add_error(type(response).__name__)
                    continue

                response_time, status_code, response_data = response
                result.total_operations += 1
                result.response_times.append(response_time)

                if status_code == 200:
                    result.successful_operations += 1

                    # Extraer IDs
                    if "data" in response_data:
                        data = response_data["data"]

                        # Verificar fragmento_id
                        frag_id = data.get("fragmento_id")
                        if frag_id:
                            if frag_id in all_received_ids:
                                result.duplicate_ids.add(frag_id)
                            all_received_ids.add(frag_id)

                        # Verificar job_id
                        job_id = response_data.get("job_id")
                        if job_id:
                            if job_id in all_job_ids:
                                result.data_inconsistencies.append(
                                    f"Job ID duplicado: {job_id}"
                                )
                            all_job_ids.add(job_id)
                else:
                    result.failed_operations += 1
                    result.add_error(f"HTTP_{status_code}")

            # Pequeña pausa entre batches
            await asyncio.sleep(1)

        # Verificar integridad
        expected_ids = {
            f"test_concurrent_integrity_{i:04d}" for i in range(num_fragments)
        }
        missing_ids = expected_ids - all_received_ids
        unexpected_ids = all_received_ids - expected_ids

        print(f"\n📊 Análisis de integridad:")  # noqa: F541
        print(f"   - IDs esperados: {len(expected_ids)}")
        print(f"   - IDs recibidos: {len(all_received_ids)}")
        print(f"   - IDs faltantes: {len(missing_ids)}")
        print(f"   - IDs inesperados: {len(unexpected_ids)}")
        print(f"   - IDs duplicados: {len(result.duplicate_ids)}")
        print(f"   - Jobs únicos: {len(all_job_ids)}")

        if missing_ids:
            print(f"\n⚠️  IDs faltantes (primeros 10):")  # noqa: F541
            for missing_id in list(missing_ids)[:10]:
                print(f"   - {missing_id}")
                result.missing_data.append(f"ID: {missing_id}")

        if unexpected_ids:
            print(f"\n⚠️  IDs inesperados (primeros 10):")  # noqa: F541
            for unexpected_id in list(unexpected_ids)[:10]:
                print(f"   - {unexpected_id}")
                result.data_inconsistencies.append(f"ID inesperado: {unexpected_id}")

        result.print_summary()

        # Assertions estrictas para integridad
        assert len(result.duplicate_ids) == 0, (
            f"Se encontraron {len(result.duplicate_ids)} IDs duplicados"
        )
        assert len(missing_ids) == 0, f"Faltan {len(missing_ids)} IDs"
        assert len(unexpected_ids) == 0, (
            f"Se encontraron {len(unexpected_ids)} IDs inesperados"
        )
        assert result.calculate_success_rate() > 95, (
            f"Tasa de éxito muy baja: {result.calculate_success_rate():.1f}%"
        )

    @pytest.mark.asyncio
    async def test_job_tracker_concurrency(self, api_base_url, sample_article_factory):
        """
        Test 5: Verifica que el JobTrackerService maneja correctamente la concurrencia.

        Según el análisis, JobTrackerService es thread-safe, pero verificamos
        que funcione correctamente bajo alta carga.
        """
        print("\n" + "=" * 80)
        print("TEST 5: CONCURRENCIA EN JOB TRACKER SERVICE")
        print("=" * 80)

        result = ConcurrencyTestResult("Job Tracker Concurrency")

        # Enviar artículos grandes para procesamiento asíncrono
        num_async_articles = 30
        articles = []

        for i in range(num_async_articles):
            # Crear artículos grandes (>10KB) para forzar procesamiento asíncrono
            article = sample_article_factory(f"async_{i}", size=15000)
            articles.append(article)

        print(
            f"📋 Enviando {num_async_articles} artículos grandes para procesamiento asíncrono..."
        )

        # Enviar todos los artículos concurrentemente
        job_ids = []

        async with aiohttp.ClientSession() as session:
            tasks = []
            for article in articles:
                endpoint = f"{api_base_url}/procesar_articulo"
                task = self._send_request(session, endpoint, article)
                tasks.append(task)

            responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Recolectar job_ids
        for response in responses:
            if not isinstance(response, Exception):
                _, status_code, response_data = response
                if status_code == 200 and "job_id" in response_data:
                    job_ids.append(response_data["job_id"])

        print(f"✅ Se crearon {len(job_ids)} jobs asíncronos")

        # Ahora consultar todos los jobs concurrentemente
        print(f"\n🔄 Consultando estado de todos los jobs concurrentemente...")  # noqa: F541

        async def check_job_status(session, job_id):
            endpoint = f"{api_base_url}/status/{job_id}"
            try:
                async with session.get(endpoint) as response:
                    if response.status == 200:
                        data = await response.json()
                        return job_id, "found", data
                    else:
                        return job_id, "not_found", None
            except Exception as e:
                return job_id, "error", str(e)

        # Consultar todos los jobs múltiples veces
        for round_num in range(3):
            print(f"\n  Ronda {round_num + 1}/3 de consultas...")

            async with aiohttp.ClientSession() as session:
                tasks = []
                for job_id in job_ids:
                    task = check_job_status(session, job_id)
                    tasks.append(task)

                results = await asyncio.gather(*tasks)

            # Analizar resultados
            found_count = 0
            status_counts = defaultdict(int)

            for job_id, status, data in results:
                if status == "found":
                    found_count += 1
                    if data and "data" in data:
                        job_status = data["data"].get("status", "unknown")
                        status_counts[job_status] += 1
                else:
                    result.data_inconsistencies.append(f"Job {job_id} status: {status}")

            print(f"  ✅ Jobs encontrados: {found_count}/{len(job_ids)}")
            print(f"  📊 Estados: {dict(status_counts)}")

            # Pequeña pausa entre rondas
            await asyncio.sleep(2)

        # Verificar que no hay duplicados o pérdidas en el tracking
        print(f"\n📊 Verificación final del Job Tracker:")  # noqa: F541
        print(f"   - Jobs creados: {len(job_ids)}")
        print(f"   - Jobs únicos: {len(set(job_ids))}")
        print(f"   - Inconsistencias: {len(result.data_inconsistencies)}")

        result.total_operations = len(job_ids) * 3  # 3 rondas de consultas
        result.successful_operations = found_count

        result.print_summary()

        # Assertions
        assert len(job_ids) == len(set(job_ids)), "Se generaron job_ids duplicados"
        assert found_count > 0, "No se encontraron jobs en el tracker"


def run_concurrency_stress_test():
    """
    Ejecuta un test de estrés de concurrencia adicional.

    Este test es más agresivo y puede causar fallos en el sistema.
    Se ejecuta por separado de los tests normales.
    """
    import asyncio

    async def stress_test():
        print("\n" + "=" * 80)
        print("TEST DE ESTRÉS DE CONCURRENCIA (OPCIONAL)")
        print("=" * 80)
        print("⚠️  ADVERTENCIA: Este test puede causar fallos en el sistema")

        base_url = f"http://{API_HOST}:{API_PORT}"

        # Configuración agresiva
        num_workers = 100
        requests_per_worker = 50

        print(f"\n📋 Configuración de estrés:")  # noqa: F541
        print(f"   - Workers: {num_workers}")
        print(f"   - Requests por worker: {requests_per_worker}")
        print(f"   - Total requests: {num_workers * requests_per_worker}")

        async def stress_worker(worker_id: int):
            successes = 0
            failures = 0

            async with aiohttp.ClientSession() as session:
                for i in range(requests_per_worker):
                    article = {
                        "medio": f"Stress Test {worker_id}",
                        "area_geografica": "Test",
                        "tipo_medio": "Digital",
                        "titular": f"Stress test article {worker_id}-{i}",
                        "fecha_publicacion": "2024-01-15T10:00:00Z",
                        "contenido_texto": f"Contenido de estrés " * 100,  # noqa: F541
                        "idioma": "es",
                    }

                    try:
                        async with session.post(
                            f"{base_url}/procesar_articulo",
                            json=article,
                            timeout=aiohttp.ClientTimeout(total=5),
                        ) as response:
                            if response.status == 200:
                                successes += 1
                            else:
                                failures += 1
                    except:  # noqa: E722
                        failures += 1

            return successes, failures

        print("\n🚀 Iniciando test de estrés...")
        start_time = time.time()

        # Lanzar todos los workers
        workers = [stress_worker(i) for i in range(num_workers)]
        results = await asyncio.gather(*workers, return_exceptions=True)

        total_time = time.time() - start_time

        # Analizar resultados
        total_successes = 0
        total_failures = 0

        for result in results:
            if isinstance(result, tuple):
                successes, failures = result
                total_successes += successes
                total_failures += failures
            else:
                total_failures += requests_per_worker

        total_requests = total_successes + total_failures
        success_rate = (
            (total_successes / total_requests * 100) if total_requests > 0 else 0
        )

        print(f"\n📊 Resultados del test de estrés:")  # noqa: F541
        print(f"   - Duración: {total_time:.2f} segundos")
        print(f"   - Total requests: {total_requests}")
        print(f"   - Exitosas: {total_successes}")
        print(f"   - Fallidas: {total_failures}")
        print(f"   - Tasa de éxito: {success_rate:.1f}%")
        print(f"   - Throughput: {total_requests / total_time:.2f} req/s")

        if success_rate < 50:
            print("\n⚠️  El sistema mostró degradación severa bajo estrés extremo")
        else:
            print("\n✅ El sistema manejó el estrés razonablemente bien")

    # Ejecutar el test de estrés
    asyncio.run(stress_test())


if __name__ == "__main__":
    # Permitir ejecución directa del archivo
    import subprocess
    import sys

    print("Ejecutando tests de concurrencia...")
    cmd = [sys.executable, "-m", "pytest", __file__, "-v", "-s"]
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\n✅ Tests de concurrencia completados exitosamente")

        # Preguntar si ejecutar test de estrés
        response = input("\n¿Ejecutar test de estrés adicional? (s/n): ")
        if response.lower() == "s":
            run_concurrency_stress_test()
    else:
        print("\n❌ Tests de concurrencia fallaron")

    sys.exit(result.returncode)
