#!/usr/bin/env python3
"""
Script para iniciar el procesamiento de un artículo pendiente dinámicamente
Versión corregida que usa artículos reales de la BD en lugar de datos hardcodeados
"""

import json
import os
import sys

import requests
from supabase import create_client

# Configuración con variables de entorno
PIPELINE_URL = os.getenv(
    "PIPELINE_URL", "http://localhost:8003/procesar_articulo"
)  # CORREGIDO: endpoint correcto
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://aukbzqbcvbsnjdhflyvr.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")  # Usar ANON_KEY como el pipeline

if not SUPABASE_KEY:
    print("❌ ERROR: SUPABASE_ANON_KEY no está configurada")
    print("   Configura: export SUPABASE_ANON_KEY=tu_clave")
    sys.exit(1)


def get_latest_pending_article():
    """Obtiene el último artículo pendiente de la BD"""
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Buscar último artículo pendiente con contenido
        response = (
            client.table("articulos")
            .select(
                "id, url, medio, area_geografica, tipo_medio, titular, fecha_publicacion, autor, idioma, seccion, es_opinion, es_oficial"
            )
            .eq("estado_procesamiento", "pendiente")
            .is_("contenido_texto", "null")
            .order("id", desc=True)
            .limit(1)
            .execute()
        )

        if response.data and len(response.data) > 0:
            return response.data[0]

        # Si no hay pendientes sin contenido, buscar cualquier pendiente
        response = (
            client.table("articulos")
            .select(
                "id, url, medio, area_geografica, tipo_medio, titular, fecha_publicacion, autor, idioma, seccion, es_opinion, es_oficial, contenido_texto"
            )
            .eq("estado_procesamiento", "pendiente")
            .order("id", desc=True)
            .limit(1)
            .execute()
        )

        if response.data and len(response.data) > 0:
            return response.data[0]

        return None

    except Exception as e:
        print(f"❌ Error al obtener artículo de BD: {e}")
        return None


def create_test_article():
    """Crea artículo de prueba cuando no hay artículos pendientes"""
    from datetime import datetime

    return {
        "url": f"https://test.example.com/article-{int(datetime.now().timestamp())}",
        "medio": "Test Script",
        "area_geografica": "HISPANOAMERICA",
        "tipo_medio": "digital",
        "titular": f"Artículo de prueba para pipeline - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "fecha_publicacion": datetime.now().isoformat(),
        "contenido_texto": """
        Este es un artículo de prueba generado automáticamente para verificar 
        el funcionamiento del pipeline. Contiene suficiente texto para superar 
        las validaciones mínimas de contenido y permitir el procesamiento completo
        a través de las 7 fases del sistema.
        
        El contenido incluye varios párrafos para simular un artículo real de
        mediana extensión que pueda ser procesado correctamente por el sistema
        de análisis y extracción de información.
        """,
        "autor": "Sistema de Testing",
        "idioma": "es",
        "seccion": "pruebas",
        "es_opinion": False,
        "es_oficial": False,
    }


def main():
    print("=== TRIGGER PIPELINE - VERSIÓN DINÁMICA ===")

    # Intentar obtener artículo real de la BD
    article_data = get_latest_pending_article()

    if article_data:
        print(f"✅ Usando artículo de BD - ID: {article_data.get('id')}")
        print(f"   URL: {article_data.get('url', 'N/A')[:60]}...")
        print(f"   Título: {article_data.get('titular', 'N/A')[:60]}...")

        # Si el artículo no tiene contenido_texto, agregarlo
        if not article_data.get("contenido_texto"):
            article_data["contenido_texto"] = "Contenido de prueba para procesamiento"

    else:
        print("⚠️  No se encontraron artículos pendientes en BD")
        print("   Creando artículo de prueba...")
        article_data = create_test_article()

    try:
        print(f"\n🚀 Enviando artículo al pipeline: {PIPELINE_URL}")
        response = requests.post(PIPELINE_URL, json=article_data, timeout=60)

        if response.status_code == 200:
            try:
                result = response.json()
                print(f"\n✅ Procesamiento iniciado exitosamente!")  # noqa: F541
                print(f"   Request ID: {result.get('request_id', 'N/A')}")
                print(f"   Job ID: {result.get('job_id', 'N/A')}")
                if "mensaje" in result:
                    print(f"   Mensaje: {result['mensaje']}")

            except json.JSONDecodeError:
                print(f"\n✅ Procesamiento iniciado (respuesta no JSON)")  # noqa: F541
                print(f"   Response: {response.text[:200]}...")

        else:
            print(f"\n❌ Error HTTP: {response.status_code}")
            try:
                error_detail = response.json()
                print(
                    f"   Error: {json.dumps(error_detail, indent=2, ensure_ascii=False)}"
                )
            except:  # noqa: E722
                print(f"   Response: {response.text}")

    except requests.exceptions.Timeout:
        print(f"\n⏱️  Timeout - El procesamiento puede estar en progreso")  # noqa: F541
        print("   Verifica logs del pipeline para confirmar estado")

    except Exception as e:
        print(f"\n❌ Error al conectar con el pipeline: {e}")
        print(f"   Verifica que el pipeline esté ejecutándose en: {PIPELINE_URL}")


if __name__ == "__main__":
    main()
