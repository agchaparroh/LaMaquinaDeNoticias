#!/usr/bin/env python
"""
Script de prueba para verificar la alineación de campos de entidades con el RPC.

Este script crea datos de prueba con campos alineados al RPC actualizado
y verifica que se persistan correctamente en Supabase.
"""

import json  # noqa: F401
import os
import sys
from datetime import datetime

# Añadir el directorio del módulo al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src/module_pipeline"))

from src.services.payload_builder import PayloadBuilder
from src.services.supabase_service import SupabaseService


def crear_entidades_prueba():
    """Crea entidades de prueba con campos alineados al RPC."""
    return [
        {
            # Campos principales alineados con RPC
            "id": "ENT-TEST-001",
            "nombre": "Juan Pérez González",
            "tipo": "PERSONA",
            "descripcion": "Ministro de Economía del país",
            "alias": ["Juan Pérez", "Ministro Pérez"],
            "relevancia": 9,  # Escala 1-10
            "metadata": {
                "cargo": "Ministro de Economía",
                "periodo": "2023-2025",
                "partido_politico": "Partido Democrático",
            },
            "id_temporal": "1",
            # Campos adicionales para compatibilidad con procesamiento
            "id_entidad": 1,
            "texto_entidad": "Juan Pérez González",
            "tipo_entidad": "PERSONA",
            "relevancia_entidad": 0.9,
            "metadata_entidad": {
                "tipo": "PERSONA",
                "alias": ["Juan Pérez", "Ministro Pérez"],
                "descripcion_estructurada": ["Ministro de Economía del país"],
            },
        },
        {
            # Campos principales alineados con RPC
            "id": "ENT-TEST-002",
            "nombre": "Ministerio de Economía",
            "tipo": "INSTITUCION",
            "descripcion": "Institución gubernamental encargada de la política económica",
            "alias": ["MinEconomía", "MINECO"],
            "relevancia": 8,
            "metadata": {
                "tipo_institucion": "Ministerio",
                "pais": "España",
                "fundacion": "1977",
            },
            "id_temporal": "2",
            # Campos adicionales para compatibilidad
            "id_entidad": 2,
            "texto_entidad": "Ministerio de Economía",
            "tipo_entidad": "INSTITUCION",
            "relevancia_entidad": 0.8,
            "metadata_entidad": {
                "tipo": "INSTITUCION",
                "alias": ["MinEconomía", "MINECO"],
            },
        },
        {
            # Campos principales alineados con RPC
            "id": "ENT-TEST-003",
            "nombre": "Madrid",
            "tipo": "LUGAR",
            "descripcion": "Capital de España",
            "alias": ["Villa de Madrid"],
            "relevancia": 7,
            "metadata": {
                "tipo_lugar": "Ciudad",
                "pais": "España",
                "poblacion": "3.3 millones",
            },
            "id_temporal": "3",
            # Campos adicionales para compatibilidad
            "id_entidad": 3,
            "texto_entidad": "Madrid",
            "tipo_entidad": "LUGAR",
            "relevancia_entidad": 0.7,
            "metadata_entidad": {"tipo": "LUGAR"},
        },
    ]


def main():
    """Función principal para probar la persistencia de entidades."""
    print("=== TEST DE ALINEACIÓN DE ENTIDADES CON RPC ===\n")

    # Inicializar servicios
    print("1. Inicializando servicios...")
    supabase_service = SupabaseService()
    payload_builder = PayloadBuilder()

    # Crear datos de prueba
    print("2. Creando datos de prueba con campos alineados...")
    entidades_prueba = crear_entidades_prueba()

    print(f"   - Creadas {len(entidades_prueba)} entidades de prueba")
    for ent in entidades_prueba:
        print(f"   - {ent['nombre']} ({ent['tipo']})")

    # Crear payload completo
    print("\n3. Construyendo payload para RPC...")

    # Metadatos del artículo
    metadatos_articulo = {
        "url": "https://ejemplo.com/noticia-test-entidades",
        "titular": "Prueba de Alineación de Entidades con RPC",
        "medio": "Test News",
        "area_geografica": "España",
        "tipo_medio": "Digital",
        "fecha_publicacion": datetime.now().isoformat(),
        "autor": "Script de Prueba",
        "idioma_original": "es",
        "seccion": "Tecnología",
        "es_opinion": False,
        "es_oficial": False,
        "contenido_texto_original": "Contenido de prueba para verificar la alineación de campos de entidades.",
    }

    # Datos de procesamiento
    procesamiento_articulo = {
        "resumen_generado_pipeline": "Artículo de prueba para verificar campos de entidades",
        "palabras_clave_generadas": ["prueba", "entidades", "RPC"],
        "sentimiento_general_articulo": "neutral",
        "estado_procesamiento_final_pipeline": "completado_ok",
        "version_pipeline_aplicada": "1.0.0-test",
        "fecha_ingesta_sistema": datetime.now().isoformat(),
        "fecha_procesamiento_pipeline": datetime.now().isoformat(),
    }

    try:
        # Construir payload
        payload = payload_builder.construir_payload_articulo(
            metadatos_articulo_data=metadatos_articulo,
            procesamiento_articulo_data=procesamiento_articulo,
            entidades_autonomas_data=entidades_prueba,
        )

        print("   ✓ Payload construido exitosamente")

        # Mostrar estructura del payload
        print("\n4. Verificando estructura del payload...")
        payload_dict = payload.model_dump()

        if "entidades_autonomas" in payload_dict:
            print(
                f"   - Entidades en payload: {len(payload_dict['entidades_autonomas'])}"
            )

            # Verificar primera entidad
            if payload_dict["entidades_autonomas"]:
                primera_entidad = payload_dict["entidades_autonomas"][0]
                print("\n   Primera entidad en payload:")
                print(f"   - id: {primera_entidad.get('id')}")
                print(f"   - nombre: {primera_entidad.get('nombre')}")
                print(f"   - tipo: {primera_entidad.get('tipo')}")
                print(f"   - relevancia: {primera_entidad.get('relevancia')}")
                print(f"   - metadata: {primera_entidad.get('metadata')}")

                # Verificar que NO existan campos con sufijos
                campos_incorrectos = []
                if "nombre_entidad" in primera_entidad:
                    campos_incorrectos.append("nombre_entidad")
                if "tipo_entidad" in primera_entidad:
                    campos_incorrectos.append("tipo_entidad")
                if "relevancia_entidad_articulo" in primera_entidad:
                    campos_incorrectos.append("relevancia_entidad_articulo")
                if "metadata_entidad" in primera_entidad:
                    campos_incorrectos.append("metadata_entidad")

                if campos_incorrectos:
                    print(
                        f"\n   ⚠️  ADVERTENCIA: Se encontraron campos con sufijos antiguos: {campos_incorrectos}"
                    )
                else:
                    print("\n   ✓ Campos correctamente alineados (sin sufijos)")

        # Persistir en Supabase
        print("\n5. Persistiendo en Supabase...")

        resultado = supabase_service.persistir_articulo_completo_rpc(
            payload_articulo=payload
        )

        if resultado["success"]:
            print("   ✓ Persistencia exitosa!")
            print(f"   - ID del artículo: {resultado['article_id']}")

            # Verificar entidades persistidas
            if "entity_count" in resultado:
                print(f"   - Entidades persistidas: {resultado['entity_count']}")
        else:
            print(
                f"   ✗ Error en persistencia: {resultado.get('error', 'Error desconocido')}"
            )

    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
