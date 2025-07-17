"""
Fase 5: Extracción de Datos Cuantitativos
=========================================

Esta fase extrae datos cuantitativos del texto cuando se detectan
números significativos, usando el contexto de hechos y entidades ya extraídos.
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
from ..models.procesamiento import (
    DatosCuantitativos,
    HechoProcesado,
    EntidadProcesada
)
from ..models.simplificacion import ResultadoFase2Simplificacion
from ..models.metadatos import MetadatosDato

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


# Ruta al prompt de datos
_PROMPT_DATOS_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "Datos.md"
_PROMPT_DATOS_TEMPLATE: Optional[str] = None


def _cargar_prompt_datos() -> str:
    """
    Carga el prompt de extracción de datos desde el archivo.
    
    Returns:
        Contenido del prompt de datos
        
    Raises:
        FileNotFoundError: Si no se encuentra el archivo del prompt
    """
    global _PROMPT_DATOS_TEMPLATE
    
    if _PROMPT_DATOS_TEMPLATE is None:
        if not _PROMPT_DATOS_PATH.exists():
            raise FileNotFoundError(
                f"No se encontró el archivo de prompt en: {_PROMPT_DATOS_PATH}"
            )
        
        with open(_PROMPT_DATOS_PATH, "r", encoding="utf-8") as f:
            _PROMPT_DATOS_TEMPLATE = f.read()
            
        logger.info(f"Prompt de datos cargado desde: {_PROMPT_DATOS_PATH}")
    
    return _PROMPT_DATOS_TEMPLATE


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
            "tipo": hecho.metadata_hecho.tipo_hecho_llm
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


def _preparar_prompt_datos(
    texto_simplificado: str,
    hechos_json: str,
    entidades_json: str,
    titulo: str = "No disponible",
    fuente: str = "No disponible",
    fecha_publicacion: str = "No disponible"
) -> str:
    """
    Prepara el prompt de extracción de datos con el contexto.
    
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
    prompt = _cargar_prompt_datos()
    
    # Reemplazar placeholders
    prompt = prompt.replace("{{TITULO}}", titulo)
    prompt = prompt.replace("{{FUENTE}}", fuente)
    prompt = prompt.replace("{{FECHA_FUENTE}}", fecha_publicacion)
    prompt = prompt.replace("{{CONTENIDO}}", texto_simplificado)
    prompt = prompt.replace("{{Fase4_Hechos}}", hechos_json)
    prompt = prompt.replace("{{Fase3_Entidades}}", entidades_json)
    
    return prompt


async def _llamar_groq_datos_async(
    client: Any,
    prompt: str,
    modelo: str = "llama-3.1-8b-instant",
    max_retries: int = 3
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Versión asíncrona de llamada a Groq para extraer datos cuantitativos.
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
                        "content": "Eres un experto en extracción de datos cuantitativos de textos periodísticos. Identificas números, estadísticas, métricas y datos numéricos con precisión y contexto."
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
            raise GroqAPIError(f"Error al extraer datos después de {max_retries} intentos: {str(e)}")


def _llamar_groq_datos(
    client: Any,
    prompt: str,
    modelo: str = "llama-3.1-8b-instant",
    max_retries: int = 3
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Llama a la API de Groq para extraer datos cuantitativos.
    
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
                        "content": "Eres un experto en análisis de datos cuantitativos en textos periodísticos. Extraes valores numéricos, porcentajes, estadísticas y métricas con precisión, vinculándolos correctamente con los hechos y entidades relacionados."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Baja temperatura para precisión numérica
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
            raise GroqAPIError(f"Error al extraer datos después de {max_retries} intentos: {str(e)}")


def _procesar_datos_extraidos(
    datos_raw: List[Dict[str, Any]],
    id_fragmento: UUID,
    fragment_processor: FragmentProcessor
) -> List[DatosCuantitativos]:
    """
    Procesa los datos extraídos del LLM a objetos DatosCuantitativos.
    
    Args:
        datos_raw: Lista de datos del LLM
        id_fragmento: ID del fragmento procesado
        fragment_processor: Procesador de fragmentos para IDs
        
    Returns:
        Lista de DatosCuantitativos
    """
    datos_procesados = []
    
    for dato in datos_raw:
        try:
            # Extraer periodo
            periodo = dato.get("periodo", {})
            fecha_inicio = periodo.get("inicio")
            fecha_fin = periodo.get("fin")
            
            # Crear metadatos específicos
            metadatos = MetadatosDato(
                indicador_llm=dato.get("indicador", ""),
                categoria_llm=dato.get("categoria", "otro"),
                hecho_id_relacionado=dato.get("hecho_id"),
                ambito_geografico_llm=dato.get("ambito_geografico", []),
                periodo_inicio_llm=fecha_inicio,
                periodo_fin_llm=fecha_fin,
                tipo_periodo_llm=dato.get("tipo_periodo", "puntual"),
                valor_anterior_llm=dato.get("valor_anterior"),
                variacion_absoluta_llm=dato.get("variacion_absoluta"),
                variacion_porcentual_llm=dato.get("variacion_porcentual"),
                tendencia_llm=dato.get("tendencia")
            )
            
            # Crear dato cuantitativo
            dato_procesado = DatosCuantitativos(
                id_dato_cuantitativo=dato.get("id", 0),
                id_fragmento_origen=id_fragmento,
                descripcion_dato=dato.get("indicador", ""),
                valor_dato=float(dato.get("valor", 0)),
                unidad_dato=dato.get("unidad"),
                fecha_dato=f"{fecha_inicio} - {fecha_fin}" if fecha_inicio and fecha_fin else None,
                metadata_dato=metadatos
            )
            
            datos_procesados.append(dato_procesado)
            
        except Exception as e:
            logger.warning(f"Error procesando dato {dato.get('id')}: {str(e)}")
            continue
    
    return datos_procesados


def ejecutar_fase_5_datos(
    resultado_simplificacion: ResultadoFase2Simplificacion,
    hechos_extraidos: List[HechoProcesado],
    entidades_extraidas: List[EntidadProcesada],
    contexto_articulo: Optional[Dict[str, Any]] = None,
    groq_api_key: Optional[str] = None,
    ejecutar_siempre: bool = False
) -> Dict[str, Any]:
    """
    Ejecuta la Fase 5: Extracción de Datos Cuantitativos.
    
    Esta fase es condicional y solo se ejecuta si hay datos numéricos
    significativos en el texto (conteo_datos > 0).
    
    Args:
        resultado_simplificacion: Resultado de la fase 2 con texto simplificado
        hechos_extraidos: Hechos extraídos en fase 4
        entidades_extraidas: Entidades extraídas en fase 3
        contexto_articulo: Contexto del artículo (título, fuente, etc.)
        groq_api_key: API key de Groq (opcional, usa variable de entorno)
        ejecutar_siempre: Si True, ejecuta aunque no haya datos detectados
        
    Returns:
        Diccionario con datos extraídos y metadatos
        
    Raises:
        ProcessingError: Si hay errores en el procesamiento
    """
    logger.info(f"Iniciando Fase 5: Extracción de Datos para fragmento {resultado_simplificacion.id_fragmento}")
    
    # Verificar si debe ejecutarse
    conteo_datos = contexto_articulo.get("conteo_datos", 0) if contexto_articulo else 0
    if not ejecutar_siempre and conteo_datos == 0:
        logger.info("No se detectaron datos cuantitativos. Saltando fase 5.")
        return {
            "id_fragmento": resultado_simplificacion.id_fragmento,
            "datos_extraidos": [],
            "total_datos": 0,
            "fase_omitida": True,
            "razon": "No se detectaron datos cuantitativos en el análisis previo",
            "metadatos_extraccion": {
                "fase": "fase_5_datos",
                "omitida": True,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    try:
        # Validar entrada
        if not resultado_simplificacion.texto_simplificado:
            raise ValueError("No hay texto simplificado disponible para extraer datos")
        
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
        prompt = _preparar_prompt_datos(
            texto_simplificado=resultado_simplificacion.texto_simplificado,
            hechos_json=hechos_json,
            entidades_json=entidades_json,
            titulo=contexto.get("titulo", "No disponible"),
            fuente=contexto.get("fuente", "No disponible"),
            fecha_publicacion=contexto.get("fecha_publicacion", "No disponible")
        )
        
        # Llamar a Groq
        respuesta, metadatos_llamada = _llamar_groq_datos(client, prompt)
        
        # Obtener datos del response
        datos_raw = respuesta.get("datos_cuantitativos", [])
        logger.info(f"Extraídos {len(datos_raw)} datos cuantitativos")
        
        # Procesar datos
        fragment_processor = FragmentProcessor(resultado_simplificacion.id_fragmento)
        datos_procesados = _procesar_datos_extraidos(
            datos_raw,
            resultado_simplificacion.id_fragmento,
            fragment_processor
        )
        
        # Crear resultado
        resultado = {
            "id_fragmento": resultado_simplificacion.id_fragmento,
            "datos_extraidos": datos_procesados,
            "total_datos": len(datos_procesados),
            "metadatos_extraccion": {
                "fase": "fase_5_datos",
                "modelo_usado": metadatos_llamada["nombre_modelo"],
                "tokens_prompt": metadatos_llamada.get("tokens_prompt"),
                "tokens_respuesta": metadatos_llamada.get("tokens_respuesta"),
                "duracion_ms": metadatos_llamada["duracion_llamada_ms"],
                "conteo_datos_inicial": conteo_datos,
                "timestamp": datetime.now().isoformat()
            },
            "categorias_datos": _contar_categorias_datos(datos_procesados)
        }
        
        logger.info(
            f"Fase 5 completada: {len(datos_procesados)} datos extraídos. "
            f"Categorías: {resultado['categorias_datos']}"
        )
        
        return resultado
        
    except Exception as e:
        logger.error(f"Error en Fase 5: {str(e)}")
        error_info = handle_generic_phase_error(
            article_id=str(resultado_simplificacion.id_fragmento),
            phase=ErrorPhase.FASE_3_CITAS_DATOS,  # Ahora es fase 5
            step_failed="extraccion_datos",
            exception=e
        )
        
        # Retornar resultado vacío con error
        return {
            "id_fragmento": resultado_simplificacion.id_fragmento,
            "datos_extraidos": [],
            "total_datos": 0,
            "error": str(error_info),
            "metadatos_extraccion": {
                "fase": "fase_5_datos",
                "error": True,
                "timestamp": datetime.now().isoformat()
            }
        }


def _contar_categorias_datos(datos: List[DatosCuantitativos]) -> Dict[str, int]:
    """
    Cuenta los datos por categoría.
    
    Args:
        datos: Lista de datos procesados
        
    Returns:
        Diccionario con conteo por categoría
    """
    conteo = {}
    for dato in datos:
        categoria = dato.metadata_dato.categoria_llm
        conteo[categoria] = conteo.get(categoria, 0) + 1
    return conteo


async def _procesar_chunk_datos_async(
    chunk_text: str,
    chunk_index: int,
    resultado_simplificacion: ResultadoFase2Simplificacion,
    hechos_chunk: List[HechoProcesado],
    entidades_chunk: List[EntidadProcesada],
    contexto_articulo: Dict[str, Any],
    client: Any,
    fragment_processor: FragmentProcessor
) -> Tuple[List[DatosCuantitativos], Dict[str, Any]]:
    """
    Procesa un chunk individual para extraer datos cuantitativos de forma asíncrona.
    """
    logger.debug(f"Procesando chunk {chunk_index + 1} para datos cuantitativos (async)")
    
    try:
        # Preparar contexto para chunk
        hechos_json = json.dumps([{
            "id": hecho.id_hecho,
            "contenido": hecho.texto_hecho,
            "tipo": hecho.metadata_hecho.tipo_hecho_llm if hasattr(hecho, 'metadata_hecho') and hecho.metadata_hecho else "DESCONOCIDO"
        } for hecho in hechos_chunk], ensure_ascii=False, indent=2)
        
        entidades_json = json.dumps([{
            "id": entidad.id_entidad,
            "nombre": entidad.texto_entidad,
            "tipo": entidad.tipo_entidad
        } for entidad in entidades_chunk], ensure_ascii=False, indent=2)
        
        # Preparar prompt para chunk
        prompt = _preparar_prompt_datos(
            texto_simplificado=chunk_text,
            hechos_contexto=hechos_json,
            entidades_contexto=entidades_json,
            titulo=contexto_articulo.get("titulo", "No disponible"),
            fuente=contexto_articulo.get("fuente", "No disponible"),
            fecha_publicacion=contexto_articulo.get("fecha_publicacion", "No disponible")
        )
        
        # Llamar a Groq de forma asíncrona
        respuesta, metadatos = await _llamar_groq_datos_async(
            client, prompt, "llama-3.1-8b-instant"
        )
        
        # Procesar datos del chunk
        datos_chunk = respuesta.get("datos_cuantitativos", [])
        
        # Ajustar IDs para evitar colisiones entre chunks
        for dato in datos_chunk:
            dato["id"] = dato.get("id", 0) + (chunk_index * 1000)
        
        # Procesar datos
        datos_procesados = _procesar_datos_extraidos(
            datos_chunk,
            resultado_simplificacion.id_fragmento,
            fragment_processor
        )
        
        logger.debug(f"Chunk {chunk_index + 1}: {len(datos_procesados)} datos extraídos")
        
        return datos_procesados, metadatos
        
    except Exception as e:
        logger.error(f"Error procesando chunk {chunk_index + 1} para datos: {str(e)}")
        return [], {"error": str(e), "duracion_llamada_ms": 0}


async def extraer_datos_con_chunking_paralelo(
    resultado_simplificacion: ResultadoFase2Simplificacion,
    chunks: List[str],
    hechos_por_chunk: List[List[HechoProcesado]],
    entidades_por_chunk: List[List[EntidadProcesada]],
    contexto_articulo: Optional[Dict[str, Any]] = None,
    groq_api_key: Optional[str] = None,
    max_concurrent_chunks: int = 5
) -> Dict[str, Any]:
    """
    Extrae datos cuantitativos de chunks procesando en paralelo.
    """
    logger.info(f"Extrayendo datos cuantitativos de {len(chunks)} chunks EN PARALELO")
    inicio_total = datetime.now()
    
    # Validaciones
    api_key = groq_api_key or os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("No se encontró GROQ_API_KEY")
    
    client = Groq(api_key=api_key)
    contexto = contexto_articulo or {}
    fragment_processor = FragmentProcessor(resultado_simplificacion.id_fragmento)
    
    # Procesar chunks en lotes
    todos_los_datos = []
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
            
            task = _procesar_chunk_datos_async(
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
                
                datos, metadatos = resultado
                todos_los_datos.extend(datos)
                
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
        "datos_extraidos": todos_los_datos,
        "total_datos": len(todos_los_datos),
        "metadatos_extraccion": {
            "fase": "fase_5_datos",
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
        "categorias_datos": _contar_categorias_datos(todos_los_datos) if todos_los_datos else {},
        "requiere_consolidacion": True
    }
    
    logger.info(
        f"Procesamiento paralelo completado: {len(todos_los_datos)} datos en {duracion_total}ms "
        f"({metadatos_agregados['parallel_batches']} lotes)"
    )
    
    return resultado


def extraer_datos_con_chunking(
    resultado_simplificacion: ResultadoFase2Simplificacion,
    chunks: List[str],
    hechos_por_chunk: List[List[HechoProcesado]],
    entidades_por_chunk: List[List[EntidadProcesada]],
    contexto_articulo: Optional[Dict[str, Any]] = None,
    groq_api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extrae datos de texto dividido en chunks (versión secuencial - legacy).
    
    Esta función mantiene compatibilidad con el procesamiento secuencial.
    Para aprovechar el procesamiento paralelo, usar extraer_datos_con_chunking_paralelo.
    
    Procesa cada chunk con su contexto local de hechos y entidades.
    
    Args:
        resultado_simplificacion: Resultado de la fase 2
        chunks: Lista de chunks de texto
        hechos_por_chunk: Hechos extraídos por cada chunk
        entidades_por_chunk: Entidades extraídas por cada chunk
        contexto_articulo: Contexto del artículo
        groq_api_key: API key de Groq
        
    Returns:
        Diccionario con todos los datos extraídos
    """
    logger.info(f"Extrayendo datos de {len(chunks)} chunks")
    
    todos_los_datos = []
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
        # Verificar si hay hechos o entidades en este chunk
        if not hechos_por_chunk[i] and not entidades_por_chunk[i]:
            logger.info(f"Saltando chunk {i+1} - sin hechos ni entidades")
            continue
            
        logger.info(f"Procesando chunk {i+1}/{len(chunks)} para datos")
        
        try:
            # Preparar contexto local del chunk
            hechos_json, entidades_json = _preparar_contexto_referencias(
                hechos_por_chunk[i],
                entidades_por_chunk[i]
            )
            
            # Preparar prompt para chunk
            prompt = _preparar_prompt_datos(
                texto_simplificado=chunk,
                hechos_json=hechos_json,
                entidades_json=entidades_json,
                titulo=contexto.get("titulo", "No disponible"),
                fuente=contexto.get("fuente", "No disponible"),
                fecha_publicacion=contexto.get("fecha_publicacion", "No disponible")
            )
            
            # Llamar a Groq
            respuesta, metadatos = _llamar_groq_datos(
                client, prompt, "llama-3.1-8b-instant"
            )
            
            # Procesar datos del chunk
            datos_chunk = respuesta.get("datos_cuantitativos", [])
            
            # Ajustar IDs para evitar colisiones
            for dato in datos_chunk:
                dato["id"] = dato.get("id", 0) + (i * 1000)
            
            # Procesar datos
            datos_procesados = _procesar_datos_extraidos(
                datos_chunk,
                resultado_simplificacion.id_fragmento,
                fragment_processor
            )
            
            todos_los_datos.extend(datos_procesados)
            
            # Agregar metadatos
            if metadatos.get("tokens_prompt"):
                metadatos_agregados["tokens_prompt_total"] += metadatos["tokens_prompt"]
            if metadatos.get("tokens_respuesta"):
                metadatos_agregados["tokens_respuesta_total"] += metadatos["tokens_respuesta"]
            metadatos_agregados["duracion_total_ms"] += metadatos["duracion_llamada_ms"]
            metadatos_agregados["chunks_procesados"] += 1
            
        except Exception as e:
            logger.error(f"Error procesando chunk {i+1} para datos: {str(e)}")
            continue
    
    # Crear resultado agregado
    return {
        "id_fragmento": resultado_simplificacion.id_fragmento,
        "datos_extraidos": todos_los_datos,
        "total_datos": len(todos_los_datos),
        "metadatos_extraccion": {
            "fase": "fase_5_datos",
            "modelo_usado": "llama-3.1-8b-instant",
            "tokens_prompt": metadatos_agregados["tokens_prompt_total"],
            "tokens_respuesta": metadatos_agregados["tokens_respuesta_total"],
            "duracion_ms": metadatos_agregados["duracion_total_ms"],
            "chunks_procesados": metadatos_agregados["chunks_procesados"],
            "chunks_totales": len(chunks),
            "timestamp": datetime.now().isoformat()
        },
        "categorias_datos": _contar_categorias_datos(todos_los_datos),
        "requiere_consolidacion": True
    }