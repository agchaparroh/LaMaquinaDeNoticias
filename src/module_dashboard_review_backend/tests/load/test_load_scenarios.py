"""
Load testing for Dashboard Review Backend.

Tests system behavior under sustained high load to identify
breaking points and performance degradation patterns.
"""

import asyncio
import time
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import psutil
import random
import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.main import app


class TestLoadScenarios:
    """Test various load scenarios."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture  
    def load_test_service(self):
        """Mock services configured for load testing."""
        with patch('src.api.dashboard.get_hechos_service') as mock_hechos:
            with patch('src.api.feedback.get_feedback_service') as mock_feedback:
                # Create services
                hechos_service = MagicMock()
                feedback_service = MagicMock()
                
                # Performance tracking
                metrics = {
                    'requests': defaultdict(int),
                    'response_times': defaultdict(list),
                    'errors': defaultdict(int),
                    'throughput': []
                }
                
                # Simulate realistic database behavior
                async def mock_get_hechos(params):
                    start_time = time.time()
                    
                    # Simulate varying response times based on load
                    base_delay = 0.02
                    load_factor = min(metrics['requests']['total'] / 1000, 2.0)
                    delay = base_delay * (1 + load_factor + random.random() * 0.01)
                    
                    await asyncio.sleep(delay)
                    
                    # Simulate occasional errors under high load
                    if metrics['requests']['total'] > 5000 and random.random() < 0.01:
                        metrics['errors']['database'] += 1
                        raise Exception("Database connection timeout")
                    
                    # Track metrics
                    response_time = time.time() - start_time
                    metrics['response_times']['hechos'].append(response_time)
                    metrics['requests']['hechos'] += 1
                    metrics['requests']['total'] += 1
                    
                    # Return data
                    limit = params.get('limit', 20)
                    data = [
                        {
                            'id': i,
                            'contenido': f'Hecho {i}',
                            'importancia': (i % 10) + 1,
                            'articulo_metadata': {}
                        }
                        for i in range(limit)
                    ]
                    
                    return data, 1000
                
                async def mock_submit_feedback(hecho_id, feedback):
                    start_time = time.time()
                    
                    # Simulate write operation
                    await asyncio.sleep(0.03 + random.random() * 0.02)
                    
                    # Track metrics
                    response_time = time.time() - start_time
                    metrics['response_times']['feedback'].append(response_time)
                    metrics['requests']['feedback'] += 1
                    metrics['requests']['total'] += 1
                
                # Configure mocks
                hechos_service.get_hechos_for_revision = AsyncMock(
                    side_effect=mock_get_hechos
                )
                feedback_service.submit_importancia_feedback = AsyncMock(
                    side_effect=mock_submit_feedback
                )
                feedback_service.submit_evaluacion_editorial = AsyncMock(
                    side_effect=mock_submit_feedback
                )
                
                mock_hechos.return_value = hechos_service
                mock_feedback.return_value = feedback_service
                
                # Attach metrics
                hechos_service._metrics = metrics
                feedback_service._metrics = metrics
                
                yield hechos_service, feedback_service, metrics
    
    def run_load_test(self, client: TestClient, duration_seconds: int, 
                     rps_target: int, scenario: str = "mixed") -> Dict:
        """
        Run a load test for specified duration and RPS.
        
        Args:
            client: Test client
            duration_seconds: Test duration
            rps_target: Target requests per second
            scenario: Load scenario (read, write, mixed)
            
        Returns:
            Test results and metrics
        """
        results = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'response_times': [],
            'errors_by_type': defaultdict(int),
            'throughput_per_second': [],
            'resource_usage': []
        }
        
        start_time = time.time()
        request_interval = 1.0 / rps_target
        
        def make_request():
            """Make a single request based on scenario."""
            try:
                request_start = time.time()
                
                if scenario == "read" or (scenario == "mixed" and random.random() < 0.8):
                    # Read request
                    params = {
                        'limit': random.choice([10, 20, 50]),
                        'offset': random.randint(0, 100) * 20
                    }
                    response = client.get("/dashboard/hechos_revision", params=params)
                else:
                    # Write request
                    hecho_id = random.randint(1, 1000)
                    if random.random() < 0.5:
                        response = client.post(
                            f"/dashboard/feedback/hecho/{hecho_id}/importancia_feedback",
                            json={
                                "importancia_editor_final": random.randint(1, 10),
                                "usuario_id_editor": f"load_test_{random.randint(1, 10)}"
                            }
                        )
                    else:
                        response = client.post(
                            f"/dashboard/feedback/hecho/{hecho_id}/evaluacion_editorial",
                            json={
                                "evaluacion_editorial": random.choice([
                                    "verificado_ok_editorial",
                                    "declarado_falso_editorial"
                                ]),
                                "justificacion_evaluacion_editorial": "Load test"
                            }
                        )
                
                request_time = time.time() - request_start
                
                results['total_requests'] += 1
                results['response_times'].append(request_time)
                
                if response.status_code == 200:
                    results['successful_requests'] += 1
                else:
                    results['failed_requests'] += 1
                    results['errors_by_type'][response.status_code] += 1
                
                return request_time
                
            except Exception as e:
                results['failed_requests'] += 1
                results['errors_by_type'][type(e).__name__] += 1
                return None
        
        # Track resource usage
        process = psutil.Process()
        
        # Run load test
        with ThreadPoolExecutor(max_workers=min(rps_target, 100)) as executor:
            futures = []
            requests_sent = 0
            last_throughput_check = start_time
            
            while time.time() - start_time < duration_seconds:
                # Submit new request
                futures.append(executor.submit(make_request))
                requests_sent += 1
                
                # Control request rate
                time.sleep(request_interval)
                
                # Calculate throughput every second
                if time.time() - last_throughput_check >= 1.0:
                    completed = len([f for f in futures if f.done()])
                    throughput = completed - sum(results['throughput_per_second'])
                    results['throughput_per_second'].append(throughput)
                    
                    # Record resource usage
                    results['resource_usage'].append({
                        'time': time.time() - start_time,
                        'cpu_percent': process.cpu_percent(),
                        'memory_mb': process.memory_info().rss / 1024 / 1024
                    })
                    
                    last_throughput_check = time.time()
            
            # Wait for remaining requests
            for future in as_completed(futures):
                future.result()
        
        # Calculate final metrics
        results['duration'] = time.time() - start_time
        results['actual_rps'] = results['total_requests'] / results['duration']
        
        return results
    
    def test_sustained_normal_load(self, client, load_test_service):
        """Test system under sustained normal load."""
        _, _, metrics = load_test_service
        
        print("\n=== Sustained Normal Load Test ===")
        print("Duration: 30 seconds, Target: 50 RPS")
        
        results = self.run_load_test(
            client,
            duration_seconds=30,
            rps_target=50,
            scenario="mixed"
        )
        
        self._print_load_test_results(results)
        
        # Assertions for normal load
        success_rate = results['successful_requests'] / results['total_requests']
        assert success_rate > 0.99, f"Success rate {success_rate:.2%} below 99%"
        
        # Response time requirements
        response_times = results['response_times']
        p95 = sorted(response_times)[int(len(response_times) * 0.95)]
        assert p95 < 0.2, f"P95 response time {p95:.3f}s exceeds 200ms"
    
    def test_spike_load(self, client, load_test_service):
        """Test system behavior during traffic spikes."""
        _, _, metrics = load_test_service
        
        print("\n=== Spike Load Test ===")
        print("Normal: 30 RPS, Spike: 200 RPS")
        
        # Run with varying load
        results = {
            'phases': [],
            'total_requests': 0,
            'total_errors': 0
        }
        
        # Phase 1: Normal load
        print("\nPhase 1: Normal load (10s)")
        phase1 = self.run_load_test(client, 10, 30, "mixed")
        results['phases'].append(('normal', phase1))
        
        # Phase 2: Spike
        print("\nPhase 2: Spike load (10s)")
        phase2 = self.run_load_test(client, 10, 200, "mixed")
        results['phases'].append(('spike', phase2))
        
        # Phase 3: Recovery
        print("\nPhase 3: Recovery (10s)")
        phase3 = self.run_load_test(client, 10, 30, "mixed")
        results['phases'].append(('recovery', phase3))
        
        # Analyze spike handling
        for phase_name, phase_results in results['phases']:
            print(f"\n{phase_name.capitalize()} Phase:")
            success_rate = phase_results['successful_requests'] / phase_results['total_requests']
            avg_response = statistics.mean(phase_results['response_times'])
            print(f"  Success rate: {success_rate:.2%}")
            print(f"  Avg response: {avg_response:.3f}s")
        
        # System should handle spike without complete failure
        spike_success_rate = results['phases'][1][1]['successful_requests'] / results['phases'][1][1]['total_requests']
        assert spike_success_rate > 0.90, "System should maintain >90% success during spike"
        
        # Recovery should return to normal
        recovery_success_rate = results['phases'][2][1]['successful_requests'] / results['phases'][2][1]['total_requests']
        assert recovery_success_rate > 0.98, "System should recover after spike"
    
    def test_sustained_high_load(self, client, load_test_service):
        """Test system limits with sustained high load."""
        _, _, metrics = load_test_service
        
        print("\n=== Sustained High Load Test ===")
        print("Duration: 60 seconds, Target: 150 RPS")
        
        results = self.run_load_test(
            client,
            duration_seconds=60,
            rps_target=150,
            scenario="mixed"
        )
        
        self._print_load_test_results(results)
        
        # Analyze degradation
        early_response_times = results['response_times'][:1000]
        late_response_times = results['response_times'][-1000:]
        
        early_avg = statistics.mean(early_response_times)
        late_avg = statistics.mean(late_response_times)
        degradation = (late_avg - early_avg) / early_avg
        
        print(f"\nPerformance degradation: {degradation:.1%}")
        
        # Some degradation is acceptable, but not too much
        assert degradation < 0.5, "Performance degradation exceeds 50%"
    
    def test_read_heavy_load(self, client, load_test_service):
        """Test with read-heavy workload."""
        _, _, metrics = load_test_service
        
        print("\n=== Read-Heavy Load Test ===")
        print("Duration: 30 seconds, Target: 100 RPS (95% reads)")
        
        results = self.run_load_test(
            client,
            duration_seconds=30,
            rps_target=100,
            scenario="read"
        )
        
        self._print_load_test_results(results)
        
        # Read-heavy workload should perform well
        success_rate = results['successful_requests'] / results['total_requests']
        assert success_rate > 0.99, "Read-heavy workload should have >99% success"
        
        # Check response times
        p50 = sorted(results['response_times'])[int(len(results['response_times']) * 0.50)]
        assert p50 < 0.05, "Median read response should be under 50ms"
    
    def test_write_heavy_load(self, client, load_test_service):
        """Test with write-heavy workload."""
        _, _, metrics = load_test_service
        
        print("\n=== Write-Heavy Load Test ===")
        print("Duration: 30 seconds, Target: 50 RPS (100% writes)")
        
        results = self.run_load_test(
            client,
            duration_seconds=30,
            rps_target=50,
            scenario="write"
        )
        
        self._print_load_test_results(results)
        
        # Write operations are slower, adjust expectations
        success_rate = results['successful_requests'] / results['total_requests']
        assert success_rate > 0.95, "Write-heavy workload should have >95% success"
    
    def test_memory_leak_detection(self, client, load_test_service):
        """Test for memory leaks under sustained load."""
        _, _, metrics = load_test_service
        
        print("\n=== Memory Leak Detection Test ===")
        print("Duration: 120 seconds, Target: 30 RPS")
        
        # Force garbage collection before starting
        import gc
        gc.collect()
        
        results = self.run_load_test(
            client,
            duration_seconds=120,
            rps_target=30,
            scenario="mixed"
        )
        
        # Analyze memory usage over time
        memory_usage = [r['memory_mb'] for r in results['resource_usage']]
        
        # Calculate memory growth
        initial_memory = statistics.mean(memory_usage[:5])
        final_memory = statistics.mean(memory_usage[-5:])
        memory_growth = final_memory - initial_memory
        growth_rate = memory_growth / initial_memory
        
        print(f"\nMemory Analysis:")
        print(f"  Initial: {initial_memory:.1f} MB")
        print(f"  Final: {final_memory:.1f} MB")
        print(f"  Growth: {memory_growth:.1f} MB ({growth_rate:.1%})")
        
        # Memory growth should be minimal
        assert memory_growth < 100, "Memory growth exceeds 100MB"
        assert growth_rate < 0.5, "Memory growth rate exceeds 50%"
    
    def test_connection_exhaustion(self, client):
        """Test behavior when connections are exhausted."""
        with patch('src.services.supabase_client.SupabaseClient.get_client') as mock:
            # Simulate connection pool exhaustion
            connection_count = {'current': 0, 'max': 10}
            
            def mock_execute():
                if connection_count['current'] >= connection_count['max']:
                    raise Exception("Connection pool exhausted")
                
                connection_count['current'] += 1
                time.sleep(0.1)  # Hold connection
                connection_count['current'] -= 1
                
                return MagicMock(data=[], count=0)
            
            # Setup mock
            client_mock = MagicMock()
            table_mock = MagicMock()
            table_mock.execute = mock_execute
            
            for method in ['select', 'eq', 'order', 'limit', 'range']:
                setattr(table_mock, method, MagicMock(return_value=table_mock))
            
            client_mock.table.return_value = table_mock
            mock.return_value = client_mock
            
            print("\n=== Connection Exhaustion Test ===")
            
            # Try to make more concurrent requests than connections
            errors = []
            success = []
            
            def make_request(i):
                try:
                    response = client.get("/dashboard/hechos_revision")
                    if response.status_code == 200:
                        success.append(i)
                    else:
                        errors.append((i, response.status_code))
                except Exception as e:
                    errors.append((i, str(e)))
            
            # Launch many concurrent requests
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(make_request, i) for i in range(20)]
                for future in as_completed(futures):
                    future.result()
            
            print(f"Successful requests: {len(success)}")
            print(f"Failed requests: {len(errors)}")
            
            # Some requests should fail due to exhaustion
            assert len(errors) > 0, "Should have connection exhaustion errors"
            assert len(success) > 0, "Some requests should still succeed"
    
    def test_cascading_failure_prevention(self, client, load_test_service):
        """Test that failures don't cascade through the system."""
        hechos_service, feedback_service, metrics = load_test_service
        
        print("\n=== Cascading Failure Prevention Test ===")
        
        # Configure service to fail intermittently
        failure_rate = {'current': 0.0}
        
        async def failing_get_hechos(params):
            if random.random() < failure_rate['current']:
                raise Exception("Service temporarily unavailable")
            
            await asyncio.sleep(0.02)
            return [], 0
        
        hechos_service.get_hechos_for_revision.side_effect = failing_get_hechos
        
        # Gradually increase failure rate
        phases = [
            ("Normal", 0.0, 10),
            ("10% failures", 0.1, 10),
            ("25% failures", 0.25, 10),
            ("50% failures", 0.5, 10),
            ("Recovery", 0.0, 10)
        ]
        
        for phase_name, fail_rate, duration in phases:
            failure_rate['current'] = fail_rate
            
            print(f"\n{phase_name} phase:")
            results = self.run_load_test(client, duration, 30, "read")
            
            success_rate = results['successful_requests'] / results['total_requests']
            print(f"  Success rate: {success_rate:.2%}")
            
            # Even with 50% backend failures, API should handle gracefully
            if fail_rate > 0:
                assert results['failed_requests'] > 0, "Should have some failures"
    
    def _print_load_test_results(self, results: Dict):
        """Print formatted load test results."""
        print(f"\nResults:")
        print(f"  Total requests: {results['total_requests']}")
        print(f"  Successful: {results['successful_requests']}")
        print(f"  Failed: {results['failed_requests']}")
        print(f"  Actual RPS: {results['actual_rps']:.1f}")
        
        if results['response_times']:
            times = sorted(results['response_times'])
            print(f"\nResponse times:")
            print(f"  Min: {min(times):.3f}s")
            print(f"  P50: {times[int(len(times) * 0.50)]:.3f}s")
            print(f"  P95: {times[int(len(times) * 0.95)]:.3f}s")
            print(f"  P99: {times[int(len(times) * 0.99)]:.3f}s")
            print(f"  Max: {max(times):.3f}s")
        
        if results['errors_by_type']:
            print(f"\nErrors by type:")
            for error_type, count in results['errors_by_type'].items():
                print(f"  {error_type}: {count}")
        
        if results['resource_usage']:
            avg_cpu = statistics.mean(r['cpu_percent'] for r in results['resource_usage'])
            max_memory = max(r['memory_mb'] for r in results['resource_usage'])
            print(f"\nResource usage:")
            print(f"  Avg CPU: {avg_cpu:.1f}%")
            print(f"  Max memory: {max_memory:.1f} MB")


class TestLoadPatterns:
    """Test specific load patterns and scenarios."""
    
    def test_gradual_ramp_up(self, client):
        """Test system behavior with gradually increasing load."""
        print("\n=== Gradual Ramp-up Test ===")
        
        with patch('src.api.dashboard.get_hechos_service') as mock:
            service = MagicMock()
            service.get_hechos_for_revision = AsyncMock(return_value=([], 0))
            mock.return_value = service
            
            results_by_rps = {}
            
            # Gradually increase load
            for rps in [10, 25, 50, 75, 100, 150, 200]:
                print(f"\nTesting {rps} RPS...")
                
                response_times = []
                errors = 0
                
                # Run for 5 seconds at each level
                start_time = time.time()
                request_count = 0
                
                with ThreadPoolExecutor(max_workers=min(rps, 50)) as executor:
                    while time.time() - start_time < 5:
                        def make_request():
                            try:
                                req_start = time.time()
                                response = client.get("/dashboard/hechos_revision")
                                req_time = time.time() - req_start
                                
                                if response.status_code == 200:
                                    return req_time
                                else:
                                    return None
                            except:
                                return None
                        
                        future = executor.submit(make_request)
                        request_count += 1
                        
                        # Control rate
                        time.sleep(1.0 / rps)
                    
                    # Collect results
                    for future in as_completed(executor._futures):
                        result = future.result()
                        if result:
                            response_times.append(result)
                        else:
                            errors += 1
                
                # Calculate metrics
                if response_times:
                    results_by_rps[rps] = {
                        'mean': statistics.mean(response_times),
                        'p95': sorted(response_times)[int(len(response_times) * 0.95)],
                        'errors': errors,
                        'success_rate': len(response_times) / request_count
                    }
                    
                    print(f"  Mean response: {results_by_rps[rps]['mean']:.3f}s")
                    print(f"  P95 response: {results_by_rps[rps]['p95']:.3f}s")
                    print(f"  Success rate: {results_by_rps[rps]['success_rate']:.2%}")
            
            # Find breaking point
            breaking_point = None
            for rps in sorted(results_by_rps.keys()):
                if results_by_rps[rps]['success_rate'] < 0.95:
                    breaking_point = rps
                    break
            
            print(f"\nBreaking point: {breaking_point or '>200'} RPS")
            
            # System should handle at least 100 RPS
            assert breaking_point is None or breaking_point > 100, \
                "System should handle at least 100 RPS"
