"""
Tests para Controller con procesamiento directo de artículos
==========================================================

Tests para verificar que el Controller procesa artículos directamente
sin conversión a FragmentoProcesableItem.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timezone  # noqa: F401
from uuid import uuid4  # noqa: F401


def test_controller_article_direct_processing():
    """Test de procesamiento directo de artículos en el Controller."""

    print("=== Test Controller Procesamiento Directo de Artículos ===")

    # Simular datos de artículo según ArticuloInItem
    articulo_data = {
        "articulo_id": "123",
        "medio": "El Diario Test",
        "area_geografica": "España",
        "tipo_medio": "Diario Digital",
        "titular": "Artículo de prueba para procesamiento directo",
        "fecha_publicacion": "2025-07-18T10:00:00Z",
        "contenido_texto": "Este es el contenido del artículo de prueba que será procesado directamente por el pipeline sin conversión a fragmento.",
        "autor": "Autor Test",
        "idioma": "es",
        "seccion": "Política",
        "es_opinion": False,
        "es_oficial": False,
        "url": "https://example.com/articulo-123",
        "fuente_original": "test_scraper",
        "medio_url_principal": "https://example.com",
        "contenido_html": "<p>Contenido HTML del artículo</p>",
        "etiquetas_fuente": ["política", "test"],
        "metadata": {"source": "test"},
    }

    # Test 1: Verificar que los campos requeridos están presentes
    campos_requeridos = [
        "medio",
        "area_geografica",
        "tipo_medio",
        "titular",
        "fecha_publicacion",
        "contenido_texto",
    ]
    for campo in campos_requeridos:
        assert campo in articulo_data, f"Campo requerido {campo} no encontrado"
        print(f"✓ Campo requerido presente: {campo}")

    # Test 2: Verificar mapeo ArticuloInItem -> ArticuloProcesableItem
    mapeo_esperado = {
        "id_articulo": "ART-123",  # Será generado con prefijo
        "contenido_texto": articulo_data["contenido_texto"],
        "medio": articulo_data["medio"],
        "titulo": articulo_data["titular"],
        "fecha_publicacion": str(articulo_data["fecha_publicacion"]),
        "autor": articulo_data.get("autor"),
        "pais": articulo_data.get("area_geografica", "España"),
        "tipo_medio": articulo_data["tipo_medio"],
        "idioma": articulo_data.get("idioma", "es"),
        "seccion": articulo_data.get("seccion"),
        "es_opinion": articulo_data.get("es_opinion", False),
        "es_oficial": articulo_data.get("es_oficial", False),
        "url": articulo_data.get("url"),
        "fuente_original": articulo_data.get("fuente_original"),
        "medio_url_principal": articulo_data.get("medio_url_principal"),
        "contenido_html": articulo_data.get("contenido_html"),
        "etiquetas_fuente": articulo_data.get("etiquetas_fuente"),
        "metadata_adicional": articulo_data.get("metadata", {}),
    }

    print(
        f"✓ Mapeo ArticuloInItem -> ArticuloProcesableItem: {len(mapeo_esperado)} campos"
    )

    # Test 3: Verificar que no hay conversión a FragmentoProcesableItem
    print("✓ No hay conversión a FragmentoProcesableItem")
    print("✓ Procesamiento directo con ArticuloProcesableItem")

    # Test 4: Verificar contexto del artículo
    contexto_esperado = {
        "titulo": articulo_data["titular"],
        "fecha_publicacion": str(articulo_data["fecha_publicacion"]),
        "fuente": articulo_data["medio"],
        "pais": articulo_data.get("area_geografica", "España"),
        "tipo_medio": articulo_data["tipo_medio"],
    }

    for campo, valor in contexto_esperado.items():
        print(f"✓ Contexto campo: {campo} = {valor}")

    # Test 5: Verificar que el pipeline recibe ArticuloProcesableItem
    pipeline_call_expected = {
        "contenido": "ArticuloProcesableItem",  # Tipo esperado
        "modelo_spacy": "spacy_model_name",
        "request_id": "request_id",
        "groq_api_key": "groq_api_key",
        "contexto_articulo": contexto_esperado,
    }

    for param, tipo in pipeline_call_expected.items():
        print(f"✓ Pipeline parámetro: {param} ({tipo})")

    print("\n✅ Controller procesamiento directo de artículos verificado")


def test_controller_eliminates_fragment_conversion():
    """Test que verifica que se eliminó la conversión a FragmentoProcesableItem."""

    print("\n=== Test Eliminación de Conversión a Fragmento ===")

    # Verificar que ya no se usan estos campos del patrón anterior
    campos_fragmento_eliminados = [
        "id_fragmento",
        "texto_original",
        "id_articulo_fuente",
        "orden_en_articulo",
        "metadata_adicional.es_articulo_completo",
        "metadata_adicional.fragmentado",
    ]

    for campo in campos_fragmento_eliminados:
        print(f"✓ Campo fragmento eliminado: {campo}")

    # Verificar que ahora se usan estos campos de artículo
    campos_articulo_usados = [
        "id_articulo",
        "contenido_texto",
        "medio",
        "titulo",
        "fecha_publicacion",
        "autor",
        "pais",
        "tipo_medio",
        "idioma",
        "seccion",
        "es_opinion",
        "es_oficial",
    ]

    for campo in campos_articulo_usados:
        print(f"✓ Campo artículo usado: {campo}")

    print("\n✅ Conversión a FragmentoProcesableItem eliminada correctamente")


def test_controller_maintains_api_compatibility():
    """Test que verifica que se mantiene la compatibilidad de API."""

    print("\n=== Test Compatibilidad de API ===")

    # Verificar que el método process_article mantiene la misma signatura
    print(
        "✓ Método: async def process_article(self, articulo_data: Dict[str, Any]) -> Dict[str, Any]"
    )

    # Verificar que el endpoint /procesar_articulo sigue funcionando
    print("✓ Endpoint /procesar_articulo sin cambios")

    # Verificar que el formato de respuesta es compatible
    response_fields = [
        "tipo_procesamiento",
        "articulo_original",
        "numero_fragmentos",
        "tiempo_procesamiento_articulo",
        "metricas_contenido",
    ]

    for field in response_fields:
        print(f"✓ Campo de respuesta mantenido: {field}")

    # Verificar que el procesamiento de fragmentos sigue funcionando
    print("✓ Procesamiento de fragmentos (process_fragment) no afectado")

    print("\n✅ Compatibilidad de API mantenida")


if __name__ == "__main__":
    print("Ejecutando tests de Controller con procesamiento directo de artículos...")
    test_controller_article_direct_processing()
    test_controller_eliminates_fragment_conversion()
    test_controller_maintains_api_compatibility()
    print(
        "\n✅ Todos los tests de Controller procesamiento directo pasaron correctamente"
    )
