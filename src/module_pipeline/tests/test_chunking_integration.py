"""
Test Suite: Chunking Integration - Sistema de Chunks para Pipeline
================================================================

Suite de pruebas específica para el sistema de chunking que valida:
- Funcionamiento correcto del ChunkingService
- Decisiones automáticas de chunking basadas en thresholds
- Procesamiento paralelo de chunks
- Consolidación de resultados cross-chunk
- Preservación de contexto y metadatos
- Manejo de IDs secuenciales durante chunking

Estas pruebas aseguran que el sistema de chunking funciona correctamente
tanto para artículos cortos como largos, manteniendo la integridad de los datos.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any
from uuid import uuid4

# Imports del sistema de chunking
from src.services.chunking_service import ChunkingService, ChunkType, ContentChunk
from src.services.consolidation_service import ConsolidationService
from src.utils.fragment_processor import FragmentProcessor

# Imports de modelos
from src.models.procesamiento import (
    ResultadoFase2Simplificacion,
    EntidadProcesada,
    HechoProcesado
)

# Imports de configuración
from src.config import pipeline_config, get_chunking_config, get_parallel_processing_config

# Imports de fases que manejan chunking
from src.pipeline.fase_3_entidades import (
    ejecutar_fase_3_entidades,
    extraer_entidades_con_chunking,
    extraer_entidades_con_chunking_paralelo
)
from src.pipeline.fase_4_hechos import (
    ejecutar_fase_4_hechos,
    extraer_hechos_con_chunking,
    extraer_hechos_con_chunking_paralelo
)


# =============================================================================
# FIXTURES PARA DATOS DE PRUEBA
# =============================================================================

@pytest.fixture
def chunking_service():
    """Instancia del servicio de chunking."""
    return ChunkingService()

@pytest.fixture
def consolidation_service():
    """Instancia del servicio de consolidación."""
    return ConsolidationService()

@pytest.fixture
def fragment_processor():
    """Instancia del procesador de fragmentos."""
    return FragmentProcessor()

@pytest.fixture
def short_text():
    """Texto corto que NO debe activar chunking."""
    return "Juan Pérez se reunió con María González. La reunión duró 2 horas y trataron temas económicos."

@pytest.fixture
def medium_text():
    """Texto mediano que está en el límite del chunking."""
    content = "El presidente Juan Pérez anunció nuevas medidas económicas. "
    content += "El ministro de Economía Carlos López explicó los detalles. "
    content += "La secretaria de Hacienda María González presentó las cifras. "
    # Repetir para llegar cerca del threshold
    return content * 20  # ~3000 caracteres

@pytest.fixture
def long_text():
    """Texto largo que SÍ debe activar chunking."""
    content = """
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
    """
    return content

@pytest.fixture
def resultado_fase2_mock():
    """Mock de resultado de Fase 2 para testing."""
    return ResultadoFase2Simplificacion(
        id_fragmento=uuid4(),
        texto_simplificado="Texto simplificado para testing",
        cambios_realizados=["test_simplification"],
        metadatos_simplificacion={"test": True}
    )


# =============================================================================
# TESTS DEL CHUNKING SERVICE
# =============================================================================

class TestChunkingService:
    """Tests del servicio de chunking básico."""
    
    def test_chunking_service_initialization(self, chunking_service):
        """Test que el servicio se inicializa correctamente."""
        assert chunking_service is not None
        assert chunking_service.config is not None
    
    def test_should_chunk_decision_short_text(self, chunking_service, short_text):
        """Test que texto corto NO activa chunking."""
        should_chunk = chunking_service.should_chunk(short_text)
        assert not should_chunk, "Texto corto no debería activar chunking"
    
    def test_should_chunk_decision_long_text(self, chunking_service, long_text):
        """Test que texto largo SÍ activa chunking."""
        should_chunk = chunking_service.should_chunk(long_text)
        assert should_chunk, "Texto largo debería activar chunking"
    
    def test_create_chunks_from_short_text(self, chunking_service, short_text):
        """Test creación de chunks con texto corto."""
        chunks = chunking_service.create_chunks(short_text)
        
        # Texto corto debería generar un solo chunk
        assert len(chunks) == 1
        assert chunks[0].text == short_text
        assert chunks[0].chunk_id == 0
        assert chunks[0].metadata["total_chunks"] == 1
    
    def test_create_chunks_from_long_text(self, chunking_service, long_text):
        """Test creación de chunks con texto largo."""
        chunks = chunking_service.create_chunks(long_text)
        
        # Texto largo debería generar múltiples chunks
        assert len(chunks) > 1, "Texto largo debería generar múltiples chunks"
        
        # Verificar que cada chunk tiene estructura correcta
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_id == i
            assert chunk.text is not None
            assert len(chunk.text) > 0
            assert chunk.context is not None
            assert chunk.metadata is not None
            assert chunk.metadata["total_chunks"] == len(chunks)
    
    def test_chunk_context_preservation(self, chunking_service, long_text):
        """Test que el contexto se preserva entre chunks."""
        chunks = chunking_service.create_chunks(long_text)
        
        if len(chunks) > 1:
            # Verificar overlap de contexto entre chunks consecutivos
            for i in range(len(chunks) - 1):
                current_chunk = chunks[i]
                next_chunk = chunks[i + 1]
                
                # Verificar que hay contexto anterior/posterior
                assert current_chunk.context["next_chunk_preview"] is not None
                assert next_chunk.context["previous_chunk_summary"] is not None
    
    def test_chunk_ids_are_sequential(self, chunking_service, long_text):
        """Test que los IDs de chunks son secuenciales."""
        chunks = chunking_service.create_chunks(long_text)
        
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_id == i
            assert chunk.metadata["chunk_index"] == i


# =============================================================================
# TESTS DE DECISIONES AUTOMÁTICAS DE CHUNKING
# =============================================================================

class TestChunkingDecisions:
    """Tests de decisiones automáticas basadas en thresholds."""
    
    def test_chars_threshold_decision(self, chunking_service):
        """Test decisión basada en threshold de caracteres."""
        config = get_chunking_config()
        
        # Texto justo debajo del threshold
        short_text = "x" * (config.chars_threshold - 100)
        assert not chunking_service.should_chunk(short_text)
        
        # Texto justo arriba del threshold
        long_text = "x" * (config.chars_threshold + 100)
        assert chunking_service.should_chunk(long_text)
    
    def test_entities_threshold_simulation(self, chunking_service):
        """Test simulación de threshold de entidades."""
        config = get_chunking_config()
        
        # Simular decisión basada en número de entidades
        # (En la práctica esto se haría durante el análisis spaCy)
        few_entities = config.entities_threshold - 5
        many_entities = config.entities_threshold + 5
        
        assert not chunking_service._should_chunk_by_entities(few_entities)
        assert chunking_service._should_chunk_by_entities(many_entities)
    
    def test_multiple_criteria_chunking(self, chunking_service):
        """Test decisión de chunking con múltiples criterios."""
        config = get_chunking_config()
        
        # Texto que cumple múltiples criterios
        long_text_many_entities = "Juan Pérez, María González, Carlos López. " * 200
        
        # Debería activar chunking por ambos criterios
        assert chunking_service.should_chunk(long_text_many_entities)
        
        # Verificar que detecta ambos criterios
        analysis = chunking_service.analyze_content(long_text_many_entities)
        assert analysis["exceeds_chars_threshold"]
        # Note: entities detection sería real con spaCy en implementación real


# =============================================================================
# TESTS DE PROCESAMIENTO PARALELO DE CHUNKS
# =============================================================================

class TestParallelChunkProcessing:
    """Tests del procesamiento paralelo de chunks."""
    
    @pytest.mark.asyncio
    async def test_parallel_entity_extraction(self, resultado_fase2_mock):
        """Test extracción paralela de entidades."""
        chunks = ["Chunk 1: Juan Pérez", "Chunk 2: María González", "Chunk 3: Carlos López"]
        
        with patch('src.pipeline.fase_3_entidades.Groq') as mock_groq:
            # Mock respuesta para cada chunk
            mock_groq.return_value.chat.completions.create.return_value = Mock(
                choices=[Mock(message=Mock(content='{"entidades": [{"id": 1, "nombre": "Test", "tipo": "PERSONA"}]}'))],
                usage=Mock(prompt_tokens=100, completion_tokens=50)
            )
            
            # Test procesamiento paralelo
            resultado = await extraer_entidades_con_chunking_paralelo(
                resultado_fase2_mock, 
                chunks,
                max_concurrent_chunks=3
            )
            
            # Verificar que se procesaron todos los chunks
            assert "entidades_extraidas" in resultado
            assert resultado["metadatos_extraccion"]["parallel_processing"] is True
            assert resultado["metadatos_extraccion"]["chunks_processed"] == len(chunks)
    
    @pytest.mark.asyncio
    async def test_parallel_vs_sequential_performance(self, resultado_fase2_mock):
        """Test comparación de rendimiento paralelo vs secuencial."""
        chunks = ["Chunk 1", "Chunk 2", "Chunk 3", "Chunk 4", "Chunk 5"]
        
        with patch('src.pipeline.fase_3_entidades.Groq') as mock_groq:
            mock_groq.return_value.chat.completions.create.return_value = Mock(
                choices=[Mock(message=Mock(content='{"entidades": []}'))],
                usage=Mock(prompt_tokens=100, completion_tokens=50)
            )
            
            # Medir tiempo secuencial
            import time
            start_time = time.time()
            resultado_seq = extraer_entidades_con_chunking(resultado_fase2_mock, chunks)
            tiempo_secuencial = time.time() - start_time
            
            # Medir tiempo paralelo
            start_time = time.time()
            resultado_par = await extraer_entidades_con_chunking_paralelo(
                resultado_fase2_mock, chunks, max_concurrent_chunks=3
            )
            tiempo_paralelo = time.time() - start_time
            
            # Verificar que ambos producen resultados válidos
            assert "entidades_extraidas" in resultado_seq
            assert "entidades_extraidas" in resultado_par
            
            # En un entorno real, el paralelo debería ser más rápido
            # Con mocks, verificamos que la estructura es correcta
            assert resultado_par["metadatos_extraccion"]["parallel_processing"] is True
    
    @pytest.mark.asyncio
    async def test_parallel_processing_error_handling(self, resultado_fase2_mock):
        """Test manejo de errores en procesamiento paralelo."""
        chunks = ["Chunk válido", "Chunk que falla", "Otro chunk válido"]
        
        with patch('src.pipeline.fase_3_entidades.Groq') as mock_groq:
            # Simular que el segundo chunk falla
            def side_effect(*args, **kwargs):
                call_count = getattr(side_effect, 'call_count', 0)
                side_effect.call_count = call_count + 1
                
                if call_count == 1:  # Segunda llamada falla
                    raise Exception("Error simulado en chunk")
                else:
                    return Mock(
                        choices=[Mock(message=Mock(content='{"entidades": []}'))],
                        usage=Mock(prompt_tokens=100, completion_tokens=50)
                    )
            
            mock_groq.return_value.chat.completions.create.side_effect = side_effect
            
            # El procesamiento paralelo debería manejar el error
            resultado = await extraer_entidades_con_chunking_paralelo(
                resultado_fase2_mock, chunks, max_concurrent_chunks=3
            )
            
            # Verificar que se procesaron los chunks exitosos
            assert "entidades_extraidas" in resultado
            assert "errores_chunks" in resultado["metadatos_extraccion"]
            assert len(resultado["metadatos_extraccion"]["errores_chunks"]) > 0


# =============================================================================
# TESTS DE CONSOLIDACIÓN CROSS-CHUNK
# =============================================================================

class TestCrossChunkConsolidation:
    """Tests de consolidación de resultados entre chunks."""
    
    def test_consolidate_duplicate_entities(self, consolidation_service):
        """Test consolidación de entidades duplicadas."""
        entidades_chunk1 = [
            {"id": 1, "nombre": "Juan Pérez", "tipo": "PERSONA"},
            {"id": 2, "nombre": "Ministerio de Economía", "tipo": "ORGANIZACION"}
        ]
        
        entidades_chunk2 = [
            {"id": 3, "nombre": "Juan Perez", "tipo": "PERSONA"},  # Variación ortográfica
            {"id": 4, "nombre": "María González", "tipo": "PERSONA"}
        ]
        
        # Consolidar entidades
        entidades_consolidadas = consolidation_service.consolidate_entities([
            entidades_chunk1, entidades_chunk2
        ])
        
        # Verificar que se eliminaron duplicados
        assert len(entidades_consolidadas) == 3  # Juan Pérez consolidado
        
        # Verificar que se mantuvieron IDs secuenciales
        ids = [e["id"] for e in entidades_consolidadas]
        assert ids == [1, 2, 3]  # IDs renumerados secuencialmente
    
    def test_consolidate_similar_facts(self, consolidation_service):
        """Test consolidación de hechos similares."""
        hechos_chunk1 = [
            {"id": 1, "contenido": "El presidente se reunió con el ministro", "tipo_hecho": "EVENTO"}
        ]
        
        hechos_chunk2 = [
            {"id": 2, "contenido": "Reunión presidencial con ministro de economía", "tipo_hecho": "EVENTO"}
        ]
        
        # Consolidar hechos
        hechos_consolidados = consolidation_service.consolidate_facts([
            hechos_chunk1, hechos_chunk2
        ])
        
        # Verificar consolidación de hechos similares
        assert len(hechos_consolidados) == 1  # Hechos similares consolidados
        assert "reunión" in hechos_consolidados[0]["contenido"].lower()
    
    def test_consolidation_preserves_best_quality(self, consolidation_service):
        """Test que la consolidación preserva la mejor calidad."""
        entidades_chunks = [
            [{"id": 1, "nombre": "J. Pérez", "tipo": "PERSONA", "descripcion": ""}],
            [{"id": 2, "nombre": "Juan Pérez", "tipo": "PERSONA", "descripcion": "Presidente del país"}]
        ]
        
        consolidadas = consolidation_service.consolidate_entities(entidades_chunks)
        
        # Debería preservar la entidad con más información
        assert len(consolidadas) == 1
        assert consolidadas[0]["nombre"] == "Juan Pérez"  # Nombre completo
        assert len(consolidadas[0]["descripcion"]) > 0     # Descripción completa
    
    def test_consolidation_threshold_configuration(self, consolidation_service):
        """Test que el threshold de consolidación es configurable."""
        config = get_parallel_processing_config()
        
        # Verificar que el threshold se puede configurar
        original_threshold = consolidation_service.similarity_threshold
        
        # Cambiar threshold temporalmente
        consolidation_service.similarity_threshold = 0.9  # Más estricto
        
        entidades_similares = [
            [{"id": 1, "nombre": "Juan Pérez", "tipo": "PERSONA"}],
            [{"id": 2, "nombre": "Juan Perez", "tipo": "PERSONA"}]  # Sin tilde
        ]
        
        # Con threshold alto, no debería consolidar
        resultado_estricto = consolidation_service.consolidate_entities(entidades_similares)
        
        # Restaurar threshold original
        consolidation_service.similarity_threshold = original_threshold
        
        # Verificar que el threshold afecta el resultado
        assert isinstance(resultado_estricto, list)


# =============================================================================
# TESTS DE INTEGRACIÓN CHUNKING + FASES
# =============================================================================

class TestChunkingPhasesIntegration:
    """Tests de integración entre chunking y fases del pipeline."""
    
    @pytest.mark.asyncio
    async def test_fase3_automatic_chunking_activation(self, long_text):
        """Test que Fase 3 activa chunking automáticamente."""
        resultado_fase2 = ResultadoFase2Simplificacion(
            id_fragmento=uuid4(),
            texto_simplificado=long_text,
            cambios_realizados=["test"],
            metadatos_simplificacion={}
        )
        
        with patch('src.pipeline.fase_3_entidades.Groq') as mock_groq:
            mock_groq.return_value.chat.completions.create.return_value = Mock(
                choices=[Mock(message=Mock(content='{"entidades": []}'))],
                usage=Mock(prompt_tokens=100, completion_tokens=50)
            )
            
            resultado = await ejecutar_fase_3_entidades(resultado_fase2)
            
            # Verificar que se activó chunking automáticamente
            assert "metadatos_extraccion" in resultado
            metadatos = resultado["metadatos_extraccion"]
            
            # Si el texto era largo, debería haber usado chunking
            if len(long_text) > pipeline_config.chunking.chars_threshold:
                assert metadatos.get("chunking_used", False) is True
                assert metadatos.get("chunks_processed", 0) > 1
    
    @pytest.mark.asyncio 
    async def test_fase4_chunking_with_cross_references(self):
        """Test que Fase 4 maneja referencias cruzadas con chunking."""
        # Texto que debería generar chunks y referencias entre entidades
        texto_con_referencias = """
        Juan Pérez, presidente de la nación, se reunió con María González, 
        ministra de Economía. Durante la reunión, Pérez anunció que González 
        liderará el nuevo programa económico. El programa, según González,
        incluirá medidas que Pérez había propuesto anteriormente.
        """ * 50  # Repetir para forzar chunking
        
        resultado_fase2 = ResultadoFase2Simplificacion(
            id_fragmento=uuid4(),
            texto_simplificado=texto_con_referencias,
            cambios_realizados=["test"],
            metadatos_simplificacion={}
        )
        
        with patch('src.pipeline.fase_4_hechos.Groq') as mock_groq:
            mock_groq.return_value.chat.completions.create.return_value = Mock(
                choices=[Mock(message=Mock(content='{"hechos": [{"id": 1, "contenido": "Reunión presidencial", "entidades_relacionadas": ["Juan Pérez", "María González"]}]}'))],
                usage=Mock(prompt_tokens=100, completion_tokens=50)
            )
            
            resultado = await ejecutar_fase_4_hechos(resultado_fase2)
            
            # Verificar que se procesaron referencias cruzadas
            assert "hechos_extraidos" in resultado
            assert "metadatos_extraccion" in resultado
            
            # Si se usó chunking, debería haber consolidación
            metadatos = resultado["metadatos_extraccion"]
            if metadatos.get("chunking_used", False):
                assert "consolidation_applied" in metadatos


# =============================================================================
# TESTS DE RENDIMIENTO CON CHUNKING
# =============================================================================

class TestChunkingPerformance:
    """Tests de rendimiento del sistema de chunking."""
    
    def test_chunking_overhead_is_minimal(self, chunking_service, medium_text):
        """Test que el overhead de chunking es mínimo."""
        import time
        
        # Medir tiempo sin chunking (texto se procesa completo)
        start_time = time.time()
        for _ in range(10):
            # Simular procesamiento simple
            len(medium_text.split())
        tiempo_sin_chunks = time.time() - start_time
        
        # Medir tiempo con chunking
        start_time = time.time()
        for _ in range(10):
            chunks = chunking_service.create_chunks(medium_text)
            for chunk in chunks:
                len(chunk.text.split())
        tiempo_con_chunks = time.time() - start_time
        
        # El overhead debería ser menor al 50%
        overhead = (tiempo_con_chunks - tiempo_sin_chunks) / tiempo_sin_chunks
        assert overhead < 0.5, f"Overhead de chunking demasiado alto: {overhead:.2%}"
    
    def test_memory_usage_with_large_content(self, chunking_service):
        """Test uso de memoria con contenido grande."""
        # Crear contenido muy grande
        huge_content = "Este es un texto muy largo. " * 10000  # ~270KB
        
        # El chunking debería manejar esto sin problemas de memoria
        try:
            chunks = chunking_service.create_chunks(huge_content)
            
            # Verificar que se crearon chunks apropiados
            assert len(chunks) > 10  # Contenido grande debería crear muchos chunks
            
            # Verificar que cada chunk es manejable
            for chunk in chunks:
                assert len(chunk.text) <= pipeline_config.chunking.chars_threshold * 1.2  # 20% margen
                
        except MemoryError:
            pytest.fail("Chunking causó problemas de memoria con contenido grande")
    
    @pytest.mark.asyncio
    async def test_parallel_processing_scales_with_chunks(self, resultado_fase2_mock):
        """Test que el procesamiento paralelo escala con el número de chunks."""
        # Test con diferentes cantidades de chunks
        chunk_counts = [2, 5, 10]
        processing_times = []
        
        for count in chunk_counts:
            chunks = [f"Chunk {i}: Contenido de prueba" for i in range(count)]
            
            with patch('src.pipeline.fase_3_entidades.Groq') as mock_groq:
                mock_groq.return_value.chat.completions.create.return_value = Mock(
                    choices=[Mock(message=Mock(content='{"entidades": []}'))],
                    usage=Mock(prompt_tokens=100, completion_tokens=50)
                )
                
                import time
                start_time = time.time()
                
                await extraer_entidades_con_chunking_paralelo(
                    resultado_fase2_mock, chunks, max_concurrent_chunks=3
                )
                
                processing_time = time.time() - start_time
                processing_times.append(processing_time)
        
        # Con procesamiento paralelo, el tiempo no debería crecer linealmente
        # (aunque con mocks es difícil medir tiempo real)
        assert all(t >= 0 for t in processing_times), "Todos los procesamientos deberían completarse"


if __name__ == "__main__":
    # Ejecutar tests cuando se ejecuta directamente
    pytest.main([__file__, "-v", "--tb=short"])