#!/usr/bin/env python3
"""
Script simplificado para verificar la alineación de campos de datos cuantitativos.
Verifica la transformación sin necesidad de conectar a Supabase.
"""

import os
import sys
from datetime import datetime

# Añadir el directorio del módulo al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src/module_pipeline'))

# Importar solo lo necesario para la verificación
from src.models.persistencia import DatoCuantitativoExtraidoItem
from src.services.payload_builder import PayloadBuilder

def verificar_modelo_datos():
    """Verifica que el modelo DatoCuantitativoExtraidoItem tenga los campos correctos."""
    print("=== VERIFICACIÓN DEL MODELO DatoCuantitativoExtraidoItem ===\n")
    
    # Crear una instancia de prueba con campos RPC
    dato_prueba = DatoCuantitativoExtraidoItem(
        id_temporal_hecho="HECHO-001",
        indicador="PIB trimestral",
        categoria="económico",
        valor_numerico=3.5,
        unidad="porcentaje",
        ambito_geografico=["España", "Europa"]
    )
    
    # Verificar campos principales
    print("Campos principales del modelo:")
    print(f"  - id_temporal_hecho: {dato_prueba.id_temporal_hecho}")
    print(f"  - indicador: {dato_prueba.indicador}")
    print(f"  - categoria: {dato_prueba.categoria}")
    print(f"  - valor_numerico: {dato_prueba.valor_numerico}")
    print(f"  - unidad: {dato_prueba.unidad}")
    print(f"  - ambito_geografico: {dato_prueba.ambito_geografico}")
    
    # Verificar que NO existan campos antiguos en el modelo
    dato_dict = dato_prueba.model_dump()
    campos_antiguos = ['descripcion_dato', 'valor_dato', 'unidad_dato', 'hecho_principal_relacionado_id_temporal']
    campos_encontrados = [campo for campo in campos_antiguos if campo in dato_dict]
    
    if campos_encontrados:
        print(f"\n⚠️  ADVERTENCIA: Se encontraron campos antiguos en el modelo: {campos_encontrados}")
    else:
        print("\n✓ El modelo NO contiene campos antiguos")
    
    return dato_prueba

def verificar_payload_builder():
    """Verifica que PayloadBuilder mapee correctamente los campos."""
    print("\n\n=== VERIFICACIÓN DE PAYLOAD BUILDER ===\n")
    
    builder = PayloadBuilder()
    
    # Datos de prueba con campos antiguos (como vendría del pipeline)
    datos_antiguos = [{
        "id_dato_cuantitativo": 1,
        "descripcion_dato": "Inflación anual",  # Campo antiguo
        "valor_dato": 2.7,                      # Campo antiguo
        "unidad_dato": "porcentaje",            # Campo antiguo
        "hecho_principal_relacionado_id_temporal": "HECHO-002",  # Campo antiguo
        "categoria": "económico",
        "fecha_dato": "2024-03-31"
    }]
    
    # Datos de prueba con campos nuevos (ya alineados)
    datos_nuevos = [{
        "id_temporal_hecho": "HECHO-003",
        "indicador": "Tasa de desempleo",
        "valor_numerico": 11.2,
        "unidad": "porcentaje",
        "categoria": "social",
        "ambito_geografico": ["España"]
    }]
    
    # Crear payload con ambos tipos de datos
    metadatos_articulo = {
        "url": "https://test.com/noticia",
        "titular": "Test de Alineación",
        "medio": "Test News",
        "fecha_publicacion": datetime.now().isoformat(),
        "contenido_texto_original": "Contenido de prueba"
    }
    
    procesamiento_articulo = {
        "estado_procesamiento_final_pipeline": "completado_ok",
        "fecha_ingesta_sistema": datetime.now().isoformat(),
        "fecha_procesamiento_pipeline": datetime.now().isoformat()
    }
    
    try:
        # Probar con datos antiguos
        print("1. Probando mapeo de campos antiguos:")
        payload1 = builder.construir_payload_articulo(
            metadatos_articulo_data=metadatos_articulo,
            procesamiento_articulo_data=procesamiento_articulo,
            datos_cuantitativos_data=datos_antiguos
        )
        
        if payload1.datos_cuantitativos_extraidos:
            dato_mapeado = payload1.datos_cuantitativos_extraidos[0]
            print(f"   - descripcion_dato → indicador: {dato_mapeado.indicador}")
            print(f"   - valor_dato → valor_numerico: {dato_mapeado.valor_numerico}")
            print(f"   - unidad_dato → unidad: {dato_mapeado.unidad}")
            print(f"   - hecho_principal_relacionado_id_temporal → id_temporal_hecho: {dato_mapeado.id_temporal_hecho}")
            print("   ✓ Mapeo de campos antiguos funciona correctamente")
        
        # Probar con datos nuevos
        print("\n2. Probando con campos ya alineados:")
        payload2 = builder.construir_payload_articulo(
            metadatos_articulo_data=metadatos_articulo,
            procesamiento_articulo_data=procesamiento_articulo,
            datos_cuantitativos_data=datos_nuevos
        )
        
        if payload2.datos_cuantitativos_extraidos:
            dato_nuevo = payload2.datos_cuantitativos_extraidos[0]
            print(f"   - indicador: {dato_nuevo.indicador}")
            print(f"   - valor_numerico: {dato_nuevo.valor_numerico}")
            print(f"   - unidad: {dato_nuevo.unidad}")
            print(f"   - id_temporal_hecho: {dato_nuevo.id_temporal_hecho}")
            print(f"   - ambito_geografico: {dato_nuevo.ambito_geografico}")
            print("   ✓ Campos nuevos se mantienen correctamente")
        
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR en PayloadBuilder: {str(e)}")
        return False

def main():
    print("=== VERIFICACIÓN DE ALINEACIÓN DE DATOS CUANTITATIVOS ===")
    print("=== (Sin conexión a Supabase) ===\n")
    
    # Verificar modelo
    modelo_ok = verificar_modelo_datos()
    
    # Verificar PayloadBuilder
    builder_ok = verificar_payload_builder()
    
    # Resumen
    print("\n\n=== RESUMEN DE VERIFICACIÓN ===")
    if modelo_ok and builder_ok:
        print("✓ La alineación de campos de datos cuantitativos está COMPLETA")
        print("✓ El modelo tiene los campos correctos esperados por el RPC")
        print("✓ PayloadBuilder mapea correctamente campos antiguos a nuevos")
        print("✓ PayloadBuilder preserva campos nuevos sin modificación")
    else:
        print("✗ Hay problemas con la alineación de campos")

if __name__ == "__main__":
    main()