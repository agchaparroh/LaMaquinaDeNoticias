from typing import Optional, List, Dict, Any
from uuid import UUID  # Solo para tipos, no para generar IDs
import os
import json
from pathlib import Path
from datetime import datetime

# ✅ IMPORTAR FRAGMENT PROCESSOR
from ..utils.fragment_processor import FragmentProcessor

# ✅ IMPORTAR FUNCIONES DE VALIDACIÓN
from ..utils.validation import (
    escape_html,
    validate_confidence_score,
    validate_offset_range
)

# Importar modelos de resultado de la fase 2 desde el módulo de modelos
from ..models.procesamiento import (
    ResultadoFase2Extraccion, 
    HechoProcesado, 
    EntidadProcesada,
    ResultadoFase1Triaje
)
from ..models.metadatos import MetadatosHecho, MetadatosEntidad

# Importar manejadores de errores y tipos necesarios
from ..utils.error_handling import (
    handle_generic_phase_error,
    ErrorPhase,
    retry_groq_api,
    GroqAPIError,
    ProcessingError
)

# Importar servicio Groq
try:
    from groq import Groq
except ImportError:
    Groq = None

from loguru import logger

# --- Funciones auxiliares para la Fase 2 ---

_PROMPT_EXTRACCION_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "Prompt_2_elementos_basicos.md"
_PROMPT_EXTRACCION_TEMPLATE: Optional[str] = None

class ErrorFase2(Exception):
    """Excepción base para errores específicos de la Fase 2."""
    pass

def _load_prompt_template() -> str:
    """Carga la plantilla del prompt para extracción de elementos básicos."""
    global _PROMPT_EXTRACCION_TEMPLATE
    if _PROMPT_EXTRACCION_TEMPLATE is None:
        try:
            with open(_PROMPT_EXTRACCION_PATH, "r", encoding="utf-8") as f:
                _PROMPT_EXTRACCION_TEMPLATE = f.read()
            logger.info(f"Plantilla de prompt de extracción cargada desde: {_PROMPT_EXTRACCION_PATH}")
        except FileNotFoundError:
            logger.error(f"No se encontró el archivo de prompt de extracción en: {_PROMPT_EXTRACCION_PATH}")
            raise ErrorFase2(f"Archivo de prompt de extracción no encontrado: {_PROMPT_EXTRACCION_PATH}")
        except Exception as e:
            logger.error(f"Error al cargar el prompt de extracción: {e}")
            raise ErrorFase2(f"Error cargando prompt de extracción: {e}")
    return _PROMPT_EXTRACCION_TEMPLATE

def _get_groq_config() -> Dict[str, Any]:
    """Carga la configuración para la API de Groq desde variables de entorno."""
    return {
        "api_key": os.getenv("GROQ_API_KEY"),
        "model_id": os.getenv("GROQ_MODEL_ID", "mixtral-8x7b-32768"),
        "timeout": float(os.getenv("GROQ_API_TIMEOUT", "30.0")),
        "temperature": float(os.getenv("GROQ_API_TEMPERATURE", "0.1")),
        "max_tokens": int(os.getenv("GROQ_API_MAX_TOKENS", "2000")),  # Más tokens para extracción
        "max_retries": int(os.getenv("GROQ_MAX_RETRIES", "3")),
        "max_wait_seconds": int(os.getenv("GROQ_MAX_WAIT_SECONDS", "60")),
    }

@retry_groq_api()
def _llamar_groq_api_extraccion(
    config: Dict[str, Any],
    texto_contenido: str,
    titulo_documento: str = "No disponible",
    fuente_tipo: str = "No disponible",
    pais_origen: str = "No disponible",
    fecha_fuente: str = "No disponible"
) -> tuple[str, str]:
    """
    Llama a la API de Groq para extracción de elementos básicos.
    Retries son manejados por @retry_groq_api.
    Levanta GroqAPIError en caso de fallo persistente o configuración incorrecta.
    """
    article_id_log = config.get("article_id", "N/A")
    if not Groq:
        logger.error(f"SDK de Groq no instalado. Artículo: {article_id_log}")
        raise GroqAPIError("SDK de Groq no instalado.", phase=ErrorPhase.FASE_2_EXTRACCION, article_id=config.get("article_id"))
    if not config.get("api_key"):
        logger.error(f"GROQ_API_KEY no configurada. Artículo: {article_id_log}")
        raise GroqAPIError("GROQ_API_KEY no configurada.", phase=ErrorPhase.FASE_2_EXTRACCION, article_id=config.get("article_id"))

    try:
        prompt_template = _load_prompt_template()
    except ErrorFase2 as e_prompt:
        logger.error(f"Fallo al cargar plantilla de prompt para extracción. Artículo: {article_id_log}. Error: {e_prompt}")
        raise GroqAPIError(f"Fallo al cargar plantilla de prompt para extracción: {e_prompt}", phase=ErrorPhase.FASE_2_EXTRACCION, article_id=config.get("article_id")) from e_prompt

    # Formatear el prompt con las variables
    prompt_formateado = prompt_template.replace("{{TITULO_O_DOCUMENTO}}", titulo_documento)\
                                     .replace("{{FUENTE_O_TIPO}}", fuente_tipo)\
                                     .replace("{{PAIS_ORIGEN}}", pais_origen)\
                                     .replace("{{FECHA_FUENTE}}", fecha_fuente)\
                                     .replace("{{CONTENIDO}}", texto_contenido)

    client = Groq(api_key=config["api_key"], timeout=config["timeout"])

    logger.info(f"Enviando solicitud a Groq API para extracción (modelo: {config['model_id']}). Artículo: {article_id_log}")
    
    # Agregar instrucción para obtener solo JSON
    system_prompt = "Eres un asistente que extrae información estructurada de textos. Responde ÚNICAMENTE con el JSON solicitado, sin texto adicional, sin markdown, sin explicaciones."
    
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": prompt_formateado,
            }
        ],
        model=config["model_id"],
        temperature=config["temperature"],
        max_tokens=config["max_tokens"],
        response_format={"type": "json_object"}  # Forzar respuesta JSON
    )
    
    respuesta_contenido = chat_completion.choices[0].message.content
    if not respuesta_contenido or not respuesta_contenido.strip():
        logger.warning(f"Groq API para extracción devolvió una respuesta vacía. Artículo: {article_id_log}")
        raise GroqAPIError("Respuesta vacía de Groq API para extracción.", phase=ErrorPhase.FASE_2_EXTRACCION, article_id=config.get("article_id"))
    
    logger.info(f"Respuesta recibida de Groq API para extracción. Artículo: {article_id_log}")
    return prompt_formateado, respuesta_contenido

def _parsear_hechos_from_json(
    response_json: Dict[str, Any], 
    id_fragmento_origen: UUID,
    processor: FragmentProcessor  # ✅ AÑADIDO
) -> List[HechoProcesado]:
    """
    Parsea los hechos desde la respuesta JSON del LLM y los convierte a HechoProcesado.
    SOLUCIÓN ARQUITECTÓNICA: Usa FragmentProcessor para IDs secuenciales.
    """
    hechos_procesados = []
    hechos_raw = response_json.get("hechos", [])
    
    logger.debug(f"Parseando {len(hechos_raw)} hechos del JSON para fragmento {id_fragmento_origen}")
    
    for hecho_raw in hechos_raw:
        try:
            # ✅ Usar el ID del JSON (que ya es secuencial)
            id_hecho_json = hecho_raw.get("id", 1)
            
            # ✅ Registrar en el processor para validación
            texto_hecho = hecho_raw.get("contenido", "")
            
            # ✅ SANITIZAR TEXTO DEL HECHO
            texto_hecho_sanitizado = escape_html(texto_hecho)
            
            descripcion_hecho = texto_hecho_sanitizado[:50]  # Descripción para debugging
            id_hecho_registrado = processor.next_hecho_id(descripcion_hecho)
            
            # ✅ Validar consistencia
            if id_hecho_json != id_hecho_registrado:
                logger.warning(
                    f"Inconsistencia de ID hecho: JSON={id_hecho_json}, "
                    f"Processor={id_hecho_registrado}. Usando ID del JSON."
                )
            
            # Extraer fechas
            fecha_obj = hecho_raw.get("fecha", {})
            fecha_inicio = fecha_obj.get("inicio")
            fecha_fin = fecha_obj.get("fin")
            
            # ✅ VALIDAR CONFIANZA SI VIENE EN EL JSON
            confianza = hecho_raw.get("confianza", 0.8)
            try:
                confianza = validate_confidence_score(float(confianza))
            except (ValueError, TypeError):
                logger.warning(f"Confianza inválida para hecho {id_hecho_json}: {confianza}. Usando valor por defecto.")
                confianza = 0.8
            
            # ✅ VALIDAR OFFSETS SI EXISTEN
            offset_inicio = hecho_raw.get("offset_inicio")
            offset_fin = hecho_raw.get("offset_fin")
            if offset_inicio is not None or offset_fin is not None:
                try:
                    offset_inicio, offset_fin = validate_offset_range(
                        offset_inicio if offset_inicio is not None else None,
                        offset_fin if offset_fin is not None else None
                    )
                    # Validar coherencia con el texto
                    if offset_fin and len(texto_hecho) > 0:
                        if offset_fin - (offset_inicio or 0) > len(texto_hecho) * 2:
                            logger.warning(
                                f"Offsets parecen incorrectos para hecho {id_hecho_json}: "
                                f"rango={offset_fin - (offset_inicio or 0)}, len_texto={len(texto_hecho)}"
                            )
                except ValueError as e:
                    logger.warning(f"Offsets inválidos para hecho {id_hecho_json}: {e}")
                    offset_inicio = offset_fin = None
            
            # Crear metadatos del hecho
            metadata_hecho = MetadatosHecho(
                precision_temporal=hecho_raw.get("precision_temporal"),
                tipo_hecho=hecho_raw.get("tipo_hecho"),
                pais=hecho_raw.get("pais", []),
                region=hecho_raw.get("region", []),
                ciudad=hecho_raw.get("ciudad", []),
                es_futuro=hecho_raw.get("es_futuro"),
                estado_programacion=hecho_raw.get("estado_programacion")
            )
            
            # Crear HechoProcesado con ID secuencial
            hecho_procesado = HechoProcesado(
                id_hecho=id_hecho_json,  # ✅ int secuencial del JSON
                texto_original_del_hecho=texto_hecho_sanitizado,  # ✅ TEXTO SANITIZADO
                confianza_extraccion=confianza,  # ✅ CONFIANZA VALIDADA
                offset_inicio_hecho=offset_inicio,  # ✅ OFFSETS VALIDADOS
                offset_fin_hecho=offset_fin,
                id_fragmento_origen=id_fragmento_origen,
                metadata_hecho=metadata_hecho,
                respuesta_llm_bruta={
                    "id_original": id_hecho_json,
                    "fecha": fecha_obj
                }
            )
            
            hechos_procesados.append(hecho_procesado)
            logger.trace(f"Hecho procesado: ID {hecho_procesado.id_hecho}, Tipo: {metadata_hecho.tipo_hecho}")
            
        except Exception as e:
            logger.warning(f"Error al parsear hecho {hecho_raw.get('id', 'N/A')}: {e}")
            continue
    
    logger.info(f"Parseados {len(hechos_procesados)} hechos exitosamente para fragmento {id_fragmento_origen}")
    return hechos_procesados

def _parsear_entidades_from_json(
    response_json: Dict[str, Any], 
    id_fragmento_origen: UUID,
    processor: FragmentProcessor  # ✅ AÑADIDO
) -> List[EntidadProcesada]:
    """
    Parsea las entidades desde la respuesta JSON del LLM y las convierte a EntidadProcesada.
    SOLUCIÓN ARQUITECTÓNICA: Usa FragmentProcessor para IDs secuenciales.
    """
    entidades_procesadas = []
    entidades_raw = response_json.get("entidades", [])
    
    logger.debug(f"Parseando {len(entidades_raw)} entidades del JSON para fragmento {id_fragmento_origen}")
    
    for entidad_raw in entidades_raw:
        try:
            # ✅ Usar el ID del JSON (que ya es secuencial)
            id_entidad_json = entidad_raw.get("id", 1)
            
            # ✅ Registrar en el processor
            nombre_entidad = entidad_raw.get("nombre", "")
            
            # ✅ SANITIZAR TEXTO DE ENTIDAD
            nombre_entidad_sanitizado = escape_html(nombre_entidad)
            
            id_entidad_registrado = processor.next_entidad_id(nombre_entidad_sanitizado)
            
            # ✅ Validar consistencia
            if id_entidad_json != id_entidad_registrado:
                logger.warning(
                    f"Inconsistencia de ID entidad: JSON={id_entidad_json}, "
                    f"Processor={id_entidad_registrado}. Usando ID del JSON."
                )
            
            # Procesar descripción (viene con guiones)
            descripcion_raw = entidad_raw.get("descripcion", "")
            descripcion_estructurada = []
            if descripcion_raw:
                # Dividir por guiones y limpiar
                partes = descripcion_raw.split(" - ")
                # ✅ SANITIZAR CADA PARTE DE LA DESCRIPCIÓN
                descripcion_estructurada = [
                    escape_html(parte.strip()) 
                    for parte in partes 
                    if parte.strip()
                ]
            
            # ✅ SANITIZAR TIPO DE ENTIDAD
            tipo_entidad = escape_html(entidad_raw.get("tipo", "DESCONOCIDO"))
            
            # ✅ VALIDAR RELEVANCIA SI VIENE EN EL JSON
            relevancia = entidad_raw.get("relevancia", 0.7)
            try:
                relevancia = validate_confidence_score(float(relevancia))
            except (ValueError, TypeError):
                logger.warning(f"Relevancia inválida para entidad {id_entidad_json}: {relevancia}. Usando valor por defecto.")
                relevancia = 0.7
            
            # ✅ VALIDAR OFFSETS SI EXISTEN
            offset_inicio = entidad_raw.get("offset_inicio")
            offset_fin = entidad_raw.get("offset_fin")
            if offset_inicio is not None or offset_fin is not None:
                try:
                    offset_inicio, offset_fin = validate_offset_range(
                        offset_inicio if offset_inicio is not None else None,
                        offset_fin if offset_fin is not None else None
                    )
                    # Validar coherencia con el texto
                    if offset_fin and len(nombre_entidad) > 0:
                        if offset_fin - (offset_inicio or 0) > len(nombre_entidad) * 2:
                            logger.warning(
                                f"Offsets parecen incorrectos para entidad {id_entidad_json}: "
                                f"rango={offset_fin - (offset_inicio or 0)}, len_texto={len(nombre_entidad)}"
                            )
                except ValueError as e:
                    logger.warning(f"Offsets inválidos para entidad {id_entidad_json}: {e}")
                    offset_inicio = offset_fin = None
            
            # ✅ SANITIZAR ALIAS
            alias_sanitizados = []
            if entidad_raw.get("alias"):
                alias_sanitizados = [
                    escape_html(alias.strip()) 
                    for alias in entidad_raw["alias"] 
                    if isinstance(alias, str) and alias.strip()
                ]
            
            # Crear metadatos de la entidad
            metadata_entidad = MetadatosEntidad(
                tipo=tipo_entidad,
                alias=alias_sanitizados,
                fecha_nacimiento=entidad_raw.get("fecha_nacimiento"),
                fecha_disolucion=entidad_raw.get("fecha_disolucion"),
                descripcion_estructurada=descripcion_estructurada
            )
            
            # Crear EntidadProcesada con ID secuencial
            entidad_procesada = EntidadProcesada(
                id_entidad=id_entidad_json,  # ✅ int secuencial del JSON
                texto_entidad=nombre_entidad_sanitizado,  # ✅ TEXTO SANITIZADO
                tipo_entidad=tipo_entidad,  # ✅ TIPO SANITIZADO
                relevancia_entidad=relevancia,  # ✅ RELEVANCIA VALIDADA
                offset_inicio_entidad=offset_inicio,  # ✅ OFFSETS VALIDADOS
                offset_fin_entidad=offset_fin,
                id_fragmento_origen=id_fragmento_origen,
                metadata_entidad=metadata_entidad
            )
            
            entidades_procesadas.append(entidad_procesada)
            logger.trace(f"Entidad procesada: ID {entidad_procesada.id_entidad}, Nombre: {entidad_procesada.texto_entidad}, Tipo: {entidad_procesada.tipo_entidad}")
            
        except Exception as e:
            logger.warning(f"Error al parsear entidad {entidad_raw.get('id', 'N/A')}: {e}")
            continue
    
    logger.info(f"Parseadas {len(entidades_procesadas)} entidades exitosamente para fragmento {id_fragmento_origen}")
    return entidades_procesadas

def ejecutar_fase_2(
    resultado_fase_1: ResultadoFase1Triaje,
    processor: FragmentProcessor  # ✅ AÑADIDO
) -> ResultadoFase2Extraccion:
    """
    Ejecuta la Fase 2: Extracción de Elementos Básicos.
    Extrae hechos principales y entidades mencionadas del texto preprocesado.
    
    SOLUCIÓN ARQUITECTÓNICA: Usa FragmentProcessor para mantener IDs secuenciales
    coherentes a través de todas las fases del pipeline.

    Args:
        resultado_fase_1: El resultado de la Fase 1 con el texto preprocesado.
        processor: FragmentProcessor para gestión de IDs secuenciales.

    Returns:
        Un objeto ResultadoFase2Extraccion con los hechos y entidades extraídos.

    Raises:
        ErrorFase2: Para errores específicos durante el procesamiento de la fase.
    """
    logger.info(f"Iniciando Fase 2: Extracción para fragmento ID: {resultado_fase_1.id_fragmento}")
    
    # Verificar que hay texto para procesar
    if not resultado_fase_1.texto_para_siguiente_fase or not resultado_fase_1.texto_para_siguiente_fase.strip():
        logger.warning(f"No hay texto para procesar en Fase 2 para fragmento {resultado_fase_1.id_fragmento}")
        # Retornar resultado vacío
        resultado_vacio = ResultadoFase2Extraccion(
            id_fragmento=resultado_fase_1.id_fragmento,
            hechos_extraidos=[],
            entidades_extraidas=[],
            advertencias_extraccion=["No se proporcionó texto para procesar"]
        )
        resultado_vacio.touch()
        return resultado_vacio
    
    # Configuración de Groq
    groq_config = _get_groq_config()
    groq_config_with_id = {**groq_config, "article_id": str(resultado_fase_1.id_fragmento)}
    
    if not groq_config.get("api_key"):
        logger.error(f"No se encontró GROQ_API_KEY. No se puede procesar fragmento {resultado_fase_1.id_fragmento}")
        # Aplicar fallback
        error_dict = handle_generic_phase_error(
            article_id=str(resultado_fase_1.id_fragmento),
            phase=ErrorPhase.FASE_2_EXTRACCION,
            step_failed="Configuración API",
            exception=RuntimeError("GROQ_API_KEY no configurada")
        )
        
        resultado_fallback = ResultadoFase2Extraccion(
            id_fragmento=resultado_fase_1.id_fragmento,
            hechos_extraidos=[],
            entidades_extraidas=[],
            advertencias_extraccion=[error_dict["message"]]
        )
        resultado_fallback.touch()
        return resultado_fallback
    
    # Variables para el procesamiento
    prompt_formateado = None
    respuesta_llm_cruda = None
    hechos_extraidos = []
    entidades_extraidas = []
    advertencias = []
    
    try:
        # Preparar contexto del documento (usar valores por defecto si no están disponibles)
        titulo_documento = "Fragmento de documento"
        fuente_tipo = "Documento procesado"
        pais_origen = "No especificado"
        fecha_fuente = datetime.now().strftime("%Y-%m-%d")
        
        # Si tenemos metadatos de la fase 1, intentar extraer información adicional
        if resultado_fase_1.metadatos_specificos_triaje:
            # Podríamos tener información adicional aquí
            pass
        
        # ✅ SANITIZAR TEXTO ANTES DE ENVIAR A GROQ
        texto_sanitizado_para_llm = escape_html(resultado_fase_1.texto_para_siguiente_fase)
        
        # Llamar a Groq API para extracción
        prompt_formateado, respuesta_llm_cruda = _llamar_groq_api_extraccion(
            config=groq_config_with_id,
            texto_contenido=texto_sanitizado_para_llm,
            titulo_documento=titulo_documento,
            fuente_tipo=fuente_tipo,
            pais_origen=pais_origen,
            fecha_fuente=fecha_fuente
        )
        
        logger.trace(f"Respuesta LLM (cruda) para extracción de {resultado_fase_1.id_fragmento}:\n{respuesta_llm_cruda}")
        
        # Parsear respuesta JSON
        try:
            respuesta_json = json.loads(respuesta_llm_cruda)
        except json.JSONDecodeError as e:
            logger.error(f"Error al parsear JSON de respuesta LLM: {e}")
            raise ProcessingError(
                message=f"Respuesta LLM no es JSON válido: {str(e)}",
                phase=ErrorPhase.FASE_2_EXTRACCION,
                processing_step="Parseo JSON",
                article_id=str(resultado_fase_1.id_fragmento)
            )
        
        # ✅ VALIDAR ESTRUCTURA JSON
        if not isinstance(respuesta_json, dict):
            raise ProcessingError(
                message="Respuesta JSON debe ser un objeto/diccionario",
                phase=ErrorPhase.FASE_2_EXTRACCION,
                processing_step="Validación estructura JSON",
                article_id=str(resultado_fase_1.id_fragmento)
            )
        
        # Validar que contenga las claves esperadas
        if 'hechos' not in respuesta_json and 'entidades' not in respuesta_json:
            logger.warning(f"Respuesta JSON no contiene 'hechos' ni 'entidades' para fragmento {resultado_fase_1.id_fragmento}")
            respuesta_json['hechos'] = []
            respuesta_json['entidades'] = []
        
        # ✅ Parsear hechos usando el processor
        hechos_extraidos = _parsear_hechos_from_json(
            respuesta_json, 
            resultado_fase_1.id_fragmento,
            processor  # ✅ Pasar processor
        )
        
        # ✅ Parsear entidades usando el processor
        entidades_extraidas = _parsear_entidades_from_json(
            respuesta_json, 
            resultado_fase_1.id_fragmento,
            processor  # ✅ Pasar processor
        )
        
        # ✅ Logging de processor para debugging
        processor.log_summary()
        
        # Generar resumen si no hay elementos extraídos
        if not hechos_extraidos and not entidades_extraidas:
            advertencias.append("No se extrajeron hechos ni entidades del texto")
            logger.warning(f"No se extrajeron elementos del fragmento {resultado_fase_1.id_fragmento}")
        
    except GroqAPIError as e:
        logger.error(f"GroqAPIError durante extracción para {resultado_fase_1.id_fragmento}: {e}")
        error_dict = handle_generic_phase_error(
            article_id=str(resultado_fase_1.id_fragmento),
            phase=ErrorPhase.FASE_2_EXTRACCION,
            step_failed="Llamada Groq API",
            exception=e
        )
        advertencias.append(error_dict["message"])
        
    except Exception as e:
        logger.error(f"Error inesperado durante extracción para {resultado_fase_1.id_fragmento}: {e}")
        error_dict = handle_generic_phase_error(
            article_id=str(resultado_fase_1.id_fragmento),
            phase=ErrorPhase.FASE_2_EXTRACCION,
            step_failed="Procesamiento general",
            exception=e
        )
        advertencias.append(error_dict["message"])
    
    # Crear metadata de extracción
    metadata_extraccion = {
        "modelo_usado": groq_config.get("model_id", "desconocido"),
        "tokens_prompt": len(prompt_formateado.split()) if prompt_formateado else 0,
        "tokens_respuesta": len(respuesta_llm_cruda.split()) if respuesta_llm_cruda else 0,
        "num_hechos_extraidos": len(hechos_extraidos),
        "num_entidades_extraidas": len(entidades_extraidas),
        "timestamp_extraccion": datetime.now().isoformat(),
        "ids_secuenciales": True  # ✅ Indicador de que usa IDs secuenciales
    }
    
    # Ensamblar resultado final
    resultado = ResultadoFase2Extraccion(
        id_fragmento=resultado_fase_1.id_fragmento,
        hechos_extraidos=hechos_extraidos,
        entidades_extraidas=entidades_extraidas,
        resumen_extraccion=f"Extraídos {len(hechos_extraidos)} hechos y {len(entidades_extraidas)} entidades con IDs secuenciales",
        prompt_extraccion_usado=prompt_formateado,
        advertencias_extraccion=advertencias,
        metadata_extraccion=metadata_extraccion
    )
    
    resultado.touch()
    
    logger.info(
        f"Fase 2: Extracción completada para fragmento ID: {resultado_fase_1.id_fragmento}. "
        f"Hechos: {len(hechos_extraidos)}, Entidades: {len(entidades_extraidas)}"
    )
    
    return resultado

# ✅ TEST BÁSICO PARA VERIFICAR LA IMPLEMENTACIÓN
if __name__ == "__main__":
    from uuid import uuid4
    from ..utils.fragment_processor import FragmentProcessor
    
    # Test básico
    test_fragmento = uuid4()
    processor = FragmentProcessor(test_fragmento)
    
    # Mock resultado fase 1
    resultado_fase1_mock = ResultadoFase1Triaje(
        id_fragmento=test_fragmento,
        es_relevante=True,
        texto_para_siguiente_fase="Pedro Sánchez anunció nuevas medidas económicas en España."
    )
    
    try:
        # Test fase 2
        resultado = ejecutar_fase_2(resultado_fase1_mock, processor)
        print(f"✅ Test exitoso: {len(resultado.hechos_extraidos)} hechos, {len(resultado.entidades_extraidas)} entidades")
        print(f"✅ Processor summary:")
        processor.log_summary()
    except Exception as e:
        print(f"❌ Error en test: {e}")
