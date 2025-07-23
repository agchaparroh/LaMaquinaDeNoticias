#!/usr/bin/env python
"""
Script de prueba para verificar la alineación de campos de datos cuantitativos con el RPC.

Este script crea datos de prueba con campos alineados al RPC actualizado
y verifica que se persistan correctamente en Supabase.
"""

import os
import sys
from datetime import datetime
import json

# Añadir el directorio del módulo al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src/module_pipeline'))

from ..src.services.supabase_service import SupabaseService
from ..src.services.payload_builder import PayloadBuilder

def crear_hechos_prueba():
    """Crea hechos de prueba necesarios para los datos cuantitativos."""
    return [
        {
            # Campos principales alineados con RPC
            "id_temporal": "1",
            "contenido": "El PIB creció un 3.5% en el primer trimestre",
            "tipo_hecho": "SUCESO",
            "fecha_ocurrencia_inicio": "2024-03-31",
            "importancia": 8,
            "precision_temporal": "trimestre",
            "metadata": {
                "pais": ["España"],
                "region": ["Nacional"],
                "ciudad": [],
                "etiquetas": ["economía", "PIB"]
            }
        },
        {
            "id_temporal": "2",
            "contenido": "La inflación interanual alcanzó el 2.7%",
            "tipo_hecho": "SUCESO",
            "fecha_ocurrencia_inicio": "2024-03-31",
            "importancia": 7,
            "precision_temporal": "mes",
            "metadata": {
                "pais": ["España"],
                "region": ["Nacional"],
                "ciudad": [],
                "etiquetas": ["economía", "inflación"]
            }
        }
    ]

def crear_datos_cuantitativos_prueba():
    """Crea datos cuantitativos de prueba con campos alineados al RPC."""
    return [
        {
            # Campos principales alineados con RPC
            "id_temporal_hecho": "1",  # Referencia al hecho del PIB
            "indicador": "Crecimiento del PIB trimestral",
            "categoria": "económico",
            "valor_numerico": 3.5,
            "unidad": "porcentaje",
            "ambito_geografico": ["España"],
            "periodo_referencia_inicio": "2024-01-01",
            "periodo_referencia_fin": "2024-03-31",
            "tendencia": "aumento",
            
            # Campos temporales
            "id_temporal_dato": "DATO-001",
            
            # Campos adicionales no procesados por RPC pero útiles
            "tipo_periodo": "trimestral",
            "valor_anterior": 2.8,
            "variacion_absoluta": 0.7,
            "variacion_porcentual": 25.0,
            "fuente_especifica": "INE",
            
            # Campos adicionales para compatibilidad con procesamiento
            "id_dato_cuantitativo": 1,
            "descripcion_dato": "Crecimiento del PIB trimestral",
            "valor_dato": 3.5,
            "unidad_dato": "porcentaje",
            "fecha_dato": "2024-01-01 - 2024-03-31"
        },
        {
            # Campos principales alineados con RPC
            "id_temporal_hecho": "2",  # Referencia al hecho de inflación
            "indicador": "Inflación interanual",
            "categoria": "económico",
            "valor_numerico": 2.7,
            "unidad": "porcentaje",
            "ambito_geografico": ["España", "Zona Euro"],
            "periodo_referencia_inicio": "2023-03-01",
            "periodo_referencia_fin": "2024-03-31",
            "tendencia": "disminución",
            
            # Campos temporales
            "id_temporal_dato": "DATO-002",
            
            # Campos adicionales
            "tipo_periodo": "anual",
            "valor_anterior": 3.2,
            "variacion_absoluta": -0.5,
            "variacion_porcentual": -15.6,
            "fuente_especifica": "Eurostat",
            
            # Compatibilidad
            "id_dato_cuantitativo": 2,
            "descripcion_dato": "Inflación interanual",
            "valor_dato": 2.7,
            "unidad_dato": "porcentaje",
            "fecha_dato": "2023-03-01 - 2024-03-31"
        },
        {
            # Campos principales alineados con RPC
            "id_temporal_hecho": "1",  # También relacionado con el PIB
            "indicador": "Tasa de desempleo",
            "categoria": "social",
            "valor_numerico": 11.2,
            "unidad": "porcentaje",
            "ambito_geografico": ["España"],
            "periodo_referencia_inicio": "2024-03-31",
            "periodo_referencia_fin": "2024-03-31",
            "tendencia": "estable",
            
            # Campos temporales
            "id_temporal_dato": "DATO-003",
            
            # Campos adicionales
            "tipo_periodo": "puntual",
            "valor_anterior": 11.3,
            "variacion_absoluta": -0.1,
            "variacion_porcentual": -0.9,
            "fuente_especifica": "EPA",
            
            # Compatibilidad
            "id_dato_cuantitativo": 3,
            "descripcion_dato": "Tasa de desempleo",
            "valor_dato": 11.2,
            "unidad_dato": "porcentaje",
            "fecha_dato": "2024-03-31"
        }
    ]

def main():
    """Función principal para probar la persistencia de datos cuantitativos."""
    print("=== TEST DE ALINEACIÓN DE DATOS CUANTITATIVOS CON RPC ===\n")
    
    # Inicializar servicios
    print("1. Inicializando servicios...")
    supabase_service = SupabaseService()
    payload_builder = PayloadBuilder()
    
    # Crear datos de prueba
    print("2. Creando datos de prueba con campos alineados...")
    hechos_prueba = crear_hechos_prueba()
    datos_prueba = crear_datos_cuantitativos_prueba()
    
    print(f"   - Creados {len(hechos_prueba)} hechos de prueba")
    print(f"   - Creados {len(datos_prueba)} datos cuantitativos de prueba")
    
    for dato in datos_prueba:
        print(f"   - {dato['indicador']}: {dato['valor_numerico']} {dato['unidad']}")
    
    # Crear payload completo
    print("\n3. Construyendo payload para RPC...")
    
    # Metadatos del artículo
    metadatos_articulo = {
        "url": "https://ejemplo.com/noticia-test-datos",
        "titular": "Prueba de Alineación de Datos Cuantitativos con RPC",
        "medio": "Test News",
        "area_geografica": "España",
        "tipo_medio": "Digital",
        "fecha_publicacion": datetime.now().isoformat(),
        "autor": "Script de Prueba",
        "idioma_original": "es",
        "seccion": "Economía",
        "es_opinion": False,
        "es_oficial": False,
        "contenido_texto_original": "Contenido de prueba para verificar la alineación de campos de datos cuantitativos."
    }
    
    # Datos de procesamiento
    procesamiento_articulo = {
        "resumen_generado_pipeline": "Artículo de prueba para verificar campos de datos cuantitativos",
        "palabras_clave_generadas": ["prueba", "datos", "RPC", "economía"],
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
            hechos_extraidos_data=hechos_prueba,
            datos_cuantitativos_data=datos_prueba
        )
        
        print("   ✓ Payload construido exitosamente")
        
        # Mostrar estructura del payload
        print("\n4. Verificando estructura del payload...")
        payload_dict = payload.model_dump()
        
        if "datos_cuantitativos_extraidos" in payload_dict:
            print(f"   - Datos en payload: {len(payload_dict['datos_cuantitativos_extraidos'])}")
            
            # Verificar primer dato
            if payload_dict['datos_cuantitativos_extraidos']:
                primer_dato = payload_dict['datos_cuantitativos_extraidos'][0]
                print("\n   Primer dato cuantitativo en payload:")
                print(f"   - id_temporal_hecho: {primer_dato.get('id_temporal_hecho')}")
                print(f"   - indicador: {primer_dato.get('indicador')}")
                print(f"   - categoria: {primer_dato.get('categoria')}")
                print(f"   - valor_numerico: {primer_dato.get('valor_numerico')}")
                print(f"   - unidad: {primer_dato.get('unidad')}")
                print(f"   - ambito_geografico: {primer_dato.get('ambito_geografico')}")
                print(f"   - tendencia: {primer_dato.get('tendencia')}")
                
                # Verificar que NO existan campos con sufijos
                campos_incorrectos = []
                if 'descripcion_dato' in primer_dato:
                    campos_incorrectos.append('descripcion_dato (debe ser indicador)')
                if 'valor_dato' in primer_dato:
                    campos_incorrectos.append('valor_dato (debe ser valor_numerico)')
                if 'unidad_dato' in primer_dato:
                    campos_incorrectos.append('unidad_dato (debe ser unidad)')
                if 'hecho_principal_relacionado_id_temporal' in primer_dato:
                    campos_incorrectos.append('hecho_principal_relacionado_id_temporal (debe ser id_temporal_hecho)')
                
                if campos_incorrectos:
                    print(f"\n   ⚠️  ADVERTENCIA: Se encontraron campos con nombres antiguos: {campos_incorrectos}")
                else:
                    print("\n   ✓ Campos correctamente alineados con RPC")
                
                # Verificar campos críticos
                if not primer_dato.get('ambito_geografico'):
                    print("   ⚠️  ADVERTENCIA: Campo 'ambito_geografico' está vacío (requerido por RPC)")
        
        if "hechos_extraidos" in payload_dict:
            print(f"\n   - Hechos en payload: {len(payload_dict['hechos_extraidos'])}")
        
        # Persistir en Supabase
        print("\n5. Persistiendo en Supabase...")
        
        resultado = supabase_service.persistir_articulo_completo_rpc(
            payload_articulo=payload
        )
        
        if resultado['success']:
            print("   ✓ Persistencia exitosa!")
            print(f"   - ID del artículo: {resultado['article_id']}")
            
            # Verificar datos persistidos
            if 'data_count' in resultado:
                print(f"   - Datos cuantitativos persistidos: {resultado['data_count']}")
            if 'fact_count' in resultado:
                print(f"   - Hechos persistidos: {resultado['fact_count']}")
        else:
            print(f"   ✗ Error en persistencia: {resultado.get('error', 'Error desconocido')}")
            
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()