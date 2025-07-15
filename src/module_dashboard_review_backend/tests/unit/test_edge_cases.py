"""
Tests de casos edge y validaciones para la funcionalidad de relaciones.

Verifica el manejo correcto de situaciones límite, datos inconsistentes,
y escenarios poco comunes que podrían ocurrir en producción.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch
from typing import Dict, List, Any

from src.models.domain import HechoRelacionado, TipoRelacion
from src.models.responses import HechoResponse, ArticuloMetadata, HechoRelacionInfo
from src.models.requests import HechoFilterParams
from src.services.hechos_service import HechosService
from pydantic import ValidationError


class TestHechoRelacionadoEdgeCases:
    """Tests de casos edge para el modelo HechoRelacionado."""
    
    def test_relacion_circular_self_reference(self):
        """Test relación donde un hecho se relaciona consigo mismo."""
        relacion = HechoRelacionado(
            hecho_origen_id=1,
            fecha_ocurrencia_origen="[2024-01-01 10:00:00,2024-01-01 12:00:00)",
            hecho_destino_id=1,  # Mismo hecho
            fecha_ocurrencia_destino="[2024-01-01 10:00:00,2024-01-01 12:00:00)",
            tipo_relacion="actualizacion",
            fuerza_relacion=3
        )
        
        # Debe funcionar correctamente
        assert relacion.involves_hecho(1) is True
        assert relacion.get_related_id(1) == 1  # Se relaciona consigo mismo
        assert relacion.get_direction_for_hecho(1) == "origen"  # Primera coincidencia
    
    def test_relacion_con_fechas_invalidas_pero_strings_validos(self):
        """Test relación con strings de fecha que no son rangos válidos."""
        # Strings que no siguen el formato tstzrange estándar
        relacion = HechoRelacionado(
            hecho_origen_id=1,
            fecha_ocurrencia_origen="2024-01-01 invalid format",
            hecho_destino_id=2,
            fecha_ocurrencia_destino="not a range at all",
            tipo_relacion="contradictorio",
            fuerza_relacion=5
        )
        
        # El modelo debe aceptar cualquier string (la validación de formato
        # sería responsabilidad de otra capa)
        assert relacion.tipo_relacion == "contradictorio"
        assert relacion.is_bidirectional is True
    
    def test_relacion_con_descripcion_muy_larga(self):
        """Test relación con descripción extremadamente larga."""
        descripcion_larga = "A" * 10000  # 10KB de texto
        
        relacion = HechoRelacionado(
            hecho_origen_id=1,
            fecha_ocurrencia_origen="[2024-01-01 10:00:00,2024-01-01 12:00:00)",
            hecho_destino_id=2,
            fecha_ocurrencia_destino="[2024-01-01 14:00:00,2024-01-01 16:00:00)",
            tipo_relacion="complementario",
            fuerza_relacion=7,
            descripcion_relacion=descripcion_larga
        )
        
        assert len(relacion.descripcion_relacion) == 10000
        assert relacion.descripcion_relacion.startswith("AAAA")
    
    def test_relacion_con_tipo_no_enum(self):
        """Test relación con tipo que no está en el enum TipoRelacion."""
        # Debería aceptarse porque tipo_relacion es str, no enum obligatorio
        relacion = HechoRelacionado(
            hecho_origen_id=1,
            fecha_ocurrencia_origen="[2024-01-01 10:00:00,2024-01-01 12:00:00)",
            hecho_destino_id=2,
            fecha_ocurrencia_destino="[2024-01-01 14:00:00,2024-01-01 16:00:00)",
            tipo_relacion="tipo_personalizado_no_enum",
            fuerza_relacion=5
        )
        
        assert relacion.tipo_relacion == "tipo_personalizado_no_enum"
        # Los métodos de TipoRelacion no lo reconocerán
        assert TipoRelacion.is_causal("tipo_personalizado_no_enum") is False
        assert TipoRelacion.is_temporal("tipo_personalizado_no_enum") is False
        assert TipoRelacion.is_contradictory("tipo_personalizado_no_enum") is False
    
    def test_relacion_con_ids_extremadamente_grandes(self):
        """Test relación con IDs muy grandes."""
        id_grande = 2**63 - 1  # Máximo int64
        
        relacion = HechoRelacionado(
            hecho_origen_id=id_grande,
            fecha_ocurrencia_origen="[2024-01-01 10:00:00,2024-01-01 12:00:00)",
            hecho_destino_id=id_grande - 1,
            fecha_ocurrencia_destino="[2024-01-01 14:00:00,2024-01-01 16:00:00)",
            tipo_relacion="consecuencia",
            fuerza_relacion=9
        )
        
        assert relacion.hecho_origen_id == id_grande
        assert relacion.hecho_destino_id == id_grande - 1
        assert relacion.involves_hecho(id_grande) is True
        assert relacion.get_related_id(id_grande) == id_grande - 1


class TestHechoResponseEdgeCases:
    """Tests de casos edge para el modelo HechoResponse."""
    
    def test_hecho_response_con_arrays_vacios(self):
        """Test HechoResponse con todos los arrays vacíos."""
        articulo = ArticuloMetadata(
            medio="Test",
            titular="Test",
            fecha_publicacion=datetime.now(),
            area_geografica="Test",
            tipo_medio="Test",
            es_opinion=False,
            es_oficial=False
        )
        
        hecho = HechoResponse(
            id=1,
            contenido="Test content",
            fecha_ocurrencia="2024-01-01T10:00:00",
            precision_temporal="exact",
            importancia=5,
            tipo_hecho="test",
            pais=[],  # Array vacío
            region=[],  # Array vacío
            ciudad=[],  # Array vacío
            etiquetas=[],  # Array vacío
            fecha_ingreso=datetime.now(),
            articulo_metadata=articulo,
            relaciones=[]  # Sin relaciones
        )
        
        assert len(hecho.pais) == 0
        assert len(hecho.region) == 0
        assert len(hecho.ciudad) == 0
        assert len(hecho.etiquetas) == 0
        assert len(hecho.relaciones) == 0
    
    def test_hecho_response_con_muchas_relaciones(self):
        """Test HechoResponse con un número extremo de relaciones."""
        articulo = ArticuloMetadata(
            medio="Test",
            titular="Test",
            fecha_publicacion=datetime.now(),
            area_geografica="Test",
            tipo_medio="Test",
            es_opinion=False,
            es_oficial=False
        )
        
        # Crear 1000 relaciones
        relaciones = []
        for i in range(1000):
            relaciones.append(HechoRelacionInfo(
                hecho_relacionado_id=i + 2,
                tipo_relacion="complementario",
                fuerza_relacion=(i % 10) + 1,
                direccion="origen"
            ))
        
        hecho = HechoResponse(
            id=1,
            contenido="Hecho con muchas relaciones",
            fecha_ocurrencia="2024-01-01T10:00:00",
            precision_temporal="approximate",
            importancia=8,
            tipo_hecho="evento_masivo",
            fecha_ingreso=datetime.now(),
            articulo_metadata=articulo,
            relaciones=relaciones
        )
        
        assert len(hecho.relaciones) == 1000
        assert all(r.hecho_relacionado_id >= 2 for r in hecho.relaciones)
    
    def test_hecho_response_con_metadata_none(self):
        """Test HechoResponse con metadata como None."""
        articulo = ArticuloMetadata(
            medio="Test",
            titular="Test",
            fecha_publicacion=datetime.now(),
            area_geografica="Test",
            tipo_medio="Test",
            es_opinion=False,
            es_oficial=False
        )
        
        hecho = HechoResponse(
            id=1,
            contenido="Test",
            fecha_ocurrencia="2024-01-01T10:00:00",
            precision_temporal="unknown",
            importancia=1,
            tipo_hecho="test",
            fecha_ingreso=datetime.now(),
            articulo_metadata=articulo,
            metadata=None  # None en lugar de dict
        )
        
        # El modelo debe usar el valor por defecto
        assert hecho.metadata == {}


class TestHechosServiceEdgeCases:
    """Tests de casos edge para HechosService."""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client."""
        with patch('src.services.hechos_service.SupabaseClient.get_client') as mock:
            client = MagicMock()
            mock.return_value = client
            yield client
    
    @pytest.fixture
    def hechos_service(self, mock_supabase_client):
        """HechosService con mock."""
        return HechosService()
    
    @pytest.mark.asyncio
    async def test_get_relaciones_con_datos_inconsistentes(self, hechos_service, mock_supabase_client):
        """Test manejo de datos inconsistentes desde la base de datos."""
        # Datos que violan el schema esperado
        datos_inconsistentes = [
            {
                "hecho_origen_id": 1,
                "fecha_ocurrencia_origen": "[2024-01-01 10:00:00,2024-01-01 12:00:00)",
                "hecho_destino_id": 2,
                "fecha_ocurrencia_destino": "[2024-01-01 14:00:00,2024-01-01 16:00:00)",
                "tipo_relacion": "causa",
                "fuerza_relacion": 15,  # Fuera del rango 1-10
                "descripcion_relacion": "Test",
                "fecha_deteccion": "2024-01-15T10:30:00"
            },
            {
                "hecho_origen_id": 3,
                "fecha_ocurrencia_origen": None,  # Campo requerido como None
                "hecho_destino_id": 4,
                "fecha_ocurrencia_destino": "[2024-01-01 16:00:00,2024-01-01 18:00:00)",
                "tipo_relacion": "consecuencia",
                "fuerza_relacion": 7,
                "descripcion_relacion": None,
                "fecha_deteccion": "2024-01-15T11:00:00"
            }
        ]
        
        # Setup mock
        mock_query = MagicMock()
        mock_result = MagicMock()
        mock_result.data = datos_inconsistentes
        mock_query.execute.return_value = mock_result
        
        mock_supabase_client.table.return_value.select.return_value = mock_query
        mock_query.or_.return_value = mock_query
        
        # El método debe manejar errores de validación
        with pytest.raises(Exception):
            await hechos_service.get_relaciones_para_hechos([1, 2, 3, 4])
    
    @pytest.mark.asyncio
    async def test_get_relaciones_con_referencia_circular_compleja(self, hechos_service, mock_supabase_client):
        """Test relaciones circulares complejas A→B→C→A."""
        datos_circulares = [
            {
                "hecho_origen_id": 1,
                "fecha_ocurrencia_origen": "[2024-01-01 10:00:00,2024-01-01 12:00:00)",
                "hecho_destino_id": 2,
                "fecha_ocurrencia_destino": "[2024-01-01 14:00:00,2024-01-01 16:00:00)",
                "tipo_relacion": "consecuencia",
                "fuerza_relacion": 8,
                "descripcion_relacion": "A causa B",
                "fecha_deteccion": "2024-01-15T10:30:00"
            },
            {
                "hecho_origen_id": 2,
                "fecha_ocurrencia_origen": "[2024-01-01 14:00:00,2024-01-01 16:00:00)",
                "hecho_destino_id": 3,
                "fecha_ocurrencia_destino": "[2024-01-01 18:00:00,2024-01-01 20:00:00)",
                "tipo_relacion": "consecuencia",
                "fuerza_relacion": 7,
                "descripcion_relacion": "B causa C",
                "fecha_deteccion": "2024-01-15T11:00:00"
            },
            {
                "hecho_origen_id": 3,
                "fecha_ocurrencia_origen": "[2024-01-01 18:00:00,2024-01-01 20:00:00)",
                "hecho_destino_id": 1,
                "fecha_ocurrencia_destino": "[2024-01-01 10:00:00,2024-01-01 12:00:00)",
                "tipo_relacion": "consecuencia",
                "fuerza_relacion": 6,
                "descripcion_relacion": "C causa A (circular)",
                "fecha_deteccion": "2024-01-15T12:00:00"
            }
        ]
        
        # Setup mock
        mock_query = MagicMock()
        mock_result = MagicMock()
        mock_result.data = datos_circulares
        mock_query.execute.return_value = mock_result
        
        mock_supabase_client.table.return_value.select.return_value = mock_query
        mock_query.or_.return_value = mock_query
        
        # Test
        resultado = await hechos_service.get_relaciones_para_hechos([1, 2, 3])
        
        # Verificar que se manejan correctamente las relaciones circulares
        assert 1 in resultado
        assert 2 in resultado
        assert 3 in resultado
        
        # Cada hecho debe tener 2 relaciones (una como origen, una como destino)
        assert len(resultado[1]) == 2
        assert len(resultado[2]) == 2
        assert len(resultado[3]) == 2
        
        # Verificar direcciones correctas
        relaciones_1 = resultado[1]
        related_ids_1 = [r.hecho_relacionado_id for r in relaciones_1]
        assert 2 in related_ids_1  # 1→2
        assert 3 in related_ids_1  # 3→1
    
    @pytest.mark.asyncio
    async def test_get_relaciones_con_ids_duplicados(self, hechos_service, mock_supabase_client):
        """Test comportamiento con IDs duplicados en la lista de entrada."""
        datos_mock = [
            {
                "hecho_origen_id": 1,
                "fecha_ocurrencia_origen": "[2024-01-01 10:00:00,2024-01-01 12:00:00)",
                "hecho_destino_id": 2,
                "fecha_ocurrencia_destino": "[2024-01-01 14:00:00,2024-01-01 16:00:00)",
                "tipo_relacion": "causa",
                "fuerza_relacion": 8,
                "descripcion_relacion": "Test",
                "fecha_deteccion": "2024-01-15T10:30:00"
            }
        ]
        
        # Setup mock
        mock_query = MagicMock()
        mock_result = MagicMock()
        mock_result.data = datos_mock
        mock_query.execute.return_value = mock_result
        
        mock_supabase_client.table.return_value.select.return_value = mock_query
        mock_query.or_.return_value = mock_query
        
        # Test con IDs duplicados
        ids_con_duplicados = [1, 1, 2, 2, 1, 3]
        resultado = await hechos_service.get_relaciones_para_hechos(ids_con_duplicados)
        
        # Debe funcionar sin problemas
        assert isinstance(resultado, dict)
        
        # Verificar que se construyó la query correctamente (sin duplicados en string)
        expected_or_filter = (
            "hecho_origen_id.in.(1,1,2,2,1,3), "
            "hecho_destino_id.in.(1,1,2,2,1,3)"
        )
        mock_query.or_.assert_called_once_with(expected_or_filter)
    
    @pytest.mark.asyncio
    async def test_get_relaciones_con_lista_enormemente_grande(self, hechos_service, mock_supabase_client):
        """Test con lista de IDs enormemente grande."""
        # Setup mock para retornar datos vacíos
        mock_query = MagicMock()
        mock_result = MagicMock()
        mock_result.data = []
        mock_query.execute.return_value = mock_result
        
        mock_supabase_client.table.return_value.select.return_value = mock_query
        mock_query.or_.return_value = mock_query
        
        # Lista con 10,000 IDs
        ids_grandes = list(range(1, 10001))
        resultado = await hechos_service.get_relaciones_para_hechos(ids_grandes)
        
        # Debe funcionar sin problemas
        assert resultado == {}
        
        # Verificar que la query se construyó (aunque sea muy larga)
        mock_query.or_.assert_called_once()
        call_args = mock_query.or_.call_args[0][0]
        assert "hecho_origen_id.in." in call_args
        assert "hecho_destino_id.in." in call_args
    
    @pytest.mark.asyncio
    async def test_get_hechos_for_revision_con_relaciones_malformadas(self, hechos_service, mock_supabase_client):
        """Test get_hechos_for_revision cuando get_relaciones_para_hechos falla."""
        # Mock que retorna hechos válidos
        hechos_data = [
            {
                "id": 1,
                "contenido": "Test hecho",
                "fecha_ocurrencia": "2024-01-01T00:00:00",
                "precision_temporal": "exact",
                "importancia": 8,
                "tipo_hecho": "declaracion",
                "pais": ["Argentina"],
                "region": [],
                "ciudad": [],
                "etiquetas": [],
                "frecuencia_citacion": 0,
                "total_menciones": 0,
                "menciones_confirmatorias": 0,
                "fecha_ingreso": "2024-01-15T10:30:00",
                "evaluacion_editorial": None,
                "editor_evaluador": None,
                "fecha_evaluacion_editorial": None,
                "justificacion_evaluacion_editorial": None,
                "consenso_fuentes": None,
                "es_evento_futuro": False,
                "estado_programacion": None,
                "metadata": {},
                "articulos": {
                    "medio": "Test Medio",
                    "titular": "Test Titular",
                    "fecha_publicacion": "2024-01-01T00:00:00",
                    "url": "https://test.com/1",
                    "area_geografica": "Argentina",
                    "tipo_medio": "digital",
                    "autor": "Test Author",
                    "seccion": "Test",
                    "es_opinion": False,
                    "es_oficial": False,
                    "resumen": None,
                    "categorias_asignadas": [],
                    "puntuacion_relevancia": None,
                    "estado_procesamiento": None
                }
            }
        ]
        
        # Setup mock para consulta principal
        mock_query = MagicMock()
        mock_result = MagicMock()
        mock_result.data = hechos_data
        mock_query.execute.return_value = mock_result
        
        # Count query
        mock_count_result = MagicMock()
        mock_count_result.count = 1
        
        def table_side_effect(table_name):
            if table_name == 'hecho_relacionado':
                # Simular error en consulta de relaciones
                raise Exception("Database error in relationships")
            
            query_mock = MagicMock()
            
            def select_side_effect(*args, **kwargs):
                if 'count' in kwargs and kwargs['count'] == 'exact' and args[0] == 'id':
                    count_mock = MagicMock()
                    count_mock.execute.return_value = mock_count_result
                    return count_mock
                return mock_query
            
            query_mock.select = select_side_effect
            
            # Chain methods for main query
            query_mock.order = MagicMock(return_value=query_mock)
            query_mock.range = MagicMock(return_value=query_mock)
            
            return query_mock
        
        mock_supabase_client.table.side_effect = table_side_effect
        
        # El método debe fallar cuando no puede obtener relaciones
        filter_params = {"limit": 10, "offset": 0}
        with pytest.raises(Exception) as exc_info:
            await hechos_service.get_hechos_for_revision(filter_params)
        
        assert "Database error in relationships" in str(exc_info.value)


class TestValidacionesFiltros:
    """Tests de validaciones para filtros edge cases."""
    
    def test_filtro_fechas_orden_incorrecto(self):
        """Test validación cuando fecha_fin es anterior a fecha_inicio."""
        with pytest.raises(ValidationError) as exc_info:
            HechoFilterParams(
                fecha_inicio=datetime(2024, 12, 31),
                fecha_fin=datetime(2024, 1, 1)  # Anterior a inicio
            )
        assert "fecha_fin must be after or equal to fecha_inicio" in str(exc_info.value)
    
    def test_filtro_fechas_iguales(self):
        """Test que fechas iguales son válidas."""
        misma_fecha = datetime(2024, 6, 15)
        filtro = HechoFilterParams(
            fecha_inicio=misma_fecha,
            fecha_fin=misma_fecha
        )
        assert filtro.fecha_inicio == filtro.fecha_fin
    
    def test_filtro_importancia_rango_invalido(self):
        """Test validación de rango de importancia inválido."""
        with pytest.raises(ValidationError) as exc_info:
            HechoFilterParams(
                importancia_min=8,
                importancia_max=3  # Menor que min
            )
        assert "importancia_max must be greater than or equal to importancia_min" in str(exc_info.value)
    
    def test_filtro_importancia_extremos_validos(self):
        """Test rangos de importancia en los extremos."""
        # Mínimo válido
        filtro1 = HechoFilterParams(importancia_min=1, importancia_max=1)
        assert filtro1.importancia_min == 1
        
        # Máximo válido
        filtro2 = HechoFilterParams(importancia_min=10, importancia_max=10)
        assert filtro2.importancia_max == 10
        
        # Rango completo
        filtro3 = HechoFilterParams(importancia_min=1, importancia_max=10)
        assert filtro3.importancia_max - filtro3.importancia_min == 9
    
    def test_filtro_strings_muy_largos(self):
        """Test manejo de strings extremadamente largos en filtros."""
        string_largo = "A" * 1000  # 1KB de texto
        
        # Debería truncarse o validarse según max_length
        with pytest.raises(ValidationError):
            HechoFilterParams(medio=string_largo)  # max_length=100
        
        with pytest.raises(ValidationError):
            HechoFilterParams(area_geografica=string_largo)  # max_length=50
    
    def test_filtro_caracteres_especiales(self):
        """Test filtros con caracteres especiales y Unicode."""
        filtro = HechoFilterParams(
            medio="El País (España) 🇪🇸",
            area_geografica="São Paulo, Brasil 🇧🇷",
            tipo_hecho="declaración_política",
            evaluacion_editorial="verificado_✓"
        )
        
        assert "🇪🇸" in filtro.medio
        assert "São Paulo" in filtro.area_geografica
        assert "declaración_política" == filtro.tipo_hecho
        assert "verificado_✓" == filtro.evaluacion_editorial
    
    def test_to_dict_excluye_none_valores(self):
        """Test que to_dict excluye correctamente valores None."""
        filtro = HechoFilterParams(
            medio="Test",
            fecha_inicio=None,
            importancia_min=5,
            area_geografica=None,
            limit=20
        )
        
        dict_result = filtro.to_dict()
        
        assert "medio" in dict_result
        assert "importancia_min" in dict_result
        assert "limit" in dict_result
        assert "fecha_inicio" not in dict_result
        assert "area_geografica" not in dict_result
        
        # Verificar valores
        assert dict_result["medio"] == "Test"
        assert dict_result["importancia_min"] == 5
        assert dict_result["limit"] == 20


class TestRelacionesBidireccionales:
    """Tests específicos para relaciones bidireccionales y casos complejos."""
    
    def test_relacion_bidireccional_contradictoria(self):
        """Test relación contradictoria (bidireccional por naturaleza)."""
        relacion = HechoRelacionado(
            hecho_origen_id=1,
            fecha_ocurrencia_origen="[2024-01-01 10:00:00,2024-01-01 12:00:00)",
            hecho_destino_id=2,
            fecha_ocurrencia_destino="[2024-01-01 10:30:00,2024-01-01 11:30:00)",
            tipo_relacion="contradictorio",
            fuerza_relacion=9
        )
        
        assert relacion.is_bidirectional is True
        
        # Desde la perspectiva del hecho 1
        assert relacion.get_related_id(1) == 2
        assert relacion.get_direction_for_hecho(1) == "origen"
        
        # Desde la perspectiva del hecho 2
        assert relacion.get_related_id(2) == 1
        assert relacion.get_direction_for_hecho(2) == "destino"
    
    def test_relaciones_multiples_mismo_par_hechos(self):
        """Test múltiples relaciones entre el mismo par de hechos."""
        # Dos relaciones diferentes entre los mismos hechos
        relacion1 = HechoRelacionado(
            hecho_origen_id=1,
            fecha_ocurrencia_origen="[2024-01-01 10:00:00,2024-01-01 12:00:00)",
            hecho_destino_id=2,
            fecha_ocurrencia_destino="[2024-01-01 14:00:00,2024-01-01 16:00:00)",
            tipo_relacion="causa",
            fuerza_relacion=8
        )
        
        relacion2 = HechoRelacionado(
            hecho_origen_id=1,
            fecha_ocurrencia_origen="[2024-01-01 10:00:00,2024-01-01 12:00:00)",
            hecho_destino_id=2,
            fecha_ocurrencia_destino="[2024-01-01 14:00:00,2024-01-01 16:00:00)",
            tipo_relacion="temporal_anterior",
            fuerza_relacion=6
        )
        
        # Ambas relaciones son válidas y diferentes
        assert relacion1.tipo_relacion != relacion2.tipo_relacion
        assert relacion1.fuerza_relacion != relacion2.fuerza_relacion
        
        # Pero involucran los mismos hechos
        for relacion in [relacion1, relacion2]:
            assert relacion.involves_hecho(1)
            assert relacion.involves_hecho(2)
            assert relacion.get_related_id(1) == 2
            assert relacion.get_related_id(2) == 1
    
    def test_cadena_relaciones_larga(self):
        """Test cadena larga de relaciones A→B→C→D→E."""
        # Crear cadena de 5 hechos
        relaciones = []
        for i in range(4):  # 4 relaciones para 5 hechos
            relacion = HechoRelacionado(
                hecho_origen_id=i + 1,
                fecha_ocurrencia_origen=f"[2024-01-0{i+1} 10:00:00,2024-01-0{i+1} 12:00:00)",
                hecho_destino_id=i + 2,
                fecha_ocurrencia_destino=f"[2024-01-0{i+2} 10:00:00,2024-01-0{i+2} 12:00:00)",
                tipo_relacion="consecuencia",
                fuerza_relacion=7 - i  # Fuerza decreciente
            )
            relaciones.append(relacion)
        
        # Verificar cadena
        assert len(relaciones) == 4
        
        # Verificar secuencia
        for i, relacion in enumerate(relaciones):
            assert relacion.hecho_origen_id == i + 1
            assert relacion.hecho_destino_id == i + 2
            assert relacion.tipo_relacion == "consecuencia"
        
        # Verificar fuerzas decrecientes
        fuerzas = [r.fuerza_relacion for r in relaciones]
        assert fuerzas == [7, 6, 5, 4]