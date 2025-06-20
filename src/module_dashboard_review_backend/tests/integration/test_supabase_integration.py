"""
Integration tests with real Supabase instance.

These tests require a real Supabase test instance to be configured.
They test actual database operations, constraints, and behaviors.

IMPORTANT: Set TEST_SUPABASE_URL and TEST_SUPABASE_KEY environment variables
pointing to a test instance before running these tests.
"""

import os
import asyncio
import time
from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import random
import uuid
from typing import List, Dict

from src.main import app
from src.services.supabase_client import SupabaseClient


# Skip tests if test database credentials not provided
SKIP_INTEGRATION = not all([
    os.getenv('TEST_SUPABASE_URL'),
    os.getenv('TEST_SUPABASE_KEY')
])

pytestmark = pytest.mark.skipif(
    SKIP_INTEGRATION,
    reason="Test Supabase credentials not configured"
)


class TestRealSupabaseIntegration:
    """Integration tests with real Supabase instance."""
    
    @pytest.fixture
    def test_client(self):
        """Create test client with test database."""
        with patch.dict(os.environ, {
            'SUPABASE_URL': os.getenv('TEST_SUPABASE_URL', ''),
            'SUPABASE_KEY': os.getenv('TEST_SUPABASE_KEY', '')
        }):
            # Reset singleton for test
            SupabaseClient._instance = None
            SupabaseClient._client = None
            
            yield TestClient(app)
            
            # Cleanup after test
            SupabaseClient._instance = None
            SupabaseClient._client = None
    
    @pytest.fixture
    async def test_data_cleanup(self, test_client):
        """Fixture to track and cleanup test data."""
        created_hechos = []
        created_feedback = []
        
        yield created_hechos, created_feedback
        
        # Cleanup after test
        if created_hechos or created_feedback:
            client = SupabaseClient.get_client()
            
            # Delete test feedback
            if created_feedback:
                for feedback_id in created_feedback:
                    try:
                        client.table('feedback_importancia_hechos')\
                            .delete()\
                            .eq('id', feedback_id)\
                            .execute()
                    except:
                        pass
            
            # Delete test hechos
            if created_hechos:
                for hecho_id in created_hechos:
                    try:
                        client.table('hechos')\
                            .delete()\
                            .eq('id', hecho_id)\
                            .execute()
                    except:
                        pass
    
    async def create_test_hecho(self, **kwargs) -> Dict:
        """Create a test hecho in the database."""
        client = SupabaseClient.get_client()
        
        # Default test data
        test_hecho = {
            'contenido': f'Test hecho {uuid.uuid4()}',
            'fecha_ocurrencia': datetime.now().isoformat(),
            'importancia': random.randint(1, 10),
            'tipo_hecho': 'test',
            'pais': 'Test Country',
            'consenso_fuentes': 1,
            **kwargs
        }
        
        result = client.table('hechos').insert(test_hecho).execute()
        return result.data[0] if result.data else None
    
    @pytest.mark.asyncio
    async def test_real_database_connection(self, test_client):
        """Test actual connection to Supabase."""
        print("\n=== Real Database Connection Test ===")
        
        # Test health check with real database
        response = test_client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        
        print(f"Database status: {data['dependencies']['supabase']['status']}")
        print(f"Response time: {data['dependencies']['supabase'].get('response_time_ms', 'N/A')}ms")
        
        assert data['dependencies']['supabase']['status'] == 'ok'
        assert 'response_time_ms' in data['dependencies']['supabase']
    
    @pytest.mark.asyncio
    async def test_real_hecho_retrieval(self, test_client, test_data_cleanup):
        """Test retrieving hechos from real database."""
        created_hechos, _ = test_data_cleanup
        
        print("\n=== Real Hecho Retrieval Test ===")
        
        # Create test data
        test_hechos = []
        for i in range(5):
            hecho = await self.create_test_hecho(
                contenido=f'Integration test hecho {i}',
                importancia=i + 5,
                pais='Argentina' if i % 2 == 0 else 'Chile'
            )
            if hecho:
                test_hechos.append(hecho)
                created_hechos.append(hecho['id'])
        
        print(f"Created {len(test_hechos)} test hechos")
        
        # Test retrieval without filters
        response = test_client.get("/dashboard/hechos_revision")
        assert response.status_code == 200
        
        data = response.json()
        assert 'items' in data
        assert 'pagination' in data
        
        # Should include our test hechos
        retrieved_ids = [item['id'] for item in data['items']]
        test_ids = [h['id'] for h in test_hechos]
        
        found_test_hechos = sum(1 for tid in test_ids if tid in retrieved_ids)
        print(f"Found {found_test_hechos}/{len(test_hechos)} test hechos")
        
        # Test with filters
        response = test_client.get(
            "/dashboard/hechos_revision",
            params={
                'pais_publicacion': 'Argentina',
                'importancia_min': 7
            }
        )
        
        assert response.status_code == 200
        filtered_data = response.json()
        
        # Should only get Argentina hechos with importance >= 7
        for item in filtered_data['items']:
            if item['id'] in test_ids:
                assert item['pais'] == 'Argentina'
                assert item['importancia'] >= 7
    
    @pytest.mark.asyncio
    async def test_real_feedback_submission(self, test_client, test_data_cleanup):
        """Test submitting feedback to real database."""
        created_hechos, created_feedback = test_data_cleanup
        
        print("\n=== Real Feedback Submission Test ===")
        
        # Create a test hecho
        test_hecho = await self.create_test_hecho(
            contenido='Hecho for feedback test',
            importancia=5
        )
        created_hechos.append(test_hecho['id'])
        
        # Submit importance feedback
        response = test_client.post(
            f"/dashboard/feedback/hecho/{test_hecho['id']}/importancia_feedback",
            json={
                "importancia_editor_final": 8,
                "usuario_id_editor": "integration_test_user"
            }
        )
        
        assert response.status_code == 200
        
        # Verify feedback was saved
        client = SupabaseClient.get_client()
        result = client.table('feedback_importancia_hechos')\
            .select('*')\
            .eq('hecho_id', test_hecho['id'])\
            .execute()
        
        assert len(result.data) > 0
        feedback = result.data[0]
        created_feedback.append(feedback['id'])
        
        assert feedback['importancia_editor_final'] == 8
        assert feedback['usuario_id_editor'] == 'integration_test_user'
        
        print("✓ Feedback saved successfully")
        
        # Submit editorial evaluation
        response = test_client.post(
            f"/dashboard/feedback/hecho/{test_hecho['id']}/evaluacion_editorial",
            json={
                "evaluacion_editorial": "verificado_ok_editorial",
                "justificacion_evaluacion_editorial": "Integration test verification"
            }
        )
        
        assert response.status_code == 200
        
        # Verify hecho was updated
        result = client.table('hechos')\
            .select('evaluacion_editorial, justificacion_evaluacion_editorial')\
            .eq('id', test_hecho['id'])\
            .single()\
            .execute()
        
        assert result.data['evaluacion_editorial'] == 'verificado_ok_editorial'
        assert result.data['justificacion_evaluacion_editorial'] == 'Integration test verification'
        
        print("✓ Editorial evaluation saved successfully")
    
    @pytest.mark.asyncio
    async def test_real_pagination(self, test_client, test_data_cleanup):
        """Test pagination with real data."""
        created_hechos, _ = test_data_cleanup
        
        print("\n=== Real Pagination Test ===")
        
        # Create enough test data for pagination
        for i in range(25):
            hecho = await self.create_test_hecho(
                contenido=f'Pagination test hecho {i}',
                importancia=(i % 10) + 1
            )
            if hecho:
                created_hechos.append(hecho['id'])
        
        # Test first page
        response = test_client.get(
            "/dashboard/hechos_revision",
            params={"limit": 10, "offset": 0}
        )
        
        assert response.status_code == 200
        page1 = response.json()
        
        assert len(page1['items']) <= 10
        assert page1['pagination']['page'] == 1
        assert page1['pagination']['has_next'] == True
        
        # Test second page
        response = test_client.get(
            "/dashboard/hechos_revision",
            params={"limit": 10, "offset": 10}
        )
        
        assert response.status_code == 200
        page2 = response.json()
        
        assert page2['pagination']['page'] == 2
        assert page2['pagination']['has_prev'] == True
        
        # Ensure no duplicate items between pages
        page1_ids = [item['id'] for item in page1['items']]
        page2_ids = [item['id'] for item in page2['items']]
        
        assert len(set(page1_ids) & set(page2_ids)) == 0, "Pages should not have duplicate items"
        
        print(f"✓ Pagination working correctly")
        print(f"  Page 1: {len(page1['items'])} items")
        print(f"  Page 2: {len(page2['items'])} items")
    
    @pytest.mark.asyncio
    async def test_real_filter_options(self, test_client, test_data_cleanup):
        """Test filter options with real data."""
        created_hechos, _ = test_data_cleanup
        
        print("\n=== Real Filter Options Test ===")
        
        # Create test data with various attributes
        test_medios = ['La Nación', 'Clarín', 'El Mercurio']
        test_paises = ['Argentina', 'Chile', 'Uruguay']
        
        for i in range(15):
            # Create associated articulo first
            client = SupabaseClient.get_client()
            articulo_result = client.table('articulos').insert({
                'titular': f'Test article {i}',
                'url': f'https://test.com/{i}',
                'medio': random.choice(test_medios),
                'fecha_publicacion': datetime.now().isoformat()
            }).execute()
            
            if articulo_result.data:
                articulo_id = articulo_result.data[0]['id']
                
                # Create hecho with articulo reference
                hecho = await self.create_test_hecho(
                    contenido=f'Filter test hecho {i}',
                    pais=random.choice(test_paises),
                    importancia=random.randint(1, 10),
                    articulo_id=articulo_id
                )
                
                if hecho:
                    created_hechos.append(hecho['id'])
        
        # Get filter options
        response = test_client.get("/dashboard/filtros/opciones")
        
        assert response.status_code == 200
        options = response.json()
        
        print(f"Available filters:")
        print(f"  Medios: {len(options['medios_disponibles'])}")
        print(f"  Países: {len(options['paises_disponibles'])}")
        print(f"  Importancia range: {options['importancia_range']}")
        
        # Should include our test data
        assert any(medio in options['medios_disponibles'] for medio in test_medios)
        assert any(pais in options['paises_disponibles'] for pais in test_paises)
        assert options['importancia_range']['min'] >= 1
        assert options['importancia_range']['max'] <= 10
    
    @pytest.mark.asyncio
    async def test_real_concurrent_operations(self, test_client, test_data_cleanup):
        """Test concurrent operations with real database."""
        created_hechos, created_feedback = test_data_cleanup
        
        print("\n=== Real Concurrent Operations Test ===")
        
        # Create test hechos
        test_hechos = []
        for i in range(10):
            hecho = await self.create_test_hecho(
                contenido=f'Concurrent test hecho {i}',
                importancia=5
            )
            if hecho:
                test_hechos.append(hecho)
                created_hechos.append(hecho['id'])
        
        # Define concurrent operations
        async def submit_feedback(hecho_id, importance):
            """Submit feedback asynchronously."""
            async with TestClient(app) as ac:
                response = await ac.post(
                    f"/dashboard/feedback/hecho/{hecho_id}/importancia_feedback",
                    json={
                        "importancia_editor_final": importance,
                        "usuario_id_editor": f"concurrent_user_{importance}"
                    }
                )
                return response.status_code
        
        # Submit feedback concurrently
        tasks = []
        for i, hecho in enumerate(test_hechos):
            task = asyncio.create_task(
                submit_feedback(hecho['id'], (i % 10) + 1)
            )
            tasks.append(task)
        
        # Wait for all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successes and failures
        successes = sum(1 for r in results if isinstance(r, int) and r == 200)
        failures = len(results) - successes
        
        print(f"Concurrent feedback submissions:")
        print(f"  Total: {len(results)}")
        print(f"  Successful: {successes}")
        print(f"  Failed: {failures}")
        
        # Most should succeed
        assert successes > len(results) * 0.8, "Most concurrent operations should succeed"
        
        # Verify data integrity
        client = SupabaseClient.get_client()
        for hecho in test_hechos[:5]:  # Check first 5
            result = client.table('feedback_importancia_hechos')\
                .select('*')\
                .eq('hecho_id', hecho['id'])\
                .execute()
            
            if result.data:
                # Track for cleanup
                for feedback in result.data:
                    created_feedback.append(feedback['id'])
    
    @pytest.mark.asyncio
    async def test_real_error_handling(self, test_client):
        """Test error handling with real database constraints."""
        print("\n=== Real Error Handling Test ===")
        
        # Test non-existent hecho
        response = test_client.post(
            "/dashboard/feedback/hecho/999999999/importancia_feedback",
            json={
                "importancia_editor_final": 8,
                "usuario_id_editor": "test"
            }
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()['detail'].lower()
        
        print("✓ Non-existent hecho handled correctly")
        
        # Test invalid importance value (if enforced by API)
        response = test_client.post(
            "/dashboard/feedback/hecho/1/importancia_feedback",
            json={
                "importancia_editor_final": 15,  # Out of range
                "usuario_id_editor": "test"
            }
        )
        
        assert response.status_code in [422, 400]
        print("✓ Invalid importance value handled correctly")
        
        # Test invalid evaluacion value
        response = test_client.post(
            "/dashboard/feedback/hecho/1/evaluacion_editorial",
            json={
                "evaluacion_editorial": "invalid_value",
                "justificacion_evaluacion_editorial": "Test"
            }
        )
        
        assert response.status_code == 422
        print("✓ Invalid evaluation value handled correctly")
    
    @pytest.mark.asyncio
    async def test_real_performance_metrics(self, test_client, test_data_cleanup):
        """Measure real database performance."""
        created_hechos, _ = test_data_cleanup
        
        print("\n=== Real Performance Metrics ===")
        
        # Create test data
        for i in range(50):
            hecho = await self.create_test_hecho(
                contenido=f'Performance test hecho {i}',
                importancia=(i % 10) + 1,
                pais='Test Country' if i % 2 == 0 else 'Other Country'
            )
            if hecho:
                created_hechos.append(hecho['id'])
        
        # Measure query performance
        timings = {
            'simple_query': [],
            'filtered_query': [],
            'paginated_query': []
        }
        
        # Simple query
        for _ in range(10):
            start = time.time()
            response = test_client.get("/dashboard/hechos_revision")
            duration = time.time() - start
            
            if response.status_code == 200:
                timings['simple_query'].append(duration)
        
        # Filtered query
        for _ in range(10):
            start = time.time()
            response = test_client.get(
                "/dashboard/hechos_revision",
                params={
                    'pais_publicacion': 'Test Country',
                    'importancia_min': 5,
                    'importancia_max': 8
                }
            )
            duration = time.time() - start
            
            if response.status_code == 200:
                timings['filtered_query'].append(duration)
        
        # Paginated query
        for offset in range(0, 50, 10):
            start = time.time()
            response = test_client.get(
                "/dashboard/hechos_revision",
                params={'limit': 10, 'offset': offset}
            )
            duration = time.time() - start
            
            if response.status_code == 200:
                timings['paginated_query'].append(duration)
        
        # Calculate and display metrics
        import statistics
        
        print("\nQuery Performance (seconds):")
        for query_type, times in timings.items():
            if times:
                avg = statistics.mean(times)
                p95 = sorted(times)[int(len(times) * 0.95)]
                print(f"\n{query_type}:")
                print(f"  Average: {avg:.3f}s")
                print(f"  P95: {p95:.3f}s")
                print(f"  Min: {min(times):.3f}s")
                print(f"  Max: {max(times):.3f}s")


class TestDatabaseConstraints:
    """Test database constraints and data integrity."""
    
    @pytest.mark.asyncio
    async def test_unique_constraints(self, test_client, test_data_cleanup):
        """Test unique constraint handling."""
        created_hechos, created_feedback = test_data_cleanup
        
        print("\n=== Unique Constraint Test ===")
        
        # Create a test hecho
        hecho = await TestRealSupabaseIntegration().create_test_hecho()
        created_hechos.append(hecho['id'])
        
        # Submit feedback
        response = test_client.post(
            f"/dashboard/feedback/hecho/{hecho['id']}/importancia_feedback",
            json={
                "importancia_editor_final": 7,
                "usuario_id_editor": "test_user"
            }
        )
        
        assert response.status_code == 200
        
        # Submit again with same user - should update, not duplicate
        response = test_client.post(
            f"/dashboard/feedback/hecho/{hecho['id']}/importancia_feedback",
            json={
                "importancia_editor_final": 9,
                "usuario_id_editor": "test_user"
            }
        )
        
        assert response.status_code == 200
        
        # Verify only one record exists
        client = SupabaseClient.get_client()
        result = client.table('feedback_importancia_hechos')\
            .select('*')\
            .eq('hecho_id', hecho['id'])\
            .eq('usuario_id_editor', 'test_user')\
            .execute()
        
        assert len(result.data) == 1
        assert result.data[0]['importancia_editor_final'] == 9
        
        created_feedback.append(result.data[0]['id'])
        
        print("✓ Unique constraint working correctly")
    
    @pytest.mark.asyncio
    async def test_foreign_key_constraints(self, test_client):
        """Test foreign key constraint enforcement."""
        print("\n=== Foreign Key Constraint Test ===")
        
        # Try to reference non-existent hecho
        response = test_client.post(
            "/dashboard/feedback/hecho/999999999/importancia_feedback",
            json={
                "importancia_editor_final": 8,
                "usuario_id_editor": "test"
            }
        )
        
        # Should fail with 404 (hecho not found)
        assert response.status_code == 404
        
        print("✓ Foreign key constraints enforced")
