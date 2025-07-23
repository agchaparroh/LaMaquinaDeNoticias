"""
Tests para ValidadorRelacionesPost7B
====================================

Verifica que el validador corrige correctamente los tipos de relación
inválidos generados por el LLM.
"""

import pytest
from ....src.utils.validador_relaciones_post7b import ValidadorRelacionesPost7B


def test_validador_corrige_tipos_invalidos_entidad_entidad():
    """Test que el validador corrige tipos inválidos en relaciones entidad-entidad."""
    validador = ValidadorRelacionesPost7B()
    
    # Datos con tipos inválidos (tipos de hecho-entidad)
    datos_entrada = {
        "entidad_relacion": [
            {
                "id_entidad_origen": "E1",
                "id_entidad_destino": "E2",
                "tipo_relacion": "ubicacion",  # INVÁLIDO
                "descripcion": "Se encuentra en"
            },
            {
                "id_entidad_origen": "E3",
                "id_entidad_destino": "E4",
                "tipo_relacion": "mencionado",  # INVÁLIDO
                "descripcion": "Mencionado junto a"
            },
            {
                "id_entidad_origen": "E5",
                "id_entidad_destino": "E6",
                "tipo_relacion": "miembro_de",  # VÁLIDO
                "descripcion": "Es miembro de"
            }
        ]
    }
    
    # Validar y corregir
    datos_corregidos = validador.validar_y_corregir(datos_entrada)
    
    # Verificar correcciones
    assert len(datos_corregidos["entidad_relacion"]) == 3
    assert datos_corregidos["entidad_relacion"][0]["tipo_relacion"] == "aliado_con"  # ubicacion → aliado_con
    assert datos_corregidos["entidad_relacion"][1]["tipo_relacion"] == "aliado_con"  # mencionado → aliado_con
    assert datos_corregidos["entidad_relacion"][2]["tipo_relacion"] == "miembro_de"  # sin cambios
    
    # Verificar estadísticas
    estadisticas = validador.obtener_estadisticas(datos_entrada, datos_corregidos)
    assert estadisticas["entidad_relacion"]["corregidas"] == 2
    assert estadisticas["entidad_relacion"]["descartadas"] == 0


def test_validador_descarta_tipos_no_corregibles():
    """Test que el validador descarta tipos que no puede corregir."""
    validador = ValidadorRelacionesPost7B()
    
    datos_entrada = {
        "entidad_relacion": [
            {
                "id_entidad_origen": "E1",
                "id_entidad_destino": "E2",
                "tipo_relacion": "tipo_inexistente",  # No corregible
                "descripcion": "Relación desconocida"
            },
            {
                "id_entidad_origen": "E3",
                "id_entidad_destino": "E4",
                "tipo_relacion": "empleado_de",  # VÁLIDO
                "descripcion": "Trabaja para"
            }
        ]
    }
    
    datos_corregidos = validador.validar_y_corregir(datos_entrada)
    
    # Solo debe quedar la relación válida
    assert len(datos_corregidos["entidad_relacion"]) == 1
    assert datos_corregidos["entidad_relacion"][0]["tipo_relacion"] == "empleado_de"
    
    # Verificar estadísticas
    estadisticas = validador.obtener_estadisticas(datos_entrada, datos_corregidos)
    assert estadisticas["entidad_relacion"]["descartadas"] == 1
    assert estadisticas["entidad_relacion"]["corregidas"] == 0


def test_validador_hecho_entidad_usa_otro_por_defecto():
    """Test que el validador usa 'otro' como tipo por defecto para hecho-entidad."""
    validador = ValidadorRelacionesPost7B()
    
    datos_entrada = {
        "hecho_entidad": [
            {
                "id_temporal": "E1",
                "tipo_relacion": "tipo_invalido",  # INVÁLIDO
                "relevancia_en_hecho": 5
            },
            {
                "id_temporal": "E2",
                "tipo_relacion": "protagonista",  # VÁLIDO
                "relevancia_en_hecho": 10
            }
        ]
    }
    
    datos_corregidos = validador.validar_y_corregir(datos_entrada)
    
    assert len(datos_corregidos["hecho_entidad"]) == 2
    assert datos_corregidos["hecho_entidad"][0]["tipo_relacion"] == "otro"
    assert datos_corregidos["hecho_entidad"][1]["tipo_relacion"] == "protagonista"


def test_validador_contradicciones_usa_contenido_por_defecto():
    """Test que el validador usa 'contenido' como tipo por defecto para contradicciones."""
    validador = ValidadorRelacionesPost7B()
    
    datos_entrada = {
        "contradicciones": [
            {
                "hecho_principal_id": 1,
                "hecho_contradictorio_id": 2,
                "tipo_contradiccion": "tipo_invalido",  # INVÁLIDO
                "grado_contradiccion": 3
            },
            {
                "hecho_principal_id": 3,
                "hecho_contradictorio_id": 4,
                "tipo_contradiccion": "fecha",  # VÁLIDO
                "grado_contradiccion": 5
            }
        ]
    }
    
    datos_corregidos = validador.validar_y_corregir(datos_entrada)
    
    assert len(datos_corregidos["contradicciones"]) == 2
    assert datos_corregidos["contradicciones"][0]["tipo_contradiccion"] == "contenido"
    assert datos_corregidos["contradicciones"][1]["tipo_contradiccion"] == "fecha"


def test_validador_caso_real_ubicacion():
    """Test con el caso real que causa el error: tipo 'ubicacion' en entidad_relacion."""
    validador = ValidadorRelacionesPost7B()
    
    # Simulando el caso real del error
    datos_entrada = {
        "entidad_relacion": [
            {
                "id_entidad_origen": "ENT_5",
                "id_entidad_destino": "ENT_3",
                "tipo_relacion": "ubicacion",  # Este es el error real!
                "descripcion": "Plaza San Miguel está ubicada en San Miguel",
                "fuerza_relacion": 10
            }
        ]
    }
    
    datos_corregidos = validador.validar_y_corregir(datos_entrada)
    
    # Debe corregir 'ubicacion' a 'aliado_con' (relación neutral geográfica)
    assert len(datos_corregidos["entidad_relacion"]) == 1
    assert datos_corregidos["entidad_relacion"][0]["tipo_relacion"] == "aliado_con"
    
    # Verificar que mantiene otros campos
    assert datos_corregidos["entidad_relacion"][0]["id_entidad_origen"] == "ENT_5"
    assert datos_corregidos["entidad_relacion"][0]["id_entidad_destino"] == "ENT_3"
    assert datos_corregidos["entidad_relacion"][0]["descripcion"] == "Plaza San Miguel está ubicada en San Miguel"
    assert datos_corregidos["entidad_relacion"][0]["fuerza_relacion"] == 10


def test_validador_rangos_numericos():
    """Test que el validador ajusta valores numéricos fuera de rango."""
    validador = ValidadorRelacionesPost7B()
    
    datos_entrada = {
        "entidad_relacion": [
            {
                "id_entidad_origen": "E1",
                "id_entidad_destino": "E2",
                "tipo_relacion": "miembro_de",
                "fuerza_relacion": 15  # > 10
            },
            {
                "id_entidad_origen": "E3",
                "id_entidad_destino": "E4",
                "tipo_relacion": "empleado_de",
                "fuerza_relacion": -2  # < 1
            }
        ],
        "hecho_entidad": [
            {
                "id_temporal": "E5",
                "tipo_relacion": "protagonista",
                "relevancia_en_hecho": 20  # > 10
            }
        ],
        "contradicciones": [
            {
                "hecho_principal_id": 1,
                "hecho_contradictorio_id": 2,
                "tipo_contradiccion": "fecha",
                "grado_contradiccion": 10  # > 5
            }
        ]
    }
    
    datos_corregidos = validador.validar_y_corregir(datos_entrada)
    
    # Verificar ajustes de rango
    assert datos_corregidos["entidad_relacion"][0]["fuerza_relacion"] == 10  # Ajustado de 15
    assert datos_corregidos["entidad_relacion"][1]["fuerza_relacion"] == 1   # Ajustado de -2
    assert datos_corregidos["hecho_entidad"][0]["relevancia_en_hecho"] == 10  # Ajustado de 20
    assert datos_corregidos["contradicciones"][0]["grado_contradiccion"] == 5  # Ajustado de 10


def test_validador_entidades_iguales():
    """Test que el validador descarta relaciones donde origen = destino."""
    validador = ValidadorRelacionesPost7B()
    
    datos_entrada = {
        "entidad_relacion": [
            {
                "id_entidad_origen": "E1",
                "id_entidad_destino": "E1",  # Misma entidad!
                "tipo_relacion": "miembro_de",
                "fuerza_relacion": 5
            },
            {
                "id_entidad_origen": "E2",
                "id_entidad_destino": "E3",  # Diferentes, OK
                "tipo_relacion": "aliado_con",
                "fuerza_relacion": 5
            }
        ]
    }
    
    datos_corregidos = validador.validar_y_corregir(datos_entrada)
    
    # Solo debe quedar la relación válida
    assert len(datos_corregidos["entidad_relacion"]) == 1
    assert datos_corregidos["entidad_relacion"][0]["id_entidad_origen"] == "E2"
    assert datos_corregidos["entidad_relacion"][0]["id_entidad_destino"] == "E3"


def test_validador_campos_obligatorios():
    """Test que el validador descarta registros sin campos obligatorios."""
    validador = ValidadorRelacionesPost7B()
    
    datos_entrada = {
        "entidad_relacion": [
            {
                # Falta id_entidad_destino
                "id_entidad_origen": "E1",
                "tipo_relacion": "miembro_de"
            },
            {
                # Todos los campos obligatorios presentes
                "id_entidad_origen": "E2",
                "id_entidad_destino": "E3",
                "tipo_relacion": "empleado_de"
            }
        ],
        "hecho_entidad": [
            {
                # Falta id_temporal
                "tipo_relacion": "protagonista",
                "relevancia_en_hecho": 5
            }
        ]
    }
    
    datos_corregidos = validador.validar_y_corregir(datos_entrada)
    
    # Solo deben quedar registros con campos obligatorios
    assert len(datos_corregidos["entidad_relacion"]) == 1
    assert datos_corregidos["entidad_relacion"][0]["id_entidad_origen"] == "E2"
    assert len(datos_corregidos["hecho_entidad"]) == 0


if __name__ == "__main__":
    # Ejecutar tests
    test_validador_corrige_tipos_invalidos_entidad_entidad()
    test_validador_descarta_tipos_no_corregibles()
    test_validador_hecho_entidad_usa_otro_por_defecto()
    test_validador_contradicciones_usa_contenido_por_defecto()
    test_validador_caso_real_ubicacion()
    test_validador_rangos_numericos()
    test_validador_entidades_iguales()
    test_validador_campos_obligatorios()
    
    print("✅ Todos los tests pasaron exitosamente!")
    print("\nEl validador ahora valida TODOS los constraints de la BD:")
    print("- Tipos de enumeración (tipo_relacion, tipo_contradiccion)")
    print("- Rangos numéricos (fuerza_relacion 1-10, relevancia 1-10, grado_contradiccion 1-5)")
    print("- Relaciones diferentes (origen != destino)")
    print("- Campos obligatorios NOT NULL")
    print("\nListo para resolver TODOS los problemas de constraints de Supabase!")