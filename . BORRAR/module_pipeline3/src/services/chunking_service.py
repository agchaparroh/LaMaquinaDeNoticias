"""
ChunkingService: División Inteligente de Texto con Preservación de Contexto
===========================================================================

Este servicio implementa la división de textos largos en chunks manejables
para el procesamiento por LLMs, manteniendo coherencia semántica y contexto.

CARACTERÍSTICAS:
- División respetando límites de oraciones y párrafos
- Ventanas de contexto superpuestas (overlap)
- Preservación de elementos completos (hechos, citas)
- Metadata de contexto para cada chunk
- Soporte para diferentes estrategias según tipo de contenido
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID  # noqa: F401

try:
    import spacy
    from spacy.language import Language
except ImportError:
    spacy = None
    Language = None

from loguru import logger
from pydantic import BaseModel, Field

from ..config import get_spacy_fallback_models, get_spacy_model_name


# Modelos de datos
class ChunkType(str, Enum):
    """Tipos de chunking según el contenido."""

    ENTITIES = "entities"
    FACTS = "facts"
    QUOTES = "quotes"
    DATA = "data"
    GENERAL = "general"


class ChunkingConfig(BaseModel):
    """Configuración para el servicio de chunking."""

    max_chunk_size: int = Field(
        default=3000, description="Tamaño máximo de cada chunk en caracteres"
    )
    overlap_size: int = Field(
        default=200, description="Tamaño de superposición entre chunks"
    )
    context_window: int = Field(
        default=100, description="Ventana de contexto adicional"
    )
    min_chunk_size: int = Field(
        default=500, description="Tamaño mínimo para crear un chunk"
    )
    respect_sentence_boundaries: bool = Field(
        default=True, description="Respetar límites de oraciones"
    )
    respect_paragraph_boundaries: bool = Field(
        default=True, description="Respetar límites de párrafos"
    )
    max_sentences_per_chunk: Optional[int] = Field(
        default=None, description="Máximo de oraciones por chunk"
    )


@dataclass
class TextChunk:
    """Representa un chunk de texto con su contexto."""

    index: int
    total: int
    text: str
    start_offset: int
    end_offset: int
    overlap_start: Optional[int] = None
    overlap_end: Optional[int] = None
    overlap_text: Optional[str] = None
    context: Dict[str, Any] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.context is None:
            self.context = {}
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el chunk a diccionario."""
        return {
            "index": self.index,
            "total": self.total,
            "text": self.text,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "overlap_text": self.overlap_text,
            "context": self.context,
            "metadata": self.metadata,
        }


class ChunkingService:
    """
    Servicio para dividir textos largos en chunks manejables.

    Implementa estrategias inteligentes de división que preservan
    el contexto y la coherencia semántica del texto.
    """

    def __init__(
        self,
        config: Optional[ChunkingConfig] = None,
        nlp_model: Optional[Language] = None,
    ):
        """
        Inicializa el servicio de chunking.

        Args:
            config: Configuración del servicio
            nlp_model: Modelo spaCy precargado (opcional)
        """
        self.config = config or ChunkingConfig()
        self.nlp = nlp_model
        self._nlp_cache = {}

        logger.info(
            "ChunkingService inicializado",
            max_chunk_size=self.config.max_chunk_size,
            overlap_size=self.config.overlap_size,
        )

    def _get_nlp_model(self, model_name: Optional[str] = None) -> Optional[Language]:
        """Obtiene o carga el modelo spaCy usando configuración centralizada."""
        if self.nlp:
            return self.nlp

        if not spacy:
            logger.warning("spaCy no está instalado. Usando chunking simple.")
            return None

        # Usar configuración centralizada si no se especifica modelo
        if model_name is None:
            model_name = get_spacy_model_name()

        if model_name not in self._nlp_cache:
            # Intentar cargar el modelo solicitado
            loaded_model = self._try_load_model(model_name)
            if loaded_model:
                self._nlp_cache[model_name] = loaded_model
                return loaded_model

            # Si falló, intentar modelos de fallback
            fallback_models = get_spacy_fallback_models()
            for fallback_model in fallback_models:
                if fallback_model != model_name:  # No intentar el mismo modelo otra vez
                    loaded_model = self._try_load_model(fallback_model)
                    if loaded_model:
                        logger.warning(
                            f"Chunking usando modelo de fallback '{fallback_model}' en lugar de '{model_name}'"
                        )
                        self._nlp_cache[model_name] = (
                            loaded_model  # Cache con el nombre solicitado
                        )
                        return loaded_model

            logger.warning(
                f"No se pudo cargar modelo spaCy '{model_name}' ni ningún fallback para chunking"
            )
            return None

        return self._nlp_cache.get(model_name)

    def _try_load_model(self, model_name: str) -> Optional[Language]:
        """Intenta cargar un modelo spaCy específico."""
        try:
            model = spacy.load(model_name)
            logger.debug(f"Modelo spaCy '{model_name}' cargado para chunking")
            return model
        except Exception as e:
            logger.debug(f"No se pudo cargar modelo spaCy '{model_name}': {e}")
            return None

    def create_chunks(
        self,
        text: str,
        chunk_type: ChunkType = ChunkType.GENERAL,
        preserve_boundaries: bool = True,
        custom_config: Optional[ChunkingConfig] = None,
    ) -> List[TextChunk]:
        """
        Crea chunks del texto según la estrategia especificada.

        Args:
            text: Texto a dividir
            chunk_type: Tipo de chunking a aplicar
            preserve_boundaries: Si preservar límites naturales del texto
            custom_config: Configuración específica para esta operación

        Returns:
            Lista de chunks con contexto preservado
        """
        if not text or not text.strip():
            return []

        config = custom_config or self.config

        # Verificar si necesita chunking
        if len(text) <= config.max_chunk_size:
            logger.debug("Texto no requiere chunking")
            return [
                TextChunk(
                    index=0,
                    total=1,
                    text=text,
                    start_offset=0,
                    end_offset=len(text),
                    context={"single_chunk": True, "chunk_type": chunk_type.value},
                )
            ]

        logger.info(
            f"Iniciando chunking de texto",  # noqa: F541
            text_length=len(text),
            chunk_type=chunk_type.value,
            preserve_boundaries=preserve_boundaries,
        )

        # Seleccionar estrategia de chunking
        if preserve_boundaries and self._get_nlp_model():
            chunks = self._create_intelligent_chunks(text, chunk_type, config)
        else:
            chunks = self._create_simple_chunks(text, config)

        # Añadir contexto a cada chunk
        chunks = self._enrich_chunks_with_context(chunks, chunk_type)

        logger.info(f"Chunking completado: {len(chunks)} chunks creados")
        return chunks

    def _create_intelligent_chunks(
        self, text: str, chunk_type: ChunkType, config: ChunkingConfig
    ) -> List[TextChunk]:
        """
        Crea chunks respetando límites naturales del lenguaje.

        Utiliza spaCy para identificar oraciones y párrafos,
        creando divisiones que preservan la coherencia.
        """
        nlp = self._get_nlp_model()
        if not nlp:
            return self._create_simple_chunks(text, config)

        # Procesar con spaCy
        # Para textos muy largos, usar pipe con n_process
        doc = nlp(text)

        chunks = []
        current_chunk_text = []  # noqa: F841
        current_chunk_start = 0  # noqa: F841
        current_chunk_chars = 0  # noqa: F841

        # Estrategia específica según tipo
        if chunk_type == ChunkType.QUOTES:
            chunks = self._chunk_by_quotes(doc, config)
        elif chunk_type == ChunkType.ENTITIES:
            chunks = self._chunk_by_entity_density(doc, config)
        else:
            # Estrategia general por oraciones
            chunks = self._chunk_by_sentences(doc, config)

        return chunks

    def _chunk_by_sentences(self, doc, config: ChunkingConfig) -> List[TextChunk]:
        """Divide por oraciones respetando límites."""
        chunks = []
        current_sentences = []
        current_start = 0
        current_chars = 0

        for sent in doc.sents:
            sent_text = sent.text
            sent_len = len(sent_text)

            # Verificar si agregar esta oración excede el límite
            if current_chars + sent_len > config.max_chunk_size and current_sentences:
                # Crear chunk con las oraciones acumuladas
                chunk_text = " ".join(current_sentences)
                chunks.append(
                    TextChunk(
                        index=len(chunks),
                        total=0,  # Se actualizará después
                        text=chunk_text,
                        start_offset=current_start,
                        end_offset=current_start + len(chunk_text),
                        metadata={"sentence_count": len(current_sentences)},
                    )
                )

                # Preparar para siguiente chunk con overlap
                if config.overlap_size > 0 and len(current_sentences) > 1:
                    # Mantener última(s) oración(es) como overlap
                    overlap_sentences = current_sentences[-2:]
                    current_sentences = overlap_sentences + [sent_text]
                    current_start = chunks[-1].end_offset - sum(
                        len(s) for s in overlap_sentences
                    )
                    current_chars = sum(len(s) for s in current_sentences)
                else:
                    current_sentences = [sent_text]
                    current_start = sent.start_char
                    current_chars = sent_len
            else:
                current_sentences.append(sent_text)
                if not current_sentences:
                    current_start = sent.start_char
                current_chars += sent_len + 1  # +1 por el espacio

        # Último chunk
        if current_sentences:
            chunk_text = " ".join(current_sentences)
            chunks.append(
                TextChunk(
                    index=len(chunks),
                    total=len(chunks) + 1,
                    text=chunk_text,
                    start_offset=current_start,
                    end_offset=current_start + len(chunk_text),
                    metadata={"sentence_count": len(current_sentences)},
                )
            )

        # Actualizar totales
        for chunk in chunks:
            chunk.total = len(chunks)

        return chunks

    def _chunk_by_quotes(self, doc, config: ChunkingConfig) -> List[TextChunk]:
        """Estrategia especial para textos con muchas citas."""
        # Detectar patrones de citas
        quote_pattern = re.compile(r'["«]([^"»]+)["»]')

        chunks = []
        current_text = []
        current_start = 0
        current_quotes = 0

        for sent in doc.sents:
            sent_quotes = len(quote_pattern.findall(sent.text))

            # Si hay muchas citas, considerar crear chunk
            if current_quotes + sent_quotes > 5 and current_text:
                chunk_text = " ".join(current_text)
                chunks.append(
                    TextChunk(
                        index=len(chunks),
                        total=0,
                        text=chunk_text,
                        start_offset=current_start,
                        end_offset=current_start + len(chunk_text),
                        metadata={
                            "quote_count": current_quotes,
                            "chunk_type": "quote_heavy",
                        },
                    )
                )
                current_text = [sent.text]
                current_start = sent.start_char
                current_quotes = sent_quotes
            else:
                current_text.append(sent.text)
                current_quotes += sent_quotes

        # Último chunk
        if current_text:
            chunk_text = " ".join(current_text)
            chunks.append(
                TextChunk(
                    index=len(chunks),
                    total=len(chunks) + 1,
                    text=chunk_text,
                    start_offset=current_start,
                    end_offset=len(doc.text),
                    metadata={"quote_count": current_quotes},
                )
            )

        # Actualizar totales
        for chunk in chunks:
            chunk.total = len(chunks)

        return chunks if chunks else self._chunk_by_sentences(doc, config)

    def _chunk_by_entity_density(self, doc, config: ChunkingConfig) -> List[TextChunk]:
        """Estrategia para textos con muchas entidades."""
        chunks = []
        current_text = []
        current_start = 0
        current_entities = []

        for sent in doc.sents:
            sent_entities = list(sent.ents)

            # Si hay muchas entidades nuevas, considerar nuevo chunk
            if len(current_entities) + len(sent_entities) > 15 and current_text:
                chunk_text = " ".join(current_text)
                chunks.append(
                    TextChunk(
                        index=len(chunks),
                        total=0,
                        text=chunk_text,
                        start_offset=current_start,
                        end_offset=current_start + len(chunk_text),
                        metadata={
                            "entity_count": len(current_entities),
                            "entity_types": list(
                                set(e.label_ for e in current_entities)
                            ),
                        },
                    )
                )
                current_text = [sent.text]
                current_start = sent.start_char
                current_entities = sent_entities
            else:
                current_text.append(sent.text)
                current_entities.extend(sent_entities)

        # Último chunk
        if current_text:
            chunk_text = " ".join(current_text)
            chunks.append(
                TextChunk(
                    index=len(chunks),
                    total=len(chunks) + 1,
                    text=chunk_text,
                    start_offset=current_start,
                    end_offset=len(doc.text),
                    metadata={
                        "entity_count": len(current_entities),
                        "entity_types": list(set(e.label_ for e in current_entities)),
                    },
                )
            )

        # Actualizar totales
        for chunk in chunks:
            chunk.total = len(chunks)

        return chunks if chunks else self._chunk_by_sentences(doc, config)

    def _create_simple_chunks(
        self, text: str, config: ChunkingConfig
    ) -> List[TextChunk]:
        """
        Crea chunks simples por tamaño con overlap.

        Fallback cuando no hay spaCy o no se requiere inteligencia.
        """
        chunks = []
        text_length = len(text)
        chunk_size = config.max_chunk_size
        overlap = config.overlap_size

        start = 0
        index = 0

        while start < text_length:
            # Calcular fin del chunk
            end = min(start + chunk_size, text_length)

            # Intentar cortar en espacio si es posible
            if end < text_length:
                space_pos = text.rfind(" ", start, end)
                if (
                    space_pos > start + chunk_size // 2
                ):  # Si encontramos espacio en segunda mitad
                    end = space_pos

            # Extraer texto del chunk
            chunk_text = text[start:end].strip()

            # Calcular overlap con chunk anterior
            overlap_start = None
            overlap_text = None
            if index > 0 and overlap > 0:
                overlap_start = max(0, start - overlap)
                overlap_text = text[overlap_start:start].strip()

            chunks.append(
                TextChunk(
                    index=index,
                    total=0,  # Se actualizará después
                    text=chunk_text,
                    start_offset=start,
                    end_offset=end,
                    overlap_start=overlap_start,
                    overlap_text=overlap_text,
                )
            )

            # Mover al siguiente chunk con overlap
            start = end - overlap if end < text_length else text_length
            index += 1

        # Actualizar total en todos los chunks
        total_chunks = len(chunks)
        for chunk in chunks:
            chunk.total = total_chunks

        return chunks

    def _enrich_chunks_with_context(
        self, chunks: List[TextChunk], chunk_type: ChunkType
    ) -> List[TextChunk]:
        """
        Enriquece cada chunk con información de contexto.

        Añade metadata sobre posición, relaciones y tipo de contenido.
        """
        for i, chunk in enumerate(chunks):
            # Contexto básico
            chunk.context.update(
                {
                    "chunk_type": chunk_type.value,
                    "position": "first"
                    if i == 0
                    else "last"
                    if i == len(chunks) - 1
                    else "middle",
                    "has_previous": i > 0,
                    "has_next": i < len(chunks) - 1,
                    "chunk_number": i + 1,
                    "total_chunks": len(chunks),
                }
            )

            # Referencias a chunks adyacentes
            if i > 0:
                chunk.context["previous_chunk_end"] = (
                    chunks[i - 1].text[-50:]
                    if len(chunks[i - 1].text) > 50
                    else chunks[i - 1].text
                )

            if i < len(chunks) - 1:
                chunk.context["next_chunk_start"] = (
                    chunks[i + 1].text[:50]
                    if len(chunks[i + 1].text) > 50
                    else chunks[i + 1].text
                )

            # Estadísticas del chunk
            chunk.metadata.update(
                {
                    "character_count": len(chunk.text),
                    "approximate_tokens": len(chunk.text.split()),
                    "has_overlap": chunk.overlap_text is not None,
                }
            )

        return chunks

    def merge_overlapping_results(
        self,
        results_by_chunk: Dict[int, List[Any]],
        overlap_info: List[Tuple[int, int]],
    ) -> List[Any]:
        """
        Fusiona resultados de chunks con overlap.

        Args:
            results_by_chunk: Resultados indexados por chunk
            overlap_info: Información sobre overlaps entre chunks

        Returns:
            Lista consolidada sin duplicados
        """
        # Implementación básica - se puede extender según necesidad
        merged = []
        seen_texts = set()

        for chunk_idx in sorted(results_by_chunk.keys()):
            for result in results_by_chunk[chunk_idx]:
                # Usar texto como clave de deduplicación (simplificado)
                result_text = str(result)
                if result_text not in seen_texts:
                    merged.append(result)
                    seen_texts.add(result_text)

        return merged

    def calculate_optimal_chunk_size(
        self, text_length: int, chunk_type: ChunkType, target_chunks: int = 5
    ) -> ChunkingConfig:
        """
        Calcula configuración óptima de chunking para un texto.

        Args:
            text_length: Longitud del texto
            chunk_type: Tipo de contenido
            target_chunks: Número objetivo de chunks

        Returns:
            Configuración optimizada
        """
        # Calcular tamaño base
        base_size = text_length // target_chunks

        # Ajustar según tipo
        if chunk_type == ChunkType.QUOTES:
            # Chunks más pequeños para preservar contexto de citas
            chunk_size = min(base_size, 2000)
            overlap = 150
        elif chunk_type == ChunkType.ENTITIES:
            # Chunks medianos para capturar relaciones
            chunk_size = min(base_size, 3000)
            overlap = 200
        elif chunk_type == ChunkType.DATA:
            # Chunks más grandes para datos relacionados
            chunk_size = min(base_size, 4000)
            overlap = 100
        else:
            chunk_size = min(base_size, 3000)
            overlap = 200

        return ChunkingConfig(
            max_chunk_size=max(chunk_size, self.config.min_chunk_size),
            overlap_size=overlap,
            context_window=100,
        )


# Utilidades de conveniencia
def create_chunking_service(
    config: Optional[ChunkingConfig] = None, nlp_model: Optional[Language] = None
) -> ChunkingService:
    """Factory function para crear ChunkingService."""
    return ChunkingService(config, nlp_model)


def estimate_chunks_needed(
    text_length: int, max_chunk_size: int = 3000, overlap_size: int = 200
) -> int:
    """
    Estima el número de chunks necesarios para un texto.

    Args:
        text_length: Longitud del texto
        max_chunk_size: Tamaño máximo por chunk
        overlap_size: Tamaño de overlap

    Returns:
        Número estimado de chunks
    """
    if text_length <= max_chunk_size:
        return 1

    effective_chunk_size = max_chunk_size - overlap_size
    return ((text_length - max_chunk_size) // effective_chunk_size) + 2
