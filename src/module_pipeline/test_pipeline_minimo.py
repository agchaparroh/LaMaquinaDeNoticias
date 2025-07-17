#!/usr/bin/env python3
"""
Test mínimo del pipeline - Criterio 1
=====================================
Verifica que el pipeline puede procesar un artículo de tamaño medio
y persistirlo exitosamente en Supabase.
"""

import asyncio
import os
import sys
import json
from datetime import datetime
from uuid import uuid4

# Añadir el directorio src al path
sys.path.insert(0, '/app/src')

from src.controller import PipelineController
from src.utils.config import GROQ_API_KEY

async def test_criterio_1():
    """Test del Criterio 1: Procesamiento de artículo medio con persistencia."""
    print("\n=== TEST CRITERIO 1: Artículo tamaño medio + persistencia ===\n")
    
    # Artículo de prueba (tamaño medio ~2000 caracteres)
    articulo_test = {
        "id": 1100,
        "url": "https://www.infobae.com/test/2025/07/17/test-pipeline-criterio-1",
        "medio": "Infobae Test",
        "tipo_medio": "otro",
        "titular": "La Unión Europea alcanza un acuerdo histórico sobre regulación de inteligencia artificial",
        "fecha_publicacion": "2025-07-17T10:00:00Z",
        "autor": "María García",
        "contenido_texto": """La Unión Europea ha logrado un acuerdo histórico sobre la regulación de la inteligencia artificial (IA), 
        estableciendo el primer marco legal integral del mundo para esta tecnología. El acuerdo, alcanzado tras largas 
        negociaciones entre el Parlamento Europeo y los estados miembros, busca equilibrar la innovación tecnológica 
        con la protección de los derechos fundamentales.

        La presidenta de la Comisión Europea, Ursula von der Leyen, calificó el acuerdo como "un momento decisivo para 
        Europa" y añadió que "este reglamento garantizará que la IA se desarrolle de manera que respete nuestros valores 
        y derechos fundamentales". Por su parte, el comisario de Mercado Interior, Thierry Breton, destacó que "Europa 
        se convierte en el primer continente en establecer normas claras para el uso de la IA".

        El nuevo reglamento establece diferentes niveles de riesgo para las aplicaciones de IA. Los sistemas considerados 
        de "riesgo inaceptable", como los sistemas de puntuación social al estilo chino o el reconocimiento facial 
        biométrico en espacios públicos con fines policiales, quedarán prohibidos con excepciones muy limitadas.

        Los sistemas de "alto riesgo", que incluyen aplicaciones en áreas críticas como salud, educación, empleo y 
        aplicación de la ley, estarán sujetos a estrictos requisitos antes de su comercialización. Estos incluyen 
        evaluaciones de riesgo, alta calidad de los conjuntos de datos, trazabilidad de los resultados y supervisión 
        humana adecuada.

        Las empresas tecnológicas han expresado preocupación por el impacto potencial en la innovación. Sam Altman, 
        CEO de OpenAI, advirtió que "una regulación excesivamente restrictiva podría frenar el desarrollo de la IA 
        en Europa". Sin embargo, defensores de los derechos civiles han aplaudido las medidas como necesarias para 
        proteger a los ciudadanos.

        El reglamento también aborda específicamente los modelos de IA generativa como ChatGPT, requiriendo transparencia 
        sobre el contenido generado por IA y salvaguardias contra la generación de contenido ilegal. Las multas por 
        incumplimiento pueden alcanzar hasta el 7% de la facturación global anual de una empresa.""",
        "idioma": "es",
        "seccion": "tecnologia",
        "area_geografica": "EUROPA"
    }
    
    controller = PipelineController()
    
    try:
        print(f"1. Procesando artículo ID: {articulo_test['id']}")
        print(f"   Titular: {articulo_test['titular'][:80]}...")
        print(f"   Tamaño: {len(articulo_test['contenido_texto'])} caracteres")
        
        resultado = await controller.process_article(articulo_test)
        
        print("\n2. Resultado del procesamiento:")
        print(f"   - Éxito: {resultado.get('exito', False)}")
        print(f"   - Fase completada: {resultado.get('fase_completada', 0)}/7")
        print(f"   - Request ID: {resultado.get('request_id', 'N/A')}")
        
        if resultado.get('payload'):
            print("\n3. Payload generado exitosamente")
            payload = resultado['payload']
            if hasattr(payload, 'resumen_generado_fragmento'):
                print(f"   - Resumen: {payload.resumen_generado_fragmento[:100]}...")
            print(f"   - Estado: {getattr(payload, 'estado_procesamiento_final_fragmento', 'N/A')}")
        
        if resultado.get('persistencia'):
            print("\n4. PERSISTENCIA EXITOSA EN SUPABASE:")
            persist_data = resultado['persistencia']
            print(f"   - Fragmento ID: {persist_data.get('fragmento_id', 'N/A')}")
            print(f"   - Hechos insertados: {persist_data.get('hechos_insertados', 0)}")
            print(f"   - Entidades insertadas: {persist_data.get('entidades_insertadas', 0)}")
            print(f"   - Citas insertadas: {persist_data.get('citas_insertadas', 0)}")
            print(f"   - Datos insertados: {persist_data.get('datos_insertados', 0)}")
            print("\n✅ CRITERIO 1 COMPLETADO: Procesamiento y persistencia exitosos")
        else:
            print("\n❌ CRITERIO 1 FALLIDO: No se completó la persistencia en Supabase")
            if resultado.get('errores'):
                print(f"   Errores: {resultado['errores']}")
        
        # Mostrar estadísticas del procesamiento
        if resultado.get('metadatos', {}).get('processor_stats'):
            stats = resultado['metadatos']['processor_stats']
            print("\n5. Estadísticas del procesamiento:")
            print(f"   - Total hechos: {stats.get('total_hechos', 0)}")
            print(f"   - Total entidades: {stats.get('total_entidades', 0)}")
            print(f"   - Total citas: {stats.get('total_citas', 0)}")
            print(f"   - Total datos: {stats.get('total_datos', 0)}")
            
        return resultado.get('exito', False) and resultado.get('persistencia') is not None
        
    except Exception as e:
        print(f"\n❌ ERROR en test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Verificar que tenemos API key de Groq
    if not GROQ_API_KEY:
        print("ERROR: No se encontró GROQ_API_KEY en las variables de entorno")
        sys.exit(1)
    
    # Ejecutar test
    success = asyncio.run(test_criterio_1())
    
    print("\n" + "="*60)
    if success:
        print("✅ TEST CRITERIO 1 PASADO")
        sys.exit(0)
    else:
        print("❌ TEST CRITERIO 1 FALLIDO")
        sys.exit(1)