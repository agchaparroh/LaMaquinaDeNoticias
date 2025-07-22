#!/usr/bin/env python
"""
Script de prueba para verificar la alineación de campos de hechos con el RPC.

Este script crea datos de prueba con campos alineados al RPC actualizado
y verifica que se persistan correctamente en Supabase.
"""

import os
import sys
from datetime import datetime
import json

# Añadir el directorio del módulo al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src/module_pipeline'))

from src.services.supabase_service import SupabaseService
from src.services.payload_builder import PayloadBuilder

def crear_hechos_prueba():
    """Crea hechos de prueba con campos alineados al RPC actualizado."""
    return [
        {
            # Campos principales alineados con RPC actualizado
            "id_temporal": "1",
            "contenido": "El presidente anunció nuevas medidas económicas durante la rueda de prensa",
            "tipo_hecho": "ANUNCIO",
            "importancia": 9,  # Escala 1-10
            "fecha_ocurrencia_inicio": "2025-01-21T10:00:00Z",
            "fecha_ocurrencia_fin": "2025-01-21T11:00:00Z",
            "precision_temporal": "exacta",
            "metadata": {
                "pais": ["España"],
                "region": ["Madrid"],
                "ciudad": ["Madrid"],
                "etiquetas": ["economía", "gobierno", "política"]
            },
            
            # Campos adicionales para compatibilidad con HechoExtraidoItem
            "es_evento_futuro": False,
            "estado_programacion": None,
            "lugar_ocurrencia_hecho": "Palacio de la Moncloa, Madrid",
            "contexto_adicional_hecho": "Rueda de prensa matinal tras el Consejo de Ministros",
            "subtipo_hecho": "gubernamental",
            "detalle_complejo_hecho": {
                "duracion_minutos": 60,
                "numero_asistentes": 50
            },
            "entidades_del_hecho": []
        },
        {
            # Campos principales alineados con RPC actualizado
            "id_temporal": "2",
            "contenido": "Se registró un aumento del 15% en las exportaciones durante el último trimestre",
            "tipo_hecho": "SUCESO",
            "importancia": 7,
            "fecha_ocurrencia_inicio": "2024-10-01T00:00:00Z",
            "fecha_ocurrencia_fin": "2024-12-31T23:59:59Z",
            "precision_temporal": "trimestre",
            "metadata": {
                "pais": ["España"],
                "region": [],
                "ciudad": [],
                "etiquetas": ["economía", "comercio", "exportaciones"]
            },
            
            # Campos adicionales
            "es_evento_futuro": False,
            "estado_programacion": None,
            "lugar_ocurrencia_hecho": "España",
            "contexto_adicional_hecho": "Datos del Instituto Nacional de Estadística",
            "subtipo_hecho": "económico",
            "detalle_complejo_hecho": {
                "porcentaje_aumento": 15,
                "trimestre": "Q4-2024"
            },
            "entidades_del_hecho": []
        },
        {
            # Campos principales alineados con RPC actualizado
            "id_temporal": "3",
            "contenido": "Se celebrará una cumbre internacional sobre cambio climático en Barcelona",
            "tipo_hecho": "EVENTO",
            "importancia": 8,
            "fecha_ocurrencia_inicio": "2025-06-15T09:00:00Z",
            "fecha_ocurrencia_fin": "2025-06-17T18:00:00Z",
            "precision_temporal": "dia",
            "metadata": {
                "pais": ["España"],
                "region": ["Cataluña"],
                "ciudad": ["Barcelona"],
                "etiquetas": ["medioambiente", "internacional", "cumbre"]
            },
            
            # Campos adicionales
            "es_evento_futuro": True,
            "estado_programacion": "confirmado",
            "lugar_ocurrencia_hecho": "Centro de Convenciones de Barcelona",
            "contexto_adicional_hecho": "Participarán representantes de 50 países",
            "subtipo_hecho": "cumbre internacional",
            "detalle_complejo_hecho": {
                "numero_paises": 50,
                "duracion_dias": 3
            },
            "entidades_del_hecho": []
        }
    ]

def verificar_campos_hecho(hecho_dict):
    """Verifica que un hecho tenga los campos correctos alineados con el RPC."""
    campos_correctos = {
        'id_temporal': 'string',
        'contenido': 'string',
        'tipo_hecho': 'string',
        'importancia': 'number',
        'fecha_ocurrencia_inicio': 'string',
        'fecha_ocurrencia_fin': 'string',
        'precision_temporal': 'string',
        'metadata': 'object'
    }
    
    campos_incorrectos = {
        'id_temporal_hecho': 'Debe ser id_temporal',
        'descripcion_hecho': 'Debe ser contenido',
        'relevancia_hecho': 'Debe ser importancia',
        'fecha_ocurrencia_hecho_inicio': 'Debe ser fecha_ocurrencia_inicio',
        'fecha_ocurrencia_hecho_fin': 'Debe ser fecha_ocurrencia_fin',
        'metadata_hecho': 'Debe ser metadata'
    }
    
    print("\n   Verificación de campos:")
    
    # Verificar campos correctos
    for campo, tipo in campos_correctos.items():
        if campo in hecho_dict:
            print(f"   ✓ {campo}: presente")
        else:
            print(f"   ✗ {campo}: FALTA")
    
    # Verificar campos incorrectos
    errores_encontrados = []
    for campo_incorrecto, mensaje in campos_incorrectos.items():
        if campo_incorrecto in hecho_dict:
            errores_encontrados.append(f"{campo_incorrecto} ({mensaje})")
    
    if errores_encontrados:
        print(f"\n   ⚠️  ERRORES: Campos con nombres antiguos encontrados:")
        for error in errores_encontrados:
            print(f"      - {error}")
        return False
    else:
        print("\n   ✓ Todos los campos están correctamente alineados con el RPC")
        return True

def main():
    """Función principal para probar la persistencia de hechos."""
    print("=== TEST DE ALINEACIÓN DE HECHOS CON RPC ===\n")
    
    # Inicializar servicios
    print("1. Inicializando servicios...")
    supabase_service = SupabaseService()
    payload_builder = PayloadBuilder()
    
    # Crear datos de prueba
    print("2. Creando datos de prueba con campos alineados...")
    hechos_prueba = crear_hechos_prueba()
    
    print(f"   - Creados {len(hechos_prueba)} hechos de prueba")
    for hecho in hechos_prueba:
        print(f"   - {hecho['tipo_hecho']}: {hecho['contenido'][:50]}...")
    
    # Crear payload completo
    print("\n3. Construyendo payload para RPC...")
    
    # Metadatos del artículo
    metadatos_articulo = {
        "url": "https://ejemplo.com/noticia-test-hechos",
        "titular": "Prueba de Alineación de Hechos con RPC Actualizado",
        "medio": "Test News",
        "area_geografica": "España",
        "tipo_medio": "Digital",
        "fecha_publicacion": datetime.now().isoformat(),
        "autor": "Script de Prueba",
        "idioma_original": "es",
        "seccion": "Tecnología",
        "es_opinion": False,
        "es_oficial": False,
        "contenido_texto_original": "Contenido de prueba para verificar la alineación de campos de hechos con el RPC actualizado."
    }
    
    # Datos de procesamiento
    procesamiento_articulo = {
        "resumen_generado_pipeline": "Artículo de prueba para verificar campos de hechos alineados con RPC",
        "palabras_clave_generadas": ["prueba", "hechos", "RPC", "alineación"],
        "sentimiento_general_articulo": "neutral",
        "estado_procesamiento_final_pipeline": "completado_ok",
        "version_pipeline_aplicada": "1.0.0-test",
        "fecha_ingesta_sistema": datetime.now().isoformat(),
        "fecha_procesamiento_pipeline": datetime.now().isoformat()
    }
    
    try:
        # Construir payload
        payload = payload_builder.construir_payload_articulo(
            metadatos_articulo_data=metadatos_articulo,
            procesamiento_articulo_data=procesamiento_articulo,
            hechos_extraidos_data=hechos_prueba
        )
        
        print("   ✓ Payload construido exitosamente")
        
        # Mostrar estructura del payload
        print("\n4. Verificando estructura del payload...")
        payload_dict = payload.model_dump()
        
        if "hechos_extraidos" in payload_dict:
            print(f"   - Hechos en payload: {len(payload_dict['hechos_extraidos'])}")
            
            # Verificar primer hecho
            if payload_dict['hechos_extraidos']:
                primer_hecho = payload_dict['hechos_extraidos'][0]
                print("\n   Primer hecho en payload:")
                print(f"   - id_temporal: {primer_hecho.get('id_temporal')}")
                print(f"   - contenido: {primer_hecho.get('contenido')[:50]}...")
                print(f"   - tipo_hecho: {primer_hecho.get('tipo_hecho')}")
                print(f"   - importancia: {primer_hecho.get('importancia')}")
                print(f"   - precision_temporal: {primer_hecho.get('precision_temporal')}")
                print(f"   - metadata: {primer_hecho.get('metadata')}")
                
                # Verificar campos
                campos_correctos = verificar_campos_hecho(primer_hecho)
                
                if not campos_correctos:
                    print("\n   ✗ ERROR: Los campos no están correctamente alineados con el RPC")
                    return
        
        # Mostrar JSON del primer hecho para verificación visual
        print("\n5. JSON del primer hecho (para verificación):")
        if payload_dict['hechos_extraidos']:
            primer_hecho_json = json.dumps(payload_dict['hechos_extraidos'][0], indent=2, ensure_ascii=False)
            print(primer_hecho_json)
        
        # Persistir en Supabase
        print("\n6. Persistiendo en Supabase...")
        
        resultado = supabase_service.persistir_articulo_completo_rpc(
            payload_articulo=payload
        )
        
        if resultado['success']:
            print("   ✓ Persistencia exitosa!")
            print(f"   - ID del artículo: {resultado['article_id']}")
            
            # Verificar hechos persistidos
            if 'fact_count' in resultado:
                print(f"   - Hechos persistidos: {resultado['fact_count']}")
                
            print("\n✅ TEST COMPLETADO: Los hechos están correctamente alineados con el RPC")
        else:
            print(f"   ✗ Error en persistencia: {resultado.get('error', 'Error desconocido')}")
            print(f"   Detalles: {resultado.get('details', 'Sin detalles adicionales')}")
            
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()