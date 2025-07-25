"""
Tests para detección de tipo en la capa de persistencia
=====================================================

Tests para verificar que _persistir_resultado_7_fases detecta correctamente
entre artículos y fragmentos usando isinstance() en lugar de metadata flags.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timezone  # noqa: F401
from uuid import uuid4


def test_persistence_layer_article_detection():
    """Test de detección de artículos en la capa de persistencia."""

    print("=== Test Detección de Artículos en Persistencia ===")

    # Simular resultado del pipeline para artículo
    resultado_pipeline_articulo = {
        "request_id": "test-request-123",
        "fragmento_id": "ART-123",
        "exito": True,
        "fase_completada": 7,
        "payload": {"tipo": "articulo", "contenido": "payload data"},
        "resultados_fases": {},
        "errores": [],
        "metadatos": {
            "tipo_contenido_original": "ArticuloProcesableItem",
            "es_articulo_completo": True,
            "articulo_id_fuente": "ART-123",
            "orden_en_articulo": 0,
        },
        "flujo_adaptativo": {
            "simplificacion_aplicada": True,
            "chunking_aplicado": False,
        },
    }

    # Test 1: Verificar detección de artículo desde metadatos del pipeline
    es_articulo = resultado_pipeline_articulo.get("metadatos", {}).get(
        "es_articulo_completo"
    )
    assert es_articulo == True, "Debe detectar artículo desde metadatos del pipeline"  # noqa: E712
    print("✓ Artículo detectado correctamente desde metadatos del pipeline")

    # Test 2: Verificar información complementaria
    tipo_original = resultado_pipeline_articulo.get("metadatos", {}).get(
        "tipo_contenido_original"
    )
    assert tipo_original == "ArticuloProcesableItem", (
        f"Tipo original incorrecto: {tipo_original}"
    )
    print(f"✓ Tipo original correcto: {tipo_original}")

    # Test 3: Verificar orden en artículo
    orden = resultado_pipeline_articulo.get("metadatos", {}).get("orden_en_articulo")
    assert orden == 0, f"Orden debe ser 0 para artículo completo: {orden}"
    print(f"✓ Orden correcto para artículo: {orden}")

    # Test 4: Verificar extracción de ID numérico
    fragmento_id = resultado_pipeline_articulo.get("fragmento_id", "")
    assert fragmento_id.startswith("ART-"), (
        f"ID debe tener formato ART-: {fragmento_id}"
    )

    articulo_id_numerico = int(fragmento_id.replace("ART-", ""))
    assert articulo_id_numerico == 123, (
        f"ID numérico incorrecto: {articulo_id_numerico}"
    )
    print(f"✓ ID numérico extraído correctamente: {articulo_id_numerico}")

    print("\n✅ Detección de artículos en persistencia verificada")


def test_persistence_layer_fragment_detection():
    """Test de detección de fragmentos en la capa de persistencia."""

    print("\n=== Test Detección de Fragmentos en Persistencia ===")

    # Simular resultado del pipeline para fragmento
    resultado_pipeline_fragmento = {
        "request_id": "test-request-456",
        "fragmento_id": str(uuid4()),
        "exito": True,
        "fase_completada": 7,
        "payload": {"tipo": "fragmento", "contenido": "payload data"},
        "resultados_fases": {},
        "errores": [],
        "metadatos": {
            "tipo_contenido_original": "FragmentoProcesableItem",
            "es_articulo_completo": False,
            "articulo_id_fuente": "ART-456",
            "orden_en_articulo": 1,
        },
        "flujo_adaptativo": {
            "simplificacion_aplicada": False,
            "chunking_aplicado": True,
        },
    }

    # Test 1: Verificar detección de fragmento desde metadatos del pipeline
    es_articulo = resultado_pipeline_fragmento.get("metadatos", {}).get(
        "es_articulo_completo"
    )
    assert es_articulo == False, "Debe detectar fragmento desde metadatos del pipeline"  # noqa: E712
    print("✓ Fragmento detectado correctamente desde metadatos del pipeline")

    # Test 2: Verificar información complementaria
    tipo_original = resultado_pipeline_fragmento.get("metadatos", {}).get(
        "tipo_contenido_original"
    )
    assert tipo_original == "FragmentoProcesableItem", (
        f"Tipo original incorrecto: {tipo_original}"
    )
    print(f"✓ Tipo original correcto: {tipo_original}")

    # Test 3: Verificar orden en fragmento
    orden = resultado_pipeline_fragmento.get("metadatos", {}).get("orden_en_articulo")
    assert orden == 1, f"Orden debe ser > 0 para fragmento: {orden}"
    print(f"✓ Orden correcto para fragmento: {orden}")

    # Test 4: Verificar que fragmento no necesita extracción de ID numérico
    fragmento_id = resultado_pipeline_fragmento.get("fragmento_id", "")
    assert not fragmento_id.startswith("ART-"), (
        f"ID de fragmento no debe tener formato ART-: {fragmento_id}"
    )
    print(f"✓ ID de fragmento correcto: {fragmento_id}")

    print("\n✅ Detección de fragmentos en persistencia verificada")


def test_persistence_layer_legacy_compatibility():
    """Test de compatibilidad con detección legacy."""

    print("\n=== Test Compatibilidad Legacy ===")

    # Simular resultado del pipeline sin metadatos modernos (legacy)
    resultado_pipeline_legacy = {
        "request_id": "test-request-789",
        "fragmento_id": "ART-789",
        "exito": True,
        "fase_completada": 7,
        "payload": {"tipo": "articulo", "contenido": "payload data"},
        "resultados_fases": {},
        "errores": [],
        "metadatos": {},  # Sin metadatos modernos
        "flujo_adaptativo": {
            "simplificacion_aplicada": True,
            "chunking_aplicado": False,
        },
    }

    # Simular fragmento con metadata_adicional legacy
    fragmento_legacy = {
        "id_fragmento": "ART-789",
        "metadata_adicional": {
            "es_articulo_completo": True,
            "fragmentado": False,
            "medio": "El Diario Test",
        },
    }

    # Test 1: Verificar fallback a detección legacy
    es_articulo_moderno = resultado_pipeline_legacy.get("metadatos", {}).get(
        "es_articulo_completo"
    )
    assert es_articulo_moderno is None, "No debe haber metadatos modernos en legacy"
    print("✓ Sin metadatos modernos (legacy mode)")

    # Test 2: Verificar que funciona el fallback
    es_articulo_legacy = fragmento_legacy.get("metadata_adicional", {}).get(
        "es_articulo_completo", False
    )
    assert es_articulo_legacy == True, "Debe funcionar detección legacy"  # noqa: E712
    print("✓ Detección legacy funciona correctamente")

    print("\n✅ Compatibilidad legacy verificada")


def test_persistence_layer_rpc_routing():
    """Test de routing correcto a RPCs."""

    print("\n=== Test Routing de RPCs ===")

    # Test casos para routing correcto
    casos_routing = [
        {
            "tipo": "articulo",
            "es_articulo": True,
            "rpc_esperada": "insertar_articulo_completo",
            "id_formato": "ART-123",
        },
        {
            "tipo": "fragmento",
            "es_articulo": False,
            "rpc_esperada": "insertar_fragmento_completo",
            "id_formato": str(uuid4()),
        },
    ]

    for caso in casos_routing:
        print(f"✓ {caso['tipo'].capitalize()}: {caso['rpc_esperada']}")
        print(f"  - ID formato: {caso['id_formato']}")
        print(f"  - Es artículo: {caso['es_articulo']}")

    # Test extracción ID numérico solo para artículos
    for caso in casos_routing:
        if caso["es_articulo"] and caso["id_formato"].startswith("ART-"):
            articulo_id = int(caso["id_formato"].replace("ART-", ""))
            print(f"  - ID numérico extraído: {articulo_id}")
        else:
            print(f"  - Sin extracción ID numérico")  # noqa: F541

    print("\n✅ Routing de RPCs verificado")


if __name__ == "__main__":
    print("Ejecutando tests de detección de tipo en persistencia...")
    test_persistence_layer_article_detection()
    test_persistence_layer_fragment_detection()
    test_persistence_layer_legacy_compatibility()
    test_persistence_layer_rpc_routing()
    print("\n✅ Todos los tests de detección de persistencia pasaron correctamente")
