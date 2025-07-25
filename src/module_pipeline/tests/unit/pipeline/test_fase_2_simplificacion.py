"""
Tests para la Fase 2: Simplificación de Texto
============================================
"""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch  # noqa: F401
from uuid import uuid4

import pytest

from ....src.models.procesamiento import ResultadoFase1Triaje
from ....src.models.simplificacion import (
    MetadatosFase2Simplificacion,  # noqa: F401
    ResultadoFase2Simplificacion,
)
from ....src.pipeline.fase_2_simplificacion import (
    _analizar_transformaciones,
    _calcular_fechas_relativas,
    _llamar_groq_simplificacion,
    _preparar_prompt_simplificacion,  # noqa: F401
    ejecutar_fase_2_simplificacion,
    simplificar_con_chunking,
)


class TestCalcularFechasRelativas:
    """Tests para el cálculo de fechas relativas."""

    def test_calcular_fechas_correctamente(self):
        """Debe calcular las fechas relativas correctamente."""
        fechas = _calcular_fechas_relativas("2025-06-10")

        assert fechas["{{FECHA_AYER}}"] == "2025-06-09"
        assert fechas["{{FECHA_MAÑANA}}"] == "2025-06-11"
        assert "{{FECHA_INICIO_SEMANA_PASADA}}" in fechas
        assert "{{FECHA_FIN_SEMANA_PASADA}}" in fechas

    def test_fecha_invalida_retorna_vacio(self):
        """Debe retornar diccionario vacío con fecha inválida."""
        assert _calcular_fechas_relativas("fecha-invalida") == {}
        assert _calcular_fechas_relativas(None) == {}
        assert _calcular_fechas_relativas("") == {}


class TestAnalizarTransformaciones:
    """Tests para el análisis de transformaciones."""

    def test_detectar_siglas_expandidas(self):
        """Debe detectar cuando se expanden siglas."""
        original = "El BCE anunció medidas"
        simplificado = "El Banco Central Europeo (BCE) anunció medidas"

        transformaciones = _analizar_transformaciones(original, simplificado)
        assert transformaciones["siglas_expandidas"] > 0

    def test_detectar_referencias_temporales(self):
        """Debe detectar resolución de referencias temporales."""
        original = "Ayer el ministro declaró"
        simplificado = "El 9 de junio de 2025 el ministro declaró"

        transformaciones = _analizar_transformaciones(original, simplificado)
        assert transformaciones["referencias_temporales"] > 0

    def test_detectar_valoraciones_eliminadas(self):
        """Debe detectar eliminación de valoraciones."""
        original = "El polémico plan fue controvertido"
        simplificado = "El plan fue discutido"

        transformaciones = _analizar_transformaciones(original, simplificado)
        assert transformaciones["valoraciones_eliminadas"] >= 2


class TestLlamarGroqSimplificacion:
    """Tests para la llamada a Groq."""

    @patch("src.pipeline.fase_2_simplificacion.datetime")
    def test_llamada_exitosa(self, mock_datetime):
        """Debe procesar respuesta exitosa de Groq."""
        # Mock de datetime
        mock_datetime.now.return_value = datetime(2025, 6, 10, 12, 0, 0)

        # Mock del cliente Groq
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Texto simplificado"))]
        mock_response.usage = Mock(prompt_tokens=100, completion_tokens=80)
        mock_client.chat.completions.create.return_value = mock_response

        texto, metadatos = _llamar_groq_simplificacion(
            mock_client, "prompt de prueba", "llama-3.1-8b-instant"
        )

        assert texto == "Texto simplificado"
        assert metadatos["nombre_modelo"] == "llama-3.1-8b-instant"
        assert metadatos["tokens_prompt"] == 100
        assert metadatos["tokens_respuesta"] == 80
        assert "duracion_llamada_ms" in metadatos

    def test_manejo_error_groq(self):
        """Debe manejar errores de Groq correctamente."""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("Error de API")

        with pytest.raises(Exception):
            _llamar_groq_simplificacion(mock_client, "prompt", "modelo")


class TestEjecutarFase2Simplificacion:
    """Tests para la función principal de simplificación."""

    @pytest.fixture
    def resultado_triaje_mock(self):
        """Fixture para resultado de triaje."""
        return ResultadoFase1Triaje(
            id_resultado_triaje=uuid4(),
            id_fragmento=uuid4(),
            es_relevante=True,
            texto_para_siguiente_fase="El polémico plan del BCE será implementado mañana.",
        )

    @patch("src.pipeline.fase_2_simplificacion.Groq")
    @patch("src.pipeline.fase_2_simplificacion._cargar_prompt_simplificacion")
    def test_simplificacion_exitosa(
        self, mock_cargar_prompt, mock_groq_class, resultado_triaje_mock
    ):
        """Debe simplificar texto exitosamente."""
        # Mock del prompt
        mock_cargar_prompt.return_value = "Simplifica: {{CONTENIDO_ORIGINAL}}"

        # Mock del cliente Groq
        mock_client = Mock()
        mock_groq_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content="El plan del Banco Central Europeo (BCE) será implementado el 11 de junio de 2025."
                )
            )
        ]
        mock_response.usage = Mock(prompt_tokens=150, completion_tokens=120)
        mock_client.chat.completions.create.return_value = mock_response

        # Ejecutar con API key mock
        resultado = ejecutar_fase_2_simplificacion(
            resultado_triaje_mock, fecha_articulo="2025-06-10", groq_api_key="test-key"
        )

        # Verificar resultado
        assert isinstance(resultado, ResultadoFase2Simplificacion)
        assert resultado.simplificacion_exitosa
        assert "Banco Central Europeo (BCE)" in resultado.texto_simplificado
        assert resultado.metadatos_simplificacion is not None
        assert resultado.metadatos_simplificacion.longitud_texto_original > 0
        assert resultado.metadatos_simplificacion.longitud_texto_simplificado > 0

    def test_error_sin_texto(self, resultado_triaje_mock):
        """Debe fallar si no hay texto para simplificar."""
        resultado_triaje_mock.texto_para_siguiente_fase = None

        resultado = ejecutar_fase_2_simplificacion(
            resultado_triaje_mock, groq_api_key="test-key"
        )

        assert not resultado.simplificacion_exitosa
        assert resultado.requiere_revision_manual
        assert "Error" in resultado.razon_revision

    @patch("src.pipeline.fase_2_simplificacion.os.getenv")
    def test_error_sin_api_key(self, mock_getenv, resultado_triaje_mock):
        """Debe fallar si no hay API key."""
        mock_getenv.return_value = None

        resultado = ejecutar_fase_2_simplificacion(resultado_triaje_mock)

        assert not resultado.simplificacion_exitosa
        assert resultado.requiere_revision_manual

    @patch("src.pipeline.fase_2_simplificacion.Groq")
    @patch("src.pipeline.fase_2_simplificacion._cargar_prompt_simplificacion")
    def test_uso_modelo_grande_para_texto_largo(
        self, mock_cargar_prompt, mock_groq_class, resultado_triaje_mock
    ):
        """Debe usar modelo grande para textos largos."""
        # Texto largo
        resultado_triaje_mock.texto_para_siguiente_fase = "x" * 7000

        mock_cargar_prompt.return_value = "Simplifica: {{CONTENIDO_ORIGINAL}}"

        mock_client = Mock()
        mock_groq_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Texto simplificado largo"))]
        mock_response.usage = Mock(prompt_tokens=1000, completion_tokens=800)
        mock_client.chat.completions.create.return_value = mock_response

        resultado = ejecutar_fase_2_simplificacion(  # noqa: F841
            resultado_triaje_mock, groq_api_key="test-key"
        )

        # Verificar que se llamó con el modelo grande
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]["model"] == "llama-3.1-70b-versatile"


class TestSimplificarConChunking:
    """Tests para simplificación con chunking."""

    @pytest.fixture
    def resultado_triaje_mock(self):
        """Fixture para resultado de triaje."""
        return ResultadoFase1Triaje(
            id_resultado_triaje=uuid4(),
            id_fragmento=uuid4(),
            es_relevante=True,
            texto_para_siguiente_fase="Texto completo original",
        )

    @patch("src.pipeline.fase_2_simplificacion.Groq")
    @patch("src.pipeline.fase_2_simplificacion._cargar_prompt_simplificacion")
    def test_simplificar_multiples_chunks(
        self, mock_cargar_prompt, mock_groq_class, resultado_triaje_mock
    ):
        """Debe simplificar múltiples chunks correctamente."""
        mock_cargar_prompt.return_value = "Simplifica: {{CONTENIDO_ORIGINAL}}"

        # Mock del cliente Groq
        mock_client = Mock()
        mock_groq_class.return_value = mock_client

        # Respuestas para cada chunk
        respuestas = [
            "Chunk 1 simplificado",
            "Chunk 2 simplificado",
            "Chunk 3 simplificado",
        ]

        mock_responses = []
        for resp in respuestas:
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content=resp))]
            mock_response.usage = Mock(prompt_tokens=50, completion_tokens=40)
            mock_responses.append(mock_response)

        mock_client.chat.completions.create.side_effect = mock_responses

        # Ejecutar
        chunks = ["Chunk 1 original", "Chunk 2 original", "Chunk 3 original"]
        resultado = simplificar_con_chunking(
            resultado_triaje_mock, chunks, groq_api_key="test-key"
        )

        # Verificar
        assert resultado.simplificacion_exitosa
        assert "Chunk 1 simplificado" in resultado.texto_simplificado
        assert "Chunk 2 simplificado" in resultado.texto_simplificado
        assert "Chunk 3 simplificado" in resultado.texto_simplificado
        assert (
            resultado.texto_simplificado.count("\n\n") == 2
        )  # 3 chunks = 2 separadores
        assert (
            "Procesado en 3 chunks"
            in resultado.metadatos_simplificacion.advertencias_simplificacion
        )

    @patch("src.pipeline.fase_2_simplificacion.Groq")
    @patch("src.pipeline.fase_2_simplificacion._cargar_prompt_simplificacion")
    def test_fallo_parcial_usa_original(
        self, mock_cargar_prompt, mock_groq_class, resultado_triaje_mock
    ):
        """Debe usar chunk original si falla la simplificación."""
        mock_cargar_prompt.return_value = "Simplifica: {{CONTENIDO_ORIGINAL}}"

        mock_client = Mock()
        mock_groq_class.return_value = mock_client

        # Primera llamada exitosa, segunda falla
        mock_response_ok = Mock()
        mock_response_ok.choices = [Mock(message=Mock(content="Chunk 1 simplificado"))]
        mock_response_ok.usage = Mock(prompt_tokens=50, completion_tokens=40)

        mock_client.chat.completions.create.side_effect = [
            mock_response_ok,
            Exception("Error en chunk 2"),
        ]

        chunks = ["Chunk 1", "Chunk 2"]
        resultado = simplificar_con_chunking(
            resultado_triaje_mock, chunks, groq_api_key="test-key"
        )

        # Debe contener el chunk 1 simplificado y el chunk 2 original
        assert "Chunk 1 simplificado" in resultado.texto_simplificado
        assert "Chunk 2" in resultado.texto_simplificado
