"""
Validador de Relaciones Post-Fase 7B
====================================

Valida y corrige los tipos de relación generados por el LLM para asegurar
que cumplan con los constraints de la base de datos antes de la persistencia.

Este validador es crítico para resolver el problema de "entidad_relacion_tipo_relacion_check"
que impide la persistencia de artículos procesados.
"""

from typing import Dict, Any, List, Optional, Set
from enum import Enum
import logging

from .logging_config import get_logger

# Configurar logger para este módulo
logger = get_logger("ValidadorRelacionesPost7B")


class TipoRelacionEntidadEntidad(str, Enum):
    """Tipos válidos de relación entre entidades según constraint BD."""
    MIEMBRO_DE = "miembro_de"
    SUBSIDIARIA_DE = "subsidiaria_de"
    ALIADO_CON = "aliado_con"
    OPOSITOR_A = "opositor_a"
    SUCESOR_DE = "sucesor_de"
    PREDECESOR_DE = "predecesor_de"
    CASADO_CON = "casado_con"
    FAMILIAR_DE = "familiar_de"
    EMPLEADO_DE = "empleado_de"


class TipoRelacionHechoEntidad(str, Enum):
    """Tipos válidos de relación entre hechos y entidades según constraint BD."""
    PROTAGONISTA = "protagonista"
    MENCIONADO = "mencionado"
    AFECTADO = "afectado"
    DECLARANTE = "declarante"
    UBICACION = "ubicacion"
    CONTEXTO = "contexto"
    VICTIMA = "victima"
    AGRESOR = "agresor"
    ORGANIZADOR = "organizador"
    PARTICIPANTE = "participante"
    OTRO = "otro"


class TipoRelacionHechoHecho(str, Enum):
    """Tipos válidos de relación entre hechos según constraint BD."""
    CAUSA = "causa"
    CONSECUENCIA = "consecuencia"
    CONTEXTO_HISTORICO = "contexto_historico"
    RESPUESTA_A = "respuesta_a"
    ACLARACION_DE = "aclaracion_de"
    VERSION_ALTERNATIVA = "version_alternativa"
    SEGUIMIENTO_DE = "seguimiento_de"


class TipoContradiccion(str, Enum):
    """Tipos válidos de contradicción según constraint BD."""
    FECHA = "fecha"
    CONTENIDO = "contenido"
    ENTIDADES = "entidades"
    UBICACION = "ubicacion"
    VALOR = "valor"
    COMPLETA = "completa"


class ValidadorRelacionesPost7B:
    """
    Valida y corrige las relaciones extraídas por el LLM en fase 7B.
    
    El problema principal es que el LLM confunde los tipos de relación,
    usando tipos de hecho-entidad para relaciones entidad-entidad.
    """
    
    
    def _validar_relaciones_entidad_entidad(self, relaciones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Valida y corrige las relaciones entidad-entidad.
        
        Este es el método más crítico porque aquí es donde ocurre el error principal:
        el LLM usa tipos como 'ubicacion', 'mencionado', etc. que son para hecho-entidad.
        
        Validaciones aplicadas:
        1. Tipo de relación válido
        2. fuerza_relacion entre 1-10
        3. entidad_origen_id != entidad_destino_id
        4. Campos obligatorios no NULL
        """
        relaciones_validas = []
        
        for relacion in relaciones:
            # Validar campos obligatorios
            if not relacion.get("id_entidad_origen") or not relacion.get("id_entidad_destino"):
                logger.error("Relación entidad-entidad sin IDs origen/destino. Descartando.")
                self.stats["entidad_relacion_descartadas"] += 1
                continue
            
            # Validar que no sea la misma entidad (check_different_related_entities)
            if relacion.get("id_entidad_origen") == relacion.get("id_entidad_destino"):
                logger.error(
                    f"Relación entidad-entidad con mismo origen y destino: {relacion.get('id_entidad_origen')}. "
                    f"Descartando relación."
                )
                self.stats["entidad_relacion_descartadas"] += 1
                continue
            
            # Validar y corregir tipo_relacion
            tipo_original = relacion.get("tipo_relacion", "").lower()
            
            if tipo_original in self.tipos_entidad_entidad:
                # El tipo ya es válido
                pass
            elif tipo_original in self.mapeo_correcciones_entidad:
                # Intentar corregir el tipo
                tipo_corregido = self.mapeo_correcciones_entidad[tipo_original]
                logger.warning(
                    f"Corrigiendo tipo de relación entidad-entidad: '{tipo_original}' → '{tipo_corregido}' "
                    f"(entidades: {relacion.get('id_entidad_origen')} - {relacion.get('id_entidad_destino')})"
                )
                relacion["tipo_relacion"] = tipo_corregido
                self.stats["entidad_relacion_corregidas"] += 1
            else:
                # Si no podemos corregir, descartar
                logger.error(
                    f"Tipo de relación entidad-entidad inválido y no corregible: '{tipo_original}' "
                    f"(entidades: {relacion.get('id_entidad_origen')} - {relacion.get('id_entidad_destino')}). "
                    f"Descartando relación."
                )
                self.stats["entidad_relacion_descartadas"] += 1
                continue
            
            # Validar y corregir fuerza_relacion (debe ser 1-10)
            fuerza = relacion.get("fuerza_relacion", 5)
            if fuerza is None:
                fuerza = 5  # Valor por defecto
            try:
                fuerza = int(fuerza)
                if fuerza < 1:
                    logger.warning(f"fuerza_relacion < 1 ({fuerza}), ajustando a 1")
                    fuerza = 1
                    self.stats["entidad_relacion_corregidas"] += 1
                elif fuerza > 10:
                    logger.warning(f"fuerza_relacion > 10 ({fuerza}), ajustando a 10")
                    fuerza = 10
                    self.stats["entidad_relacion_corregidas"] += 1
            except (ValueError, TypeError):
                logger.warning(f"fuerza_relacion inválida ({fuerza}), usando 5 por defecto")
                fuerza = 5
                self.stats["entidad_relacion_corregidas"] += 1
            
            relacion["fuerza_relacion"] = fuerza
            relaciones_validas.append(relacion)
        
        return relaciones_validas
    
    def _validar_relaciones_hecho_entidad(self, relaciones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Valida las relaciones hecho-entidad.
        
        Validaciones:
        1. Tipo de relación válido
        2. relevancia_en_hecho entre 1-10
        3. Campos obligatorios
        """
        relaciones_validas = []
        
        for relacion in relaciones:
            # Validar campos obligatorios
            if not relacion.get("id_temporal"):
                logger.error("Relación hecho-entidad sin id_temporal. Descartando.")
                self.stats["hecho_entidad_corregidas"] += 1
                continue
            
            # Validar tipo_relacion
            tipo_original = relacion.get("tipo_relacion", "otro").lower()
            
            if tipo_original not in self.tipos_hecho_entidad:
                logger.warning(
                    f"Tipo de relación hecho-entidad inválido: '{tipo_original}'. Usando 'otro'."
                )
                relacion["tipo_relacion"] = "otro"
                self.stats["hecho_entidad_corregidas"] += 1
            
            # Validar relevancia_en_hecho (debe ser 1-10)
            relevancia = relacion.get("relevancia_en_hecho", 5)
            if relevancia is None:
                relevancia = 5
            try:
                relevancia = int(relevancia)
                if relevancia < 1:
                    logger.warning(f"relevancia_en_hecho < 1 ({relevancia}), ajustando a 1")
                    relevancia = 1
                    self.stats["hecho_entidad_corregidas"] += 1
                elif relevancia > 10:
                    logger.warning(f"relevancia_en_hecho > 10 ({relevancia}), ajustando a 10")
                    relevancia = 10
                    self.stats["hecho_entidad_corregidas"] += 1
            except (ValueError, TypeError):
                logger.warning(f"relevancia_en_hecho inválida ({relevancia}), usando 5 por defecto")
                relevancia = 5
                self.stats["hecho_entidad_corregidas"] += 1
            
            relacion["relevancia_en_hecho"] = relevancia
            relaciones_validas.append(relacion)
        
        return relaciones_validas
    
    def _validar_relaciones_hecho_hecho(self, relaciones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Valida las relaciones hecho-hecho.
        
        Validaciones:
        1. Tipo de relación válido
        2. fuerza_relacion entre 1-10
        3. hechos diferentes (o al menos fechas diferentes)
        4. Campos obligatorios
        """
        relaciones_validas = []
        
        for relacion in relaciones:
            # Validar campos obligatorios
            if not relacion.get("hecho_origen_id") or not relacion.get("hecho_destino_id"):
                logger.error("Relación hecho-hecho sin IDs origen/destino. Descartando.")
                self.stats["hecho_relacionado_descartadas"] += 1
                continue
            
            # Nota: La validación de check_different_related_hechos permite mismo ID si las fechas son diferentes
            # Por ahora solo validamos que no sean exactamente iguales ambos
            if (relacion.get("hecho_origen_id") == relacion.get("hecho_destino_id") and
                relacion.get("fecha_ocurrencia_origen") == relacion.get("fecha_ocurrencia_destino")):
                logger.error(
                    f"Relación hecho-hecho con mismo hecho y fecha: {relacion.get('hecho_origen_id')}. "
                    f"Descartando relación."
                )
                self.stats["hecho_relacionado_descartadas"] += 1
                continue
            
            # Validar tipo_relacion
            tipo_original = relacion.get("tipo_relacion", "").lower()
            
            if tipo_original not in self.tipos_hecho_hecho:
                logger.error(
                    f"Tipo de relación hecho-hecho inválido: '{tipo_original}' "
                    f"(hechos: {relacion.get('hecho_origen_id')} - {relacion.get('hecho_destino_id')}). "
                    f"Descartando relación."
                )
                self.stats["hecho_relacionado_descartadas"] += 1
                continue
            
            # Validar fuerza_relacion (debe ser 1-10)
            fuerza = relacion.get("fuerza_relacion", 5)
            if fuerza is None:
                fuerza = 5
            try:
                fuerza = int(fuerza)
                if fuerza < 1:
                    logger.warning(f"fuerza_relacion < 1 ({fuerza}), ajustando a 1")
                    fuerza = 1
                elif fuerza > 10:
                    logger.warning(f"fuerza_relacion > 10 ({fuerza}), ajustando a 10")
                    fuerza = 10
            except (ValueError, TypeError):
                logger.warning(f"fuerza_relacion inválida ({fuerza}), usando 5 por defecto")
                fuerza = 5
            
            relacion["fuerza_relacion"] = fuerza
            relaciones_validas.append(relacion)
        
        return relaciones_validas
    
    def _validar_contradicciones(self, contradicciones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Valida las contradicciones.
        
        Validaciones:
        1. Tipo de contradicción válido
        2. grado_contradiccion entre 1-5
        3. hechos diferentes (similar a relaciones hecho-hecho)
        4. Campos obligatorios
        """
        contradicciones_validas = []
        
        for contradiccion in contradicciones:
            # Validar campos obligatorios
            if not contradiccion.get("hecho_principal_id") or not contradiccion.get("hecho_contradictorio_id"):
                logger.error("Contradicción sin IDs principal/contradictorio. Descartando.")
                self.stats["contradicciones_corregidas"] += 1
                continue
            
            # Validar que no sea el mismo hecho (similar a check_different_hechos)
            if (contradiccion.get("hecho_principal_id") == contradiccion.get("hecho_contradictorio_id") and
                contradiccion.get("fecha_ocurrencia_principal") == contradiccion.get("fecha_ocurrencia_contradictoria")):
                logger.error(
                    f"Contradicción con mismo hecho y fecha: {contradiccion.get('hecho_principal_id')}. "
                    f"Descartando."
                )
                self.stats["contradicciones_corregidas"] += 1
                continue
            
            # Validar tipo_contradiccion
            tipo_original = contradiccion.get("tipo_contradiccion", "contenido").lower()
            
            if tipo_original not in self.tipos_contradiccion:
                logger.warning(
                    f"Tipo de contradicción inválido: '{tipo_original}'. Usando 'contenido'."
                )
                contradiccion["tipo_contradiccion"] = "contenido"
                self.stats["contradicciones_corregidas"] += 1
            
            # Validar grado_contradiccion (debe ser 1-5)
            grado = contradiccion.get("grado_contradiccion", 3)
            if grado is None:
                grado = 3
            try:
                grado = int(grado)
                if grado < 1:
                    logger.warning(f"grado_contradiccion < 1 ({grado}), ajustando a 1")
                    grado = 1
                    self.stats["contradicciones_corregidas"] += 1
                elif grado > 5:
                    logger.warning(f"grado_contradiccion > 5 ({grado}), ajustando a 5")
                    grado = 5
                    self.stats["contradicciones_corregidas"] += 1
            except (ValueError, TypeError):
                logger.warning(f"grado_contradiccion inválido ({grado}), usando 3 por defecto")
                grado = 3
                self.stats["contradicciones_corregidas"] += 1
            
            contradiccion["grado_contradiccion"] = grado
            contradicciones_validas.append(contradiccion)
        
        return contradicciones_validas
    
    def __init__(self):
        """Inicializa el validador con los conjuntos de valores válidos."""
        # Convertir enums a sets para búsqueda rápida
        self.tipos_entidad_entidad = {e.value for e in TipoRelacionEntidadEntidad}
        self.tipos_hecho_entidad = {e.value for e in TipoRelacionHechoEntidad}
        self.tipos_hecho_hecho = {e.value for e in TipoRelacionHechoHecho}
        self.tipos_contradiccion = {e.value for e in TipoContradiccion}
        
        # Contadores para estadísticas
        self.stats = {
            "entidad_relacion_corregidas": 0,
            "entidad_relacion_descartadas": 0,
            "hecho_entidad_corregidas": 0,
            "hecho_relacionado_descartadas": 0,
            "contradicciones_corregidas": 0
        }
        
        # Mapeo de tipos incorrectos comunes a tipos válidos
        self.mapeo_correcciones_entidad = {
            # Tipos de hecho-entidad que el LLM usa incorrectamente
            "ubicacion": "aliado_con",  # Si es una relación geográfica
            "mencionado": "aliado_con",  # Relación neutral
            "organizador": "empleado_de",  # Si organiza, probablemente trabaja para
            "participante": "miembro_de",  # Si participa, es miembro
            "protagonista": "miembro_de",  # Actor principal, probablemente miembro
            "afectado": "opositor_a",  # Si está afectado, puede ser opositor
            "declarante": "empleado_de",  # Si declara por una org, trabaja para ella
            "contexto": "aliado_con",  # Relación contextual neutral
            "victima": "opositor_a",  # Si es víctima, probablemente opositor
            "agresor": "opositor_a",  # Si es agresor, es opositor
        }
    
    def validar_y_corregir(self, datos_fase_7b: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida y corrige todos los tipos de relación en los datos de fase 7B.
        
        Args:
            datos_fase_7b: Diccionario con los datos extraídos en fase 7B
            
        Returns:
            Diccionario con los datos corregidos
        """
        # Resetear estadísticas
        self.stats = {
            "entidad_relacion_corregidas": 0,
            "entidad_relacion_descartadas": 0,
            "hecho_entidad_corregidas": 0,
            "hecho_relacionado_descartadas": 0,
            "contradicciones_corregidas": 0
        }
        
        datos_corregidos = datos_fase_7b.copy()
        
        # Validar relaciones entidad-entidad
        if "entidad_relacion" in datos_corregidos:
            datos_corregidos["entidad_relacion"] = self._validar_relaciones_entidad_entidad(
                datos_corregidos["entidad_relacion"]
            )
        
        # Validar relaciones hecho-entidad (generalmente vienen de fases anteriores, pero verificar)
        if "hecho_entidad" in datos_corregidos:
            datos_corregidos["hecho_entidad"] = self._validar_relaciones_hecho_entidad(
                datos_corregidos["hecho_entidad"]
            )
        
        # Validar relaciones hecho-hecho
        if "hecho_relacionado" in datos_corregidos:
            datos_corregidos["hecho_relacionado"] = self._validar_relaciones_hecho_hecho(
                datos_corregidos["hecho_relacionado"]
            )
        
        # Validar contradicciones
        if "contradicciones" in datos_corregidos:
            datos_corregidos["contradicciones"] = self._validar_contradicciones(
                datos_corregidos["contradicciones"]
            )
        
        return datos_corregidos
    
    def obtener_estadisticas(self, datos_originales: Dict[str, Any], datos_corregidos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera estadísticas sobre las correcciones realizadas.
        
        Args:
            datos_originales: Datos antes de la validación
            datos_corregidos: Datos después de la validación
            
        Returns:
            Diccionario con estadísticas de las correcciones
        """
        estadisticas = {
            "entidad_relacion": {
                "total_original": len(datos_originales.get("entidad_relacion", [])),
                "total_corregido": len(datos_corregidos.get("entidad_relacion", [])),
                "descartadas": self.stats["entidad_relacion_descartadas"],
                "corregidas": self.stats["entidad_relacion_corregidas"]
            },
            "hecho_entidad": {
                "total_original": len(datos_originales.get("hecho_entidad", [])),
                "total_corregido": len(datos_corregidos.get("hecho_entidad", [])),
                "corregidas": self.stats["hecho_entidad_corregidas"]
            },
            "hecho_relacionado": {
                "total_original": len(datos_originales.get("hecho_relacionado", [])),
                "total_corregido": len(datos_corregidos.get("hecho_relacionado", [])),
                "descartadas": self.stats["hecho_relacionado_descartadas"]
            },
            "contradicciones": {
                "total_original": len(datos_originales.get("contradicciones", [])),
                "total_corregido": len(datos_corregidos.get("contradicciones", [])),
                "corregidas": self.stats["contradicciones_corregidas"]
            }
        }
        
        return estadisticas