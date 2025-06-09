"""
Test simple de integración para verificar el flujo básico
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from uuid import uuid4

from src.controller import PipelineController


class TestBasicIntegration:
    """Test básico para verificar que el controller funciona."""
    
    @pytest.mark.asyncio
    async def test_controller_initialization(self):
        """Test que el controller se inicializa correctamente."""
        controller = PipelineController()
        assert controller is not None
        assert controller.groq_service is None  # Se inicializa cuando se necesita
        assert controller.supabase_service is None  # Se inicializa cuando se necesita
        
        # Verificar métricas iniciales
        metrics = controller.get_metrics()
        assert metrics["articulos_procesados"] == 0
        assert metrics["fragmentos_procesados"] == 0
        assert metrics["errores_totales"] == 0
    
    @pytest.mark.asyncio
    async def test_process_article_missing_fields(self):
        """Test que verifica el manejo de campos faltantes."""
        controller = PipelineController()
        
        # Artículo con campos faltantes
        incomplete_article = {
            "medio": "Test News",
            "titular": "Test"
            # Faltan campos requeridos
        }
        
        with pytest.raises(ValueError) as exc_info:
            await controller.process_article(incomplete_article)
        
        assert "Campo requerido" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_fragment_validation(self):
        """Test de validación de fragmento con modelo Pydantic."""
        from src.models.entrada import FragmentoProcesableItem
        
        # Fragmento válido
        valid_fragment = {
            "id_fragmento": "test_123",
            "texto_original": "Texto de prueba",
            "id_articulo_fuente": "article_456",
            "orden_en_articulo": 0,
            "metadata_adicional": {}
        }
        
        # Debe crear el modelo sin errores
        fragment = FragmentoProcesableItem(**valid_fragment)
        assert fragment.id_fragmento == "test_123"
        assert fragment.texto_original == "Texto de prueba"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
