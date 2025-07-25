#!/usr/bin/env python3
"""
Configuración y validación del modelo de embeddings para la Máquina de Noticias
Tarea 26.1: Configure and Validate Embedding Model

Este script configura un modelo de embeddings que genera vectores de 384 dimensiones
compatible con el esquema de base de datos existente.
"""

import logging
import os  # noqa: F401
import re
from datetime import datetime
from typing import Any, Dict, List, Union

import numpy as np

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EmbeddingModel:
    """
    Clase para manejar la generación de embeddings vectoriales de 384 dimensiones
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Inicializar el modelo de embeddings

        Args:
            model_name: Nombre del modelo a usar (debe generar vectores de 384 dim)
        """
        self.model_name = model_name
        self.expected_dimensions = 384
        self.model = None
        self._setup_model()

    def _setup_model(self):
        """
        Configurar el modelo de embeddings
        """
        try:
            # Intentar usar sentence-transformers (recomendado)
            from sentence_transformers import SentenceTransformer

            logger.info(f"Cargando modelo {self.model_name}...")
            self.model = SentenceTransformer(self.model_name)

            # Validar dimensiones
            test_embedding = self.model.encode("Test text")
            actual_dimensions = len(test_embedding)

            if actual_dimensions != self.expected_dimensions:
                raise ValueError(
                    f"El modelo {self.model_name} genera vectores de {actual_dimensions} "
                    f"dimensiones, pero se requieren {self.expected_dimensions}"
                )

            logger.info(
                f"Modelo configurado correctamente: {actual_dimensions} dimensiones"
            )

        except ImportError:
            logger.error(
                "sentence-transformers no está instalado. Instalarlo con: pip install sentence-transformers"
            )
            raise
        except Exception as e:
            logger.error(f"Error configurando modelo: {e}")
            raise

    def preprocess_text(self, text: Union[str, None]) -> str:
        """
        Preprocesamiento estándar de texto para embeddings

        Args:
            text: Texto a procesar

        Returns:
            Texto preprocesado
        """
        if not text or not isinstance(text, str):
            return ""

        # Limpiar texto
        text = text.strip()

        # Remover saltos de línea múltiples
        text = re.sub(r"\n+", " ", text)

        # Remover espacios múltiples
        text = re.sub(r"\s+", " ", text)

        # Limitar longitud (sentence-transformers tiene límites)
        max_length = 512
        if len(text) > max_length:
            text = text[:max_length]
            logger.warning(f"Texto truncado a {max_length} caracteres")

        return text

    def generate_embedding(self, text: Union[str, None]) -> np.ndarray:
        """
        Generar embedding para un texto

        Args:
            text: Texto de entrada

        Returns:
            Vector de embedding como numpy array
        """
        if not self.model:
            raise RuntimeError("Modelo no configurado")

        # Preprocesar texto
        processed_text = self.preprocess_text(text)

        if not processed_text:
            # Retornar vector de ceros para texto vacío
            logger.warning("Texto vacío, retornando vector de ceros")
            return np.zeros(self.expected_dimensions)

        try:
            # Generar embedding
            embedding = self.model.encode(processed_text)

            # Validar dimensiones
            if len(embedding) != self.expected_dimensions:
                raise ValueError(
                    f"Embedding generado tiene {len(embedding)} dimensiones, esperadas {self.expected_dimensions}"
                )

            return embedding

        except Exception as e:
            logger.error(f"Error generando embedding: {e}")
            raise

    def generate_batch_embeddings(
        self, texts: List[str], batch_size: int = 32
    ) -> List[np.ndarray]:
        """
        Generar embeddings para múltiples textos en lotes

        Args:
            texts: Lista de textos
            batch_size: Tamaño del lote

        Returns:
            Lista de vectores de embedding
        """
        if not self.model:
            raise RuntimeError("Modelo no configurado")

        # Preprocesar todos los textos
        processed_texts = [self.preprocess_text(text) for text in texts]

        embeddings = []

        for i in range(0, len(processed_texts), batch_size):
            batch = processed_texts[i : i + batch_size]

            # Filtrar textos vacíos
            valid_texts = [text if text else " " for text in batch]

            try:
                batch_embeddings = self.model.encode(valid_texts)
                embeddings.extend(batch_embeddings)

                logger.info(
                    f"Procesado lote {i // batch_size + 1}: {len(batch)} textos"
                )

            except Exception as e:
                logger.error(f"Error procesando lote {i // batch_size + 1}: {e}")
                # Procesar individualmente en caso de error
                for text in batch:
                    try:
                        emb = self.generate_embedding(text)
                        embeddings.append(emb)
                    except:  # noqa: E722
                        embeddings.append(np.zeros(self.expected_dimensions))

        return embeddings

    def validate_embedding(self, embedding: np.ndarray) -> Dict[str, Any]:
        """
        Validar un embedding generado

        Args:
            embedding: Vector de embedding

        Returns:
            Diccionario con resultados de validación
        """
        validation_results = {"valid": True, "errors": [], "warnings": [], "stats": {}}

        # Validar tipo
        if not isinstance(embedding, np.ndarray):
            validation_results["valid"] = False
            validation_results["errors"].append("Embedding no es un numpy array")
            return validation_results

        # Validar dimensiones
        if len(embedding) != self.expected_dimensions:
            validation_results["valid"] = False
            validation_results["errors"].append(
                f"Dimensiones incorrectas: {len(embedding)} vs {self.expected_dimensions}"
            )

        # Validar valores
        if np.any(np.isnan(embedding)):
            validation_results["valid"] = False
            validation_results["errors"].append("Contiene valores NaN")

        if np.any(np.isinf(embedding)):
            validation_results["valid"] = False
            validation_results["errors"].append("Contiene valores infinitos")

        # Verificar vector de ceros
        if np.allclose(embedding, 0):
            validation_results["warnings"].append("Embedding es vector de ceros")

        # Estadísticas
        validation_results["stats"] = {
            "dimensions": len(embedding),
            "mean": float(np.mean(embedding)),
            "std": float(np.std(embedding)),
            "min": float(np.min(embedding)),
            "max": float(np.max(embedding)),
            "norm": float(np.linalg.norm(embedding)),
        }

        return validation_results


def run_validation_tests():
    """
    Ejecutar pruebas de validación del modelo
    """
    logger.info("=== INICIANDO VALIDACIÓN DEL MODELO DE EMBEDDINGS ===")

    try:
        # Crear instancia del modelo
        model = EmbeddingModel()

        # Textos de prueba variados
        test_texts = [
            "El presidente anunció nuevas medidas económicas para combatir la inflación.",
            "La empresa tecnológica registró pérdidas en el último trimestre debido a la competencia.",
            "Los científicos descubrieron una nueva especie de bacteria en aguas profundas.",
            "",  # Texto vacío
            "Texto muy corto.",
            "Este es un texto más largo que contiene múltiples oraciones con información detallada sobre diversos temas políticos, económicos y sociales que podrían aparecer en artículos de noticias y que necesita ser procesado por el sistema de embeddings para generar representaciones vectoriales apropiadas.",
        ]

        logger.info("Probando generación individual de embeddings...")

        all_valid = True
        for i, text in enumerate(test_texts):
            logger.info(
                f"Procesando texto {i + 1}: '{text[:50]}{'...' if len(text) > 50 else ''}'"
            )

            # Generar embedding
            embedding = model.generate_embedding(text)

            # Validar
            validation = model.validate_embedding(embedding)

            if validation["valid"]:
                logger.info(
                    f"✅ Embedding válido - dimensiones: {validation['stats']['dimensions']}, norm: {validation['stats']['norm']:.4f}"
                )
            else:
                logger.error(f"❌ Embedding inválido: {validation['errors']}")
                all_valid = False

            if validation["warnings"]:
                logger.warning(f"⚠️  Advertencias: {validation['warnings']}")

        # Probar procesamiento en lotes
        logger.info("Probando procesamiento en lotes...")
        batch_embeddings = model.generate_batch_embeddings(test_texts, batch_size=3)

        if len(batch_embeddings) == len(test_texts):
            logger.info(
                f"✅ Procesamiento en lotes exitoso: {len(batch_embeddings)} embeddings generados"
            )
        else:
            logger.error(
                f"❌ Error en procesamiento en lotes: {len(batch_embeddings)} vs {len(test_texts)}"
            )
            all_valid = False

        # Prueba de determinismo
        logger.info("Probando determinismo...")
        emb1 = model.generate_embedding(test_texts[0])
        emb2 = model.generate_embedding(test_texts[0])

        if np.allclose(emb1, emb2):
            logger.info("✅ Modelo determinista: mismo texto genera mismo embedding")
        else:
            logger.warning(
                "⚠️  Modelo no determinista: mismo texto genera embeddings diferentes"
            )

        # Prueba de similitud semántica
        logger.info("Probando similitud semántica...")
        emb_politico1 = model.generate_embedding(
            "El presidente anunció nuevas políticas económicas"
        )
        emb_politico2 = model.generate_embedding(
            "El mandatario presentó medidas para la economía"
        )
        emb_ciencia = model.generate_embedding(
            "Los científicos descubrieron una nueva galaxia"
        )

        sim_politica = np.dot(emb_politico1, emb_politico2)
        sim_mixta = np.dot(emb_politico1, emb_ciencia)

        if sim_politica > sim_mixta:
            logger.info(
                f"✅ Similitud semántica correcta: política ({sim_politica:.4f}) > mixta ({sim_mixta:.4f})"
            )
        else:
            logger.warning(
                f"⚠️  Similitud semántica inesperada: política ({sim_politica:.4f}) <= mixta ({sim_mixta:.4f})"
            )

        # Resumen final
        if all_valid:
            logger.info("🎉 TODAS LAS VALIDACIONES EXITOSAS")
            logger.info(f"Modelo configurado: {model.model_name}")
            logger.info(f"Dimensiones: {model.expected_dimensions}")
            return True
        else:
            logger.error("❌ ALGUNAS VALIDACIONES FALLARON")
            return False

    except Exception as e:
        logger.error(f"Error durante la validación: {e}")
        return False


def generate_configuration_report():
    """
    Generar reporte de configuración
    """
    config_report = {
        "timestamp": datetime.now().isoformat(),
        "model_name": "all-MiniLM-L6-v2",
        "expected_dimensions": 384,
        "preprocessing_steps": [
            "Limpieza de espacios en blanco",
            "Normalización de saltos de línea",
            "Truncado a 512 caracteres máximo",
            "Manejo de texto vacío (vector de ceros)",
        ],
        "batch_processing": {
            "default_batch_size": 32,
            "error_handling": "Individual fallback en caso de error de lote",
        },
        "validation_criteria": [
            "Dimensiones exactas: 384",
            "Sin valores NaN o infinitos",
            "Detección de vectores de ceros",
            "Estadísticas básicas (media, desviación, norma)",
        ],
    }

    return config_report


if __name__ == "__main__":
    # Ejecutar validación
    success = run_validation_tests()

    # Generar reporte
    report = generate_configuration_report()

    print("\n=== REPORTE DE CONFIGURACIÓN ===")
    print(f"Modelo: {report['model_name']}")
    print(f"Dimensiones: {report['expected_dimensions']}")
    print(f"Validación exitosa: {'Sí' if success else 'No'}")

    if success:
        print("✅ El modelo está listo para generar embeddings para la base de datos")
    else:
        print("❌ Revisar los errores antes de proceder")
