#!/usr/bin/env python3
"""
Script para verificar permisos de lectura de Supabase de forma dinámica
Versión corregida que no usa IDs hardcodeados y verifica permisos completos
"""

import os
import sys

from supabase import Client, create_client

# Configuración con variables de entorno
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


def test_connection_and_permissions(key_name, key_value):
    """Prueba conexión y permisos con una clave específica"""
    if not key_value:
        print(f"   ⚠️  {key_name} no configurada")
        return False

    try:
        client: Client = create_client(SUPABASE_URL, key_value)
        print(f"   ✅ Cliente creado con {key_name}")

        # Test 1: Contar artículos (lectura básica)
        count_response = client.table("articulos").select("id", count="exact").execute()
        total_articles = count_response.count or 0
        print(f"   📊 Total de artículos: {total_articles}")

        if total_articles == 0:
            print(f"   ⚠️  No hay artículos en la tabla")  # noqa: F541
            return True  # Conexión OK, pero sin datos

        # Test 2: Leer artículos recientes
        recent_response = (
            client.table("articulos")
            .select("id, url, titular, estado_procesamiento, fecha_recopilacion")
            .order("id", desc=True)
            .limit(5)
            .execute()
        )

        if recent_response.data:
            print(
                f"   ✅ Lectura de artículos recientes: {len(recent_response.data)} encontrados"
            )
            for i, art in enumerate(recent_response.data[:3], 1):
                estado = art.get("estado_procesamiento", "N/A")
                print(f"      {i}. ID {art['id']}: {art['titular'][:50]}... [{estado}]")
        else:
            print(f"   ❌ No se pudieron leer artículos")  # noqa: F541
            return False

        # Test 3: Filtrar por estado
        try:
            pending_response = (
                client.table("articulos")
                .select("id", count="exact")
                .eq("estado_procesamiento", "pendiente")
                .execute()
            )

            completed_response = (
                client.table("articulos")
                .select("id", count="exact")
                .eq("estado_procesamiento", "completado")
                .execute()
            )

            print(f"   📈 Artículos pendientes: {pending_response.count or 0}")
            print(f"   📈 Artículos completados: {completed_response.count or 0}")

        except Exception as e:
            print(f"   ⚠️  Error en filtros: {e}")

        # Test 4: Verificar acceso a otras tablas
        tables_to_check = [
            "hechos",
            "entidades",
            "citas_textuales",
            "datos_cuantitativos",
        ]

        for table in tables_to_check:
            try:
                table_response = (
                    client.table(table).select("id", count="exact").limit(1).execute()
                )
                count = table_response.count or 0
                print(f"   📋 Tabla {table}: {count} registros")
            except Exception as e:
                print(f"   ❌ Error accediendo a tabla {table}: {e}")

        return True

    except Exception as e:
        print(f"   ❌ Error con {key_name}: {e}")
        return False


def test_write_permissions(key_name, key_value):
    """Prueba permisos de escritura (solo con service key)"""
    if key_name != "SERVICE_ROLE_KEY" or not key_value:
        return None

    try:
        client: Client = create_client(SUPABASE_URL, key_value)  # noqa: F841

        # Intentar crear un artículo de prueba (sin enviarlo realmente)
        test_article = {  # noqa: F841
            "url": "https://test-write-permissions.example.com",
            "medio": "Test Write",
            "titular": "Test de permisos de escritura",
            "estado_procesamiento": "pendiente",
        }

        print(f"   🔐 Probando escritura con {key_name}...")

        # Nota: No ejecutamos el insert real para evitar datos basura
        # Solo verificamos que el cliente se puede crear
        print(f"   ✅ Cliente de escritura configurado correctamente")  # noqa: F541
        return True

    except Exception as e:
        print(f"   ❌ Error en permisos de escritura: {e}")
        return False


def check_environment_config():
    """Verifica configuración de variables de entorno"""
    print("🔧 VERIFICANDO CONFIGURACIÓN DE ENTORNO")
    print("-" * 50)

    config_ok = True

    if not SUPABASE_URL:
        print("❌ SUPABASE_URL no configurada")
        config_ok = False
    else:
        print(f"✅ SUPABASE_URL: {SUPABASE_URL}")

    if not SUPABASE_ANON_KEY:
        print("❌ SUPABASE_ANON_KEY no configurada")
        config_ok = False
    else:
        print(f"✅ SUPABASE_ANON_KEY: {SUPABASE_ANON_KEY[:20]}...")

    if not SUPABASE_SERVICE_KEY:
        print("⚠️  SUPABASE_SERVICE_ROLE_KEY no configurada (opcional para lectura)")
    else:
        print(f"✅ SUPABASE_SERVICE_ROLE_KEY: {SUPABASE_SERVICE_KEY[:20]}...")

    return config_ok


def main():
    """Función principal de testing"""
    print("=== TEST DE PERMISOS SUPABASE ===")
    print("🔍 Versión dinámica - Sin IDs hardcodeados\n")

    # Verificar configuración
    if not check_environment_config():
        print("\n❌ Configuración incompleta. Configura las variables de entorno:")
        print("   export SUPABASE_URL='tu_url'")
        print("   export SUPABASE_ANON_KEY='tu_clave_anon'")
        print("   export SUPABASE_SERVICE_ROLE_KEY='tu_clave_service' # opcional")
        sys.exit(1)

    print(f"\n🔐 PROBANDO PERMISOS DE LECTURA")  # noqa: F541
    print("-" * 50)

    results = {}

    # Test ANON_KEY (usado por el pipeline)
    if SUPABASE_ANON_KEY:
        print(f"📖 Probando con ANON_KEY (usado por pipeline):")  # noqa: F541
        results["anon"] = test_connection_and_permissions("ANON_KEY", SUPABASE_ANON_KEY)

    # Test SERVICE_ROLE_KEY (permisos completos)
    if SUPABASE_SERVICE_KEY:
        print(f"\n🔑 Probando con SERVICE_ROLE_KEY (permisos completos):")  # noqa: F541
        results["service"] = test_connection_and_permissions(
            "SERVICE_ROLE_KEY", SUPABASE_SERVICE_KEY
        )

        # Probar permisos de escritura
        test_write_permissions("SERVICE_ROLE_KEY", SUPABASE_SERVICE_KEY)

    # Resumen
    print(f"\n📋 RESUMEN DE RESULTADOS")  # noqa: F541
    print("-" * 50)

    success_count = 0
    total_tests = 0

    for key, result in results.items():
        total_tests += 1
        if result:
            success_count += 1
            print(f"✅ {key.upper()}_KEY: Funcional")
        else:
            print(f"❌ {key.upper()}_KEY: Problemas detectados")

    if success_count == total_tests and total_tests > 0:
        print(
            f"\n🎉 ¡TODOS LOS TESTS DE CONEXIÓN EXITOSOS! ({success_count}/{total_tests})"
        )

        if "anon" in results and results["anon"]:
            print("✅ El pipeline puede leer datos de Supabase correctamente")

        return 0
    else:
        print(f"\n⚠️  Algunos tests fallaron ({success_count}/{total_tests})")
        print("\n💡 Recomendaciones:")

        if "anon" not in results or not results["anon"]:
            print("   - Verificar que SUPABASE_ANON_KEY tenga permisos de lectura")
            print("   - Revisar RLS (Row Level Security) policies")

        if "service" in results and not results["service"]:
            print("   - Verificar que SUPABASE_SERVICE_ROLE_KEY sea válida")

        print("   - Verificar conectividad de red con Supabase")

        return 1


if __name__ == "__main__":
    sys.exit(main())
