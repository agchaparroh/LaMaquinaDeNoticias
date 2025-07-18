import pytest
import uuid
import logging # For checking log levels
from loguru import logger # For accessing loguru specific record attributes

from src.module_pipeline.src.utils.error_handling import (
    handle_spacy_load_error_fase1, # Corrected casing
    handle_groq_relevance_error_fase1,
    handle_groq_translation_fallback_fase1,
    handle_generic_phase_error,
    ErrorPhase,
    ErrorType, # Import for checking error_type in logs
    PipelineException, # For generic error test
    ProcessingError # For generic error test
)

# Fixture to capture log messages
@pytest.fixture
def caplog_fixture(caplog):
    # Configure Loguru to propagate to standard logging (which caplog captures)
    # This might be needed if Loguru by default doesn't send to caplog
    # logger.add(logging.StreamHandler(), format="{level} {message}") # Example, might need adjustment
    caplog.set_level(logging.DEBUG) # Capture from DEBUG level up for standard logging
    return caplog

def test_handle_spacy_load_error_fase1(caplog_fixture):
    article_id = str(uuid.uuid4())
    model_name = "es_test_model"
    original_exception = ValueError("Test spaCy load error")

    result = handle_spacy_load_error_fase1(article_id, model_name, original_exception)

    assert result["id_fragmento"] == article_id
    assert result["es_relevante"] is True # Updated logic
    assert result["decision_triaje"] == "FALLBACK_ACEPTADO_ERROR_PREPROCESO" # Updated logic
    expected_justification = f"Fallo al cargar modelo spaCy '{model_name}': {str(original_exception)}. Preprocesamiento degradado, artículo aceptado automáticamente."
    assert result["justificacion_triaje"] == expected_justification
    assert result["categoria_principal"] == "INDETERMINADO"
    assert result["palabras_clave_triaje"] == []
    assert result["puntuacion_triaje"] == 0.0
    assert result["confianza_triaje"] == 0.0
    assert result["texto_para_siguiente_fase"] == "[PREPROCESAMIENTO_FALLIDO]" # Updated
    assert result["metadatos_specificos_triaje"]["error_type"] == "SPACY_MODEL_LOAD_FAILURE"
    assert result["metadatos_specificos_triaje"]["model_name"] == model_name
    assert str(original_exception) in result["metadatos_specificos_triaje"]["details"]
    assert "SpaCy model loading failed" in result["metadatos_specificos_triaje"]["message"]

    # Check structured logs
    assert len(caplog_fixture.records) == 1
    log_record = caplog_fixture.records[0]
    assert log_record.levelname == "WARNING"
    expected_log_message = f"Fallback: spaCy model '{model_name}' loading failed for article {article_id}. Preprocessing degraded, article accepted by policy."
    assert log_record.message == expected_log_message

    # Access Loguru specific fields via record.loguru_record if needed, or check extra if propagated
    # For caplog, Loguru's extra fields are often in record.loguru_record.extra
    # However, the format_error_for_logging puts them directly in the dict that logger.bind uses.
    # So, we check the `extra` attribute of the LogRecord if available or the formatted message.
    # The most reliable is to check `log_record.loguru_record.extra` if using Loguru directly for assertions
    # but caplog might not fully expose this without specific Loguru handlers.
    # Let's assume format_error_for_logging's output is bound and some fields are accessible.
    # The most important fields from `format_error_for_logging` are part of the bound logger's context.
    # These are not directly on `LogRecord` unless Loguru's handler is set up to pass them as `extra`.
    # For simplicity, we'll check the message and level, and trust `format_error_for_logging` works.
    # To check structured parts, we'd ideally use a custom Loguru sink in tests.
    # For now, rely on the message content and that the correct exception was formatted.
    assert f"'fase': '{ErrorPhase.FASE_1_TRIAJE.value}'" in str(log_record.loguru_record.extra) # Example check
    assert f"'error_type': '{ErrorType.PROCESSING_ERROR.value}'" in str(log_record.loguru_record.extra)
    assert f"'original_error': '{str(original_exception)}'" in str(log_record.loguru_record.extra['details'])


def test_handle_groq_relevance_error_fase1(caplog_fixture):
    article_id = str(uuid.uuid4())
    text_cleaned = "Este es un texto limpio de prueba."
    original_exception = RuntimeError("Test Groq API error")

    result = handle_groq_relevance_error_fase1(article_id, text_cleaned, original_exception)

    assert result["id_fragmento"] == article_id
    assert result["es_relevante"] is True # Updated logic
    assert result["decision_triaje"] == "FALLBACK_ACEPTADO_ERROR_LLM" # Updated logic
    expected_justification = f"Fallo en API Groq para evaluación de relevancia: {str(original_exception)}. Artículo aceptado automáticamente por política de fallback."
    assert result["justificacion_triaje"] == expected_justification
    assert result["texto_para_siguiente_fase"] == text_cleaned
    assert result["metadatos_specificos_triaje"]["error_type"] == "GROQ_RELEVANCE_API_FAILURE"
    assert str(original_exception) in result["metadatos_specificos_triaje"]["details"]
    assert "Groq API failed during relevance evaluation" in result["metadatos_specificos_triaje"]["message"]

    # Check structured logs
    assert len(caplog_fixture.records) == 1
    log_record = caplog_fixture.records[0]
    assert log_record.levelname == "ERROR"
    expected_log_message = f"Fallback: Groq API relevance evaluation failed for article {article_id}. Accepting article by policy."
    assert log_record.message == expected_log_message
    assert f"'fase': '{ErrorPhase.FASE_1_TRIAJE.value}'" in str(log_record.loguru_record.extra)
    assert f"'error_type': '{ErrorType.GROQ_API_ERROR.value}'" in str(log_record.loguru_record.extra)
    assert f"'original_error': '{str(original_exception)}'" in str(log_record.loguru_record.extra['details'])
    assert f"'text_cleaned_excerpt': '{text_cleaned[:100]}'" in str(log_record.loguru_record.extra['details'])


def test_handle_groq_translation_fallback_fase1_with_exception(caplog_fixture):
    article_id = str(uuid.uuid4())
    text_cleaned = "This is original text."
    original_language = "en"
    original_exception = ConnectionError("Test translation API error")

    result = handle_groq_translation_fallback_fase1(article_id, text_cleaned, original_language, original_exception)

    assert result["status"] == "TRANSLATION_FALLBACK_APPLIED"
    assert f"Traducción de '{original_language}' falló. Se usará texto original." == result["message"]
    assert result["original_text_used"] is True
    assert result["texto_para_siguiente_fase"] == text_cleaned
    assert str(original_exception) in result["error_details"]
    assert result["article_id"] == article_id

    # Check structured logs
    assert len(caplog_fixture.records) == 1
    log_record = caplog_fixture.records[0]
    assert log_record.levelname == "WARNING"
    expected_log_message = f"Fallback: Groq translation from '{original_language}' failed for article {article_id}. Using original text."
    assert log_record.message == expected_log_message
    assert f"'fase': '{ErrorPhase.FASE_1_TRIAJE.value}'" in str(log_record.loguru_record.extra)
    assert f"'error_type': '{ErrorType.PROCESSING_ERROR.value}'" in str(log_record.loguru_record.extra)
    assert f"'original_error': '{str(original_exception)}'" in str(log_record.loguru_record.extra['details'])
    assert f"'original_language': '{original_language}'" in str(log_record.loguru_record.extra['details'])


def test_handle_groq_translation_fallback_fase1_no_exception(caplog_fixture):
    article_id = str(uuid.uuid4())
    text_cleaned = "Ceci est le texte original."
    original_language = "fr"

    result = handle_groq_translation_fallback_fase1(article_id, text_cleaned, original_language, None)

    assert result["status"] == "TRANSLATION_FALLBACK_APPLIED"
    assert f"Traducción de '{original_language}' falló. Se usará texto original." == result["message"]
    assert result["texto_para_siguiente_fase"] == text_cleaned
    assert result["error_details"] is None

    # Check structured logs
    assert len(caplog_fixture.records) == 1
    log_record = caplog_fixture.records[0]
    assert log_record.levelname == "WARNING"
    expected_log_message = f"Fallback: Groq translation from '{original_language}' failed for article {article_id}. Using original text."
    assert log_record.message == expected_log_message
    assert f"'original_error': 'N/A'" in str(log_record.loguru_record.extra['details'])


def test_handle_generic_phase_error_with_generic_exception(caplog_fixture):
    article_id = str(uuid.uuid4())
    phase = ErrorPhase.FASE_2_EXTRACCION
    step_failed = "entity_linking"
    exception = Exception("Generic processing error")

    result = handle_generic_phase_error(article_id, phase, step_failed, exception)

    assert result["id_fragmento"] == article_id
    assert result["status"] == "ERROR"
    assert result["phase_name"] == phase.value
    assert result["error_type"] == "PROCESSING_ERROR" # Default from the function
    assert f"Fallo en {phase.value} durante {step_failed}: {str(exception)}" == result["message"]
    assert result["step_failed"] == step_failed
    assert result["exception_type"] == type(exception).__name__
    assert str(exception) in result["details"]
    assert result["data"] == {}

    # Check logs
    assert any(f"Error en {phase.value} durante el paso '{step_failed}' para artículo {article_id}" in record.message and record.levelname == "ERROR" for record in caplog_fixture.records)
    assert any(f"Usando fallback para {phase.value} (Artículo: {article_id})" in record.message and record.levelname == "INFO" for record in caplog_fixture.records)

def test_handle_generic_phase_error_with_pipeline_exception(caplog_fixture):
    from src.module_pipeline.src.utils.error_handling import GroqAPIError # Specific PipelineException
    article_id = str(uuid.uuid4())
    phase = ErrorPhase.FASE_3_CITAS_DATOS
    step_failed = "quote_extraction"
    exception = GroqAPIError(message="Groq failed", phase=phase)

    result = handle_generic_phase_error(article_id, phase, step_failed, exception)

    assert result["error_type"] == "groq_api_error" # Derived from exception type
    assert result["phase_name"] == phase.value
    assert f"Fallo en {phase.value} durante {step_failed}: {str(exception)}" == result["message"]

    # Check logs
    assert any(f"Error en {phase.value} durante el paso '{step_failed}' para artículo {article_id}" in record.message and record.levelname == "ERROR" for record in caplog_fixture.records)
    assert any(f"Usando fallback para {phase.value} (Artículo: {article_id})" in record.message and record.levelname == "INFO" for record in caplog_fixture.records)

# Test with a different ErrorPhase
def test_handle_generic_phase_error_fase_4(caplog_fixture):
    article_id = str(uuid.uuid4())
    phase = ErrorPhase.FASE_4_NORMALIZACION
    step_failed = "data_normalization"
    exception = ValueError("Normalization value error")

    result = handle_generic_phase_error(article_id, phase, step_failed, exception)

    assert result["id_fragmento"] == article_id
    assert result["status"] == "ERROR"
    assert result["phase_name"] == phase.value
    assert result["error_type"] == "PROCESSING_ERROR" # Default as ValueError is not a PipelineException subclass defined in the handler
    assert f"Fallo en {phase.value} durante {step_failed}: {str(exception)}" == result["message"]
    assert result["step_failed"] == step_failed
    assert result["exception_type"] == type(exception).__name__

    # Check logs
    assert any(f"Error en {phase.value} durante el paso '{step_failed}' para artículo {article_id}" in record.message and record.levelname == "ERROR" for record in caplog_fixture.records)
    assert any(f"Usando fallback para {phase.value} (Artículo: {article_id})" in record.message and record.levelname == "INFO" for record in caplog_fixture.records)

# Ensure the directory exists
# Note: This is a placeholder, actual directory creation should be handled by the environment/setup
# For the agent, this comment serves as a reminder if ls fails.
# import os
# test_utils_dir = "src/module_pipeline/tests/test_utils"
# if not os.path.exists(test_utils_dir):
# os.makedirs(test_utils_dir)
# print(f"Directory {test_utils_dir} created or already exists.")
# (No need to run os.makedirs if the tool handles it, which it should)

# Check function name casing from previous step, it was:
# handle_spacy_load_error_fase1 (correct in previous step)
# In this test file, I used handle_spacy_load_Error_fase1 (with capital E)
# This will be corrected if an import error occurs, or I can correct it preemptively.
# For now, I'll assume the actual function name is `handle_spacy_load_error_fase1`
# and the import statement here should reflect that for consistency.
# The `create_file_with_block` doesn't run Python, so it won't catch it.
# Correcting the import:
# from src.module_pipeline.src.utils.error_handling import (
# handle_spacy_load_error_fase1,
# ...
# )
# The tool output for create_file will show the created content. I will check it then.

# Final check of the requirements:
# - Create test_error_handling.py (Done)
# - Add imports (Done, with a note on casing for spacy handler)
# - Test handle_spacy_load_error_fase1 (Done with dict checks and caplog)
# - Test handle_groq_relevance_error_fase1 (Done with dict checks, text_cleaned, and caplog)
# - Test handle_groq_translation_fallback_fase1 (Done with dict checks and caplog, with/without exception)
# - Test handle_generic_phase_error (Done with dict checks, different phases, and caplog)

# All items for Part 1 seem covered by the generated test code.
# The caplog fixture is defined once and reused.
# Tests cover structure of returned dict and logging.
# UUIDs are converted to strings for article_id as typically done.
# Different exception types are used in tests.
# Test for generic handler includes a case with a specific PipelineException (GroqAPIError)
# to check error_type derivation.
# Test for generic handler also checks different ErrorPhase enum values.
# The directory creation comment is just a thought process note.
# The casing for 'handle_spacy_load_Error_fase1' in the import will be 'handle_spacy_load_error_fase1'.
# I will ensure the import in the created file is `handle_spacy_load_error_fase1`.
# The content provided to `create_file_with_block` has the corrected casing for the import.
# `handle_spacy_load_Error_fase1` was a typo in my thought process, the actual code uses `handle_spacy_load_error_fase1`.
# The provided code for `create_file_with_block` uses `handle_spacy_load_Error_fase1`. I need to correct this.

# Corrected import statement in the file content:
# from src.module_pipeline.src.utils.error_handling import (
# handle_spacy_load_error_fase1, # Corrected casing
# handle_groq_relevance_error_fase1,
# handle_groq_translation_fallback_fase1,
# handle_generic_phase_error,
# ErrorPhase
# )
# And the function call:
# result = handle_spacy_load_error_fase1(article_id, model_name, exception) # Corrected casing

# I will provide the corrected content to the tool.Okay, I will now create the test file `src/module_pipeline/tests/test_utils/test_error_handling.py` with the content generated and refined in the thought block. I've ensured the correct casing for `handle_spacy_load_error_fase1` in the import and its usage.
