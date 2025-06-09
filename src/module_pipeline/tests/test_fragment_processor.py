"""
Test específico del FragmentProcessor
====================================

Test enfocado únicamente en verificar que el sistema de IDs secuenciales
funciona correctamente en todas las situaciones.
"""

import os
import sys
from pathlib import Path
from uuid import uuid4

print("🔧 Test específico del FragmentProcessor...")

# Configuración básica
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Configurar logging simple
from loguru import logger
logger.remove()
logger.add(sys.stderr, level="INFO", format="<level>{level: <8}</level> | <cyan>{message}</cyan>")

# Import del FragmentProcessor
try:
    from utils.fragment_processor import FragmentProcessor
    print("✅ FragmentProcessor importado exitosamente")
except ImportError as e:
    print(f"❌ Error importando FragmentProcessor: {e}")
    sys.exit(1)

def test_ids_secuenciales():
    """Test de generación de IDs secuenciales."""
    print("\n📊 TEST: IDs Secuenciales")
    print("-" * 40)
    
    id_fragmento = uuid4()
    processor = FragmentProcessor(id_fragmento)
    
    # Test básico de secuencia
    ids_hechos = []
    ids_entidades = []
    ids_citas = []
    ids_datos = []
    
    for i in range(10):
        ids_hechos.append(processor.next_hecho_id(f"Hecho {i+1}"))
        ids_entidades.append(processor.next_entidad_id(f"Entidad {i+1}"))
        ids_citas.append(processor.next_cita_id(f"Cita {i+1}"))
        ids_datos.append(processor.next_dato_id(f"Dato {i+1}"))
    
    # Verificar secuencias
    expected_sequence = list(range(1, 11))
    
    assert ids_hechos == expected_sequence, f"Hechos: esperado {expected_sequence}, obtenido {ids_hechos}"
    assert ids_entidades == expected_sequence, f"Entidades: esperado {expected_sequence}, obtenido {ids_entidades}"
    assert ids_citas == expected_sequence, f"Citas: esperado {expected_sequence}, obtenido {ids_citas}"
    assert ids_datos == expected_sequence, f"Datos: esperado {expected_sequence}, obtenido {ids_datos}"
    
    print(f"✅ Secuencias correctas:")
    print(f"   - Hechos: {ids_hechos[:5]}... (10 elementos)")
    print(f"   - Entidades: {ids_entidades[:5]}... (10 elementos)")
    print(f"   - Citas: {ids_citas[:5]}... (10 elementos)")
    print(f"   - Datos: {ids_datos[:5]}... (10 elementos)")
    
    return True

def test_multiples_fragmentos():
    """Test de IDs con múltiples fragmentos."""
    print("\n🔗 TEST: Múltiples Fragmentos")
    print("-" * 40)
    
    # Crear 3 fragmentos diferentes
    fragmentos = [uuid4() for _ in range(3)]
    processors = [FragmentProcessor(frag_id) for frag_id in fragmentos]
    
    # Generar IDs en cada fragmento
    for i, processor in enumerate(processors):
        hechos = [processor.next_hecho_id(f"F{i+1}_Hecho_{j+1}") for j in range(5)]
        entidades = [processor.next_entidad_id(f"F{i+1}_Entidad_{j+1}") for j in range(5)]
        
        expected = [1, 2, 3, 4, 5]
        assert hechos == expected, f"Fragmento {i+1} hechos incorrectos"
        assert entidades == expected, f"Fragmento {i+1} entidades incorrectas"
        
        print(f"✅ Fragmento {i+1}: Hechos={hechos}, Entidades={entidades}")
    
    return True

def test_estadisticas():
    """Test de estadísticas del processor."""
    print("\n📈 TEST: Estadísticas")
    print("-" * 40)
    
    id_fragmento = uuid4()
    processor = FragmentProcessor(id_fragmento)
    
    # Estado inicial
    stats_inicial = processor.get_stats()
    assert stats_inicial['total_hechos'] == 0
    assert stats_inicial['total_entidades'] == 0
    assert stats_inicial['total_citas'] == 0
    assert stats_inicial['total_datos'] == 0
    
    print("✅ Estado inicial correcto (todos en 0)")
    
    # Generar algunos elementos
    for i in range(3):
        processor.next_hecho_id(f"Hecho {i}")
        processor.next_entidad_id(f"Entidad {i}")
    
    for i in range(2):
        processor.next_cita_id(f"Cita {i}")
    
    processor.next_dato_id("Dato único")
    
    # Verificar estadísticas finales
    stats_final = processor.get_stats()
    
    assert stats_final['total_hechos'] == 3
    assert stats_final['total_entidades'] == 3
    assert stats_final['total_citas'] == 2
    assert stats_final['total_datos'] == 1
    
    print(f"✅ Estadísticas finales correctas:")
    print(f"   - Hechos: {stats_final['total_hechos']}")
    print(f"   - Entidades: {stats_final['total_entidades']}")
    print(f"   - Citas: {stats_final['total_citas']}")
    print(f"   - Datos: {stats_final['total_datos']}")
    
    return True

def test_referencias_globales():
    """Test de referencias globales."""
    print("\n🌐 TEST: Referencias Globales")
    print("-" * 40)
    
    id_fragmento = uuid4()
    processor = FragmentProcessor(id_fragmento)
    
    # Generar algunos IDs
    hecho_id = processor.next_hecho_id("Test hecho")
    entidad_id = processor.next_entidad_id("Test entidad")
    
    # Crear referencias globales
    ref_hecho = processor.get_global_reference("hecho", hecho_id)
    ref_entidad = processor.get_global_reference("entidad", entidad_id)
    
    print(f"✅ Referencias globales generadas:")
    print(f"   - Hecho: {ref_hecho}")
    print(f"   - Entidad: {ref_entidad}")
    
    # Parsear referencias
    parsed_hecho = processor.parse_global_reference(ref_hecho)
    parsed_entidad = processor.parse_global_reference(ref_entidad)
    
    assert parsed_hecho['fragmento_id'] == id_fragmento
    assert parsed_hecho['tipo'] == 'hecho'
    assert parsed_hecho['id_local'] == hecho_id
    
    assert parsed_entidad['fragmento_id'] == id_fragmento
    assert parsed_entidad['tipo'] == 'entidad'
    assert parsed_entidad['id_local'] == entidad_id
    
    print("✅ Parsing de referencias globales correcto")
    
    return True

def test_casos_edge():
    """Test de casos edge y límites."""
    print("\n⚠️ TEST: Casos Edge")
    print("-" * 40)
    
    id_fragmento = uuid4()
    processor = FragmentProcessor(id_fragmento)
    
    # Test con descripción None
    hecho_id = processor.next_hecho_id(None)
    assert hecho_id == 1
    print("✅ Descripción None manejada correctamente")
    
    # Test con descripción vacía
    entidad_id = processor.next_entidad_id("")
    assert entidad_id == 1
    print("✅ Descripción vacía manejada correctamente")
    
    # Test con descripción muy larga
    descripcion_larga = "A" * 1000
    cita_id = processor.next_cita_id(descripcion_larga)
    assert cita_id == 1
    print("✅ Descripción muy larga manejada correctamente")
    
    # Verificar que las estadísticas siguen siendo correctas
    stats = processor.get_stats()
    assert stats['total_hechos'] == 1
    assert stats['total_entidades'] == 1
    assert stats['total_citas'] == 1
    
    print("✅ Estadísticas correctas después de casos edge")
    
    return True

def ejecutar_todos_los_tests():
    """Ejecuta todos los tests del FragmentProcessor."""
    print("\n" + "="*60)
    print("🧪 TESTS DEL FRAGMENTPROCESSOR")
    print("="*60)
    
    tests = [
        ("IDs Secuenciales", test_ids_secuenciales),
        ("Múltiples Fragmentos", test_multiples_fragmentos),
        ("Estadísticas", test_estadisticas),
        ("Referencias Globales", test_referencias_globales),
        ("Casos Edge", test_casos_edge)
    ]
    
    resultados = []
    
    for nombre, test_func in tests:
        try:
            success = test_func()
            resultados.append((nombre, success))
            print(f"✅ {nombre}: EXITOSO")
        except Exception as e:
            print(f"❌ {nombre}: FALLIDO - {e}")
            resultados.append((nombre, False))
    
    # Resumen final
    print("\n" + "="*60)
    print("📊 RESUMEN DE TESTS FRAGMENTPROCESSOR")
    print("="*60)
    
    exitosos = sum(1 for _, success in resultados if success)
    total = len(resultados)
    
    print(f"\n📈 Resultados:")
    print(f"   - Tests exitosos: {exitosos}/{total}")
    print(f"   - Tasa de éxito: {(exitosos/total)*100:.1f}%")
    
    if exitosos == total:
        print(f"\n🎉 TODOS LOS TESTS DEL FRAGMENTPROCESSOR PASARON")
        print(f"   - Sistema de IDs completamente funcional")
        print(f"   - Generación secuencial verificada")
        print(f"   - Estadísticas precisas")
        print(f"   - Referencias globales operativas")
        print(f"   - Casos edge manejados correctamente")
    else:
        print(f"\n⚠️ Algunos tests fallaron:")
        for nombre, success in resultados:
            if not success:
                print(f"   - {nombre}")
    
    return exitosos == total

if __name__ == "__main__":
    try:
        success = ejecutar_todos_los_tests()
        
        if success:
            print("\n🏆 ¡FRAGMENTPROCESSOR COMPLETAMENTE FUNCIONAL!")
        else:
            print("\n❌ Algunos tests del FragmentProcessor fallaron.")
            
    except Exception as e:
        print(f"\n💥 Error crítico: {e}")
        import traceback
        traceback.print_exc()
