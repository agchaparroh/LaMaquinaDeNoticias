#!/usr/bin/env python3
"""
Script para verificar el estado de artículos procesados dinámicamente
Versión corregida que puede verificar cualquier artículo o los más recientes
"""

import os
import sys

from supabase import create_client

# Configuración con variables de entorno
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://aukbzqbcvbsnjdhflyvr.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")  # Cambiar a ANON_KEY

if not SUPABASE_KEY:
    print("❌ ERROR: SUPABASE_ANON_KEY no está configurada")
    print("   Configura: export SUPABASE_ANON_KEY=tu_clave")
    sys.exit(1)


def check_specific_article(client, article_id):
    """Verifica un artículo específico por ID"""
    try:
        response = (
            client.table("articulos")
            .select("*")
            .eq("id", article_id)
            .single()
            .execute()
        )

        if response.data:
            articulo = response.data
            print(f"\n✅ Artículo ID {article_id} encontrado:")
            print(f"  - URL: {articulo.get('url', 'N/A')}")
            print(f"  - Título: {articulo.get('titular', 'N/A')[:80]}...")
            print(f"  - Estado: {articulo.get('estado_procesamiento', 'N/A')}")
            print(
                f"  - Fecha procesamiento: {articulo.get('fecha_procesamiento', 'N/A')}"
            )
            print(f"  - Resumen: {articulo.get('resumen', 'No disponible')}")

            error = articulo.get("error_detalle")
            if error:
                print(f"  - Error: {error[:100]}...")

            # Verificar elementos procesados si está completado
            if articulo.get("estado_procesamiento") == "completado":
                print(f"\n🎉 ARTÍCULO PROCESADO EXITOSAMENTE!")  # noqa: F541
                check_processed_elements(client, article_id)
                return True
            else:
                print(f"\n⚠️ Artículo en estado: {articulo.get('estado_procesamiento')}")
                return False
        else:
            print(f"\n❌ No se encontró artículo con ID {article_id}")
            return False

    except Exception as e:
        print(f"\n❌ Error al verificar artículo {article_id}: {e}")
        return False


def check_processed_elements(client, article_id):
    """Verifica elementos procesados para un artículo"""
    try:
        print(f"\n=== Elementos procesados para artículo {article_id} ===")

        # Hechos
        hechos = (
            client.table("hechos")
            .select("id, contenido")
            .eq("articulo_id", article_id)
            .execute()
        )
        print(f"✅ Hechos: {len(hechos.data) if hechos.data else 0}")
        if hechos.data and len(hechos.data) > 0:
            for i, hecho in enumerate(
                hechos.data[:3], 1
            ):  # Mostrar solo los primeros 3
                print(f"    {i}. {hecho.get('contenido', '')[:60]}...")

        # Entidades (directamente desde tabla entidades)
        entidades = (
            client.table("entidades")
            .select("id, nombre, tipo")
            .eq("articulo_id", article_id)
            .execute()
        )
        print(f"✅ Entidades: {len(entidades.data) if entidades.data else 0}")
        if entidades.data and len(entidades.data) > 0:
            for i, ent in enumerate(
                entidades.data[:5], 1
            ):  # Mostrar solo las primeras 5
                print(f"    {i}. {ent.get('nombre', 'N/A')} ({ent.get('tipo', 'N/A')})")

        # Citas
        citas = (
            client.table("citas_textuales")
            .select("id, cita")
            .eq("articulo_id", article_id)
            .execute()
        )
        print(f"✅ Citas: {len(citas.data) if citas.data else 0}")
        if citas.data and len(citas.data) > 0:
            for i, cita in enumerate(citas.data[:2], 1):  # Mostrar solo las primeras 2
                print(f'    {i}. "{cita.get("cita", "")[:80]}..."')

        # Datos cuantitativos
        datos = (
            client.table("datos_cuantitativos")
            .select("id, valor, unidad")
            .eq("articulo_id", article_id)
            .execute()
        )
        print(f"✅ Datos cuantitativos: {len(datos.data) if datos.data else 0}")
        if datos.data and len(datos.data) > 0:
            for i, dato in enumerate(datos.data[:3], 1):  # Mostrar solo los primeros 3
                print(f"    {i}. {dato.get('valor', 'N/A')} {dato.get('unidad', '')}")

    except Exception as e:
        print(f"❌ Error al verificar elementos procesados: {e}")


def show_recent_articles(client, limit=5):
    """Muestra artículos procesados recientemente"""
    try:
        print(f"\n=== Últimos {limit} artículos procesados exitosamente ===")

        ultimos = (
            client.table("articulos")
            .select("id, titular, fecha_procesamiento, estado_procesamiento")
            .eq("estado_procesamiento", "completado")
            .order("fecha_procesamiento", desc=True)
            .limit(limit)
            .execute()
        )

        if ultimos.data:
            for art in ultimos.data:
                fecha = art.get("fecha_procesamiento", "N/A")[:19]  # Solo fecha y hora
                print(f"  - ID {art['id']}: {art['titular'][:60]}... ({fecha})")
            return [art["id"] for art in ultimos.data]
        else:
            print("  ❌ No hay artículos procesados exitosamente")
            return []

    except Exception as e:
        print(f"❌ Error al obtener artículos recientes: {e}")
        return []


def show_pending_articles(client, limit=5):
    """Muestra artículos pendientes"""
    try:
        print(f"\n=== Artículos pendientes (últimos {limit}) ===")

        pendientes = (
            client.table("articulos")
            .select("id, titular, fecha_recopilacion")
            .eq("estado_procesamiento", "pendiente")
            .order("id", desc=True)
            .limit(limit)
            .execute()
        )

        if pendientes.data:
            for art in pendientes.data:
                fecha = art.get("fecha_recopilacion", "N/A")[:19]
                print(f"  - ID {art['id']}: {art['titular'][:60]}... ({fecha})")
            return [art["id"] for art in pendientes.data]
        else:
            print("  ❌ No hay artículos pendientes")
            return []

    except Exception as e:
        print(f"❌ Error al obtener artículos pendientes: {e}")
        return []


def main():
    """Función principal"""
    # Crear cliente
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    print("=== VERIFICADOR DE ESTADO DE ARTÍCULOS ===")

    # Si se proporciona un ID específico como argumento
    if len(sys.argv) > 1:
        try:
            article_id = int(sys.argv[1])
            print(f"🔍 Verificando artículo específico: ID {article_id}")
            check_specific_article(client, article_id)
            return
        except ValueError:
            print("❌ ERROR: El ID del artículo debe ser un número")
            sys.exit(1)

    # Mostrar artículos procesados recientemente
    completed_ids = show_recent_articles(client)

    # Mostrar artículos pendientes
    pending_ids = show_pending_articles(client)  # noqa: F841

    # Ofrecer verificar uno específico si hay completados
    if completed_ids:
        print(f"\n💡 Para verificar un artículo específico:")  # noqa: F541
        print(f"   python {sys.argv[0]} <ID>")
        print(f"   Ejemplo: python {sys.argv[0]} {completed_ids[0]}")

    # Estadísticas generales
    try:
        print(f"\n=== Estadísticas generales ===")  # noqa: F541

        # Contar por estado
        estados = ["pendiente", "completado", "error"]
        for estado in estados:
            count = (
                client.table("articulos")
                .select("id", count="exact")
                .eq("estado_procesamiento", estado)
                .execute()
            )
            print(f"  - {estado.capitalize()}: {count.count or 0}")

    except Exception as e:
        print(f"❌ Error al obtener estadísticas: {e}")


if __name__ == "__main__":
    main()
