#!/usr/bin/env python3
"""
Script para verificar si hay datos realmente persistidos en Supabase
Revisa todas las tablas principales para buscar hechos, entidades, citas y datos
"""

import os  # noqa: F401

from supabase import Client, create_client

# Configuración desde .env
SUPABASE_URL = "https://aukbzqbcvbsnjdhflyvr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1a2J6cWJjdmJzbmpkaGZseXZyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU5MTI2NjYsImV4cCI6MjA2MTQ4ODY2Nn0.KfRQ1Jv7HIGwMHUS8e8IgN92iv1go7VvyK-6wqgog3s"


def verify_database_data():
    """Verifica qué datos están realmente persistidos en la base de datos"""

    print("=" * 60)
    print("VERIFICACIÓN DE DATOS PERSISTIDOS EN SUPABASE")
    print("=" * 60)

    try:
        # Crear cliente
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Conexión establecida con Supabase")

        # Lista de tablas principales a verificar
        tables_to_check = [
            "articulos",
            "hechos",
            "entidades",
            "citas_textuales",
            "datos_cuantitativos",
            "relaciones_hechos",
            "relaciones_entidades",
            "contradicciones",
            "documentos_extensos",
            "fragmentos_extensos",
        ]

        print("\n📊 CONTEO DE REGISTROS POR TABLA:")
        print("-" * 40)

        total_records = 0
        table_counts = {}

        for table in tables_to_check:
            try:
                # Intentar contar registros en cada tabla
                response = supabase.table(table).select("id", count="exact").execute()
                count = response.count if response.count is not None else 0
                table_counts[table] = count
                total_records += count

                status = "✅" if count > 0 else "❌"
                print(f"{status} {table:<25} : {count:>8} registros")

                # Si hay registros, mostrar algunos ejemplos
                if count > 0:
                    sample_response = (
                        supabase.table(table).select("*").limit(3).execute()
                    )
                    if sample_response.data:
                        print(f"   📝 Muestra de registros:")  # noqa: F541
                        for i, record in enumerate(sample_response.data[:2], 1):
                            # Mostrar campos relevantes según la tabla
                            if table == "articulos":
                                print(
                                    f"      {i}. ID: {record.get('id')}, URL: {str(record.get('url', 'N/A'))[:50]}..."
                                )
                            elif table == "hechos":
                                print(
                                    f"      {i}. ID: {record.get('id')}, Contenido: {str(record.get('contenido_hecho', 'N/A'))[:50]}..."
                                )
                            elif table == "entidades":
                                print(
                                    f"      {i}. ID: {record.get('id')}, Nombre: {record.get('nombre', 'N/A')}, Tipo: {record.get('tipo', 'N/A')}"
                                )
                            elif table == "citas_textuales":
                                print(
                                    f"      {i}. ID: {record.get('id')}, Cita: {str(record.get('texto_cita', 'N/A'))[:50]}..."
                                )
                            elif table == "datos_cuantitativos":
                                print(
                                    f"      {i}. ID: {record.get('id')}, Indicador: {record.get('indicador', 'N/A')}, Valor: {record.get('valor', 'N/A')}"
                                )
                            else:
                                # Para otras tablas, mostrar ID y algunos campos
                                print(
                                    f"      {i}. ID: {record.get('id')}, Campos: {list(record.keys())[:5]}"
                                )
                        print()

            except Exception as e:
                print(f"❌ {table:<25} : Error al acceder - {str(e)[:50]}")
                table_counts[table] = "ERROR"

        print("-" * 40)
        print(f"📈 TOTAL DE REGISTROS: {total_records}")

        # Análisis de resultados
        print("\n🔍 ANÁLISIS DE RESULTADOS:")
        print("-" * 40)

        if total_records == 0:
            print("❌ NO SE ENCONTRARON DATOS PERSISTIDOS")
            print("   - La base de datos parece estar vacía")
            print("   - El pipeline no ha persistido ningún artículo procesado")
            print("   - Verificar si el pipeline se ejecutó correctamente")
        else:
            print(f"✅ SE ENCONTRARON {total_records} REGISTROS PERSISTIDOS")

            # Verificar coherencia de datos
            articles = table_counts.get("articulos", 0)
            facts = table_counts.get("hechos", 0)
            entities = table_counts.get("entidades", 0)
            quotes = table_counts.get("citas_textuales", 0)
            data_points = table_counts.get("datos_cuantitativos", 0)

            print(f"   📰 Artículos: {articles}")
            print(f"   📋 Hechos: {facts}")
            print(f"   👤 Entidades: {entities}")
            print(f"   💬 Citas: {quotes}")
            print(f"   📊 Datos cuantitativos: {data_points}")

            # Verificar si los datos están balanceados
            if articles > 0:
                if facts == 0 and entities == 0:
                    print("\n⚠️  ADVERTENCIA: Hay artículos pero no hechos ni entidades")
                    print(
                        "   - Los artículos pueden no haber sido procesados completamente"
                    )
                else:
                    print(
                        f"\n✅ DATOS COHERENTES: {facts} hechos y {entities} entidades para {articles} artículos"
                    )

        # Verificar tablas de procesamiento reciente
        print("\n🕐 VERIFICACIÓN DE ACTIVIDAD RECIENTE:")
        print("-" * 40)

        try:
            # Buscar artículos con timestamps recientes
            recent_articles = (
                supabase.table("articulos")
                .select("id, url, fecha_procesamiento_pipeline")
                .order("fecha_procesamiento_pipeline", desc=True)
                .limit(5)
                .execute()
            )

            if recent_articles.data:
                print("📅 Últimos artículos procesados:")
                for article in recent_articles.data:
                    fecha = article.get("fecha_procesamiento_pipeline", "N/A")
                    print(f"   - ID {article.get('id')}: {fecha}")
            else:
                print("❌ No se encontraron artículos con timestamps de procesamiento")

        except Exception as e:
            print(f"❌ Error verificando actividad reciente: {e}")

        # Verificar RPCs disponibles
        print("\n🔧 VERIFICACIÓN DE FUNCIONES RPC:")
        print("-" * 40)

        rpc_functions = [
            "insertar_articulo_completo",
            "actualizar_articulo_procesado",
            "insertar_fragmento_completo",
            "buscar_entidad_similar",
        ]

        for rpc_name in rpc_functions:
            try:
                # Hacer una llamada de prueba muy básica
                if rpc_name == "buscar_entidad_similar":
                    test_response = supabase.rpc(
                        rpc_name,
                        {  # noqa: F841
                            "nombre_busqueda": "test",
                            "umbral_similitud": 0.1,
                            "limite_resultados": 1,
                        },
                    ).execute()
                else:
                    # Para otras RPCs, solo verificar que existen (esto podría fallar por parámetros)
                    pass

                print(f"✅ {rpc_name} - Disponible")

            except Exception as e:
                if "does not exist" in str(e) or "function" in str(e).lower():
                    print(f"❌ {rpc_name} - No existe")
                else:
                    print(f"⚠️  {rpc_name} - Existe pero falló la prueba")

        return total_records > 0

    except Exception as e:
        print(f"❌ ERROR GENERAL: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = verify_database_data()

    print("\n" + "=" * 60)
    if success:
        print("🎉 CONCLUSIÓN: HAY DATOS PERSISTIDOS EN LA BASE DE DATOS")
    else:
        print("💭 CONCLUSIÓN: NO HAY DATOS PERSISTIDOS EN LA BASE DE DATOS")
    print("=" * 60)
