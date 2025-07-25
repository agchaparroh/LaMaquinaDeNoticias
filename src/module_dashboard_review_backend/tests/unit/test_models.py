"""
Tests unitarios para los modelos Pydantic del Dashboard Review Backend.

Prueba la validación, creación y métodos helper de los nuevos modelos
implementados para la funcionalidad de relaciones entre hechos.
"""

from datetime import datetime
from typing import Any, Dict

import pytest
from pydantic import ValidationError

from src.models.domain import HechoRelacionado, TipoRelacion
from src.models.requests import HechoFilterParams, PaginationParams  # noqa: F401
from src.models.responses import (
    ArticuloMetadata,
    HechoRelacionInfo,
    HechoResponse,  # noqa: F401
    PaginatedResponse,
    PaginationInfo,
)


class TestTipoRelacion:
    """Tests para enum TipoRelacion."""

    def test_tipos_relacion_values(self):
        """Verificar que todos los tipos de relación están definidos."""
        expected_values = {
            "consecuencia",
            "causa",
            "contradictorio",
            "complementario",
            "temporal_anterior",
            "temporal_posterior",
            "misma_fuente",
            "actualizacion",
            "correccion",
            "ampliacion",
        }
        actual_values = {tipo.value for tipo in TipoRelacion}
        assert actual_values == expected_values

    def test_is_causal_method(self):
        """Verificar método is_causal."""
        assert TipoRelacion.is_causal("consecuencia") is True
        assert TipoRelacion.is_causal("causa") is True
        assert TipoRelacion.is_causal("contradictorio") is False
        assert TipoRelacion.is_causal("temporal_anterior") is False

    def test_is_temporal_method(self):
        """Verificar método is_temporal."""
        assert TipoRelacion.is_temporal("temporal_anterior") is True
        assert TipoRelacion.is_temporal("temporal_posterior") is True
        assert TipoRelacion.is_temporal("consecuencia") is False
        assert TipoRelacion.is_temporal("contradictorio") is False

    def test_is_contradictory_method(self):
        """Verificar método is_contradictory."""
        assert TipoRelacion.is_contradictory("contradictorio") is True
        assert TipoRelacion.is_contradictory("consecuencia") is False
        assert TipoRelacion.is_contradictory("complementario") is False


class TestHechoRelacionado:
    """Tests para modelo HechoRelacionado."""

    @pytest.fixture
    def valid_relacion_data(self) -> Dict[str, Any]:
        """Datos válidos para crear HechoRelacionado."""
        return {
            "hecho_origen_id": 123,
            "fecha_ocurrencia_origen": "[2024-01-01 10:00:00,2024-01-01 12:00:00)",
            "hecho_destino_id": 456,
            "fecha_ocurrencia_destino": "[2024-01-01 14:00:00,2024-01-01 16:00:00)",
            "tipo_relacion": "consecuencia",
            "fuerza_relacion": 8,
            "descripcion_relacion": "El evento A causó el evento B",
            "fecha_deteccion": datetime(2024, 1, 15, 10, 30),
        }

    def test_crear_relacion_valida(self, valid_relacion_data):
        """Crear relación con datos válidos."""
        relacion = HechoRelacionado(**valid_relacion_data)

        assert relacion.hecho_origen_id == 123
        assert relacion.hecho_destino_id == 456
        assert relacion.tipo_relacion == "consecuencia"
        assert relacion.fuerza_relacion == 8
        assert relacion.descripcion_relacion == "El evento A causó el evento B"

    def test_fuerza_relacion_default(self, valid_relacion_data):
        """Verificar valor por defecto de fuerza_relacion."""
        del valid_relacion_data["fuerza_relacion"]
        relacion = HechoRelacionado(**valid_relacion_data)
        assert relacion.fuerza_relacion == 5

    def test_fuerza_relacion_validation(self, valid_relacion_data):
        """Validar rango de fuerza_relacion."""
        # Valor muy bajo
        valid_relacion_data["fuerza_relacion"] = 0
        with pytest.raises(ValidationError):
            HechoRelacionado(**valid_relacion_data)

        # Valor muy alto
        valid_relacion_data["fuerza_relacion"] = 11
        with pytest.raises(ValidationError):
            HechoRelacionado(**valid_relacion_data)

        # Valores válidos en los extremos
        valid_relacion_data["fuerza_relacion"] = 1
        relacion1 = HechoRelacionado(**valid_relacion_data)
        assert relacion1.fuerza_relacion == 1

        valid_relacion_data["fuerza_relacion"] = 10
        relacion2 = HechoRelacionado(**valid_relacion_data)
        assert relacion2.fuerza_relacion == 10

    def test_is_bidirectional_property(self, valid_relacion_data):
        """Verificar propiedad is_bidirectional."""
        # Relación bidireccional
        valid_relacion_data["tipo_relacion"] = "contradictorio"
        relacion = HechoRelacionado(**valid_relacion_data)
        assert relacion.is_bidirectional is True

        # Relación unidireccional
        valid_relacion_data["tipo_relacion"] = "consecuencia"
        relacion = HechoRelacionado(**valid_relacion_data)
        assert relacion.is_bidirectional is False

    def test_is_strong_relation_property(self, valid_relacion_data):
        """Verificar propiedad is_strong_relation."""
        # Relación fuerte
        valid_relacion_data["fuerza_relacion"] = 8
        relacion = HechoRelacionado(**valid_relacion_data)
        assert relacion.is_strong_relation is True

        # Relación débil
        valid_relacion_data["fuerza_relacion"] = 5
        relacion = HechoRelacionado(**valid_relacion_data)
        assert relacion.is_strong_relation is False

    def test_involves_hecho_method(self, valid_relacion_data):
        """Verificar método involves_hecho."""
        relacion = HechoRelacionado(**valid_relacion_data)

        assert relacion.involves_hecho(123) is True  # origen
        assert relacion.involves_hecho(456) is True  # destino
        assert relacion.involves_hecho(789) is False  # no involucrado

    def test_get_related_id_method(self, valid_relacion_data):
        """Verificar método get_related_id."""
        relacion = HechoRelacionado(**valid_relacion_data)

        assert relacion.get_related_id(123) == 456  # origen -> destino
        assert relacion.get_related_id(456) == 123  # destino -> origen
        assert relacion.get_related_id(789) is None  # no involucrado

    def test_get_direction_for_hecho_method(self, valid_relacion_data):
        """Verificar método get_direction_for_hecho."""
        relacion = HechoRelacionado(**valid_relacion_data)

        assert relacion.get_direction_for_hecho(123) == "origen"
        assert relacion.get_direction_for_hecho(456) == "destino"
        assert relacion.get_direction_for_hecho(789) is None


class TestArticuloMetadata:
    """Tests para modelo ArticuloMetadata."""

    @pytest.fixture
    def valid_articulo_data(self) -> Dict[str, Any]:
        """Datos válidos para crear ArticuloMetadata."""
        return {
            "medio": "La Nación",
            "titular": "Presidente anuncia nuevas medidas",
            "fecha_publicacion": datetime(2024, 1, 15, 10, 30),
            "url": "https://lanacion.com/politica/1234",
            "area_geografica": "Argentina",
            "tipo_medio": "diario_digital",
            "autor": "Juan Pérez",
            "seccion": "Política",
            "es_opinion": False,
            "es_oficial": True,
            "resumen": "El presidente anunció nuevas medidas económicas...",
            "categorias_asignadas": ["política", "economía"],
            "puntuacion_relevancia": 8,
            "estado_procesamiento": "completado",
        }

    def test_crear_articulo_valido(self, valid_articulo_data):
        """Crear artículo con datos válidos."""
        articulo = ArticuloMetadata(**valid_articulo_data)

        assert articulo.medio == "La Nación"
        assert articulo.titular == "Presidente anuncia nuevas medidas"
        assert articulo.es_opinion is False
        assert articulo.es_oficial is True
        assert len(articulo.categorias_asignadas) == 2

    def test_campos_opcionales(self, valid_articulo_data):
        """Verificar manejo de campos opcionales."""
        # Remover campos opcionales
        optional_fields = [
            "url",
            "autor",
            "seccion",
            "resumen",
            "puntuacion_relevancia",
        ]
        for field in optional_fields:
            del valid_articulo_data[field]

        articulo = ArticuloMetadata(**valid_articulo_data)
        assert articulo.url is None
        assert articulo.autor is None
        assert articulo.seccion is None
        assert articulo.resumen is None
        assert articulo.puntuacion_relevancia is None

    def test_categorias_default(self):
        """Verificar valor por defecto de categorias_asignadas."""
        articulo_data = {
            "medio": "Test",
            "titular": "Test",
            "fecha_publicacion": datetime.now(),
            "area_geografica": "Test",
            "tipo_medio": "Test",
            "es_opinion": False,
            "es_oficial": False,
        }
        articulo = ArticuloMetadata(**articulo_data)
        assert articulo.categorias_asignadas == []


class TestHechoRelacionInfo:
    """Tests para modelo HechoRelacionInfo."""

    def test_crear_relacion_info_valida(self):
        """Crear HechoRelacionInfo con datos válidos."""
        relacion_info = HechoRelacionInfo(
            hecho_relacionado_id=456,
            tipo_relacion="consecuencia",
            fuerza_relacion=8,
            descripcion_relacion="Resultado directo del evento anterior",
            direccion="destino",
        )

        assert relacion_info.hecho_relacionado_id == 456
        assert relacion_info.tipo_relacion == "consecuencia"
        assert relacion_info.fuerza_relacion == 8
        assert relacion_info.direccion == "destino"

    def test_fuerza_relacion_validation(self):
        """Validar rango de fuerza_relacion."""
        # Valor inválido bajo
        with pytest.raises(ValidationError):
            HechoRelacionInfo(
                hecho_relacionado_id=456,
                tipo_relacion="causa",
                fuerza_relacion=0,
                direccion="origen",
            )

        # Valor inválido alto
        with pytest.raises(ValidationError):
            HechoRelacionInfo(
                hecho_relacionado_id=456,
                tipo_relacion="causa",
                fuerza_relacion=11,
                direccion="origen",
            )

    def test_descripcion_opcional(self):
        """Verificar que descripcion_relacion es opcional."""
        relacion_info = HechoRelacionInfo(
            hecho_relacionado_id=456,
            tipo_relacion="complementario",
            fuerza_relacion=6,
            direccion="origen",
        )
        assert relacion_info.descripcion_relacion is None


class TestHechoFilterParams:
    """Tests para modelo HechoFilterParams."""

    def test_filtros_opcionales(self):
        """Verificar que todos los filtros son opcionales."""
        params = HechoFilterParams()

        assert params.fecha_inicio is None
        assert params.fecha_fin is None
        assert params.medio is None
        assert params.area_geografica is None
        assert params.tipo_hecho is None
        assert params.evaluacion_editorial is None
        assert params.importancia_min is None
        assert params.importancia_max is None
        assert params.limit == 20  # valor por defecto
        assert params.offset == 0  # valor por defecto

    def test_validacion_fechas(self):
        """Validar que fecha_fin debe ser posterior a fecha_inicio."""
        fecha_inicio = datetime(2024, 1, 15)
        fecha_fin = datetime(2024, 1, 10)  # anterior a inicio

        with pytest.raises(ValidationError):
            HechoFilterParams(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

    def test_validacion_importancia(self):
        """Validar rango de importancia."""
        with pytest.raises(ValidationError):
            HechoFilterParams(
                importancia_min=5,
                importancia_max=3,  # max menor que min
            )

    def test_to_dict_method(self):
        """Verificar método to_dict excluye valores None."""
        params = HechoFilterParams(medio="La Nación", importancia_min=5, limit=10)

        result = params.to_dict()

        assert "medio" in result
        assert "importancia_min" in result
        assert "limit" in result
        assert "fecha_inicio" not in result  # None values excluded
        assert "area_geografica" not in result


class TestPaginatedResponse:
    """Tests para modelo PaginatedResponse."""

    def test_crear_response_paginada(self):
        """Crear respuesta paginada válida."""
        items = [{"id": 1, "test": "data"}]
        pagination = PaginationInfo(
            total_items=100,
            page=1,
            per_page=20,
            total_pages=5,
            has_next=True,
            has_prev=False,
        )

        response = PaginatedResponse[dict](items=items, pagination=pagination)

        assert len(response.items) == 1
        assert response.pagination.total_items == 100
        assert response.pagination.has_next is True
        assert response.pagination.has_prev is False
