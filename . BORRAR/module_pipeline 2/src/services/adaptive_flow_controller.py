"""
AdaptiveFlowController: Control de Flujo Dinámico del Pipeline
=============================================================

Toma decisiones sobre el flujo del pipeline basándose en el análisis
de contenido, determinando qué fases ejecutar y cómo procesarlas.
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from loguru import logger

from ..models.analisis import AnalisisComponentes, FlowDecision


@dataclass
class PipelineThresholds:
    """Umbrales configurables para decisiones del pipeline."""

    chunking_entities_threshold: int = 30
    chunking_chars_threshold: int = 6000
    chunking_quotes_threshold: int = 30
    chunking_data_threshold: int = 30
    large_model_token_threshold: int = 8000
    min_data_for_extraction: int = 1
    min_quotes_for_extraction: int = 1
    high_density_entities_threshold: float = 10.0
    high_density_data_threshold: float = 5.0


class AdaptiveFlowController:
    """
    Controlador de flujo adaptativo del pipeline.

    Evalúa las características del contenido y toma decisiones
    sobre cómo procesarlo de manera óptima.
    """

    def __init__(self, thresholds: Optional[PipelineThresholds] = None):
        """
        Inicializa el controlador.

        Args:
            thresholds: Umbrales personalizados (usa valores por defecto si no se proporcionan)
        """
        self.thresholds = thresholds or self._load_thresholds_from_env()
        logger.info(
            "AdaptiveFlowController inicializado",
            entities_threshold=self.thresholds.chunking_entities_threshold,
            chars_threshold=self.thresholds.chunking_chars_threshold,
        )

    def _load_thresholds_from_env(self) -> PipelineThresholds:
        """Carga umbrales desde variables de entorno."""
        return PipelineThresholds(
            chunking_entities_threshold=int(
                os.getenv("PIPELINE_CHUNKING_ENTITIES_THRESHOLD", "30")
            ),
            chunking_chars_threshold=int(
                os.getenv("PIPELINE_CHUNKING_CHARS_THRESHOLD", "6000")
            ),
            chunking_quotes_threshold=int(
                os.getenv("PIPELINE_CHUNKING_QUOTES_THRESHOLD", "30")
            ),
            chunking_data_threshold=int(
                os.getenv("PIPELINE_CHUNKING_DATA_THRESHOLD", "30")
            ),
            large_model_token_threshold=int(
                os.getenv("PIPELINE_GROQ_MODEL_TOKEN_THRESHOLD", "8000")
            ),
            min_data_for_extraction=int(
                os.getenv("PIPELINE_MIN_DATA_FOR_EXTRACTION", "1")
            ),
            min_quotes_for_extraction=int(
                os.getenv("PIPELINE_MIN_QUOTES_FOR_EXTRACTION", "1")
            ),
            high_density_entities_threshold=float(
                os.getenv("PIPELINE_HIGH_DENSITY_ENTITIES_THRESHOLD", "10.0")
            ),
            high_density_data_threshold=float(
                os.getenv("PIPELINE_HIGH_DENSITY_DATA_THRESHOLD", "5.0")
            ),
        )

    def evaluate_content(self, analysis: AnalisisComponentes) -> FlowDecision:
        """
        Evalúa el contenido y genera decisiones de flujo.

        Args:
            analysis: Análisis del contenido realizado por SpacyAnalyzer

        Returns:
            FlowDecision con todas las decisiones para el pipeline
        """
        decision = FlowDecision()
        justificaciones = []

        # Decisiones de chunking por tipo
        decision.chunk_entities = self._should_chunk_entities(analysis)
        if decision.chunk_entities:
            justificaciones.append(
                f"Chunking entidades: {analysis.conteo_entidades} entidades detectadas"
            )

        decision.chunk_facts = self._should_chunk_facts(analysis)
        if decision.chunk_facts:
            justificaciones.append(
                f"Chunking hechos: texto de {analysis.longitud_caracteres} caracteres"
            )

        decision.chunk_quotes = self._should_chunk_quotes(analysis)
        if decision.chunk_quotes:
            justificaciones.append(
                f"Chunking citas: {'entrevista' if analysis.es_entrevista else f'{analysis.conteo_citas} citas'}"
            )

        decision.chunk_data = self._should_chunk_data(analysis)
        if decision.chunk_data:
            justificaciones.append(
                f"Chunking datos: {analysis.conteo_datos} elementos numéricos"
            )

        # Decisiones de ejecución de fases
        decision.execute_data_phase = (
            analysis.conteo_datos >= self.thresholds.min_data_for_extraction
        )
        if not decision.execute_data_phase:
            justificaciones.append(
                "Fase de datos omitida: sin datos numéricos detectados"
            )

        decision.execute_quotes_phase = (
            analysis.conteo_citas >= self.thresholds.min_quotes_for_extraction
        )
        if not decision.execute_quotes_phase:
            justificaciones.append("Fase de citas omitida: sin citas detectadas")

        # Decisión de modelo LLM
        decision.use_large_model = self._should_use_large_model(analysis)
        if decision.use_large_model:
            justificaciones.append(
                f"Modelo grande recomendado: {analysis.conteo_tokens} tokens"
            )

        # Configuración de chunking si aplica
        if any(
            [
                decision.chunk_entities,
                decision.chunk_facts,
                decision.chunk_quotes,
                decision.chunk_data,
            ]
        ):
            chunk_config = self._calculate_chunk_config(analysis, decision)
            decision.recommended_chunk_size = chunk_config["chunk_size"]
            decision.recommended_overlap = chunk_config["overlap"]

        decision.justificacion = (
            "; ".join(justificaciones) if justificaciones else "Procesamiento estándar"
        )

        logger.info(
            "Decisiones de flujo generadas",
            chunk_any=any(
                [
                    decision.chunk_entities,
                    decision.chunk_facts,
                    decision.chunk_quotes,
                    decision.chunk_data,
                ]
            ),
            use_large_model=decision.use_large_model,
            skip_phases=2
            - sum([decision.execute_data_phase, decision.execute_quotes_phase]),
        )

        return decision

    def _should_chunk_entities(self, analysis: AnalisisComponentes) -> bool:
        """Determina si aplicar chunking para entidades."""
        # Por número absoluto
        if analysis.conteo_entidades > self.thresholds.chunking_entities_threshold:
            return True

        # Por densidad
        if (
            analysis.densidad_entidades
            > self.thresholds.high_density_entities_threshold
        ):
            return True

        # Por concentración en oraciones
        if analysis.max_entidades_por_oracion > 8:
            return True

        return False

    def _should_chunk_facts(self, analysis: AnalisisComponentes) -> bool:
        """Determina si aplicar chunking para hechos."""
        # Por longitud de texto
        if analysis.longitud_caracteres > self.thresholds.chunking_chars_threshold:
            return True

        # Por número de oraciones muy largas
        if analysis.promedio_tokens_por_oracion > 50 and analysis.conteo_oraciones > 20:
            return True

        return False

    def _should_chunk_quotes(self, analysis: AnalisisComponentes) -> bool:
        """Determina si aplicar chunking para citas."""
        # Si es entrevista
        if analysis.es_entrevista:
            return True

        # Por número de citas
        if analysis.conteo_citas > self.thresholds.chunking_quotes_threshold:
            return True

        # Si hay muchas citas pero texto corto (alta densidad)
        if analysis.conteo_citas > 10 and analysis.longitud_caracteres < 3000:
            return True

        return False

    def _should_chunk_data(self, analysis: AnalisisComponentes) -> bool:
        """Determina si aplicar chunking para datos."""
        # Por número absoluto
        if analysis.conteo_datos > self.thresholds.chunking_data_threshold:
            return True

        # Por densidad
        if analysis.densidad_numerica > self.thresholds.high_density_data_threshold:
            return True

        # Si tiene muchos tipos de datos numéricos
        tipos_datos = sum(
            [analysis.tiene_fechas, analysis.tiene_monedas, analysis.tiene_porcentajes]
        )
        if tipos_datos >= 2 and analysis.conteo_datos > 15:
            return True

        return False

    def _should_use_large_model(self, analysis: AnalisisComponentes) -> bool:
        """Determina si usar el modelo grande (70B)."""
        # Por número de tokens
        if analysis.conteo_tokens > self.thresholds.large_model_token_threshold:
            return True

        # Por complejidad (muchas entidades y relaciones potenciales)
        if analysis.conteo_entidades > 50:
            return True

        # Por densidad muy alta de información
        if analysis.densidad_entidades > 15 or analysis.densidad_numerica > 10:
            return True

        return False

    def _calculate_chunk_config(
        self, analysis: AnalisisComponentes, decision: FlowDecision
    ) -> Dict[str, int]:
        """
        Calcula configuración óptima de chunking.

        Returns:
            Dict con chunk_size y overlap recomendados
        """
        # Configuración base
        chunk_size = 3000
        overlap = 200

        # Ajustar según el tipo de contenido predominante
        if decision.chunk_quotes and (
            analysis.es_entrevista or analysis.conteo_citas > 20
        ):
            # Chunks más pequeños para preservar contexto de citas
            chunk_size = 2000
            overlap = 250

        elif decision.chunk_entities and analysis.densidad_entidades > 10:
            # Chunks medianos con buen overlap para relaciones
            chunk_size = 2500
            overlap = 300

        elif decision.chunk_data and analysis.conteo_datos > 40:
            # Chunks más grandes para datos relacionados
            chunk_size = 4000
            overlap = 150

        # Ajustar por longitud promedio de oraciones
        if analysis.promedio_tokens_por_oracion > 40:
            # Oraciones largas: reducir chunk size
            chunk_size = int(chunk_size * 0.8)
            overlap = int(overlap * 1.2)

        # Límites mínimos y máximos
        chunk_size = max(1500, min(5000, chunk_size))
        overlap = max(100, min(500, overlap))

        return {"chunk_size": chunk_size, "overlap": overlap}

    def validate_decision(
        self, decision: FlowDecision, analysis: AnalisisComponentes
    ) -> bool:
        """
        Valida que las decisiones sean coherentes.

        Args:
            decision: Decisiones tomadas
            analysis: Análisis original

        Returns:
            True si las decisiones son válidas
        """
        # Validar que no se omitan fases críticas
        if analysis.conteo_datos > 10 and not decision.execute_data_phase:
            logger.warning("Muchos datos detectados pero fase de datos deshabilitada")
            return False

        if analysis.conteo_citas > 10 and not decision.execute_quotes_phase:
            logger.warning("Muchas citas detectadas pero fase de citas deshabilitada")
            return False

        # Validar coherencia de chunking
        if decision.chunk_entities and analysis.conteo_entidades < 5:
            logger.warning("Chunking de entidades activado con pocas entidades")
            return False

        return True

    def get_processing_stats(self, decision: FlowDecision) -> Dict[str, Any]:
        """
        Obtiene estadísticas sobre las decisiones de procesamiento.

        Args:
            decision: Decisiones tomadas

        Returns:
            Dict con estadísticas
        """
        return {
            "phases_to_execute": 5
            + sum([decision.execute_data_phase, decision.execute_quotes_phase]),
            "chunking_phases": sum(
                [
                    decision.chunk_entities,
                    decision.chunk_facts,
                    decision.chunk_quotes,
                    decision.chunk_data,
                ]
            ),
            "use_large_model": decision.use_large_model,
            "estimated_complexity": self._estimate_complexity(decision),
        }

    def _estimate_complexity(self, decision: FlowDecision) -> str:
        """Estima la complejidad del procesamiento."""
        score = 0

        # Puntos por chunking
        score += (
            sum(
                [
                    decision.chunk_entities,
                    decision.chunk_facts,
                    decision.chunk_quotes,
                    decision.chunk_data,
                ]
            )
            * 2
        )

        # Puntos por modelo grande
        if decision.use_large_model:
            score += 3

        # Puntos por fases opcionales
        score += sum([decision.execute_data_phase, decision.execute_quotes_phase])

        if score <= 2:
            return "baja"
        elif score <= 5:
            return "media"
        elif score <= 8:
            return "alta"
        else:
            return "muy alta"


# Función de conveniencia
def create_adaptive_flow_controller(
    thresholds: Optional[PipelineThresholds] = None,
) -> AdaptiveFlowController:
    """Factory function para crear AdaptiveFlowController."""
    return AdaptiveFlowController(thresholds)
