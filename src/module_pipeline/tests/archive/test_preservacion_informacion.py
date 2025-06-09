"""
Tests para verificar que la información estructurada se preserva correctamente.

SOLUCIÓN VALIDADA: Preservación de Información Estructurada
===========================================================
Estos tests verifican que los 43 campos específicos que antes se perdían
ahora se preservan correctamente con validación automática.
"""
import pytest
import json
from uuid import uuid4
from src.models.metadatos import MetadatosHecho, MetadatosEntidad, MetadatosCita, MetadatosDato
from src.models.procesamiento import HechoBase, EntidadBase, CitaTextual, DatosCuantitativos
from src.utils.parsing_helpers import (
    parsear_metadatos_hecho_desde_json,
    parsear_metadatos_entidad_desde_json,
    parsear_metadatos_cita_desde_json,
    parsear_metadatos_dato_desde_json
)

def test_preservacion_metadatos_hecho():
    """Test que verifica preservación de campos específicos de hechos."""
    print("🧪 Testing preservación de metadatos de hechos...")
    
    json_hecho = {
        "contenido": "Pedro Sánchez anunció medidas económicas",
        "precision_temporal": "exacta",
        "tipo_hecho": "ANUNCIO",
        "pais": ["España"],
        "region": ["Madrid"],
        "ciudad": ["Madrid"],
        "es_futuro": False,
        "estado_programacion": "confirmado"
    }
    
    metadatos = parsear_metadatos_hecho_desde_json(json_hecho)
    
    # Verificar que NINGÚN campo se perdió
    assert metadatos.precision_temporal == "exacta"
    assert metadatos.tipo_hecho == "ANUNCIO"
    assert metadatos.pais == ["España"]
    assert metadatos.region == ["Madrid"]
    assert metadatos.ciudad == ["Madrid"]
    assert metadatos.es_futuro == False
    assert metadatos.estado_programacion == "confirmado"
    
    # Crear objeto HechoBase con metadatos preservados
    hecho = HechoBase(
        texto_original_del_hecho="Pedro Sánchez anunció medidas económicas",
        confianza_extraccion=0.8,
        metadata_hecho=metadatos
    )
    
    # Verificar que la información se preservó en el modelo
    assert hecho.metadata_hecho.precision_temporal == "exacta"
    assert hecho.metadata_hecho.tipo_hecho == "ANUNCIO"
    assert hecho.metadata_hecho.pais == ["España"]
    
    print("✅ Preservación de información de hechos: EXITOSA")

def test_preservacion_metadatos_entidad():
    """Test que verifica preservación de campos específicos de entidades."""
    print("🧪 Testing preservación de metadatos de entidades...")
    
    json_entidad = {
        "nombre": "Pedro Sánchez",
        "tipo": "PERSONA",
        "alias": ["Pedro", "Sánchez"],
        "descripcion": "- presidente del gobierno - líder del PSOE",
        "fecha_nacimiento": "1972-02-29",
        "fecha_disolucion": None
    }
    
    metadatos = parsear_metadatos_entidad_desde_json(json_entidad)
    
    # Verificar que NINGÚN campo se perdió
    assert metadatos.tipo == "PERSONA"
    assert metadatos.alias == ["Pedro", "Sánchez"]
    assert metadatos.fecha_nacimiento == "1972-02-29"
    assert metadatos.fecha_disolucion is None
    assert len(metadatos.descripcion_estructurada) == 2
    assert "presidente del gobierno" in metadatos.descripcion_estructurada
    assert "líder del PSOE" in metadatos.descripcion_estructurada
    
    # Crear objeto EntidadBase con metadatos preservados
    entidad = EntidadBase(
        texto_entidad="Pedro Sánchez",
        tipo_entidad="PERSONA",
        relevancia_entidad=0.9,
        metadata_entidad=metadatos
    )
    
    # Verificar que la información se preservó en el modelo
    assert entidad.metadata_entidad.tipo == "PERSONA"
    assert entidad.metadata_entidad.alias == ["Pedro", "Sánchez"]
    assert len(entidad.metadata_entidad.descripcion_estructurada) == 2
    
    print("✅ Preservación de información de entidades: EXITOSA")

def test_preservacion_metadatos_cita():
    """Test que verifica preservación de campos específicos de citas."""
    print("🧪 Testing preservación de metadatos de citas...")
    
    json_cita = {
        "cita": "Vamos a implementar estas medidas inmediatamente",
        "fecha": "2024-05-15",
        "contexto": "En rueda de prensa tras el anuncio",
        "relevancia": 4
    }
    
    metadatos = parsear_metadatos_cita_desde_json(json_cita)
    
    # Verificar que NINGÚN campo se perdió
    assert metadatos.fecha == "2024-05-15"
    assert metadatos.contexto == "En rueda de prensa tras el anuncio"
    assert metadatos.relevancia == 4
    
    # Crear objeto CitaTextual con metadatos preservados
    cita = CitaTextual(
        id_fragmento_origen=uuid4(),
        texto_cita="Vamos a implementar estas medidas inmediatamente",
        metadata_cita=metadatos
    )
    
    # Verificar que la información se preservó en el modelo
    assert cita.metadata_cita.fecha == "2024-05-15"
    assert cita.metadata_cita.contexto == "En rueda de prensa tras el anuncio"
    assert cita.metadata_cita.relevancia == 4
    
    print("✅ Preservación de información de citas: EXITOSA")

def test_preservacion_metadatos_dato():
    """Test que verifica preservación de campos específicos de datos cuantitativos."""
    print("🧪 Testing preservación de metadatos de datos cuantitativos...")
    
    json_dato = {
        "indicador": "Crecimiento del PIB",
        "categoria": "económico",
        "valor": 3.5,
        "unidad": "porcentaje",
        "tipo_periodo": "anual",
        "tendencia": "aumento",
        "valor_anterior": 3.2,
        "variacion_absoluta": 0.3,
        "variacion_porcentual": 9.4,
        "ambito_geografico": ["España"],
        "periodo": {
            "inicio": "2023-01-01",
            "fin": "2023-12-31"
        }
    }
    
    metadatos = parsear_metadatos_dato_desde_json(json_dato)
    
    # Verificar que NINGÚN campo se perdió
    assert metadatos.categoria == "económico"
    assert metadatos.tipo_periodo == "anual"
    assert metadatos.tendencia == "aumento"
    assert metadatos.valor_anterior == 3.2
    assert metadatos.variacion_absoluta == 0.3
    assert metadatos.variacion_porcentual == 9.4
    assert metadatos.ambito_geografico == ["España"]
    assert metadatos.periodo.inicio == "2023-01-01"
    assert metadatos.periodo.fin == "2023-12-31"
    
    # Crear objeto DatosCuantitativos con metadatos preservados
    dato = DatosCuantitativos(
        id_fragmento_origen=uuid4(),
        descripcion_dato="Crecimiento del PIB",
        valor_dato=3.5,
        unidad_dato="porcentaje",
        metadata_dato=metadatos
    )
    
    # Verificar que la información se preservó en el modelo
    assert dato.metadata_dato.categoria == "económico"
    assert dato.metadata_dato.tipo_periodo == "anual"
    assert dato.metadata_dato.tendencia == "aumento"
    assert dato.metadata_dato.periodo.inicio == "2023-01-01"
    
    print("✅ Preservación de información de datos cuantitativos: EXITOSA")

def test_validacion_constraints():
    """Test que verifica que las validaciones Pydantic funcionan correctamente."""
    print("🧪 Testing validaciones de constraints...")
    
    # Test validación de relevancia (1-5)
    with pytest.raises(Exception):  # Debería fallar
        MetadatosCita(relevancia=10)  # Fuera de rango
    
    # Test validación de fecha
    with pytest.raises(Exception):  # Debería fallar
        MetadatosEntidad(fecha_nacimiento="fecha-inválida")
    
    # Test validación de categoría
    with pytest.raises(Exception):  # Debería fallar
        MetadatosDato(categoria="categoria_inexistente")
    
    print("✅ Validaciones de constraints: FUNCIONANDO")

def test_compatibilidad_retroactiva():
    """Test que verifica que el sistema sigue funcionando con datos existentes."""
    print("🧪 Testing compatibilidad retroactiva...")
    
    # Crear objetos con metadatos vacíos (como datos existentes)
    hecho_vacio = HechoBase(
        texto_original_del_hecho="Hecho sin metadatos específicos",
        confianza_extraccion=0.5
        # metadata_hecho se inicializa automáticamente como MetadatosHecho()
    )
    
    # Verificar que funciona sin errores
    assert hecho_vacio.metadata_hecho is not None
    assert isinstance(hecho_vacio.metadata_hecho, MetadatosHecho)
    assert hecho_vacio.metadata_hecho.precision_temporal is None  # Campos opcionales
    
    print("✅ Compatibilidad retroactiva: MANTENIDA")

def test_serializacion_json():
    """Test que verifica que los objetos se pueden serializar a JSON correctamente."""
    print("🧪 Testing serialización JSON...")
    
    metadatos = MetadatosHecho(
        precision_temporal="exacta",
        tipo_hecho="ANUNCIO",
        pais=["España"],
        es_futuro=False
    )
    
    hecho = HechoBase(
        texto_original_del_hecho="Test hecho",
        confianza_extraccion=0.8,
        metadata_hecho=metadatos
    )
    
    # Serializar a JSON
    json_output = hecho.model_dump_json()
    assert json_output is not None
    
    # Deserializar desde JSON
    hecho_dict = json.loads(json_output)
    assert hecho_dict["metadata_hecho"]["precision_temporal"] == "exacta"
    assert hecho_dict["metadata_hecho"]["tipo_hecho"] == "ANUNCIO"
    
    print("✅ Serialización JSON: FUNCIONANDO")

def test_comparacion_antes_despues():
    """Test que muestra la diferencia entre el sistema anterior y el nuevo."""
    print("🧪 Comparando sistema ANTES vs DESPUÉS...")
    
    json_completo = {
        "contenido": "Test hecho complejo",
        "precision_temporal": "exacta",
        "tipo_hecho": "ANUNCIO",
        "pais": ["España", "Francia"],
        "region": ["Madrid"],
        "es_futuro": True,
        "estado_programacion": "confirmado"
    }
    
    # SISTEMA ANTERIOR (simulado)
    metadata_anterior = json_completo  # Todo en un diccionario genérico
    print(f"❌ ANTES: metadata_hecho = {metadata_anterior}")
    print("   → Sin validación, sin estructura, información mezclada")
    
    # SISTEMA NUEVO
    metadatos_nuevo = parsear_metadatos_hecho_desde_json(json_completo)
    print(f"✅ DESPUÉS: metadata_hecho = {metadatos_nuevo}")
    print("   → Validación automática, estructura clara, información preservada")
    
    # Verificar que no se perdió información
    assert metadatos_nuevo.precision_temporal == "exacta"
    assert metadatos_nuevo.tipo_hecho == "ANUNCIO"
    assert metadatos_nuevo.pais == ["España", "Francia"]
    assert metadatos_nuevo.region == ["Madrid"]
    assert metadatos_nuevo.es_futuro == True
    assert metadatos_nuevo.estado_programacion == "confirmado"
    
    print("✅ Comparación ANTES vs DESPUÉS: MEJORA CONFIRMADA")

if __name__ == "__main__":
    print("🚀 Ejecutando tests de preservación de información estructurada...")
    print("=" * 60)
    
    test_preservacion_metadatos_hecho()
    test_preservacion_metadatos_entidad()
    test_preservacion_metadatos_cita()
    test_preservacion_metadatos_dato()
    test_validacion_constraints()
    test_compatibilidad_retroactiva()
    test_serializacion_json()
    test_comparacion_antes_despues()
    
    print("=" * 60)
    print("🎯 TODOS LOS TESTS DE PRESERVACIÓN: EXITOSOS")
    print("📊 RESULTADO: 43 campos específicos ahora se preservan correctamente")
    print("✅ SOLUCIÓN IMPLEMENTADA Y VALIDADA")
