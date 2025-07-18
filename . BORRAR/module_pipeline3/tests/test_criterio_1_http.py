#!/usr/bin/env python3
"""
Test Criterio 1 via HTTP endpoint
=================================
Verifica procesamiento y persistencia usando el endpoint HTTP real.
"""

import requests
import json
import time
import sys

def test_criterio_1_http():
    """Test del Criterio 1 usando el endpoint HTTP."""
    print("\n=== TEST CRITERIO 1 VIA HTTP ===\n")
    
    # URL del endpoint
    url = "http://localhost:8003/procesar_articulo"
    
    # Artículo de prueba
    articulo_test = {
        "id": 1100,
        "url": "https://www.test.com/articulo-test-criterio-1",
        "medio": "Test News",
        "tipo_medio": "otro",
        "area_geografica": "EUROPA",
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
        aplicación de la ley, estarán sujetos a estrictos requisitos antes de su comercialización.""",
        "idioma": "es",
        "seccion": "tecnologia"
    }
    
    try:
        print(f"1. Enviando artículo al pipeline...")
        print(f"   Titular: {articulo_test['titular'][:60]}...")
        print(f"   Tamaño: {len(articulo_test['contenido_texto'])} caracteres\n")
        
        # Enviar request
        response = requests.post(url, json=articulo_test, timeout=60)
        
        if response.status_code != 200:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
        
        result = response.json()
        print(f"2. Respuesta inicial recibida:")
        print(f"   - Job ID: {result.get('job_id', 'N/A')}")
        print(f"   - Estado: {result.get('status', 'N/A')}")
        
        # Si hay job_id, esperar y verificar estado
        job_id = result.get('job_id')
        if job_id:
            print(f"\n3. Esperando procesamiento del job {job_id}...")
            
            # Esperar un tiempo razonable
            time.sleep(10)
            
            # Verificar estado del job
            status_url = f"http://localhost:8003/job_status/{job_id}"
            status_response = requests.get(status_url, timeout=30)
            
            if status_response.status_code == 200:
                job_status = status_response.json()
                print(f"\n4. Estado del job:")
                print(f"   - Estado: {job_status.get('status', 'N/A')}")
                print(f"   - Progreso: {job_status.get('progress', 0)}%")
                
                if job_status.get('result'):
                    resultado = job_status['result']
                    print(f"\n5. Resultado del procesamiento:")
                    print(f"   - Éxito: {resultado.get('exito', False)}")
                    print(f"   - Fase completada: {resultado.get('fase_completada', 0)}/7")
                    
                    if resultado.get('persistencia'):
                        persist = resultado['persistencia']
                        print(f"\n6. PERSISTENCIA EN SUPABASE:")
                        print(f"   - Exitosa: {persist.get('exitosa', False)}")
                        print(f"   - Fragmento ID: {persist.get('fragmento_id', 'N/A')}")
                        print(f"   - Hechos: {persist.get('hechos_insertados', 0)}")
                        print(f"   - Entidades: {persist.get('entidades_insertadas', 0)}")
                        
                        if persist.get('exitosa'):
                            print("\n✅ CRITERIO 1 COMPLETADO")
                            return True
                    
                    print("\n❌ No se encontró información de persistencia")
                    return False
        
        # Si no hay job_id, verificar resultado directo
        if result.get('persistencia'):
            print("\n✅ CRITERIO 1 COMPLETADO (resultado directo)")
            return True
        
        print("\n❌ No se completó la persistencia")
        return False
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_criterio_1_http()
    sys.exit(0 if success else 1)