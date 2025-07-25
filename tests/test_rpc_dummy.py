#!/usr/bin/env python3
"""
Script de prueba para el RPC actualizar_articulo_procesado con datos dummy.
Verifica que la persistencia funcione correctamente con el nuevo formato.
"""

import json
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from supabase import create_client

# Cargar variables de entorno
load_dotenv()

# Conectar a Supabase
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

# Primero, necesitamos crear un artículo de prueba
print("=== CREANDO ARTÍCULO DE PRUEBA ===")

timestamp = int(datetime.now().timestamp())
articulo_data = {
    "url": f"https://ejemplo.com/noticia-test-{timestamp}",
    "storage_path": f"test/{datetime.now().strftime('%Y/%m/%d')}/test-article-{timestamp}.html.gz",
    "medio": "Test Media",
    "area_geografica": "HISPANOAMERICA",
    "tipo_medio": "digital",
    "titular": "Artículo de prueba para RPC",
    "fecha_publicacion": datetime.now(timezone.utc).isoformat(),
    "fecha_recopilacion": datetime.now(timezone.utc).isoformat(),
    "idioma": "es",
    "contenido_texto": "Este es un artículo de prueba para verificar el RPC.",
}

try:
    result = supabase.table("articulos").insert(articulo_data).execute()
    articulo_id = result.data[0]["id"]
    print(f"✅ Artículo creado con ID: {articulo_id}")
except Exception as e:
    print(f"❌ Error creando artículo: {e}")
    exit(1)

# Preparar datos dummy para el RPC
print("\n=== PREPARANDO DATOS PARA RPC ===")

datos_rpc = {
    "articulo_id": articulo_id,
    "resumen": "Este es un resumen generado por el pipeline de prueba",
    "categorias_asignadas": ["política", "economía", "tecnología"],
    "puntuacion_relevancia": 8,
    "area_geografica": "ARGENTINA",
    "entidades_autonomas": [
        {
            "id_temporal": "temp_ent_001",
            "nombre": "Juan Pérez González",
            "tipo": "PERSONA",
            "descripcion": "Ministro de Economía de la Nación",
            "alias": ["JPG", "Ministro Pérez"],
            "relevancia": 9,
            "metadata": {"cargo": "Ministro", "partido": "Independiente"},
        },
        {
            "id_temporal": "temp_ent_002",
            "nombre": "Ministerio de Economía",
            "tipo": "INSTITUCION",
            "descripcion": "Organismo gubernamental encargado de la política económica",
            "relevancia": 8,
            "metadata": {"tipo_institucion": "gubernamental", "nivel": "nacional"},
        },
        {
            "id_temporal": "temp_ent_003",
            "id_entidad_normalizada": 1,  # Simular entidad ya existente
            "nombre": "Argentina",
            "tipo": "LUGAR",
            "descripcion": "República Argentina",
            "relevancia": 7,
        },
    ],
    "hechos_extraidos": [
        {
            "id_temporal": "temp_hecho_001",
            "contenido": "El Ministro de Economía anunció un nuevo plan de estabilización económica con medidas fiscales y monetarias",
            "tipo_hecho": "ANUNCIO",
            "importancia": 9,
            "precision_temporal": "dia",
            "fecha_ocurrencia_inicio": datetime.now(timezone.utc).isoformat(),
            "fecha_ocurrencia_fin": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "pais": ["Argentina"],
                "region": ["Buenos Aires"],
                "ciudad": ["CABA"],
                "etiquetas": ["economía", "política fiscal", "inflación"],
            },
            "entidades_del_hecho": [
                {
                    "id_temporal": "temp_ent_001",
                    "tipo_relacion": "protagonista",
                    "relevancia_en_hecho": 10,
                },
                {
                    "id_temporal": "temp_ent_002",
                    "tipo_relacion": "protagonista",
                    "relevancia_en_hecho": 8,
                },
            ],
        },
        {
            "id_temporal": "temp_hecho_002",
            "contenido": "La inflación mensual se ubicó en 3.5% según el último informe oficial",
            "tipo_hecho": "SUCESO",
            "importancia": 7,
            "precision_temporal": "mes",
            "fecha_ocurrencia_inicio": "2024-01-01T00:00:00Z",
            "fecha_ocurrencia_fin": "2024-01-31T23:59:59Z",
            "metadata": {
                "pais": ["Argentina"],
                "etiquetas": ["inflación", "indicadores económicos"],
            },
        },
    ],
    "citas_textuales_extraidas": [
        {
            "cita": "Estamos implementando un conjunto integral de medidas para estabilizar la economía y recuperar el crecimiento",
            "id_temporal_entidad_emisora": "temp_ent_001",
            "id_temporal_hecho_contexto": "temp_hecho_001",
            "fecha_cita": datetime.now(timezone.utc).isoformat(),
            "contexto": "Durante la conferencia de prensa en el Ministerio",
            "relevancia": 5,
        },
        {
            "cita": "La inflación está mostrando signos de desaceleración",
            "id_temporal_entidad_emisora": "temp_ent_001",
            "contexto": "En declaraciones a la prensa",
            "relevancia": 4,
        },
    ],
    "datos_cuantitativos_extraidos": [
        {
            "id_temporal_hecho": "temp_hecho_002",
            "indicador": "Inflación mensual",
            "categoria": "económico",
            "valor_numerico": 3.5,
            "unidad": "%",
            "ambito_geografico": ["Argentina"],
            "periodo_referencia_inicio": "2024-01-01",
            "periodo_referencia_fin": "2024-01-31",
            "tendencia": "disminución",
        },
        {
            "indicador": "Déficit fiscal",
            "categoria": "presupuestario",
            "valor_numerico": 2.8,
            "unidad": "% del PBI",
            "ambito_geografico": ["Argentina"],
            "periodo_referencia_inicio": "2024-01-01",
            "periodo_referencia_fin": "2024-03-31",
            "tendencia": "estable",
        },
    ],
    "relaciones_hechos": [
        {
            "id_hecho_origen": "temp_hecho_001",
            "id_hecho_destino": "temp_hecho_002",
            "tipo_relacion": "respuesta_a",
            "fuerza_relacion": 8,
            "descripcion_relacion": "El plan económico es una respuesta a los niveles de inflación",
        }
    ],
    "relaciones_entidades": [
        {
            "id_entidad_origen": "temp_ent_001",
            "id_entidad_destino": "temp_ent_002",
            "tipo_relacion": "empleado_de",
            "descripcion": "Juan Pérez González dirige el Ministerio de Economía",
            "fuerza_relacion": 10,
        }
    ],
}

# Llamar al RPC
print("\n=== EJECUTANDO RPC ===")
print(f"Enviando datos para artículo ID: {articulo_id}")

try:
    result = supabase.rpc(
        "actualizar_articulo_procesado", {"datos_json": datos_rpc}
    ).execute()

    print("\n=== RESULTADO DEL RPC ===")
    print(json.dumps(result.data, indent=2, ensure_ascii=False))

    if result.data.get("status") == "exito":
        print("\n✅ RPC ejecutado exitosamente!")
        print(f"   - Hechos insertados: {result.data.get('hechos_insertados', 0)}")
        print(
            f"   - Entidades insertadas: {result.data.get('entidades_insertadas', 0)}"
        )
        print(f"   - Entidades nuevas: {result.data.get('entidades_nuevas', 0)}")
        print(f"   - Citas insertadas: {result.data.get('citas_insertadas', 0)}")
        print(
            f"   - Datos cuantitativos insertados: {result.data.get('datos_insertados', 0)}"
        )
        print(
            f"   - Relaciones insertadas: {result.data.get('relaciones_insertadas', 0)}"
        )
    else:
        print("\n❌ Error en RPC:")
        print(f"   Mensaje: {result.data.get('mensaje', 'Sin mensaje')}")
        print(f"   Código: {result.data.get('codigo_sql', 'Sin código')}")

except Exception as e:
    print(f"\n❌ Error ejecutando RPC: {e}")

# Verificar los datos insertados
print("\n=== VERIFICANDO DATOS INSERTADOS ===")

try:
    # Verificar artículo actualizado
    articulo = supabase.table("articulos").select("*").eq("id", articulo_id).execute()
    if articulo.data:
        art = articulo.data[0]
        print(f"\n📄 Artículo actualizado:")  # noqa: F541
        print(f"   - Estado: {art.get('estado_procesamiento')}")
        print(f"   - Resumen: {art.get('resumen', '')[:100]}...")
        print(f"   - Categorías: {art.get('categorias_asignadas')}")
        print(f"   - Puntuación: {art.get('puntuacion_relevancia')}")
        print(f"   - Área geográfica: {art.get('area_geografica')}")

    # Contar registros insertados
    hechos = (
        supabase.table("hecho_articulo")
        .select("count", count="exact")
        .eq("articulo_id", articulo_id)
        .execute()
    )
    print(f"\n📊 Hechos vinculados al artículo: {hechos.count}")

    citas = (
        supabase.table("citas_textuales")
        .select("count", count="exact")
        .eq("articulo_id", articulo_id)
        .execute()
    )
    print(f"💬 Citas vinculadas al artículo: {citas.count}")

    datos = (
        supabase.table("datos_cuantitativos")
        .select("count", count="exact")
        .eq("articulo_id", articulo_id)
        .execute()
    )
    print(f"📈 Datos cuantitativos vinculados: {datos.count}")

except Exception as e:
    print(f"❌ Error verificando datos: {e}")

print("\n=== PRUEBA COMPLETADA ===")
