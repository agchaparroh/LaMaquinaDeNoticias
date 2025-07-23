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

from ...src.controller import PipelineController
from ...src.utils.config import GROQ_API_KEY

async def test_criterio_1():
    """Test del Criterio 1: Procesamiento de artículo medio con persistencia."""
    print("\n=== TEST CRITERIO 1: Artículo tamaño medio + persistencia ===\n")
    
    # Artículo de prueba (tamaño medio ~2000 caracteres) - Cumple criterios de relevancia
    articulo_test = {
        "id": 1100,
        "url": "https://www.infobae.com/test/2025/07/17/test-pipeline-criterio-1",
        "medio": "Infobae Test",
        "tipo_medio": "otro",
        "titular": "Congreso de México aprueba reforma judicial que elimina autonomía de la Corte Suprema",
        "fecha_publicacion": "2025-07-17T10:00:00Z",
        "autor": "Roberto Hernández",
        "contenido_texto": """El Congreso de México aprobó este jueves 17 de julio de 2025 una controvertida reforma judicial 
        que modifica sustancialmente la estructura y funcionamiento del Poder Judicial, eliminando la autonomía de la 
        Suprema Corte de Justicia de la Nación (SCJN) y estableciendo un nuevo sistema de elección popular para los magistrados.

        La votación en la Cámara de Diputados concluyó con 334 votos a favor, 166 en contra y 0 abstenciones, superando 
        la mayoría calificada necesaria de dos tercios. El presidente Andrés Manuel López Obrador celebró la aprobación 
        declarando que "hoy es un día histórico para la justicia mexicana".

        La ministra presidenta de la SCJN, Norma Lucía Piña Hernández, advirtió que la reforma "representa un retroceso 
        de 100 años en la independencia judicial" y anunció que presentarán recursos ante organismos internacionales. 
        "Esta reforma viola los principios fundamentales de separación de poderes establecidos en nuestra Constitución", 
        afirmó Piña Hernández.

        Los cambios principales incluyen: la elección popular directa de ministros, magistrados y jueces federales cada 
        seis años; la reducción de 11 a 9 ministros en la SCJN; la eliminación del Consejo de la Judicatura Federal; 
        y la creación de un Tribunal de Disciplina Judicial controlado por el Ejecutivo.

        La oposición, liderada por el PAN, PRI y PRD, denunció irregularidades en el proceso legislativo. El coordinador 
        del PAN en el Senado, Julen Rementería, señaló que "se está destruyendo el equilibrio de poderes para concentrar 
        todo el poder en el Ejecutivo". Por su parte, la senadora del PRI, Claudia Ruiz Massieu, calificó la reforma 
        como "un golpe de Estado técnico".

        Organizaciones civiles y barras de abogados convocaron a protestas masivas para el próximo sábado 20 de julio. 
        La Barra Mexicana de Abogados emitió un comunicado alertando sobre "las graves consecuencias para el Estado de 
        Derecho y la seguridad jurídica del país".

        La reforma debe ser ratificada por al menos 17 congresos estatales para entrar en vigor. Hasta el momento, 
        15 estados controlados por Morena han anunciado su apoyo, mientras que la oposición busca frenar el proceso 
        en estados como Coahuila y Nuevo León, donde gobierna en coalición.""",
        "idioma": "es",
        "seccion": "politica",
        "area_geografica": "MEXICO"
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