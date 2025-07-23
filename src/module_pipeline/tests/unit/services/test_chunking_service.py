"""
Tests para ChunkingService
=========================

Pruebas unitarias para el servicio de chunking inteligente.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4

from ....src.services.chunking_service import (
    ChunkingService,
    ChunkingConfig,
    ChunkType,
    TextChunk,
    create_chunking_service,
    estimate_chunks_needed
)


class TestChunkingService:
    """Tests para ChunkingService."""
    
    @pytest.fixture
    def config(self):
        """Configuración de prueba."""
        return ChunkingConfig(
            max_chunk_size=100,
            overlap_size=20,
            context_window=10,
            min_chunk_size=30
        )
    
    @pytest.fixture
    def service(self, config):
        """Servicio de chunking configurado."""
        return ChunkingService(config)
    
    @pytest.fixture
    def mock_nlp(self):
        """Mock del modelo spaCy."""
        mock_model = MagicMock()
        mock_model.lang = "es"
        return mock_model
    
    def test_init_default_config(self):
        """Test inicialización con config por defecto."""
        service = ChunkingService()
        assert service.config.max_chunk_size == 3000
        assert service.config.overlap_size == 200
        assert service.nlp is None
    
    def test_init_custom_config(self, config):
        """Test inicialización con config personalizada."""
        service = ChunkingService(config)
        assert service.config.max_chunk_size == 100
        assert service.config.overlap_size == 20
    
    def test_create_chunks_empty_text(self, service):
        """Test chunking de texto vacío."""
        chunks = service.create_chunks("")
        assert chunks == []
        
        chunks = service.create_chunks("   ")
        assert chunks == []
    
    def test_create_chunks_single_chunk(self, service):
        """Test texto que no requiere chunking."""
        text = "Este es un texto corto."
        chunks = service.create_chunks(text)
        
        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].index == 0
        assert chunks[0].total == 1
        assert chunks[0].start_offset == 0
        assert chunks[0].end_offset == len(text)
        assert chunks[0].context["single_chunk"] is True
    
    def test_create_simple_chunks(self, service):
        """Test chunking simple sin spaCy."""
        # Texto largo que requiere múltiples chunks
        text = "A" * 150  # 150 caracteres
        chunks = service.create_chunks(
            text, 
            preserve_boundaries=False
        )
        
        assert len(chunks) == 2
        # Primer chunk: 100 chars
        assert len(chunks[0].text) == 100
        assert chunks[0].index == 0
        assert chunks[0].total == 2
        
        # Segundo chunk: 50 chars + 20 overlap = 70 chars
        assert len(chunks[1].text) == 70
        assert chunks[1].index == 1
        assert chunks[1].overlap_text is not None
    
    def test_create_chunks_with_word_boundaries(self, service):
        """Test respeto de límites de palabras."""
        text = "Primera palabra. " * 10  # ~170 caracteres
        chunks = service.create_chunks(text, preserve_boundaries=False)
        
        # Verificar que no corta palabras
        for chunk in chunks:
            assert not chunk.text.endswith("palab")
            assert not chunk.text.startswith("ra.")
    
    @patch('src.services.chunking_service.spacy')
    def test_create_intelligent_chunks_with_spacy(self, mock_spacy, service, mock_nlp):
        """Test chunking inteligente con spaCy."""
        # Configurar mock de spaCy
        mock_spacy.load.return_value = mock_nlp
        
        # Mock del documento procesado
        mock_doc = MagicMock()
        mock_sents = []
        
        # Crear oraciones mock
        for i in range(5):
            sent = MagicMock()
            sent.text = f"Oración número {i}. "
            sent.start_char = i * 20
            sent.end_char = (i + 1) * 20
            mock_sents.append(sent)
        
        mock_doc.sents = mock_sents
        mock_doc.text = "".join(s.text for s in mock_sents)
        mock_nlp.return_value = mock_doc
        
        # Reinicializar servicio para cargar modelo
        service = ChunkingService(service.config)
        service.nlp = mock_nlp
        
        chunks = service.create_chunks(mock_doc.text)
        
        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.metadata.get("sentence_count") is not None
    
    def test_chunk_type_specific_strategies(self, service):
        """Test diferentes estrategias según tipo."""
        text = "Texto de prueba. " * 20
        
        # Test estrategia QUOTES
        chunks_quotes = service.create_chunks(
            text, 
            chunk_type=ChunkType.QUOTES,
            preserve_boundaries=False
        )
        
        # Test estrategia ENTITIES
        chunks_entities = service.create_chunks(
            text,
            chunk_type=ChunkType.ENTITIES,
            preserve_boundaries=False
        )
        
        # Verificar que se aplica el tipo correcto
        assert all(c.context["chunk_type"] == "quotes" for c in chunks_quotes)
        assert all(c.context["chunk_type"] == "entities" for c in chunks_entities)
    
    def test_chunk_context_enrichment(self, service):
        """Test enriquecimiento de contexto."""
        text = "A" * 250  # Forzar 3 chunks
        chunks = service.create_chunks(text, preserve_boundaries=False)
        
        assert len(chunks) >= 2
        
        # Primer chunk
        assert chunks[0].context["position"] == "first"
        assert chunks[0].context["has_previous"] is False
        assert chunks[0].context["has_next"] is True
        
        # Último chunk
        assert chunks[-1].context["position"] == "last"
        assert chunks[-1].context["has_previous"] is True
        assert chunks[-1].context["has_next"] is False
        
        # Verificar referencias entre chunks
        if len(chunks) > 1:
            assert "next_chunk_start" in chunks[0].context
            assert "previous_chunk_end" in chunks[1].context
    
    def test_calculate_optimal_chunk_size(self, service):
        """Test cálculo de tamaño óptimo."""
        # Test para diferentes tipos
        config_quotes = service.calculate_optimal_chunk_size(
            10000, ChunkType.QUOTES
        )
        assert config_quotes.max_chunk_size <= 2000
        assert config_quotes.overlap_size == 150
        
        config_entities = service.calculate_optimal_chunk_size(
            10000, ChunkType.ENTITIES
        )
        assert config_entities.max_chunk_size <= 3000
        assert config_entities.overlap_size == 200
        
        config_data = service.calculate_optimal_chunk_size(
            10000, ChunkType.DATA
        )
        assert config_data.max_chunk_size <= 4000
        assert config_data.overlap_size == 100
    
    def test_merge_overlapping_results(self, service):
        """Test fusión de resultados con overlap."""
        results_by_chunk = {
            0: ["resultado1", "resultado2"],
            1: ["resultado2", "resultado3"],  # resultado2 duplicado
            2: ["resultado4"]
        }
        
        overlap_info = [(0, 1), (1, 2)]
        
        merged = service.merge_overlapping_results(
            results_by_chunk,
            overlap_info
        )
        
        # Debe eliminar duplicados
        assert len(merged) == 4
        assert "resultado1" in merged
        assert "resultado2" in merged
        assert "resultado3" in merged
        assert "resultado4" in merged
    
    def test_custom_config_per_operation(self, service):
        """Test config personalizada por operación."""
        text = "A" * 500
        custom_config = ChunkingConfig(
            max_chunk_size=200,
            overlap_size=50
        )
        
        chunks = service.create_chunks(
            text,
            custom_config=custom_config,
            preserve_boundaries=False
        )
        
        # Verificar que usa la config personalizada
        assert chunks[0].text[:200] == "A" * 200


class TestUtilityFunctions:
    """Tests para funciones de utilidad."""
    
    def test_create_chunking_service(self):
        """Test factory function."""
        service = create_chunking_service()
        assert isinstance(service, ChunkingService)
        assert service.config.max_chunk_size == 3000
        
        # Con config personalizada
        config = ChunkingConfig(max_chunk_size=500)
        service = create_chunking_service(config)
        assert service.config.max_chunk_size == 500
    
    def test_estimate_chunks_needed(self):
        """Test estimación de chunks."""
        # Texto que cabe en un chunk
        assert estimate_chunks_needed(1000) == 1
        
        # Texto que requiere múltiples chunks
        assert estimate_chunks_needed(10000, 3000, 200) == 4
        
        # Casos edge
        assert estimate_chunks_needed(3000, 3000, 200) == 1
        assert estimate_chunks_needed(3001, 3000, 200) == 2


class TestTextChunk:
    """Tests para la clase TextChunk."""
    
    def test_text_chunk_initialization(self):
        """Test inicialización de TextChunk."""
        chunk = TextChunk(
            index=0,
            total=3,
            text="Texto de prueba",
            start_offset=0,
            end_offset=15
        )
        
        assert chunk.index == 0
        assert chunk.total == 3
        assert chunk.text == "Texto de prueba"
        assert chunk.context == {}
        assert chunk.metadata == {}
    
    def test_text_chunk_to_dict(self):
        """Test conversión a diccionario."""
        chunk = TextChunk(
            index=1,
            total=2,
            text="Chunk de prueba",
            start_offset=100,
            end_offset=115,
            overlap_text="overlap",
            context={"key": "value"},
            metadata={"count": 5}
        )
        
        chunk_dict = chunk.to_dict()
        
        assert chunk_dict["index"] == 1
        assert chunk_dict["total"] == 2
        assert chunk_dict["text"] == "Chunk de prueba"
        assert chunk_dict["overlap_text"] == "overlap"
        assert chunk_dict["context"]["key"] == "value"
        assert chunk_dict["metadata"]["count"] == 5


@pytest.mark.integration
class TestChunkingServiceIntegration:
    """Tests de integración con casos reales."""
    
    def test_real_spanish_text_chunking(self):
        """Test con texto real en español."""
        text = """
        El presidente del Gobierno, Pedro Sánchez, anunció ayer un paquete de medidas
        económicas destinadas a paliar los efectos de la inflación. Entre las medidas
        destacan la reducción del IVA en productos básicos y el aumento de las ayudas
        a familias vulnerables.
        
        La ministra de Economía, Nadia Calviño, explicó que estas medidas tendrán un
        impacto presupuestario de 10.000 millones de euros. "Es fundamental proteger
        a los más vulnerables", declaró Calviño en rueda de prensa.
        
        Por su parte, la oposición criticó duramente las medidas, calificándolas de
        "insuficientes y tardías". El líder del PP, Alberto Núñez Feijóo, señaló que
        el gobierno "llega tarde y mal" a la crisis económica.
        """ * 5  # Repetir para hacer el texto más largo
        
        config = ChunkingConfig(
            max_chunk_size=500,
            overlap_size=50,
            respect_sentence_boundaries=True
        )
        
        service = ChunkingService(config)
        chunks = service.create_chunks(text, ChunkType.GENERAL)
        
        # Verificaciones
        assert len(chunks) > 1
        assert all(chunk.text.strip() for chunk in chunks)
        assert all(chunk.total == len(chunks) for chunk in chunks)
        
        # Verificar que no hay pérdida de texto
        reconstructed = ""
        for i, chunk in enumerate(chunks):
            if i == 0:
                reconstructed += chunk.text
            else:
                # Remover overlap del chunk actual
                if chunk.overlap_text:
                    text_without_overlap = chunk.text[len(chunk.overlap_text):].strip()
                    reconstructed += " " + text_without_overlap
                else:
                    reconstructed += " " + chunk.text
        
        # El texto reconstruido debe contener todo el contenido original
        assert len(reconstructed.strip()) >= len(text.strip()) * 0.9  # 90% para margen