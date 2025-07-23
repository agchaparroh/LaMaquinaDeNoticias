#!/usr/bin/env python3
"""
Script de diagnóstico para verificar el fix del error E012
"""

import sys
from uuid import uuid4
from pathlib import Path

# Añadir el directorio src al path
sys.path.insert(0, str(Path(__file__).parent))

# Importar modelos y funciones
from ...src.models.procesamiento import EntidadProcesada
from ...src.models.metadatos import MetadatosEntidad
from ...src.models.simplificacion import ResultadoFase2Simplificacion
from ...src.pipeline.fase_3_entidades import ejecutar_fase_3_entidades

def test_entidad_procesada_creation():
    """Test creación de EntidadProcesada con todos los campos requeridos"""
    print("=== Test 1: Creación de EntidadProcesada ===")
    try:
        # Crear metadatos
        metadatos = MetadatosEntidad(
            tipo="PERSONA",
            alias=["Presidente", "Pedro S."],
            fecha_nacimiento="1972-02-29"
        )
        
        # Crear entidad con todos los campos requeridos
        entidad = EntidadProcesada(
            id_entidad=1,
            nombre="Pedro Sánchez",
            tipo="PERSONA",
            relevancia=9,
            id_fragmento_origen=uuid4(),  # Campo requerido
            metadata_entidad=metadatos
        )
        
        print("✅ EntidadProcesada creada correctamente")
        print(f"   - id_fragmento_origen: {entidad.id_fragmento_origen}")
        return True
    except Exception as e:
        print(f"❌ Error creando EntidadProcesada: {str(e)}")
        return False

def test_fase_3_entidades():
    """Test ejecutar_fase_3_entidades con resultado de simplificación"""
    print("\n=== Test 2: Ejecutar fase_3_entidades ===")
    try:
        # Crear resultado de simplificación mock
        resultado_simplif = ResultadoFase2Simplificacion(
            id_resultado_simplificacion=uuid4(),
            id_fragmento=uuid4(),
            texto_simplificado="Pedro Sánchez, presidente del Gobierno, anunció nuevas medidas económicas.",
            simplificacion_exitosa=True
        )
        
        print(f"   - id_fragmento en resultado_simplif: {resultado_simplif.id_fragmento}")
        
        # Ejecutar fase 3
        resultado = ejecutar_fase_3_entidades(
            resultado_simplificacion=resultado_simplif,
            contexto_articulo={
                "titulo": "Test",
                "fuente": "Test",
                "pais": "España",
                "fecha_publicacion": "2025-01-17"
            }
        )
        
        if resultado.get("error"):
            print(f"❌ Fase 3 retornó con error: {resultado['error']}")
            return False
        
        print(f"✅ Fase 3 ejecutada correctamente")
        print(f"   - Entidades extraídas: {resultado.get('total_entidades', 0)}")
        
        # Verificar que las entidades tienen id_fragmento_origen
        for entidad in resultado.get("entidades_extraidas", []):
            if hasattr(entidad, 'id_fragmento_origen'):
                print(f"   - Entidad '{entidad.nombre}' tiene id_fragmento_origen: {entidad.id_fragmento_origen}")
            else:
                print(f"   ❌ Entidad '{entidad.nombre}' NO tiene id_fragmento_origen")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Error ejecutando fase_3_entidades: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Ejecutar tests de diagnóstico"""
    print("DIAGNÓSTICO ERROR E012 - EntidadProcesada sin id_fragmento")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 2
    
    # Test 1
    if test_entidad_procesada_creation():
        tests_passed += 1
    
    # Test 2
    if test_fase_3_entidades():
        tests_passed += 1
    
    print(f"\n{'=' * 60}")
    print(f"RESULTADO: {tests_passed}/{total_tests} tests pasados")
    
    if tests_passed == total_tests:
        print("✅ Todos los tests pasaron - Error E012 parece estar solucionado")
    else:
        print("❌ Algunos tests fallaron - Error E012 persiste")

if __name__ == "__main__":
    main()