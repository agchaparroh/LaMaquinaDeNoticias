#!/usr/bin/env python3
"""
Script de prueba para verificar el funcionamiento de la RPC insertar_fragmento_completo
"""

import os
import sys
from datetime import datetime

from loguru import logger

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from services.supabase_service import get_supabase_service
from utils.error_handling import ErrorPhase  # noqa: F401

# Configurar logging detallado
logger.remove()
logger.add(sys.stderr, level="DEBUG")


def test_rpc_simple():
    """Prueba básica de la RPC con datos mínimos"""
    logger.info("=== Iniciando prueba de RPC insertar_fragmento_completo ===")

    try:
        # Obtener servicio
        service = get_supabase_service()
        logger.info("Servicio Supabase inicializado")

        # Crear payload mínimo de prueba
        payload_minimo = {
            # Campos requeridos para fragmento
            "indice_secuencial_fragmento": 1,
            "contenido_texto_original_fragmento": "Este es un fragmento de prueba para verificar la RPC.",
            "fecha_procesamiento_pipeline_fragmento": datetime.now().isoformat(),
            "estado_procesamiento_final_fragmento": "EXITOSO",
            # Listas vacías para elementos extraídos
            "hechos_extraidos": [
                {
                    "texto_hecho": "Hecho de prueba 1",
                    "certeza": 0.9,
                    "fuente": "prueba",
                    "contexto": "contexto de prueba",
                }
            ],
            "entidades_autonomas": [
                {
                    "texto_entidad": "Entidad Prueba",
                    "tipo_entidad": "ORGANIZACION",
                    "confianza": 0.85,
                    "contexto": "contexto entidad",
                }
            ],
            "citas_textuales_extraidas": [],
            "datos_cuantitativos_extraidos": [],
            "relaciones_hechos": [],
            "relaciones_entidades": [],
            "contradicciones_detectadas": [],
        }

        logger.info("Payload de prueba creado")
        logger.debug(f"Payload: {payload_minimo}")

        # Llamar RPC directamente
        logger.info("Llamando RPC insertar_fragmento_completo...")
        resultado = service.insertar_fragmento_completo(payload_minimo)

        # Analizar resultado
        if resultado:
            logger.success(f"RPC ejecutada exitosamente")  # noqa: F541
            logger.info(f"Resultado completo: {resultado}")
            logger.info(f"Fragmento ID: {resultado.get('fragmento_id')}")
            logger.info(f"Hechos insertados: {resultado.get('hechos_insertados')}")
            logger.info(
                f"Entidades insertadas: {resultado.get('entidades_insertadas')}"
            )
        else:
            logger.error("RPC retornó None - verificar logs anteriores")

    except Exception as e:
        logger.error(f"Error en prueba: {type(e).__name__}: {str(e)}")
        logger.exception("Traceback completo:")


def test_rpc_con_client_directo():
    """Prueba usando el cliente Supabase directamente"""
    logger.info("\n=== Prueba directa con cliente Supabase ===")

    try:
        service = get_supabase_service()
        client = service.get_client()

        # Payload simple con documento_id y fragmento_id incluidos
        payload = {
            "datos_json": {
                "documento_id": 999999,  # ID ficticio numérico
                "fragmento_id": 999999,  # ID ficticio numérico
                "indice_secuencial_fragmento": 99,
                "contenido_texto_original_fragmento": "Prueba directa del cliente",
                "fecha_procesamiento_pipeline_fragmento": datetime.now().isoformat(),
                "estado_procesamiento_final_fragmento": "PRUEBA",
                "hechos_extraidos": [],
                "entidades_autonomas": [],
                "citas_textuales_extraidas": [],
                "datos_cuantitativos_extraidos": [],
                "relaciones_hechos": [],
                "relaciones_entidades": [],
                "contradicciones_detectadas": [],
            }
        }

        logger.info("Ejecutando RPC directamente...")
        response = client.rpc("insertar_fragmento_completo", payload).execute()

        logger.info(f"Response type: {type(response)}")
        logger.info(f"Response data: {response.data}")
        logger.info(f"Response data type: {type(response.data)}")

        if hasattr(response, "error"):
            logger.warning(f"Response error: {response.error}")

    except Exception as e:
        logger.error(f"Error en prueba directa: {type(e).__name__}: {str(e)}")
        logger.exception("Traceback completo:")


if __name__ == "__main__":
    # Ejecutar pruebas
    test_rpc_simple()
    test_rpc_con_client_directo()

    logger.info("\n=== Pruebas completadas ===")
