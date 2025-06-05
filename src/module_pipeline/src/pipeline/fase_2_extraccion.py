"""
Fase 2: Extracción de Elementos Básicos
=======================================

Esta fase se encarga de:
- Extraer hechos principales del texto
- Identificar entidades mencionadas (personas, organizaciones, lugares)
- Asignar IDs temporales a elementos extraídos
- Crear estructuras HechoBase y EntidadBase

TODO: Implementar según Tarea #16 de TaskMaster
"""

from typing import Dict, Any
from loguru import logger

async def ejecutar_fase_2(resultado_fase1: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ejecuta la fase 2 del pipeline: Extracción de Elementos Básicos.
    
    Args:
        resultado_fase1: Resultado de la Fase 1 con texto limpio
        
    Returns:
        ResultadoFase2Extraccion con hechos y entidades extraídos
    """
    logger.info("Iniciando Fase 2: Extracción de Elementos Básicos")
    
    # TODO: Implementar lógica completa
    # 1. Usar Groq API con Prompt_2_elementos_basicos.md
    # 2. Extraer hechos principales
    # 3. Identificar entidades mencionadas
    # 4. Crear objetos HechoBase y EntidadBase
    # 5. Retornar ResultadoFase2Extraccion
    
    raise NotImplementedError("Pendiente de implementación - Tarea #16")
