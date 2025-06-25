"""
Test de configuración y conexión con Redis
Verifica que Redis esté correctamente configurado y accesible
"""
import os
import sys
import time
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from src.config import get_redis_client, RedisKeys, ConnectionManager
    from src.patterns import PatternStorage, Pattern, PatternStatus
    from src.analyzer import AnalysisStrategy
    print("✅ Imports exitosos")
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    sys.exit(1)


def test_redis_connection():
    """Test conexión básica a Redis"""
    print("\n=== TEST CONEXIÓN REDIS ===")
    
    try:
        redis_client = get_redis_client()
        print("✅ Cliente Redis creado")
        
        # Test ping
        pong = redis_client.ping()
        print(f"✅ Redis PING: {pong}")
        
        # Test set/get básico
        test_key = "test:connection"
        test_value = f"Test at {datetime.now().isoformat()}"
        
        redis_client.set(test_key, test_value, ex=60)
        retrieved = redis_client.get(test_key)
        
        assert retrieved == test_value
        print(f"✅ SET/GET funcionando: {retrieved}")
        
        # Limpiar
        redis_client.delete(test_key)
        
        return True
        
    except Exception as e:
        print(f"❌ Error conectando a Redis: {e}")
        return False


def test_redis_keys():
    """Test que las claves de Redis estén bien formateadas"""
    print("\n=== TEST REDIS KEYS ===")
    
    try:
        # Verificar formato de claves
        domain = "example.com"
        section = "noticias"
        
        pattern_key = RedisKeys.pattern("test-id")
        assert pattern_key.startswith("pattern:")
        print(f"✅ Pattern key: {pattern_key}")
        
        domain_patterns = RedisKeys.domain_patterns(domain)
        assert domain in domain_patterns
        print(f"✅ Domain patterns key: {domain_patterns}")
        
        analysis_cache = RedisKeys.analysis_cache(domain, section)
        assert domain in analysis_cache and section in analysis_cache
        print(f"✅ Analysis cache key: {analysis_cache}")
        
        spider_code = RedisKeys.spider_code("spider-test")
        assert spider_code.startswith("spider:code:")
        print(f"✅ Spider code key: {spider_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en keys de Redis: {e}")
        return False


def test_connection_manager():
    """Test del Connection Manager con pool"""
    print("\n=== TEST CONNECTION MANAGER ===")
    
    try:
        manager = ConnectionManager()
        print("✅ Connection Manager creado")
        
        # Obtener conexión del pool
        conn = manager.get_connection()
        print("✅ Conexión obtenida del pool")
        
        # Test operación
        conn.set("test:pool", "pool_test", ex=60)
        value = conn.get("test:pool")
        assert value == "pool_test"
        print(f"✅ Operación con pool exitosa: {value}")
        
        # Verificar estado del pool
        pool_stats = manager.get_pool_stats()
        print(f"✅ Estado del pool: {pool_stats}")
        
        # Limpiar
        conn.delete("test:pool")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en Connection Manager: {e}")
        return False


def test_pattern_storage_redis():
    """Test de PatternStorage con Redis real"""
    print("\n=== TEST PATTERN STORAGE ===")
    
    try:
        storage = PatternStorage()
        print("✅ PatternStorage creado")
        
        # Crear patrón de prueba
        test_pattern = Pattern(
            domain="test-redis.com",
            section="test-section",
            strategy=AnalysisStrategy.SCRAPING,
            confidence=0.75,
            status=PatternStatus.TESTING
        )
        
        # Guardar
        saved = storage.save_pattern(test_pattern)
        print(f"✅ Patrón guardado: {saved.id}")
        
        # Recuperar
        patterns = storage.get_patterns_by_domain_section("test-redis.com", "test-section")
        assert len(patterns) > 0
        assert patterns[0].domain == "test-redis.com"
        print(f"✅ Patrón recuperado: {patterns[0].id}")
        
        # Actualizar estadísticas
        storage.update_pattern_stats(saved.id, success=True)
        print("✅ Estadísticas actualizadas")
        
        # Limpiar
        redis_client = get_redis_client()
        redis_client.delete(f"pattern:{saved.id}")
        redis_client.srem("domain:test-redis.com:patterns", saved.id)
        
        return True
        
    except Exception as e:
        print(f"❌ Error en PatternStorage: {e}")
        return False


def test_redis_performance():
    """Test básico de rendimiento de Redis"""
    print("\n=== TEST RENDIMIENTO REDIS ===")
    
    try:
        redis_client = get_redis_client()
        
        # Test escrituras
        start_time = time.time()
        for i in range(100):
            redis_client.set(f"perf:test:{i}", f"value_{i}", ex=60)
        write_time = time.time() - start_time
        print(f"✅ 100 escrituras en {write_time:.3f}s ({100/write_time:.1f} ops/s)")
        
        # Test lecturas
        start_time = time.time()
        for i in range(100):
            redis_client.get(f"perf:test:{i}")
        read_time = time.time() - start_time
        print(f"✅ 100 lecturas en {read_time:.3f}s ({100/read_time:.1f} ops/s)")
        
        # Limpiar
        keys = redis_client.keys("perf:test:*")
        if keys:
            redis_client.delete(*keys)
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test de rendimiento: {e}")
        return False


def main():
    """Ejecutar todos los tests de Redis"""
    print("🔧 INICIANDO TESTS DE REDIS SETUP")
    print("=" * 50)
    
    # Verificar configuración
    print("\n📋 CONFIGURACIÓN:")
    print(f"REDIS_HOST: {os.getenv('REDIS_HOST', 'localhost')}")
    print(f"REDIS_PORT: {os.getenv('REDIS_PORT', '6379')}")
    print(f"REDIS_DB: {os.getenv('REDIS_DB', '0')}")
    
    tests = [
        ("Conexión Redis", test_redis_connection),
        ("Redis Keys", test_redis_keys),
        ("Connection Manager", test_connection_manager),
        ("Pattern Storage", test_pattern_storage_redis),
        ("Rendimiento", test_redis_performance)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Error ejecutando {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE TESTS:")
    print("=" * 50)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    total_pass = sum(1 for _, success in results if success)
    total_tests = len(results)
    
    print(f"\nTotal: {total_pass}/{total_tests} tests pasados")
    
    if total_pass == total_tests:
        print("\n🎉 TODOS LOS TESTS PASARON! Redis está correctamente configurado.")
        return 0
    else:
        print("\n⚠️ Algunos tests fallaron. Verifica la configuración de Redis.")
        return 1


if __name__ == "__main__":
    sys.exit(main())