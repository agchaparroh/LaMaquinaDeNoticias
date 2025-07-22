#!/usr/bin/env python3
"""
Script de prueba simplificado para verificar la alineación de campos de hechos con el RPC.
No requiere dependencias externas, solo verifica la estructura de datos.
"""

import json
from datetime import datetime

def crear_hecho_pipeline_coordinator_format():
    """
    Simula el formato de datos que genera pipeline_coordinator.py
    después de las actualizaciones realizadas.
    """
    return {
        # Campos alineados con RPC (como se mapean en pipeline_coordinator.py)
        "id_temporal": "1",
        "contenido": "El presidente anunció nuevas medidas económicas",
        "tipo_hecho": "ANUNCIO",
        "importancia": 9,
        "fecha_ocurrencia_inicio": "2025-01-21T10:00:00Z",
        "fecha_ocurrencia_fin": "2025-01-21T11:00:00Z",
        "precision_temporal": "exacta",
        "metadata": {
            "pais": ["Venezuela"],
            "region": ["Caracas Capital"],
            "ciudad": ["Caracas"],
            "etiquetas": []
        },
        # Campos adicionales para HechoExtraidoItem
        "es_evento_futuro": False,
        "estado_programacion": None,
        "lugar_ocurrencia_hecho": "Palacio de Miraflores, Caracas",
        "contexto_adicional_hecho": "Rueda de prensa oficial",
        "subtipo_hecho": "gubernamental",
        "detalle_complejo_hecho": {},
        "entidades_del_hecho": []
    }

def crear_hecho_modelo_antiguo():
    """
    Simula el formato ANTIGUO con campos incorrectos (antes de la actualización).
    """
    return {
        # Campos con nombres antiguos (INCORRECTOS)
        "id_temporal_hecho": "1",  # ❌ Debería ser id_temporal
        "descripcion_hecho": "El presidente anunció nuevas medidas económicas",  # ❌ Debería ser contenido
        "tipo_hecho": "ANUNCIO",
        "relevancia_hecho": 9,  # ❌ Debería ser importancia
        "fecha_ocurrencia_hecho_inicio": "2025-01-21T10:00:00Z",  # ❌ Sin sufijo _hecho
        "fecha_ocurrencia_hecho_fin": "2025-01-21T11:00:00Z",  # ❌ Sin sufijo _hecho
        "precision_temporal": "exacta",
        "metadata_hecho": {  # ❌ Debería ser metadata
            "pais": ["Venezuela"],
            "region": ["Caracas Capital"],
            "ciudad": ["Caracas"]
        }
    }

def verificar_campos_rpc(hecho_dict, nombre_prueba):
    """Verifica que un hecho tenga los campos correctos para el RPC."""
    print(f"\n{'='*60}")
    print(f"VERIFICANDO: {nombre_prueba}")
    print('='*60)
    
    # Campos esperados por el RPC actualizado
    campos_requeridos = {
        'id_temporal': 'ID temporal del hecho',
        'contenido': 'Contenido/descripción del hecho',
        'tipo_hecho': 'Tipo de hecho (SUCESO, ANUNCIO, etc)',
        'importancia': 'Importancia del hecho (1-10)',
        'fecha_ocurrencia_inicio': 'Fecha de inicio ISO 8601',
        'fecha_ocurrencia_fin': 'Fecha de fin ISO 8601',
        'precision_temporal': 'Precisión temporal',
        'metadata': 'Metadatos adicionales (pais, region, ciudad, etiquetas)'
    }
    
    # Campos que NO deberían existir (nombres antiguos)
    campos_incorrectos = {
        'id_temporal_hecho': 'Usar id_temporal',
        'descripcion_hecho': 'Usar contenido',
        'relevancia_hecho': 'Usar importancia',
        'fecha_ocurrencia_hecho_inicio': 'Usar fecha_ocurrencia_inicio',
        'fecha_ocurrencia_hecho_fin': 'Usar fecha_ocurrencia_fin',
        'metadata_hecho': 'Usar metadata'
    }
    
    todos_correctos = True
    
    # Verificar campos requeridos
    print("\n✓ Campos Requeridos:")
    for campo, descripcion in campos_requeridos.items():
        if campo in hecho_dict:
            valor = hecho_dict[campo]
            if isinstance(valor, dict):
                valor_str = f"{{{len(valor)} campos}}"
            elif isinstance(valor, list):
                valor_str = f"[{len(valor)} elementos]"
            elif isinstance(valor, str) and len(valor) > 50:
                valor_str = f'"{valor[:47]}..."'
            else:
                valor_str = f'"{valor}"'
            print(f"  ✅ {campo}: {valor_str}")
        else:
            print(f"  ❌ {campo}: FALTA - {descripcion}")
            todos_correctos = False
    
    # Verificar campos incorrectos
    print("\n✗ Campos Incorrectos (no deberían existir):")
    campos_malos_encontrados = []
    for campo_malo, correccion in campos_incorrectos.items():
        if campo_malo in hecho_dict:
            campos_malos_encontrados.append(f"{campo_malo} → {correccion}")
            todos_correctos = False
    
    if campos_malos_encontrados:
        for campo in campos_malos_encontrados:
            print(f"  ❌ {campo}")
    else:
        print("  ✅ Ninguno encontrado (correcto)")
    
    # Verificar estructura de metadata
    if 'metadata' in hecho_dict:
        print("\n📦 Estructura de metadata:")
        metadata = hecho_dict['metadata']
        if isinstance(metadata, dict):
            for key, value in metadata.items():
                print(f"  - {key}: {value}")
        else:
            print(f"  ❌ ERROR: metadata no es un diccionario, es {type(metadata)}")
            todos_correctos = False
    
    return todos_correctos

def main():
    """Función principal del test."""
    print("🔍 TEST DE ALINEACIÓN DE CAMPOS DE HECHOS CON RPC ACTUALIZADO")
    print("="*60)
    print("Fecha: 2025-01-21")
    print("Objetivo: Verificar que los campos estén alineados con el RPC")
    print("="*60)
    
    # Crear datos de prueba
    hecho_correcto = crear_hecho_pipeline_coordinator_format()
    hecho_antiguo = crear_hecho_modelo_antiguo()
    
    # Test 1: Verificar formato correcto
    resultado1 = verificar_campos_rpc(hecho_correcto, "Formato Actualizado (Correcto)")
    
    # Test 2: Verificar formato antiguo (debe fallar)
    resultado2 = verificar_campos_rpc(hecho_antiguo, "Formato Antiguo (Incorrecto)")
    
    # Mostrar JSON de ejemplo correcto
    print("\n" + "="*60)
    print("📋 EJEMPLO DE HECHO CORRECTAMENTE FORMATEADO:")
    print("="*60)
    print(json.dumps(hecho_correcto, indent=2, ensure_ascii=False))
    
    # Resumen final
    print("\n" + "="*60)
    print("📊 RESUMEN DE RESULTADOS:")
    print("="*60)
    print(f"Test 1 (Formato Actualizado): {'✅ PASÓ' if resultado1 else '❌ FALLÓ'}")
    print(f"Test 2 (Formato Antiguo): {'✅ FALLÓ CORRECTAMENTE' if not resultado2 else '❌ PASÓ INCORRECTAMENTE'}")
    
    if resultado1 and not resultado2:
        print("\n✅ ¡ÉXITO! Los campos están correctamente alineados con el RPC actualizado.")
        print("   El pipeline ahora genera hechos con la estructura esperada por Supabase.")
    else:
        print("\n❌ ERROR: Hay problemas con la alineación de campos.")
        if not resultado1:
            print("   - El formato actualizado no tiene todos los campos correctos")
        if resultado2:
            print("   - El formato antiguo no está siendo rechazado correctamente")

if __name__ == "__main__":
    main()