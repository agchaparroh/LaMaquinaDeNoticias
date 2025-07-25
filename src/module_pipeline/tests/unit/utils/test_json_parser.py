#!/usr/bin/env python3
"""
Script de prueba para el parser JSON robusto
"""

import sys
from pathlib import Path

# Añadir el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ....src.utils.json_parser import (
    analyze_llm_response_format,
    clean_markdown_wrapper,
    detect_markdown_blocks,
    detect_truncation,
    parse_llm_json_response,
)


def test_json_parser():
    """Ejecuta pruebas del parser JSON con diferentes casos."""

    print("🧪 PRUEBAS DEL PARSER JSON ROBUSTO")
    print("=" * 50)

    # Caso 1: JSON limpio
    print("\n📋 Caso 1: JSON limpio")
    json_limpio = '{"entidades": [{"id": 1, "nombre": "Test"}], "hechos": []}'
    resultado = parse_llm_json_response(json_limpio)
    print(f"✅ Parseado correctamente: {resultado}")

    # Caso 2: JSON con markdown
    print("\n📋 Caso 2: JSON envuelto en markdown")
    json_markdown = """```json
{
  "entidades": [
    {
      "id": 1,
      "nombre": "Pedro Sánchez",
      "tipo": "PERSONA"
    }
  ],
  "hechos": [
    {
      "id": 1,
      "contenido": "Anunció nuevas medidas"
    }
  ]
}
```"""
    resultado = parse_llm_json_response(json_markdown)
    print(f"✅ Parseado correctamente después de limpiar markdown: {resultado}")

    # Caso 3: JSON truncado
    print("\n📋 Caso 3: JSON truncado")
    json_truncado = """```json
{
  "entidades": [
    {
      "id": 1,
      "nombre": "Test",
      "tipo": "PERSONA"
    }
  ],
  "hechos": [
    {
      "id": 1,
      "contenido": "Este es un hecho que está incomple"""

    # Analizar formato
    metrics = analyze_llm_response_format(json_truncado)
    print(f"📊 Métricas: {metrics}")

    # Intentar parsear
    resultado = parse_llm_json_response(json_truncado, attempt_repair=True)
    if resultado:
        print(f"⚠️  JSON reparado (datos incompletos): {resultado}")
    else:
        print("❌ No se pudo reparar el JSON truncado")

    # Caso 4: Detectar markdown
    print("\n📋 Caso 4: Detección de bloques markdown")
    texto_con_bloques = """Aquí hay texto normal
```json
{"test": true}
```
Y más texto
```python
print("hola")
```"""
    bloques = detect_markdown_blocks(texto_con_bloques)
    print(f"✅ Bloques detectados: {len(bloques)}")
    for i, (start, end, lang) in enumerate(bloques):
        print(f"   Bloque {i + 1}: lenguaje='{lang}', posición={start}-{end}")

    # Caso 5: Limpieza de markdown
    print("\n📋 Caso 5: Limpieza de markdown wrapper")
    original = '```json\n{"key": "value"}\n```'
    limpio = clean_markdown_wrapper(original)
    print(f"Original: {repr(original)}")
    print(f"Limpio: {repr(limpio)}")

    # Caso 6: Detección de truncamiento
    print("\n📋 Caso 6: Detección de truncamiento")
    casos_truncamiento = [
        '{"complete": true}',
        '{"incomplete": "valor sin cerr',
        '{"array": [1, 2, 3',
        '{"nested": {"inner": "val',
    ]

    for caso in casos_truncamiento:
        truncado, razon = detect_truncation(caso)
        estado = "TRUNCADO" if truncado else "COMPLETO"
        print(f"{estado}: {repr(caso[:30])}... {razon if truncado else ''}")

    print("\n✅ Todas las pruebas completadas")


if __name__ == "__main__":
    test_json_parser()
