#!/usr/bin/env python3
"""
Test simple para verificar alineación de citas textuales con RPC
No requiere dependencias externas al proyecto
"""

import json
import sys
from datetime import datetime

# Configurar path para imports
sys.path.append("/home/ec2-user/projects/LaMaquinaDeNoticias/src/module_pipeline")

# Imports de modelos internos
from src.models.metadatos import MetadatosCita
from src.models.persistencia import CitaTextualExtraidaItem
from src.models.procesamiento import CitaTextual


def test_cita_textual_extraida_item():
    """Prueba la estructura de CitaTextualExtraidaItem con campos esperados por RPC"""
    print("\n=== TEST: CitaTextualExtraidaItem ===")

    # Crear instancia con campos esperados por RPC
    cita_item = CitaTextualExtraidaItem(
        id_temporal_cita="CITA-001",
        cita="Implementaremos medidas inmediatas para controlar la inflación",
        id_temporal_entidad_emisora="ENT-003",
        id_temporal_hecho_contexto="HEC-002",
        fecha_cita="2023-03-14T10:30:00Z",
        contexto="Durante rueda de prensa matinal",
        relevancia=4,
        nombre_entidad_emisora="Nicolás Maduro",
    )

    # Verificar que los campos tienen los nombres correctos
    campos_correctos = {
        "id_temporal_cita": "CITA-001",
        "cita": "Implementaremos medidas inmediatas para controlar la inflación",
        "id_temporal_entidad_emisora": "ENT-003",
        "id_temporal_hecho_contexto": "HEC-002",
        "fecha_cita": "2023-03-14T10:30:00Z",
        "contexto": "Durante rueda de prensa matinal",
        "relevancia": 4,
    }

    print("✓ Campos esperados por RPC:")
    for campo, valor_esperado in campos_correctos.items():
        valor_actual = getattr(cita_item, campo, None)
        if valor_actual == valor_esperado:
            print(f"  ✓ {campo}: {valor_actual}")
        else:
            print(f"  ✗ {campo}: esperado={valor_esperado}, actual={valor_actual}")

    # Probar que los campos antiguos ya NO existen
    campos_antiguos = [
        "texto_cita",
        "contexto_cita",
        "relevancia_cita",
        "cargo_entidad_emisora",
    ]
    print("\n✓ Verificando que campos antiguos NO existen:")
    for campo in campos_antiguos:
        if hasattr(cita_item, campo):
            print(f"  ✗ ERROR: Campo antiguo '{campo}' aún existe!")
        else:
            print(f"  ✓ Campo antiguo '{campo}' correctamente removido")

    return cita_item


def test_pipeline_coordinator_mapping():
    """Simula el mapeo que hace pipeline_coordinator.py"""
    print("\n=== TEST: Pipeline Coordinator Mapping ===")

    # Crear una cita de prueba como vendría de fase_6
    # Nota: MetadatosCita tiene campos adicionales no documentados en el modelo
    metadata = MetadatosCita(
        fecha="2023-03-14", relevancia=4, contexto="Durante rueda de prensa matinal"
    )

    # Añadir campos adicionales que usa fase_6_citas.py pero no están en el modelo
    # Estos deberían añadirse al modelo MetadatosCita
    metadata_dict = metadata.model_dump()
    metadata_dict["hecho_relacionado_id"] = 2
    metadata_dict["entidad_emisora_id"] = 3

    cita = CitaTextual(
        id_cita=1,
        id_fragmento_origen="ART-123",
        texto_cita="Implementaremos medidas inmediatas para controlar la inflación",
        id_entidad_citada=3,
        contexto_cita="Durante rueda de prensa matinal",
        metadata_cita=metadata,
    )

    # Simular el mapeo correcto (según la actualización)
    cita_data_correcto = {
        "id_temporal_cita": str(cita.id_cita),
        "cita": cita.texto_cita,
        "id_temporal_entidad_emisora": str(cita.id_entidad_citada),
        "id_temporal_hecho_contexto": str(
            metadata_dict.get("hecho_relacionado_id", "")
        ),
        "fecha_cita": f"{cita.metadata_cita.fecha}T00:00:00Z",
        "contexto": cita.contexto_cita,
        "relevancia": cita.metadata_cita.relevancia,
    }

    print("✓ Mapeo CORRECTO (nombres sin sufijos _cita):")
    print(json.dumps(cita_data_correcto, indent=2, ensure_ascii=False))

    # Mostrar cómo sería el mapeo INCORRECTO (antiguo)
    cita_data_incorrecto = {
        "id_temporal_cita": str(cita.id_cita),
        "texto_cita": cita.texto_cita,  # INCORRECTO
        "entidad_emisora_id_temporal": str(cita.id_entidad_citada),
        "hecho_principal_relacionado_id_temporal": str(
            cita.metadata_cita.hecho_relacionado_id
        ),  # INCORRECTO
        "fecha_cita": cita.metadata_cita.fecha,
        "contexto_cita": cita.contexto_cita,  # INCORRECTO
        "relevancia_cita": cita.metadata_cita.relevancia,  # INCORRECTO
    }

    print("\n✗ Mapeo INCORRECTO (nombres antiguos con sufijos):")
    print(json.dumps(cita_data_incorrecto, indent=2, ensure_ascii=False))

    return cita_data_correcto


def test_rpc_field_names():
    """Verifica que los nombres coinciden con los esperados por RPC"""
    print("\n=== TEST: Nombres de campos RPC ===")

    # Campos que espera el RPC actualizado
    campos_rpc_esperados = [
        "cita",
        "id_temporal_entidad_emisora",
        "id_temporal_hecho_contexto",
        "fecha_cita",
        "contexto",
        "relevancia",
    ]

    # Crear payload de prueba
    cita_payload = {
        "cita": "Implementaremos medidas inmediatas",
        "id_temporal_entidad_emisora": "3",
        "id_temporal_hecho_contexto": "2",
        "fecha_cita": "2023-03-14T10:30:00Z",
        "contexto": "Durante rueda de prensa",
        "relevancia": 4,
    }

    print("✓ Payload con campos esperados por RPC:")
    print(json.dumps(cita_payload, indent=2, ensure_ascii=False))

    # Verificar que todos los campos esperados están presentes
    print("\n✓ Verificación de campos:")
    for campo in campos_rpc_esperados:
        if campo in cita_payload:
            print(f"  ✓ {campo}: presente")
        else:
            print(f"  ✗ {campo}: FALTANTE")

    # Verificar que NO hay campos con sufijos antiguos
    campos_no_deseados = ["texto_cita", "contexto_cita", "relevancia_cita"]
    print("\n✓ Verificación de campos no deseados:")
    for campo in campos_no_deseados:
        if campo in cita_payload:
            print(f"  ✗ {campo}: presente (NO DEBERÍA ESTAR)")
        else:
            print(f"  ✓ {campo}: ausente (correcto)")


def test_escala_relevancia():
    """Verifica que la escala de relevancia es 1-5"""
    print("\n=== TEST: Escala de Relevancia ===")

    # Test valor válido
    try:
        cita_valida = CitaTextualExtraidaItem(  # noqa: F841
            id_temporal_cita="CITA-001",
            cita="Test de relevancia",
            relevancia=5,  # Máximo válido
        )
        print("✓ Relevancia=5 aceptada (máximo válido)")
    except Exception as e:
        print(f"✗ ERROR con relevancia=5: {e}")

    # Test valor inválido (si hubiera validación)
    try:
        cita_invalida = CitaTextualExtraidaItem(  # noqa: F841
            id_temporal_cita="CITA-002",
            cita="Test de relevancia",
            relevancia=10,  # Antiguo máximo, ahora inválido
        )
        print("✗ Relevancia=10 aceptada (DEBERÍA ser inválido)")
        print("  Nota: La validación de rango debe implementarse en el modelo")
    except Exception as e:
        print(f"✓ Relevancia=10 rechazada correctamente: {e}")


def main():
    """Ejecuta todos los tests"""
    print("=" * 60)
    print("TEST DE ALINEACIÓN CITAS TEXTUALES CON RPC")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")

    # Ejecutar tests
    test_cita_textual_extraida_item()
    test_pipeline_coordinator_mapping()
    test_rpc_field_names()
    test_escala_relevancia()

    print("\n" + "=" * 60)
    print("RESUMEN:")
    print("- CitaTextualExtraidaItem debe usar campos sin sufijos")
    print("- Pipeline coordinator debe mapear a nombres esperados por RPC")
    print("- Relevancia debe usar escala 1-5")
    print("- Campo nuevo: id_temporal_hecho_contexto")
    print("=" * 60)


if __name__ == "__main__":
    main()
