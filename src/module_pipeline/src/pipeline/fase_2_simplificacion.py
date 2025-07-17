"""
Fase 2: Simplificación de Texto
===============================

Esta fase transforma el lenguaje periodístico complejo en texto claro y objetivo,
optimizado para la comprensión del LLM en fases posteriores.

Transformaciones principales:
- Idiomas y metáforas → lenguaje literal
- Referencias relativas → absolutas
- Siglas → nombres completos
- Lenguaje valorativo → neutral
"""

from typing import Optional, Dict, Any, Tuple
from uuid import UUID, uuid4
from datetime import datetime, timedelta
import os
import re
from pathlib import Path

from loguru import logger

# Importar modelos
from ..models.simplificacion import (
    ResultadoFase2Simplificacion,
    MetadatosFase2Simplificacion
)
from ..models.procesamiento import ResultadoFase1Triaje

# Importar utilidades
from ..utils.error_handling import (
    handle_generic_phase_error,
    ErrorPhase,
    GroqAPIError,
    ProcessingError
)
from ..utils.json_parser import parse_llm_json_response
from ..utils.validation import escape_html

# Importar servicio Groq
try:
    from groq import Groq
except ImportError:
    Groq = None


# Ruta al prompt de simplificación
_PROMPT_SIMPLIFICACION_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "Simplificación.md"
_PROMPT_SIMPLIFICACION_TEMPLATE: Optional[str] = None


def _cargar_prompt_simplificacion() -> str:
    """
    Carga el prompt de simplificación desde el archivo.
    
    Returns:
        Contenido del prompt de simplificación
        
    Raises:
        FileNotFoundError: Si no se encuentra el archivo del prompt
    """
    global _PROMPT_SIMPLIFICACION_TEMPLATE
    
    if _PROMPT_SIMPLIFICACION_TEMPLATE is None:
        if not _PROMPT_SIMPLIFICACION_PATH.exists():
            raise FileNotFoundError(
                f"No se encontró el archivo de prompt en: {_PROMPT_SIMPLIFICACION_PATH}"
            )
        
        with open(_PROMPT_SIMPLIFICACION_PATH, "r", encoding="utf-8") as f:
            _PROMPT_SIMPLIFICACION_TEMPLATE = f.read()
            
        logger.info(f"Prompt de simplificación cargado desde: {_PROMPT_SIMPLIFICACION_PATH}")
    
    return _PROMPT_SIMPLIFICACION_TEMPLATE


def _calcular_fechas_relativas(fecha_articulo: Optional[str]) -> Dict[str, str]:
    """
    Calcula fechas absolutas a partir de referencias relativas.
    
    Args:
        fecha_articulo: Fecha del artículo en formato YYYY-MM-DD
        
    Returns:
        Diccionario con fechas calculadas
    """
    if not fecha_articulo:
        return {}
    
    try:
        fecha = datetime.strptime(fecha_articulo, "%Y-%m-%d")
        
        return {
            "{{FECHA_AYER}}": (fecha - timedelta(days=1)).strftime("%Y-%m-%d"),
            "{{FECHA_MAÑANA}}": (fecha + timedelta(days=1)).strftime("%Y-%m-%d"),
            "{{FECHA_INICIO_SEMANA_PASADA}}": (fecha - timedelta(days=fecha.weekday() + 7)).strftime("%Y-%m-%d"),
            "{{FECHA_FIN_SEMANA_PASADA}}": (fecha - timedelta(days=fecha.weekday() + 1)).strftime("%Y-%m-%d"),
        }
    except ValueError as e:
        logger.warning(f"Error al parsear fecha del artículo: {e}")
        return {}


def _preparar_prompt_simplificacion(
    texto: str,
    fecha_articulo: Optional[str] = None
) -> str:
    """
    Prepara el prompt de simplificación con el texto y contexto.
    
    Args:
        texto: Texto a simplificar
        fecha_articulo: Fecha del artículo para resolver referencias temporales
        
    Returns:
        Prompt completo para el LLM
    """
    prompt = _cargar_prompt_simplificacion()
    
    # Reemplazar el contenido original
    prompt = prompt.replace("{{CONTENIDO_ORIGINAL}}", texto)
    
    # Si hay fecha, calcular y reemplazar fechas relativas
    if fecha_articulo:
        fechas = _calcular_fechas_relativas(fecha_articulo)
        for placeholder, fecha in fechas.items():
            prompt = prompt.replace(placeholder, fecha)
    
    return prompt


def _analizar_transformaciones(
    texto_original: str,
    texto_simplificado: str
) -> Dict[str, int]:
    """
    Analiza las transformaciones realizadas en el texto.
    
    Args:
        texto_original: Texto antes de simplificar
        texto_simplificado: Texto después de simplificar
        
    Returns:
        Conteo de transformaciones por tipo
    """
    transformaciones = {
        "metaforas": 0,
        "siglas_expandidas": 0,
        "referencias_temporales": 0,
        "eufemismos": 0,
        "valoraciones_eliminadas": 0
    }
    
    # Detectar expansión de siglas (patrón: SIGLA → Nombre Completo (SIGLA))
    siglas_pattern = r'\b[A-Z]{2,}\b'
    siglas_original = set(re.findall(siglas_pattern, texto_original))
    siglas_expandidas = len([s for s in siglas_original if f"({s})" in texto_simplificado])
    transformaciones["siglas_expandidas"] = siglas_expandidas
    
    # Detectar resolución de referencias temporales
    referencias_temporales = ["ayer", "hoy", "mañana", "la semana pasada", "el mes pasado"]
    for ref in referencias_temporales:
        if ref in texto_original.lower() and ref not in texto_simplificado.lower():
            transformaciones["referencias_temporales"] += 1
    
    # Detectar eliminación de valoraciones (palabras típicamente valorativas)
    valoraciones = ["polémico", "controvertido", "exitoso", "brillante", "sorprendente", "tibia"]
    for val in valoraciones:
        if val in texto_original.lower() and val not in texto_simplificado.lower():
            transformaciones["valoraciones_eliminadas"] += 1
    
    return transformaciones


def _llamar_groq_simplificacion(
    client: Any,
    prompt: str,
    modelo: str = "llama-3.1-8b-instant",
    max_retries: int = 3
) -> Tuple[str, Dict[str, Any]]:
    """
    Llama a la API de Groq para simplificar el texto.
    
    Args:
        client: Cliente de Groq
        prompt: Prompt con el texto a simplificar
        modelo: Modelo a usar
        max_retries: Número máximo de reintentos
        
    Returns:
        Tupla (texto_simplificado, metadatos_llamada)
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
                    "content": "Eres un experto en simplificación de lenguaje periodístico. Tu tarea es transformar textos complejos en versiones claras y objetivas, manteniendo toda la información factual."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,  # Baja temperatura para consistencia
            max_tokens=8000
            )
        
            duracion_ms = int((datetime.now() - inicio).total_seconds() * 1000)
            
            texto_simplificado = response.choices[0].message.content.strip()
            
            metadatos = {
                "nombre_modelo": modelo,
                "tokens_prompt": response.usage.prompt_tokens if response.usage else None,
                "tokens_respuesta": response.usage.completion_tokens if response.usage else None,
                "duracion_llamada_ms": duracion_ms
            }
            
            return texto_simplificado, metadatos
            
        except Exception as e:
            logger.error(f"Error en llamada a Groq (intento {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            raise GroqAPIError(f"Error al simplificar texto después de {max_retries} intentos: {str(e)}")


def ejecutar_fase_2_simplificacion(
    resultado_triaje: ResultadoFase1Triaje,
    fecha_articulo: Optional[str] = None,
    groq_api_key: Optional[str] = None
) -> ResultadoFase2Simplificacion:
    """
    Ejecuta la Fase 2: Simplificación de texto periodístico.
    
    Esta fase transforma el lenguaje complejo en texto claro y objetivo,
    optimizado para el procesamiento por LLM en fases posteriores.
    
    Args:
        resultado_triaje: Resultado de la fase 1 con el texto a simplificar
        fecha_articulo: Fecha del artículo (YYYY-MM-DD) para resolver referencias
        groq_api_key: API key de Groq (opcional, usa variable de entorno)
        
    Returns:
        ResultadoFase2Simplificacion con el texto simplificado
        
    Raises:
        ProcessingError: Si hay errores en el procesamiento
    """
    logger.info(f"Iniciando Fase 2: Simplificación para fragmento {resultado_triaje.id_fragmento}")
    
    try:
        # Validar entrada
        if not resultado_triaje.texto_para_siguiente_fase:
            raise ValueError("No hay texto disponible para simplificar")
        
        # Obtener API key
        api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("No se encontró GROQ_API_KEY")
        
        # Inicializar cliente Groq
        if Groq is None:
            raise ImportError("El paquete 'groq' no está instalado")
        
        client = Groq(api_key=api_key)
        
        # Obtener texto a simplificar
        texto_original = resultado_triaje.texto_para_siguiente_fase
        
        # Preparar prompt
        prompt = _preparar_prompt_simplificacion(texto_original, fecha_articulo)
        
        # Determinar modelo según longitud del texto
        modelo = "llama-3.1-8b-instant"
        if len(texto_original) > 10000:  # Umbral para modelo grande - casos excepcionales
            modelo = "llama3-70b-8192"
            logger.info(f"Usando modelo grande debido a longitud del texto: {len(texto_original)} chars")
        
        # Llamar a Groq
        texto_simplificado, metadatos_llamada = _llamar_groq_simplificacion(
            client, prompt, modelo
        )
        
        # Analizar transformaciones
        transformaciones = _analizar_transformaciones(texto_original, texto_simplificado)
        
        # Calcular reducción de complejidad (aproximación basada en longitud)
        reduccion = ((len(texto_original) - len(texto_simplificado)) / len(texto_original)) * 100
        reduccion = max(0, min(100, reduccion))  # Clamp entre 0 y 100
        
        # Crear metadatos
        metadatos = MetadatosFase2Simplificacion(
            nombre_modelo_simplificacion=metadatos_llamada["nombre_modelo"],
            tokens_prompt_simplificacion=metadatos_llamada.get("tokens_prompt"),
            tokens_respuesta_simplificacion=metadatos_llamada.get("tokens_respuesta"),
            duracion_llamada_ms_simplificacion=metadatos_llamada["duracion_llamada_ms"],
            fecha_articulo_original=fecha_articulo,
            longitud_texto_original=len(texto_original),
            longitud_texto_simplificado=len(texto_simplificado),
            transformaciones_realizadas=transformaciones,
            reduccion_complejidad_porcentaje=reduccion
        )
        
        # Verificar si requiere revisión manual
        requiere_revision = False
        razon_revision = None
        
        # Criterios para revisión manual
        if len(texto_simplificado) < len(texto_original) * 0.5:
            requiere_revision = True
            razon_revision = "Reducción excesiva del texto (>50%)"
        elif transformaciones["valoraciones_eliminadas"] > 10:
            requiere_revision = True
            razon_revision = "Alto número de valoraciones eliminadas"
        
        # Crear resultado
        resultado = ResultadoFase2Simplificacion(
            id_resultado_simplificacion=uuid4(),
            id_fragmento=resultado_triaje.id_fragmento,
            texto_simplificado=texto_simplificado,
            simplificacion_exitosa=True,
            metadatos_simplificacion=metadatos,
            prompt_simplificacion_usado=prompt[:500] + "...",  # Primeros 500 chars
            requiere_revision_manual=requiere_revision,
            razon_revision=razon_revision
        )
        
        logger.info(
            f"Fase 2 completada: {len(texto_original)} → {len(texto_simplificado)} chars "
            f"({reduccion:.1f}% reducción), {sum(transformaciones.values())} transformaciones"
        )
        logger.info(f"DEBUG TRUNCATION: tokens_prompt={metadatos_llamada.get('tokens_prompt')}, "
                   f"tokens_respuesta={metadatos_llamada.get('tokens_respuesta')}, "
                   f"texto_simplificado_length={len(texto_simplificado)}")
        
        return resultado
        
    except Exception as e:
        logger.error(f"Error en Fase 2: {str(e)}")
        error_info = handle_generic_phase_error(
            article_id=str(resultado_triaje.id_fragmento),
            phase=ErrorPhase.SIMPLIFICACION,
            step_failed="proceso_simplificacion",
            exception=e
        )
        
        # Retornar resultado fallido
        return ResultadoFase2Simplificacion(
            id_resultado_simplificacion=uuid4(),
            id_fragmento=resultado_triaje.id_fragmento,
            texto_simplificado=resultado_triaje.texto_para_siguiente_fase or "",  # Fallback al original
            simplificacion_exitosa=False,
            metadatos_simplificacion=MetadatosFase2Simplificacion(
                advertencias_simplificacion=[str(error_info)]
            ),
            requiere_revision_manual=True,
            razon_revision=f"Error en simplificación: {str(e)}"
        )


def simplificar_con_chunking(
    resultado_triaje: ResultadoFase1Triaje,
    chunks: list[str],
    fecha_articulo: Optional[str] = None,
    groq_api_key: Optional[str] = None
) -> ResultadoFase2Simplificacion:
    """
    Simplifica texto que ha sido dividido en chunks.
    
    Procesa cada chunk por separado y luego los une manteniendo
    la coherencia del texto completo.
    
    Args:
        resultado_triaje: Resultado de la fase 1
        chunks: Lista de chunks de texto
        fecha_articulo: Fecha del artículo
        groq_api_key: API key de Groq
        
    Returns:
        ResultadoFase2Simplificacion con el texto completo simplificado
    """
    logger.info(f"Simplificando {len(chunks)} chunks para fragmento {resultado_triaje.id_fragmento}")
    
    # Simplificar cada chunk
    chunks_simplificados = []
    metadatos_agregados = {
        "tokens_prompt_total": 0,
        "tokens_respuesta_total": 0,
        "duracion_total_ms": 0,
        "transformaciones_totales": {}
    }
    
    api_key = groq_api_key or os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("No se encontró GROQ_API_KEY")
    
    client = Groq(api_key=api_key)
    
    for i, chunk in enumerate(chunks):
        logger.info(f"Simplificando chunk {i+1}/{len(chunks)}")
        
        try:
            # Preparar prompt para chunk
            prompt = _preparar_prompt_simplificacion(chunk, fecha_articulo)
            
            # Llamar a Groq
            texto_simplificado, metadatos = _llamar_groq_simplificacion(
                client, prompt, "llama-3.1-8b-instant"
            )
            
            chunks_simplificados.append(texto_simplificado)
            
            # Agregar metadatos
            if metadatos.get("tokens_prompt"):
                metadatos_agregados["tokens_prompt_total"] += metadatos["tokens_prompt"]
            if metadatos.get("tokens_respuesta"):
                metadatos_agregados["tokens_respuesta_total"] += metadatos["tokens_respuesta"]
            metadatos_agregados["duracion_total_ms"] += metadatos["duracion_llamada_ms"]
            
        except Exception as e:
            logger.error(f"Error simplificando chunk {i+1}: {str(e)}")
            # En caso de error, usar el chunk original
            chunks_simplificados.append(chunk)
    
    # Unir chunks simplificados
    texto_simplificado_completo = "\n\n".join(chunks_simplificados)
    
    # Calcular transformaciones totales
    texto_original_completo = resultado_triaje.texto_para_siguiente_fase or ""
    transformaciones_totales = _analizar_transformaciones(
        texto_original_completo,
        texto_simplificado_completo
    )
    
    # Crear metadatos
    metadatos = MetadatosFase2Simplificacion(
        nombre_modelo_simplificacion="llama-3.1-8b-instant",
        tokens_prompt_simplificacion=metadatos_agregados["tokens_prompt_total"],
        tokens_respuesta_simplificacion=metadatos_agregados["tokens_respuesta_total"],
        duracion_llamada_ms_simplificacion=metadatos_agregados["duracion_total_ms"],
        fecha_articulo_original=fecha_articulo,
        longitud_texto_original=len(texto_original_completo),
        longitud_texto_simplificado=len(texto_simplificado_completo),
        transformaciones_realizadas=transformaciones_totales,
        advertencias_simplificacion=[f"Procesado en {len(chunks)} chunks"]
    )
    
    # Crear resultado
    return ResultadoFase2Simplificacion(
        id_resultado_simplificacion=uuid4(),
        id_fragmento=resultado_triaje.id_fragmento,
        texto_simplificado=texto_simplificado_completo,
        simplificacion_exitosa=True,
        metadatos_simplificacion=metadatos,
        requiere_revision_manual=False
    )