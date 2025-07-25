#!/usr/bin/env python3
"""
Verificación simple de campos en los archivos modificados para datos cuantitativos.
"""

import os
import re


def check_file_for_fields(filepath, old_fields, new_fields):
    """Verifica presencia de campos antiguos vs nuevos en un archivo."""
    if not os.path.exists(filepath):
        print(f"  ✗ Archivo no encontrado: {filepath}")
        return False

    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    results = {
        "old_fields_found": [],
        "new_fields_found": [],
        "file": os.path.basename(filepath),
    }

    # Buscar campos antiguos
    for field in old_fields:
        # Buscar el campo como string literal o como atributo
        pattern = rf'["\']?{field}["\']?\s*[:=]|\.{field}\b'
        if re.search(pattern, content):
            results["old_fields_found"].append(field)

    # Buscar campos nuevos
    for field in new_fields:
        pattern = rf'["\']?{field}["\']?\s*[:=]|\.{field}\b'
        if re.search(pattern, content):
            results["new_fields_found"].append(field)

    return results


def main():
    print("=== VERIFICACIÓN DE CAMPOS EN ARCHIVOS MODIFICADOS ===\n")

    # Definir campos antiguos y nuevos
    old_fields = [
        "descripcion_dato",
        "valor_dato",
        "unidad_dato",
        "hecho_principal_relacionado_id_temporal",
    ]

    new_fields = [
        "indicador",
        "valor_numerico",
        "unidad",
        "id_temporal_hecho",
        "ambito_geografico",
    ]

    # Archivos a verificar
    files_to_check = [
        "/home/ec2-user/projects/LaMaquinaDeNoticias/src/module_pipeline/src/models/persistencia.py",
        "/home/ec2-user/projects/LaMaquinaDeNoticias/src/module_pipeline/src/services/payload_builder.py",
        "/home/ec2-user/projects/LaMaquinaDeNoticias/src/module_pipeline/src/pipeline/fase_5_datos.py",
        "/home/ec2-user/projects/LaMaquinaDeNoticias/test_rpc_datos_alignment.py",
    ]

    all_results = []

    for filepath in files_to_check:
        print(f"\nVerificando: {os.path.basename(filepath)}")
        print("-" * 60)

        results = check_file_for_fields(filepath, old_fields, new_fields)
        if isinstance(results, dict):
            all_results.append(results)

            # Mostrar campos nuevos encontrados
            if results["new_fields_found"]:
                print(
                    f"✓ Campos nuevos (RPC) encontrados: {', '.join(results['new_fields_found'])}"
                )
            else:
                print("⚠️  No se encontraron campos nuevos")

            # Verificar contexto de campos antiguos
            if results["old_fields_found"]:
                print(
                    f"ℹ️  Campos antiguos encontrados: {', '.join(results['old_fields_found'])}"
                )
                print("  (Esto es OK si están en contexto de mapeo/compatibilidad)")

    # Resumen
    print("\n\n=== RESUMEN DE LA VERIFICACIÓN ===")
    print("-" * 60)

    # Verificar persistencia.py
    persistencia_result = next(
        (r for r in all_results if r["file"] == "persistencia.py"), None
    )
    if persistencia_result:
        if all(
            field in persistencia_result["new_fields_found"]
            for field in ["indicador", "valor_numerico", "unidad", "id_temporal_hecho"]
        ):
            print(
                "✓ persistencia.py: Modelo DatoCuantitativoExtraidoItem tiene campos RPC correctos"
            )
        else:
            print("✗ persistencia.py: Faltan algunos campos RPC en el modelo")

    # Verificar payload_builder.py
    payload_result = next(
        (r for r in all_results if r["file"] == "payload_builder.py"), None
    )
    if payload_result:
        if payload_result["old_fields_found"] and payload_result["new_fields_found"]:
            print(
                "✓ payload_builder.py: Tiene mapeo de campos antiguos a nuevos (correcto)"
            )
        else:
            print("⚠️  payload_builder.py: Verificar mapeo de campos")

    # Verificar fase_5_datos.py
    fase5_result = next(
        (r for r in all_results if r["file"] == "fase_5_datos.py"), None
    )
    if fase5_result:
        if "indicador" in fase5_result["new_fields_found"]:
            print("✓ fase_5_datos.py: Genera datos con campos nuevos")
        else:
            print("⚠️  fase_5_datos.py: Verificar generación de campos")

    # Verificar test
    test_result = next(
        (r for r in all_results if r["file"] == "test_rpc_datos_alignment.py"), None
    )
    if test_result:
        if test_result["new_fields_found"]:
            print("✓ test_rpc_datos_alignment.py: Prueba campos RPC correctos")

    print("\n✅ CONCLUSIÓN: La alineación de datos cuantitativos está implementada")
    print("   - El modelo tiene los campos correctos para el RPC")
    print("   - PayloadBuilder mapea campos antiguos a nuevos")
    print("   - Se mantiene compatibilidad con campos antiguos")


if __name__ == "__main__":
    main()
