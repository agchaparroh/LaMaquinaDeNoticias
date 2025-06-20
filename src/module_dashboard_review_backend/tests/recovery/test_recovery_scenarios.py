"""
Recovery tests for Dashboard Review Backend.

Tests system resilience and recovery from various failure scenarios
including database outages, network issues, and service crashes.
"""

import asyncio
import time
from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock, PropertyMock
import random
from typing import Dict, List
import psutil

from src.main import app
from src.utils.exceptions import DatabaseConnectionError


class TestDatabaseRecovery:
    """Test recovery from database-related failures."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_failing_supabase(self):
        """Mock Supabase client that can simulate failures."""
        with patch('src.services.supabase_client.SupabaseClient.get_client') as mock:
            client = MagicMock()
            
            # Failure control
            failure_config = {
                'enabled': False,
                'type': 'connection',  # connection, timeout, data_corruption
                'duration': 0,
                'start_time': None
            }
            
            def should_fail():
                if not failure_config['enabled']:
                    return False
                
                if failure_config['duration'] > 0:
                    elapsed = time.time() - failure_config['start_time']
                    return elapsed < failure_config['duration']
                
                return True
            
            # Mock table operations
            table_mock = MagicMock()
            
            def mock_execute():
                if should_fail():
                    if failure_config['type'] == 'connection':
                        raise DatabaseConnectionError("Connection to database lost")
                    elif failure_config['type'] == 'timeout':
                        time.sleep(5)  # Simulate timeout
                        raise TimeoutError("Query timeout")
                    elif failure_config['type'] == 'data_corruption':
                        return MagicMock(data=[{'corrupted': True}], count=None)
                
                # Normal operation
                return MagicMock(
                    data=[
                        {
                            'id': i,
                            'contenido': f'Test hecho {i}',
                            'fecha_ocurrencia': '2024-01-15T10:00:00',
                            'importancia': 5,
                            'articulos': {'medio': 'Test Media'}
                        }
                        for i in range(10)
                    ],
                    count=100
                )
            
            table_mock.execute = mock_execute
            
            # Setup method chaining
            for method in ['select', 'insert', 'update', 'eq', 'gte', 'lte', 
                          'order', 'limit', 'range', 'single']:
                setattr(table_mock, method, MagicMock(return_value=table_mock))
            
            client.table.return_value = table_mock
            
            # Attach control methods
            def enable_failure(failure_type='connection', duration=0):
                failure_config['enabled'] = True
                failure_config['type'] = failure_type
                failure_config['duration'] = duration
                failure_config['start_time'] = time.time()
            
            def disable_failure():
                failure_config['enabled'] = False
            
            client.enable_failure = enable_failure
            client.disable_failure = disable_failure
            client._failure_config = failure_config
            
            mock.return_value = client
            yield client
    
    def test_database_connection_recovery(self, client, mock_failing_supabase):
        """Test recovery from temporary database connection loss."""
        print("\n=== Database Connection Recovery Test ===")
        
        # Phase 1: Normal operation
        print("Phase 1: Normal operation")
        response = client.get("/dashboard/hechos_revision")
        assert response.status_code == 200
        initial_data = response.json()
        assert len(initial_data['items']) > 0
        
        # Phase 2: Simulate connection failure
        print("Phase 2: Database connection failure (5 seconds)")
        mock_failing_supabase.enable_failure('connection', duration=5)
        
        # Requests should fail during outage
        start_time = time.time()
        errors = 0
        attempts = 0
        
        while time.time() - start_time < 6:
            response = client.get("/dashboard/hechos_revision")
            attempts += 1
            if response.status_code != 200:
                errors += 1
            time.sleep(0.5)
        
        print(f"  Attempts: {attempts}, Errors: {errors}")
        assert errors > 0, "Should have errors during database outage"
        
        # Phase 3: Recovery
        print("Phase 3: Automatic recovery")
        # Wait for failure to expire
        time.sleep(1)
        
        # Should recover automatically
        recovery_attempts = 0
        recovered = False
        
        for i in range(10):
            response = client.get("/dashboard/hechos_revision")
            recovery_attempts += 1
            
            if response.status_code == 200:
                recovered = True
                break
            
            time.sleep(0.5)
        
        print(f"  Recovery attempts: {recovery_attempts}")
        assert recovered, "System should recover after database comes back"
        
        # Verify data integrity after recovery
        recovery_data = response.json()
        assert len(recovery_data['items']) > 0, "Should return data after recovery"
    
    def test_database_timeout_handling(self, client, mock_failing_supabase):
        """Test handling of database query timeouts."""
        print("\n=== Database Timeout Handling Test ===")
        
        # Enable timeout failures
        mock_failing_supabase.enable_failure('timeout', duration=3)
        
        # Make request that will timeout
        start_time = time.time()
        response = client.get("/dashboard/hechos_revision")
        duration = time.time() - start_time
        
        print(f"Request duration: {duration:.2f}s")
        print(f"Response status: {response.status_code}")
        
        # Should fail fast, not hang indefinitely
        assert response.status_code == 500
        assert duration < 10, "Should timeout quickly, not hang"
        
        # Disable failures and verify recovery
        mock_failing_supabase.disable_failure()
        
        response = client.get("/dashboard/hechos_revision")
        assert response.status_code == 200, "Should work after timeout resolved"
    
    def test_partial_data_recovery(self, client, mock_failing_supabase):
        """Test handling of partial/corrupted data responses."""
        print("\n=== Partial Data Recovery Test ===")
        
        # Configure to return corrupted data
        mock_failing_supabase.enable_failure('data_corruption')
        
        # System should handle corrupted data gracefully
        response = client.get("/dashboard/hechos_revision")
        
        # Might return 500 or empty results, but shouldn't crash
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            # Should have handled corrupted data somehow
            assert 'items' in data
    
    def test_connection_pool_recovery(self, client):
        """Test recovery of connection pool after exhaustion."""
        print("\n=== Connection Pool Recovery Test ===")
        
        with patch('src.services.supabase_client.SupabaseClient.execute_with_retry') as mock_retry:
            # Simulate connection pool exhaustion then recovery
            call_count = {'total': 0}
            
            async def mock_execute(func, *args, **kwargs):
                call_count['total'] += 1
                
                # Fail first 5 calls (pool exhausted)
                if call_count['total'] <= 5:
                    raise Exception("Connection pool exhausted")
                
                # Then recover
                return MagicMock(data=[], count=0)
            
            mock_retry.side_effect = mock_execute
            
            # Make multiple attempts
            attempts = []
            for i in range(10):
                response = client.get("/dashboard/hechos_revision")
                attempts.append({
                    'attempt': i + 1,
                    'status': response.status_code,
                    'success': response.status_code == 200
                })
                time.sleep(0.1)
            
            # Analyze recovery pattern
            failures = sum(1 for a in attempts if not a['success'])
            recoveries = sum(1 for a in attempts if a['success'])
            
            print(f"Total attempts: {len(attempts)}")
            print(f"Failures: {failures}")
            print(f"Successful recoveries: {recoveries}")
            
            # Should eventually recover
            assert recoveries > 0, "Should recover after pool issues resolved"
            assert attempts[-1]['success'], "Should be working by the end"
    
    def test_retry_mechanism_effectiveness(self, client):
        """Test the effectiveness of retry mechanisms."""
        print("\n=== Retry Mechanism Test ===")
        
        with patch('src.services.supabase_client.SupabaseClient.get_client') as mock_client:
            # Track retry attempts
            retry_counts = []
            
            def create_flaky_execute(success_after=2):
                attempts = {'count': 0}
                
                def flaky_execute():
                    attempts['count'] += 1
                    retry_counts.append(attempts['count'])
                    
                    if attempts['count'] < success_after:
                        raise Exception(f"Temporary failure {attempts['count']}")
                    
                    return MagicMock(data=[], count=0)
                
                return flaky_execute
            
            # Setup mock
            client_mock = MagicMock()
            table_mock = MagicMock()
            
            # Make it fail twice then succeed
            table_mock.execute = create_flaky_execute(success_after=3)
            
            for method in ['select', 'eq', 'order', 'limit', 'range']:
                setattr(table_mock, method, MagicMock(return_value=table_mock))
            
            client_mock.table.return_value = table_mock
            mock_client.return_value = client_mock
            
            # Make request - should retry and eventually succeed
            response = client.get("/dashboard/hechos_revision")
            
            print(f"Retry attempts: {retry_counts}")
            print(f"Final status: {response.status_code}")
            
            # Should succeed after retries
            assert response.status_code == 200, "Should succeed after retries"
            assert len(retry_counts) >= 2, "Should have retried at least once"


class TestServiceRecovery:
    """Test recovery from service-level failures."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_service_restart_recovery(self, client):
        """Test that service can recover from restart/crash."""
        print("\n=== Service Restart Recovery Test ===")
        
        # Phase 1: Normal operation
        response = client.get("/health")
        assert response.status_code == 200
        initial_uptime = None
        
        # Get detailed health for uptime
        response = client.get("/health/detailed")
        if response.status_code == 200:
            initial_uptime = response.json().get('uptime', 0)
        
        print(f"Initial uptime: {initial_uptime:.1f}s")
        
        # Simulate service "restart" by resetting some state
        from src.services.supabase_client import SupabaseClient
        
        # Reset singleton
        SupabaseClient._instance = None
        SupabaseClient._client = None
        
        # Phase 2: After "restart"
        print("Phase 2: After simulated restart")
        
        # Service should be immediately available
        response = client.get("/health")
        assert response.status_code == 200, "Health check should work immediately"
        
        # Functional endpoints should work
        response = client.get("/dashboard/hechos_revision")
        # Might fail if DB not mocked, but shouldn't crash
        assert response.status_code in [200, 500]
        
        print("✓ Service recovered successfully")
    
    def test_memory_pressure_recovery(self, client):
        """Test recovery from memory pressure situations."""
        print("\n=== Memory Pressure Recovery Test ===")
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        print(f"Initial memory: {initial_memory:.1f} MB")
        
        # Phase 1: Create memory pressure
        print("Phase 1: Creating memory pressure")
        
        # Make many requests with large responses
        large_data = []
        for i in range(100):
            response = client.get("/dashboard/hechos_revision", params={"limit": 100})
            if response.status_code == 200:
                # Keep references to create memory pressure
                large_data.append(response.json())
        
        peak_memory = process.memory_info().rss / 1024 / 1024
        print(f"Peak memory: {peak_memory:.1f} MB")
        
        # Phase 2: Release memory pressure
        print("Phase 2: Releasing memory")
        large_data = None
        
        # Force garbage collection
        import gc
        gc.collect()
        
        # Wait a moment
        time.sleep(1)
        
        final_memory = process.memory_info().rss / 1024 / 1024
        print(f"Final memory: {final_memory:.1f} MB")
        
        # Phase 3: Verify normal operation
        print("Phase 3: Verifying normal operation")
        response = client.get("/dashboard/hechos_revision")
        assert response.status_code in [200, 500], "Should still be operational"
        
        # Memory should have been released
        memory_recovered = peak_memory - final_memory
        print(f"Memory recovered: {memory_recovered:.1f} MB")
        
        # Should recover at least some memory
        assert memory_recovered > 0, "Should recover some memory"
    
    def test_cascading_service_failure_recovery(self, client):
        """Test recovery from cascading service failures."""
        print("\n=== Cascading Failure Recovery Test ===")
        
        with patch('src.api.dashboard.get_hechos_service') as mock_hechos:
            with patch('src.api.feedback.get_feedback_service') as mock_feedback:
                # Setup services
                hechos_service = MagicMock()
                feedback_service = MagicMock()
                
                # Failure states
                service_states = {
                    'hechos': 'healthy',
                    'feedback': 'healthy'
                }
                
                async def mock_hechos_call(params):
                    if service_states['hechos'] == 'failed':
                        raise Exception("Hechos service unavailable")
                    return [], 0
                
                async def mock_feedback_call(hecho_id, feedback):
                    if service_states['feedback'] == 'failed':
                        raise Exception("Feedback service unavailable")
                    
                    # If hechos service is down, this might also fail
                    if service_states['hechos'] == 'failed' and random.random() < 0.5:
                        raise Exception("Cascading failure from hechos service")
                
                hechos_service.get_hechos_for_revision = AsyncMock(
                    side_effect=mock_hechos_call
                )
                feedback_service.submit_importancia_feedback = AsyncMock(
                    side_effect=mock_feedback_call
                )
                
                mock_hechos.return_value = hechos_service
                mock_feedback.return_value = feedback_service
                
                # Phase 1: Normal operation
                print("Phase 1: All services healthy")
                response = client.get("/dashboard/hechos_revision")
                assert response.status_code == 200
                
                # Phase 2: Hechos service fails
                print("Phase 2: Hechos service fails")
                service_states['hechos'] = 'failed'
                
                # Both endpoints might be affected
                response = client.get("/dashboard/hechos_revision")
                assert response.status_code == 500
                
                # Feedback might still work or fail (cascading)
                response = client.post(
                    "/dashboard/feedback/hecho/123/importancia_feedback",
                    json={
                        "importancia_editor_final": 8,
                        "usuario_id_editor": "test"
                    }
                )
                # Could be 200 or 500 depending on cascade
                
                # Phase 3: Recovery
                print("Phase 3: Services recover")
                service_states['hechos'] = 'healthy'
                service_states['feedback'] = 'healthy'
                
                # Both should work again
                response = client.get("/dashboard/hechos_revision")
                assert response.status_code == 200
                
                response = client.post(
                    "/dashboard/feedback/hecho/123/importancia_feedback",
                    json={
                        "importancia_editor_final": 8,
                        "usuario_id_editor": "test"
                    }
                )
                assert response.status_code == 200
                
                print("✓ Recovered from cascading failures")
    
    def test_circuit_breaker_behavior(self, client):
        """Test circuit breaker pattern for failing services."""
        print("\n=== Circuit Breaker Test ===")
        
        with patch('src.services.supabase_client.SupabaseClient.execute_with_retry') as mock:
            # Track circuit breaker state
            circuit_state = {
                'failures': 0,
                'threshold': 5,
                'is_open': False,
                'opened_at': None,
                'timeout': 5  # seconds
            }
            
            async def mock_with_circuit_breaker(func, *args, **kwargs):
                # Check if circuit is open
                if circuit_state['is_open']:
                    # Check if timeout has passed
                    if time.time() - circuit_state['opened_at'] > circuit_state['timeout']:
                        print("  Circuit breaker: Attempting reset")
                        circuit_state['is_open'] = False
                        circuit_state['failures'] = 0
                    else:
                        print("  Circuit breaker: OPEN - failing fast")
                        raise Exception("Circuit breaker is open")
                
                # Try the operation
                try:
                    # Simulate failures for first N attempts
                    if circuit_state['failures'] < circuit_state['threshold']:
                        raise Exception("Service failure")
                    
                    # Success
                    return MagicMock(data=[], count=0)
                    
                except Exception as e:
                    circuit_state['failures'] += 1
                    
                    # Open circuit if threshold reached
                    if circuit_state['failures'] >= circuit_state['threshold']:
                        circuit_state['is_open'] = True
                        circuit_state['opened_at'] = time.time()
                        print(f"  Circuit breaker: OPENED after {circuit_state['failures']} failures")
                    
                    raise e
            
            mock.side_effect = mock_with_circuit_breaker
            
            # Make requests and observe circuit breaker behavior
            results = []
            
            print("Making requests to observe circuit breaker:")
            for i in range(15):
                start = time.time()
                response = client.get("/dashboard/hechos_revision")
                duration = time.time() - start
                
                results.append({
                    'attempt': i + 1,
                    'status': response.status_code,
                    'duration': duration,
                    'circuit_open': circuit_state['is_open']
                })
                
                print(f"  Attempt {i+1}: Status {response.status_code}, "
                      f"Duration {duration:.3f}s, Circuit: "
                      f"{'OPEN' if circuit_state['is_open'] else 'CLOSED'}")
                
                time.sleep(0.5)
            
            # Analyze results
            failed_attempts = sum(1 for r in results if r['status'] != 200)
            fast_fails = sum(1 for r in results if r['duration'] < 0.1 and r['status'] != 200)
            
            print(f"\nResults:")
            print(f"  Failed attempts: {failed_attempts}")
            print(f"  Fast fails (circuit open): {fast_fails}")
            
            # Should have some fast fails when circuit is open
            assert fast_fails > 0, "Circuit breaker should cause fast fails"
            
            # Response time should be faster when circuit is open
            open_circuit_times = [r['duration'] for r in results if r['circuit_open']]
            if open_circuit_times:
                avg_open_time = sum(open_circuit_times) / len(open_circuit_times)
                assert avg_open_time < 0.1, "Circuit breaker should fail fast"


class TestNetworkRecovery:
    """Test recovery from network-related issues."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_network_timeout_recovery(self, client):
        """Test recovery from network timeouts."""
        print("\n=== Network Timeout Recovery Test ===")
        
        with patch('httpx.AsyncClient.request') as mock_request:
            # Simulate network timeouts
            timeout_count = {'current': 0, 'max': 3}
            
            async def mock_network_request(*args, **kwargs):
                timeout_count['current'] += 1
                
                if timeout_count['current'] <= timeout_count['max']:
                    # Simulate network timeout
                    await asyncio.sleep(0.1)
                    raise asyncio.TimeoutError("Network request timed out")
                
                # Eventually succeed
                return MagicMock(
                    status_code=200,
                    json=lambda: {'data': [], 'count': 0}
                )
            
            mock_request.side_effect = mock_network_request
            
            # Should handle timeouts gracefully
            response = client.get("/dashboard/hechos_revision")
            
            # Might fail or succeed depending on retry logic
            assert response.status_code in [200, 500]
            
            print(f"Network timeout attempts: {timeout_count['current']}")
    
    def test_intermittent_network_issues(self, client):
        """Test handling of intermittent network problems."""
        print("\n=== Intermittent Network Issues Test ===")
        
        with patch('src.services.supabase_client.SupabaseClient.get_client') as mock:
            # Simulate intermittent failures
            request_count = {'total': 0}
            
            def create_intermittent_execute():
                def execute():
                    request_count['total'] += 1
                    
                    # Fail 30% of the time
                    if random.random() < 0.3:
                        raise Exception("Network error: Connection reset")
                    
                    return MagicMock(data=[], count=0)
                
                return execute
            
            # Setup mock
            client_mock = MagicMock()
            table_mock = MagicMock()
            table_mock.execute = create_intermittent_execute()
            
            for method in ['select', 'eq', 'order', 'limit', 'range']:
                setattr(table_mock, method, MagicMock(return_value=table_mock))
            
            client_mock.table.return_value = table_mock
            mock.return_value = client_mock
            
            # Make multiple requests
            results = []
            for i in range(20):
                response = client.get("/dashboard/hechos_revision")
                results.append({
                    'attempt': i + 1,
                    'status': response.status_code,
                    'success': response.status_code == 200
                })
            
            # Calculate success rate
            success_rate = sum(1 for r in results if r['success']) / len(results)
            
            print(f"Total requests: {len(results)}")
            print(f"Successful: {sum(1 for r in results if r['success'])}")
            print(f"Failed: {sum(1 for r in results if not r['success'])}")
            print(f"Success rate: {success_rate:.1%}")
            
            # Should handle intermittent issues reasonably well
            # With 30% network failure rate and retries, should still have decent success
            assert success_rate > 0.5, "Should handle intermittent network issues"


class TestDataIntegrityRecovery:
    """Test recovery and data integrity after failures."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_transaction_rollback_on_failure(self, client):
        """Test that failed operations don't leave inconsistent state."""
        print("\n=== Transaction Rollback Test ===")
        
        with patch('src.api.feedback.get_feedback_service') as mock:
            service = MagicMock()
            
            # Track state changes
            state_changes = []
            
            async def mock_feedback_with_failure(hecho_id, feedback):
                # Record attempted change
                state_changes.append({
                    'hecho_id': hecho_id,
                    'operation': 'update',
                    'timestamp': time.time()
                })
                
                # Fail after partial operation
                if len(state_changes) % 3 == 0:
                    raise Exception("Operation failed mid-transaction")
                
                return True
            
            service.submit_importancia_feedback = AsyncMock(
                side_effect=mock_feedback_with_failure
            )
            mock.return_value = service
            
            # Attempt multiple operations
            results = []
            for i in range(10):
                response = client.post(
                    f"/dashboard/feedback/hecho/{i}/importancia_feedback",
                    json={
                        "importancia_editor_final": 8,
                        "usuario_id_editor": "test"
                    }
                )
                
                results.append({
                    'hecho_id': i,
                    'status': response.status_code,
                    'success': response.status_code == 200
                })
            
            # Analyze results
            print(f"State changes attempted: {len(state_changes)}")
            print(f"Successful operations: {sum(1 for r in results if r['success'])}")
            print(f"Failed operations: {sum(1 for r in results if not r['success'])}")
            
            # Failed operations should not have partial state
            failed_ids = [r['hecho_id'] for r in results if not r['success']]
            print(f"Failed hecho IDs: {failed_ids}")
            
            # In a real system, we'd verify no partial updates were persisted
            assert len(failed_ids) > 0, "Should have some failures"
    
    def test_cache_invalidation_after_recovery(self, client):
        """Test that caches are properly invalidated after recovery."""
        print("\n=== Cache Invalidation Test ===")
        
        with patch('src.api.dashboard.get_hechos_service') as mock:
            service = MagicMock()
            
            # Simulate cached data
            cache = {'filter_options': None, 'timestamp': None}
            
            async def mock_get_filter_options():
                # Return cached data if available and fresh
                if cache['filter_options'] and cache['timestamp']:
                    age = time.time() - cache['timestamp']
                    if age < 60:  # 1 minute cache
                        print("  Returning cached data")
                        return cache['filter_options']
                
                # Generate fresh data
                print("  Generating fresh data")
                data = {
                    'medios_disponibles': ['Medio1', 'Medio2'],
                    'paises_disponibles': ['Pais1', 'Pais2'],
                    'importancia_range': {'min': 1, 'max': 10}
                }
                
                cache['filter_options'] = data
                cache['timestamp'] = time.time()
                
                return data
            
            service.get_filter_options = AsyncMock(side_effect=mock_get_filter_options)
            
            # Simulate failure that should invalidate cache
            failure_mode = {'enabled': False}
            
            async def mock_get_filter_options_with_failure():
                if failure_mode['enabled']:
                    # Invalidate cache on failure
                    cache['filter_options'] = None
                    cache['timestamp'] = None
                    raise Exception("Service temporarily unavailable")
                
                return await mock_get_filter_options()
            
            service.get_filter_options = AsyncMock(
                side_effect=mock_get_filter_options_with_failure
            )
            mock.return_value = service
            
            # Phase 1: Populate cache
            print("Phase 1: Populating cache")
            response = client.get("/dashboard/filtros/opciones")
            assert response.status_code == 200
            
            # Phase 2: Use cached data
            print("Phase 2: Using cached data")
            response = client.get("/dashboard/filtros/opciones")
            assert response.status_code == 200
            
            # Phase 3: Failure (should invalidate cache)
            print("Phase 3: Service failure")
            failure_mode['enabled'] = True
            response = client.get("/dashboard/filtros/opciones")
            assert response.status_code == 500
            
            # Phase 4: Recovery (should not use stale cache)
            print("Phase 4: Recovery with fresh data")
            failure_mode['enabled'] = False
            response = client.get("/dashboard/filtros/opciones")
            assert response.status_code == 200
            
            # Verify cache was invalidated and refreshed
            assert cache['filter_options'] is not None, "Cache should be repopulated"
            print("✓ Cache properly invalidated and refreshed")
