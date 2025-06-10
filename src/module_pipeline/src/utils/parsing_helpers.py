"""
Funciones helper para parsear respuestas LLM preservando información estructurada.
Reemplazan la lógica de colapso en metadata_* genérico.

SOLUCIÓN AL PROBLEMA: Preservación de Información Estructurada
==============================================================
ANTES: Información específica se perdía al mapear todo a Dict[str, Any]
DESPUÉS: Cada campo específico se mapea a su modelo Pydantic correspondiente
"""
import json
import logging
from typing import Dict, List, Any
from ..models.metadatos import MetadatosHecho, MetadatosEntidad, MetadatosCita, MetadatosDato, PeriodoReferencia
from ..utils.validation import escape_html  # ✅ Importar función de sanitización

logger = logging.getLogger(__name__)

def parsear_metadatos_hecho_desde_json(hecho_data: Dict[str, Any]) -> MetadatosHecho:
    """
    Parsea metadatos específicos de hecho desde JSON del LLM.
    Preserva información que antes se perdía.
    
    Campos preservados:
    - precision_temporal, tipo_hecho, pais, region, ciudad
    - es_futuro, estado_programacion
    """
    try:
        # ✅ SANITIZAR campos de texto
        tipo_hecho = hecho_data.get("tipo_hecho")
        if tipo_hecho and isinstance(tipo_hecho, str):
            tipo_hecho = escape_html(tipo_hecho)
        
        # ✅ SANITIZAR listas de strings
        pais = hecho_data.get("pais", [])
        if isinstance(pais, list):
            pais = [escape_html(p) if isinstance(p, str) else p for p in pais]
        
        region = hecho_data.get("region", [])
        if isinstance(region, list):
            region = [escape_html(r) if isinstance(r, str) else r for r in region]
        
        ciudad = hecho_data.get("ciudad", [])
        if isinstance(ciudad, list):
            ciudad = [escape_html(c) if isinstance(c, str) else c for c in ciudad]
        
        return MetadatosHecho(
            precision_temporal=hecho_data.get("precision_temporal"),
            tipo_hecho=tipo_hecho,
            pais=pais,
            region=region,
            ciudad=ciudad,
            es_futuro=hecho_data.get("es_futuro"),
            estado_programacion=hecho_data.get("estado_programacion")
        )
    except Exception as e:
        logger.warning(f"Error parseando metadatos de hecho: {e}")
        logger.debug(f"Datos problemáticos: {hecho_data}")
        return MetadatosHecho()  # Devolver objeto vacío en caso de error

def parsear_metadatos_entidad_desde_json(entidad_data: Dict[str, Any]) -> MetadatosEntidad:
    """
    Parsea metadatos específicos de entidad desde JSON del LLM.
    Preserva información que antes se perdía.
    
    Campos preservados:
    - tipo, alias, fecha_nacimiento, fecha_disolucion, descripcion
    """
    try:
        # Procesar descripción con guiones si existe
        descripcion_estructurada = []
        if entidad_data.get("descripcion"):
            desc = entidad_data["descripcion"]
            if isinstance(desc, str) and desc.strip():
                if desc.startswith("-"):
                    # Separar por guiones y limpiar
                    descripcion_estructurada = [
                        line.strip()[1:].strip() 
                        for line in desc.split("-") 
                        if line.strip() and len(line.strip()) > 1
                    ]
                else:
                    # Si no tiene guiones, usar como un solo elemento
                    descripcion_estructurada = [desc.strip()]
        
        return MetadatosEntidad(
            tipo=entidad_data.get("tipo"),
            alias=entidad_data.get("alias", []),
            fecha_nacimiento=entidad_data.get("fecha_nacimiento"),
            fecha_disolucion=entidad_data.get("fecha_disolucion"),
            descripcion_estructurada=descripcion_estructurada
        )
    except Exception as e:
        logger.warning(f"Error parseando metadatos de entidad: {e}")
        logger.debug(f"Datos problemáticos: {entidad_data}")
        return MetadatosEntidad()

def parsear_metadatos_cita_desde_json(cita_data: Dict[str, Any]) -> MetadatosCita:
    """
    Parsea metadatos específicos de cita desde JSON del LLM.
    Preserva información que antes se perdía.
    
    Campos preservados:
    - fecha, contexto, relevancia (con validación 1-5)
    """
    try:
        # ✅ SANITIZAR contexto si existe
        contexto = cita_data.get("contexto")
        if contexto and isinstance(contexto, str):
            contexto = escape_html(contexto)
        
        # ✅ VALIDAR relevancia está en rango 1-5
        relevancia = cita_data.get("relevancia")
        if relevancia is not None:
            try:
                relevancia = int(relevancia)
                if not 1 <= relevancia <= 5:
                    logger.warning(f"Relevancia fuera de rango [1-5]: {relevancia}")
                    relevancia = None
            except (ValueError, TypeError):
                logger.warning(f"Relevancia no es un entero válido: {relevancia}")
                relevancia = None
        
        return MetadatosCita(
            fecha=cita_data.get("fecha"),
            contexto=contexto,
            relevancia=relevancia
        )
    except Exception as e:
        logger.warning(f"Error parseando metadatos de cita: {e}")
        logger.debug(f"Datos problemáticos: {cita_data}")
        return MetadatosCita()

def parsear_metadatos_dato_desde_json(dato_data: Dict[str, Any]) -> MetadatosDato:
    """
    Parsea metadatos específicos de dato cuantitativo desde JSON del LLM.
    Preserva información que antes se perdía.
    
    Campos preservados:
    - categoria, tipo_periodo, tendencia, valor_anterior, variaciones
    - ambito_geografico, periodo (objeto anidado)
    """
    try:
        # ✅ SANITIZAR campos de texto
        categoria = dato_data.get("categoria")
        if categoria and isinstance(categoria, str):
            categoria = escape_html(categoria)
        
        tipo_periodo = dato_data.get("tipo_periodo")
        if tipo_periodo and isinstance(tipo_periodo, str):
            tipo_periodo = escape_html(tipo_periodo)
        
        tendencia = dato_data.get("tendencia")
        if tendencia and isinstance(tendencia, str):
            tendencia = escape_html(tendencia)
        
        # ✅ SANITIZAR lista de ámbitos geográficos
        ambito_geografico = dato_data.get("ambito_geografico", [])
        if isinstance(ambito_geografico, list):
            ambito_geografico = [
                escape_html(a) if isinstance(a, str) else a 
                for a in ambito_geografico
            ]
        
        # Procesar periodo si existe
        periodo = None
        if dato_data.get("periodo"):
            periodo_data = dato_data["periodo"]
            if isinstance(periodo_data, dict):
                periodo = PeriodoReferencia(
                    inicio=periodo_data.get("inicio"),
                    fin=periodo_data.get("fin")
                )
        
        return MetadatosDato(
            categoria=categoria,
            tipo_periodo=tipo_periodo,
            tendencia=tendencia,
            valor_anterior=dato_data.get("valor_anterior"),
            variacion_absoluta=dato_data.get("variacion_absoluta"),
            variacion_porcentual=dato_data.get("variacion_porcentual"),
            ambito_geografico=ambito_geografico,
            periodo=periodo
        )
    except Exception as e:
        logger.warning(f"Error parseando metadatos de dato: {e}")
        logger.debug(f"Datos problemáticos: {dato_data}")
        return MetadatosDato()

# Funciones de ejemplo para uso en fases del pipeline
def ejemplo_parseo_fase2(respuesta_llm: str, fragmento_id) -> Dict[str, Any]:
    """
    EJEMPLO: Cómo usar las funciones de parsing en Fase 2.
    Esta función muestra el patrón correcto para preservar información.
    """
    try:
        data = json.loads(respuesta_llm)
        
        # Parsear hechos con metadatos específicos
        hechos_parseados = []
        for hecho_data in data.get("hechos", []):
            # ✅ PRESERVAR INFORMACIÓN: Usar modelo específico
            metadatos = parsear_metadatos_hecho_desde_json(hecho_data)
            
            # Crear objeto HechoProcesado con metadatos preservados
            # (Este código se usaría en la implementación real de Fase 2)
            hecho_info = {
                "id_fragmento_origen": fragmento_id,
                "texto_original_del_hecho": hecho_data["contenido"],
                "confianza_extraccion": 0.8,  # Valor por defecto
                "metadata_hecho": metadatos  # ✅ Metadatos específicos
            }
            hechos_parseados.append(hecho_info)
        
        # Parsear entidades con metadatos específicos
        entidades_parseadas = []
        for entidad_data in data.get("entidades", []):
            # ✅ PRESERVAR INFORMACIÓN: Usar modelo específico
            metadatos = parsear_metadatos_entidad_desde_json(entidad_data)
            
            entidad_info = {
                "id_fragmento_origen": fragmento_id,
                "texto_entidad": entidad_data["nombre"],
                "tipo_entidad": entidad_data.get("tipo", "DESCONOCIDO"),
                "relevancia_entidad": 0.7,  # Valor por defecto
                "metadata_entidad": metadatos  # ✅ Metadatos específicos
            }
            entidades_parseadas.append(entidad_info)
            
        return {
            "hechos": hechos_parseados,
            "entidades": entidades_parseadas
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON de Fase 2: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado en parsing Fase 2: {e}")
        raise

def ejemplo_parseo_fase3(respuesta_llm: str, fragmento_id) -> Dict[str, Any]:
    """
    EJEMPLO: Cómo usar las funciones de parsing en Fase 3.
    Esta función muestra el patrón correcto para preservar información.
    """
    try:
        data = json.loads(respuesta_llm)
        
        # Parsear citas con metadatos específicos
        citas_parseadas = []
        for cita_data in data.get("citas_textuales", []):
            # ✅ PRESERVAR INFORMACIÓN: Usar modelo específico
            metadatos = parsear_metadatos_cita_desde_json(cita_data)
            
            cita_info = {
                "id_fragmento_origen": fragmento_id,
                "texto_cita": cita_data["cita"],
                "id_entidad_citada": cita_data.get("entidad_id"),  # Mapear a UUID si existe
                "metadata_cita": metadatos  # ✅ Metadatos específicos
            }
            citas_parseadas.append(cita_info)
        
        # Parsear datos cuantitativos con metadatos específicos
        datos_parseados = []
        for dato_data in data.get("datos_cuantitativos", []):
            # ✅ PRESERVAR INFORMACIÓN: Usar modelo específico
            metadatos = parsear_metadatos_dato_desde_json(dato_data)
            
            dato_info = {
                "id_fragmento_origen": fragmento_id,
                "descripcion_dato": dato_data["indicador"],
                "valor_dato": dato_data["valor"],
                "unidad_dato": dato_data.get("unidad"),
                "metadata_dato": metadatos  # ✅ Metadatos específicos
            }
            datos_parseados.append(dato_info)
            
        return {
            "citas": citas_parseadas,
            "datos": datos_parseados
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON de Fase 3: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado en parsing Fase 3: {e}")
        raise
