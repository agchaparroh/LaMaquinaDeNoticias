import pytest
import uuid
from unittest.mock import patch, MagicMock

from src.module_pipeline.src.pipeline.fase_1_triaje import ejecutar_fase_1, ErrorFase1
from src.module_pipeline.src.models.procesamiento import ResultadoFase1Triaje, MetadatosFase1Triaje

# Helper to create a mock spaCy model
def _get_mock_spacy_model(lang="es"):
    mock_model = MagicMock()
    mock_model.meta = {"name": f"{lang}_test_model"}
    mock_model.lang = lang
    # Mock the model's behavior when called with text
    mock_doc = MagicMock()
    mock_doc.ents = []
    mock_doc.sents = []
    mock_model.return_value = mock_doc
    return mock_model

# Test data
SAMPLE_UUID = uuid.uuid4()
SAMPLE_TEXT = "Este es un texto de prueba para la Fase 1."
SAMPLE_TEXT_EN = "This is a test text in English for Phase 1."

@patch('src.module_pipeline.src.pipeline.fase_1_triaje._cargar_modelo_spacy')
def test_ejecutar_fase_1_spacy_load_failure(mock_cargar_modelo_spacy):
    """
    Test that ejecutar_fase_1 returns a fallback ResultadoFase1Triaje
    when spaCy model loading fails (_cargar_modelo_spacy returns None).
    """
    mock_cargar_modelo_spacy.side_effect = RuntimeError("Simulated spaCy load failure")

    id_fragmento = SAMPLE_UUID
    texto_original = SAMPLE_TEXT
    modelo_spacy_nombre = "es_core_news_nonexistent"

    resultado = ejecutar_fase_1(id_fragmento, texto_original, modelo_spacy_nombre)

    assert isinstance(resultado, ResultadoFase1Triaje)
    assert resultado.id_fragmento == id_fragmento
    assert resultado.es_relevante is True # Updated: Fallback accepts article
    assert resultado.decision_triaje == "FALLBACK_ACEPTADO_ERROR_PREPROCESO" # Updated
    assert "Fallo al cargar modelo spaCy" in resultado.justificacion_triaje # Updated message
    assert "Simulated spaCy load failure" in resultado.justificacion_triaje
    assert resultado.texto_para_siguiente_fase == texto_original # Updated: original text

    assert isinstance(resultado.metadatos_specificos_triaje, MetadatosFase1Triaje)
    assert resultado.metadatos_specificos_triaje.nombre_modelo_triaje == modelo_spacy_nombre
    assert resultado.metadatos_specificos_triaje.notas_adicionales is not None
    # The actual message is in metadatos_specificos_triaje.message from the handler's dict construction
    assert any("SpaCy model loading failed" in nota for nota in resultado.metadatos_specificos_triaje.notas_adicionales)


@patch('src.module_pipeline.src.pipeline.fase_1_triaje._cargar_modelo_spacy')
@patch('src.module_pipeline.src.pipeline.fase_1_triaje._get_groq_config')
@patch('src.module_pipeline.src.pipeline.fase_1_triaje._limpiar_texto') # Mock to control cleaned text
def test_ejecutar_fase_1_groq_api_key_missing(mock_limpiar_texto, mock_get_groq_config, mock_cargar_modelo_spacy):
    """
    Test fallback when Groq API key is missing. Expects a fallback ResultadoFase1Triaje.
    """
    mock_cargar_modelo_spacy.return_value = _get_mock_spacy_model()
    mock_get_groq_config.return_value = {"api_key": None, "model_id": "test_model_no_key"}

    cleaned_text_mock = "Texto limpio simulado."
    mock_limpiar_texto.return_value = cleaned_text_mock

    id_fragmento = SAMPLE_UUID
    texto_original = SAMPLE_TEXT

    resultado = ejecutar_fase_1(id_fragmento, texto_original)

    assert isinstance(resultado, ResultadoFase1Triaje)
    assert resultado.id_fragmento == id_fragmento
    assert resultado.es_relevante is True # Fallback accepts
    assert resultado.decision_triaje == "FALLBACK_ACEPTADO_ERROR_LLM" # Fallback decision
    assert "GROQ_API_KEY no configurada" in resultado.justificacion_triaje
    assert resultado.texto_para_siguiente_fase == cleaned_text_mock # Cleaned text should be passed

    assert isinstance(resultado.metadatos_specificos_triaje, MetadatosFase1Triaje)
    assert resultado.metadatos_specificos_triaje.nombre_modelo_triaje == "test_model_no_key"
    assert resultado.metadatos_specificos_triaje.notas_adicionales is not None
    assert any("GROQ_API_KEY no configurada" in nota for nota in resultado.metadatos_specificos_triaje.notas_adicionales)

@patch('src.module_pipeline.src.pipeline.fase_1_triaje._cargar_modelo_spacy')
@patch('src.module_pipeline.src.pipeline.fase_1_triaje._get_groq_config')
@patch('src.module_pipeline.src.pipeline.fase_1_triaje._llamar_groq_api_triaje')
@patch('src.module_pipeline.src.pipeline.fase_1_triaje._limpiar_texto')
def test_ejecutar_fase_1_groq_relevance_api_error(mock_limpiar_texto, mock_llamar_groq_triaje, mock_get_groq_config, mock_cargar_modelo_spacy):
    """
    Test fallback when _llamar_groq_api_triaje raises GroqAPIError.
    """
    from src.module_pipeline.src.utils.error_handling import GroqAPIError, ErrorPhase

    mock_cargar_modelo_spacy.return_value = _get_mock_spacy_model()
    mock_get_groq_config.return_value = {"api_key": "fake_key", "model_id": "test_relevance_model"}

    cleaned_text_mock = "Texto limpio para prueba de error Groq."
    mock_limpiar_texto.return_value = cleaned_text_mock

    # Simulate GroqAPIError being raised by the decorated function
    simulated_groq_error = GroqAPIError("Simulated Groq API Error during relevance", phase=ErrorPhase.FASE_1_TRIAJE)
    mock_llamar_groq_triaje.side_effect = simulated_groq_error

    id_fragmento = SAMPLE_UUID
    texto_original = SAMPLE_TEXT

    resultado = ejecutar_fase_1(id_fragmento, texto_original)

    assert isinstance(resultado, ResultadoFase1Triaje)
    assert resultado.id_fragmento == id_fragmento
    assert resultado.es_relevante is True # Fallback accepts
    assert resultado.decision_triaje == "FALLBACK_ACEPTADO_ERROR_LLM" # Fallback decision
    assert "Simulated Groq API Error during relevance" in resultado.justificacion_triaje
    assert resultado.texto_para_siguiente_fase == cleaned_text_mock # Cleaned text

    assert isinstance(resultado.metadatos_specificos_triaje, MetadatosFase1Triaje)
    assert resultado.metadatos_specificos_triaje.nombre_modelo_triaje == "test_relevance_model"
    assert resultado.metadatos_specificos_triaje.notas_adicionales is not None
    assert any("Groq API failed during relevance evaluation" in nota for nota in resultado.metadatos_specificos_triaje.notas_adicionales)


@patch('src.module_pipeline.src.pipeline.fase_1_triaje._cargar_modelo_spacy')
@patch('src.module_pipeline.src.pipeline.fase_1_triaje._get_groq_config')
@patch('src.module_pipeline.src.pipeline.fase_1_triaje._detectar_idioma')
@patch('src.module_pipeline.src.pipeline.fase_1_triaje._llamar_groq_api_triaje')
@patch('src.module_pipeline.src.pipeline.fase_1_triaje._llamar_groq_api_traduccion')
@patch('src.module_pipeline.src.pipeline.fase_1_triaje._limpiar_texto')
def test_ejecutar_fase_1_groq_translation_api_error(
    mock_limpiar_texto,
    mock_llamar_traduccion,
    mock_llamar_triaje,
    mock_detectar_idioma,
    mock_get_groq_config,
    mock_cargar_modelo_spacy
):
    """
    Test fallback when _llamar_groq_api_traduccion raises GroqAPIError.
    Ensures original cleaned text is used and notes are added.
    """
    from src.module_pipeline.src.utils.error_handling import GroqAPIError, ErrorPhase

    mock_spacy_model = _get_mock_spacy_model(lang="en")
    mock_cargar_modelo_spacy.return_value = mock_spacy_model

    mock_detectar_idioma.return_value = "en"

    cleaned_text_en_mock = "Simulated cleaned English text."
    mock_limpiar_texto.return_value = cleaned_text_en_mock

    mock_get_groq_config.return_value = {"api_key": "fake_key", "model_id": "test_translation_model"}

    mock_triaje_response_content = """
    EXCLUSIÓN: NO
    TIPO DE ARTÍCULO: NOTICIA
    Relevancia geográfica: [4] - España
    Relevancia temática: [5] - Economía
    Densidad factual: [3]
    Complejidad relacional: [3]
    Valor informativo: [4]
    TOTAL: [19]/25
    DECISIÓN: PROCESAR
    JUSTIFICACIÓN: El artículo es relevante.
    ELEMENTOS CLAVE:
    - Elemento 1
    - Elemento 2
    """
    mock_llamar_triaje.return_value = ("mocked_prompt_triaje", mock_triaje_response_content)

    # Mock translation call to return None (simulating failure)
    mock_llamar_traduccion.return_value = None

    id_fragmento = SAMPLE_UUID
    # Use English text to match detected language "en"
    texto_original_en = SAMPLE_TEXT_EN

    # Expected cleaned text (basic cleaning for this test)
    # Assuming _limpiar_texto with the mock model does minimal changes or we focus on the fallback path
    expected_cleaned_text = texto_original_en.strip()

    resultado = ejecutar_fase_1(id_fragmento, texto_original_en)

    assert isinstance(resultado, ResultadoFase1Triaje)
    assert resultado.id_fragmento == id_fragmento
    assert resultado.es_relevante is True # Triaje was successful
    assert resultado.decision_triaje == "PROCESAR" # Triaje was successful

    # Check that texto_para_siguiente_fase is the original cleaned English text
    # This depends on how _limpiar_texto behaves with the mock.
    # For simplicity, we can mock _limpiar_texto too if needed, or trust it's minimal.
    # Let's assume _limpiar_texto returns something based on texto_original_en.
    # The key is that it's NOT a translated text.
    assert resultado.texto_para_siguiente_fase == expected_cleaned_text

    assert isinstance(resultado.metadatos_specificos_triaje, MetadatosFase1Triaje)
    assert resultado.metadatos_specificos_triaje.idioma_detectado_original == "en"
    assert resultado.metadatos_specificos_triaje.notas_adicionales is not None
    assert len(resultado.metadatos_specificos_triaje.notas_adicionales) > 0
    assert any("Traducción de 'en' falló" in nota for nota in resultado.metadatos_specificos_triaje.notas_adicionales)
    assert any("Se usará texto original" in nota for nota in resultado.metadatos_specificos_triaje.notas_adicionales)

# Example of a test for a successful run (optional, but good for baseline)
@patch('src.module_pipeline.src.pipeline.fase_1_triaje._cargar_modelo_spacy')
@patch('src.module_pipeline.src.pipeline.fase_1_triaje._get_groq_config')
@patch('src.module_pipeline.src.pipeline.fase_1_triaje._llamar_groq_api_triaje')
@patch('src.module_pipeline.src.pipeline.fase_1_triaje._llamar_groq_api_traduccion') # Mock translation too
def test_ejecutar_fase_1_successful_run_no_translation_needed(
    mock_llamar_traduccion,
    mock_llamar_triaje,
    mock_get_groq_config,
    mock_cargar_modelo_spacy
):
    mock_cargar_modelo_spacy.return_value = _get_mock_spacy_model(lang="es")
    mock_get_groq_config.return_value = {
        "api_key": "fake_key", "model_id": "test_model_success",
        "max_retries": 1, "max_wait_seconds": 1, "timeout": 5.0,
        "temperature": 0.1, "max_tokens": 100
    }

    mock_triaje_response_content = """
    EXCLUSIÓN: NO
    TIPO DE ARTÍCULO: NOTICIA DE ALTA RELEVANCIA
    Relevancia geográfica: [5] - España
    Relevancia temática: [5] - Política
    Densidad factual: [4]
    Complejidad relacional: [4]
    Valor informativo: [5]
    TOTAL: [23]/25
    DECISIÓN: PROCESAR
    JUSTIFICACIÓN: Artículo muy relevante sobre política española.
    ELEMENTOS CLAVE:
    - Elecciones
    - Nuevo gobierno
    """
    mock_llamar_triaje.return_value = ("mocked_prompt_success", mock_triaje_response_content)

    id_fragmento = SAMPLE_UUID
    texto_original = "Este es un artículo muy importante sobre la política en España."
    # Expected cleaned text (basic cleaning for this test)
    expected_cleaned_text = texto_original.strip()

    resultado = ejecutar_fase_1(id_fragmento, texto_original)

    assert isinstance(resultado, ResultadoFase1Triaje)
    assert resultado.es_relevante is True
    assert resultado.decision_triaje == "PROCESAR"
    assert resultado.justificacion_triaje == "Artículo muy relevante sobre política española."
    assert resultado.categoria_principal == "NOTICIA DE ALTA RELEVANCIA" # From mock
    assert "Elecciones" in resultado.palabras_clave_triaje
    assert resultado.puntuacion_triaje == 23.0
    assert resultado.texto_para_siguiente_fase == expected_cleaned_text # No translation needed

    assert isinstance(resultado.metadatos_specificos_triaje, MetadatosFase1Triaje)
    assert resultado.metadatos_specificos_triaje.idioma_detectado_original == "es"
    assert resultado.metadatos_specificos_triaje.notas_adicionales is None # No fallbacks occurred

    # Ensure translation was not called
    mock_llamar_traduccion.assert_not_called()
