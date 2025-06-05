from typing import Optional, List, Dict, Any
from uuid import UUID
import re
import os
import time
import json # Para posible parseo si Groq devuelve JSON string, aunque el prompt pide texto.
from pathlib import Path

# Importar el modelo de resultado de la fase 1 desde el módulo de modelos
from ..models.procesamiento import ResultadoFase1Triaje, MetadatosFase1Triaje

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
        logger.error("spaCy no está instalado. No se puede cargar ningún modelo.")
        return None

    if modelo not in _NLP_MODELS_CACHE:
        try:
            logger.info(f"Cargando modelo spaCy: {modelo}")
            _NLP_MODELS_CACHE[modelo] = spacy.load(modelo)
            logger.info(f"Modelo spaCy '{modelo}' cargado exitosamente.")
        except OSError:
            logger.error(f"No se pudo cargar el modelo spaCy '{modelo}'. "
                         f"Asegúrate de que está descargado (ej: python -m spacy download {modelo})")
            _NLP_MODELS_CACHE[modelo] = None # Marcar como no cargado para no reintentar innecesariamente
        except Exception as e:
            logger.error(f"Error inesperado al cargar el modelo spaCy '{modelo}': {e}")
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

    nlp_model = _cargar_modelo_spacy(modelo_spacy_nombre)
    if not nlp_model: # Si el modelo (incluido el fallback) no se pudo cargar
        # Crear un resultado parcial indicando el fallo en la carga del modelo
        logger.error(f"Fallo crítico: No se pudo cargar ningún modelo de spaCy para el fragmento {id_fragmento_original}.")
        # Podríamos devolver un ResultadoFase1Triaje con un estado de error aquí
        # o lanzar una excepción más específica si se prefiere no continuar.
        raise ErrorFase1(f"No se pudo cargar el modelo spaCy necesario ('{modelo_spacy_nombre}' o fallback). Imposible continuar Fase 1.")

    texto_limpio = _limpiar_texto(texto_original_fragmento, nlp_model)
    idioma_detectado = _detectar_idioma(texto_limpio, nlp_model)

    logger.debug(f"Fragmento {id_fragmento_original}: Texto limpio generado, Idioma detectado: {idioma_detectado}")

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
    if not groq_config.get("api_key"):
        logger.error(f"No se encontró GROQ_API_KEY. Imposible realizar evaluación de relevancia para {id_fragmento_original}.")
        # Aquí podríamos decidir si lanzar un error o continuar con un resultado parcial sin evaluación LLM.
        # Por ahora, lanzaremos error para asegurar que la configuración esté completa.
        raise ErrorFase1("GROQ_API_KEY no configurada en variables de entorno.")

    # Para fragmentos, no tenemos título, medio, etc. Usaremos placeholders.
    # El prompt debe ser robusto a esto, o esta información debe ser opcional.
    prompt_formateado, respuesta_llm_cruda = _llamar_groq_api_triaje(
        config=groq_config,
        texto_contenido=texto_limpio,
        titulo="No disponible (fragmento)",
        medio="No disponible (fragmento)",
        pais="No disponible (fragmento)",
        fecha_pub="No disponible (fragmento)"
    )

    if respuesta_llm_cruda is None:
        logger.error(f"No se obtuvo respuesta del LLM para triaje del fragmento {id_fragmento_original} después de reintentos.")
        # Decidir cómo manejar: ¿ErrorFase1 o resultado parcial sin evaluación?
        # Por ahora, error, ya que la evaluación es clave.
        raise ErrorFase1(f"Fallo al obtener respuesta de Groq API para triaje de {id_fragmento_original}.")

    logger.trace(f"Respuesta LLM (cruda) para triaje de {id_fragmento_original}:\n{respuesta_llm_cruda}")
    
    evaluacion_triaje = _parsear_respuesta_triaje(respuesta_llm_cruda)
    logger.debug(f"Evaluación de triaje parseada para {id_fragmento_original}: {evaluacion_triaje}")

    # Aquí se usarían los campos de 'evaluacion_triaje' para popular 'ResultadoFase1Triaje'
    # Por ejemplo:
    # relevancia_evaluada = evaluacion_triaje.get("decision")
    # puntuacion_relevancia = evaluacion_triaje.get("total_puntuacion")
    # ... y otros campos como justificacion, tipo_articulo, metricas, etc.

    # --- Subtarea 15.4: Implementación de Lógica de Traducción ---
    texto_traducido_para_llm = None
    # Solo traducir si el idioma no es español y la decisión de triaje no es DESCARTAR directamente
    # (aunque la decisión final de usar el texto traducido dependerá de la lógica en 15.5)
    if idioma_detectado and idioma_detectado.lower() != "es" and evaluacion_triaje.get("decision") != "DESCARTAR":
        if texto_limpio and texto_limpio.strip(): # Solo traducir si hay texto
            logger.info(f"Traduciendo texto de '{idioma_detectado}' a 'es' para fragmento {id_fragmento_original}.")
            texto_traducido_para_llm = _llamar_groq_api_traduccion(
                config=groq_config,
                texto_a_traducir=texto_limpio,
                idioma_origen=idioma_detectado
            )
            if texto_traducido_para_llm:
                logger.debug(f"Texto traducido para {id_fragmento_original}: '{texto_traducido_para_llm[:100]}...'" )
            else:
                logger.warning(f"La traducción para {id_fragmento_original} falló o devolvió None.")
        else:
            logger.debug(f"No se requiere traducción para {id_fragmento_original} (texto limpio vacío)." )
    else:
        logger.debug(f"No se requiere traducción para {id_fragmento_original} (idioma: {idioma_detectado}, decisión triaje: {evaluacion_triaje.get('decision')}).")

    # --- Subtarea 15.5: Ensamblaje final del objeto ResultadoFase1Triaje ---
    metricas_dict = {
        "relevancia_geografica_score": evaluacion_triaje.get("relevancia_geografica_score"),
        "relevancia_geografica_pais": evaluacion_triaje.get("relevancia_geografica_pais"),
        "relevancia_tematica_score": evaluacion_triaje.get("relevancia_tematica_score"),
        "relevancia_tematica_tema": evaluacion_triaje.get("relevancia_tematica_tema"),
        "densidad_factual_score": evaluacion_triaje.get("densidad_factual_score"),
        "complejidad_relacional_score": evaluacion_triaje.get("complejidad_relacional_score"),
        "valor_informativo_score": evaluacion_triaje.get("valor_informativo_score"),
        "exclusion_aplicada": evaluacion_triaje.get("exclusion"),
        "exclusion_categoria": evaluacion_triaje.get("exclusion_categoria")
    }

    metadatos_fase1 = MetadatosFase1Triaje(
        nombre_modelo_triaje=groq_config.get("modelo", "llama3-8b-8192"),
        tokens_prompt_triaje=None,  # TODO: Obtener de la respuesta de Groq si está disponible
        tokens_respuesta_triaje=None,  # TODO: Obtener de la respuesta de Groq si está disponible
        duracion_llamada_ms_triaje=None,  # TODO: Medir tiempo de llamada
        texto_limpio_utilizado=texto_limpio,
        idioma_detectado_original=idioma_detectado
    )

    resultado_final = ResultadoFase1Triaje(
        id_fragmento=id_fragmento_original,
        es_relevante=(evaluacion_triaje.get("decision", "ERROR_TRIAGE") == "PROCESAR"),
        decision_triaje=evaluacion_triaje.get("decision", "ERROR_TRIAGE"),
        justificacion_triaje=evaluacion_triaje.get("justificacion"),
        categoria_principal=evaluacion_triaje.get("tipo_articulo"),
        palabras_clave_triaje=evaluacion_triaje.get("elementos_clave", []),
        puntuacion_triaje=evaluacion_triaje.get("total_puntuacion"),
        confianza_triaje=None,  # Podríamos mapear esto desde algún score si es necesario
        texto_para_siguiente_fase=texto_traducido_para_llm if texto_traducido_para_llm else texto_limpio,
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
) -> tuple[Optional[str], Optional[str]]:
    """Llama a la API de Groq para evaluación de triaje y maneja reintentos."""
    if not Groq:
        logger.error("El SDK de Groq no está instalado. No se puede llamar a la API.")
        return None, None
    if not config.get("api_key"):
        logger.error("GROQ_API_KEY no proporcionada en la configuración.")
        return None, None

    try:
        prompt_template = _load_prompt_template()
    except ErrorFase1:
        return None, None # Error ya logueado en _load_prompt_template

    prompt_formateado = prompt_template.replace("{{TITULO}}", titulo)\
                                     .replace("{{MEDIO}}", medio)\
                                     .replace("{{PAIS}}", pais)\
                                     .replace("{{FECHA_PUB}}", fecha_pub)\
                                     .replace("{{CONTENIDO}}", texto_contenido)
    
    client = Groq(api_key=config["api_key"], timeout=config["timeout"])
    
    for intento in range(config["max_retries"] + 1):
        try:
            logger.info(f"Enviando solicitud a Groq API (intento {intento + 1}/{config['max_retries'] + 1}) para triaje...")
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
            logger.info("Respuesta recibida de Groq API para triaje.")
            return prompt_formateado, respuesta_contenido
        except Exception as e:
            logger.warning(f"Error en llamada a Groq API (intento {intento + 1}): {e}")
            if intento < config["max_retries"]:
                espera = min(config["max_wait_seconds"], (2 ** intento))
                logger.info(f"Reintentando en {espera} segundos...")
                time.sleep(espera)
            else:
                logger.error("Máximo número de reintentos alcanzado para Groq API.")
                return prompt_formateado, None # Devuelve el prompt usado incluso si falla
    return prompt_formateado, None # No debería llegar aquí si max_retries >= 0

def _parsear_respuesta_triaje(respuesta_llm: str) -> Dict[str, Any]:
    """Parsea la respuesta textual del LLM para el triaje."""
    parsed_data = {
        "exclusion": None, "exclusion_categoria": None,
        "tipo_articulo": None,
        "relevancia_geografica_score": None, "relevancia_geografica_pais": None,
        "relevancia_tematica_score": None, "relevancia_tematica_tema": None,
        "densidad_factual_score": None,
        "complejidad_relacional_score": None,
        "valor_informativo_score": None,
        "total_puntuacion": None,
        "decision": None,
        "justificacion": None,
        "elementos_clave": []
    }

    if not respuesta_llm:
        return parsed_data

    # EXCLUSIÓN
    match = re.search(r"EXCLUSIÓN:\s*(SÍ|NO)(?:\s*-\s*(.*?))?", respuesta_llm, re.IGNORECASE)
    if match:
        parsed_data["exclusion"] = match.group(1).upper()
        if match.group(2):
            parsed_data["exclusion_categoria"] = match.group(2).strip()

    # TIPO DE ARTÍCULO
    match = re.search(r"TIPO DE ARTÍCULO:\s*([A-ZÁÉÍÓÚÑ\s]+)", respuesta_llm, re.IGNORECASE)
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
        # Regex: Puntuación: [1-5] - [Detalle opcional] OR Puntuación: [1-5]
        pattern = re.compile(rf"{key_text}:\s*\[(\d)\](?:\s*-\s*(.*?))?", re.IGNORECASE | re.DOTALL)
        match = pattern.search(respuesta_llm)
        if match:
            try:
                parsed_data[score_field] = int(match.group(1))
                if detail_field and match.group(2):
                    parsed_data[detail_field] = match.group(2).strip()
            except ValueError:
                logger.warning(f"No se pudo parsear la puntuación para '{key_text}'. Valor: {match.group(1)}")

    # TOTAL
    match = re.search(r"TOTAL:\s*\[?(\d+(?:\.\d+)?)\]?\s*/\s*25", respuesta_llm, re.IGNORECASE)
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
    # Captura todo hasta 'ELEMENTOS CLAVE:' o el final del string si 'ELEMENTOS CLAVE:' no existe.
    match = re.search(r"JUSTIFICACIÓN:\s*(.*?)(?:\n\s*ELEMENTOS CLAVE:|\Z)", respuesta_llm, re.IGNORECASE | re.DOTALL)
    if match:
        parsed_data["justificacion"] = match.group(1).strip()

    # ELEMENTOS CLAVE
    # Busca la sección 'ELEMENTOS CLAVE:' y captura las líneas siguientes que empiezan con '-' o '*'
    elementos_match = re.search(r"ELEMENTOS CLAVE:\s*\n(.*?)(?:\n\s*\n|\Z)", respuesta_llm, re.IGNORECASE | re.DOTALL)
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
) -> Optional[str]:
    """Llama a la API de Groq para traducir texto y maneja reintentos."""
    if not Groq:
        logger.error("El SDK de Groq no está instalado. No se puede realizar la traducción.")
        return None
    if not config.get("api_key"):
        logger.error("GROQ_API_KEY no proporcionada en la configuración para traducción.")
        return None

    # Prompt simple y directo para traducción
    prompt_traduccion = (
        f"Traduce el siguiente texto de '{idioma_origen}' a {idioma_destino}. "
        f"El resultado debe ser únicamente el texto traducido, sin ningún tipo de comentario, explicación o etiqueta adicional. "
        f"Texto a traducir:\n\n{texto_a_traducir}"
    )
    
    client = Groq(api_key=config["api_key"], timeout=config["timeout"])
    
    for intento in range(config["max_retries"] + 1):
        try:
            logger.info(f"Enviando solicitud a Groq API (intento {intento + 1}/{config['max_retries'] + 1}) para traducción...")
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt_traduccion,
                    }
                ],
                model=config["model_id"],
                temperature=config.get("translation_temperature", config["temperature"]), # Permitir temp. específica para traducción
                max_tokens=config.get("translation_max_tokens", config["max_tokens"]), # Permitir max_tokens específico
            )
            respuesta_contenido = chat_completion.choices[0].message.content
            logger.info("Respuesta de traducción recibida de Groq API.")
            return respuesta_contenido.strip() # Devolver solo el texto traducido
        except Exception as e:
            logger.warning(f"Error en llamada a Groq API para traducción (intento {intento + 1}): {e}")
            if intento < config["max_retries"]:
                espera = min(config["max_wait_seconds"], (2 ** intento))
                logger.info(f"Reintentando traducción en {espera} segundos...")
                time.sleep(espera)
            else:
                logger.error("Máximo número de reintentos alcanzado para traducción con Groq API.")
                return None
    return None # No debería llegar aquí


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
