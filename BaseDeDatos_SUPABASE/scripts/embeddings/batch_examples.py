#!/usr/bin/env python3
"""
Ejemplos de uso del framework de procesamiento batch
Tarea 26.2: Implement Batch Processing Framework - Examples

Este script demuestra cómo usar el framework para diferentes tipos de tablas.
"""

import logging
from typing import Dict

from batch_processor import BatchProcessingConfig, EmbeddingBatchProcessor

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def text_combiner_hechos(record: Dict) -> str:
    """
    Combinar campos de texto para tabla 'hechos'

    Args:
        record: Registro de la tabla hechos

    Returns:
        Texto combinado para embedding
    """
    parts = []

    # Contenido principal
    if record.get("contenido"):
        parts.append(record["contenido"])

    # Tipo de hecho
    if record.get("tipo_hecho"):
        parts.append(f"Tipo: {record['tipo_hecho']}")

    # Países (si es una lista)
    if record.get("pais"):
        paises = record["pais"]
        if isinstance(paises, list):
            parts.append(f"Países: {', '.join(paises)}")
        else:
            parts.append(f"País: {paises}")

    # Etiquetas
    if record.get("etiquetas"):
        etiquetas = record["etiquetas"]
        if isinstance(etiquetas, list):
            parts.append(f"Etiquetas: {', '.join(etiquetas)}")

    return " | ".join(parts)


def text_combiner_entidades(record: Dict) -> str:
    """
    Combinar campos de texto para tabla 'entidades'

    Args:
        record: Registro de la tabla entidades

    Returns:
        Texto combinado para embedding
    """
    parts = []

    # Nombre principal
    if record.get("nombre"):
        parts.append(record["nombre"])

    # Tipo de entidad
    if record.get("tipo"):
        parts.append(f"Tipo: {record['tipo']}")

    # Descripción
    if record.get("descripcion"):
        parts.append(record["descripcion"])

    # Alias
    if record.get("alias"):
        alias = record["alias"]
        if isinstance(alias, list) and alias:
            parts.append(f"También conocido como: {', '.join(alias)}")

    return " | ".join(parts)


def text_combiner_hilos_narrativos(record: Dict) -> str:
    """
    Combinar campos de texto para tabla 'hilos_narrativos'

    Args:
        record: Registro de la tabla hilos_narrativos

    Returns:
        Texto combinado para embedding
    """
    parts = []

    # Título
    if record.get("titulo"):
        parts.append(record["titulo"])

    # Descripción principal
    if record.get("descripcion"):
        parts.append(record["descripcion"])

    # Descripción curada
    if record.get("descripcion_hilo_curada"):
        parts.append(f"Enfoque editorial: {record['descripcion_hilo_curada']}")

    # Puntos clave
    if record.get("puntos_clave_novedades"):
        parts.append(f"Novedades: {record['puntos_clave_novedades']}")

    # Etiquetas principales
    if record.get("etiquetas_principales"):
        etiquetas = record["etiquetas_principales"]
        if isinstance(etiquetas, list) and etiquetas:
            parts.append(f"Temas: {', '.join(etiquetas)}")

    return " | ".join(parts)


def text_combiner_citas_textuales(record: Dict) -> str:
    """
    Combinar campos de texto para tabla 'citas_textuales'

    Args:
        record: Registro de la tabla citas_textuales

    Returns:
        Texto combinado para embedding
    """
    parts = []

    # Cita principal
    if record.get("cita"):
        parts.append(record["cita"])

    # Contexto
    if record.get("contexto"):
        parts.append(f"Contexto: {record['contexto']}")

    # Etiquetas
    if record.get("etiquetas"):
        etiquetas = record["etiquetas"]
        if isinstance(etiquetas, list) and etiquetas:
            parts.append(f"Etiquetas: {', '.join(etiquetas)}")

    return " | ".join(parts)


def text_combiner_fragmentos_extensos(record: Dict) -> str:
    """
    Combinar campos de texto para tabla 'fragmentos_extensos'

    Args:
        record: Registro de la tabla fragmentos_extensos

    Returns:
        Texto combinado para embedding
    """
    parts = []

    # Título de sección (si existe)
    if record.get("titulo_seccion"):
        parts.append(f"Sección: {record['titulo_seccion']}")

    # Contenido principal
    if record.get("contenido"):
        parts.append(record["contenido"])

    return " | ".join(parts)


def text_combiner_datos_cuantitativos(record: Dict) -> str:
    """
    Combinar campos de texto para tabla 'datos_cuantitativos'

    Args:
        record: Registro de la tabla datos_cuantitativos

    Returns:
        Texto combinado para embedding
    """
    parts = []

    # Indicador
    if record.get("indicador"):
        parts.append(record["indicador"])

    # Categoría
    if record.get("categoria"):
        parts.append(f"Categoría: {record['categoria']}")

    # Valor y unidad
    if record.get("valor_numerico") and record.get("unidad"):
        parts.append(f"Valor: {record['valor_numerico']} {record['unidad']}")

    # Ámbito geográfico
    if record.get("ambito_geografico"):
        ambito = record["ambito_geografico"]
        if isinstance(ambito, list):
            parts.append(f"Ámbito: {', '.join(ambito)}")

    # Fuente específica
    if record.get("fuente_especifica"):
        parts.append(f"Fuente: {record['fuente_especifica']}")

    # Notas
    if record.get("notas"):
        parts.append(f"Notas: {record['notas']}")

    return " | ".join(parts)


def demo_process_single_table():
    """
    Demostración de procesamiento de una tabla simple
    """
    logger.info("=== DEMO: Procesamiento de tabla simple ===")

    # Configuración conservadora para demo
    config = BatchProcessingConfig(
        batch_size=5,
        max_retries=2,
        enable_progress_bar=True,
        transaction_size=2,
        validate_embeddings=True,
    )

    processor = EmbeddingBatchProcessor(config)

    try:
        if processor.setup():
            logger.info("Procesando tabla 'hilos_narrativos' (simple)...")

            stats = processor.process_table(
                table_name="hilos_narrativos", text_column="titulo", id_column="id"
            )

            logger.info(f"Demo completada: {stats.success_rate:.1f}% éxito")
        else:
            logger.error("No se pudo configurar el procesador")

    except Exception as e:
        logger.error(f"Error en demo: {e}")

    finally:
        processor.cleanup()


def demo_process_complex_table():
    """
    Demostración de procesamiento de tabla compleja con text_combiner
    """
    logger.info("=== DEMO: Procesamiento de tabla compleja ===")

    config = BatchProcessingConfig(
        batch_size=3,
        max_retries=2,
        enable_progress_bar=True,
        transaction_size=1,
        validate_embeddings=True,
    )

    processor = EmbeddingBatchProcessor(config)

    try:
        if processor.setup():
            logger.info("Procesando tabla 'entidades' (compleja)...")

            stats = processor.process_table(
                table_name="entidades",
                text_column="nombre",  # Columna principal
                id_column="id",
                additional_columns=["tipo", "descripcion", "alias"],
                text_combiner=text_combiner_entidades,
            )

            logger.info(f"Demo completada: {stats.success_rate:.1f}% éxito")
        else:
            logger.error("No se pudo configurar el procesador")

    except Exception as e:
        logger.error(f"Error en demo: {e}")

    finally:
        processor.cleanup()


def get_table_processing_config():
    """
    Obtener configuraciones específicas para cada tabla

    Returns:
        Diccionario con configuraciones por tabla
    """
    return {
        "hechos": {
            "text_column": "contenido",
            "additional_columns": ["tipo_hecho", "pais", "etiquetas"],
            "text_combiner": text_combiner_hechos,
            "batch_size": 20,  # Tabla grande
        },
        "entidades": {
            "text_column": "nombre",
            "additional_columns": ["tipo", "descripcion", "alias"],
            "text_combiner": text_combiner_entidades,
            "batch_size": 10,  # Tabla mediana
        },
        "hilos_narrativos": {
            "text_column": "titulo",
            "additional_columns": [
                "descripcion",
                "descripcion_hilo_curada",
                "puntos_clave_novedades",
                "etiquetas_principales",
            ],
            "text_combiner": text_combiner_hilos_narrativos,
            "batch_size": 5,  # Tabla pequeña
        },
        "fragmentos_extensos": {
            "text_column": "contenido",
            "additional_columns": ["titulo_seccion"],
            "text_combiner": text_combiner_fragmentos_extensos,
            "batch_size": 5,  # Tabla pequeña
        },
        "citas_textuales": {
            "text_column": "cita",
            "additional_columns": ["contexto", "etiquetas"],
            "text_combiner": text_combiner_citas_textuales,
            "batch_size": 5,  # Tabla pequeña
        },
        "datos_cuantitativos": {
            "text_column": "indicador",
            "additional_columns": [
                "categoria",
                "valor_numerico",
                "unidad",
                "ambito_geografico",
                "fuente_especifica",
                "notas",
            ],
            "text_combiner": text_combiner_datos_cuantitativos,
            "batch_size": 10,  # Tabla potencialmente mediana
        },
    }


if __name__ == "__main__":
    logger.info("🧪 Ejecutando demos del framework de procesamiento batch")

    # Demo simple
    demo_process_single_table()

    print("\n" + "=" * 50 + "\n")

    # Demo complejo
    demo_process_complex_table()

    print("\n" + "=" * 50 + "\n")

    # Mostrar configuraciones disponibles
    configs = get_table_processing_config()
    logger.info("📋 Configuraciones disponibles para tablas:")
    for table, config in configs.items():
        logger.info(
            f"  {table}: batch_size={config['batch_size']}, combiner={'Sí' if config['text_combiner'] else 'No'}"
        )
