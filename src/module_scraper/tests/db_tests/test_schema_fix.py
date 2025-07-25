#!/usr/bin/env python
"""
Test simple para verificar la corrección del esquema de base de datos
"""

import os  # noqa: F401
import sys
from datetime import datetime
from pathlib import Path

# Añadir el directorio del módulo al path
module_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(module_dir))

# Cargar variables de entorno de test
from dotenv import load_dotenv  # noqa: E402

env_test_path = module_dir / ".env.test"
load_dotenv(dotenv_path=env_test_path, override=True)

from scraper_core.items import ArticuloInItem  # noqa: E402
from scraper_core.utils.supabase_client import SupabaseClient  # noqa: E402


def test_schema_fix():
    """Test para verificar que la columna contenido_texto existe y funciona"""
    print("🔍 Verificando corrección del esquema de base de datos...")

    # 1. Crear cliente Supabase
    try:
        client = SupabaseClient()
        print("✓ Cliente Supabase conectado")
    except Exception as e:
        print(f"✗ Error conectando a Supabase: {e}")
        return False

    # 2. Verificar que la columna contenido_texto existe
    try:
        query = """
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'articulos' 
        AND table_schema = 'public'
        AND column_name = 'contenido_texto'
        """
        response = client.client.table("articulos").select("*").limit(0).execute()
        print("✓ Tabla articulos accesible")

        # Verificar estructura de columnas
        result = client.client.rpc("exec_sql", {"query": query}).execute()  # noqa: F841
        print(f"✓ Consulta de esquema ejecutada")  # noqa: F541
    except Exception as e:
        print(f"✗ Error verificando esquema: {e}")

    # 3. Crear item de prueba
    try:
        item = ArticuloInItem()
        item["url"] = f"http://test.com/schema-test-{datetime.now().timestamp()}"
        item["titular"] = "Test Esquema Fix"
        item["contenido_texto"] = "Este es contenido de texto de prueba"
        item["medio"] = "Test Medio Schema"
        item["area_geografica"] = "Test"
        item["tipo_medio"] = "test"
        item["fecha_publicacion"] = datetime.now()

        print("✓ Item de prueba creado")

        # Convertir a dict para inserción
        data = {
            "url": item["url"],
            "titular": item["titular"],
            "contenido_texto": item["contenido_texto"],
            "medio": item["medio"],
            "area_geografica": item["area_geografica"],
            "tipo_medio": item["tipo_medio"],
            "fecha_publicacion": item["fecha_publicacion"].isoformat(),
            "fecha_recopilacion": datetime.now().isoformat(),
            "storage_path": f"test/schema/{datetime.now().timestamp()}.html.gz",
        }

        print("✓ Datos preparados para inserción")

    except Exception as e:
        print(f"✗ Error preparando item de prueba: {e}")
        return False

    # 4. Intentar insertar en base de datos
    try:
        response = client.upsert_articulo(data)
        print("✓ Inserción exitosa en base de datos")
        print(f"  URL insertada: {data['url']}")
        print(f"  contenido_texto guardado: {data['contenido_texto'][:50]}...")

    except Exception as e:
        print(f"✗ Error insertando en base de datos: {e}")
        return False

    # 5. Verificar que se puede leer el contenido_texto
    try:
        response = (
            client.client.table("articulos")
            .select("url, titular, contenido_texto")
            .eq("url", data["url"])
            .execute()
        )
        if response.data:
            record = response.data[0]
            print("✓ Lectura exitosa desde base de datos")
            print(f"  Titular: {record['titular']}")
            print(f"  contenido_texto leído: {record['contenido_texto'][:50]}...")
        else:
            print("✗ No se encontró el registro insertado")
            return False

    except Exception as e:
        print(f"✗ Error leyendo desde base de datos: {e}")
        return False

    # 6. Limpiar datos de prueba
    try:
        client.client.table("articulos").delete().eq("url", data["url"]).execute()
        print("✓ Datos de prueba limpiados")
    except Exception as e:
        print(f"⚠️ Advertencia: No se pudieron limpiar datos de prueba: {e}")

    print("\n🎉 ¡Corrección del esquema verificada exitosamente!")
    return True


if __name__ == "__main__":
    success = test_schema_fix()
    if not success:
        print("\n💥 El test falló. Revisa los errores arriba.")
        sys.exit(1)
    else:
        print("\n✅ Todas las verificaciones pasaron!")
        sys.exit(0)
