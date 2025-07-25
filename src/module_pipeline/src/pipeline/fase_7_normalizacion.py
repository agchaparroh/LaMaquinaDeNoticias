"""
Fase 7: Normalización y Vinculación
===================================

Esta fase incluye:
- 7A: Normalización de entidades (Supabase)
- 7B: Detección de relaciones (paralelo)
  - 7B.1: Relaciones estructurales
  - 7B.2: Relaciones temporales
"""

import asyncio
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple  # noqa: F401
from uuid import UUID, uuid4  # noqa: F401

from ..utils.logging_config import get_logger

# Configurar logger para este módulo
logger = get_logger("Fase7_Normalizacion")

# Importar modelos
from ..models.procesamiento import (  # noqa: E402
    CitaTextual,
    ContradiccionDetectada,
    DatosCuantitativos,
    EntidadEntidadRelacion,
    EntidadProcesada,
    HechoEntidadRelacion,
    HechoHechoRelacion,
    HechoProcesado,
    ResultadoFase4Normalizacion,
)

# Importar servicios
from ..services.entity_normalizer import NormalizadorEntidades  # noqa: E402
from ..services.supabase_service import SupabaseService  # noqa: E402

# Importar utilidades
from ..utils.error_handling import (  # noqa: E402
    ErrorPhase,
    GroqAPIError,  # noqa: F401
    ProcessingError,  # noqa: F401
    SupabaseRPCError,  # noqa: F401
    handle_generic_phase_error,
)
from ..utils.json_parser import parse_llm_json_response  # noqa: E402
from ..utils.validador_relaciones_post7b import ValidadorRelacionesPost7B  # noqa: E402
from ..utils.validation import (  # noqa: E402
    escape_html,  # noqa: F401
    sanitize_entity_name,  # noqa: F401
    validate_date_optional,  # noqa: F401
    validate_wikidata_uri,  # noqa: F401
)

# Importar servicio Groq
try:
    from groq import Groq
except ImportError:
    Groq = None


# Rutas a los prompts de relaciones
_PROMPT_RELACIONES_ESTRUCTURALES_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "prompts"
    / "7B.1_Relaciones-Estructurales.md"
)
_PROMPT_RELACIONES_TEMPORALES_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "prompts"
    / "7B.2_Relaciones-Temporales.md"
)

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

        with open(_PROMPT_RELACIONES_ESTRUCTURALES_PATH, encoding="utf-8") as f:
            _PROMPT_RELACIONES_ESTRUCTURALES = f.read()

        logger.info(f"Prompt de relaciones estructurales cargado")  # noqa: F541

    return _PROMPT_RELACIONES_ESTRUCTURALES


def _cargar_prompt_relaciones_temporales() -> str:
    """Carga el prompt de relaciones temporales."""
    global _PROMPT_RELACIONES_TEMPORALES

    if _PROMPT_RELACIONES_TEMPORALES is None:
        if not _PROMPT_RELACIONES_TEMPORALES_PATH.exists():
            raise FileNotFoundError(
                f"No se encontró el archivo de prompt en: {_PROMPT_RELACIONES_TEMPORALES_PATH}"
            )

        with open(_PROMPT_RELACIONES_TEMPORALES_PATH, encoding="utf-8") as f:
            _PROMPT_RELACIONES_TEMPORALES = f.read()

        logger.info(f"Prompt de relaciones temporales cargado")  # noqa: F541

    return _PROMPT_RELACIONES_TEMPORALES


def _preparar_contexto_relaciones(
    hechos: List[HechoProcesado], entidades: List[EntidadProcesada]
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
                "contenido": h.contenido,
                "tipo": h.metadata_hecho.tipo_hecho,
            }
            for h in hechos
        ],
        "entidades": [
            {"id": e.id_entidad, "nombre": e.nombre, "tipo": e.tipo} for e in entidades
        ],
    }

    return json.dumps(contexto, ensure_ascii=False, indent=2)


def _preparar_contexto_temporal(hechos: List[HechoProcesado]) -> str:
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
                "contenido": h.contenido,
                "fecha_inicio": h.fecha_inicio,
                "fecha_fin": h.fecha_fin,
                "tipo": h.tipo_hecho,
            }
            for h in hechos
        ]
    }

    return json.dumps(contexto, ensure_ascii=False, indent=2)


async def _detectar_relaciones_estructurales(
    hechos: List[HechoProcesado],
    entidades: List[EntidadProcesada],
    contexto_articulo: Dict[str, Any],
    groq_api_key: str,
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
            logger.info(
                f"Usando modelo grande para relaciones estructurales ({tokens_estimados} tokens)"
            )

        # Preparar prompt
        prompt = _cargar_prompt_relaciones_estructurales()
        prompt = prompt.replace(
            "{{TITULO_O_DOCUMENTO}}", contexto_articulo.get("titulo", "No disponible")
        )
        prompt = prompt.replace(
            "{{FUENTE_O_TIPO}}", contexto_articulo.get("fuente", "No disponible")
        )
        prompt = prompt.replace(
            "{{PAIS_ORIGEN}}", contexto_articulo.get("pais", "No disponible")
        )
        prompt = prompt.replace(
            "{{FECHA_FUENTE}}",
            contexto_articulo.get("fecha_publicacion", "No disponible"),
        )
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
                        "content": "Eres un experto en análisis de relaciones en textos periodísticos. Identificas con precisión las conexiones entre hechos y entidades.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=4000,
                response_format={"type": "json_object"},
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
                "tokens_prompt": response.usage.prompt_tokens
                if response.usage
                else None,
                "tokens_respuesta": response.usage.completion_tokens
                if response.usage
                else None,
            },
        }

    except Exception as e:
        logger.error(f"Error detectando relaciones estructurales: {str(e)}")
        return {
            "relaciones": {"hecho_entidad": [], "entidad_relacion": []},
            "error": str(e),
        }


async def _detectar_relaciones_temporales(
    hechos: List[HechoProcesado],
    texto_simplificado: str,
    contexto_articulo: Dict[str, Any],
    groq_api_key: str,
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
            logger.info(
                f"Usando modelo grande para relaciones temporales ({tokens_estimados} tokens)"
            )

        # Preparar prompt
        prompt = _cargar_prompt_relaciones_temporales()
        prompt = prompt.replace(
            "{{TITULO_O_DOCUMENTO}}", contexto_articulo.get("titulo", "No disponible")
        )
        prompt = prompt.replace(
            "{{FUENTE_O_TIPO}}", contexto_articulo.get("fuente", "No disponible")
        )
        prompt = prompt.replace(
            "{{PAIS_ORIGEN}}", contexto_articulo.get("pais", "No disponible")
        )
        prompt = prompt.replace(
            "{{FECHA_FUENTE}}",
            contexto_articulo.get("fecha_publicacion", "No disponible"),
        )
        prompt = prompt.replace("{{HECHOS_CONTEXTO}}", contexto_hechos)
        prompt = prompt.replace(
            "{{TEXTO_SIMPLIFICADO}}", texto_simplificado[:3000]
        )  # Limitar contexto

        # Llamar a Groq
        client = Groq(api_key=groq_api_key)

        inicio = datetime.now()
        response = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model=modelo,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto en análisis temporal y causal de eventos. Identificas relaciones temporales y contradicciones con precisión.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=4000,
                response_format={"type": "json_object"},
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
                "tokens_prompt": response.usage.prompt_tokens
                if response.usage
                else None,
                "tokens_respuesta": response.usage.completion_tokens
                if response.usage
                else None,
            },
        }

    except Exception as e:
        logger.error(f"Error detectando relaciones temporales: {str(e)}")
        return {
            "relaciones": {"hecho_relacionado": [], "contradicciones": []},
            "error": str(e),
        }


def ejecutar_fase_7a_normalizacion(
    entidades: List[EntidadProcesada],
    supabase_service: Optional[SupabaseService] = None,
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
        "errores": 0,
    }

    for entidad in entidades:
        try:
            # Intentar normalizar
            resultado = normalizador.normalizar_entidad(
                nombre_entidad=entidad.nombre,
                tipo_entidad=entidad.tipo,
                # Removido metadata - no es un parámetro válido
            )

            if not resultado["es_nueva"]:
                # Actualizar entidad con información normalizada
                entidad.id_entidad_normalizada = resultado["id_entidad_normalizada"]
                entidad.nombre_entidad_normalizada = resultado["nombre_normalizado"]
                entidad.uri_wikidata = resultado.get(
                    "uri_wikidata"
                )  # Este campo puede no existir
                entidad.similitud_normalizacion = resultado["score_similitud"]
                estadisticas["normalizadas"] += 1
            else:
                estadisticas["no_encontradas"] += 1

            entidades_normalizadas.append(entidad)

        except Exception as e:
            logger.error(f"Error normalizando entidad {entidad.nombre}: {str(e)}")
            estadisticas["errores"] += 1
            entidades_normalizadas.append(entidad)

    logger.info(
        f"Fase 7A completada: {estadisticas['normalizadas']} normalizadas, "
        f"{estadisticas['no_encontradas']} no encontradas, "
        f"{estadisticas['errores']} errores"
    )

    return {
        "entidades_normalizadas": entidades_normalizadas,
        "estadisticas": estadisticas,
    }


async def ejecutar_fase_7b_relaciones(
    hechos: List[HechoProcesado],
    entidades: List[EntidadProcesada],
    texto_simplificado: str,
    contexto_articulo: Dict[str, Any],
    groq_api_key: Optional[str] = None,
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
        tarea_estructurales, tarea_temporales, return_exceptions=True
    )

    duracion_total_ms = int((datetime.now() - inicio).total_seconds() * 1000)

    # Procesar resultados
    resultado_estructurales = (
        resultados[0]
        if not isinstance(resultados[0], Exception)
        else {"error": str(resultados[0])}
    )
    resultado_temporales = (
        resultados[1]
        if not isinstance(resultados[1], Exception)
        else {"error": str(resultados[1])}
    )

    # Consolidar resultados
    todas_relaciones = {
        "relaciones_estructurales": resultado_estructurales.get("relaciones", {}),
        "relaciones_temporales": resultado_temporales.get("relaciones", {}),
        "metadatos": {
            "duracion_total_ms": duracion_total_ms,
            "paralelo": True,
            "metadatos_estructurales": resultado_estructurales.get("metadatos", {}),
            "metadatos_temporales": resultado_temporales.get("metadatos", {}),
        },
    }

    # COMPLETAR CAMPOS FALTANTES: Agregar información que el LLM no puede generar
    logger.info("Completando campos faltantes en relaciones detectadas")

    # Completar hecho_entidad (agregar fecha_ocurrencia_hecho)
    if "hecho_entidad" in todas_relaciones["relaciones_estructurales"]:
        todas_relaciones["relaciones_estructurales"]["hecho_entidad"] = (
            _completar_campos_hecho_entidad(
                todas_relaciones["relaciones_estructurales"]["hecho_entidad"], hechos
            )
        )

    # Completar hecho_relacionado (agregar fechas de ocurrencia origen/destino)
    if "hecho_relacionado" in todas_relaciones["relaciones_temporales"]:
        todas_relaciones["relaciones_temporales"]["hecho_relacionado"] = (
            _completar_campos_hecho_relacionado(
                todas_relaciones["relaciones_temporales"]["hecho_relacionado"], hechos
            )
        )

    # Completar contradicciones (agregar fechas, estado_resolucion, fecha_deteccion)
    if "contradicciones" in todas_relaciones["relaciones_temporales"]:
        todas_relaciones["relaciones_temporales"]["contradicciones"] = (
            _completar_campos_contradicciones(
                todas_relaciones["relaciones_temporales"]["contradicciones"], hechos
            )
        )

    # VALIDACIÓN POST-7B: Aplicar validador de relaciones
    logger.info("Aplicando validación post-7B a las relaciones detectadas")
    validador = ValidadorRelacionesPost7B()

    # Preparar datos para validación
    datos_para_validar = {
        "entidad_relacion": todas_relaciones["relaciones_estructurales"].get(
            "entidad_relacion", []
        ),
        "hecho_entidad": todas_relaciones["relaciones_estructurales"].get(
            "hecho_entidad", []
        ),
        "hecho_relacionado": todas_relaciones["relaciones_temporales"].get(
            "hecho_relacionado", []
        ),
        "contradicciones": todas_relaciones["relaciones_temporales"].get(
            "contradicciones", []
        ),
    }

    # Validar y corregir
    datos_validados = validador.validar_y_corregir(datos_para_validar)

    # Obtener estadísticas de validación
    estadisticas_validacion = validador.obtener_estadisticas(
        datos_para_validar, datos_validados
    )

    # Actualizar con datos validados
    todas_relaciones["relaciones_estructurales"]["entidad_relacion"] = datos_validados[
        "entidad_relacion"
    ]
    todas_relaciones["relaciones_estructurales"]["hecho_entidad"] = datos_validados[
        "hecho_entidad"
    ]
    todas_relaciones["relaciones_temporales"]["hecho_relacionado"] = datos_validados[
        "hecho_relacionado"
    ]
    todas_relaciones["relaciones_temporales"]["contradicciones"] = datos_validados[
        "contradicciones"
    ]

    # Agregar estadísticas de validación a metadatos
    todas_relaciones["metadatos"]["validacion_post_7b"] = estadisticas_validacion

    logger.info(
        f"Validación post-7B completada: "
        f"{estadisticas_validacion['entidad_relacion']['descartadas']} relaciones entidad-entidad descartadas, "
        f"{estadisticas_validacion['entidad_relacion']['corregidas']} corregidas"
    )

    # Contar relaciones
    total_relaciones = (
        len(todas_relaciones["relaciones_estructurales"].get("hecho_entidad", []))
        + len(todas_relaciones["relaciones_estructurales"].get("entidad_relacion", []))
        + len(todas_relaciones["relaciones_temporales"].get("hecho_relacionado", []))
        + len(todas_relaciones["relaciones_temporales"].get("contradicciones", []))
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
    supabase_service: Optional[SupabaseService] = None,
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
            entidades, supabase_service
        )

        entidades_normalizadas = resultado_normalizacion["entidades_normalizadas"]

        # Fase 7B: Relaciones (ejecutar async en thread separado)
        def run_async_in_thread():
            return asyncio.run(
                ejecutar_fase_7b_relaciones(
                    hechos,
                    entidades_normalizadas,
                    texto_simplificado,
                    contexto_articulo,
                    groq_api_key,
                )
            )

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
                    "hecho_entidad": len(
                        resultado_relaciones["relaciones_estructurales"].get(
                            "hecho_entidad", []
                        )
                    ),
                    "entidad_relacion": len(
                        resultado_relaciones["relaciones_estructurales"].get(
                            "entidad_relacion", []
                        )
                    ),
                    "hecho_hecho": len(
                        resultado_relaciones["relaciones_temporales"].get(
                            "hecho_relacionado", []
                        )
                    ),
                    "contradicciones": len(
                        resultado_relaciones["relaciones_temporales"].get(
                            "contradicciones", []
                        )
                    ),
                },
                "relaciones_completas": resultado_relaciones,
            },
        )

        logger.info("Fase 7 completada exitosamente")
        return resultado

    except Exception as e:
        logger.error(f"Error en Fase 7: {str(e)}")
        error_info = handle_generic_phase_error(
            article_id=str(hechos[0].id_fragmento_origen if hechos else "unknown"),
            phase=ErrorPhase.FASE_4_NORMALIZACION,
            step_failed="normalizacion_relaciones",
            exception=e,
        )

        # Retornar resultado con error
        return ResultadoFase4Normalizacion(
            id_resultado_normalizacion=str(uuid4()),
            id_fragmento=hechos[0].id_fragmento_origen if hechos else str(uuid4()),
            entidades_normalizadas=entidades,  # Sin normalizar
            estado_general_normalizacion="Fallido",
            metadata_normalizacion={"error": str(error_info)},
        )


def _completar_campos_hecho_entidad(
    relaciones_hecho_entidad: List[Dict[str, Any]], hechos: List[HechoProcesado]
) -> List[Dict[str, Any]]:
    """
    Completa los campos faltantes para relaciones hecho-entidad.

    Agrega fecha_ocurrencia_hecho desde el hecho correspondiente.

    Args:
        relaciones_hecho_entidad: Lista de relaciones detectadas por LLM
        hechos: Lista de hechos procesados

    Returns:
        Lista de relaciones con campos completados
    """
    # Crear índice de hechos por ID
    hechos_dict = {h.id_hecho: h for h in hechos}

    relaciones_completas = []

    for relacion in relaciones_hecho_entidad:
        hecho_id = relacion.get("hecho_id")
        if hecho_id not in hechos_dict:
            logger.warning(
                f"Hecho {hecho_id} no encontrado para relación hecho-entidad"
            )
            continue

        hecho = hechos_dict[hecho_id]

        # Crear tstzrange desde fecha_inicio/fecha_fin del hecho
        fecha_ocurrencia_hecho = (
            f"[{hecho.fecha_inicio} 00:00:00+00,{hecho.fecha_fin} 23:59:59+00)"
        )

        relacion_completa = {
            "hecho_id": hecho_id,
            "fecha_ocurrencia_hecho": fecha_ocurrencia_hecho,
            "entidad_id": relacion.get("entidad_id"),
            "tipo_relacion": relacion.get("tipo_relacion", "otro"),
            "relevancia_en_hecho": relacion.get("relevancia_en_hecho", 5),
        }

        relaciones_completas.append(relacion_completa)

    logger.info(
        f"Completados campos para {len(relaciones_completas)} relaciones hecho-entidad"
    )
    return relaciones_completas


def _completar_campos_hecho_relacionado(
    relaciones_hecho_relacionado: List[Dict[str, Any]], hechos: List[HechoProcesado]
) -> List[Dict[str, Any]]:
    """
    Completa los campos faltantes para relaciones hecho-hecho.

    Agrega fecha_ocurrencia_origen y fecha_ocurrencia_destino desde los hechos correspondientes.

    Args:
        relaciones_hecho_relacionado: Lista de relaciones detectadas por LLM
        hechos: Lista de hechos procesados

    Returns:
        Lista de relaciones con campos completados
    """
    # Crear índice de hechos por ID
    hechos_dict = {h.id_hecho: h for h in hechos}

    relaciones_completas = []

    for relacion in relaciones_hecho_relacionado:
        hecho_origen_id = relacion.get("hecho_origen_id")
        hecho_destino_id = relacion.get("hecho_destino_id")

        if hecho_origen_id not in hechos_dict:
            logger.warning(
                f"Hecho origen {hecho_origen_id} no encontrado para relación hecho-hecho"
            )
            continue

        if hecho_destino_id not in hechos_dict:
            logger.warning(
                f"Hecho destino {hecho_destino_id} no encontrado para relación hecho-hecho"
            )
            continue

        hecho_origen = hechos_dict[hecho_origen_id]
        hecho_destino = hechos_dict[hecho_destino_id]

        # Crear tstzrange para ambos hechos
        fecha_ocurrencia_origen = f"[{hecho_origen.fecha_inicio} 00:00:00+00,{hecho_origen.fecha_fin} 23:59:59+00)"
        fecha_ocurrencia_destino = f"[{hecho_destino.fecha_inicio} 00:00:00+00,{hecho_destino.fecha_fin} 23:59:59+00)"

        relacion_completa = {
            "hecho_origen_id": hecho_origen_id,
            "fecha_ocurrencia_origen": fecha_ocurrencia_origen,
            "hecho_destino_id": hecho_destino_id,
            "fecha_ocurrencia_destino": fecha_ocurrencia_destino,
            "tipo_relacion": relacion.get("tipo_relacion", "contexto_historico"),
            "fuerza_relacion": relacion.get("fuerza_relacion", 5),
            "descripcion_relacion": relacion.get("descripcion_relacion", ""),
        }

        relaciones_completas.append(relacion_completa)

    logger.info(
        f"Completados campos para {len(relaciones_completas)} relaciones hecho-hecho"
    )
    return relaciones_completas


def _completar_campos_contradicciones(
    contradicciones: List[Dict[str, Any]], hechos: List[HechoProcesado]
) -> List[Dict[str, Any]]:
    """
    Completa los campos faltantes para contradicciones.

    Agrega fechas de ocurrencia, estado_resolucion y fecha_deteccion.

    Args:
        contradicciones: Lista de contradicciones detectadas por LLM
        hechos: Lista de hechos procesados

    Returns:
        Lista de contradicciones con campos completados
    """
    # Crear índice de hechos por ID
    hechos_dict = {h.id_hecho: h for h in hechos}

    contradicciones_completas = []
    fecha_deteccion_actual = datetime.now().isoformat()

    for contradiccion in contradicciones:
        hecho_principal_id = contradiccion.get("hecho_principal_id")
        hecho_contradictorio_id = contradiccion.get("hecho_contradictorio_id")

        if hecho_principal_id not in hechos_dict:
            logger.warning(
                f"Hecho principal {hecho_principal_id} no encontrado para contradicción"
            )
            continue

        if hecho_contradictorio_id not in hechos_dict:
            logger.warning(
                f"Hecho contradictorio {hecho_contradictorio_id} no encontrado para contradicción"
            )
            continue

        hecho_principal = hechos_dict[hecho_principal_id]
        hecho_contradictorio = hechos_dict[hecho_contradictorio_id]

        # Crear tstzrange para ambos hechos
        fecha_ocurrencia_principal = f"[{hecho_principal.fecha_inicio} 00:00:00+00,{hecho_principal.fecha_fin} 23:59:59+00)"
        fecha_ocurrencia_contradictoria = f"[{hecho_contradictorio.fecha_inicio} 00:00:00+00,{hecho_contradictorio.fecha_fin} 23:59:59+00)"

        contradiccion_completa = {
            "hecho_principal_id": hecho_principal_id,
            "fecha_ocurrencia_principal": fecha_ocurrencia_principal,
            "hecho_contradictorio_id": hecho_contradictorio_id,
            "fecha_ocurrencia_contradictoria": fecha_ocurrencia_contradictoria,
            "tipo_contradiccion": contradiccion.get("tipo_contradiccion", "contenido"),
            "grado_contradiccion": contradiccion.get("grado_contradiccion", 3),
            "descripcion": contradiccion.get("descripcion", ""),
            "estado_resolucion": "pendiente",  # Default
            "fecha_deteccion": fecha_deteccion_actual,
        }

        contradicciones_completas.append(contradiccion_completa)

    logger.info(
        f"Completados campos para {len(contradicciones_completas)} contradicciones"
    )
    return contradicciones_completas


def _convertir_a_modelos_pydantic(
    relaciones_validadas: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Convierte los diccionarios validados a modelos Pydantic para validación adicional.

    NOTA: Esta función es opcional. Los diccionarios validados ya están listos
    para persistencia, pero si se requiere validación adicional con Pydantic,
    esta función puede ser útil.

    Args:
        relaciones_validadas: Diccionario con relaciones validadas

    Returns:
        Diccionario con objetos Pydantic o listas vacías si hay errores
    """
    resultado = {
        "hecho_entidad": [],
        "entidad_relacion": [],
        "hecho_relacionado": [],
        "contradicciones": [],
    }

    # Convertir hecho_entidad
    for rel in relaciones_validadas.get("hecho_entidad", []):
        try:
            obj = HechoEntidadRelacion(**rel)
            resultado["hecho_entidad"].append(obj.model_dump())
        except Exception as e:
            logger.error(f"Error creando HechoEntidadRelacion: {e}")
            continue

    # Convertir entidad_relacion
    for rel in relaciones_validadas.get("entidad_relacion", []):
        try:
            obj = EntidadEntidadRelacion(**rel)
            resultado["entidad_relacion"].append(obj.model_dump())
        except Exception as e:
            logger.error(f"Error creando EntidadEntidadRelacion: {e}")
            continue

    # Convertir hecho_relacionado
    for rel in relaciones_validadas.get("hecho_relacionado", []):
        try:
            obj = HechoHechoRelacion(**rel)
            resultado["hecho_relacionado"].append(obj.model_dump())
        except Exception as e:
            logger.error(f"Error creando HechoHechoRelacion: {e}")
            continue

    # Convertir contradicciones
    for cont in relaciones_validadas.get("contradicciones", []):
        try:
            obj = ContradiccionDetectada(**cont)
            resultado["contradicciones"].append(obj.model_dump())
        except Exception as e:
            logger.error(f"Error creando ContradiccionDetectada: {e}")
            continue

    return resultado
