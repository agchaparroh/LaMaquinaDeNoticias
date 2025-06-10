from typing import Optional, List, Dict, Any
from uuid import UUID
import os
import json
from pathlib import Path
from datetime import datetime

# ✅ IMPORTAR FRAGMENT PROCESSOR
from ..utils.fragment_processor import FragmentProcessor

# Importar modelos de resultado de la fase 3 desde el módulo de modelos
from ..models.procesamiento import (
    ResultadoFase3CitasDatos,
    CitaTextual,
    DatosCuantitativos,
    ResultadoFase2Extraccion,
    ResultadoFase1Triaje  # Necesario para acceder al texto original
)
from ..models.metadatos import MetadatosCita, MetadatosDato, PeriodoReferencia

# Importar funciones de validación
from ..utils.validation import (
    escape_html,
    validate_date_optional,
    validate_numeric_value
)

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

# --- Funciones auxiliares para la Fase 3 ---

_PROMPT_CITAS_DATOS_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "Prompt_3_citas_datos.md"
_PROMPT_CITAS_DATOS_TEMPLATE: Optional[str] = None

class ErrorFase3(Exception):
    """Excepción base para errores específicos de la Fase 3."""
    pass

def _load_prompt_template() -> str:
    """Carga la plantilla del prompt para extracción de citas y datos cuantitativos."""
    global _PROMPT_CITAS_DATOS_TEMPLATE
    if _PROMPT_CITAS_DATOS_TEMPLATE is None:
        try:
            with open(_PROMPT_CITAS_DATOS_PATH, "r", encoding="utf-8") as f:
                _PROMPT_CITAS_DATOS_TEMPLATE = f.read()
            logger.info(f"Plantilla de prompt de citas y datos cargada desde: {_PROMPT_CITAS_DATOS_PATH}")
        except FileNotFoundError:
            logger.error(f"No se encontró el archivo de prompt de citas y datos en: {_PROMPT_CITAS_DATOS_PATH}")
            raise ErrorFase3(f"Archivo de prompt de citas y datos no encontrado: {_PROMPT_CITAS_DATOS_PATH}")
        except Exception as e:
            logger.error(f"Error al cargar el prompt de citas y datos: {e}")
            raise ErrorFase3(f"Error cargando prompt de citas y datos: {e}")
    return _PROMPT_CITAS_DATOS_TEMPLATE

def _get_groq_config() -> Dict[str, Any]:
    """Carga la configuración para la API de Groq desde variables de entorno."""
    return {
        "api_key": os.getenv("GROQ_API_KEY"),
        "model_id": os.getenv("GROQ_MODEL_ID", "mixtral-8x7b-32768"),
        "timeout": float(os.getenv("GROQ_API_TIMEOUT", "30.0")),
        "temperature": float(os.getenv("GROQ_API_TEMPERATURE", "0.1")),
        "max_tokens": int(os.getenv("GROQ_API_MAX_TOKENS", "3000")),  # Más tokens para análisis complejo
        "max_retries": int(os.getenv("GROQ_MAX_RETRIES", "3")),
        "max_wait_seconds": int(os.getenv("GROQ_MAX_WAIT_SECONDS", "60")),
    }

def _formatear_json_paso_1(resultado_fase_2: ResultadoFase2Extraccion) -> str:
    """
    Formatea los resultados de fase 2 como JSON_PASO_1 para el prompt.
    CRÍTICO: Preserva los IDs secuenciales exactos sin modificación.
    
    Args:
        resultado_fase_2: Resultado de la fase 2 con hechos y entidades extraídos
        
    Returns:
        JSON string formateado con la estructura esperada por el prompt
    """
    logger.debug(f"Formateando JSON_PASO_1 para fragmento {resultado_fase_2.id_fragmento}")
    
    # Crear estructura de hechos preservando IDs secuenciales
    hechos_json = []
    for hecho in resultado_fase_2.hechos_extraidos:
        hecho_dict = {
            "id": hecho.id_hecho,  # ✅ ID secuencial preservado
            "contenido": hecho.texto_original_del_hecho,
            "tipo": hecho.metadata_hecho.tipo_hecho if hecho.metadata_hecho else None
        }
        hechos_json.append(hecho_dict)
    
    # Crear estructura de entidades preservando IDs secuenciales
    entidades_json = []
    for entidad in resultado_fase_2.entidades_extraidas:
        entidad_dict = {
            "id": entidad.id_entidad,  # ✅ ID secuencial preservado
            "nombre": entidad.texto_entidad,
            "tipo": entidad.tipo_entidad
        }
        entidades_json.append(entidad_dict)
    
    # Construir JSON_PASO_1
    json_paso_1 = {
        "hechos": hechos_json,
        "entidades": entidades_json
    }
    
    json_string = json.dumps(json_paso_1, ensure_ascii=False, indent=2)
    logger.trace(f"JSON_PASO_1 formateado: {json_string[:500]}...")
    
    return json_string

@retry_groq_api()
def _llamar_groq_api_citas_datos(
    config: Dict[str, Any],
    texto_contenido: str,
    json_paso_1: str,
    titulo_documento: str = "No disponible",
    fuente_tipo: str = "No disponible",
    fecha_fuente: str = "No disponible"
) -> tuple[str, str]:
    """
    Llama a la API de Groq para extracción de citas y datos cuantitativos.
    Retries son manejados por @retry_groq_api.
    Levanta GroqAPIError en caso de fallo persistente o configuración incorrecta.
    """
    article_id_log = config.get("article_id", "N/A")
    if not Groq:
        logger.error(f"SDK de Groq no instalado. Artículo: {article_id_log}")
        raise GroqAPIError("SDK de Groq no instalado.", phase=ErrorPhase.FASE_3_CITAS_DATOS, article_id=config.get("article_id"))
    if not config.get("api_key"):
        logger.error(f"GROQ_API_KEY no configurada. Artículo: {article_id_log}")
        raise GroqAPIError("GROQ_API_KEY no configurada.", phase=ErrorPhase.FASE_3_CITAS_DATOS, article_id=config.get("article_id"))

    try:
        prompt_template = _load_prompt_template()
    except ErrorFase3 as e_prompt:
        logger.error(f"Fallo al cargar plantilla de prompt para citas y datos. Artículo: {article_id_log}. Error: {e_prompt}")
        raise GroqAPIError(f"Fallo al cargar plantilla de prompt para citas y datos: {e_prompt}", phase=ErrorPhase.FASE_3_CITAS_DATOS, article_id=config.get("article_id")) from e_prompt

    # Formatear el prompt con las variables
    prompt_formateado = prompt_template.replace("{{TITULO_O_DOCUMENTO}}", titulo_documento)\
                                     .replace("{{FUENTE_O_TIPO}}", fuente_tipo)\
                                     .replace("{{FECHA_FUENTE}}", fecha_fuente)\
                                     .replace("{{CONTENIDO}}", texto_contenido)\
                                     .replace("{{JSON_PASO_1}}", json_paso_1)

    client = Groq(api_key=config["api_key"], timeout=config["timeout"])

    logger.info(f"Enviando solicitud a Groq API para citas y datos (modelo: {config['model_id']}). Artículo: {article_id_log}")
    
    # Agregar instrucción para obtener solo JSON
    system_prompt = "Eres un asistente especializado en extracción de citas textuales y datos cuantitativos. Responde ÚNICAMENTE con el JSON solicitado, sin texto adicional, sin markdown, sin explicaciones."
    
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
        logger.warning(f"Groq API para citas y datos devolvió una respuesta vacía. Artículo: {article_id_log}")
        raise GroqAPIError("Respuesta vacía de Groq API para citas y datos.", phase=ErrorPhase.FASE_3_CITAS_DATOS, article_id=config.get("article_id"))
    
    logger.info(f"Respuesta recibida de Groq API para citas y datos. Artículo: {article_id_log}")
    return prompt_formateado, respuesta_contenido

def _parsear_citas_textuales_from_json(
    response_json: Dict[str, Any],
    id_fragmento_origen: UUID,
    processor: FragmentProcessor
) -> List[CitaTextual]:
    """
    Parsea las citas textuales desde la respuesta JSON del LLM y las convierte a CitaTextual.
    SOLUCIÓN ARQUITECTÓNICA: Usa IDs secuenciales del JSON, no genera UUIDs.
    """
    citas_procesadas = []
    citas_raw = response_json.get("citas_textuales", [])
    ids_vistos = set()  # Para validar duplicados
    
    logger.debug(f"Parseando {len(citas_raw)} citas del JSON para fragmento {id_fragmento_origen}")
    
    for cita_raw in citas_raw:
        try:
            # ✅ Usar el ID del JSON (que ya es secuencial)
            id_cita_json = cita_raw.get("id", 1)
            
            # Validar duplicados
            if id_cita_json in ids_vistos:
                logger.warning(f"ID duplicado {id_cita_json} en citas, saltando...")
                continue
            ids_vistos.add(id_cita_json)
            
            # ✅ Registrar en el processor para validación
            descripcion_cita = cita_raw.get("cita", "")[:50]  # Primeros 50 chars para debug
            id_cita_registrado = processor.next_cita_id(descripcion_cita)
            
            # ✅ Validar consistencia
            if id_cita_json != id_cita_registrado:
                logger.warning(
                    f"Inconsistencia de ID cita: JSON={id_cita_json}, "
                    f"Processor={id_cita_registrado}. Usando ID del JSON."
                )
            
            # Extraer persona citada desde entidad_id si está disponible
            persona_citada = None
            id_entidad_citada = cita_raw.get("entidad_id")
            
            # Validar y sanitizar fecha
            fecha_cita = None
            try:
                fecha_cita = validate_date_optional(cita_raw.get("fecha"))
            except ValueError as e:
                logger.warning(f"Fecha inválida en cita {id_cita_json}: {e}")
            
            # Sanitizar contexto
            contexto_sanitizado = escape_html(cita_raw.get("contexto", "")) if cita_raw.get("contexto") else None
            
            # Crear metadatos de la cita usando MetadatosCita
            metadata_cita = MetadatosCita(
                fecha=fecha_cita,
                contexto=contexto_sanitizado,
                relevancia=cita_raw.get("relevancia", 3)
            )
            
            # Sanitizar texto de la cita
            texto_cita_sanitizado = escape_html(cita_raw.get("cita", ""))
            
            # Crear CitaTextual con ID secuencial
            cita_procesada = CitaTextual(
                id_cita=id_cita_json,  # ✅ int secuencial del JSON
                id_fragmento_origen=id_fragmento_origen,
                texto_cita=texto_cita_sanitizado,
                persona_citada=persona_citada,  # Se puede enriquecer después
                id_entidad_citada=id_entidad_citada,  # ✅ ID secuencial de fase 2
                metadata_cita=metadata_cita,
                # Almacenar hecho_id en respuesta_llm_bruta
                respuesta_llm_bruta={
                    "hecho_id": cita_raw.get("hecho_id"),
                    "cita_original": cita_raw
                }
            )
            
            citas_procesadas.append(cita_procesada)
            logger.trace(f"Cita procesada: ID {cita_procesada.id_cita}, Relevancia: {metadata_cita.relevancia}")
            
        except Exception as e:
            logger.warning(f"Error al parsear cita {cita_raw.get('id', 'N/A')}: {e}")
            continue
    
    logger.info(f"Parseadas {len(citas_procesadas)} citas exitosamente para fragmento {id_fragmento_origen}")
    return citas_procesadas

def _parsear_datos_cuantitativos_from_json(
    response_json: Dict[str, Any],
    id_fragmento_origen: UUID,
    processor: FragmentProcessor
) -> List[DatosCuantitativos]:
    """
    Parsea los datos cuantitativos desde la respuesta JSON del LLM y los convierte a DatosCuantitativos.
    SOLUCIÓN ARQUITECTÓNICA: Usa IDs secuenciales del JSON, no genera UUIDs.
    """
    datos_procesados = []
    datos_raw = response_json.get("datos_cuantitativos", [])
    ids_vistos = set()  # Para validar duplicados
    
    logger.debug(f"Parseando {len(datos_raw)} datos cuantitativos del JSON para fragmento {id_fragmento_origen}")
    
    for dato_raw in datos_raw:
        try:
            # ✅ Usar el ID del JSON (que ya es secuencial)
            id_dato_json = dato_raw.get("id", 1)
            
            # Validar duplicados
            if id_dato_json in ids_vistos:
                logger.warning(f"ID duplicado {id_dato_json} en datos cuantitativos, saltando...")
                continue
            ids_vistos.add(id_dato_json)
            
            # ✅ Registrar en el processor para validación
            descripcion_dato = dato_raw.get("indicador", "")[:50]
            id_dato_registrado = processor.next_dato_id(descripcion_dato)
            
            # ✅ Validar consistencia
            if id_dato_json != id_dato_registrado:
                logger.warning(
                    f"Inconsistencia de ID dato: JSON={id_dato_json}, "
                    f"Processor={id_dato_registrado}. Usando ID del JSON."
                )
            
            # Procesar periodo con validación de fechas
            periodo_raw = dato_raw.get("periodo", {})
            periodo_obj = None
            if periodo_raw and (periodo_raw.get("inicio") or periodo_raw.get("fin")):
                try:
                    fecha_inicio = validate_date_optional(periodo_raw.get("inicio"))
                    fecha_fin = validate_date_optional(periodo_raw.get("fin"))
                    
                    # Validar coherencia del periodo
                    if fecha_inicio and fecha_fin:
                        from datetime import datetime
                        if datetime.strptime(fecha_inicio, "%Y-%m-%d") > datetime.strptime(fecha_fin, "%Y-%m-%d"):
                            logger.warning(f"Periodo inválido en dato {id_dato_json}: fecha inicio posterior a fecha fin")
                            fecha_inicio, fecha_fin = fecha_fin, fecha_inicio  # Intercambiar
                    
                    periodo_obj = PeriodoReferencia(
                        inicio=fecha_inicio,
                        fin=fecha_fin
                    )
                except ValueError as e:
                    logger.warning(f"Error validando periodo en dato {id_dato_json}: {e}")
            
            # Crear metadatos del dato usando MetadatosDato
            metadata_dato = MetadatosDato(
                categoria=dato_raw.get("categoria"),
                tipo_periodo=dato_raw.get("tipo_periodo"),
                tendencia=dato_raw.get("tendencia"),
                valor_anterior=dato_raw.get("valor_anterior"),
                variacion_absoluta=dato_raw.get("variacion_absoluta"),
                variacion_porcentual=dato_raw.get("variacion_porcentual"),
                ambito_geografico=dato_raw.get("ambito_geografico", []),
                periodo=periodo_obj
            )
            
            # Formatear fecha_dato desde periodo si existe
            fecha_dato = None
            if periodo_obj:
                if periodo_obj.inicio and periodo_obj.fin:
                    fecha_dato = f"{periodo_obj.inicio} - {periodo_obj.fin}"
                elif periodo_obj.inicio:
                    fecha_dato = periodo_obj.inicio
                elif periodo_obj.fin:
                    fecha_dato = periodo_obj.fin
            
            # Validar valor numérico
            valor_numerico = 0.0
            try:
                valor_numerico = validate_numeric_value(dato_raw.get("valor", 0))
            except ValueError as e:
                logger.warning(f"Valor numérico inválido en dato {id_dato_json}: {e}")
            
            # Sanitizar descripción y unidad
            descripcion_sanitizada = escape_html(dato_raw.get("indicador", ""))
            unidad_sanitizada = escape_html(dato_raw.get("unidad", "")) if dato_raw.get("unidad") else None
            
            # Crear DatosCuantitativos con ID secuencial
            dato_procesado = DatosCuantitativos(
                id_dato_cuantitativo=id_dato_json,  # ✅ int secuencial del JSON
                id_fragmento_origen=id_fragmento_origen,
                descripcion_dato=descripcion_sanitizada,
                valor_dato=valor_numerico,
                unidad_dato=unidad_sanitizada,
                fecha_dato=fecha_dato,
                metadata_dato=metadata_dato,
                # Almacenar hecho_id en respuesta_llm_bruta
                respuesta_llm_bruta={
                    "hecho_id": dato_raw.get("hecho_id"),
                    "dato_original": dato_raw
                }
            )
            
            datos_procesados.append(dato_procesado)
            logger.trace(f"Dato procesado: ID {dato_procesado.id_dato_cuantitativo}, Categoría: {metadata_dato.categoria}")
            
        except Exception as e:
            logger.warning(f"Error al parsear dato cuantitativo {dato_raw.get('id', 'N/A')}: {e}")
            continue
    
    logger.info(f"Parseados {len(datos_procesados)} datos cuantitativos exitosamente para fragmento {id_fragmento_origen}")
    return datos_procesados

def ejecutar_fase_3(
    resultado_fase_2: ResultadoFase2Extraccion,
    processor: FragmentProcessor,
    resultado_fase_1: Optional[ResultadoFase1Triaje] = None
) -> ResultadoFase3CitasDatos:
    """
    Ejecuta la Fase 3: Extracción de Citas y Datos Cuantitativos.
    Extrae citas textuales y datos numéricos del texto, manteniendo referencias
    a los hechos y entidades identificados en la fase 2.
    
    SOLUCIÓN ARQUITECTÓNICA: Usa FragmentProcessor para mantener IDs secuenciales
    coherentes a través de todas las fases del pipeline.

    Args:
        resultado_fase_2: El resultado de la Fase 2 con hechos y entidades extraídos.
        processor: FragmentProcessor para gestión de IDs secuenciales.
        resultado_fase_1: Opcional. Resultado de la Fase 1 para acceder al texto original.

    Returns:
        Un objeto ResultadoFase3CitasDatos con las citas y datos extraídos.

    Raises:
        ErrorFase3: Para errores específicos durante el procesamiento de la fase.
    """
    logger.info(f"Iniciando Fase 3: Citas y Datos para fragmento ID: {resultado_fase_2.id_fragmento}")
    
    # Verificar que hay elementos para procesar
    if not resultado_fase_2.hechos_extraidos and not resultado_fase_2.entidades_extraidas:
        logger.warning(f"No hay hechos ni entidades para procesar en Fase 3 para fragmento {resultado_fase_2.id_fragmento}")
        # Retornar resultado vacío
        resultado_vacio = ResultadoFase3CitasDatos(
            id_fragmento=resultado_fase_2.id_fragmento,
            citas_textuales_extraidas=[],
            datos_cuantitativos_extraidos=[],
            advertencias_citas_datos=["No se encontraron elementos previos para análisis"]
        )
        resultado_vacio.touch()
        return resultado_vacio
    
    # Formatear JSON_PASO_1 preservando IDs secuenciales
    json_paso_1 = _formatear_json_paso_1(resultado_fase_2)
    
    # Configuración de Groq
    groq_config = _get_groq_config()
    groq_config_with_id = {**groq_config, "article_id": str(resultado_fase_2.id_fragmento)}
    
    if not groq_config.get("api_key"):
        logger.error(f"No se encontró GROQ_API_KEY. No se puede procesar fragmento {resultado_fase_2.id_fragmento}")
        # Aplicar fallback
        error_dict = handle_generic_phase_error(
            article_id=str(resultado_fase_2.id_fragmento),
            phase=ErrorPhase.FASE_3_CITAS_DATOS,
            step_failed="Configuración API",
            exception=RuntimeError("GROQ_API_KEY no configurada")
        )
        
        resultado_fallback = ResultadoFase3CitasDatos(
            id_fragmento=resultado_fase_2.id_fragmento,
            citas_textuales_extraidas=[],
            datos_cuantitativos_extraidos=[],
            advertencias_citas_datos=[error_dict["message"]]
        )
        resultado_fallback.touch()
        return resultado_fallback
    
    # Variables para el procesamiento
    prompt_formateado = None
    respuesta_llm_cruda = None
    citas_extraidas = []
    datos_extraidos = []
    advertencias = []
    
    try:
        # Obtener texto original 
        texto_contenido = "[TEXTO ORIGINAL NO DISPONIBLE]"  # Default
        
        # Intentar obtener texto desde resultado_fase_1 si está disponible
        if resultado_fase_1 and resultado_fase_1.texto_para_siguiente_fase:
            texto_contenido = resultado_fase_1.texto_para_siguiente_fase
            logger.debug(f"Usando texto original de fase 1 para fragmento {resultado_fase_2.id_fragmento}")
        else:
            # Como fallback, podríamos reconstruir desde los hechos
            logger.warning(
                f"resultado_fase_1 no proporcionado para fragmento {resultado_fase_2.id_fragmento}. "
                "Usando placeholder para texto original."
            )
            advertencias.append("Texto original no disponible, usando placeholder")
        
        # Preparar contexto del documento
        titulo_documento = "Fragmento de documento"
        fuente_tipo = "Documento procesado"
        fecha_fuente = datetime.now().strftime("%Y-%m-%d")
        
        # Si tenemos metadatos adicionales de fase 1, usarlos
        if resultado_fase_1 and resultado_fase_1.metadatos_specificos_triaje:
            # Podríamos extraer más información aquí si estuviera disponible
            pass
        
        # Llamar a Groq API para extracción
        prompt_formateado, respuesta_llm_cruda = _llamar_groq_api_citas_datos(
            config=groq_config_with_id,
            texto_contenido=texto_contenido,
            json_paso_1=json_paso_1,
            titulo_documento=titulo_documento,
            fuente_tipo=fuente_tipo,
            fecha_fuente=fecha_fuente
        )
        
        logger.trace(f"Respuesta LLM (cruda) para citas y datos de {resultado_fase_2.id_fragmento}:\n{respuesta_llm_cruda}")
        
        # Parsear respuesta JSON
        try:
            respuesta_json = json.loads(respuesta_llm_cruda)
        except json.JSONDecodeError as e:
            logger.error(f"Error al parsear JSON de respuesta LLM: {e}")
            raise ProcessingError(
                message=f"Respuesta LLM no es JSON válido: {str(e)}",
                phase=ErrorPhase.FASE_3_CITAS_DATOS,
                processing_step="Parseo JSON",
                article_id=str(resultado_fase_2.id_fragmento)
            )
        
        # ✅ Parsear citas usando el processor
        citas_extraidas = _parsear_citas_textuales_from_json(
            respuesta_json,
            resultado_fase_2.id_fragmento,
            processor  # ✅ Pasar processor
        )
        
        # ✅ Parsear datos cuantitativos usando el processor
        datos_extraidos = _parsear_datos_cuantitativos_from_json(
            respuesta_json,
            resultado_fase_2.id_fragmento,
            processor  # ✅ Pasar processor
        )
        
        # ✅ Logging de processor para debugging
        processor.log_summary()
        
        # Validar referencias cruzadas
        ids_entidades_fase2 = {e.id_entidad for e in resultado_fase_2.entidades_extraidas}
        ids_hechos_fase2 = {h.id_hecho for h in resultado_fase_2.hechos_extraidos}
        
        # Validar citas
        for cita in citas_extraidas:
            if cita.id_entidad_citada and cita.id_entidad_citada not in ids_entidades_fase2:
                advertencias.append(f"Cita {cita.id_cita} referencia entidad inexistente: {cita.id_entidad_citada}")
            # Validar hecho_id desde respuesta_llm_bruta
            hecho_id = cita.respuesta_llm_bruta.get("hecho_id") if cita.respuesta_llm_bruta else None
            if hecho_id and hecho_id not in ids_hechos_fase2:
                advertencias.append(f"Cita {cita.id_cita} referencia hecho inexistente: {hecho_id}")
        
        # Validar datos cuantitativos
        for dato in datos_extraidos:
            # Validar hecho_id desde respuesta_llm_bruta
            hecho_id = dato.respuesta_llm_bruta.get("hecho_id") if dato.respuesta_llm_bruta else None
            if hecho_id and hecho_id not in ids_hechos_fase2:
                advertencias.append(f"Dato {dato.id_dato_cuantitativo} referencia hecho inexistente: {hecho_id}")
        
        # Generar resumen si no hay elementos extraídos
        if not citas_extraidas and not datos_extraidos:
            advertencias.append("No se extrajeron citas ni datos cuantitativos del texto")
            logger.warning(f"No se extrajeron elementos del fragmento {resultado_fase_2.id_fragmento}")
        
    except GroqAPIError as e:
        logger.error(f"GroqAPIError durante extracción de citas y datos para {resultado_fase_2.id_fragmento}: {e}")
        error_dict = handle_generic_phase_error(
            article_id=str(resultado_fase_2.id_fragmento),
            phase=ErrorPhase.FASE_3_CITAS_DATOS,
            step_failed="Llamada Groq API",
            exception=e
        )
        advertencias.append(error_dict["message"])
        
    except Exception as e:
        logger.error(f"Error inesperado durante extracción de citas y datos para {resultado_fase_2.id_fragmento}: {e}")
        error_dict = handle_generic_phase_error(
            article_id=str(resultado_fase_2.id_fragmento),
            phase=ErrorPhase.FASE_3_CITAS_DATOS,
            step_failed="Procesamiento general",
            exception=e
        )
        advertencias.append(error_dict["message"])
    
    # Crear metadata de extracción
    metadata_citas_datos = {
        "modelo_usado": groq_config.get("model_id", "desconocido"),
        "tokens_prompt": len(prompt_formateado.split()) if prompt_formateado else 0,
        "tokens_respuesta": len(respuesta_llm_cruda.split()) if respuesta_llm_cruda else 0,
        "num_citas_extraidas": len(citas_extraidas),
        "num_datos_extraidos": len(datos_extraidos),
        "timestamp_extraccion": datetime.now().isoformat(),
        "ids_secuenciales": True,  # ✅ Indicador de que usa IDs secuenciales
        "json_paso_1_elementos": len(resultado_fase_2.hechos_extraidos) + len(resultado_fase_2.entidades_extraidas),
        "texto_original_disponible": resultado_fase_1 is not None
    }
    
    # Ensamblar resultado final
    resultado = ResultadoFase3CitasDatos(
        id_fragmento=resultado_fase_2.id_fragmento,
        citas_textuales_extraidas=citas_extraidas,
        datos_cuantitativos_extraidos=datos_extraidos,
        prompt_citas_datos_usado=prompt_formateado,
        advertencias_citas_datos=advertencias,
        metadata_citas_datos=metadata_citas_datos
    )
    
    resultado.touch()
    
    logger.info(
        f"Fase 3: Extracción de citas y datos completada para fragmento ID: {resultado_fase_2.id_fragmento}. "
        f"Citas: {len(citas_extraidas)}, Datos: {len(datos_extraidos)}"
    )
    
    return resultado

# ✅ TEST BÁSICO PARA VERIFICAR LA IMPLEMENTACIÓN
if __name__ == "__main__":
    from uuid import uuid4
    from ..utils.fragment_processor import FragmentProcessor
    from ..models.procesamiento import HechoProcesado, EntidadProcesada
    from ..models.metadatos import MetadatosHecho, MetadatosEntidad
    
    # Test básico
    test_fragmento = uuid4()
    processor = FragmentProcessor(test_fragmento)
    
    # Mock resultado fase 2 con datos de prueba
    hechos_mock = [
        HechoProcesado(
            id_hecho=1,
            texto_original_del_hecho="El PIB creció un 3.5% en 2022",
            confianza_extraccion=0.9,
            id_fragmento_origen=test_fragmento,
            metadata_hecho=MetadatosHecho(tipo_hecho="ANUNCIO")
        )
    ]
    
    entidades_mock = [
        EntidadProcesada(
            id_entidad=1,
            texto_entidad="Ministra de Economía",
            tipo_entidad="PERSONA",
            relevancia_entidad=0.8,
            id_fragmento_origen=test_fragmento,
            metadata_entidad=MetadatosEntidad(tipo="PERSONA")
        )
    ]
    
    resultado_fase2_mock = ResultadoFase2Extraccion(
        id_fragmento=test_fragmento,
        hechos_extraidos=hechos_mock,
        entidades_extraidas=entidades_mock
    )
    
    # Mock resultado fase 1 con texto
    resultado_fase1_mock = ResultadoFase1Triaje(
        id_fragmento=test_fragmento,
        es_relevante=True,
        texto_para_siguiente_fase="El PIB creció un 3.5% en 2022 según anunció la Ministra de Economía."
    )
    
    try:
        # Test fase 3 con texto disponible
        resultado = ejecutar_fase_3(resultado_fase2_mock, processor, resultado_fase1_mock)
        print(f"✅ Test exitoso: {len(resultado.citas_textuales_extraidas)} citas, {len(resultado.datos_cuantitativos_extraidos)} datos")
        print(f"✅ Processor summary:")
        processor.log_summary()
    except Exception as e:
        print(f"❌ Error en test: {e}")
