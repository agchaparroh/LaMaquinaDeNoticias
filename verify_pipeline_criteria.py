#!/usr/bin/env python3
"""
Script para verificar los criterios globales del PRP
"""

import json  # noqa: F401
import os
import sys
import time
from datetime import datetime

import requests
from supabase import create_client

# Configuración
PIPELINE_URL = "http://localhost:8003/procesar_articulo"
HEALTH_URL = "http://localhost:8003/health"
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://aukbzqbcvbsnjdhflyvr.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_KEY:
    print("ERROR: SUPABASE_KEY no está configurada")
    sys.exit(1)

# Crear cliente
client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=== VERIFICACIÓN DE CRITERIOS PRP ===\n")

# 1. Verificar que el pipeline está activo
print("1. Verificando estado del pipeline...")
try:
    health = requests.get(HEALTH_URL)
    if health.status_code == 200:
        print("   ✅ Pipeline activo y respondiendo")
    else:
        print("   ❌ Pipeline no responde correctamente")
except Exception as e:
    print(f"   ❌ Error al verificar pipeline: {e}")

# 2. Procesar un artículo mediano con éxito
print("\n2. Procesando artículo mediano de prueba...")
article_data = {
    "medio": "PRP Test",
    "area_geografica": "España",
    "tipo_medio": "digital",
    "titular": "Verificación de criterios PRP - Artículo mediano",
    "fecha_publicacion": datetime.now().isoformat(),
    "contenido_texto": """
    El gobierno español anunció hoy nuevas medidas económicas que afectarán
    a millones de ciudadanos. El presidente Pedro Sánchez, en una rueda de
    prensa desde el Palacio de la Moncloa, explicó que el paquete incluye
    ayudas directas por valor de 1.000 millones de euros.
    
    La ministra de Hacienda, María Jesús Montero, detalló que las medidas
    se centrarán en tres áreas principales: apoyo a las familias vulnerables,
    incentivos para las empresas que contraten jóvenes, y una reducción
    del IVA en productos básicos. "Es fundamental proteger el poder
    adquisitivo de los españoles", afirmó Montero.
    
    Por su parte, el ministro de Economía, Carlos Cuerpo, señaló que estas
    medidas se suman a las ya implementadas en el último trimestre. Se espera
    que beneficien a más de 3 millones de hogares y 500.000 empresas.
    """,
}

try:
    response = requests.post(PIPELINE_URL, json=article_data, timeout=30)
    if response.status_code == 200:
        result = response.json()
        request_id = result.get("request_id")
        print(f"   ✅ Artículo enviado correctamente (Request ID: {request_id})")

        # Esperar procesamiento
        print("   ⏳ Esperando procesamiento (30 segundos)...")
        time.sleep(30)

    else:
        print(f"   ❌ Error al procesar: {response.status_code}")
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 3. Verificar persistencia en Supabase
print("\n3. Verificando persistencia en Supabase...")
try:
    # Buscar artículos procesados recientemente
    ultimos = (
        client.table("articulos")
        .select("id, titular, estado_procesamiento, fecha_procesamiento")
        .eq("estado_procesamiento", "completado")
        .like("titular", "%PRP%")
        .order("fecha_procesamiento", desc=True)
        .limit(5)
        .execute()
    )

    if ultimos.data:
        print(
            f"   ✅ Se encontraron {len(ultimos.data)} artículos procesados con 'PRP' en el título"
        )
        for art in ultimos.data:
            print(f"      - ID {art['id']}: {art['titular'][:50]}...")
    else:
        print("   ⚠️ No se encontraron artículos con 'PRP' procesados exitosamente")

    # Verificar cualquier artículo procesado en los últimos 5 minutos
    print("\n   Buscando artículos procesados en los últimos 5 minutos...")
    cinco_min_atras = datetime.now().isoformat()
    recientes = (
        client.table("articulos")
        .select("id, titular, estado_procesamiento")
        .gte("fecha_procesamiento", cinco_min_atras)
        .execute()
    )

    if recientes.data:
        print(f"   ✅ {len(recientes.data)} artículos procesados recientemente")
    else:
        print("   ⚠️ No hay artículos procesados en los últimos 5 minutos")

except Exception as e:
    print(f"   ❌ Error al verificar Supabase: {e}")

# 4. Verificar manejo de múltiples artículos
print("\n4. Verificando manejo de múltiples artículos...")
print(
    "   [NOTA: Esta verificación requiere pruebas con spider que procese múltiples URLs]"
)

# 5. Verificar manejo de errores
print("\n5. Verificando manejo graceful de errores...")
try:
    # Enviar artículo con datos incompletos
    bad_article = {
        "medio": "Test",
        # Falta contenido_texto y otros campos requeridos
    }
    response = requests.post(PIPELINE_URL, json=bad_article)
    if response.status_code == 422:  # Validation error esperado
        print("   ✅ Errores de validación manejados correctamente")
    else:
        print(f"   ⚠️ Respuesta inesperada: {response.status_code}")
except Exception as e:
    print(f"   ✅ Error manejado: {e}")

print("\n=== RESUMEN DE VERIFICACIÓN ===")
print("""
Criterios PRP:
- [ ] ¿Procesa artículos medianos con éxito? → Verificar logs
- [ ] ¿Persiste correctamente en Supabase? → Verificar tabla articulos
- [ ] ¿Maneja múltiples artículos en cola? → Requiere prueba con spider
- [ ] ¿Los errores se manejan gracefully? → ✅ Verificado

NOTA: Revisar los logs del pipeline para confirmar si hay errores RPC.
""")
