"""
Fase 7: Normalización y Vinculación
===================================

Esta fase incluye:
- 7A: Normalización de entidades (Supabase)
- 7B: Detección de relaciones (paralelo)
  - 7B.1: Relaciones estructurales
  - 7B.2: Relaciones temporales
"""

from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
from datetime import datetime
import os
import json
import asyncio
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from loguru import logger

# Importar modelos
from ..models.procesamiento import (
    EntidadProcesada,
    HechoProcesado,
    DatosCuantitativos,
    CitaTextual,
    ResultadoFase4Normalizacion
)

# Importar servicios
from ..services.entity_normalizer import NormalizadorEntidades
from ..services.supabase_service import SupabaseService

# Importar utilidades
from ..utils.error_handling import (
    handle_generic_phase_error,
    ErrorPhase,
    GroqAPIError,
    ProcessingError,
    SupabaseRPCError
)
from ..utils.json_parser import parse_llm_json_response
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


# Rutas a los prompts de relaciones
_PROMPT_RELACIONES_ESTRUCTURALES_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "7B.1_Relaciones-Estructurales.md"
_PROMPT_RELACIONES_TEMPORALES_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "7B.2_Relaciones-Temporales.md"

_PROMPT_RELACIONES_ESTRUCTURALES: Optional[str] = None
_PROMPT_RELACIONES_TEMPORALES: Optional[str] = None


def _cargar_prompt_relaciones_estructurales() -> str:
    """Carga el prompt de relaciones estructurales."""
    global _PROMPT_RELACIONES_ESTRUCTURALES
    
    if _PROMPT_RELACIONES_ESTRUCTURALES is None:
        if not _PROMPT_RELACIONES_ESTRUCTURALES_PATH.exists():
            raise FileNotFoundError(
                f"No se encontró el archivo de prompt en: {_PROMPT_RELACIONES_ESTRUCTURALES_PATH}"
            )
        
        with open(_PROMPT_RELACIONES_ESTRUCTURALES_PATH, "r", encoding="utf-8") as f:
            _PROMPT_RELACIONES_ESTRUCTURALES = f.read()
            
        logger.info(f"Prompt de relaciones estructurales cargado")
    
    return _PROMPT_RELACIONES_ESTRUCTURALES


def _cargar_prompt_relaciones_temporales() -> str:
    """Carga el prompt de relaciones temporales."""
    global _PROMPT_RELACIONES_TEMPORALES
    
    if _PROMPT_RELACIONES_TEMPORALES is None:
        if not _PROMPT_RELACIONES_TEMPORALES_PATH.exists():
            raise FileNotFoundError(
                f"No se encontró el archivo de prompt en: {_PROMPT_RELACIONES_TEMPORALES_PATH}"
            )
        
        with open(_PROMPT_RELACIONES_TEMPORALES_PATH, "r", encoding="utf-8") as f:
            _PROMPT_RELACIONES_TEMPORALES = f.read()
            
        logger.info(f"Prompt de relaciones temporales cargado")
    
    return _PROMPT_RELACIONES_TEMPORALES


def _preparar_contexto_relaciones(
    hechos: List[HechoProcesado],
    entidades: List[EntidadProcesada]
) -> str:
    """
    Prepara el contexto de hechos y entidades para relaciones estructurales.
    
    Args:
        hechos: Lista de hechos
        entidades: Lista de entidades
        
    Returns:
        JSON con contexto mínimo
    """
    contexto = {
        "hechos": [
            {
                "id": h.id_hecho,
                "contenido": h.texto_original_del_hecho,
                "tipo": h.metadata_hecho.tipo_hecho
            }
            for h in hechos
        ],
        "entidades": [
            {
                "id": e.id_entidad,
                "nombre": e.texto_entidad,
                "tipo": e.tipo_entidad
            }
            for e in entidades
        ]
    }
    
    return json.dumps(contexto, ensure_ascii=False, indent=2)


def _preparar_contexto_temporal(
    hechos: List[HechoProcesado]
) -> str:
    """
    Prepara el contexto de hechos para relaciones temporales.
    
    Args:
        hechos: Lista de hechos
        
    Returns:
        JSON con hechos
    """
    contexto = {
        "hechos": [
            {
                "id": h.id_hecho,
                "contenido": h.texto_original_del_hecho,
                "fecha_inicio": h.metadata_hecho.fecha_inicio,
                "fecha_fin": h.metadata_hecho.fecha_fin,
                "tipo": h.metadata_hecho.tipo_hecho
            }
            for h in hechos
        ]
    }
    
    return json.dumps(contexto, ensure_ascii=False, indent=2)


async def _detectar_relaciones_estructurales(
    hechos: List[HechoProcesado],
    entidades: List[EntidadProcesada],
    contexto_articulo: Dict[str, Any],
    groq_api_key: str
) -> Dict[str, Any]:
    """
    Detecta relaciones estructurales (hecho-entidad y entidad-entidad).
    
    Args:
        hechos: Lista de hechos
        entidades: Lista de entidades
        contexto_articulo: Contexto del artículo
        groq_api_key: API key de Groq
        
    Returns:
        Diccionario con relaciones detectadas
    """
    logger.info("Detectando relaciones estructurales (7B.1)")
    
    try:
        # Preparar contexto
        contexto_json = _preparar_contexto_relaciones(hechos, entidades)
        
        # Calcular tokens aproximados
        tokens_estimados = len(contexto_json) // 4
        modelo = "llama-3.1-8b-instant"
        if tokens_estimados > 8000:
            modelo = "llama3-70b-8192"
            logger.info(f"Usando modelo grande para relaciones estructurales ({tokens_estimados} tokens)")
        
        # Preparar prompt
        prompt = _cargar_prompt_relaciones_estructurales()
        prompt = prompt.replace("{{TITULO_O_DOCUMENTO}}", contexto_articulo.get("titulo", "No disponible"))
        prompt = prompt.replace("{{FUENTE_O_TIPO}}", contexto_articulo.get("fuente", "No disponible"))
        prompt = prompt.replace("{{PAIS_ORIGEN}}", contexto_articulo.get("pais", "No disponible"))
        prompt = prompt.replace("{{FECHA_FUENTE}}", contexto_articulo.get("fecha_publicacion", "No disponible"))
        prompt = prompt.replace("{{HECHOS_Y_ENTIDADES_CONTEXTO}}", contexto_json)
        
        # Llamar a Groq
        client = Groq(api_key=groq_api_key)
        
        inicio = datetime.now()
        response = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model=modelo,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto en análisis de relaciones en textos periodísticos. Identificas con precisión las conexiones entre hechos y entidades."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
        )
        duracion_ms = int((datetime.now() - inicio).total_seconds() * 1000)
        
        # Parsear respuesta
        respuesta_texto = response.choices[0].message.content
        relaciones = parse_llm_json_response(respuesta_texto)
        
        logger.info(
            f"Relaciones estructurales detectadas: "
            f"{len(relaciones.get('hecho_entidad', []))} hecho-entidad, "
            f"{len(relaciones.get('entidad_relacion', []))} entidad-entidad"
        )
        
        return {
            "relaciones": relaciones,
            "metadatos": {
                "modelo": modelo,
                "duracion_ms": duracion_ms,
                "tokens_prompt": response.usage.prompt_tokens if response.usage else None,
                "tokens_respuesta": response.usage.completion_tokens if response.usage else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error detectando relaciones estructurales: {str(e)}")
        return {
            "relaciones": {"hecho_entidad": [], "entidad_relacion": []},
            "error": str(e)
        }


async def _detectar_relaciones_temporales(
    hechos: List[HechoProcesado],
    texto_simplificado: str,
    contexto_articulo: Dict[str, Any],
    groq_api_key: str
) -> Dict[str, Any]:
    """
    Detecta relaciones temporales y contradicciones entre hechos.
    
    Args:
        hechos: Lista de hechos
        texto_simplificado: Texto simplificado para contexto
        contexto_articulo: Contexto del artículo
        groq_api_key: API key de Groq
        
    Returns:
        Diccionario con relaciones detectadas
    """
    logger.info("Detectando relaciones temporales (7B.2)")
    
    try:
        # Preparar contexto
        contexto_hechos = _preparar_contexto_temporal(hechos)
        
        # Calcular tokens aproximados
        tokens_estimados = (len(contexto_hechos) + len(texto_simplificado)) // 4
        modelo = "llama-3.1-8b-instant"
        if tokens_estimados > 8000:
            modelo = "llama3-70b-8192"
            logger.info(f"Usando modelo grande para relaciones temporales ({tokens_estimados} tokens)")
        
        # Preparar prompt
        prompt = _cargar_prompt_relaciones_temporales()
        prompt = prompt.replace("{{TITULO_O_DOCUMENTO}}", contexto_articulo.get("titulo", "No disponible"))
        prompt = prompt.replace("{{FUENTE_O_TIPO}}", contexto_articulo.get("fuente", "No disponible"))
        prompt = prompt.replace("{{PAIS_ORIGEN}}", contexto_articulo.get("pais", "No disponible"))
        prompt = prompt.replace("{{FECHA_FUENTE}}", contexto_articulo.get("fecha_publicacion", "No disponible"))
        prompt = prompt.replace("{{HECHOS_CONTEXTO}}", contexto_hechos)
        prompt = prompt.replace("{{TEXTO_SIMPLIFICADO}}", texto_simplificado[:3000])  # Limitar contexto
        
        # Llamar a Groq
        client = Groq(api_key=groq_api_key)
        
        inicio = datetime.now()
        response = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model=modelo,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto en análisis temporal y causal de eventos. Identificas relaciones temporales y contradicciones con precisión."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
        )
        duracion_ms = int((datetime.now() - inicio).total_seconds() * 1000)
        
        # Parsear respuesta
        respuesta_texto = response.choices[0].message.content
        relaciones = parse_llm_json_response(respuesta_texto)
        
        logger.info(
            f"Relaciones temporales detectadas: "
            f"{len(relaciones.get('hecho_relacionado', []))} relaciones, "
            f"{len(relaciones.get('contradicciones', []))} contradicciones"
        )
        
        return {
            "relaciones": relaciones,
            "metadatos": {
                "modelo": modelo,
                "duracion_ms": duracion_ms,
                "tokens_prompt": response.usage.prompt_tokens if response.usage else None,
                "tokens_respuesta": response.usage.completion_tokens if response.usage else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error detectando relaciones temporales: {str(e)}")
        return {
            "relaciones": {"hecho_relacionado": [], "contradicciones": []},
            "error": str(e)
        }


def ejecutar_fase_7a_normalizacion(
    entidades: List[EntidadProcesada],
    supabase_service: Optional[SupabaseService] = None
) -> Dict[str, Any]:
    """
    Ejecuta la Fase 7A: Normalización de entidades.
    
    Busca entidades canónicas en Supabase y las vincula.
    
    Args:
        entidades: Lista de entidades a normalizar
        supabase_service: Servicio de Supabase (opcional)
        
    Returns:
        Diccionario con resultados de normalización
    """
    logger.info(f"Iniciando Fase 7A: Normalización de {len(entidades)} entidades")
    
    if not supabase_service:
        supabase_service = SupabaseService()
    
    normalizador = NormalizadorEntidades(supabase_service)
    
    entidades_normalizadas = []
    estadisticas = {
        "total": len(entidades),
        "normalizadas": 0,
        "no_encontradas": 0,
        "errores": 0
    }
    
    for entidad in entidades:
        try:
            # Intentar normalizar
            resultado = normalizador.normalizar_entidad(
                nombre_entidad=entidad.texto_entidad,
                tipo_entidad=entidad.tipo_entidad
                # Removido metadata - no es un parámetro válido
            )
            
            if not resultado["es_nueva"]:
                # Actualizar entidad con información normalizada
                entidad.id_entidad_normalizada = resultado["id_entidad_normalizada"]
                entidad.nombre_entidad_normalizada = resultado["nombre_normalizado"]
                entidad.uri_wikidata = resultado.get("uri_wikidata")  # Este campo puede no existir
                entidad.similitud_normalizacion = resultado["score_similitud"]
                estadisticas["normalizadas"] += 1
            else:
                estadisticas["no_encontradas"] += 1
            
            entidades_normalizadas.append(entidad)
            
        except Exception as e:
            logger.error(f"Error normalizando entidad {entidad.texto_entidad}: {str(e)}")
            estadisticas["errores"] += 1
            entidades_normalizadas.append(entidad)
    
    logger.info(
        f"Fase 7A completada: {estadisticas['normalizadas']} normalizadas, "
        f"{estadisticas['no_encontradas']} no encontradas, "
        f"{estadisticas['errores']} errores"
    )
    
    return {
        "entidades_normalizadas": entidades_normalizadas,
        "estadisticas": estadisticas
    }


async def ejecutar_fase_7b_relaciones(
    hechos: List[HechoProcesado],
    entidades: List[EntidadProcesada],
    texto_simplificado: str,
    contexto_articulo: Dict[str, Any],
    groq_api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Ejecuta la Fase 7B: Detección de relaciones en paralelo.
    
    Ejecuta 7B.1 (estructurales) y 7B.2 (temporales) simultáneamente.
    
    Args:
        hechos: Lista de hechos
        entidades: Lista de entidades
        texto_simplificado: Texto simplificado
        contexto_articulo: Contexto del artículo
        groq_api_key: API key de Groq
        
    Returns:
        Diccionario con todas las relaciones detectadas
    """
    logger.info("Iniciando Fase 7B: Detección de relaciones en paralelo")
    
    # Obtener API key
    api_key = groq_api_key or os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("No se encontró GROQ_API_KEY")
    
    # Ejecutar ambas detecciones en paralelo
    inicio = datetime.now()
    
    # Crear tareas asíncronas
    tarea_estructurales = _detectar_relaciones_estructurales(
        hechos, entidades, contexto_articulo, api_key
    )
    
    tarea_temporales = _detectar_relaciones_temporales(
        hechos, texto_simplificado, contexto_articulo, api_key
    )
    
    # Ejecutar en paralelo con asyncio.gather()
    resultados = await asyncio.gather(
        tarea_estructurales,
        tarea_temporales,
        return_exceptions=True
    )
    
    duracion_total_ms = int((datetime.now() - inicio).total_seconds() * 1000)
    
    # Procesar resultados
    resultado_estructurales = resultados[0] if not isinstance(resultados[0], Exception) else {"error": str(resultados[0])}
    resultado_temporales = resultados[1] if not isinstance(resultados[1], Exception) else {"error": str(resultados[1])}
    
    # Consolidar resultados
    todas_relaciones = {
        "relaciones_estructurales": resultado_estructurales.get("relaciones", {}),
        "relaciones_temporales": resultado_temporales.get("relaciones", {}),
        "metadatos": {
            "duracion_total_ms": duracion_total_ms,
            "paralelo": True,
            "metadatos_estructurales": resultado_estructurales.get("metadatos", {}),
            "metadatos_temporales": resultado_temporales.get("metadatos", {})
        }
    }
    
    # Contar relaciones
    total_relaciones = (
        len(todas_relaciones["relaciones_estructurales"].get("hecho_entidad", [])) +
        len(todas_relaciones["relaciones_estructurales"].get("entidad_relacion", [])) +
        len(todas_relaciones["relaciones_temporales"].get("hecho_relacionado", [])) +
        len(todas_relaciones["relaciones_temporales"].get("contradicciones", []))
    )
    
    logger.info(
        f"Fase 7B completada en {duracion_total_ms}ms: "
        f"{total_relaciones} relaciones totales detectadas"
    )
    
    return todas_relaciones


def ejecutar_fase_7_completa(
    hechos: List[HechoProcesado],
    entidades: List[EntidadProcesada],
    datos: List[DatosCuantitativos],
    citas: List[CitaTextual],
    texto_simplificado: str,
    contexto_articulo: Dict[str, Any],
    groq_api_key: Optional[str] = None,
    supabase_service: Optional[SupabaseService] = None
) -> ResultadoFase4Normalizacion:
    """
    Ejecuta la Fase 7 completa: Normalización + Relaciones.
    
    Esta es la función síncrona principal que orquesta ambas subfases.
    
    Args:
        hechos: Lista de hechos
        entidades: Lista de entidades
        datos: Lista de datos cuantitativos
        citas: Lista de citas textuales
        texto_simplificado: Texto simplificado
        contexto_articulo: Contexto del artículo
        groq_api_key: API key de Groq
        supabase_service: Servicio de Supabase
        
    Returns:
        ResultadoFase4Normalizacion con todos los resultados
    """
    logger.info("Iniciando Fase 7 completa: Normalización y Relaciones")
    
    try:
        # Fase 7A: Normalización
        resultado_normalizacion = ejecutar_fase_7a_normalizacion(
            entidades,
            supabase_service
        )
        
        entidades_normalizadas = resultado_normalizacion["entidades_normalizadas"]
        
        # Fase 7B: Relaciones (ejecutar async en thread separado)
        def run_async_in_thread():
            return asyncio.run(ejecutar_fase_7b_relaciones(
                hechos,
                entidades_normalizadas,
                texto_simplificado,
                contexto_articulo,
                groq_api_key
            ))

        with ThreadPoolExecutor() as executor:
            future = executor.submit(run_async_in_thread)
            resultado_relaciones = future.result()
        
        # Crear resultado final
        resultado = ResultadoFase4Normalizacion(
            id_resultado_normalizacion=str(uuid4()),
            id_fragmento=hechos[0].id_fragmento_origen if hechos else str(uuid4()),
            entidades_normalizadas=entidades_normalizadas,
            resumen_normalizacion=f"Normalizadas {resultado_normalizacion['estadisticas']['normalizadas']}/{len(entidades)} entidades",
            estado_general_normalizacion="Completo",
            metadata_normalizacion={
                "estadisticas_normalizacion": resultado_normalizacion["estadisticas"],
                "relaciones_detectadas": {
                    "hecho_entidad": len(resultado_relaciones["relaciones_estructurales"].get("hecho_entidad", [])),
                    "entidad_relacion": len(resultado_relaciones["relaciones_estructurales"].get("entidad_relacion", [])),
                    "hecho_hecho": len(resultado_relaciones["relaciones_temporales"].get("hecho_relacionado", [])),
                    "contradicciones": len(resultado_relaciones["relaciones_temporales"].get("contradicciones", []))
                },
                "relaciones_completas": resultado_relaciones
            }
        )
        
        logger.info("Fase 7 completada exitosamente")
        return resultado
        
    except Exception as e:
        logger.error(f"Error en Fase 7: {str(e)}")
        error_info = handle_generic_phase_error(
            article_id=str(hechos[0].id_fragmento_origen if hechos else "unknown"),
            phase=ErrorPhase.FASE_4_NORMALIZACION,
            step_failed="normalizacion_relaciones",
            exception=e
        )
        
        # Retornar resultado con error
        return ResultadoFase4Normalizacion(
            id_resultado_normalizacion=str(uuid4()),
            id_fragmento=hechos[0].id_fragmento_origen if hechos else str(uuid4()),
            entidades_normalizadas=entidades,  # Sin normalizar
            estado_general_normalizacion="Fallido",
            metadata_normalizacion={"error": str(error_info)}
        )