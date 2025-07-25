#!/usr/bin/env python3
"""
Script de verificación del flujo de id_fragmento en el pipeline
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple  # noqa: F401


def analizar_archivo(filepath: Path, patron: str) -> List[Tuple[int, str]]:
    """Busca un patrón en un archivo y retorna líneas coincidentes"""
    resultados = []
    try:
        with open(filepath, encoding="utf-8") as f:
            for i, linea in enumerate(f, 1):
                if re.search(patron, linea, re.IGNORECASE):
                    resultados.append((i, linea.strip()))
    except Exception as e:
        print(f"Error leyendo {filepath}: {e}")
    return resultados


def verificar_flujo_id_fragmento():
    """Verifica el flujo completo del id_fragmento"""

    base_path = Path("/home/ec2-user/projects/LaMaquinaDeNoticias/src/module_pipeline")

    print("=== VERIFICACIÓN DEL FLUJO DE id_fragmento ===\n")

    # 1. Verificar generación en controller
    print("1. GENERACIÓN DEL ID:")
    controller_path = base_path / "src/controller.py"
    generacion = analizar_archivo(
        controller_path, r'"id_fragmento":\s*str\(uuid\.uuid4\(\)\)'
    )
    if generacion:
        print(f"✅ ID generado en controller.py línea {generacion[0][0]}")
    else:
        print("❌ No se encontró generación de id_fragmento")

    # 2. Verificar propagación en fases
    print("\n2. PROPAGACIÓN EN FASES:")
    fases_dir = base_path / "src/pipeline"
    for fase in range(1, 8):
        fase_file = fases_dir / f"fase_{fase}_*.py"  # noqa: F841
        archivos_fase = list(fases_dir.glob(f"fase_{fase}_*.py"))
        if archivos_fase:
            for archivo in archivos_fase:
                usos = analizar_archivo(archivo, r"id_fragmento")
                if usos:
                    print(
                        f"✅ Fase {fase} ({archivo.name}): {len(usos)} referencias a id_fragmento"
                    )
                else:
                    print(
                        f"⚠️  Fase {fase} ({archivo.name}): Sin referencias a id_fragmento"
                    )

    # 3. Verificar construcción del payload
    print("\n3. CONSTRUCCIÓN DEL PAYLOAD:")
    metadatos_refs = analizar_archivo(controller_path, r"metadatos_fragmento\s*=\s*{")
    if metadatos_refs:
        print(f"📍 metadatos_fragmento definido en línea {metadatos_refs[0][0]}")
        # Buscar si incluye id_fragmento
        contexto_inicio = metadatos_refs[0][0]
        with open(controller_path) as f:
            lineas = f.readlines()
            # Buscar las siguientes 10 líneas después de metadatos_fragmento
            incluye_id = False
            for i in range(contexto_inicio - 1, min(contexto_inicio + 10, len(lineas))):
                if "id_fragmento" in lineas[i]:
                    incluye_id = True
                    break

            if incluye_id:
                print("✅ metadatos_fragmento INCLUYE id_fragmento")
            else:
                print("❌ metadatos_fragmento NO INCLUYE id_fragmento")

    # 4. Verificar modelo de persistencia
    print("\n4. MODELO DE PERSISTENCIA:")
    persistencia_path = base_path / "src/models/persistencia.py"
    modelo_fragmento = analizar_archivo(
        persistencia_path, r"class FragmentoPersistenciaPayload"
    )
    if modelo_fragmento:
        print(
            f"📍 FragmentoPersistenciaPayload definido en línea {modelo_fragmento[0][0]}"
        )
        # Buscar campos del modelo
        with open(persistencia_path) as f:
            lineas = f.readlines()
            en_modelo = False
            tiene_id_fragmento = False
            for i, linea in enumerate(lineas):
                if "class FragmentoPersistenciaPayload" in linea:
                    en_modelo = True
                elif (
                    en_modelo
                    and "class " in linea
                    and "FragmentoPersistenciaPayload" not in linea
                ):
                    break
                elif en_modelo and "id_fragmento" in linea and ":" in linea:
                    tiene_id_fragmento = True
                    print(f"✅ Campo id_fragmento encontrado en línea {i + 1}")
                    break

            if not tiene_id_fragmento:
                print("❌ El modelo NO define campo id_fragmento")

    # 5. Verificar payload builder
    print("\n5. PAYLOAD BUILDER:")
    builder_path = base_path / "src/services/payload_builder.py"
    metodo_fragmento = analizar_archivo(
        builder_path, r"def construir_payload_fragmento"
    )
    if metodo_fragmento:
        print(
            f"✅ Método construir_payload_fragmento encontrado en línea {metodo_fragmento[0][0]}"
        )

    # 6. Verificar alertas relacionadas
    print("\n6. ALERTAS RELACIONADAS:")
    alerts_path = base_path / ".alerts/alerts.json"
    if alerts_path.exists():
        with open(alerts_path) as f:
            alerts_data = json.load(f)
            alertas_relevantes = []
            for alert in alerts_data.get("alerts", []):
                if "id_fragmento" in alert.get(
                    "description", ""
                ) or "id_fragmento" in alert.get("annotations", {}).get("message", ""):
                    alertas_relevantes.append(alert)

            if alertas_relevantes:
                print(
                    f"⚠️  Encontradas {len(alertas_relevantes)} alertas relacionadas con id_fragmento:"
                )
                for alert in alertas_relevantes[:3]:  # Mostrar máximo 3
                    print(
                        f"   - {alert.get('timestamp', 'N/A')}: {alert.get('description', 'N/A')[:80]}..."
                    )
            else:
                print("✅ No hay alertas relacionadas con id_fragmento")

    print("\n=== RESUMEN ===")
    print("El problema principal es que:")
    print("1. El id_fragmento se genera correctamente")
    print("2. Se propaga por las fases del pipeline")
    print("3. PERO no se incluye en metadatos_fragmento al construir el payload")
    print("4. Por lo tanto, no llega a la base de datos")
    print(
        "\nSOLUCIÓN: Añadir 'id_fragmento' al diccionario metadatos_fragmento en controller.py"
    )


if __name__ == "__main__":
    verificar_flujo_id_fragmento()
