"""
Performance tests for API endpoints.

Tests response times, throughput, and resource usage under various loads.
Helps identify bottlenecks and optimize critical paths.
"""

import time
import asyncio
import statistics
from typing import List, Dict, Any
from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import psutil
import gc

from src.main import app


class TestAPIPerformance:
    """Performance tests for API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_hechos_service(self):
        """Mock HechosService for performance testing."""
        with patch('src.api.dashboard.get_hechos_service') as mock:
            service = MagicMock()
            
            # Create sample data for performance testing
            sample_hechos = []
            for i in range(100):
                hecho = {
                    "id": i,
                    "contenido": f"Test hecho content {i}",
                    "fecha_ocurrencia": "2024-01-15T10:30:00",
                    "importancia": (i % 10) + 1,
                    "tipo_hecho": "test",
                    "pais": "Argentina",
                    "articulo_metadata": {
                        "medio": f"Medio {i % 5}",
                        "titular": f"Test headline {i}",
                        "fecha_publicacion": "2024-01-15T12:00:00",
                        "url": f"https://example.com/{i}"
                    }
                }
                sample_hechos.append(hecho)
            
            # Mock async method with realistic delay
            async def mock_get_hechos(params):
                # Simulate database query time (20-50ms)
                await asyncio.sleep(0.02 + (0.03 * len(params) / 10))
                
                # Apply pagination
                limit = params.get('limit', 20)
                offset = params.get('offset', 0)
                
                return sample_hechos[offset:offset+limit], len(sample_hechos)
            
            service.get_hechos_for_revision = AsyncMock(side_effect=mock_get_hechos)
            mock.return_value = service
            yield service
    
    def measure_response_time(self, client: TestClient, endpoint: str, 
                            params: Dict[str, Any] = None, 
                            iterations: int = 100) -> Dict[str, float]:
        """
        Measure response time statistics for an endpoint.
        
        Returns:
            Dict with min, max, mean, median, p95, p99 response times
        """
        response_times = []
        
        for _ in range(iterations):
            start_time = time.perf_counter()
            response = client.get(endpoint, params=params)
            end_time = time.perf_counter()
            
            assert response.status_code == 200
            response_times.append((end_time - start_time) * 1000)  # Convert to ms
        
        response_times.sort()
        
        return {
            "min": min(response_times),
            "max": max(response_times),
            "mean": statistics.mean(response_times),
            "median": statistics.median(response_times),
            "p95": response_times[int(len(response_times) * 0.95)],
            "p99": response_times[int(len(response_times) * 0.99)],
            "std_dev": statistics.stdev(response_times) if len(response_times) > 1 else 0
        }
    
    def test_hechos_revision_response_time(self, client, mock_hechos_service):
        """Test response time for hechos_revision endpoint."""
        # Test with default parameters
        stats = self.measure_response_time(
            client, 
            "/dashboard/hechos_revision",
            iterations=100
        )
        
        print("\n=== Hechos Revision Response Time (Default Params) ===")
        print(f"Min: {stats['min']:.2f}ms")
        print(f"Max: {stats['max']:.2f}ms")
        print(f"Mean: {stats['mean']:.2f}ms")
        print(f"Median: {stats['median']:.2f}ms")
        print(f"P95: {stats['p95']:.2f}ms")
        print(f"P99: {stats['p99']:.2f}ms")
        print(f"Std Dev: {stats['std_dev']:.2f}ms")
        
        # Assert performance requirements
        assert stats['median'] < 100, "Median response time should be under 100ms"
        assert stats['p95'] < 200, "95th percentile should be under 200ms"
        assert stats['p99'] < 500, "99th percentile should be under 500ms"
    
    def test_hechos_revision_with_filters_performance(self, client, mock_hechos_service):
        """Test response time with various filter combinations."""
        test_cases = [
            # (name, params)
            ("No filters", {}),
            ("Date filter", {
                "fecha_inicio": "2024-01-01T00:00:00",
                "fecha_fin": "2024-12-31T23:59:59"
            }),
            ("All filters", {
                "fecha_inicio": "2024-01-01T00:00:00",
                "fecha_fin": "2024-12-31T23:59:59",
                "medio": "La Nacion",
                "pais_publicacion": "Argentina",
                "importancia_min": 5,
                "importancia_max": 10,
                "limit": 50
            }),
            ("Large page size", {"limit": 100}),
            ("Deep pagination", {"limit": 20, "offset": 1000})
        ]
        
        print("\n=== Filter Performance Comparison ===")
        
        for name, params in test_cases:
            stats = self.measure_response_time(
                client,
                "/dashboard/hechos_revision",
                params=params,
                iterations=50
            )
            
            print(f"\n{name}:")
            print(f"  Mean: {stats['mean']:.2f}ms")
            print(f"  P95: {stats['p95']:.2f}ms")
            
            # All filter combinations should meet performance targets
            assert stats['mean'] < 150, f"{name}: Mean response time should be under 150ms"
            assert stats['p95'] < 300, f"{name}: P95 should be under 300ms"
    
    def test_feedback_endpoints_performance(self, client):
        """Test performance of feedback submission endpoints."""
        with patch('src.api.feedback.get_feedback_service') as mock:
            service = MagicMock()
            service.submit_importancia_feedback = AsyncMock()
            service.submit_evaluacion_editorial = AsyncMock()
            mock.return_value = service
            
            # Test importance feedback
            importance_stats = self.measure_response_time(
                client,
                "/dashboard/feedback/hecho/123/importancia_feedback",
                iterations=50
            )
            
            print("\n=== Importance Feedback Performance ===")
            print(f"Mean: {importance_stats['mean']:.2f}ms")
            print(f"P95: {importance_stats['p95']:.2f}ms")
            
            # Feedback endpoints should be very fast
            assert importance_stats['mean'] < 50, "Mean response time should be under 50ms"
            assert importance_stats['p95'] < 100, "P95 should be under 100ms"
    
    def test_memory_usage_under_load(self, client, mock_hechos_service):
        """Test memory usage doesn't grow excessively under load."""
        process = psutil.Process()
        
        # Force garbage collection and get baseline
        gc.collect()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"\n=== Memory Usage Test ===")
        print(f"Baseline memory: {baseline_memory:.2f} MB")
        
        # Make many requests
        for i in range(500):
            response = client.get("/dashboard/hechos_revision", params={"limit": 50})
            assert response.status_code == 200
            
            if i % 100 == 0:
                gc.collect()
                current_memory = process.memory_info().rss / 1024 / 1024
                print(f"After {i} requests: {current_memory:.2f} MB")
        
        # Final measurement
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_growth = final_memory - baseline_memory
        
        print(f"Final memory: {final_memory:.2f} MB")
        print(f"Memory growth: {memory_growth:.2f} MB")
        
        # Memory growth should be minimal (less than 50MB for 500 requests)
        assert memory_growth < 50, "Memory growth should be less than 50MB"
    
    def test_cpu_usage_patterns(self, client, mock_hechos_service):
        """Test CPU usage patterns during various operations."""
        process = psutil.Process()
        
        print("\n=== CPU Usage Patterns ===")
        
        # Test different scenarios
        scenarios = [
            ("Light load", 10, {"limit": 20}),
            ("Heavy load", 50, {"limit": 100}),
            ("Complex filters", 30, {
                "fecha_inicio": "2024-01-01",
                "fecha_fin": "2024-12-31",
                "medio": "Test",
                "importancia_min": 5,
                "importancia_max": 8,
                "limit": 50
            })
        ]
        
        for name, requests, params in scenarios:
            cpu_samples = []
            
            # Sample CPU usage during requests
            for _ in range(requests):
                cpu_percent = process.cpu_percent(interval=0.1)
                response = client.get("/dashboard/hechos_revision", params=params)
                assert response.status_code == 200
                cpu_samples.append(cpu_percent)
            
            avg_cpu = statistics.mean(cpu_samples) if cpu_samples else 0
            max_cpu = max(cpu_samples) if cpu_samples else 0
            
            print(f"\n{name}:")
            print(f"  Average CPU: {avg_cpu:.1f}%")
            print(f"  Max CPU: {max_cpu:.1f}%")
            
            # CPU usage should be reasonable
            assert avg_cpu < 50, f"{name}: Average CPU usage should be under 50%"
            assert max_cpu < 80, f"{name}: Max CPU usage should be under 80%"
    
    def test_response_size_impact(self, client, mock_hechos_service):
        """Test how response size affects performance."""
        page_sizes = [1, 10, 20, 50, 100]
        
        print("\n=== Response Size Impact ===")
        print("Page Size | Mean Time | Time per Item")
        print("----------|-----------|---------------")
        
        for size in page_sizes:
            stats = self.measure_response_time(
                client,
                "/dashboard/hechos_revision",
                params={"limit": size},
                iterations=30
            )
            
            time_per_item = stats['mean'] / size
            print(f"{size:9} | {stats['mean']:9.2f}ms | {time_per_item:13.2f}ms")
            
            # Response time should scale sub-linearly with size
            if size > 10:
                assert time_per_item < 2.0, "Time per item should be under 2ms for larger pages"
    
    def test_concurrent_request_performance(self, client, mock_hechos_service):
        """Test performance under concurrent requests."""
        import concurrent.futures
        
        def make_request():
            start = time.perf_counter()
            response = client.get("/dashboard/hechos_revision")
            duration = (time.perf_counter() - start) * 1000
            return response.status_code, duration
        
        print("\n=== Concurrent Request Performance ===")
        
        # Test with different concurrency levels
        for num_concurrent in [1, 5, 10, 20]:
            response_times = []
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
                futures = [executor.submit(make_request) for _ in range(num_concurrent * 5)]
                
                for future in concurrent.futures.as_completed(futures):
                    status, duration = future.result()
                    assert status == 200
                    response_times.append(duration)
            
            avg_time = statistics.mean(response_times)
            max_time = max(response_times)
            
            print(f"\nConcurrency level {num_concurrent}:")
            print(f"  Average: {avg_time:.2f}ms")
            print(f"  Max: {max_time:.2f}ms")
            
            # Performance should degrade gracefully
            assert avg_time < 200 * (1 + num_concurrent/10), "Response time should scale reasonably"
    
    def test_cache_effectiveness(self, client):
        """Test effectiveness of any caching mechanisms."""
        with patch('src.api.dashboard.get_hechos_service') as mock:
            service = MagicMock()
            call_count = 0
            
            async def mock_get_filter_options():
                nonlocal call_count
                call_count += 1
                # Simulate DB query
                await asyncio.sleep(0.05)
                return {
                    "medios_disponibles": ["Medio1", "Medio2"],
                    "paises_disponibles": ["Pais1", "Pais2"],
                    "importancia_range": {"min": 1, "max": 10}
                }
            
            service.get_filter_options = AsyncMock(side_effect=mock_get_filter_options)
            mock.return_value = service
            
            print("\n=== Cache Effectiveness Test ===")
            
            # First call - cold cache
            cold_stats = self.measure_response_time(
                client,
                "/dashboard/filtros/opciones",
                iterations=10
            )
            
            # Subsequent calls - potentially cached
            warm_stats = self.measure_response_time(
                client,
                "/dashboard/filtros/opciones",
                iterations=50
            )
            
            print(f"Cold cache mean: {cold_stats['mean']:.2f}ms")
            print(f"Warm cache mean: {warm_stats['mean']:.2f}ms")
            print(f"Total service calls: {call_count}")
            
            # If caching is implemented, warm should be faster
            # This test documents current behavior
            if warm_stats['mean'] < cold_stats['mean'] * 0.8:
                print("✓ Caching appears to be effective")
            else:
                print("✗ No significant caching detected")
    
    def test_error_handling_performance(self, client):
        """Test that error handling doesn't significantly impact performance."""
        with patch('src.api.dashboard.get_hechos_service') as mock:
            service = MagicMock()
            
            # Mock that raises an error
            service.get_hechos_for_revision = AsyncMock(
                side_effect=Exception("Test error")
            )
            mock.return_value = service
            
            error_times = []
            
            for _ in range(50):
                start = time.perf_counter()
                response = client.get("/dashboard/hechos_revision")
                duration = (time.perf_counter() - start) * 1000
                
                assert response.status_code == 500
                error_times.append(duration)
            
            avg_error_time = statistics.mean(error_times)
            
            print(f"\n=== Error Handling Performance ===")
            print(f"Average error response time: {avg_error_time:.2f}ms")
            
            # Error responses should still be fast
            assert avg_error_time < 50, "Error handling should be fast (under 50ms)"
    
    def test_health_check_performance(self, client):
        """Test health check endpoints are extremely fast."""
        # Basic health check
        basic_stats = self.measure_response_time(
            client,
            "/health",
            iterations=200
        )
        
        print("\n=== Health Check Performance ===")
        print(f"Basic health check mean: {basic_stats['mean']:.2f}ms")
        print(f"Basic health check P99: {basic_stats['p99']:.2f}ms")
        
        # Health checks should be very fast
        assert basic_stats['mean'] < 5, "Basic health check should be under 5ms"
        assert basic_stats['p99'] < 10, "Basic health check P99 should be under 10ms"
        
        # Detailed health check (with mocked Supabase)
        with patch('src.services.supabase_client.SupabaseClient.execute_with_retry') as mock:
            mock.return_value = MagicMock()
            
            detailed_stats = self.measure_response_time(
                client,
                "/health/detailed",
                iterations=100
            )
            
            print(f"\nDetailed health check mean: {detailed_stats['mean']:.2f}ms")
            print(f"Detailed health check P99: {detailed_stats['p99']:.2f}ms")
            
            # Detailed check is slower but still fast
            assert detailed_stats['mean'] < 50, "Detailed health check should be under 50ms"
            assert detailed_stats['p99'] < 100, "Detailed health check P99 should be under 100ms"


class TestDatabaseQueryPerformance:
    """Test performance of database queries specifically."""
    
    @pytest.fixture
    def mock_supabase_with_timing(self):
        """Mock Supabase client that simulates realistic query times."""
        with patch('src.services.supabase_client.SupabaseClient.get_client') as mock:
            client = MagicMock()
            
            # Simulate different query complexities
            def simulate_query_time(query_type, params=None):
                base_time = {
                    'simple_select': 0.01,  # 10ms
                    'join_select': 0.02,    # 20ms
                    'count': 0.015,         # 15ms
                    'aggregate': 0.025,     # 25ms
                    'update': 0.03,         # 30ms
                    'insert': 0.025         # 25ms
                }.get(query_type, 0.02)
                
                # Add time for filters
                if params:
                    filter_count = len([k for k in params.keys() if k.startswith('filter_')])
                    base_time += filter_count * 0.005
                
                time.sleep(base_time)
            
            # Configure mock
            table_mock = MagicMock()
            client.table.return_value = table_mock
            
            # Chain methods
            for method in ['select', 'insert', 'update', 'delete', 'eq', 'neq', 
                          'gt', 'gte', 'lt', 'lte', 'order', 'limit', 'range']:
                setattr(table_mock, method, MagicMock(return_value=table_mock))
            
            # Execute with timing
            def mock_execute():
                simulate_query_time('join_select')
                return MagicMock(data=[], count=0)
            
            table_mock.execute = mock_execute
            
            mock.return_value = client
            yield client
    
    def test_query_optimization_opportunities(self, mock_supabase_with_timing):
        """Identify potential query optimization opportunities."""
        from src.services.hechos_service import HechosService
        
        service = HechosService()
        
        print("\n=== Query Optimization Analysis ===")
        
        # Test different query patterns
        test_scenarios = [
            ("Simple query", {"limit": 20}),
            ("With date filter", {
                "fecha_inicio": datetime(2024, 1, 1),
                "fecha_fin": datetime(2024, 12, 31),
                "limit": 20
            }),
            ("Multiple filters", {
                "fecha_inicio": datetime(2024, 1, 1),
                "medio": "Test",
                "pais_publicacion": "Argentina",
                "importancia_min": 5,
                "limit": 20
            }),
            ("Large result set", {"limit": 100}),
            ("Deep pagination", {"limit": 20, "offset": 500})
        ]
        
        for name, params in test_scenarios:
            start = time.perf_counter()
            
            # Run async method synchronously for testing
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    service.get_hechos_for_revision(params)
                )
                duration = (time.perf_counter() - start) * 1000
                
                print(f"\n{name}:")
                print(f"  Query time: {duration:.2f}ms")
                
                # Identify slow queries
                if duration > 100:
                    print(f"  ⚠️  Consider optimizing this query pattern")
                
            finally:
                loop.close()
