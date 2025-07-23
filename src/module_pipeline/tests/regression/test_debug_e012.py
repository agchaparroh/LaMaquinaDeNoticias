#!/usr/bin/env python3
"""
Test de debug para E012 - Captura el error completo
"""

import asyncio
import sys
import traceback
from datetime import datetime

# Añadir el directorio src al path
sys.path.insert(0, '/app/src')

from ...src.controller import PipelineController
from ...src.utils.config import GROQ_API_KEY

async def test_debug_e012():
    """Test con captura completa de errores."""
    print("\n=== TEST DEBUG E012 ===\n")
    
    # Artículo mínimo
    articulo_test = {
        "id": 9999,
        "url": "https://test.com/debug-e012",
        "medio": "Test Debug",
        "tipo_medio": "otro",
        "titular": "Test E012: El gobierno anuncia nuevas medidas económicas",
        "fecha_publicacion": "2025-07-17T10:00:00Z",
        "autor": "Debug Test",
        "contenido_texto": """El gobierno anunció hoy un paquete de medidas económicas 
        destinadas a reactivar la economía. El ministro de Economía, Juan Pérez, 
        explicó que las medidas incluyen reducción de impuestos y aumento del gasto público. 
        "Estas medidas son necesarias para impulsar el crecimiento", declaró el ministro.""",
        "idioma": "es",
        "seccion": "politica",
        "area_geografica": "AMERICA"
    }
    
    controller = PipelineController()
    
    try:
        print(f"Procesando artículo ID: {articulo_test['id']}")
        print(f"Tamaño: {len(articulo_test['contenido_texto'])} caracteres")
        
        resultado = await controller.process_article(articulo_test)
        
        print(f"\n✅ Procesamiento completado:")
        print(f"   Éxito: {resultado.get('exito', False)}")
        print(f"   Fase: {resultado.get('fase_completada', 0)}/7")
        
        if resultado.get('persistencia'):
            print(f"\n📊 Persistencia:")
            persist = resultado['persistencia']
            print(f"   Hechos: {persist.get('hechos_insertados', 0)}")
            print(f"   Entidades: {persist.get('entidades_insertadas', 0)}")
            print(f"   Citas: {persist.get('citas_insertadas', 0)}")
        else:
            print(f"\n❌ Sin persistencia")
            
        if resultado.get('errores'):
            print(f"\n⚠️ Errores detectados:")
            for error in resultado.get('errores', []):
                print(f"   - {error}")
                
    except Exception as e:
        print(f"\n❌ ERROR CAPTURADO:")
        print(f"Tipo: {type(e).__name__}")
        print(f"Mensaje: {str(e)}")
        print(f"\n📍 TRACEBACK COMPLETO:")
        traceback.print_exc()
        
        # Intentar obtener más información del error
        if hasattr(e, '__dict__'):
            print(f"\n📋 Atributos del error:")
            for key, value in e.__dict__.items():
                print(f"   {key}: {value}")

if __name__ == "__main__":
    if not GROQ_API_KEY:
        print("ERROR: No se encontró GROQ_API_KEY")
        sys.exit(1)
    
    asyncio.run(test_debug_e012())