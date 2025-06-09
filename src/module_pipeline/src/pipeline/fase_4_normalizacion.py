from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
import os
import json
from pathlib import Path
from datetime import datetime
import time

# ✅ IMPORTAR FRAGMENT PROCESSOR (SUBTAREA 6 - paso 1)
from ..utils.fragment_processor import FragmentProcessor

# Importar modelos de resultado de la fase 4 desde el módulo de modelos
from ..models.procesamiento import (
    ResultadoFase4Normalizacion,
    ResultadoFase1Triaje,
    ResultadoFase2Extraccion,
    ResultadoFase3CitasDatos,
    EntidadProcesada,
    HechoProcesado,
    CitaTextual,
    DatosCuantitativos
)

# Importar manejadores de errores y tipos necesarios
from ..utils.error_handling import (
    handle_generic_phase_error,
    ErrorPhase,
    retry_groq_api,
    GroqAPIError,
    ProcessingError,
    SupabaseRPCError,
    FallbackExecuted
)

# Importar servicio de normalización (SUBTAREA 2 - paso 1)
from ..services.entity_normalizer import NormalizadorEntidades
from ..services.supabase_service import SupabaseService

# Importar funciones de validación
from ..utils.validation import (
    escape_html,
    sanitize_entity_name,
    validate_date_optional,
    validate_wikidata_uri
)

# Importar servicio Groq
try:
    from groq import Groq
except ImportError:
    Groq = None

from loguru import logger

# --- Funciones auxiliares para la Fase 4 ---

_PROMPT_RELACIONES_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "Prompt_4_relaciones.md"
_PROMPT_RELACIONES_TEMPLATE: Optional[str] = None

class ErrorFase4(Exception):
    """Excepción base para errores específicos de la Fase 4."""
    pass

# ============================================================================
# SUBTAREA 1 - Paso 1: Define ResultadoFase4 class
# Nota: Ya está definida en procesamiento.py, pero necesitamos estructuras adicionales
# ============================================================================

# Estructuras para almacenar relaciones (SUBTAREA 1 - paso 3)
class RelacionHechoEntidad:
    """Estructura para relaciones entre hechos y entidades."""
    def __init__(
        self, 
        hecho_id: int, 
        entidad_id: int, 
        tipo_relacion: str, 
        relevancia_en_hecho: int
    ):
        self.hecho_id = hecho_id
        self.entidad_id = entidad_id
        self.tipo_relacion = tipo_relacion
        self.relevancia_en_hecho = relevancia_en_hecho
        self.id_relacion = uuid4()  # ID único para la relación
        
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la relación a diccionario para serialización."""
        return {
            "id_relacion": str(self.id_relacion),
            "hecho_id": self.hecho_id,
            "entidad_id": self.entidad_id,
            "tipo_relacion": self.tipo_relacion,
            "relevancia_en_hecho": self.relevancia_en_hecho
        }

class RelacionHechoHecho:
    """Estructura para relaciones entre hechos."""
    def __init__(
        self,
        hecho_origen_id: int,
        hecho_destino_id: int,
        tipo_relacion: str,
        fuerza_relacion: int,
        descripcion_relacion: str
    ):
        self.hecho_origen_id = hecho_origen_id
        self.hecho_destino_id = hecho_destino_id
        self.tipo_relacion = tipo_relacion
        self.fuerza_relacion = fuerza_relacion
        self.descripcion_relacion = descripcion_relacion
        self.id_relacion = uuid4()
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id_relacion": str(self.id_relacion),
            "hecho_origen_id": self.hecho_origen_id,
            "hecho_destino_id": self.hecho_destino_id,
            "tipo_relacion": self.tipo_relacion,
            "fuerza_relacion": self.fuerza_relacion,
            "descripcion_relacion": self.descripcion_relacion
        }

class RelacionEntidadEntidad:
    """Estructura para relaciones entre entidades."""
    def __init__(
        self,
        entidad_origen_id: int,
        entidad_destino_id: int,
        tipo_relacion: str,
        descripcion: str,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
        fuerza_relacion: int = 5
    ):
        self.entidad_origen_id = entidad_origen_id
        self.entidad_destino_id = entidad_destino_id
        self.tipo_relacion = tipo_relacion
        self.descripcion = descripcion
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.fuerza_relacion = fuerza_relacion
        self.id_relacion = uuid4()
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id_relacion": str(self.id_relacion),
            "entidad_origen_id": self.entidad_origen_id,
            "entidad_destino_id": self.entidad_destino_id,
            "tipo_relacion": self.tipo_relacion,
            "descripcion": self.descripcion,
            "fecha_inicio": self.fecha_inicio,
            "fecha_fin": self.fecha_fin,
            "fuerza_relacion": self.fuerza_relacion
        }

class Contradiccion:
    """Estructura para contradicciones identificadas."""
    def __init__(
        self,
        hecho_principal_id: int,
        hecho_contradictorio_id: int,
        tipo_contradiccion: str,
        grado_contradiccion: int,
        descripcion: str
    ):
        self.hecho_principal_id = hecho_principal_id
        self.hecho_contradictorio_id = hecho_contradictorio_id
        self.tipo_contradiccion = tipo_contradiccion
        self.grado_contradiccion = grado_contradiccion
        self.descripcion = descripcion
        self.id_contradiccion = uuid4()
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id_contradiccion": str(self.id_contradiccion),
            "hecho_principal_id": self.hecho_principal_id,
            "hecho_contradictorio_id": self.hecho_contradictorio_id,
            "tipo_contradiccion": self.tipo_contradiccion,
            "grado_contradiccion": self.grado_contradiccion,
            "descripcion": self.descripcion
        }

# ============================================================================
# SUBTAREA 1 - Paso 2, 4, 5, 6: Funciones auxiliares
# ============================================================================

def _load_prompt_template() -> str:
    """Carga la plantilla del prompt para extracción de relaciones."""
    global _PROMPT_RELACIONES_TEMPLATE
    if _PROMPT_RELACIONES_TEMPLATE is None:
        try:
            with open(_PROMPT_RELACIONES_PATH, "r", encoding="utf-8") as f:
                _PROMPT_RELACIONES_TEMPLATE = f.read()
            logger.info(f"Plantilla de prompt de relaciones cargada desde: {_PROMPT_RELACIONES_PATH}")
        except FileNotFoundError:
            logger.error(f"No se encontró el archivo de prompt de relaciones en: {_PROMPT_RELACIONES_PATH}")
            raise ErrorFase4(f"Archivo de prompt de relaciones no encontrado: {_PROMPT_RELACIONES_PATH}")
        except Exception as e:
            logger.error(f"Error al cargar el prompt de relaciones: {e}")
            raise ErrorFase4(f"Error cargando prompt de relaciones: {e}")
    return _PROMPT_RELACIONES_TEMPLATE

def _get_groq_config() -> Dict[str, Any]:
    """Carga la configuración para la API de Groq desde variables de entorno."""
    return {
        "api_key": os.getenv("GROQ_API_KEY"),
        "model_id": os.getenv("GROQ_MODEL_ID", "mixtral-8x7b-32768"),
        "timeout": float(os.getenv("GROQ_API_TIMEOUT", "30.0")),
        "temperature": float(os.getenv("GROQ_API_TEMPERATURE", "0.1")),
        "max_tokens": int(os.getenv("GROQ_API_MAX_TOKENS", "4000")),  # Más tokens para análisis de relaciones
        "max_retries": int(os.getenv("GROQ_MAX_RETRIES", "3")),
        "max_wait_seconds": int(os.getenv("GROQ_MAX_WAIT_SECONDS", "60")),
    }

# ============================================================================
# SUBTAREA 2 - Implementar integración con EntityNormalizer
# ============================================================================

# Cache temporal para normalización (SUBTAREA 2 - paso 6)
_NORMALIZATION_CACHE: Dict[str, Dict[str, Any]] = {}

def _normalizar_entidades_extraidas(
    entidades: List[EntidadProcesada],
    supabase_service: Optional[SupabaseService] = None,
    umbral_similitud: float = 0.8
) -> List[EntidadProcesada]:
    """
    Normaliza las entidades extraídas usando el servicio EntityNormalizer.
    
    SUBTAREA 2 - pasos 8-16: Implementación completa de normalización
    SUBTAREA 7 - pasos 2-5: NO crear nuevos objetos, solo enriquecer existentes
    
    Args:
        entidades: Lista de entidades a normalizar
        supabase_service: Servicio de Supabase (opcional para testing)
        umbral_similitud: Umbral para considerar una entidad como match
        
    Returns:
        Lista de entidades enriquecidas con información de normalización
    """
    logger.info(f"Iniciando normalización de {len(entidades)} entidades")
    
    # Si no hay servicio de Supabase, retornar entidades sin modificar
    if not supabase_service:
        logger.warning("No hay servicio de Supabase disponible, saltando normalización")
        return entidades
    
    # Crear instancia del normalizador
    normalizador = NormalizadorEntidades(supabase_service)
    
    # Estadísticas para logging
    normalizadas = 0
    nuevas = 0
    errores = 0
    
    # SUBTAREA 2 - paso 11: Batch processing (aquí procesamos una por una pero con cache)
    for entidad in entidades:
        # Crear clave de cache
        cache_key = f"{entidad.texto_entidad}:{entidad.tipo_entidad}"
        
        # Verificar cache (SUBTAREA 2 - paso 12)
        if cache_key in _NORMALIZATION_CACHE:
            resultado = _NORMALIZATION_CACHE[cache_key]
            logger.trace(f"Usando resultado cacheado para '{entidad.texto_entidad}'")
        else:
            try:
                # Llamar al servicio de normalización
                resultado = normalizador.normalizar_entidad(
                    nombre_entidad=entidad.texto_entidad,
                    tipo_entidad=entidad.tipo_entidad,
                    umbral_propio=umbral_similitud,
                    limite_resultados_propio=1
                )
                
                # Guardar en cache
                _NORMALIZATION_CACHE[cache_key] = resultado
                
            except Exception as e:
                logger.error(f"Error al normalizar entidad '{entidad.texto_entidad}': {e}")
                errores += 1
                continue
        
        # SUBTAREA 2 - paso 9 y SUBTAREA 7 - paso 2: Actualizar EntidadProcesada existente
        if not resultado.get("es_nueva", True) and resultado.get("score_similitud", 0) > umbral_similitud:
            # Entidad encontrada y supera el umbral
            entidad.id_entidad_normalizada = UUID(str(resultado["id_entidad_normalizada"]))
            
            # Sanitizar nombre normalizado
            nombre_normalizado = sanitize_entity_name(resultado["nombre_normalizado"])
            entidad.nombre_entidad_normalizada = nombre_normalizado
            
            entidad.similitud_normalizacion = resultado["score_similitud"]
            
            # Validar URI de Wikidata si está disponible
            if resultado.get("uri_wikidata"):
                try:
                    uri_validada = validate_wikidata_uri(resultado["uri_wikidata"])
                    entidad.uri_wikidata = uri_validada
                except ValueError as e:
                    logger.warning(f"URI de Wikidata inválida para entidad '{entidad.texto_entidad}': {e}")
            
            normalizadas += 1
            
            logger.debug(
                f"Entidad '{entidad.texto_entidad}' normalizada a '{resultado['nombre_normalizado']}' "
                f"(ID: {resultado['id_entidad_normalizada']}, Score: {resultado['score_similitud']:.2f})"
            )
        else:
            # Entidad nueva o score bajo
            nuevas += 1
            logger.debug(
                f"Entidad '{entidad.texto_entidad}' considerada nueva "
                f"(Score: {resultado.get('score_similitud', 0):.2f})"
            )
    
    # SUBTAREA 2 - paso 13: Logging estructurado
    logger.info(
        f"Normalización completada: {normalizadas} normalizadas, {nuevas} nuevas, {errores} errores",
        extra={
            "total_entities": len(entidades),
            "normalized": normalizadas,
            "new": nuevas,
            "errors": errores,
            "cache_hits": len([k for k in _NORMALIZATION_CACHE if k in [f"{e.texto_entidad}:{e.tipo_entidad}" for e in entidades]])
        }
    )
    
    # SUBTAREA 2 - paso 16: Preservar integridad de la lista original
    return entidades

# ============================================================================
# SUBTAREA 3 - Implementar integración con Groq API para relaciones
# ============================================================================

def _formatear_elementos_para_prompt(
    resultado_fase_2: ResultadoFase2Extraccion,
    resultado_fase_3: ResultadoFase3CitasDatos
) -> Tuple[str, str]:
    """
    Formatea los elementos para el prompt de relaciones.
    
    CRÍTICO: Formatear ELEMENTOS_BASICOS_NORMALIZADOS y ELEMENTOS_COMPLEMENTARIOS
    según el formato esperado por Prompt_4_relaciones.md
    
    Returns:
        Tupla con (elementos_basicos_json, elementos_complementarios_json)
    """
    # Formatear ELEMENTOS_BASICOS_NORMALIZADOS
    hechos_json = []
    for hecho in resultado_fase_2.hechos_extraidos:
        hecho_dict = {
            "id": hecho.id_hecho,  # ID secuencial preservado
            "contenido": hecho.texto_original_del_hecho,
            "tipo": hecho.metadata_hecho.tipo_hecho if hecho.metadata_hecho else None
        }
        hechos_json.append(hecho_dict)
    
    entidades_json = []
    for entidad in resultado_fase_2.entidades_extraidas:
        entidad_dict = {
            "id": entidad.id_entidad,  # ID secuencial preservado
            "nombre": entidad.texto_entidad,
            "tipo": entidad.tipo_entidad,
            "normalizada": entidad.nombre_entidad_normalizada if entidad.id_entidad_normalizada else None,
            "id_normalizada": str(entidad.id_entidad_normalizada) if entidad.id_entidad_normalizada else None
        }
        entidades_json.append(entidad_dict)
    
    elementos_basicos = {
        "hechos": hechos_json,
        "entidades": entidades_json
    }
    
    # Formatear ELEMENTOS_COMPLEMENTARIOS
    citas_json = []
    for cita in resultado_fase_3.citas_textuales_extraidas:
        cita_dict = {
            "id": cita.id_cita,
            "texto": cita.texto_cita,
            "persona_citada": cita.persona_citada,
            "entidad_id": cita.id_entidad_citada,
            "contexto": cita.contexto_cita
        }
        citas_json.append(cita_dict)
    
    datos_json = []
    for dato in resultado_fase_3.datos_cuantitativos_extraidos:
        dato_dict = {
            "id": dato.id_dato_cuantitativo,
            "descripcion": dato.descripcion_dato,
            "valor": dato.valor_dato,
            "unidad": dato.unidad_dato,
            "fecha": dato.fecha_dato
        }
        datos_json.append(dato_dict)
    
    elementos_complementarios = {
        "citas_textuales": citas_json,
        "datos_cuantitativos": datos_json
    }
    
    return (
        json.dumps(elementos_basicos, ensure_ascii=False, indent=2),
        json.dumps(elementos_complementarios, ensure_ascii=False, indent=2)
    )

@retry_groq_api()
def _llamar_groq_api_relaciones(
    config: Dict[str, Any],
    elementos_basicos: str,
    elementos_complementarios: str,
    titulo_documento: str = "No disponible",
    fuente_tipo: str = "No disponible",
    pais_origen: str = "No disponible",
    fecha_fuente: str = "No disponible"
) -> tuple[str, str]:
    """
    Llama a la API de Groq para extracción de relaciones.
    
    SUBTAREA 3 - pasos 2-7: Implementación completa
    """
    article_id_log = config.get("article_id", "N/A")
    if not Groq:
        logger.error(f"SDK de Groq no instalado. Artículo: {article_id_log}")
        raise GroqAPIError("SDK de Groq no instalado.", phase=ErrorPhase.FASE_4_NORMALIZACION, article_id=config.get("article_id"))
    if not config.get("api_key"):
        logger.error(f"GROQ_API_KEY no configurada. Artículo: {article_id_log}")
        raise GroqAPIError("GROQ_API_KEY no configurada.", phase=ErrorPhase.FASE_4_NORMALIZACION, article_id=config.get("article_id"))

    try:
        prompt_template = _load_prompt_template()
    except ErrorFase4 as e_prompt:
        logger.error(f"Fallo al cargar plantilla de prompt para relaciones. Artículo: {article_id_log}. Error: {e_prompt}")
        raise GroqAPIError(f"Fallo al cargar plantilla de prompt para relaciones: {e_prompt}", phase=ErrorPhase.FASE_4_NORMALIZACION, article_id=config.get("article_id")) from e_prompt

    # Formatear el prompt con las variables
    prompt_formateado = prompt_template.replace("{{TITULO_O_DOCUMENTO}}", titulo_documento)\
                                     .replace("{{FUENTE_O_TIPO}}", fuente_tipo)\
                                     .replace("{{PAIS_ORIGEN}}", pais_origen)\
                                     .replace("{{FECHA_FUENTE}}", fecha_fuente)\
                                     .replace("{{ELEMENTOS_BASICOS_NORMALIZADOS}}", elementos_basicos)\
                                     .replace("{{ELEMENTOS_COMPLEMENTARIOS}}", elementos_complementarios)

    client = Groq(api_key=config["api_key"], timeout=config["timeout"])

    logger.info(f"Enviando solicitud a Groq API para relaciones (modelo: {config['model_id']}). Artículo: {article_id_log}")
    
    # Agregar instrucción para obtener solo JSON
    system_prompt = "Eres un asistente especializado en análisis de relaciones entre elementos de texto. Responde ÚNICAMENTE con el JSON solicitado, sin texto adicional, sin markdown, sin explicaciones."
    
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
        logger.warning(f"Groq API para relaciones devolvió una respuesta vacía. Artículo: {article_id_log}")
        raise GroqAPIError("Respuesta vacía de Groq API para relaciones.", phase=ErrorPhase.FASE_4_NORMALIZACION, article_id=config.get("article_id"))
    
    logger.info(f"Respuesta recibida de Groq API para relaciones. Artículo: {article_id_log}")
    return prompt_formateado, respuesta_contenido

# ============================================================================
# SUBTAREA 4 - Implementar procesamiento y vinculación de relaciones
# ============================================================================

def _parsear_relaciones_hecho_entidad(
    relaciones_json: List[Dict[str, Any]], 
    ids_hechos_validos: set,
    ids_entidades_validas: set
) -> List[RelacionHechoEntidad]:
    """
    SUBTAREA 4 - paso 9: Parser específico para relaciones hecho-entidad
    """
    relaciones = []
    
    for rel in relaciones_json:
        hecho_id = rel.get("hecho_id")
        entidad_id = rel.get("entidad_id")
        
        # Validar que los IDs existen (SUBTAREA 4 - paso 14)
        if hecho_id not in ids_hechos_validos:
            logger.warning(f"Relación hecho-entidad con hecho_id inexistente: {hecho_id}")
            continue
        if entidad_id not in ids_entidades_validas:
            logger.warning(f"Relación hecho-entidad con entidad_id inexistente: {entidad_id}")
            continue
        
        # Validar tipo de relación (SUBTAREA 4 - paso 10)
        tipo_relacion = rel.get("tipo_relacion", "").lower()
        tipos_validos = {
            "protagonista", "mencionado", "afectado", "declarante", 
            "ubicacion", "contexto", "victima", "agresor", 
            "organizador", "participante", "otro"
        }
        if tipo_relacion not in tipos_validos:
            logger.warning(f"Tipo de relación hecho-entidad inválido: {tipo_relacion}")
            tipo_relacion = "otro"
        
        # Validar relevancia (SUBTAREA 4 - paso 11)
        relevancia = rel.get("relevancia_en_hecho", 5)
        if not isinstance(relevancia, int) or relevancia < 1 or relevancia > 10:
            logger.warning(f"Relevancia inválida: {relevancia}, usando 5")
            relevancia = 5
        
        relacion = RelacionHechoEntidad(
            hecho_id=hecho_id,
            entidad_id=entidad_id,
            tipo_relacion=tipo_relacion,
            relevancia_en_hecho=relevancia
        )
        relaciones.append(relacion)
    
    return relaciones

def _parsear_relaciones_hecho_hecho(
    relaciones_json: List[Dict[str, Any]], 
    ids_hechos_validos: set
) -> List[RelacionHechoHecho]:
    """
    SUBTAREA 4 - paso 9: Parser específico para relaciones hecho-hecho
    """
    relaciones = []
    
    for rel in relaciones_json:
        hecho_origen_id = rel.get("hecho_origen_id")
        hecho_destino_id = rel.get("hecho_destino_id")
        
        # Validar que los IDs existen
        if hecho_origen_id not in ids_hechos_validos:
            logger.warning(f"Relación hecho-hecho con hecho_origen_id inexistente: {hecho_origen_id}")
            continue
        if hecho_destino_id not in ids_hechos_validos:
            logger.warning(f"Relación hecho-hecho con hecho_destino_id inexistente: {hecho_destino_id}")
            continue
        
        # Detectar relaciones circulares (SUBTAREA 4 - paso 13)
        if hecho_origen_id == hecho_destino_id:
            logger.warning(f"Relación circular detectada: hecho {hecho_origen_id} consigo mismo")
            continue
        
        # Validar tipo de relación
        tipo_relacion = rel.get("tipo_relacion", "").lower()
        tipos_validos = {
            "causa", "consecuencia", "contexto_historico", "respuesta_a",
            "aclaracion_de", "version_alternativa", "seguimiento_de"
        }
        if tipo_relacion not in tipos_validos:
            logger.warning(f"Tipo de relación hecho-hecho inválido: {tipo_relacion}")
            continue
        
        # Validar fuerza
        fuerza = rel.get("fuerza_relacion", 5)
        if not isinstance(fuerza, int) or fuerza < 1 or fuerza > 10:
            fuerza = 5
        
        # Sanitizar descripción
        descripcion_sanitizada = escape_html(rel.get("descripcion_relacion", ""))
        
        relacion = RelacionHechoHecho(
            hecho_origen_id=hecho_origen_id,
            hecho_destino_id=hecho_destino_id,
            tipo_relacion=tipo_relacion,
            fuerza_relacion=fuerza,
            descripcion_relacion=descripcion_sanitizada
        )
        relaciones.append(relacion)
    
    return relaciones

def _parsear_relaciones_entidad_entidad(
    relaciones_json: List[Dict[str, Any]], 
    ids_entidades_validas: set
) -> List[RelacionEntidadEntidad]:
    """
    SUBTAREA 4 - paso 9: Parser específico para relaciones entidad-entidad
    """
    relaciones = []
    
    for rel in relaciones_json:
        entidad_origen_id = rel.get("entidad_origen_id")
        entidad_destino_id = rel.get("entidad_destino_id")
        
        # Validar que los IDs existen
        if entidad_origen_id not in ids_entidades_validas:
            logger.warning(f"Relación entidad-entidad con entidad_origen_id inexistente: {entidad_origen_id}")
            continue
        if entidad_destino_id not in ids_entidades_validas:
            logger.warning(f"Relación entidad-entidad con entidad_destino_id inexistente: {entidad_destino_id}")
            continue
        
        # Detectar relaciones circulares
        if entidad_origen_id == entidad_destino_id:
            logger.warning(f"Relación circular detectada: entidad {entidad_origen_id} consigo misma")
            continue
        
        # Validar tipo de relación
        tipo_relacion = rel.get("tipo_relacion", "").lower()
        tipos_validos = {
            "miembro_de", "subsidiaria_de", "aliado_con", "opositor_a",
            "sucesor_de", "predecesor_de", "casado_con", "familiar_de", "empleado_de"
        }
        if tipo_relacion not in tipos_validos:
            logger.warning(f"Tipo de relación entidad-entidad inválido: {tipo_relacion}")
            continue
        
        # Validar fuerza
        fuerza = rel.get("fuerza_relacion", 5)
        if not isinstance(fuerza, int) or fuerza < 1 or fuerza > 10:
            fuerza = 5
        
        # Validar y sanitizar fechas
        fecha_inicio_validada = None
        fecha_fin_validada = None
        try:
            fecha_inicio_validada = validate_date_optional(rel.get("fecha_inicio"))
            fecha_fin_validada = validate_date_optional(rel.get("fecha_fin"))
            
            # Validar coherencia temporal
            if fecha_inicio_validada and fecha_fin_validada:
                from datetime import datetime
                if datetime.strptime(fecha_inicio_validada, "%Y-%m-%d") > datetime.strptime(fecha_fin_validada, "%Y-%m-%d"):
                    logger.warning(f"Fechas inválidas en relación: inicio posterior a fin. Intercambiando.")
                    fecha_inicio_validada, fecha_fin_validada = fecha_fin_validada, fecha_inicio_validada
        except ValueError as e:
            logger.warning(f"Error validando fechas en relación entidad-entidad: {e}")
        
        # Sanitizar descripción
        descripcion_sanitizada = escape_html(rel.get("descripcion", ""))
        
        relacion = RelacionEntidadEntidad(
            entidad_origen_id=entidad_origen_id,
            entidad_destino_id=entidad_destino_id,
            tipo_relacion=tipo_relacion,
            descripcion=descripcion_sanitizada,
            fecha_inicio=fecha_inicio_validada,
            fecha_fin=fecha_fin_validada,
            fuerza_relacion=fuerza
        )
        relaciones.append(relacion)
    
    return relaciones

def _parsear_contradicciones(
    contradicciones_json: List[Dict[str, Any]], 
    ids_hechos_validos: set
) -> List[Contradiccion]:
    """
    SUBTAREA 4 - paso 9: Parser específico para contradicciones
    """
    contradicciones = []
    
    for cont in contradicciones_json:
        hecho_principal_id = cont.get("hecho_principal_id")
        hecho_contradictorio_id = cont.get("hecho_contradictorio_id")
        
        # Validar que los IDs existen
        if hecho_principal_id not in ids_hechos_validos:
            logger.warning(f"Contradicción con hecho_principal_id inexistente: {hecho_principal_id}")
            continue
        if hecho_contradictorio_id not in ids_hechos_validos:
            logger.warning(f"Contradicción con hecho_contradictorio_id inexistente: {hecho_contradictorio_id}")
            continue
        
        # Validar tipo de contradicción
        tipo_contradiccion = cont.get("tipo_contradiccion", "").lower()
        tipos_validos = {
            "fecha", "contenido", "entidades", "ubicacion", "valor", "completa"
        }
        if tipo_contradiccion not in tipos_validos:
            logger.warning(f"Tipo de contradicción inválido: {tipo_contradiccion}")
            tipo_contradiccion = "contenido"
        
        # Validar grado
        grado = cont.get("grado_contradiccion", 3)
        if not isinstance(grado, int) or grado < 1 or grado > 5:
            grado = 3
        
        # Sanitizar descripción
        descripcion_sanitizada = escape_html(cont.get("descripcion", ""))
        
        contradiccion = Contradiccion(
            hecho_principal_id=hecho_principal_id,
            hecho_contradictorio_id=hecho_contradictorio_id,
            tipo_contradiccion=tipo_contradiccion,
            grado_contradiccion=grado,
            descripcion=descripcion_sanitizada
        )
        contradicciones.append(contradiccion)
    
    return contradicciones

def _procesar_relaciones_desde_json(
    respuesta_json: Dict[str, Any],
    resultado_fase_2: ResultadoFase2Extraccion
) -> Dict[str, Any]:
    """
    Procesa todas las relaciones desde la respuesta JSON del LLM.
    
    SUBTAREA 4 - implementación completa
    """
    # Crear conjuntos de IDs válidos para validación
    ids_hechos_validos = {h.id_hecho for h in resultado_fase_2.hechos_extraidos}
    ids_entidades_validas = {e.id_entidad for e in resultado_fase_2.entidades_extraidas}
    
    logger.debug(f"IDs válidos - Hechos: {ids_hechos_validos}, Entidades: {ids_entidades_validas}")
    
    # Parsear cada tipo de relación
    relaciones_hecho_entidad = _parsear_relaciones_hecho_entidad(
        respuesta_json.get("hecho_entidad", []),
        ids_hechos_validos,
        ids_entidades_validas
    )
    
    relaciones_hecho_hecho = _parsear_relaciones_hecho_hecho(
        respuesta_json.get("hecho_relacionado", []),
        ids_hechos_validos
    )
    
    relaciones_entidad_entidad = _parsear_relaciones_entidad_entidad(
        respuesta_json.get("entidad_relacion", []),
        ids_entidades_validas
    )
    
    contradicciones = _parsear_contradicciones(
        respuesta_json.get("contradicciones", []),
        ids_hechos_validos
    )
    
    # Crear estructuras indexadas para consulta eficiente (SUBTAREA 4 - paso 12)
    indice_relaciones = {
        "por_hecho": {},
        "por_entidad": {},
        "hecho_hecho": {},
        "entidad_entidad": {}
    }
    
    # Indexar relaciones hecho-entidad
    for rel in relaciones_hecho_entidad:
        if rel.hecho_id not in indice_relaciones["por_hecho"]:
            indice_relaciones["por_hecho"][rel.hecho_id] = []
        indice_relaciones["por_hecho"][rel.hecho_id].append(rel)
        
        if rel.entidad_id not in indice_relaciones["por_entidad"]:
            indice_relaciones["por_entidad"][rel.entidad_id] = []
        indice_relaciones["por_entidad"][rel.entidad_id].append(rel)
    
    # Indexar relaciones hecho-hecho
    for rel in relaciones_hecho_hecho:
        if rel.hecho_origen_id not in indice_relaciones["hecho_hecho"]:
            indice_relaciones["hecho_hecho"][rel.hecho_origen_id] = []
        indice_relaciones["hecho_hecho"][rel.hecho_origen_id].append(rel)
    
    # Indexar relaciones entidad-entidad
    for rel in relaciones_entidad_entidad:
        if rel.entidad_origen_id not in indice_relaciones["entidad_entidad"]:
            indice_relaciones["entidad_entidad"][rel.entidad_origen_id] = []
        indice_relaciones["entidad_entidad"][rel.entidad_origen_id].append(rel)
    
    logger.info(
        f"Relaciones procesadas - HE: {len(relaciones_hecho_entidad)}, "
        f"HH: {len(relaciones_hecho_hecho)}, EE: {len(relaciones_entidad_entidad)}, "
        f"Contradicciones: {len(contradicciones)}"
    )
    
    return {
        "relaciones_hecho_entidad": relaciones_hecho_entidad,
        "relaciones_hecho_hecho": relaciones_hecho_hecho,
        "relaciones_entidad_entidad": relaciones_entidad_entidad,
        "contradicciones": contradicciones,
        "indices": indice_relaciones
    }

# ============================================================================
# SUBTAREA 5, 6, 7 - Función principal ejecutar_fase_4
# ============================================================================

def ejecutar_fase_4(
    processor: FragmentProcessor,  # SUBTAREA 6 - paso 1
    resultado_fase_1: ResultadoFase1Triaje,
    resultado_fase_2: ResultadoFase2Extraccion,
    resultado_fase_3: ResultadoFase3CitasDatos,
    supabase_service: Optional[SupabaseService] = None
) -> ResultadoFase4Normalizacion:
    """
    Ejecuta la Fase 4: Normalización, Vinculación y Relaciones.
    
    SUBTAREA 5 - implementación completa según detalles
    SUBTAREA 6 - firma actualizada con processor
    SUBTAREA 7 - preservación de IDs
    
    Args:
        processor: FragmentProcessor para mantener coherencia de IDs
        resultado_fase_1: Resultado de la fase 1 (triaje)
        resultado_fase_2: Resultado de la fase 2 (extracción)
        resultado_fase_3: Resultado de la fase 3 (citas y datos)
        supabase_service: Servicio de Supabase (opcional)
        
    Returns:
        ResultadoFase4Normalizacion con entidades normalizadas y relaciones
    """
    # SUBTAREA 5 - paso 1: Extraer id_fragmento
    id_fragmento = resultado_fase_1.id_fragmento
    logger.info(f"Iniciando Fase 4: Normalización y Relaciones para fragmento ID: {id_fragmento}")
    
    # Medición de tiempo
    tiempo_inicio = time.time()
    
    # SUBTAREA 6 - paso 4: Validar estado del processor
    stats_processor = processor.get_stats()
    logger.debug(f"Estado del processor al inicio de fase 4: {stats_processor}")
    
    # Variables para el procesamiento
    entidades_normalizadas = []
    relaciones_procesadas = {}
    prompt_formateado = None
    respuesta_llm_cruda = None
    advertencias = []
    estado_normalizacion = "No Requerido"
    
    try:
        # SUBTAREA 5 - paso 2: Normalizar entidades
        if resultado_fase_2.entidades_extraidas and supabase_service:
            logger.info(f"Normalizando {len(resultado_fase_2.entidades_extraidas)} entidades")
            entidades_normalizadas = _normalizar_entidades_extraidas(
                resultado_fase_2.entidades_extraidas,
                supabase_service
            )
            # Las entidades ya están enriquecidas in-place (SUBTAREA 7)
        else:
            entidades_normalizadas = resultado_fase_2.entidades_extraidas
            if not supabase_service:
                advertencias.append("Servicio de normalización no disponible")
        
        # Configuración de Groq
        groq_config = _get_groq_config()
        groq_config_with_id = {**groq_config, "article_id": str(id_fragmento)}
        
        if not groq_config.get("api_key"):
            logger.error(f"No se encontró GROQ_API_KEY. No se puede procesar fragmento {id_fragmento}")
            # Aplicar fallback
            error_dict = handle_generic_phase_error(
                article_id=str(id_fragmento),
                phase=ErrorPhase.FASE_4_NORMALIZACION,
                step_failed="Configuración API",
                exception=RuntimeError("GROQ_API_KEY no configurada")
            )
            advertencias.append(error_dict["message"])
            estado_normalizacion = "Fallido"
        else:
            # Formatear elementos para el prompt
            elementos_basicos, elementos_complementarios = _formatear_elementos_para_prompt(
                resultado_fase_2,
                resultado_fase_3
            )
            
            # Preparar contexto del documento
            titulo_documento = "Fragmento de documento"
            fuente_tipo = "Documento procesado"
            pais_origen = "No especificado"
            fecha_fuente = datetime.now().strftime("%Y-%m-%d")
            
            # Llamar a Groq API para extracción de relaciones
            try:
                prompt_formateado, respuesta_llm_cruda = _llamar_groq_api_relaciones(
                    config=groq_config_with_id,
                    elementos_basicos=elementos_basicos,
                    elementos_complementarios=elementos_complementarios,
                    titulo_documento=titulo_documento,
                    fuente_tipo=fuente_tipo,
                    pais_origen=pais_origen,
                    fecha_fuente=fecha_fuente
                )
                
                logger.trace(f"Respuesta LLM (cruda) para relaciones de {id_fragmento}:\n{respuesta_llm_cruda}")
                
                # Parsear respuesta JSON
                try:
                    respuesta_json = json.loads(respuesta_llm_cruda)
                    
                    # Procesar relaciones
                    relaciones_procesadas = _procesar_relaciones_desde_json(
                        respuesta_json,
                        resultado_fase_2
                    )
                    
                    estado_normalizacion = "Completo"
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Error al parsear JSON de respuesta LLM: {e}")
                    advertencias.append(f"Error parseando respuesta de relaciones: {e}")
                    estado_normalizacion = "Parcial"
                    
            except GroqAPIError as e:
                logger.error(f"GroqAPIError durante extracción de relaciones para {id_fragmento}: {e}")
                error_dict = handle_generic_phase_error(
                    article_id=str(id_fragmento),
                    phase=ErrorPhase.FASE_4_NORMALIZACION,
                    step_failed="Llamada Groq API",
                    exception=e
                )
                advertencias.append(error_dict["message"])
                estado_normalizacion = "Parcial"
                
    except Exception as e:
        logger.error(f"Error inesperado durante fase 4 para {id_fragmento}: {e}")
        error_dict = handle_generic_phase_error(
            article_id=str(id_fragmento),
            phase=ErrorPhase.FASE_4_NORMALIZACION,
            step_failed="Procesamiento general",
            exception=e
        )
        advertencias.append(error_dict["message"])
        estado_normalizacion = "Fallido"
    
    # SUBTAREA 5 - paso 3: Generar resumen automático
    num_normalizadas = len([e for e in entidades_normalizadas if e.id_entidad_normalizada])
    num_nuevas = len(entidades_normalizadas) - num_normalizadas
    num_relaciones = (
        len(relaciones_procesadas.get("relaciones_hecho_entidad", [])) +
        len(relaciones_procesadas.get("relaciones_hecho_hecho", [])) +
        len(relaciones_procesadas.get("relaciones_entidad_entidad", []))
    )
    
    resumen_normalizacion = (
        f"Procesadas {len(entidades_normalizadas)} entidades: "
        f"{num_normalizadas} normalizadas, {num_nuevas} nuevas. "
        f"Extraídas {num_relaciones} relaciones, "
        f"{len(relaciones_procesadas.get('contradicciones', []))} contradicciones."
    )
    
    # Calcular tiempo de procesamiento
    tiempo_procesamiento = time.time() - tiempo_inicio
    
    # SUBTAREA 5 - paso 6: Crear metadata
    metadata_normalizacion = {
        "modelo_usado": groq_config.get("model_id", "desconocido"),
        "tokens_prompt": len(prompt_formateado.split()) if prompt_formateado else 0,
        "tokens_respuesta": len(respuesta_llm_cruda.split()) if respuesta_llm_cruda else 0,
        "tiempo_procesamiento_segundos": round(tiempo_procesamiento, 2),
        "entidades_procesadas": len(entidades_normalizadas),
        "entidades_normalizadas": num_normalizadas,
        "entidades_nuevas": num_nuevas,
        "relaciones_extraidas": num_relaciones,
        "contradicciones_detectadas": len(relaciones_procesadas.get("contradicciones", [])),
        "timestamp_normalizacion": datetime.now().isoformat(),
        "ids_secuenciales_preservados": True,  # SUBTAREA 7
        "processor_stats": processor.get_stats()  # SUBTAREA 6 - paso 5
    }
    
    # SUBTAREA 5 - paso 8: Ensamblar resultado final
    resultado = ResultadoFase4Normalizacion(
        id_fragmento=id_fragmento,
        entidades_normalizadas=entidades_normalizadas,  # Ya enriquecidas in-place
        resumen_normalizacion=resumen_normalizacion,
        prompt_normalizacion_usado=prompt_formateado,
        estado_general_normalizacion=estado_normalizacion,
        metadata_normalizacion=metadata_normalizacion
    )
    
    # Agregar relaciones a metadata (temporal hasta que se agreguen campos en el modelo)
    if relaciones_procesadas:
        resultado.metadata_normalizacion["relaciones"] = {
            "hecho_entidad": [r.to_dict() for r in relaciones_procesadas.get("relaciones_hecho_entidad", [])],
            "hecho_hecho": [r.to_dict() for r in relaciones_procesadas.get("relaciones_hecho_hecho", [])],
            "entidad_entidad": [r.to_dict() for r in relaciones_procesadas.get("relaciones_entidad_entidad", [])],
            "contradicciones": [c.to_dict() for c in relaciones_procesadas.get("contradicciones", [])]
        }
    
    # Agregar advertencias si las hay
    if advertencias:
        resultado.metadata_normalizacion["advertencias"] = advertencias
    
    # SUBTAREA 5 - paso 8: Llamar .touch()
    resultado.touch()
    
    # SUBTAREA 5 - paso 11: Logging final
    logger.info(
        f"Fase 4: Normalización completada para fragmento ID: {id_fragmento}. "
        f"Estado: {estado_normalizacion}, Tiempo: {tiempo_procesamiento:.2f}s",
        extra={
            "fragment_id": str(id_fragmento),
            "normalized_entities": num_normalizadas,
            "new_entities": num_nuevas,
            "total_relationships": num_relaciones,
            "contradictions": len(relaciones_procesadas.get("contradicciones", [])),
            "processing_time": tiempo_procesamiento,
            "status": estado_normalizacion
        }
    )
    
    return resultado

# ============================================================================
# TEST BÁSICO PARA VERIFICAR LA IMPLEMENTACIÓN
# ============================================================================

if __name__ == "__main__":
    from uuid import uuid4
    
    # Setup básico de logging para testing
    import sys
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")
    
    # Test básico
    test_fragmento = uuid4()
    processor = FragmentProcessor(test_fragmento)
    
    # Mock de resultados de fases anteriores
    from ..models.procesamiento import HechoProcesado, EntidadProcesada
    from ..models.metadatos import MetadatosHecho, MetadatosEntidad, MetadatosCita, MetadatosDato
    
    # Mock fase 1
    resultado_fase1_mock = ResultadoFase1Triaje(
        id_fragmento=test_fragmento,
        es_relevante=True,
        texto_para_siguiente_fase="Texto de prueba para fase 4"
    )
    
    # Mock fase 2
    hechos_mock = [
        HechoProcesado(
            id_hecho=1,
            texto_original_del_hecho="Pedro Sánchez anunció medidas económicas",
            confianza_extraccion=0.9,
            id_fragmento_origen=test_fragmento,
            metadata_hecho=MetadatosHecho(tipo_hecho="ANUNCIO")
        ),
        HechoProcesado(
            id_hecho=2,
            texto_original_del_hecho="Las medidas entrarán en vigor próximamente",
            confianza_extraccion=0.8,
            id_fragmento_origen=test_fragmento,
            metadata_hecho=MetadatosHecho(tipo_hecho="EVENTO")
        )
    ]
    
    entidades_mock = [
        EntidadProcesada(
            id_entidad=1,
            texto_entidad="Pedro Sánchez",
            tipo_entidad="PERSONA",
            relevancia_entidad=0.9,
            id_fragmento_origen=test_fragmento,
            metadata_entidad=MetadatosEntidad(tipo="PERSONA")
        ),
        EntidadProcesada(
            id_entidad=2,
            texto_entidad="PSOE",
            tipo_entidad="ORGANIZACION",
            relevancia_entidad=0.7,
            id_fragmento_origen=test_fragmento,
            metadata_entidad=MetadatosEntidad(tipo="ORGANIZACION")
        ),
        EntidadProcesada(
            id_entidad=3,
            texto_entidad="Gobierno de España",
            tipo_entidad="INSTITUCION",
            relevancia_entidad=0.8,
            id_fragmento_origen=test_fragmento,
            metadata_entidad=MetadatosEntidad(tipo="INSTITUCION")
        )
    ]
    
    resultado_fase2_mock = ResultadoFase2Extraccion(
        id_fragmento=test_fragmento,
        hechos_extraidos=hechos_mock,
        entidades_extraidas=entidades_mock
    )
    
    # Mock fase 3
    citas_mock = [
        CitaTextual(
            id_cita=1,
            id_fragmento_origen=test_fragmento,
            texto_cita="Vamos a implementar estas medidas urgentemente",
            persona_citada="Pedro Sánchez",
            id_entidad_citada=1,
            metadata_cita=MetadatosCita(relevancia=4)
        )
    ]
    
    datos_mock = [
        DatosCuantitativos(
            id_dato_cuantitativo=1,
            id_fragmento_origen=test_fragmento,
            descripcion_dato="Inversión en medidas económicas",
            valor_dato=1000000000,
            unidad_dato="euros",
            fecha_dato="2024",
            metadata_dato=MetadatosDato(categoria="económico")
        )
    ]
    
    resultado_fase3_mock = ResultadoFase3CitasDatos(
        id_fragmento=test_fragmento,
        citas_textuales_extraidas=citas_mock,
        datos_cuantitativos_extraidos=datos_mock
    )
    
    try:
        # Test fase 4 sin servicio de Supabase (normalización saltada)
        resultado = ejecutar_fase_4(
            processor,
            resultado_fase1_mock,
            resultado_fase2_mock,
            resultado_fase3_mock,
            supabase_service=None
        )
        
        print(f"✅ Test exitoso: Estado {resultado.estado_general_normalizacion}")
        print(f"✅ Resumen: {resultado.resumen_normalizacion}")
        print(f"✅ Processor summary:")
        processor.log_summary()
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
