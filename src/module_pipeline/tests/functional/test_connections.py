#!/usr/bin/env python3
"""
Script de verificación de conectividad para Module Pipeline
=========================================================

Este script verifica la conectividad con:
1. Groq API
2. Supabase
3. Otros servicios configurados

Uso:
    python scripts/test_connections.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Añadir src al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv no instalado. Variables de entorno pueden no cargarse.")


async def test_groq_connection():
    """Verificar conectividad con Groq API."""
    print("🤖 Verificando conexión con Groq API...")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "gsk_your_groq_api_key_here":
        print("❌ GROQ_API_KEY no configurada")
        return False

    try:
        from groq import Groq

        client = Groq(api_key=api_key)

        # Test simple: listar modelos
        models = client.models.list()
        if models:
            print("✅ Conexión con Groq exitosa")
            print(f"   Modelos disponibles: {len(models.data)}")

            # Verificar modelo específico
            model_id = os.getenv("MODEL_ID", "llama-3.1-8b-instant")
            model_found = any(model.id == model_id for model in models.data)

            if model_found:
                print(f"✅ Modelo {model_id} disponible")
            else:
                print(f"⚠️  Modelo {model_id} no encontrado")
                print("   Modelos disponibles:")
                for model in models.data[:5]:  # Mostrar solo los primeros 5
                    print(f"   - {model.id}")

            return True
        else:
            print("❌ No se pudieron obtener modelos de Groq")
            return False

    except ImportError:
        print("❌ Librería 'groq' no instalada")
        return False
    except Exception as e:
        print(f"❌ Error conectando con Groq: {e}")
        return False


async def test_supabase_connection():
    """Verificar conectividad con Supabase."""
    print("\n🗄️  Verificando conexión con Supabase...")

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or url == "https://tu-proyecto.supabase.co":
        print("❌ SUPABASE_URL no configurada")
        return False

    if not key or key.startswith("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your_"):
        print("❌ SUPABASE_KEY no configurada")
        return False

    try:
        from supabase import Client, create_client

        supabase: Client = create_client(url, key)

        # Test simple: verificar que podemos conectar
        # Intentamos hacer una consulta básica a una tabla que debería existir
        response = supabase.rpc("get_database_version").execute()

        if response:
            print("✅ Conexión con Supabase exitosa")
            return True
        else:
            print("❌ No se pudo conectar con Supabase")
            return False

    except ImportError:
        print("❌ Librería 'supabase' no instalada")
        return False
    except Exception as e:
        print(f"❌ Error conectando con Supabase: {e}")
        print("   Verificar URL, key y que el proyecto esté activo")
        return False


async def test_required_rpcs():
    """Verificar que las RPCs requeridas están disponibles."""
    print("\n🔧 Verificando RPCs de Supabase...")

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("⚠️  Saltando verificación de RPCs (Supabase no configurado)")
        return False

    try:
        from supabase import Client, create_client

        supabase: Client = create_client(url, key)

        required_rpcs = [
            "insertar_articulo_completo",
            "insertar_fragmento_completo",
            "buscar_entidad_similar",
        ]

        rpc_results = []

        for rpc_name in required_rpcs:
            try:
                # Intentar llamar la RPC con parámetros de prueba
                # Esto fallará por parámetros incorrectos, pero nos dirá si la RPC existe
                if rpc_name == "buscar_entidad_similar":
                    supabase.rpc(rpc_name, {"nombre_entidad": "test"}).execute()
                else:
                    supabase.rpc(rpc_name, {"p_articulo_data": {}}).execute()

                print(f"✅ RPC {rpc_name} disponible")
                rpc_results.append(True)

            except Exception as e:
                error_msg = str(e).lower()
                # Si el error es sobre parámetros, la RPC existe
                if (
                    "parameter" in error_msg
                    or "argument" in error_msg
                    or "null value" in error_msg
                ):
                    print(f"✅ RPC {rpc_name} disponible")
                    rpc_results.append(True)
                # Si el error es sobre función no encontrada, la RPC no existe
                elif "function" in error_msg and "does not exist" in error_msg:
                    print(f"❌ RPC {rpc_name} no encontrada")
                    rpc_results.append(False)
                else:
                    print(f"⚠️  RPC {rpc_name} - Error desconocido: {e}")
                    rpc_results.append(False)

        return all(rpc_results)

    except Exception as e:
        print(f"❌ Error verificando RPCs: {e}")
        return False


async def test_optional_services():
    """Verificar servicios opcionales."""
    print("\n🔍 Verificando servicios opcionales...")

    # Verificar spaCy si está habilitado
    use_spacy = os.getenv("USE_SPACY_FILTER", "false").lower() == "true"

    if use_spacy:
        try:
            import spacy

            # Verificar modelo en español
            try:
                nlp = spacy.load("es_core_news_lg")
                print("✅ spaCy modelo español (es_core_news_lg) cargado")
            except OSError:
                print("⚠️  spaCy modelo español no encontrado")
                print("   Ejecutar: python -m spacy download es_core_news_lg")

            # Verificar modelo en inglés
            try:
                nlp = spacy.load("en_core_web_sm")  # noqa: F841
                print("✅ spaCy modelo inglés (en_core_web_sm) cargado")
            except OSError:
                print("⚠️  spaCy modelo inglés no encontrado")
                print("   Ejecutar: python -m spacy download en_core_web_sm")

        except ImportError:
            print("❌ spaCy no instalado (habilitado en configuración)")
    else:
        print("ℹ️  spaCy deshabilitado en configuración")

    # Verificar Sentry si está habilitado
    use_sentry = os.getenv("USE_SENTRY", "false").lower() == "true"

    if use_sentry:
        try:
            import sentry_sdk  # noqa: F401

            sentry_dsn = os.getenv("SENTRY_DSN")

            if sentry_dsn and not sentry_dsn.startswith("https://your-sentry"):
                print("✅ Sentry configurado")
            else:
                print("⚠️  Sentry habilitado pero DSN no configurado")

        except ImportError:
            print("❌ Sentry no instalado (habilitado en configuración)")
    else:
        print("ℹ️  Sentry deshabilitado en configuración")


async def main():
    """Función principal."""
    print("🌐 Verificación de Conectividad - Module Pipeline")
    print("=" * 55)

    tests = [
        ("Groq API", test_groq_connection),
        ("Supabase", test_supabase_connection),
        ("RPCs Supabase", test_required_rpcs),
        ("Servicios Opcionales", test_optional_services),
    ]

    results = []

    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Error en {name}: {e}")
            results.append((name, False))

    # Resumen final
    print("\n" + "=" * 55)
    print("📋 RESUMEN DE CONECTIVIDAD")
    print("=" * 55)

    passed = 0
    critical_passed = 0
    critical_tests = ["Groq API", "Supabase"]  # Tests críticos

    for name, result in results:
        status = "✅ CONECTADO" if result else "❌ FALLIDO"
        priority = "🔴 CRÍTICO" if name in critical_tests else "🟡 OPCIONAL"

        print(f"{name:.<20} {status} {priority}")

        if result:
            passed += 1
            if name in critical_tests:
                critical_passed += 1

    print(f"\nResultado: {passed}/{len(results)} servicios conectados")
    print(f"Críticos: {critical_passed}/{len(critical_tests)} servicios críticos")

    if critical_passed == len(critical_tests):
        print("\n🎉 ¡Servicios críticos conectados! Pipeline puede funcionar.")
        if passed == len(results):
            print("✨ Todos los servicios funcionando perfectamente.")
    else:
        print("\n⚠️  Servicios críticos no disponibles. Pipeline no funcionará.")
        print("\nAcciones requeridas:")
        for name, result in results:
            if not result and name in critical_tests:
                if name == "Groq API":
                    print("- Configurar GROQ_API_KEY válida")
                elif name == "Supabase":
                    print("- Configurar SUPABASE_URL y SUPABASE_KEY válidas")

        return 1

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
