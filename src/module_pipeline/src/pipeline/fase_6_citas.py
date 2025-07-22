"""
Fase 6: Extracción de Citas Textuales
=====================================

Esta fase extrae citas textuales del texto cuando se detectan
declaraciones significativas, usando el contexto de hechos y entidades.
"""

from typing import Optional, List, Dict, Any, Tuple
from uuid import uuid4
from datetime import datetime
import os
import json
import asyncio
from pathlib import Path

from ..utils.logging_config import get_logger

# Configurar logger para este módulo
logger = get_logger("Fase6_Citas")

# Importar modelos
from ..models.procesamiento import (
    CitaTextual,
    HechoProcesado,
    EntidadProcesada
)
from ..models.simplificacion import ResultadoFase2Simplificacion
from ..models.metadatos import MetadatosCita

# Importar utilidades
from ..utils.error_handling import (
    handle_generic_phase_error,
    ErrorPhase,
    GroqAPIError,
    ProcessingError
)
from ..utils.json_parser import parse_llm_json_response
from ..utils.validation import escape_html
from ..utils.fragment_processor import FragmentProcessor

# Importar servicio Groq
try:
    from groq import Groq
except ImportError:
    Groq = None


# Ruta al prompt de citas
_PROMPT_CITAS_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "Citas.md"
_PROMPT_CITAS_TEMPLATE: Optional[str] = None


def _cargar_prompt_citas() -> str:
    """
    Carga el prompt de extracción de citas desde el archivo.
    
    Returns:
        Contenido del prompt de citas
        
    Raises:
        FileNotFoundError: Si no se encuentra el archivo del prompt
    """
    global _PROMPT_CITAS_TEMPLATE
    
    if _PROMPT_CITAS_TEMPLATE is None:
        if not _PROMPT_CITAS_PATH.exists():
            raise FileNotFoundError(
                f"No se encontró el archivo de prompt en: {_PROMPT_CITAS_PATH}"
            )
        
        with open(_PROMPT_CITAS_PATH, "r", encoding="utf-8") as f:
            _PROMPT_CITAS_TEMPLATE = f.read()
            
        logger.info(f"Prompt de citas cargado desde: {_PROMPT_CITAS_PATH}")
    
    return _PROMPT_CITAS_TEMPLATE


def _preparar_contexto_referencias(
    hechos: List[HechoProcesado],
    entidades: List[EntidadProcesada]
) -> Tuple[str, str]:
    """
    Prepara el contexto de hechos y entidades para el prompt.
    
    Args:
        hechos: Lista de hechos extraídos
        entidades: Lista de entidades extraídas
        
    Returns:
        Tupla (json_hechos, json_entidades)
    """
    # Formatear hechos como JSON simple
    hechos_json = []
    for hecho in hechos:
        hechos_json.append({
            "id": hecho.id_hecho,
            "contenido": hecho.texto_original_del_hecho,
            "tipo": hecho.metadata_hecho.tipo_hecho
        })
    
    # Formatear entidades como JSON simple
    entidades_json = []
    for entidad in entidades:
        entidades_json.append({
            "id": entidad.id_entidad,
            "nombre": entidad.texto_entidad,
            "tipo": entidad.tipo_entidad
        })
    
    return json.dumps(hechos_json, ensure_ascii=False, indent=2), \
           json.dumps(entidades_json, ensure_ascii=False, indent=2)


def _preparar_prompt_citas(
    texto_simplificado: str,
    hechos_json: str,
    entidades_json: str,
    titulo: str = "No disponible",
    fuente: str = "No disponible",
    fecha_publicacion: str = "No disponible"
) -> str:
    """
    Prepara el prompt de extracción de citas con el contexto.
    
    Args:
        texto_simplificado: Texto procesado en fase 2
        hechos_json: JSON de hechos extraídos
        entidades_json: JSON de entidades extraídas
        titulo: Título del artículo
        fuente: Fuente del artículo
        fecha_publicacion: Fecha de publicación
        
    Returns:
        Prompt completo para el LLM
    """
    prompt = _cargar_prompt_citas()
    
    # Reemplazar placeholders
    prompt = prompt.replace("{{TITULO}}", titulo)
    prompt = prompt.replace("{{FUENTE}}", fuente)
    prompt = prompt.replace("{{FECHA_FUENTE}}", fecha_publicacion)
    prompt = prompt.replace("{{CONTENIDO}}", texto_simplificado)
    prompt = prompt.replace("{{Fase4_Hechos}}", hechos_json)
    prompt = prompt.replace("{{Fase3_Entidades}}", entidades_json)
    
    return prompt


async def _llamar_groq_citas_async(
    client: Any,
    prompt: str,
    modelo: str = "llama-3.1-8b-instant",
    max_retries: int = 3
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Versión asíncrona de llamada a Groq para extraer citas textuales.
    """
    import time
    
    for attempt in range(max_retries):
        inicio = datetime.now()
        
        try:
            if attempt > 0:
                await asyncio.sleep(2 ** (attempt - 1))  # Exponential backoff
            
            response = client.chat.completions.create(
                model=modelo,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto en extracción de citas textuales de textos periodísticos. Identificas declaraciones exactas, atribuciones y contexto con precisión."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=6000,
                response_format={"type": "json_object"}
            )
            
            duracion_ms = int((datetime.now() - inicio).total_seconds() * 1000)
            respuesta_texto = response.choices[0].message.content
            respuesta_parseada = parse_llm_json_response(respuesta_texto)
            
            metadatos = {
                "nombre_modelo": modelo,
                "tokens_prompt": response.usage.prompt_tokens if response.usage else None,
                "tokens_respuesta": response.usage.completion_tokens if response.usage else None,
                "duracion_llamada_ms": duracion_ms
            }
            
            return respuesta_parseada, metadatos
            
        except Exception as e:
            logger.error(f"Error en llamada a Groq (intento {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                continue
            raise GroqAPIError(f"Error al extraer citas después de {max_retries} intentos: {str(e)}")


def _llamar_groq_citas(
    client: Any,
    prompt: str,
    modelo: str = "llama-3.1-8b-instant",
    max_retries: int = 3
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Llama a la API de Groq para extraer citas textuales.
    
    Args:
        client: Cliente de Groq
        prompt: Prompt con el texto
        modelo: Modelo a usar
        max_retries: Número máximo de reintentos
        
    Returns:
        Tupla (respuesta_parseada, metadatos_llamada)
    """
    import time
    
    for attempt in range(max_retries):
        inicio = datetime.now()
        
        try:
            response = client.chat.completions.create(
                model=modelo,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto en análisis de citas textuales en textos periodísticos. Extraes declaraciones exactas, identificando correctamente quién las dijo y en qué contexto, vinculándolas con hechos y entidades."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Baja temperatura para precisión
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            duracion_ms = int((datetime.now() - inicio).total_seconds() * 1000)
            
            respuesta_texto = response.choices[0].message.content
            
            # Parsear respuesta JSON
            respuesta_parseada = parse_llm_json_response(respuesta_texto)
            
            metadatos = {
                "nombre_modelo": modelo,
                "tokens_prompt": response.usage.prompt_tokens if response.usage else None,
                "tokens_respuesta": response.usage.completion_tokens if response.usage else None,
                "duracion_llamada_ms": duracion_ms
            }
            
            return respuesta_parseada, metadatos
            
        except Exception as e:
            logger.error(f"Error en llamada a Groq (intento {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            raise GroqAPIError(f"Error al extraer citas después de {max_retries} intentos: {str(e)}")


def _procesar_citas_extraidas(
    citas_raw: List[Dict[str, Any]],
    id_fragmento: str,  # Ahora acepta string (ART-ID o UUID)
    fragment_processor: FragmentProcessor
) -> List[CitaTextual]:
    """
    Procesa las citas extraídas del LLM a objetos CitaTextual.
    
    Args:
        citas_raw: Lista de citas del LLM
        id_fragmento: ID del fragmento procesado
        fragment_processor: Procesador de fragmentos para IDs
        
    Returns:
        Lista de CitaTextual
    """
    citas_procesadas = []
    
    for cita in citas_raw:
        try:
            # Crear metadatos específicos
            metadatos = MetadatosCita(
                cita_textual=cita.get("cita", ""),
                entidad_emisora_id=cita.get("entidad_id"),
                hecho_relacionado_id=cita.get("hecho_id"),
                fecha_cita=cita.get("fecha"),
                contexto=cita.get("contexto"),
                relevancia=cita.get("relevancia", 3)
            )
            
            # Determinar persona citada
            persona_citada = None
            if cita.get("entidad_id") is not None:
                # Aquí podríamos buscar el nombre de la entidad
                # Por ahora usamos un placeholder
                persona_citada = f"Entidad {cita.get('entidad_id')}"
            
            # Crear cita textual
            cita_procesada = CitaTextual(
                id_cita=cita.get("id", 0),
                id_fragmento_origen=id_fragmento,
                texto_cita=cita.get("cita", ""),
                persona_citada=persona_citada,
                id_entidad_citada=cita.get("entidad_id"),
                contexto_cita=cita.get("contexto"),
                metadata_cita=metadatos
            )
            
            citas_procesadas.append(cita_procesada)
            
        except Exception as e:
            logger.warning(f"Error procesando cita {cita.get('id')}: {str(e)}")
            continue
    
    return citas_procesadas


def ejecutar_fase_6_citas(
    resultado_simplificacion: ResultadoFase2Simplificacion,
    hechos_extraidos: List[HechoProcesado],
    entidades_extraidas: List[EntidadProcesada],
    contexto_articulo: Optional[Dict[str, Any]] = None,
    groq_api_key: Optional[str] = None,
    ejecutar_siempre: bool = False
) -> Dict[str, Any]:
    """
    Ejecuta la Fase 6: Extracción de Citas Textuales.
    
    Esta fase es condicional y solo se ejecuta si hay citas detectadas
    en el texto (conteo_citas > 0 o es_entrevista).
    
    Args:
        resultado_simplificacion: Resultado de la fase 2 con texto simplificado
        hechos_extraidos: Hechos extraídos en fase 4
        entidades_extraidas: Entidades extraídas en fase 3
        contexto_articulo: Contexto del artículo (título, fuente, etc.)
        groq_api_key: API key de Groq (opcional, usa variable de entorno)
        ejecutar_siempre: Si True, ejecuta aunque no haya citas detectadas
        
    Returns:
        Diccionario con citas extraídas y metadatos
        
    Raises:
        ProcessingError: Si hay errores en el procesamiento
    """
    logger.info(f"Iniciando Fase 6: Extracción de Citas para fragmento {resultado_simplificacion.id_fragmento}")
    
    # Verificar si debe ejecutarse
    conteo_citas = contexto_articulo.get("conteo_citas", 0) if contexto_articulo else 0
    es_entrevista = contexto_articulo.get("es_entrevista", False) if contexto_articulo else False
    
    if not ejecutar_siempre and conteo_citas == 0 and not es_entrevista:
        logger.info("No se detectaron citas textuales. Saltando fase 6.")
        return {
            "id_fragmento": resultado_simplificacion.id_fragmento,
            "citas_extraidas": [],
            "total_citas": 0,
            "fase_omitida": True,
            "razon": "No se detectaron citas textuales en el análisis previo",
            "metadatos_extraccion": {
                "fase": "fase_6_citas",
                "omitida": True,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    try:
        # Validar entrada
        if not resultado_simplificacion.texto_simplificado:
            raise ValueError("No hay texto simplificado disponible para extraer citas")
        
        # Obtener API key
        api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("No se encontró GROQ_API_KEY")
        
        # Inicializar cliente Groq
        if Groq is None:
            raise ImportError("El paquete 'groq' no está instalado")
        
        client = Groq(api_key=api_key)
        
        # Obtener contexto del artículo
        contexto = contexto_articulo or {}
        
        # Preparar contexto de referencias
        hechos_json, entidades_json = _preparar_contexto_referencias(
            hechos_extraidos,
            entidades_extraidas
        )
        
        # Preparar prompt
        prompt = _preparar_prompt_citas(
            texto_simplificado=resultado_simplificacion.texto_simplificado,
            hechos_json=hechos_json,
            entidades_json=entidades_json,
            titulo=contexto.get("titulo", "No disponible"),
            fuente=contexto.get("fuente", "No disponible"),
            fecha_publicacion=contexto.get("fecha_publicacion", "No disponible")
        )
        
        # Llamar a Groq
        respuesta, metadatos_llamada = _llamar_groq_citas(client, prompt)
        
        # Obtener citas del response
        citas_raw = respuesta.get("citas_textuales", [])
        logger.info(f"Extraídas {len(citas_raw)} citas textuales")
        
        # Procesar citas
        fragment_processor = FragmentProcessor(resultado_simplificacion.id_fragmento)
        citas_procesadas = _procesar_citas_extraidas(
            citas_raw,
            resultado_simplificacion.id_fragmento,
            fragment_processor
        )
        
        # Vincular nombres de entidades emisoras
        _vincular_nombres_entidades(citas_procesadas, entidades_extraidas)
        
        # Crear resultado
        resultado = {
            "id_fragmento": resultado_simplificacion.id_fragmento,
            "citas_extraidas": citas_procesadas,
            "total_citas": len(citas_procesadas),
            "metadatos_extraccion": {
                "fase": "fase_6_citas",
                "modelo_usado": metadatos_llamada["nombre_modelo"],
                "tokens_prompt": metadatos_llamada.get("tokens_prompt"),
                "tokens_respuesta": metadatos_llamada.get("tokens_respuesta"),
                "duracion_ms": metadatos_llamada["duracion_llamada_ms"],
                "conteo_citas_inicial": conteo_citas,
                "es_entrevista": es_entrevista,
                "timestamp": datetime.now().isoformat()
            },
            "relevancia_promedio": _calcular_relevancia_promedio(citas_procesadas)
        }
        
        logger.info(
            f"Fase 6 completada: {len(citas_procesadas)} citas extraídas. "
            f"Relevancia promedio: {resultado['relevancia_promedio']:.2f}"
        )
        
        return resultado
        
    except Exception as e:
        logger.error(f"Error en Fase 6: {str(e)}")
        error_info = handle_generic_phase_error(
            article_id=str(resultado_simplificacion.id_fragmento),
            phase=ErrorPhase.FASE_3_CITAS_DATOS,  # Ahora es fase 6
            step_failed="extraccion_citas",
            exception=e
        )
        
        # Retornar resultado vacío con error
        return {
            "id_fragmento": resultado_simplificacion.id_fragmento,
            "citas_extraidas": [],
            "total_citas": 0,
            "error": str(error_info),
            "metadatos_extraccion": {
                "fase": "fase_6_citas",
                "error": True,
                "timestamp": datetime.now().isoformat()
            }
        }


def _vincular_nombres_entidades(
    citas: List[CitaTextual],
    entidades: List[EntidadProcesada]
) -> None:
    """
    Vincula los nombres de las entidades emisoras en las citas.
    
    Args:
        citas: Lista de citas procesadas
        entidades: Lista de entidades extraídas
    """
    # Crear diccionario de entidades por ID
    entidades_dict = {e.id_entidad: e for e in entidades}
    
    # Actualizar nombres en citas
    for cita in citas:
        if cita.id_entidad_citada and cita.id_entidad_citada in entidades_dict:
            entidad = entidades_dict[cita.id_entidad_citada]
            cita.persona_citada = entidad.texto_entidad


def _calcular_relevancia_promedio(citas: List[CitaTextual]) -> float:
    """
    Calcula la relevancia promedio de las citas.
    
    Args:
        citas: Lista de citas procesadas
        
    Returns:
        Relevancia promedio
    """
    if not citas:
        return 0.0
    
    total_relevancia = sum(c.metadata_cita.relevancia for c in citas)
    return total_relevancia / len(citas)


async def _procesar_chunk_citas_async(
    chunk_text: str,
    chunk_index: int,
    resultado_simplificacion: ResultadoFase2Simplificacion,
    hechos_chunk: List[HechoProcesado],
    entidades_chunk: List[EntidadProcesada],
    contexto_articulo: Dict[str, Any],
    client: Any,
    fragment_processor: FragmentProcessor
) -> Tuple[List[CitaTextual], Dict[str, Any]]:
    """
    Procesa un chunk individual para extraer citas textuales de forma asíncrona.
    """
    logger.debug(f"Procesando chunk {chunk_index + 1} para citas textuales (async)")
    
    try:
        # Preparar contexto para chunk
        hechos_json = json.dumps([{
            "id": hecho.id_hecho,
            "contenido": hecho.texto_hecho,
            "tipo": hecho.metadata_hecho.tipo_hecho if hasattr(hecho, 'metadata_hecho') and hecho.metadata_hecho else "DESCONOCIDO"
        } for hecho in hechos_chunk], ensure_ascii=False, indent=2)
        
        entidades_json = json.dumps([{
            "id": entidad.id_entidad,
            "nombre": entidad.texto_entidad,
            "tipo": entidad.tipo_entidad
        } for entidad in entidades_chunk], ensure_ascii=False, indent=2)
        
        # Preparar prompt para chunk
        prompt = _preparar_prompt_citas(
            texto_simplificado=chunk_text,
            hechos_contexto=hechos_json,
            entidades_contexto=entidades_json,
            titulo=contexto_articulo.get("titulo", "No disponible"),
            fuente=contexto_articulo.get("fuente", "No disponible"),
            fecha_publicacion=contexto_articulo.get("fecha_publicacion", "No disponible")
        )
        
        # Llamar a Groq de forma asíncrona
        respuesta, metadatos = await _llamar_groq_citas_async(
            client, prompt, "llama-3.1-8b-instant"
        )
        
        # Procesar citas del chunk
        citas_chunk = respuesta.get("citas_textuales", [])
        
        # Ajustar IDs para evitar colisiones entre chunks
        for cita in citas_chunk:
            cita["id"] = cita.get("id", 0) + (chunk_index * 1000)
        
        # Procesar citas
        citas_procesadas = _procesar_citas_extraidas(
            citas_chunk,
            resultado_simplificacion.id_fragmento,
            fragment_processor
        )
        
        logger.debug(f"Chunk {chunk_index + 1}: {len(citas_procesadas)} citas extraídas")
        
        return citas_procesadas, metadatos
        
    except Exception as e:
        logger.error(f"Error procesando chunk {chunk_index + 1} para citas: {str(e)}")
        return [], {"error": str(e), "duracion_llamada_ms": 0}


async def extraer_citas_con_chunking_paralelo(
    resultado_simplificacion: ResultadoFase2Simplificacion,
    chunks: List[str],
    hechos_por_chunk: List[List[HechoProcesado]],
    entidades_por_chunk: List[List[EntidadProcesada]],
    contexto_articulo: Optional[Dict[str, Any]] = None,
    groq_api_key: Optional[str] = None,
    max_concurrent_chunks: int = 5
) -> Dict[str, Any]:
    """
    Extrae citas textuales de chunks procesando en paralelo.
    """
    logger.info(f"Extrayendo citas textuales de {len(chunks)} chunks EN PARALELO")
    inicio_total = datetime.now()
    
    # Validaciones
    api_key = groq_api_key or os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("No se encontró GROQ_API_KEY")
    
    client = Groq(api_key=api_key)
    contexto = contexto_articulo or {}
    fragment_processor = FragmentProcessor(resultado_simplificacion.id_fragmento)
    
    # Procesar chunks en lotes
    todas_las_citas = []
    metadatos_agregados = {
        "tokens_prompt_total": 0,
        "tokens_respuesta_total": 0,
        "duracion_total_ms": 0,
        "chunks_procesados": len(chunks),
        "parallel_batches": 0
    }
    
    # Dividir chunks en lotes según máximo de concurrencia
    for i in range(0, len(chunks), max_concurrent_chunks):
        batch_chunks = chunks[i:i + max_concurrent_chunks]
        batch_indices = list(range(i, min(i + max_concurrent_chunks, len(chunks))))
        
        logger.info(f"Procesando lote {metadatos_agregados['parallel_batches'] + 1}: chunks {i+1}-{i+len(batch_chunks)}")
        
        # Crear tareas asíncronas para el lote
        tasks = []
        for j, chunk_text in enumerate(batch_chunks):
            chunk_idx = batch_indices[j]
            hechos_chunk = hechos_por_chunk[chunk_idx] if chunk_idx < len(hechos_por_chunk) else []
            entidades_chunk = entidades_por_chunk[chunk_idx] if chunk_idx < len(entidades_por_chunk) else []
            
            task = _procesar_chunk_citas_async(
                chunk_text=chunk_text,
                chunk_index=chunk_idx,
                resultado_simplificacion=resultado_simplificacion,
                hechos_chunk=hechos_chunk,
                entidades_chunk=entidades_chunk,
                contexto_articulo=contexto,
                client=client,
                fragment_processor=fragment_processor
            )
            tasks.append(task)
        
        # Ejecutar lote en paralelo
        try:
            resultados_lote = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Procesar resultados del lote
            for k, resultado in enumerate(resultados_lote):
                if isinstance(resultado, Exception):
                    logger.error(f"Error en chunk {batch_indices[k] + 1}: {resultado}")
                    continue
                
                citas, metadatos = resultado
                todas_las_citas.extend(citas)
                
                # Agregar metadatos
                if metadatos.get("tokens_prompt"):
                    metadatos_agregados["tokens_prompt_total"] += metadatos["tokens_prompt"]
                if metadatos.get("tokens_respuesta"):
                    metadatos_agregados["tokens_respuesta_total"] += metadatos["tokens_respuesta"]
                metadatos_agregados["duracion_total_ms"] += metadatos.get("duracion_llamada_ms", 0)
        
        except Exception as e:
            logger.error(f"Error procesando lote de chunks: {str(e)}")
        
        metadatos_agregados["parallel_batches"] += 1
        
        # Pausa breve entre lotes para rate limiting
        if i + max_concurrent_chunks < len(chunks):
            await asyncio.sleep(0.5)
    
    duracion_total = int((datetime.now() - inicio_total).total_seconds() * 1000)
    
    # Crear resultado agregado
    resultado = {
        "id_fragmento": resultado_simplificacion.id_fragmento,
        "citas_extraidas": todas_las_citas,
        "total_citas": len(todas_las_citas),
        "metadatos_extraccion": {
            "fase": "fase_6_citas",
            "modelo_usado": "llama-3.1-8b-instant",
            "tokens_prompt": metadatos_agregados["tokens_prompt_total"],
            "tokens_respuesta": metadatos_agregados["tokens_respuesta_total"],
            "duracion_ms": metadatos_agregados["duracion_total_ms"],
            "duracion_real_ms": duracion_total,
            "chunks_procesados": metadatos_agregados["chunks_procesados"],
            "parallel_batches": metadatos_agregados["parallel_batches"],
            "max_concurrent_chunks": max_concurrent_chunks,
            "parallel_processing": True,
            "timestamp": datetime.now().isoformat()
        },
        "tipos_citas": _contar_tipos_citas(todas_las_citas) if todas_las_citas else {},
        "requiere_consolidacion": True
    }
    
    logger.info(
        f"Procesamiento paralelo completado: {len(todas_las_citas)} citas en {duracion_total}ms "
        f"({metadatos_agregados['parallel_batches']} lotes)"
    )
    
    return resultado


def extraer_citas_con_chunking(
    resultado_simplificacion: ResultadoFase2Simplificacion,
    chunks: List[str],
    hechos_por_chunk: List[List[HechoProcesado]],
    entidades_por_chunk: List[List[EntidadProcesada]],
    contexto_articulo: Optional[Dict[str, Any]] = None,
    groq_api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extrae citas de texto dividido en chunks (versión secuencial - legacy).
    
    Esta función mantiene compatibilidad con el procesamiento secuencial.
    Para aprovechar el procesamiento paralelo, usar extraer_citas_con_chunking_paralelo.
    
    Procesa cada chunk con su contexto local de hechos y entidades.
    
    Args:
        resultado_simplificacion: Resultado de la fase 2
        chunks: Lista de chunks de texto
        hechos_por_chunk: Hechos extraídos por cada chunk
        entidades_por_chunk: Entidades extraídas por cada chunk
        contexto_articulo: Contexto del artículo
        groq_api_key: API key de Groq
        
    Returns:
        Diccionario con todas las citas extraídas
    """
    logger.info(f"Extrayendo citas de {len(chunks)} chunks")
    
    todas_las_citas = []
    metadatos_agregados = {
        "tokens_prompt_total": 0,
        "tokens_respuesta_total": 0,
        "duracion_total_ms": 0,
        "chunks_procesados": 0
    }
    
    api_key = groq_api_key or os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("No se encontró GROQ_API_KEY")
    
    client = Groq(api_key=api_key)
    contexto = contexto_articulo or {}
    fragment_processor = FragmentProcessor(resultado_simplificacion.id_fragmento)
    
    # Procesar cada chunk
    for i, chunk in enumerate(chunks):
        # Verificar si hay contexto en este chunk
        if not hechos_por_chunk[i] and not entidades_por_chunk[i]:
            logger.info(f"Saltando chunk {i+1} - sin hechos ni entidades")
            continue
            
        logger.info(f"Procesando chunk {i+1}/{len(chunks)} para citas")
        
        try:
            # Preparar contexto local del chunk
            hechos_json, entidades_json = _preparar_contexto_referencias(
                hechos_por_chunk[i],
                entidades_por_chunk[i]
            )
            
            # Preparar prompt para chunk
            prompt = _preparar_prompt_citas(
                texto_simplificado=chunk,
                hechos_json=hechos_json,
                entidades_json=entidades_json,
                titulo=contexto.get("titulo", "No disponible"),
                fuente=contexto.get("fuente", "No disponible"),
                fecha_publicacion=contexto.get("fecha_publicacion", "No disponible")
            )
            
            # Llamar a Groq
            respuesta, metadatos = _llamar_groq_citas(
                client, prompt, "llama-3.1-8b-instant"
            )
            
            # Procesar citas del chunk
            citas_chunk = respuesta.get("citas_textuales", [])
            
            # Ajustar IDs para evitar colisiones
            for cita in citas_chunk:
                cita["id"] = cita.get("id", 0) + (i * 1000)
            
            # Procesar citas
            citas_procesadas = _procesar_citas_extraidas(
                citas_chunk,
                resultado_simplificacion.id_fragmento,
                fragment_processor
            )
            
            # Vincular nombres locales
            _vincular_nombres_entidades(citas_procesadas, entidades_por_chunk[i])
            
            todas_las_citas.extend(citas_procesadas)
            
            # Agregar metadatos
            if metadatos.get("tokens_prompt"):
                metadatos_agregados["tokens_prompt_total"] += metadatos["tokens_prompt"]
            if metadatos.get("tokens_respuesta"):
                metadatos_agregados["tokens_respuesta_total"] += metadatos["tokens_respuesta"]
            metadatos_agregados["duracion_total_ms"] += metadatos["duracion_llamada_ms"]
            metadatos_agregados["chunks_procesados"] += 1
            
        except Exception as e:
            logger.error(f"Error procesando chunk {i+1} para citas: {str(e)}")
            continue
    
    # Crear resultado agregado
    return {
        "id_fragmento": resultado_simplificacion.id_fragmento,
        "citas_extraidas": todas_las_citas,
        "total_citas": len(todas_las_citas),
        "metadatos_extraccion": {
            "fase": "fase_6_citas",
            "modelo_usado": "llama-3.1-8b-instant",
            "tokens_prompt": metadatos_agregados["tokens_prompt_total"],
            "tokens_respuesta": metadatos_agregados["tokens_respuesta_total"],
            "duracion_ms": metadatos_agregados["duracion_total_ms"],
            "chunks_procesados": metadatos_agregados["chunks_procesados"],
            "chunks_totales": len(chunks),
            "timestamp": datetime.now().isoformat()
        },
        "relevancia_promedio": _calcular_relevancia_promedio(todas_las_citas),
        "requiere_consolidacion": True
    }


def _contar_tipos_citas(citas: List[CitaTextual]) -> Dict[str, int]:
    """
    Cuenta las citas por tipo de entidad emisora.
    
    Args:
        citas: Lista de citas procesadas
        
    Returns:
        Diccionario con conteo por tipo de entidad
    """
    conteo = {}
    for cita in citas:
        if cita.persona_citada:
            tipo = "persona_identificada"
        else:
            tipo = "persona_no_identificada"
        conteo[tipo] = conteo.get(tipo, 0) + 1
    return conteo