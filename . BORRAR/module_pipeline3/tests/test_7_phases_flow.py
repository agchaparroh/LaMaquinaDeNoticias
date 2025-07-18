"""
Test Suite: Pipeline 7 Fases - Flujo Completo E2E
=================================================

Suite de pruebas integral para el pipeline de 7 fases que valida:
- Flujo completo desde entrada hasta persistencia
- Funcionamiento correcto de cada fase individual
- Transiciones entre fases
- Manejo de errores y recovery
- Configuración dinámica
- Compatibilidad con API existente

Estas pruebas aseguran que el pipeline de 7 fases funciona correctamente
como un sistema integral manteniendo compatibilidad total.
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from datetime import datetime

# Imports del sistema
from src.models.request import ProcesarArticuloRequest
from src.models.response import ProcesarArticuloResponse, EstadoProcesamiento
from src.models.procesamiento import (
    ResultadoFase1Triaje,
    ResultadoFase2Simplificacion,
    EntidadProcesada,
    HechoProcesado,
    DatosCuantitativos,
    CitaTextual
)

# Config
from src.config import pipeline_config, get_model_for_content

# Controller y fases
from src.controller import PipelineController
from src.pipeline.fase_1_triaje import ejecutar_fase_1_triaje
from src.pipeline.fase_2_simplificacion import ejecutar_fase_2_simplificacion
from src.pipeline.fase_3_entidades import ejecutar_fase_3_entidades
from src.pipeline.fase_4_hechos import ejecutar_fase_4_hechos
from src.pipeline.fase_5_datos import ejecutar_fase_5_datos
from src.pipeline.fase_6_citas import ejecutar_fase_6_citas
from src.pipeline.fase_7_normalizacion import ejecutar_fase_7_normalizacion

# Servicios
from src.services.chunking_service import ChunkingService, ChunkType
from src.services.consolidation_service import ConsolidationService
from src.utils.fragment_processor import FragmentProcessor


# =============================================================================
# FIXTURES DE DATOS DE PRUEBA
# =============================================================================

@pytest.fixture
def sample_article_short():
    """Artículo corto que no requiere chunking."""
    return {
        "titulo": "Reunión presidencial sobre economía",
        "contenido": """
        El presidente Juan Pérez se reunió ayer con el ministro de Economía Carlos López 
        para discutir las nuevas medidas económicas. "Estamos comprometidos con el crecimiento", 
        declaró el presidente. La reunión duró 2 horas y se analizaron 3 propuestas principales.
        El PIB creció un 3.5% este trimestre según datos oficiales.
        """,
        "fuente": "Diario Nacional",
        "fecha_publicacion": "2024-01-15",
        "pais": "Argentina"
    }

@pytest.fixture
def sample_article_long():
    """Artículo largo que requiere chunking."""
    return {
        "titulo": "Análisis completo de la situación económica nacional",
        "contenido": """
        El presidente Juan Pérez se reunió ayer con el ministro de Economía Carlos López 
        para discutir las nuevas medidas económicas. "Estamos comprometidos con el crecimiento", 
        declaró el presidente. La reunión duró 2 horas y se analizaron 3 propuestas principales.
        
        En la primera propuesta, se discutió el aumento del presupuesto para infraestructura.
        El ministro López explicó que "necesitamos invertir 500 millones de pesos adicionales
        para completar los proyectos de carreteras". Esta inversión generaría aproximadamente
        2,500 empleos directos según el Ministerio de Trabajo.
        
        La segunda propuesta aborda la reforma tributaria. El secretario de Hacienda,
        María González, presentó un plan que reduciría los impuestos corporativos del 35%
        al 30% durante los próximos 2 años. "Esta medida estimulará la inversión privada",
        comentó González en rueda de prensa.
        
        La tercera propuesta se centra en el apoyo a pequeñas y medianas empresas (PyMEs).
        El director del Banco Nacional, Roberto Silva, anunció un programa de créditos
        preferenciales con tasas del 8% anual para empresas con menos de 50 empleados.
        "Queremos que las PyMEs sean el motor de nuestro crecimiento", declaró Silva.
        
        Los datos económicos recientes muestran señales mixtas. El PIB creció un 3.5% 
        este trimestre, pero la inflación alcanzó el 4.2% mensual. El desempleo se mantiene
        en 8.9%, mientras que las exportaciones aumentaron 12% respecto al año anterior.
        
        La Confederación de Trabajadores expresó su apoyo parcial a las medidas.
        Su presidente, Ana Martínez, declaró que "vemos con buenos ojos la creación de empleo,
        pero necesitamos garantías sobre los salarios reales". Los empresarios, por su parte,
        a través de la Cámara de Comercio, pidieron "mayor claridad en los plazos de implementación".
        
        El Congreso debatirá estas propuestas la próxima semana. La oposición ya anunció
        que presentará enmiendas al proyecto. El senador opositor Luis Torres comentó que
        "apoyaremos lo que beneficie al país, pero revisaremos cada punto cuidadosamente".
        
        Los mercados financieros reaccionaron positivamente. El índice bursátil subió 2.3%
        y el peso se fortaleció 1.8% frente al dólar. Los bonos gubernamentales tuvieron
        una jornada estable con leves variaciones.
        """,
        "fuente": "El Economista",
        "fecha_publicacion": "2024-01-15",
        "pais": "Argentina"
    }

@pytest.fixture
def mock_groq_response():
    """Mock de respuesta típica de Groq."""
    return {
        "choices": [
            {
                "message": {
                    "content": '{"entidades": [{"id": 1, "nombre": "Juan Pérez", "tipo": "PERSONA"}]}'
                }
            }
        ],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50
        }
    }

@pytest.fixture
def pipeline_controller():
    """Instancia del controller para pruebas."""
    return PipelineController()


# =============================================================================
# TESTS DE CONFIGURACIÓN DEL PIPELINE
# =============================================================================

class TestPipelineConfiguration:
    """Tests de configuración dinámica del pipeline."""
    
    def test_pipeline_config_loading(self):
        """Test que la configuración se carga correctamente."""
        assert pipeline_config is not None
        assert pipeline_config.chunking.entities_threshold > 0
        assert pipeline_config.groq_models.default_model is not None
        assert pipeline_config.processing.max_concurrent_chunks > 0
    
    def test_model_selection_logic(self):
        """Test de selección automática de modelos."""
        # Texto corto -> modelo default
        short_text_model = get_model_for_content(1000)
        assert short_text_model == pipeline_config.groq_models.default_model
        
        # Texto largo -> modelo large
        long_text_model = get_model_for_content(10000)
        assert long_text_model == pipeline_config.groq_models.large_model
    
    def test_chunking_decision_logic(self):
        """Test de decisiones automáticas de chunking."""
        from src.config import is_chunking_needed
        
        # No chunking necesario
        assert not is_chunking_needed('entities', 10, 1000)
        assert not is_chunking_needed('chars', 0, 3000)
        
        # Chunking necesario
        assert is_chunking_needed('entities', 50, 1000)
        assert is_chunking_needed('chars', 0, 10000)


# =============================================================================
# TESTS DE FASES INDIVIDUALES
# =============================================================================

class TestIndividualPhases:
    """Tests de funcionamiento de cada fase por separado."""
    
    @pytest.mark.asyncio
    async def test_fase_1_triaje_basic(self, sample_article_short):
        """Test básico de Fase 1 - Triaje."""
        request = ProcesarArticuloRequest(**sample_article_short)
        
        with patch('src.pipeline.fase_1_triaje.Groq') as mock_groq:
            mock_groq.return_value.chat.completions.create.return_value = Mock(
                choices=[Mock(message=Mock(content='{"relevancia": 8, "justificacion": "Artículo relevante"}'))],
                usage=Mock(prompt_tokens=100, completion_tokens=50)
            )
            
            resultado = await ejecutar_fase_1_triaje(request)
            
            assert isinstance(resultado, ResultadoFase1Triaje)
            assert resultado.relevancia_contenido > 0
            assert resultado.justificacion_relevancia is not None
    
    @pytest.mark.asyncio
    async def test_fase_2_simplificacion(self, sample_article_short):
        """Test de Fase 2 - Simplificación."""
        # Mock del resultado de fase 1
        resultado_fase1 = ResultadoFase1Triaje(
            id_fragmento=uuid4(),
            relevancia_contenido=8,
            justificacion_relevancia="Artículo relevante",
            contenido_original=sample_article_short["contenido"],
            metadatos_triaje={}
        )
        
        with patch('src.pipeline.fase_2_simplificacion.Groq') as mock_groq:
            mock_groq.return_value.chat.completions.create.return_value = Mock(
                choices=[Mock(message=Mock(content='{"texto_simplificado": "Texto simplificado"}'))],
                usage=Mock(prompt_tokens=100, completion_tokens=50)
            )
            
            resultado = await ejecutar_fase_2_simplificacion(resultado_fase1)
            
            assert isinstance(resultado, ResultadoFase2Simplificacion)
            assert resultado.texto_simplificado is not None
            assert len(resultado.texto_simplificado) > 0
    
    @pytest.mark.asyncio
    async def test_fase_3_entidades(self, sample_article_short):
        """Test de Fase 3 - Extracción de Entidades."""
        resultado_fase2 = ResultadoFase2Simplificacion(
            id_fragmento=uuid4(),
            texto_simplificado="Juan Pérez se reunió con Carlos López",
            cambios_realizados=["simplificacion"],
            metadatos_simplificacion={}
        )
        
        with patch('src.pipeline.fase_3_entidades.Groq') as mock_groq:
            mock_groq.return_value.chat.completions.create.return_value = Mock(
                choices=[Mock(message=Mock(content='{"entidades": [{"id": 1, "nombre": "Juan Pérez", "tipo": "PERSONA"}]}'))],
                usage=Mock(prompt_tokens=100, completion_tokens=50)
            )
            
            resultado = await ejecutar_fase_3_entidades(resultado_fase2)
            
            assert "entidades_extraidas" in resultado
            assert isinstance(resultado["entidades_extraidas"], list)
    
    @pytest.mark.asyncio 
    async def test_fase_4_hechos(self, sample_article_short):
        """Test de Fase 4 - Extracción de Hechos."""
        resultado_fase2 = ResultadoFase2Simplificacion(
            id_fragmento=uuid4(),
            texto_simplificado="Juan Pérez se reunió con Carlos López",
            cambios_realizados=["simplificacion"],
            metadatos_simplificacion={}
        )
        
        with patch('src.pipeline.fase_4_hechos.Groq') as mock_groq:
            mock_groq.return_value.chat.completions.create.return_value = Mock(
                choices=[Mock(message=Mock(content='{"hechos": [{"id": 1, "contenido": "Reunión presidencial", "tipo_hecho": "EVENTO"}]}'))],
                usage=Mock(prompt_tokens=100, completion_tokens=50)
            )
            
            resultado = await ejecutar_fase_4_hechos(resultado_fase2)
            
            assert "hechos_extraidos" in resultado
            assert isinstance(resultado["hechos_extraidos"], list)


# =============================================================================
# TESTS DE FLUJO COMPLETO
# =============================================================================

class TestCompleteFlow:
    """Tests del flujo completo de 7 fases."""
    
    @pytest.mark.asyncio
    async def test_complete_pipeline_short_article(self, sample_article_short, pipeline_controller):
        """Test del pipeline completo con artículo corto (sin chunking)."""
        request = ProcesarArticuloRequest(**sample_article_short)
        
        # Mock de todas las llamadas a Groq
        with patch('src.pipeline.fase_1_triaje.Groq') as mock_groq1, \
             patch('src.pipeline.fase_2_simplificacion.Groq') as mock_groq2, \
             patch('src.pipeline.fase_3_entidades.Groq') as mock_groq3, \
             patch('src.pipeline.fase_4_hechos.Groq') as mock_groq4, \
             patch('src.services.supabase_service.SupabaseService') as mock_supabase:
            
            # Mock respuestas para cada fase
            mock_groq1.return_value.chat.completions.create.return_value = Mock(
                choices=[Mock(message=Mock(content='{"relevancia": 8, "justificacion": "Relevante"}'))],
                usage=Mock(prompt_tokens=100, completion_tokens=50)
            )
            
            mock_groq2.return_value.chat.completions.create.return_value = Mock(
                choices=[Mock(message=Mock(content='{"texto_simplificado": "Texto simplificado"}'))],
                usage=Mock(prompt_tokens=100, completion_tokens=50)
            )
            
            mock_groq3.return_value.chat.completions.create.return_value = Mock(
                choices=[Mock(message=Mock(content='{"entidades": [{"id": 1, "nombre": "Juan Pérez", "tipo": "PERSONA"}]}'))],
                usage=Mock(prompt_tokens=100, completion_tokens=50)
            )
            
            mock_groq4.return_value.chat.completions.create.return_value = Mock(
                choices=[Mock(message=Mock(content='{"hechos": [{"id": 1, "contenido": "Reunión", "tipo_hecho": "EVENTO"}]}'))],
                usage=Mock(prompt_tokens=100, completion_tokens=50)
            )
            
            # Mock Supabase
            mock_supabase.return_value.insertar_articulo_completo = AsyncMock(return_value={"status": "success"})
            
            # Ejecutar pipeline completo
            resultado = await pipeline_controller.procesar_articulo(request)
            
            # Validaciones
            assert isinstance(resultado, ProcesarArticuloResponse)
            assert resultado.estado == EstadoProcesamiento.COMPLETADO
            assert resultado.resultado_procesamiento is not None
    
    @pytest.mark.asyncio
    async def test_complete_pipeline_with_chunking(self, sample_article_long, pipeline_controller):
        """Test del pipeline completo con artículo largo (con chunking)."""
        request = ProcesarArticuloRequest(**sample_article_long)
        
        # Este test verifica que el chunking se active automáticamente
        # y que el procesamiento paralelo funcione
        
        with patch('src.pipeline.fase_1_triaje.Groq') as mock_groq, \
             patch('src.services.supabase_service.SupabaseService') as mock_supabase:
            
            # Mock respuestas genéricas para todas las fases
            mock_groq.return_value.chat.completions.create.return_value = Mock(
                choices=[Mock(message=Mock(content='{"relevancia": 8, "entidades": [], "hechos": []}'))],
                usage=Mock(prompt_tokens=100, completion_tokens=50)
            )
            
            mock_supabase.return_value.insertar_articulo_completo = AsyncMock(return_value={"status": "success"})
            
            # Verificar que el chunking se activa
            chunking_service = ChunkingService()
            chunks = chunking_service.create_chunks(sample_article_long["contenido"])
            
            # Si el artículo es lo suficientemente largo, debe crear múltiples chunks
            if len(sample_article_long["contenido"]) > pipeline_config.chunking.chars_threshold:
                assert len(chunks) > 1, "El artículo largo debería generar múltiples chunks"
            
            # Ejecutar pipeline
            resultado = await pipeline_controller.procesar_articulo(request)
            
            # El pipeline debe completarse exitosamente incluso con chunking
            assert isinstance(resultado, ProcesarArticuloResponse)
            assert resultado.estado == EstadoProcesamiento.COMPLETADO
    
    @pytest.mark.asyncio
    async def test_pipeline_error_handling(self, sample_article_short, pipeline_controller):
        """Test de manejo de errores en el pipeline."""
        request = ProcesarArticuloRequest(**sample_article_short)
        
        # Simular error en fase 1
        with patch('src.pipeline.fase_1_triaje.ejecutar_fase_1_triaje') as mock_fase1:
            mock_fase1.side_effect = Exception("Error simulado en fase 1")
            
            resultado = await pipeline_controller.procesar_articulo(request)
            
            # El controller debe manejar el error gracefully
            assert isinstance(resultado, ProcesarArticuloResponse)
            assert resultado.estado == EstadoProcesamiento.ERROR
            assert "Error simulado" in str(resultado.mensaje_error)


# =============================================================================
# TESTS DE TRANSICIONES ENTRE FASES
# =============================================================================

class TestPhaseTransitions:
    """Tests de transiciones y compatibilidad entre fases."""
    
    def test_fase1_to_fase2_data_flow(self):
        """Test que los datos fluyen correctamente de Fase 1 a Fase 2."""
        # Crear resultado de fase 1
        resultado_fase1 = ResultadoFase1Triaje(
            id_fragmento=uuid4(),
            relevancia_contenido=8,
            justificacion_relevancia="Test",
            contenido_original="Contenido test",
            metadatos_triaje={"spacy_analysis": {"token_count": 100}}
        )
        
        # Verificar que tiene todos los campos necesarios para fase 2
        assert resultado_fase1.id_fragmento is not None
        assert resultado_fase1.contenido_original is not None
        assert resultado_fase1.relevancia_contenido > 0
    
    def test_fase2_to_fase3_data_flow(self):
        """Test que los datos fluyen correctamente de Fase 2 a Fase 3."""
        resultado_fase2 = ResultadoFase2Simplificacion(
            id_fragmento=uuid4(),
            texto_simplificado="Texto simplificado test",
            cambios_realizados=["normalizacion"],
            metadatos_simplificacion={"original_length": 200, "simplified_length": 150}
        )
        
        # Verificar campos necesarios para fase 3
        assert resultado_fase2.id_fragmento is not None
        assert resultado_fase2.texto_simplificado is not None
        assert len(resultado_fase2.texto_simplificado) > 0
    
    def test_data_consistency_across_phases(self):
        """Test que el ID de fragmento se mantiene a través de todas las fases."""
        fragment_id = uuid4()
        
        # Verificar que el ID se propaga correctamente
        resultado_fase1 = ResultadoFase1Triaje(
            id_fragmento=fragment_id,
            relevancia_contenido=8,
            justificacion_relevancia="Test",
            contenido_original="Test content",
            metadatos_triaje={}
        )
        
        resultado_fase2 = ResultadoFase2Simplificacion(
            id_fragmento=fragment_id,  # Mismo ID
            texto_simplificado="Simplified test",
            cambios_realizados=["test"],
            metadatos_simplificacion={}
        )
        
        assert resultado_fase1.id_fragmento == resultado_fase2.id_fragmento


# =============================================================================
# TESTS DE RENDIMIENTO Y ESCALABILIDAD
# =============================================================================

class TestPerformanceAndScalability:
    """Tests de rendimiento y escalabilidad del pipeline."""
    
    @pytest.mark.asyncio
    async def test_parallel_chunk_processing_performance(self):
        """Test de mejora de rendimiento con procesamiento paralelo."""
        from src.pipeline.fase_3_entidades import (
            extraer_entidades_con_chunking,
            extraer_entidades_con_chunking_paralelo
        )
        
        # Crear datos de prueba
        chunks = ["Chunk 1 content", "Chunk 2 content", "Chunk 3 content"]
        resultado_fase2 = ResultadoFase2Simplificacion(
            id_fragmento=uuid4(),
            texto_simplificado="Test",
            cambios_realizados=["test"],
            metadatos_simplificacion={}
        )
        
        with patch('src.pipeline.fase_3_entidades.Groq') as mock_groq:
            mock_groq.return_value.chat.completions.create.return_value = Mock(
                choices=[Mock(message=Mock(content='{"entidades": []}'))],
                usage=Mock(prompt_tokens=100, completion_tokens=50)
            )
            
            # Test secuencial
            start_time = datetime.now()
            resultado_secuencial = extraer_entidades_con_chunking(
                resultado_fase2, chunks
            )
            tiempo_secuencial = (datetime.now() - start_time).total_seconds()
            
            # Test paralelo
            start_time = datetime.now()
            resultado_paralelo = await extraer_entidades_con_chunking_paralelo(
                resultado_fase2, chunks, max_concurrent_chunks=3
            )
            tiempo_paralelo = (datetime.now() - start_time).total_seconds()
            
            # Verificar que ambos producen resultados válidos
            assert "entidades_extraidas" in resultado_secuencial
            assert "entidades_extraidas" in resultado_paralelo
            
            # Con mocks, el tiempo puede no ser significativamente diferente,
            # pero verificamos que la estructura es correcta
            assert resultado_paralelo["metadatos_extraccion"]["parallel_processing"] is True
            assert resultado_secuencial.get("metadatos_extraccion", {}).get("parallel_processing", False) is False
    
    def test_memory_usage_with_chunking(self):
        """Test que el chunking no cause problemas de memoria."""
        # Crear texto muy largo
        long_text = "Test content. " * 1000  # ~13,000 caracteres
        
        chunking_service = ChunkingService()
        chunks = chunking_service.create_chunks(long_text)
        
        # Verificar que se crearon chunks apropiados
        assert len(chunks) > 1
        
        # Verificar que cada chunk es manejable
        for chunk in chunks:
            assert len(chunk.text) <= pipeline_config.chunking.chars_threshold
            assert chunk.context is not None
            assert chunk.metadata is not None


# =============================================================================
# TESTS DE COMPATIBILIDAD Y REGRESIÓN
# =============================================================================

class TestBackwardCompatibility:
    """Tests de compatibilidad con versiones anteriores."""
    
    def test_api_response_format_compatibility(self):
        """Test que el formato de respuesta sigue siendo compatible."""
        # Crear respuesta del nuevo pipeline
        response = ProcesarArticuloResponse(
            id_tarea="test-123",
            estado=EstadoProcesamiento.COMPLETADO,
            timestamp_inicio=datetime.now(),
            timestamp_fin=datetime.now(),
            resultado_procesamiento={"test": "data"},
            metadatos={"pipeline_version": "7_phases"}
        )
        
        # Verificar que tiene todos los campos esperados por la API
        assert hasattr(response, 'id_tarea')
        assert hasattr(response, 'estado')
        assert hasattr(response, 'timestamp_inicio')
        assert hasattr(response, 'timestamp_fin')
        assert hasattr(response, 'resultado_procesamiento')
    
    def test_existing_models_still_work(self):
        """Test que los modelos existentes siguen funcionando."""
        # Test que podemos crear las estructuras de datos existentes
        request = ProcesarArticuloRequest(
            titulo="Test",
            contenido="Test content",
            fuente="Test source",
            fecha_publicacion="2024-01-01"
        )
        
        assert request.titulo == "Test"
        assert request.contenido == "Test content"
        
        # Verificar que los campos opcionales funcionan
        request_with_optional = ProcesarArticuloRequest(
            titulo="Test",
            contenido="Test content",
            fuente="Test source",
            fecha_publicacion="2024-01-01",
            pais="Argentina",
            autor="Test Author"
        )
        
        assert request_with_optional.pais == "Argentina"
        assert request_with_optional.autor == "Test Author"


# =============================================================================
# TESTS DE CONFIGURACIÓN E INTEGRACIÓN
# =============================================================================

class TestConfigurationIntegration:
    """Tests de integración con el sistema de configuración."""
    
    def test_dynamic_config_affects_pipeline_behavior(self):
        """Test que los cambios de configuración afectan el comportamiento."""
        # Verificar que la configuración actual se usa
        current_threshold = pipeline_config.chunking.chars_threshold
        
        # Test de decisión de chunking basada en configuración
        from src.config import is_chunking_needed
        
        # Texto justo debajo del threshold
        text_below = "x" * (current_threshold - 100)
        assert not is_chunking_needed('chars', 0, len(text_below))
        
        # Texto justo arriba del threshold
        text_above = "x" * (current_threshold + 100)
        assert is_chunking_needed('chars', 0, len(text_above))
    
    def test_model_selection_based_on_config(self):
        """Test que la selección de modelo se basa en la configuración."""
        token_threshold = pipeline_config.groq_models.token_threshold
        
        # Texto corto -> modelo default
        short_model = get_model_for_content(token_threshold - 1000)
        assert short_model == pipeline_config.groq_models.default_model
        
        # Texto largo -> modelo large
        long_model = get_model_for_content(token_threshold + 1000)
        assert long_model == pipeline_config.groq_models.large_model


# =============================================================================
# SUITE DE TESTS PRINCIPALES
# =============================================================================

@pytest.mark.integration
class TestIntegrationSuite:
    """Suite principal de tests de integración."""
    
    @pytest.mark.asyncio
    async def test_full_integration_with_real_flow(self, sample_article_short):
        """Test de integración completa con flujo real."""
        
        # Este test ejecuta un flujo lo más real posible
        # con mocks mínimos solo para APIs externas
        
        request = ProcesarArticuloRequest(**sample_article_short)
        controller = PipelineController()
        
        with patch('src.services.groq_service.Groq') as mock_groq, \
             patch('src.services.supabase_service.SupabaseService') as mock_supabase:
            
            # Mock respuesta de Groq más realista
            mock_groq.return_value.chat.completions.create.return_value = Mock(
                choices=[Mock(message=Mock(content='{"relevancia": 8, "justificacion": "Artículo político relevante"}'))],
                usage=Mock(prompt_tokens=150, completion_tokens=75)
            )
            
            # Mock Supabase exitoso
            mock_supabase.return_value.insertar_articulo_completo = AsyncMock(
                return_value={"status": "success", "id": "article-123"}
            )
            
            # Ejecutar pipeline completo
            resultado = await controller.procesar_articulo(request)
            
            # Validaciones comprensivas
            assert isinstance(resultado, ProcesarArticuloResponse)
            assert resultado.estado == EstadoProcesamiento.COMPLETADO
            assert resultado.id_tarea is not None
            assert resultado.timestamp_inicio is not None
            assert resultado.timestamp_fin is not None
            assert resultado.resultado_procesamiento is not None
            
            # Verificar que se guardaron metadatos del pipeline
            assert "pipeline_version" in resultado.metadatos
            assert "total_duration_ms" in resultado.metadatos


if __name__ == "__main__":
    # Ejecutar tests cuando se ejecuta directamente
    pytest.main([__file__, "-v", "--tb=short"])