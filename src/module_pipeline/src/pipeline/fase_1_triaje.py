from typing import Optional, List, Dict, Any
from uuid import UUID
import re
import os
import time
import json # Para posible parseo si Groq devuelve JSON string, aunque el prompt pide texto.
from pathlib import Path

# Importar el modelo de resultado de la fase 1 desde el módulo de modelos
from ..models.procesamiento import ResultadoFase1Triaje, MetadatosFase1Triaje

# Importar manejadores de errores y tipos necesarios
from ..utils.error_handling import (
    handle_spacy_load_error_fase1,
    handle_groq_relevance_error_fase1,
    handle_groq_translation_fallback_fase1,
    ErrorPhase, # Aunque no se usa directamente en Fase 1 handlers, buena práctica tenerla si se expande
    retry_groq_api,
    GroqAPIError
)

# Importaciones para spaCy y Groq
try:
    import spacy
    from spacy.language import Language
    # from spacy.tokens import Doc # No se usa directamente Doc como tipo aquí
except ImportError:
    spacy = None
    Language = None # Para que el type hint no falle si spacy no está

try:
    from groq import Groq
except ImportError:
    Groq = None

from loguru import logger

# --- Modelos de spaCy Cargados (Singleton simple) ---
_NLP_MODELS_CACHE: Dict[str, Optional[Language]] = {}

class ErrorFase1(Exception):
    """Excepción base para errores específicos de la Fase 1."""
    pass

def _cargar_modelo_spacy(modelo: str = "es_core_news_sm") -> Optional[Language]:
    """Carga un modelo de spaCy. Cachea el modelo cargado."""
    if not spacy:
        logger.warning("spaCy no está instalado. No se puede cargar ningún modelo.") # Changed to warning
        return None

    if modelo not in _NLP_MODELS_CACHE:
        try:
            logger.info(f"Cargando modelo spaCy: {modelo}")
            _NLP_MODELS_CACHE[modelo] = spacy.load(modelo)
            logger.info(f"Modelo spaCy '{modelo}' cargado exitosamente.")
        except OSError:
            logger.warning(f"No se pudo cargar el modelo spaCy '{modelo}'. " # Changed to warning
                         f"Asegúrate de que está descargado (ej: python -m spacy download {modelo})")
            _NLP_MODELS_CACHE[modelo] = None # Marcar como no cargado para no reintentar innecesariamente
        except Exception as e:
            logger.warning(f"Error inesperado al cargar el modelo spaCy '{modelo}': {e}") # Changed to warning
            _NLP_MODELS_CACHE[modelo] = None
    
    if _NLP_MODELS_CACHE.get(modelo) is None and modelo != "es_core_news_sm": # Evitar recursión infinita si el default falla
        logger.warning(f"Fallback: Intentando cargar modelo por defecto 'es_core_news_sm' en lugar de '{modelo}'.")
        return _cargar_modelo_spacy("es_core_news_sm")
        
    return _NLP_MODELS_CACHE.get(modelo)

def _limpiar_texto(texto_original: str, nlp_model: Optional[Language]) -> str:
    """Limpia el texto utilizando spaCy para tokenización y reglas heurísticas."""
    if not texto_original or not texto_original.strip():
        logger.debug("Texto original vacío o solo espacios, devolviendo cadena vacía.")
        return ""

    if not nlp_model:
        logger.warning("Modelo spaCy no disponible para limpieza. Devolviendo texto original con limpieza básica.")
        # Limpieza muy básica si spaCy no está disponible
        texto_limpio = re.sub(r'\s+', ' ', texto_original).strip()
        return texto_limpio

    logger.debug(f"Limpiando texto con modelo: {nlp_model.meta.get('name', 'desconocido')}")
    doc = nlp_model(texto_original)
    
    tokens_limpios = []
    for token in doc:
        if token.is_space:
            # Permitir un solo espacio si el token anterior no era un espacio.
            # Esto ayuda a consolidar múltiples espacios y mantener saltos de línea (que spaCy trata como is_space=True)
            if tokens_limpios and tokens_limpios[-1] != " ": 
                tokens_limpios.append(" ")
        elif token.is_punct and len(token.text) > 1 and all(c == token.text[0] for c in token.text):
            # Normaliza secuencias de la misma puntuación (ej: "!!!!" -> "!")
            # Solo añade si el anterior no es el mismo caracter de puntuación
            if not tokens_limpios or tokens_limpios[-1] != token.text[0]:
                tokens_limpios.append(token.text[0])
        else:
            tokens_limpios.append(token.text) # Usar token.text para mantener el case original

    texto_semi_limpio = "".join(tokens_limpios).strip()
    
    # Consolidar múltiples espacios (incluidos los resultantes de token.is_space) a uno solo.
    # Preservar saltos de línea simples y dobles, pero normalizar otros espacios alrededor de ellos.
    texto_limpio = re.sub(r'[ \t\r\f\v]+', ' ', texto_semi_limpio) # Reemplaza espacios horizontales múltiples por uno
    texto_limpio = texto_limpio.replace(' \n', '\n').replace('\n ', '\n') # Elimina espacios alrededor de \n
    texto_limpio = re.sub(r'(\n){2,}', '\n\n', texto_limpio) # Normaliza múltiples \n a un máximo de dos (párrafo)
    
    logger.trace(f"Texto original: '{texto_original[:100]}...' -> Texto limpio: '{texto_limpio[:100]}...'")
    return texto_limpio.strip()

def _detectar_idioma(texto_para_detectar: str, nlp_model: Optional[Language]) -> str:
    """
    Identifica el idioma del texto utilizando el modelo spaCy cargado.
    NOTA: Esto devolverá el idioma para el que el modelo fue entrenado (ej. 'es' para 'es_core_news_sm').
    Para una detección de idioma robusta entre múltiples idiomas desconocidos,
    se recomienda una biblioteca especializada como spacy-langdetect o similar.
    """
    if not nlp_model:
        logger.warning("Modelo spaCy no disponible para detección de idioma. Devolviendo 'und'.")
        return "und" # Indeterminado

    if not texto_para_detectar or not texto_para_detectar.strip():
        logger.debug("Texto para detección de idioma vacío, devolviendo 'und'.")
        return "und"

    # La detección de idioma con un modelo mono-lingüe de spaCy simplemente devuelve el idioma del modelo.
    lang_code = nlp_model.lang
    logger.debug(f"Idioma identificado por el modelo '{nlp_model.meta.get('name', 'desconocido')}': {lang_code}")
    logger.warning(f"Recordatorio: La detección de idioma con el modelo base '{nlp_model.meta.get('name', 'desconocido')}' "
                   f"devolverá '{lang_code}'. Para una detección multilingüe real, considere un detector de idioma dedicado.")
    return lang_code

def ejecutar_fase_1(
    id_fragmento_original: UUID,
    texto_original_fragmento: str,
    modelo_spacy_nombre: str = "es_core_news_sm" # Permitir especificar modelo
) -> ResultadoFase1Triaje:
    """
    Ejecuta la Fase 1: Preprocesamiento y Triaje.
    Limpia el texto, detecta idioma, traduce si es necesario y
    evalúa la relevancia inicial.

    Args:
        id_fragmento_original: El UUID del fragmento original que se está procesando.
        texto_original_fragmento: El contenido textual original del fragmento.
        modelo_spacy_nombre: Nombre del modelo de spaCy a utilizar.

    Returns:
        Un objeto ResultadoFase1Triaje con los resultados del procesamiento.

    Raises:
        NotImplementedError: Si la función aún no está completamente implementada.
        ErrorFase1: Para errores específicos durante el procesamiento de la fase.
    """
    logger.info(f"Iniciando Fase 1: Triaje para fragmento ID: {id_fragmento_original}")
    notas_procesamiento: List[str] = []

    try:
        nlp_model = _cargar_modelo_spacy(modelo_spacy_nombre)
        if not nlp_model: # Si el modelo (incluido el fallback) no se pudo cargar
            # Esta condición es manejada por la excepción OSError o genérica en _cargar_modelo_spacy
            # que debería ser capturada abajo si _cargar_modelo_spacy devuelve None o lanza error.
            # Sin embargo, si _cargar_modelo_spacy devuelve None sin excepción, lo manejamos aquí explícitamente.
            logger.warning(f"Fallo crítico: _cargar_modelo_spacy devolvió None para el modelo '{modelo_spacy_nombre}' para el fragmento {id_fragmento_original}.") # Changed to warning
            # Simular una excepción para que el handler la capture de forma uniforme
            raise RuntimeError(f"Modelo spaCy '{modelo_spacy_nombre}' o fallback no disponible (devuelto como None).")

        texto_limpio = _limpiar_texto(texto_original_fragmento, nlp_model)
        idioma_detectado = _detectar_idioma(texto_limpio, nlp_model) # This is 'nlp_model.lang' or 'und'

        # Initialize metadatos_fase1 here to allow adding notes for language detection
        # notas_procesamiento (list) will accumulate all notes.
        metadatos_fase1 = MetadatosFase1Triaje(
            nombre_modelo_triaje=modelo_spacy_nombre,
            texto_limpio_utilizado=texto_limpio, # Initially, text_limpio from spaCy
            idioma_detectado_original=idioma_detectado,
            notas_adicionales=[] # Start with an empty list for metadatos, will be populated by notas_procesamiento at the end or in fallbacks
        )

        if idioma_detectado == "und":
            logger.info(f"Idioma detectado como 'und' para fragmento {id_fragmento_original}. Asumiendo 'es' por defecto según documentación.")
            idioma_detectado = "es"
            notas_procesamiento.append("Idioma asumido como 'es' por fallo en detección.")

        logger.debug(f"Fragmento {id_fragmento_original}: Texto limpio generado, Idioma para LLM: {idioma_detectado}")

    except Exception as e_spacy:
        logger.warning(f"Excepción durante carga de spaCy o preprocesamiento inicial para {id_fragmento_original}: {e_spacy}")
        fallback_dict = handle_spacy_load_error_fase1(
            article_id=str(id_fragmento_original),
            model_name=modelo_spacy_nombre,
            exception=e_spacy
        )

        current_notes = list(notas_procesamiento) # Preserve any prior notes (e.g. from language detection if it ran partially)
        if fallback_dict.get("metadatos_specificos_triaje", {}).get("message"):
             current_notes.append(fallback_dict["metadatos_specificos_triaje"]["message"])

        # For SpaCy failure, texto_limpio_utilizado is the placeholder from handler, idioma original is "und"
        metadatos_error = MetadatosFase1Triaje(
            nombre_modelo_triaje=modelo_spacy_nombre,
            texto_limpio_utilizado=fallback_dict.get("texto_para_siguiente_fase", "[PREPROCESAMIENTO_FALLIDO]"),
            idioma_detectado_original="und", # SpaCy failed, so language detection likely failed or is unreliable
            notas_adicionales=current_notes if current_notes else None
        )

        resultado = ResultadoFase1Triaje(
            id_fragmento=id_fragmento_original,
            es_relevante=fallback_dict["es_relevante"], # True by new policy
            decision_triaje=fallback_dict["decision_triaje"], # "FALLBACK_ACEPTADO_ERROR_PREPROCESO"
            justificacion_triaje=fallback_dict["justificacion_triaje"],
            categoria_principal=fallback_dict["categoria_principal"],
            palabras_clave_triaje=fallback_dict["palabras_clave_triaje"],
            puntuacion_triaje=fallback_dict["puntuacion_triaje"],
            confianza_triaje=fallback_dict["confianza_triaje"],
            texto_para_siguiente_fase=texto_original_fragmento, # Use original text as per requirement
            metadatos_specificos_triaje=metadatos_error
        )
        resultado.touch()
        return resultado

    # La lógica de integración con Groq (15.3), traducción (15.4) 
    # y la creación final del objeto ResultadoFase1Triaje (15.5) siguen pendientes.

    # Ejemplo de cómo se usarían los valores (se moverá a 15.5):
    # resultado_parcial = ResultadoFase1Triaje(
    #     id_fragmento=id_fragmento_original,
    #     texto_limpio_para_llm=texto_limpio,
    #     idioma_detectado=idioma_detectado,
    #     # Los siguientes campos se llenarán en subtareas posteriores
    #     relevancia_evaluada="INDETERMINADO", # Placeholder
    #     puntuacion_relevancia=None, # Placeholder
    #     texto_traducido_para_llm=None, # Placeholder
    #     prompt_triaje_usado=None, # Placeholder
    # )
    # resultado_parcial.touch()
    # logger.info(f"Fase 1 (parcial) completada para fragmento ID: {id_fragmento_original}")
    # return resultado_parcial

    # --- Subtarea 15.3: Integración con Groq API para Evaluación de Relevancia ---
    groq_config = _get_groq_config()
    # Pass article_id to config for logging inside Groq calls
    groq_config_with_id = {**groq_config, "article_id": str(id_fragmento_original)}

    if not groq_config.get("api_key"):
        logger.warning(f"No se encontró GROQ_API_KEY. Aplicando fallback para {id_fragmento_original}.")

        api_key_exception = RuntimeError("GROQ_API_KEY no configurada. Artículo aceptado por política de fallback.")
        fallback_dict = handle_groq_relevance_error_fase1(
            article_id=str(id_fragmento_original),
            text_cleaned=texto_limpio, # spaCy preproc was successful, so texto_limpio is the one to use/pass
            exception=api_key_exception
        )

        if fallback_dict.get("metadatos_specificos_triaje", {}).get("message"):
            notas_procesamiento.append(fallback_dict["metadatos_specificos_triaje"]["message"])

        metadatos_fase1.nombre_modelo_triaje = groq_config.get("model_id", "desconocido_por_no_api_key")
        metadatos_fase1.notas_adicionales = notas_procesamiento if notas_procesamiento else None

        resultado = ResultadoFase1Triaje(
            id_fragmento=id_fragmento_original,
            es_relevante=fallback_dict["es_relevante"],
            decision_triaje=fallback_dict["decision_triaje"],
            justificacion_triaje=fallback_dict["justificacion_triaje"],
            categoria_principal=fallback_dict["categoria_principal"],
            palabras_clave_triaje=fallback_dict["palabras_clave_triaje"],
            puntuacion_triaje=fallback_dict["puntuacion_triaje"],
            confianza_triaje=fallback_dict["confianza_triaje"],
            texto_para_siguiente_fase=fallback_dict["texto_para_siguiente_fase"], # This is texto_limpio via handler
            metadatos_specificos_triaje=metadatos_fase1
        )
        resultado.touch()
        return resultado

    prompt_formateado = None
    respuesta_llm_cruda = None
    evaluacion_triaje = {}

    try:
        prompt_formateado, respuesta_llm_cruda = _llamar_groq_api_triaje(
            config=groq_config_with_id, # Use config with article_id
            texto_contenido=texto_limpio,
            titulo="No disponible (fragmento)",
            medio="No disponible (fragmento)",
            pais="No disponible (fragmento)",
            fecha_pub="No disponible (fragmento)"
        )
        logger.trace(f"Respuesta LLM (cruda) para triaje de {id_fragmento_original}:\n{respuesta_llm_cruda}")
        evaluacion_triaje = _parsear_respuesta_triaje(respuesta_llm_cruda)

        if evaluacion_triaje.get("decision") == "ERROR_TRIAGE": # Check specific error decision from parser
            logger.warning(f"Parseo de respuesta LLM resultó en error para {id_fragmento_original}. Aplicando fallback. Justificación: {evaluacion_triaje.get('justificacion')}")
            raise GroqAPIError( # Raise to consolidate fallback logic
                message=f"Error al parsear respuesta LLM: {evaluacion_triaje.get('justificacion', 'Sin justificación específica del parser.')}",
                phase=ErrorPhase.FASE_1_TRIAJE,
                article_id=str(id_fragmento_original)
            )

    except GroqAPIError as e_groq_relevance:
        logger.error(f"GroqAPIError durante evaluación de relevancia para {id_fragmento_original}: {e_groq_relevance}")
        fallback_dict = handle_groq_relevance_error_fase1(
            article_id=str(id_fragmento_original),
            text_cleaned=texto_limpio, # texto_limpio is available and is what was used for the failed call
            exception=e_groq_relevance
        )
        metadatos_fase1.nombre_modelo_triaje = groq_config.get("model_id", "desconocido_por_error_api")
        if fallback_dict.get("metadatos_specificos_triaje", {}).get("message"):
            notas_procesamiento.append(fallback_dict["metadatos_specificos_triaje"]["message"])
        metadatos_fase1.notas_adicionales = notas_procesamiento if notas_procesamiento else None

        resultado = ResultadoFase1Triaje(
            id_fragmento=id_fragmento_original,
            es_relevante=fallback_dict["es_relevante"],
            decision_triaje=fallback_dict["decision_triaje"],
            justificacion_triaje=fallback_dict["justificacion_triaje"],
            categoria_principal=fallback_dict["categoria_principal"],
            palabras_clave_triaje=fallback_dict["palabras_clave_triaje"],
            puntuacion_triaje=fallback_dict["puntuacion_triaje"],
            confianza_triaje=fallback_dict["confianza_triaje"],
            texto_para_siguiente_fase=fallback_dict["texto_para_siguiente_fase"], # This is texto_limpio via handler
            metadatos_specificos_triaje=metadatos_fase1
        )
        resultado.touch()
        return resultado
    logger.debug(f"Evaluación de triaje parseada para {id_fragmento_original}: {evaluacion_triaje}")

    # --- Subtarea 15.4: Implementación de Lógica de Traducción ---
    texto_para_siguiente_fase = texto_limpio # Default, use cleaned (original language) text

    if idioma_detectado and idioma_detectado.lower() != "es" and evaluacion_triaje.get("decision") != "DESCARTAR":
        if texto_limpio and texto_limpio.strip():
            logger.info(f"Traduciendo texto de '{idioma_detectado}' a 'es' para fragmento {id_fragmento_original}.")
            try:
                texto_traducido_llm = _llamar_groq_api_traduccion( # Use _llamar_groq_api_traduccion
                    config=groq_config_with_id, # Use config with article_id
                    texto_a_traducir=texto_limpio,
                    idioma_origen=idioma_detectado
                )
                # _llamar_groq_api_traduccion now raises GroqAPIError if translation is empty/failed
                logger.debug(f"Texto traducido para {id_fragmento_original}: '{texto_traducido_llm[:100]}...'" )
                texto_para_siguiente_fase = texto_traducido_llm # Use translated text
            except GroqAPIError as e_trans_groq: # Catch specific GroqAPIError
                logger.warning(f"GroqAPIError durante traducción para {id_fragmento_original}: {e_trans_groq}. Se usará texto original.")
                fallback_trans_dict = handle_groq_translation_fallback_fase1(
                    article_id=str(id_fragmento_original),
                    text_cleaned=texto_limpio, # This is the original text before failed translation attempt
                    original_language=idioma_detectado,
                    exception=e_trans_groq
                )
                if fallback_trans_dict.get("message"):
                    notas_procesamiento.append(fallback_trans_dict["message"])
                # texto_para_siguiente_fase remains texto_limpio (original pre-translation text)
        else:
            logger.debug(f"No se requiere traducción para {id_fragmento_original} (texto limpio vacío)." )
    else:
        logger.debug(f"No se requiere traducción para {id_fragmento_original} (idioma: {idioma_detectado}, decisión triaje: {evaluacion_triaje.get('decision')}).")

    # --- Subtarea 15.5: Ensamblaje final del objeto ResultadoFase1Triaje ---
    metadatos_fase1.nombre_modelo_triaje = groq_config.get("model_id", "llama3-8b-8192") # Default if not set by error handling
    metadatos_fase1.notas_adicionales = notas_procesamiento if notas_procesamiento else None

    puntuacion_triaje_val = evaluacion_triaje.get("total_puntuacion")
    if puntuacion_triaje_val is not None:
        try:
            puntuacion_triaje_val = float(puntuacion_triaje_val)
        except (ValueError, TypeError):
            logger.warning(f"No se pudo convertir puntuacion_triaje '{puntuacion_triaje_val}' a float. Se usará None.")
            puntuacion_triaje_val = None


    resultado_final = ResultadoFase1Triaje(
        id_fragmento=id_fragmento_original,
        es_relevante=(evaluacion_triaje.get("decision", "ERROR_TRIAGE") == "PROCESAR"),
        decision_triaje=evaluacion_triaje.get("decision", "ERROR_TRIAGE"),
        justificacion_triaje=evaluacion_triaje.get("justificacion"),
        categoria_principal=evaluacion_triaje.get("tipo_articulo"),
        palabras_clave_triaje=evaluacion_triaje.get("elementos_clave", []),
        puntuacion_triaje=puntuacion_triaje_val,
        confianza_triaje=None,  # Podríamos mapear esto desde algún score si es necesario
        texto_para_siguiente_fase=texto_para_siguiente_fase,
        metadatos_specificos_triaje=metadatos_fase1
    )

    resultado_final.touch() # Actualiza fecha_modificacion y fecha_creacion si es la primera vez

    logger.info(f"Fase 1: Triaje completada para fragmento ID: {id_fragmento_original}. "
                f"Decisión: {resultado_final.es_relevante}, Score: {evaluacion_triaje.get('total_puntuacion')}")
    
    return resultado_final

# --- Funciones para Subtarea 15.3: Integración Groq API ---

_PROMPT_TRIAGE_PATH = Path(__file__).resolve().parent.parent / "prompts" / "Prompt_1_filtrado.md"
_PROMPT_TRIAGE_TEMPLATE: Optional[str] = None

def _load_prompt_template() -> str:
    global _PROMPT_TRIAGE_TEMPLATE
    if _PROMPT_TRIAGE_TEMPLATE is None:
        try:
            with open(_PROMPT_TRIAGE_PATH, "r", encoding="utf-8") as f:
                _PROMPT_TRIAGE_TEMPLATE = f.read()
            logger.info(f"Plantilla de prompt de triaje cargada desde: {_PROMPT_TRIAGE_PATH}")
        except FileNotFoundError:
            logger.error(f"No se encontró el archivo de prompt de triaje en: {_PROMPT_TRIAGE_PATH}")
            raise ErrorFase1(f"Archivo de prompt de triaje no encontrado: {_PROMPT_TRIAGE_PATH}")
        except Exception as e:
            logger.error(f"Error al cargar el prompt de triaje: {e}")
            raise ErrorFase1(f"Error cargando prompt de triaje: {e}")
    return _PROMPT_TRIAGE_TEMPLATE

def _get_groq_config() -> Dict[str, Any]:
    """Carga la configuración para la API de Groq desde variables de entorno."""
    return {
        "api_key": os.getenv("GROQ_API_KEY"),
        "model_id": os.getenv("GROQ_MODEL_ID", "mixtral-8x7b-32768"), # Un default razonable
        "timeout": float(os.getenv("GROQ_API_TIMEOUT", "30.0")),
        "temperature": float(os.getenv("GROQ_API_TEMPERATURE", "0.1")),
        "max_tokens": int(os.getenv("GROQ_API_MAX_TOKENS", "1000")), # Ajustado para triaje
        "max_retries": int(os.getenv("GROQ_MAX_RETRIES", "3")),
        "max_wait_seconds": int(os.getenv("GROQ_MAX_WAIT_SECONDS", "60")),
    }

def _llamar_groq_api_triaje(
    config: Dict[str, Any],
    texto_contenido: str,
    titulo: str = "No disponible",
    medio: str = "No disponible",
    pais: str = "No disponible",
    fecha_pub: str = "No disponible"
) -> tuple[str, str]:
    """
    Llama a la API de Groq para evaluación de triaje.
    Retries son manejados por @retry_groq_api.
    Levanta GroqAPIError en caso de fallo persistente o configuración incorrecta.
    """
    article_id_log = config.get("article_id", "N/A") # For logging purposes
    if not Groq:
        logger.error(f"SDK de Groq no instalado. Artículo: {article_id_log}")
        raise GroqAPIError("SDK de Groq no instalado.", phase=ErrorPhase.FASE_1_TRIAJE, article_id=config.get("article_id"))
    if not config.get("api_key"):
        logger.error(f"GROQ_API_KEY no configurada. Artículo: {article_id_log}")
        raise GroqAPIError("GROQ_API_KEY no configurada.", phase=ErrorPhase.FASE_1_TRIAJE, article_id=config.get("article_id"))

    try:
        prompt_template = _load_prompt_template()
    except ErrorFase1 as e_prompt:
        logger.error(f"Fallo al cargar plantilla de prompt para triaje. Artículo: {article_id_log}. Error: {e_prompt}")
        raise GroqAPIError(f"Fallo al cargar plantilla de prompt para triaje: {e_prompt}", phase=ErrorPhase.FASE_1_TRIAJE, article_id=config.get("article_id")) from e_prompt

    prompt_formateado = prompt_template.replace("{{TITULO}}", titulo)\
                                     .replace("{{MEDIO}}", medio)\
                                     .replace("{{PAIS}}", pais)\
                                     .replace("{{FECHA_PUB}}", fecha_pub)\
                                     .replace("{{CONTENIDO}}", texto_contenido)
    
    client = Groq(api_key=config["api_key"], timeout=config["timeout"])
    
    logger.info(f"Enviando solicitud a Groq API para triaje (modelo: {config['model_id']}). Artículo: {article_id_log}")
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt_formateado,
            }
        ],
        model=config["model_id"],
        temperature=config["temperature"],
        max_tokens=config["max_tokens"],
    )
    respuesta_contenido = chat_completion.choices[0].message.content
    if not respuesta_contenido or not respuesta_contenido.strip():
        logger.warning(f"Groq API para triaje devolvió una respuesta vacía. Artículo: {article_id_log}")
        raise GroqAPIError("Respuesta vacía de Groq API para triaje.", phase=ErrorPhase.FASE_1_TRIAJE, article_id=config.get("article_id"))
    logger.info(f"Respuesta recibida de Groq API para triaje. Artículo: {article_id_log}")
    return prompt_formateado, respuesta_contenido

@retry_groq_api()
def _llamar_groq_api_triaje( # Add decorator here
    config: Dict[str, Any],
    texto_contenido: str,
    titulo: str = "No disponible",
    medio: str = "No disponible",
    pais: str = "No disponible",
    fecha_pub: str = "No disponible"
) -> tuple[str, str]:
    """
    Llama a la API de Groq para evaluación de triaje.
    Retries son manejados por @retry_groq_api.
    Levanta GroqAPIError en caso de fallo persistente o configuración incorrecta.
    """
    article_id_log = config.get("article_id", "N/A") # For logging purposes
    if not Groq:
        logger.error(f"SDK de Groq no instalado. Artículo: {article_id_log}")
        raise GroqAPIError("SDK de Groq no instalado.", phase=ErrorPhase.FASE_1_TRIAJE, article_id=config.get("article_id"))
    if not config.get("api_key"):
        logger.error(f"GROQ_API_KEY no configurada. Artículo: {article_id_log}")
        raise GroqAPIError("GROQ_API_KEY no configurada.", phase=ErrorPhase.FASE_1_TRIAJE, article_id=config.get("article_id"))

    try:
        prompt_template = _load_prompt_template()
    except ErrorFase1 as e_prompt:
        logger.error(f"Fallo al cargar plantilla de prompt para triaje. Artículo: {article_id_log}. Error: {e_prompt}")
        raise GroqAPIError(f"Fallo al cargar plantilla de prompt para triaje: {e_prompt}", phase=ErrorPhase.FASE_1_TRIAJE, article_id=config.get("article_id")) from e_prompt

    prompt_formateado = prompt_template.replace("{{TITULO}}", titulo)\
                                     .replace("{{MEDIO}}", medio)\
                                     .replace("{{PAIS}}", pais)\
                                     .replace("{{FECHA_PUB}}", fecha_pub)\
                                     .replace("{{CONTENIDO}}", texto_contenido)

    client = Groq(api_key=config["api_key"], timeout=config["timeout"])

    logger.info(f"Enviando solicitud a Groq API para triaje (modelo: {config['model_id']}). Artículo: {article_id_log}")
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt_formateado,
            }
        ],
        model=config["model_id"],
        temperature=config["temperature"],
        max_tokens=config["max_tokens"],
    )
    respuesta_contenido = chat_completion.choices[0].message.content
    if not respuesta_contenido or not respuesta_contenido.strip():
        logger.warning(f"Groq API para triaje devolvió una respuesta vacía. Artículo: {article_id_log}")
        raise GroqAPIError("Respuesta vacía de Groq API para triaje.", phase=ErrorPhase.FASE_1_TRIAJE, article_id=config.get("article_id"))
    logger.info(f"Respuesta recibida de Groq API para triaje. Artículo: {article_id_log}")
    return prompt_formateado, respuesta_contenido

def _parsear_respuesta_triaje(respuesta_llm: str) -> Dict[str, Any]:
    """
    Parsea la respuesta textual del LLM para el triaje.
    Si la respuesta es un JSON string, intenta parsearlo.
    """
    parsed_data = {
        "exclusion": None, "exclusion_categoria": None,
        "tipo_articulo": "INDETERMINADO", # Default
        "relevancia_geografica_score": None, "relevancia_geografica_pais": None,
        "relevancia_tematica_score": None, "relevancia_tematica_tema": None,
        "densidad_factual_score": None,
        "complejidad_relacional_score": None,
        "valor_informativo_score": None,
        "total_puntuacion": None,
        "decision": "ERROR_TRIAGE", # Default
        "justificacion": "Error al parsear respuesta LLM.", # Default
        "elementos_clave": []
    }

    if not respuesta_llm or not respuesta_llm.strip():
        logger.warning("Respuesta LLM para triaje está vacía o solo contiene espacios.")
        # parsed_data already reflects error state
        return parsed_data

    # Intentar parsear como JSON primero
    try:
        respuesta_llm_stripped = respuesta_llm.strip()
        json_content = respuesta_llm_stripped

        if respuesta_llm_stripped.startswith("```json"):
            json_content = respuesta_llm_stripped[7:-3].strip()
        elif respuesta_llm_stripped.startswith("```"): # Handle cases like ```\n{\n...}\n```
            json_content = respuesta_llm_stripped[3:-3].strip()

        data = json.loads(json_content)
        logger.debug("Respuesta LLM para triaje parseada como JSON.")

        # Mapear campos del JSON a parsed_data
        parsed_data["decision"] = data.get("decision", "ERROR_TRIAGE").upper()
        parsed_data["justificacion"] = data.get("justificacion", "Sin justificación del LLM (JSON).")
        parsed_data["tipo_articulo"] = data.get("tipo_articulo", "INDETERMINADO").upper()
        parsed_data["total_puntuacion"] = data.get("total_puntuacion") # Será validado a float después
        parsed_data["elementos_clave"] = data.get("elementos_clave", [])

        # Mapear puntuaciones individuales si están presentes
        parsed_data["relevancia_geografica_score"] = data.get("relevancia_geografica_score")
        parsed_data["relevancia_geografica_pais"] = data.get("relevancia_geografica_pais")
        parsed_data["relevancia_tematica_score"] = data.get("relevancia_tematica_score")
        parsed_data["relevancia_tematica_tema"] = data.get("relevancia_tematica_tema")
        parsed_data["densidad_factual_score"] = data.get("densidad_factual_score")
        parsed_data["complejidad_relacional_score"] = data.get("complejidad_relacional_score")
        parsed_data["valor_informativo_score"] = data.get("valor_informativo_score")
        parsed_data["exclusion"] = data.get("exclusion")
        parsed_data["exclusion_categoria"] = data.get("exclusion_categoria")

        # Validar y convertir puntuaciones numéricas
        for score_field in ["relevancia_geografica_score", "relevancia_tematica_score",
                            "densidad_factual_score", "complejidad_relacional_score",
                            "valor_informativo_score", "total_puntuacion"]:
            val = parsed_data.get(score_field)
            if val is not None:
                try:
                    parsed_data[score_field] = float(val) if '.' in str(val) else int(val)
                except (ValueError, TypeError):
                    logger.warning(f"Valor de puntuación JSON '{score_field}' ('{val}') no es numérico. Usando None.")
                    parsed_data[score_field] = None
        return parsed_data

    except json.JSONDecodeError:
        logger.debug("Respuesta LLM para triaje no es un JSON válido, intentando parseo basado en regex.")
        # Si no es JSON, continuar con parseo regex. Reset justificacion si se va a parsear con regex.
        parsed_data["justificacion"] = "Error al parsear respuesta LLM con Regex."


    # PARSEO BASADO EN REGEX (como fallback)
    # EXCLUSIÓN
    match = re.search(r"EXCLUSIÓN:\s*(SÍ|NO)(?:\s*-\s*(.*?))?\n", respuesta_llm, re.IGNORECASE)
    if match:
        parsed_data["exclusion"] = match.group(1).upper()
        if match.group(2):
            parsed_data["exclusion_categoria"] = match.group(2).strip()

    # TIPO DE ARTÍCULO
    match = re.search(r"TIPO DE ARTÍCULO:\s*([A-ZÁÉÍÓÚÑ\s]+?)\n", respuesta_llm, re.IGNORECASE)
    if match:
        parsed_data["tipo_articulo"] = match.group(1).strip().upper()

    # PUNTUACIONES
    score_map = {
        "Relevancia geográfica": ("relevancia_geografica_score", "relevancia_geografica_pais"),
        "Relevancia temática": ("relevancia_tematica_score", "relevancia_tematica_tema"),
        "Densidad factual": ("densidad_factual_score", None),
        "Complejidad relacional": ("complejidad_relacional_score", None),
        "Valor informativo": ("valor_informativo_score", None),
    }
    for key_text, (score_field, detail_field) in score_map.items():
        # Regex: Puntuación: [0-5](?: - Detalle)? (Allow single digit, capture detail if present)
        # Updated to be more robust against missing spaces around hyphen or varied detail format.
        pattern = re.compile(rf"{key_text}:\s*\[(\d)\](?:\s*-\s*(.*?))?\n", re.IGNORECASE | re.DOTALL)
        match = pattern.search(respuesta_llm)
        if match:
            try:
                parsed_data[score_field] = int(match.group(1))
                if detail_field and match.group(2): # Check if group 2 (detail) exists
                    parsed_data[detail_field] = match.group(2).strip()
            except ValueError:
                logger.warning(f"No se pudo parsear la puntuación REGEX para '{key_text}'. Valor: {match.group(1)}")
            except TypeError: # if match.group(2) is None and strip() is called
                if detail_field: # only assign if detail field is expected
                     parsed_data[detail_field] = None


    # TOTAL
    match = re.search(r"TOTAL:\s*\[?(\d+(?:\.\d+)?)\]?\s*/\s*25\n", respuesta_llm, re.IGNORECASE)
    if match:
        try:
            parsed_data["total_puntuacion"] = float(match.group(1))
        except ValueError:
            logger.warning(f"No se pudo parsear la puntuación total. Valor: {match.group(1)}")

    # DECISIÓN
    match = re.search(r"DECISIÓN:\s*(PROCESAR|CONSIDERAR|DESCARTAR)", respuesta_llm, re.IGNORECASE)
    if match:
        parsed_data["decision"] = match.group(1).upper()

    # JUSTIFICACIÓN
    # Captura todo hasta 'ELEMENTOS CLAVE:' o el final del string si 'ELEMENTOS CLAVE:' no existe, o hasta una nueva sección en mayúsculas.
    match = re.search(r"JUSTIFICACIÓN:\s*(.*?)(?:\n\s*ELEMENTOS CLAVE:|\n\s*[A-ZÁÉÍÓÚÑ\s]+:|\Z)", respuesta_llm, re.IGNORECASE | re.DOTALL)
    if match:
        parsed_data["justificacion"] = match.group(1).strip()

    # ELEMENTOS CLAVE
    # Busca la sección 'ELEMENTOS CLAVE:' y captura las líneas siguientes que empiezan con '-' o '*' hasta una línea en blanco o nueva sección.
    elementos_match = re.search(r"ELEMENTOS CLAVE:\s*\n((?:-\s*.*| \*\s*.*)(?:\n(?:-\s*.*| \*\s*.*))*)", respuesta_llm, re.IGNORECASE)
    if elementos_match:
        elementos_texto = elementos_match.group(1)
        # Divide por líneas y filtra las que empiezan con '-' o '*'
        parsed_data["elementos_clave"] = [line.strip()[1:].strip() for line in elementos_texto.split('\n') 
                                            if line.strip().startswith(('-', '*')) and len(line.strip()) > 1]

    return parsed_data



def _llamar_groq_api_traduccion(
    config: Dict[str, Any],
    texto_a_traducir: str,
    idioma_origen: str,
    idioma_destino: str = "español"
) -> Optional[str]: # This Optional[str] will be changed to str
@retry_groq_api()
def _llamar_groq_api_traduccion(
    config: Dict[str, Any],
    texto_a_traducir: str,
    idioma_origen: str,
    idioma_destino: str = "español"
) -> str:
    """
    Llama a la API de Groq para traducir texto. Retries son manejados por @retry_groq_api.
    Levanta GroqAPIError en caso de fallo persistente o configuración incorrecta.
    """
    article_id_log = config.get("article_id", "N/A") # For logging purposes
    if not Groq:
        logger.error(f"SDK de Groq no instalado para traducción. Artículo: {article_id_log}")
        raise GroqAPIError("SDK de Groq no instalado.", phase=ErrorPhase.FASE_1_TRIAJE, article_id=config.get("article_id"))
    if not config.get("api_key"):
        logger.error(f"GROQ_API_KEY no configurada para traducción. Artículo: {article_id_log}")
        raise GroqAPIError("GROQ_API_KEY no configurada para traducción.", phase=ErrorPhase.FASE_1_TRIAJE, article_id=config.get("article_id"))

    prompt_traduccion = (
        f"Traduce el siguiente texto de '{idioma_origen}' a {idioma_destino}. "
        f"IMPORTANTE: Devuelve ÚNICAMENTE el texto traducido, sin ningún prefijo, comentario, explicación, markdown, ni etiqueta HTML. "
        f"Solo el texto traducido puro. Texto a traducir:\n\n{texto_a_traducir}"
    )
    
    client = Groq(api_key=config["api_key"], timeout=config["timeout"])
    
    logger.info(f"Enviando solicitud a Groq API para traducción (modelo: {config['model_id']}). Artículo: {article_id_log}")
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt_traduccion,
            }
        ],
        model=config["model_id"],
        temperature=config.get("translation_temperature", config["temperature"]),
        max_tokens=config.get("translation_max_tokens", config["max_tokens"]),
    )
    respuesta_contenido = chat_completion.choices[0].message.content
    if not respuesta_contenido or not respuesta_contenido.strip():
        logger.warning(f"Groq API para traducción devolvió una respuesta vacía. Idioma origen: {idioma_origen}. Artículo: {article_id_log}")
        raise GroqAPIError("Respuesta vacía o solo espacios de Groq API para traducción.", phase=ErrorPhase.FASE_1_TRIAJE, article_id=config.get("article_id"))

    logger.info(f"Respuesta de traducción recibida de Groq API. Idioma origen: {idioma_origen}. Artículo: {article_id_log}")
    return respuesta_contenido.strip()


# Bloque para pruebas directas del módulo (opcional)
# if __name__ == '__main__':
#     from uuid import uuid4
#     # Asegúrate de tener loguru configurado si quieres ver los logs:
#     # import sys
#     # logger.remove()
#     # logger.add(sys.stderr, level="TRACE") # Para ver todos los logs, incluidos TRACE

#     test_id = uuid4()
#     test_texto_es = "  Esto   es una prueba...  ¡¡¡Con múltiples    espacios y puntuación!!! \n\n   Otra línea.  "
#     test_texto_vacio = "   "
#     test_texto_en = "This is an English text, just for testing the model language output."

#     print(f"\n--- Prueba con texto en español: {test_id} ---")
#     try:
#         # Para probar la carga de un modelo que podría no existir y el fallback:
#         # ejecutar_fase_1(test_id, test_texto_es, modelo_spacy_nombre="xx_non_existent_model_sm")
#         ejecutar_fase_1(test_id, test_texto_es)
#     except NotImplementedError as e:
#         logger.success(f"Ejecución de prueba (Español) falló como esperado (NotImplementedError): {e}")
#     except ErrorFase1 as e:
#         logger.error(f"Error específico de Fase 1 en prueba (Español): {e}")

#     print(f"\n--- Prueba con texto vacío: {test_id} ---")
#     try:
#         ejecutar_fase_1(test_id, test_texto_vacio)
#     except NotImplementedError as e:
#         logger.success(f"Ejecución de prueba (Vacío) falló como esperado (NotImplementedError): {e}")
#     except ErrorFase1 as e:
#         logger.error(f"Error específico de Fase 1 en prueba (Vacío): {e}")

#     print(f"\n--- Prueba con texto en inglés (usando modelo español por defecto): {test_id} ---")
#     # Esto demostrará que _detectar_idioma devuelve 'es' porque el modelo cargado es 'es_core_news_sm'
#     try:
#         ejecutar_fase_1(test_id, test_texto_en)
#     except NotImplementedError as e:
#         logger.success(f"Ejecución de prueba (Inglés con modelo ES) falló como esperado (NotImplementedError): {e}")
#     except ErrorFase1 as e:
#         logger.error(f"Error específico de Fase 1 en prueba (Inglés con modelo ES): {e}")

    # # Para probar con un modelo en inglés explícitamente (necesitas descargarlo: python -m spacy download en_core_web_sm)
    # print(f"\n--- Prueba con texto en inglés (usando modelo inglés): {test_id} ---")
    # try:
    #     ejecutar_fase_1(test_id, test_texto_en, modelo_spacy_nombre="en_core_web_sm")
    # except NotImplementedError as e:
    #     logger.success(f"Ejecución de prueba (Inglés con modelo EN) falló como esperado (NotImplementedError): {e}")
    # except ErrorFase1 as e:
    #     logger.error(f"Error específico de Fase 1 en prueba (Inglés con modelo EN): {e}")
