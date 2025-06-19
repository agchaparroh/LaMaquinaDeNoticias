"""
Unit tests for FeedbackService
Tests importance feedback submission with mocked Supabase operations
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import HTTPException

from services.feedback_service import FeedbackService
from services.supabase_client import SupabaseClient
from models.requests import ImportanciaFeedbackRequest, EvaluacionEditorialRequest


@pytest.fixture
def feedback_request():
    """Sample feedback request data."""
    return ImportanciaFeedbackRequest(
        importancia_editor_final=8,
        usuario_id_editor="editor123"
    )


@pytest.fixture
def evaluacion_request():
    """Sample editorial evaluation request data."""
    return EvaluacionEditorialRequest(
        evaluacion_editorial="verificado_ok_editorial",
        justificacion_evaluacion_editorial="Fact verified against multiple sources"
    )


@pytest.fixture
def mock_supabase_client():
    """Mock SupabaseClient for testing."""
    mock = Mock(spec=SupabaseClient)
    return mock


@pytest.fixture
def feedback_service():
    """Create FeedbackService instance for testing."""
    # Mock the SupabaseClient constructor
    with patch('services.feedback_service.SupabaseClient') as mock_client_class:
        mock_instance = Mock()
        mock_client_class.return_value = mock_instance
        service = FeedbackService()
        # Store the mock for test access
        service._mock_client = mock_instance
        return service


class TestFeedbackService:
    """Test suite for FeedbackService."""
    
    @pytest.mark.asyncio
    async def test_submit_importancia_feedback_hecho_exists_new_feedback(self, feedback_service, feedback_request):
        """Test submitting new importance feedback when hecho exists."""
        hecho_id = 123
        
        # Mock get_single_record to return existing hecho
        with patch.object(SupabaseClient, 'get_single_record', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"id": hecho_id, "contenido": "Test hecho"}
            
            # Mock execute_with_retry for checking existing feedback (returns empty)
            with patch.object(SupabaseClient, 'execute_with_retry', new_callable=AsyncMock) as mock_execute:
                # First call: check existing feedback (empty result)
                # Second call: insert new feedback
                mock_execute.side_effect = [
                    Mock(data=[]),  # No existing feedback
                    Mock(data=[{"id": 1}])  # Insert successful
                ]
                
                # Execute
                await feedback_service.submit_importancia_feedback(hecho_id, feedback_request)
        
        # Verify hecho existence was checked
        mock_get.assert_called_once_with(
            table_name="hechos",
            record_id=hecho_id
        )
        
        # Verify execute_with_retry was called twice
        assert mock_execute.call_count == 2
        
        # Verify insert operation was called (second call)
        insert_call = mock_execute.call_args_list[1]
        insert_operation = insert_call[0][0]
        
        # Call the insert operation to verify it's correct
        mock_client = Mock()
        mock_table = Mock()
        mock_insert = Mock()
        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        
        with patch.object(SupabaseClient, 'get_client', return_value=mock_client):
            insert_operation()
            
        # Verify correct table and data
        mock_client.table.assert_called_with('feedback_importancia_hechos')
        mock_table.insert.assert_called_with({
            'hecho_id': hecho_id,
            'usuario_id_editor': feedback_request.usuario_id_editor,
            'importancia_editor_final': feedback_request.importancia_editor_final
        })
    
    @pytest.mark.asyncio
    async def test_submit_importancia_feedback_hecho_not_found(self, feedback_service, feedback_request):
        """Test submitting feedback when hecho doesn't exist."""
        hecho_id = 999
        
        # Mock get_single_record to return None (hecho not found)
        with patch.object(SupabaseClient, 'get_single_record', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            
            # Should raise HTTPException with 404
            with pytest.raises(HTTPException) as exc_info:
                await feedback_service.submit_importancia_feedback(hecho_id, feedback_request)
            
            assert exc_info.value.status_code == 404
            assert f"Hecho with ID {hecho_id} not found" in str(exc_info.value.detail)
        
        # Verify hecho existence was checked
        mock_get.assert_called_once_with(
            table_name="hechos",
            record_id=hecho_id
        )
    
    @pytest.mark.asyncio
    async def test_submit_importancia_feedback_update_existing(self, feedback_service, feedback_request):
        """Test updating existing importance feedback."""
        hecho_id = 456
        existing_feedback_id = 789
        
        # Mock get_single_record to return existing hecho
        with patch.object(SupabaseClient, 'get_single_record', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"id": hecho_id, "contenido": "Test hecho"}
            
            # Mock execute_with_retry
            with patch.object(SupabaseClient, 'execute_with_retry', new_callable=AsyncMock) as mock_execute:
                # First call: check existing feedback (returns existing)
                # Second call: update feedback
                mock_execute.side_effect = [
                    Mock(data=[{"id": existing_feedback_id}]),  # Existing feedback found
                    Mock(data=[{"id": existing_feedback_id}])   # Update successful
                ]
                
                # Execute
                await feedback_service.submit_importancia_feedback(hecho_id, feedback_request)
        
        # Verify execute_with_retry was called twice
        assert mock_execute.call_count == 2
        
        # Verify update operation was called (second call)
        update_call = mock_execute.call_args_list[1]
        update_operation = update_call[0][0]
        
        # Call the update operation to verify it's correct
        mock_client = Mock()
        mock_table = Mock()
        mock_update = Mock()
        mock_eq = Mock()
        mock_client.table.return_value = mock_table
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq
        
        with patch.object(SupabaseClient, 'get_client', return_value=mock_client):
            update_operation()
            
        # Verify correct table and update data
        mock_client.table.assert_called_with('feedback_importancia_hechos')
        mock_table.update.assert_called_with({
            'importancia_editor_final': feedback_request.importancia_editor_final,
            'updated_at': 'now()'
        })
        mock_update.eq.assert_called_with('id', existing_feedback_id)
    
    @pytest.mark.asyncio
    async def test_submit_importancia_feedback_database_error(self, feedback_service, feedback_request):
        """Test handling database errors during feedback submission."""
        hecho_id = 123
        
        # Mock get_single_record to return existing hecho
        with patch.object(SupabaseClient, 'get_single_record', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"id": hecho_id, "contenido": "Test hecho"}
            
            # Mock execute_with_retry to raise database error
            with patch.object(SupabaseClient, 'execute_with_retry', new_callable=AsyncMock) as mock_execute:
                mock_execute.side_effect = Exception("Database connection error")
                
                # Should raise the exception
                with pytest.raises(Exception) as exc_info:
                    await feedback_service.submit_importancia_feedback(hecho_id, feedback_request)
                
                assert "Database connection error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_feedback_service_initialization(self):
        """Test FeedbackService initialization."""
        # Mock SupabaseClient
        with patch('services.feedback_service.SupabaseClient') as mock_client_class:
            mock_instance = Mock()
            mock_client_class.return_value = mock_instance
            
            # Create service
            service = FeedbackService()
            
            # Verify SupabaseClient was instantiated
            mock_client_class.assert_called_once()
            
            # Verify service has supabase_client attribute
            assert service.supabase_client == mock_instance
    
    @pytest.mark.asyncio
    async def test_submit_importancia_feedback_with_valid_importance_range(self, feedback_service):
        """Test feedback with importance values at boundaries (1 and 10)."""
        hecho_id = 123
        
        # Test minimum value (1)
        feedback_min = ImportanciaFeedbackRequest(
            importancia_editor_final=1,
            usuario_id_editor="editor123"
        )
        
        # Test maximum value (10)
        feedback_max = ImportanciaFeedbackRequest(
            importancia_editor_final=10,
            usuario_id_editor="editor123"
        )
        
        # Mock get_single_record
        with patch.object(SupabaseClient, 'get_single_record', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"id": hecho_id}
            
            # Mock execute_with_retry
            with patch.object(SupabaseClient, 'execute_with_retry', new_callable=AsyncMock) as mock_execute:
                mock_execute.return_value = Mock(data=[])
                
                # Test both min and max values
                await feedback_service.submit_importancia_feedback(hecho_id, feedback_min)
                await feedback_service.submit_importancia_feedback(hecho_id, feedback_max)
                
                # Both should succeed without errors
                assert mock_execute.call_count == 4  # 2 calls per submission
    
    @pytest.mark.asyncio
    async def test_submit_evaluacion_editorial_success(self, feedback_service, evaluacion_request):
        """Test successful editorial evaluation submission."""
        hecho_id = 123
        
        # Mock get_single_record to return existing hecho
        with patch.object(SupabaseClient, 'get_single_record', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"id": hecho_id, "contenido": "Test hecho"}
            
            # Mock execute_with_retry for update operation
            with patch.object(SupabaseClient, 'execute_with_retry', new_callable=AsyncMock) as mock_execute:
                mock_execute.return_value = Mock(data=[{"id": hecho_id}])
                
                # Execute
                await feedback_service.submit_evaluacion_editorial(hecho_id, evaluacion_request)
        
        # Verify hecho existence was checked
        mock_get.assert_called_once_with(
            table_name="hechos",
            record_id=hecho_id
        )
        
        # Verify execute_with_retry was called once for update
        assert mock_execute.call_count == 1
        
        # Verify update operation
        update_operation = mock_execute.call_args[0][0]
        
        # Call the update operation to verify it's correct
        mock_client = Mock()
        mock_table = Mock()
        mock_update = Mock()
        mock_eq = Mock()
        mock_client.table.return_value = mock_table
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq
        
        with patch.object(SupabaseClient, 'get_client', return_value=mock_client):
            update_operation()
            
        # Verify correct table and update data
        mock_client.table.assert_called_with('hechos')
        mock_table.update.assert_called_with({
            'evaluacion_editorial': evaluacion_request.evaluacion_editorial,
            'justificacion_evaluacion_editorial': evaluacion_request.justificacion_evaluacion_editorial,
            'updated_at': 'now()'
        })
        mock_update.eq.assert_called_with('id', hecho_id)
    
    @pytest.mark.asyncio
    async def test_submit_evaluacion_editorial_hecho_not_found(self, feedback_service, evaluacion_request):
        """Test editorial evaluation when hecho doesn't exist."""
        hecho_id = 999
        
        # Mock get_single_record to return None (hecho not found)
        with patch.object(SupabaseClient, 'get_single_record', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            
            # Should raise HTTPException with 404
            with pytest.raises(HTTPException) as exc_info:
                await feedback_service.submit_evaluacion_editorial(hecho_id, evaluacion_request)
            
            assert exc_info.value.status_code == 404
            assert f"Hecho with ID {hecho_id} not found" in str(exc_info.value.detail)
        
        # Verify hecho existence was checked
        mock_get.assert_called_once_with(
            table_name="hechos",
            record_id=hecho_id
        )
    
    @pytest.mark.asyncio
    async def test_submit_evaluacion_editorial_valid_enum_values(self, feedback_service):
        """Test editorial evaluation with both valid enum values."""
        hecho_id = 123
        
        # Test with 'verificado_ok_editorial'
        evaluacion_verified = EvaluacionEditorialRequest(
            evaluacion_editorial="verificado_ok_editorial",
            justificacion_evaluacion_editorial="Verified as correct"
        )
        
        # Test with 'declarado_falso_editorial'
        evaluacion_false = EvaluacionEditorialRequest(
            evaluacion_editorial="declarado_falso_editorial",
            justificacion_evaluacion_editorial="Declared as false"
        )
        
        # Mock get_single_record
        with patch.object(SupabaseClient, 'get_single_record', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"id": hecho_id}
            
            # Mock execute_with_retry
            with patch.object(SupabaseClient, 'execute_with_retry', new_callable=AsyncMock) as mock_execute:
                mock_execute.return_value = Mock(data=[{"id": hecho_id}])
                
                # Test both enum values
                await feedback_service.submit_evaluacion_editorial(hecho_id, evaluacion_verified)
                await feedback_service.submit_evaluacion_editorial(hecho_id, evaluacion_false)
                
                # Both should succeed
                assert mock_execute.call_count == 2
    
    @pytest.mark.asyncio
    async def test_submit_evaluacion_editorial_database_error(self, feedback_service, evaluacion_request):
        """Test handling database errors during editorial evaluation."""
        hecho_id = 123
        
        # Mock get_single_record to return existing hecho
        with patch.object(SupabaseClient, 'get_single_record', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"id": hecho_id}
            
            # Mock execute_with_retry to raise database error
            with patch.object(SupabaseClient, 'execute_with_retry', new_callable=AsyncMock) as mock_execute:
                mock_execute.side_effect = Exception("Database connection error")
                
                # Should raise the exception
                with pytest.raises(Exception) as exc_info:
                    await feedback_service.submit_evaluacion_editorial(hecho_id, evaluacion_request)
                
                assert "Database connection error" in str(exc_info.value)


class TestFeedbackServiceIntegration:
    """Integration tests for FeedbackService with full mock chain."""
    
    @pytest.mark.asyncio
    async def test_complete_feedback_flow_new_feedback(self, feedback_request):
        """Test complete flow for new feedback submission."""
        hecho_id = 100
        
        # Create a complete mock chain
        mock_client = Mock()
        mock_client.table = Mock()
        
        # Mock for hecho check
        mock_hechos_table = Mock()
        mock_hechos_select = Mock()
        mock_hechos_eq = Mock()
        mock_hechos_limit = Mock()
        mock_hechos_execute = Mock(return_value=Mock(data=[{"id": hecho_id}]))
        
        # Chain for hecho check
        mock_hechos_table.select = Mock(return_value=mock_hechos_select)
        mock_hechos_select.eq = Mock(return_value=mock_hechos_eq)
        mock_hechos_eq.limit = Mock(return_value=mock_hechos_limit)
        mock_hechos_limit.execute = mock_hechos_execute
        
        # Mock for feedback check
        mock_feedback_table = Mock()
        mock_feedback_select = Mock()
        mock_feedback_eq1 = Mock()
        mock_feedback_eq2 = Mock()
        mock_feedback_limit = Mock()
        mock_feedback_check_execute = Mock(return_value=Mock(data=[]))
        
        # Chain for feedback check
        mock_feedback_table.select = Mock(return_value=mock_feedback_select)
        mock_feedback_select.eq = Mock(return_value=mock_feedback_eq1)
        mock_feedback_eq1.eq = Mock(return_value=mock_feedback_eq2)
        mock_feedback_eq2.limit = Mock(return_value=mock_feedback_limit)
        mock_feedback_limit.execute = mock_feedback_check_execute
        
        # Mock for feedback insert
        mock_feedback_insert = Mock()
        mock_feedback_insert_execute = Mock(return_value=Mock(data=[{"id": 1}]))
        mock_feedback_table.insert = Mock(return_value=mock_feedback_insert)
        mock_feedback_insert.execute = mock_feedback_insert_execute
        
        # Setup table routing
        def table_router(table_name):
            if table_name == 'hechos':
                return mock_hechos_table
            elif table_name == 'feedback_importancia_hechos':
                return mock_feedback_table
            else:
                raise ValueError(f"Unexpected table: {table_name}")
        
        mock_client.table = Mock(side_effect=table_router)
        
        # Patch all necessary methods
        with patch.object(SupabaseClient, 'get_client', return_value=mock_client):
            with patch.object(SupabaseClient, 'get_single_record', new_callable=AsyncMock) as mock_get:
                mock_get.return_value = {"id": hecho_id}
                
                with patch.object(SupabaseClient, 'execute_with_retry', new_callable=AsyncMock) as mock_execute:
                    # Mock the operations passed to execute_with_retry
                    async def execute_operation(operation):
                        return operation()
                    
                    mock_execute.side_effect = execute_operation
                    
                    # Create service and execute
                    service = FeedbackService()
                    await service.submit_importancia_feedback(hecho_id, feedback_request)
        
        # Verify all operations were called correctly
        assert mock_get.call_count == 1
        assert mock_execute.call_count == 2  # Check existing + insert new
