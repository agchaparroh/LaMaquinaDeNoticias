"""
Test de verificación del procesamiento asíncrono
===============================================

Este script verifica que el procesamiento asíncrono funciona correctamente
para artículos y fragmentos largos.

Ejecutar con: python tests/test_async_processing.py
"""

import sys
import asyncio
import aiohttp
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Añadir el directorio src al PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Importar utilidades
from src.utils.config import API_HOST, API_PORT

# Configuración
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"
ASYNC_PROCESSING_THRESHOLD = 10_000  # Debe coincidir con main.py


def generate_long_article(length: int = 15_000) -> Dict[str, Any]:
    """
    Genera un artículo largo para pruebas de procesamiento asíncrono.
    
    Args:
        length: Longitud aproximada del contenido en caracteres
        
    Returns:
        Diccionario con datos del artículo
    """
    # Generar contenido largo con estructura realista
    paragraphs = []
    current_length = 0
    
    # Texto base que se repetirá con variaciones
    base_texts = [
        "Los investigadores del Instituto Nacional de Tecnología han desarrollado un nuevo sistema de inteligencia artificial capaz de analizar grandes volúmenes de datos en tiempo real. ",
        "El Dr. Carlos Martínez, director del proyecto, explicó que este avance representa un hito importante en el campo del procesamiento de lenguaje natural. ",
        "Durante la conferencia de prensa, se presentaron los resultados preliminares que muestran una mejora del 45% en la precisión del análisis semántico. ",
        "La implementación de esta tecnología podría revolucionar la forma en que las empresas procesan y analizan información no estructurada. ",
        "Según las estimaciones del equipo de investigación, el sistema podría estar disponible comercialmente en los próximos 18 meses. ",
        "Las pruebas realizadas con datasets de diferentes industrias han demostrado la versatilidad y robustez del algoritmo desarrollado. ",
        "El proyecto ha recibido financiación de diversas instituciones públicas y privadas interesadas en las aplicaciones prácticas de esta tecnología. ",
        "Los expertos del sector han destacado el potencial impacto que este desarrollo podría tener en áreas como la medicina, finanzas y educación. ",
    ]
    
    # Generar párrafos hasta alcanzar la longitud deseada
    paragraph_count = 0
    while current_length < length:
        # Crear párrafo combinando varios textos base
        paragraph = ""
        for i in range(3):  # 3 oraciones por párrafo
            text_idx = (paragraph_count + i) % len(base_texts)
            paragraph += base_texts[text_idx]
        
        # Añadir cita ocasional
        if paragraph_count % 4 == 0:
            paragraph += f'"Este es un momento histórico para la investigación en IA", afirmó el investigador principal. '
        
        # Añadir datos cuantitativos ocasionales
        if paragraph_count % 3 == 0:
            paragraph += f"Los datos muestran un incremento del {20 + paragraph_count}% en la eficiencia computacional. "
        
        paragraphs.append(paragraph.strip())
        current_length += len(paragraph)
        paragraph_count += 1
    
    # Combinar todos los párrafos
    contenido_texto = "\n\n".join(paragraphs)
    
    return {
        "medio": "Tech Innovation Daily",
        "pais_publicacion": "España",
        "tipo_medio": "Digital",
        "titular": "Revolucionario avance en inteligencia artificial: nuevo sistema procesa datos con precisión sin precedentes",
        "fecha_publicacion": datetime.utcnow().isoformat() + "Z",
        "contenido_texto": contenido_texto[:length],  # Ajustar a longitud exacta
        "url": "https://techinnovation.test/ai-breakthrough-2024",
        "autor": "María González",
        "idioma": "es",
        "seccion": "Tecnología",
        "es_opinion": False,
        "es_oficial": False,
        "metadata": {
            "tags": ["inteligencia artificial", "tecnología", "investigación"],
            "test_type": "async_processing",
            "content_length": length
        }
    }


async def test_articulo_largo_async():
    """Test 1: Enviar artículo largo y verificar procesamiento asíncrono."""
    print("\n🧪 Test 1: Procesamiento asíncrono de artículo largo")
    print("-" * 60)
    
    try:
        # Generar artículo largo
        articulo = generate_long_article(length=12_000)
        print(f"✅ Artículo generado: {len(articulo['contenido_texto'])} caracteres")
        print(f"   - Título: {articulo['titular'][:50]}...")
        print(f"   - Medio: {articulo['medio']}")
        
        # Enviar artículo vía POST
        async with aiohttp.ClientSession() as session:
            print(f"\n📤 Enviando artículo a {API_BASE_URL}/procesar_articulo...")
            start_time = time.time()
            
            async with session.post(
                f"{API_BASE_URL}/procesar_articulo",
                json=articulo,
                headers={"Content-Type": "application/json"}
            ) as response:
                response_time = time.time() - start_time
                response_data = await response.json()
                
                print(f"✅ Respuesta recibida en {response_time:.2f} segundos")
                print(f"   - Status code: {response.status}")
                print(f"   - Success: {response_data.get('success')}")
                print(f"   - Status: {response_data.get('status')}")
                
                # Verificar que es procesamiento asíncrono
                if response_data.get('status') == 'processing':
                    print(f"✅ Procesamiento asíncrono confirmado")
                    print(f"   - Job ID: {response_data.get('job_id')}")
                    print(f"   - Request ID: {response_data.get('request_id')}")
                    print(f"   - Mensaje: {response_data.get('message')}")
                    
                    # Obtener información de tracking
                    tracking = response_data.get('tracking', {})
                    print(f"\n📊 Información de tracking:")
                    print(f"   - Tiempo estimado: {tracking.get('estimated_time_seconds')} segundos")
                    print(f"   - Endpoint de status: {tracking.get('check_status_endpoint')}")
                    
                    # Verificar metadata
                    metadata = response_data.get('metadata', {})
                    print(f"\n📋 Metadata:")
                    print(f"   - Longitud: {metadata.get('longitud_caracteres')} caracteres")
                    print(f"   - Es artículo largo: {metadata.get('es_articulo_largo')}")
                    print(f"   - Threshold usado: {metadata.get('threshold_usado')}")
                    
                    # Verificar respuesta inmediata (debe ser < 1 segundo)
                    if response_time < 1.0:
                        print(f"\n✅ Respuesta inmediata confirmada ({response_time:.2f}s < 1s)")
                    else:
                        print(f"\n⚠️  Respuesta tardó más de lo esperado ({response_time:.2f}s)")
                    
                    return response_data.get('job_id')
                    
                else:
                    print(f"❌ No se detectó procesamiento asíncrono")
                    print(f"   - Status recibido: {response_data.get('status')}")
                    return None
                    
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        return None


async def check_job_status(job_id: str, max_attempts: int = 30, wait_seconds: int = 2):
    """
    Consulta periódicamente el estado de un job hasta que complete.
    
    Args:
        job_id: ID del job a consultar
        max_attempts: Máximo número de intentos
        wait_seconds: Segundos entre intentos
        
    Returns:
        Diccionario con el resultado final o None si falla
    """
    print(f"\n🔍 Consultando estado del job: {job_id}")
    print("-" * 40)
    
    async with aiohttp.ClientSession() as session:
        for attempt in range(max_attempts):
            try:
                async with session.get(f"{API_BASE_URL}/status/{job_id}") as response:
                    if response.status == 404:
                        print(f"❌ Job no encontrado: {job_id}")
                        return None
                    
                    status_data = await response.json()
                    job_status = status_data.get('data', {}).get('status')
                    
                    print(f"   Intento {attempt + 1}/{max_attempts}: Status = {job_status}")
                    
                    # Si está completado o falló, retornar resultado
                    if job_status == 'completed':
                        print(f"✅ Job completado exitosamente")
                        result = status_data.get('data', {}).get('result', {})
                        print(f"   - Fragmento ID: {result.get('fragmento_id')}")
                        print(f"   - Tiempo procesamiento: {result.get('tiempo_procesamiento_segundos')}s")
                        print(f"   - Elementos extraídos: {result.get('elementos_extraidos', {})}")
                        return status_data
                        
                    elif job_status == 'failed':
                        print(f"❌ Job falló")
                        error = status_data.get('data', {}).get('error', {})
                        print(f"   - Tipo: {error.get('tipo')}")
                        print(f"   - Mensaje: {error.get('mensaje')}")
                        return status_data
                    
                    # Si sigue procesando, esperar
                    await asyncio.sleep(wait_seconds)
                    
            except Exception as e:
                print(f"   Error consultando status: {e}")
                await asyncio.sleep(wait_seconds)
    
    print(f"⏱️  Timeout: Job no completó después de {max_attempts * wait_seconds} segundos")
    return None


async def test_multiples_requests_concurrentes():
    """Test 2: Enviar múltiples requests concurrentes."""
    print("\n🧪 Test 2: Múltiples requests concurrentes")
    print("-" * 60)
    
    try:
        # Generar 5 artículos de diferentes tamaños
        articulos = []
        sizes = [11_000, 12_000, 13_000, 14_000, 15_000]
        
        for i, size in enumerate(sizes):
            articulo = generate_long_article(length=size)
            articulo['titular'] = f"Artículo concurrente #{i+1}: {articulo['titular'][:30]}..."
            articulos.append(articulo)
        
        print(f"✅ Generados {len(articulos)} artículos de diferentes tamaños")
        for i, art in enumerate(articulos):
            print(f"   - Artículo {i+1}: {len(art['contenido_texto'])} caracteres")
        
        # Enviar todos los artículos concurrentemente
        print(f"\n📤 Enviando {len(articulos)} artículos simultáneamente...")
        start_time = time.time()
        
        async def send_article(session, article, index):
            """Envía un artículo y retorna el job_id."""
            try:
                async with session.post(
                    f"{API_BASE_URL}/procesar_articulo",
                    json=article,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    data = await response.json()
                    return {
                        'index': index,
                        'job_id': data.get('job_id'),
                        'status': data.get('status'),
                        'success': data.get('success')
                    }
            except Exception as e:
                return {
                    'index': index,
                    'error': str(e)
                }
        
        # Crear tareas concurrentes
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i, articulo in enumerate(articulos):
                task = send_article(session, articulo, i)
                tasks.append(task)
            
            # Ejecutar todas las tareas concurrentemente
            results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        print(f"✅ Todas las solicitudes enviadas en {total_time:.2f} segundos")
        
        # Verificar resultados
        job_ids = []
        for result in results:
            if 'error' in result:
                print(f"   ❌ Artículo {result['index']+1}: Error - {result['error']}")
            else:
                print(f"   ✅ Artículo {result['index']+1}: Job ID = {result['job_id']}")
                if result['job_id']:
                    job_ids.append(result['job_id'])
        
        print(f"\n📊 Resumen:")
        print(f"   - Jobs creados exitosamente: {len(job_ids)}/{len(articulos)}")
        print(f"   - Tiempo total: {total_time:.2f} segundos")
        print(f"   - Tiempo promedio por request: {total_time/len(articulos):.2f} segundos")
        
        # Verificar que el sistema maneja múltiples jobs
        if len(job_ids) == len(articulos):
            print(f"\n✅ El sistema maneja correctamente múltiples jobs concurrentes")
        else:
            print(f"\n⚠️  Algunos jobs no se crearon correctamente")
        
        return job_ids
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        return []


async def test_articulo_pequeno_sincrono():
    """Test 3: Verificar que artículos pequeños se procesan síncronamente."""
    print("\n🧪 Test 3: Procesamiento síncrono de artículo pequeño")
    print("-" * 60)
    
    try:
        # Generar artículo pequeño (menos del threshold)
        articulo = generate_long_article(length=5_000)  # Mitad del threshold
        print(f"✅ Artículo pequeño generado: {len(articulo['contenido_texto'])} caracteres")
        print(f"   - Bajo el threshold de {ASYNC_PROCESSING_THRESHOLD} caracteres")
        
        # Enviar artículo
        async with aiohttp.ClientSession() as session:
            print(f"\n📤 Enviando artículo pequeño...")
            start_time = time.time()
            
            async with session.post(
                f"{API_BASE_URL}/procesar_articulo",
                json=articulo,
                headers={"Content-Type": "application/json"}
            ) as response:
                response_time = time.time() - start_time
                response_data = await response.json()
                
                print(f"✅ Respuesta recibida en {response_time:.2f} segundos")
                print(f"   - Status code: {response.status}")
                print(f"   - Success: {response_data.get('success')}")
                
                # Verificar que NO es procesamiento asíncrono
                if 'data' in response_data and 'fase_1_triaje' in response_data['data']:
                    print(f"✅ Procesamiento síncrono confirmado")
                    print(f"   - Resultado completo recibido inmediatamente")
                    
                    # Verificar algunos elementos del resultado
                    data = response_data['data']
                    metricas = data.get('metricas', {})
                    print(f"\n📊 Métricas del procesamiento:")
                    print(f"   - Tiempo total: {metricas.get('tiempo_total_segundos', 0):.2f}s")
                    print(f"   - Hechos extraídos: {metricas.get('conteos_elementos', {}).get('hechos_extraidos', 0)}")
                    print(f"   - Entidades extraídas: {metricas.get('conteos_elementos', {}).get('entidades_extraidas', 0)}")
                    
                    return True
                    
                elif response_data.get('status') == 'processing':
                    print(f"❌ Se detectó procesamiento asíncrono (no esperado)")
                    print(f"   - El artículo pequeño debería procesarse síncronamente")
                    return False
                    
                else:
                    print(f"❌ Respuesta inesperada")
                    print(f"   - Data: {json.dumps(response_data, indent=2)}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Ejecutar todos los tests de procesamiento asíncrono."""
    print("=" * 80)
    print("TEST DE VERIFICACIÓN DE PROCESAMIENTO ASÍNCRONO")
    print("=" * 80)
    print(f"\n📍 API URL: {API_BASE_URL}")
    print(f"📏 Threshold asíncrono: {ASYNC_PROCESSING_THRESHOLD} caracteres")
    
    # Verificar que el API está activa
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_BASE_URL}/health") as response:
                if response.status == 200:
                    print(f"✅ API está activa y respondiendo")
                else:
                    print(f"❌ API no responde correctamente (status: {response.status})")
                    return 1
    except Exception as e:
        print(f"❌ No se puede conectar al API: {e}")
        print(f"   Asegúrate de que el servidor esté ejecutándose en {API_BASE_URL}")
        return 1
    
    # Test 1: Artículo largo asíncrono
    job_id = await test_articulo_largo_async()
    
    if job_id:
        # Esperar y verificar estado del job
        final_status = await check_job_status(job_id)
        if final_status:
            data = final_status.get('data', {})
            if data.get('status') == 'completed':
                print(f"\n✅ Test 1: Test asíncrono exitoso")
            else:
                print(f"\n❌ Test 1: Error - Job no completó exitosamente")
        else:
            print(f"\n❌ Test 1: Error - No se pudo verificar estado del job")
    else:
        print(f"\n❌ Test 1: Error - No se obtuvo job_id")
    
    # Test 2: Múltiples requests concurrentes
    job_ids = await test_multiples_requests_concurrentes()
    
    if job_ids:
        print(f"\n✅ Test 2: Múltiples requests concurrentes exitoso")
        print(f"   - Se crearon {len(job_ids)} jobs concurrentemente")
    else:
        print(f"\n❌ Test 2: Error - No se pudieron crear jobs concurrentes")
    
    # Test 3: Artículo pequeño síncrono
    sync_result = await test_articulo_pequeno_sincrono()
    
    if sync_result:
        print(f"\n✅ Test 3: Procesamiento síncrono verificado")
    else:
        print(f"\n❌ Test 3: Error - Procesamiento síncrono falló")
    
    # Resumen final
    print("\n" + "=" * 80)
    print("RESUMEN DE TESTS")
    print("=" * 80)
    
    test_results = {
        "Test 1 (Asíncrono)": job_id is not None,
        "Test 2 (Concurrencia)": len(job_ids) > 0,
        "Test 3 (Síncrono)": sync_result
    }
    
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("\n✅ ¡TODOS LOS TESTS PASARON! El procesamiento asíncrono funciona correctamente")
        return 0
    else:
        print(f"\n❌ {total - passed} tests fallaron. Revisa los errores arriba.")
        return 1


if __name__ == "__main__":
    # Ejecutar con asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
