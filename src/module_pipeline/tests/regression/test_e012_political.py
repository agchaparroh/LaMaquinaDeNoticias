#!/usr/bin/env python3
"""
Test E012 con artículo claramente político
"""

import asyncio
import sys
import traceback

sys.path.insert(0, '/app/src')

from ...src.controller import PipelineController
from ...src.utils.config import GROQ_API_KEY

async def test_e012_political():
    """Test con artículo que debe pasar Fase 1."""
    print("\n=== TEST E012 - ARTÍCULO POLÍTICO ===\n")
    
    # Artículo claramente político que debe pasar Fase 1
    articulo_test = {
        "id": 8888,
        "url": "https://test.com/e012-political",
        "medio": "Test E012",
        "tipo_medio": "otro",
        "titular": "El presidente anuncia reforma constitucional tras reunión con el Congreso",
        "fecha_publicacion": "2025-07-17T10:00:00Z",
        "autor": "Test E012",
        "contenido_texto": """El presidente de la República anunció hoy una ambiciosa reforma constitucional 
        tras una reunión extraordinaria con líderes del Congreso Nacional. La propuesta, que modificaría 
        varios artículos fundamentales de la Constitución, busca ampliar los derechos sociales y reformar 
        el sistema electoral del país.

        Durante la conferencia de prensa, el mandatario declaró: "Esta reforma es necesaria para modernizar 
        nuestras instituciones democráticas y garantizar mayor participación ciudadana". La ministra de 
        Justicia, María González, explicó que el proyecto incluye cambios en el sistema de elección de 
        magistrados del Tribunal Supremo y la creación de nuevos mecanismos de democracia directa.

        Los partidos de oposición han expresado reservas sobre algunos aspectos de la reforma. El líder 
        del principal partido opositor, Carlos Mendoza, advirtió que "cualquier cambio constitucional debe 
        ser ampliamente consensuado y no puede vulnerar el equilibrio de poderes". Por su parte, los 
        sindicatos y organizaciones sociales han manifestado su apoyo a las reformas sociales propuestas.

        El proceso de reforma requerirá una mayoría calificada de dos tercios en ambas cámaras del Congreso, 
        seguido de un referéndum nacional. El gobierno espera iniciar el debate parlamentario la próxima 
        semana, con la meta de someter la propuesta a votación popular antes de fin de año.""",
        "idioma": "es",
        "seccion": "politica",
        "area_geografica": "AMERICA"
    }
    
    controller = PipelineController()
    
    try:
        print(f"Procesando artículo ID: {articulo_test['id']}")
        print(f"Título: {articulo_test['titular']}")
        print(f"Tamaño: {len(articulo_test['contenido_texto'])} caracteres")
        
        resultado = await controller.process_article(articulo_test)
        
        print(f"\n📊 RESULTADO:")
        print(f"   Éxito: {resultado.get('exito', False)}")
        print(f"   Fase completada: {resultado.get('fase_completada', 0)}/7")
        print(f"   Request ID: {resultado.get('request_id', 'N/A')}")
        
        # Verificar fases completadas
        if resultado.get('fase_completada', 0) < 7:
            print(f"\n⚠️ Pipeline terminó prematuramente en fase {resultado.get('fase_completada')}")
            if resultado.get('resultado_triaje'):
                print(f"   Triaje: relevante={resultado['resultado_triaje'].get('es_relevante')}")
        
        # Verificar persistencia
        if resultado.get('persistencia'):
            persist = resultado['persistencia']
            print(f"\n✅ PERSISTENCIA:")
            print(f"   Hechos insertados: {persist.get('hechos_insertados', 0)}")
            print(f"   Entidades insertadas: {persist.get('entidades_insertadas', 0)}")
            print(f"   Citas insertadas: {persist.get('citas_insertadas', 0)}")
            print(f"   Datos insertados: {persist.get('datos_insertados', 0)}")
            
            if persist.get('hechos_insertados', 0) > 0 or persist.get('entidades_insertadas', 0) > 0:
                print("\n🎉 E012 RESUELTO - Datos persistidos exitosamente!")
            else:
                print("\n❌ E012 PERSISTE - 0 datos persistidos")
        else:
            print(f"\n❌ Sin persistencia")
            if resultado.get('errores'):
                print(f"   Errores: {resultado['errores']}")
                
    except Exception as e:
        print(f"\n💥 EXCEPCIÓN CAPTURADA:")
        print(f"Tipo: {type(e).__name__}")
        print(f"Mensaje: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    if not GROQ_API_KEY:
        print("ERROR: No se encontró GROQ_API_KEY")
        sys.exit(1)
    
    asyncio.run(test_e012_political())