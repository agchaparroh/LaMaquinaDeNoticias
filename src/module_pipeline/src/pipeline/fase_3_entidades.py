"""
Fase 3: Extracción de Entidades
===============================

Esta fase extrae todas las entidades mencionadas en el texto simplificado,
identificando personas, organizaciones, lugares, eventos, etc.
"""

from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
from datetime import datetime
import os
import json
import asyncio
from pathlib import Path

from loguru import logger

# Importar modelos
from ..models.procesamiento import EntidadProcesada
from ..models.simplificacion import ResultadoFase2Simplificacion
from ..models.metadatos import MetadatosEntidad

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


# Ruta al prompt de entidades
_PROMPT_ENTIDADES_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "Entidades.md"
_PROMPT_ENTIDADES_TEMPLATE: Optional[str] = None


def _cargar_prompt_entidades() -> str:
    """
    Carga el prompt de extracción de entidades desde el archivo.
    
    Returns:
        Contenido del prompt de entidades
        
    Raises:
        FileNotFoundError: Si no se encuentra el archivo del prompt
    """
    global _PROMPT_ENTIDADES_TEMPLATE
    
    if _PROMPT_ENTIDADES_TEMPLATE is None:
        if not _PROMPT_ENTIDADES_PATH.exists():
            raise FileNotFoundError(
                f"No se encontró el archivo de prompt en: {_PROMPT_ENTIDADES_PATH}"
            )
        
        with open(_PROMPT_ENTIDADES_PATH, "r", encoding="utf-8") as f:
            _PROMPT_ENTIDADES_TEMPLATE = f.read()
            
        logger.info(f"Prompt de entidades cargado desde: {_PROMPT_ENTIDADES_PATH}")
    
    return _PROMPT_ENTIDADES_TEMPLATE


def _preparar_prompt_entidades(
    texto_simplificado: str,
    titulo: str = "No disponible",
    fuente: str = "No disponible",
    pais: str = "No disponible",
    fecha_publicacion: str = "No disponible"
) -> str:
    """
    Prepara el prompt de extracción de entidades con el contexto.
    
    Args:
        texto_simplificado: Texto procesado en fase 2
        titulo: Título del artículo
        fuente: Fuente del artículo
        pais: País de origen
        fecha_publicacion: Fecha de publicación
        
    Returns:
        Prompt completo para el LLM
    """
    prompt = _cargar_prompt_entidades()
    
    # Reemplazar placeholders
    prompt = prompt.replace("{{TITULO}}", titulo)
    prompt = prompt.replace("{{FUENTE}}", fuente)
    prompt = prompt.replace("{{PAIS}}", pais)
    prompt = prompt.replace("{{FECHA_FUENTE}}", fecha_publicacion)
    prompt = prompt.replace("{{CONTENIDO}}", texto_simplificado)
    
    return prompt


async def _llamar_groq_entidades_async(
    client: Any,
    prompt: str,
    modelo: str = "llama-3.1-8b-instant",
    max_retries: int = 3
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Versión asíncrona de llamada a Groq para extraer entidades.
    
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
            # Llamada asíncrona simulando con asyncio sleep para rate limiting
            if attempt > 0:
                await asyncio.sleep(2 ** (attempt - 1))  # Exponential backoff
            
            response = client.chat.completions.create(
                model=modelo,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto en extracción de entidades de textos periodísticos. Extraes personas, organizaciones, lugares, eventos y otros elementos relevantes con precisión."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Baja temperatura para consistencia
                max_tokens=6000,
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
                continue
            raise GroqAPIError(f"Error al extraer entidades después de {max_retries} intentos: {str(e)}")


def _llamar_groq_entidades(
    client: Any,
    prompt: str,
    modelo: str = "llama-3.1-8b-instant",
    max_retries: int = 3
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Llama a la API de Groq para extraer entidades.
    
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
                        "content": "Eres un experto en extracción de entidades de textos periodísticos. Extraes personas, organizaciones, lugares, eventos y otros elementos relevantes con precisión."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Baja temperatura para consistencia
                max_tokens=6000,
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
            raise GroqAPIError(f"Error al extraer entidades después de {max_retries} intentos: {str(e)}")


def _procesar_entidades_extraidas(
    entidades_raw: List[Dict[str, Any]],
    id_fragmento: UUID,
    fragment_processor: FragmentProcessor
) -> List[EntidadProcesada]:
    """
    Procesa las entidades extraídas del LLM a objetos EntidadProcesada.
    
    Args:
        entidades_raw: Lista de entidades del LLM
        id_fragmento: ID del fragmento procesado
        fragment_processor: Procesador de fragmentos para IDs
        
    Returns:
        Lista de EntidadProcesada
    """
    entidades_procesadas = []
    
    for entidad in entidades_raw:
        try:
            # Crear metadatos específicos
            metadatos = MetadatosEntidad(
                tipo=entidad.get("tipo", "DESCONOCIDO"),
                alias=entidad.get("alias", []),
                fecha_nacimiento=entidad.get("fecha_nacimiento"),
                fecha_disolucion=entidad.get("fecha_disolucion"),
                descripcion_estructurada=entidad.get("descripcion", "").split(" - ") if entidad.get("descripcion") else []
            )
            
            # Crear entidad procesada
            entidad_procesada = EntidadProcesada(
                id_entidad=entidad.get("id", 0),
                texto_entidad=entidad.get("nombre", ""),
                tipo_entidad=entidad.get("tipo", "DESCONOCIDO"),
                relevancia_entidad=0.8,  # Relevancia por defecto
                id_fragmento_origen=id_fragmento,
                metadata_entidad=metadatos
            )
            
            entidades_procesadas.append(entidad_procesada)
            
        except Exception as e:
            logger.warning(f"Error procesando entidad {entidad.get('id')}: {str(e)}")
            continue
    
    return entidades_procesadas


def ejecutar_fase_3_entidades(
    resultado_simplificacion: ResultadoFase2Simplificacion,
    contexto_articulo: Optional[Dict[str, Any]] = None,
    groq_api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Ejecuta la Fase 3: Extracción de Entidades.
    
    Identifica todas las entidades mencionadas en el texto simplificado:
    personas, organizaciones, lugares, eventos, normativas y conceptos.
    
    Args:
        resultado_simplificacion: Resultado de la fase 2 con texto simplificado
        contexto_articulo: Contexto del artículo (título, fuente, etc.)
        groq_api_key: API key de Groq (opcional, usa variable de entorno)
        
    Returns:
        Diccionario con entidades extraídas y metadatos
        
    Raises:
        ProcessingError: Si hay errores en el procesamiento
    """
    logger.info(f"Iniciando Fase 3: Extracción de Entidades para fragmento {resultado_simplificacion.id_fragmento}")
    
    try:
        # Validar entrada
        if not resultado_simplificacion.texto_simplificado:
            raise ValueError("No hay texto simplificado disponible para extraer entidades")
        
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
        
        # Preparar prompt
        prompt = _preparar_prompt_entidades(
            texto_simplificado=resultado_simplificacion.texto_simplificado,
            titulo=contexto.get("titulo", "No disponible"),
            fuente=contexto.get("fuente", "No disponible"),
            pais=contexto.get("pais", "No disponible"),
            fecha_publicacion=contexto.get("fecha_publicacion", "No disponible")
        )
        
        # Determinar modelo según longitud
        modelo = "llama-3.1-8b-instant"
        if len(resultado_simplificacion.texto_simplificado) > 10000:
            modelo = "llama3-70b-8192"
            logger.info(f"Usando modelo grande para extracción de entidades")
        
        # Llamar a Groq
        respuesta, metadatos_llamada = _llamar_groq_entidades(client, prompt, modelo)
        
        # Obtener entidades del response
        entidades_raw = respuesta.get("entidades", [])
        logger.info(f"Extraídas {len(entidades_raw)} entidades")
        
        # Procesar entidades
        fragment_processor = FragmentProcessor(resultado_simplificacion.id_fragmento)
        entidades_procesadas = _procesar_entidades_extraidas(
            entidades_raw,
            resultado_simplificacion.id_fragmento,
            fragment_processor
        )
        
        # Crear resultado
        resultado = {
            "id_fragmento": resultado_simplificacion.id_fragmento,
            "entidades_extraidas": entidades_procesadas,
            "total_entidades": len(entidades_procesadas),
            "metadatos_extraccion": {
                "fase": "fase_3_entidades",
                "modelo_usado": metadatos_llamada["nombre_modelo"],
                "tokens_prompt": metadatos_llamada.get("tokens_prompt"),
                "tokens_respuesta": metadatos_llamada.get("tokens_respuesta"),
                "duracion_ms": metadatos_llamada["duracion_llamada_ms"],
                "timestamp": datetime.now().isoformat()
            },
            "tipos_entidades": _contar_tipos_entidades(entidades_procesadas)
        }
        
        logger.info(
            f"Fase 3 completada: {len(entidades_procesadas)} entidades extraídas. "
            f"Tipos: {resultado['tipos_entidades']}"
        )
        
        return resultado
        
    except Exception as e:
        logger.error(f"Error en Fase 3: {str(e)}")
        error_info = handle_generic_phase_error(
            article_id=str(resultado_simplificacion.id_fragmento),
            phase=ErrorPhase.FASE_2_EXTRACCION,  # Ahora es fase 3
            step_failed="extraccion_entidades",
            exception=e
        )
        
        # Retornar resultado vacío con error
        return {
            "id_fragmento": resultado_simplificacion.id_fragmento,
            "entidades_extraidas": [],
            "total_entidades": 0,
            "error": str(error_info),
            "metadatos_extraccion": {
                "fase": "fase_3_entidades",
                "error": True,
                "timestamp": datetime.now().isoformat()
            }
        }


def _contar_tipos_entidades(entidades: List[EntidadProcesada]) -> Dict[str, int]:
    """
    Cuenta las entidades por tipo.
    
    Args:
        entidades: Lista de entidades procesadas
        
    Returns:
        Diccionario con conteo por tipo
    """
    conteo = {}
    for entidad in entidades:
        tipo = entidad.tipo_entidad
        conteo[tipo] = conteo.get(tipo, 0) + 1
    return conteo


async def _procesar_chunk_entidades_async(
    chunk_text: str,
    chunk_index: int,
    resultado_simplificacion: ResultadoFase2Simplificacion,
    contexto_articulo: Dict[str, Any],
    client: Any,
    fragment_processor: FragmentProcessor
) -> Tuple[List[EntidadProcesada], Dict[str, Any]]:
    """
    Procesa un chunk individual para extraer entidades de forma asíncrona.
    
    Args:
        chunk_text: Texto del chunk
        chunk_index: Índice del chunk
        resultado_simplificacion: Resultado de fase 2
        contexto_articulo: Contexto del artículo
        client: Cliente de Groq
        fragment_processor: Procesador de fragmentos
        
    Returns:
        Tupla (entidades_procesadas, metadatos)
    """
    logger.debug(f"Procesando chunk {chunk_index + 1} para entidades (async)")
    
    try:
        # Preparar prompt para chunk
        prompt = _preparar_prompt_entidades(
            texto_simplificado=chunk_text,
            titulo=contexto_articulo.get("titulo", "No disponible"),
            fuente=contexto_articulo.get("fuente", "No disponible"),
            pais=contexto_articulo.get("pais", "No disponible"),
            fecha_publicacion=contexto_articulo.get("fecha_publicacion", "No disponible")
        )
        
        # Llamar a Groq de forma asíncrona
        respuesta, metadatos = await _llamar_groq_entidades_async(
            client, prompt, "llama-3.1-8b-instant"
        )
        
        # Procesar entidades del chunk
        entidades_chunk = respuesta.get("entidades", [])
        
        # Ajustar IDs para evitar colisiones entre chunks
        for entidad in entidades_chunk:
            entidad["id"] = entidad.get("id", 0) + (chunk_index * 1000)
        
        # Procesar entidades
        entidades_procesadas = _procesar_entidades_extraidas(
            entidades_chunk,
            resultado_simplificacion.id_fragmento,
            fragment_processor
        )
        
        logger.debug(f"Chunk {chunk_index + 1}: {len(entidades_procesadas)} entidades extraídas")
        
        return entidades_procesadas, metadatos
        
    except Exception as e:
        logger.error(f"Error procesando chunk {chunk_index + 1} para entidades: {str(e)}")
        return [], {"error": str(e), "duracion_llamada_ms": 0}


async def extraer_entidades_con_chunking_paralelo(
    resultado_simplificacion: ResultadoFase2Simplificacion,
    chunks: List[str],
    contexto_articulo: Optional[Dict[str, Any]] = None,
    groq_api_key: Optional[str] = None,
    max_concurrent_chunks: int = 5
) -> Dict[str, Any]:
    """
    Extrae entidades de texto dividido en chunks procesando en paralelo.
    
    Usa asyncio.gather() para procesar múltiples chunks simultáneamente,
    respetando límites de concurrencia para evitar rate limiting.
    
    Args:
        resultado_simplificacion: Resultado de la fase 2
        chunks: Lista de chunks de texto
        contexto_articulo: Contexto del artículo
        groq_api_key: API key de Groq
        max_concurrent_chunks: Máximo de chunks procesados en paralelo
        
    Returns:
        Diccionario con todas las entidades extraídas
    """
    logger.info(f"Extrayendo entidades de {len(chunks)} chunks EN PARALELO")
    inicio_total = datetime.now()
    
    # Validaciones
    api_key = groq_api_key or os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("No se encontró GROQ_API_KEY")
    
    client = Groq(api_key=api_key)
    contexto = contexto_articulo or {}
    fragment_processor = FragmentProcessor(resultado_simplificacion.id_fragmento)
    
    # Procesar chunks en lotes para respetar concurrencia
    todas_las_entidades = []
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
            task = _procesar_chunk_entidades_async(
                chunk_text=chunk_text,
                chunk_index=batch_indices[j],
                resultado_simplificacion=resultado_simplificacion,
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
                
                entidades, metadatos = resultado
                todas_las_entidades.extend(entidades)
                
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
        "entidades_extraidas": todas_las_entidades,
        "total_entidades": len(todas_las_entidades),
        "metadatos_extraccion": {
            "fase": "fase_3_entidades",
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
        "tipos_entidades": _contar_tipos_entidades(todas_las_entidades),
        "requiere_consolidacion": True
    }
    
    logger.info(
        f"Procesamiento paralelo completado: {len(todas_las_entidades)} entidades en {duracion_total}ms "
        f"({metadatos_agregados['parallel_batches']} lotes)"
    )
    
    return resultado


def extraer_entidades_con_chunking(
    resultado_simplificacion: ResultadoFase2Simplificacion,
    chunks: List[str],
    contexto_articulo: Optional[Dict[str, Any]] = None,
    groq_api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extrae entidades de texto dividido en chunks (versión secuencial - legacy).
    
    Esta función mantiene compatibilidad con el procesamiento secuencial.
    Para aprovechar el procesamiento paralelo, usar extraer_entidades_con_chunking_paralelo.
    
    Args:
        resultado_simplificacion: Resultado de la fase 2
        chunks: Lista de chunks de texto
        contexto_articulo: Contexto del artículo
        groq_api_key: API key de Groq
        
    Returns:
        Diccionario con todas las entidades extraídas
    """
    logger.info(f"Extrayendo entidades de {len(chunks)} chunks (secuencial)")
    
    todas_las_entidades = []
    metadatos_agregados = {
        "tokens_prompt_total": 0,
        "tokens_respuesta_total": 0,
        "duracion_total_ms": 0,
        "chunks_procesados": len(chunks)
    }
    
    api_key = groq_api_key or os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("No se encontró GROQ_API_KEY")
    
    client = Groq(api_key=api_key)
    contexto = contexto_articulo or {}
    fragment_processor = FragmentProcessor(resultado_simplificacion.id_fragmento)
    
    # Procesar cada chunk
    for i, chunk in enumerate(chunks):
        logger.info(f"Procesando chunk {i+1}/{len(chunks)} para entidades")
        
        try:
            # Preparar prompt para chunk
            prompt = _preparar_prompt_entidades(
                texto_simplificado=chunk,
                titulo=contexto.get("titulo", "No disponible"),
                fuente=contexto.get("fuente", "No disponible"),
                pais=contexto.get("pais", "No disponible"),
                fecha_publicacion=contexto.get("fecha_publicacion", "No disponible")
            )
            
            # Llamar a Groq
            respuesta, metadatos = _llamar_groq_entidades(
                client, prompt, "llama-3.1-8b-instant"
            )
            
            # Procesar entidades del chunk
            entidades_chunk = respuesta.get("entidades", [])
            
            # Ajustar IDs para evitar colisiones entre chunks
            for entidad in entidades_chunk:
                # Offset de IDs basado en chunk
                entidad["id"] = entidad.get("id", 0) + (i * 1000)
            
            # Procesar entidades
            entidades_procesadas = _procesar_entidades_extraidas(
                entidades_chunk,
                resultado_simplificacion.id_fragmento,
                fragment_processor
            )
            
            todas_las_entidades.extend(entidades_procesadas)
            
            # Agregar metadatos
            if metadatos.get("tokens_prompt"):
                metadatos_agregados["tokens_prompt_total"] += metadatos["tokens_prompt"]
            if metadatos.get("tokens_respuesta"):
                metadatos_agregados["tokens_respuesta_total"] += metadatos["tokens_respuesta"]
            metadatos_agregados["duracion_total_ms"] += metadatos["duracion_llamada_ms"]
            
        except Exception as e:
            logger.error(f"Error procesando chunk {i+1} para entidades: {str(e)}")
            continue
    
    # Crear resultado agregado
    return {
        "id_fragmento": resultado_simplificacion.id_fragmento,
        "entidades_extraidas": todas_las_entidades,
        "total_entidades": len(todas_las_entidades),
        "metadatos_extraccion": {
            "fase": "fase_3_entidades",
            "modelo_usado": "llama-3.1-8b-instant",
            "tokens_prompt": metadatos_agregados["tokens_prompt_total"],
            "tokens_respuesta": metadatos_agregados["tokens_respuesta_total"],
            "duracion_ms": metadatos_agregados["duracion_total_ms"],
            "chunks_procesados": metadatos_agregados["chunks_procesados"],
            "parallel_processing": False,
            "timestamp": datetime.now().isoformat()
        },
        "tipos_entidades": _contar_tipos_entidades(todas_las_entidades),
        "requiere_consolidacion": True
    }