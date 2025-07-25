"""
Fase 7B: Detección de Relaciones
=================================

Submódulo de la Fase 7 dedicado a la detección paralela de relaciones:
- 7B.1: Relaciones estructurales (hecho-entidad, entidad-entidad)
- 7B.2: Relaciones temporales (hecho-hecho, contradicciones)
"""

import asyncio  # noqa: F401
import json  # noqa: F401
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple  # noqa: F401

from loguru import logger

# Importar modelos
from ..models.procesamiento import (
    EntidadProcesada,  # noqa: F401
    HechoProcesado,  # noqa: F401
)


@dataclass
class RelacionHechoEntidad:
    """Relación entre un hecho y una entidad."""

    hecho_id: int
    entidad_id: int
    tipo_relacion: str  # protagonista, afectado, declarante, ubicacion, etc.
    relevancia_en_hecho: int  # 1-10


@dataclass
class RelacionEntidadEntidad:
    """Relación entre dos entidades."""

    entidad_origen_id: int
    entidad_destino_id: int
    tipo_relacion: str  # miembro_de, aliado_con, empleado_de, etc.
    descripcion: Optional[str] = None
    fecha_inicio: Optional[str] = None
    fecha_fin: Optional[str] = None
    fuerza_relacion: int = 5  # 1-10


@dataclass
class RelacionHechoHecho:
    """Relación temporal/causal entre dos hechos."""

    hecho_origen_id: int
    hecho_destino_id: int
    tipo_relacion: str  # causa, consecuencia, contexto_historico, etc.
    fuerza_relacion: int = 5  # 1-10
    descripcion_relacion: Optional[str] = None


@dataclass
class Contradiccion:
    """Contradicción detectada entre dos hechos."""

    hecho_principal_id: int
    hecho_contradictorio_id: int
    tipo_contradiccion: str  # fecha, contenido, entidades, etc.
    grado_contradiccion: int = 3  # 1-5
    descripcion: str


class DetectorRelaciones:
    """
    Detecta y analiza relaciones entre elementos extraídos.

    Procesa las relaciones detectadas por los LLMs y las estructura
    en objetos tipados para facilitar su uso posterior.
    """

    def __init__(self):
        """Inicializa el detector de relaciones."""
        self.relaciones_hecho_entidad: List[RelacionHechoEntidad] = []
        self.relaciones_entidad_entidad: List[RelacionEntidadEntidad] = []
        self.relaciones_hecho_hecho: List[RelacionHechoHecho] = []
        self.contradicciones: List[Contradiccion] = []

    def procesar_relaciones_estructurales(
        self, resultado_llm: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Procesa las relaciones estructurales detectadas por el LLM.

        Args:
            resultado_llm: Respuesta del LLM con relaciones estructurales

        Returns:
            Diccionario con relaciones procesadas y estadísticas
        """
        logger.info("Procesando relaciones estructurales")

        # Procesar relaciones hecho-entidad
        for rel in resultado_llm.get("hecho_entidad", []):
            try:
                relacion = RelacionHechoEntidad(
                    hecho_id=rel["hecho_id"],
                    entidad_id=rel["entidad_id"],
                    tipo_relacion=rel["tipo_relacion"],
                    relevancia_en_hecho=rel.get("relevancia_en_hecho", 5),
                )
                self.relaciones_hecho_entidad.append(relacion)
            except Exception as e:
                logger.warning(f"Error procesando relación hecho-entidad: {e}")

        # Procesar relaciones entidad-entidad
        for rel in resultado_llm.get("entidad_relacion", []):
            try:
                relacion = RelacionEntidadEntidad(
                    entidad_origen_id=rel["entidad_origen_id"],
                    entidad_destino_id=rel["entidad_destino_id"],
                    tipo_relacion=rel["tipo_relacion"],
                    descripcion=rel.get("descripcion"),
                    fecha_inicio=rel.get("fecha_inicio"),
                    fecha_fin=rel.get("fecha_fin"),
                    fuerza_relacion=rel.get("fuerza_relacion", 5),
                )
                self.relaciones_entidad_entidad.append(relacion)
            except Exception as e:
                logger.warning(f"Error procesando relación entidad-entidad: {e}")

        return {
            "hecho_entidad_procesadas": len(self.relaciones_hecho_entidad),
            "entidad_entidad_procesadas": len(self.relaciones_entidad_entidad),
        }

    def procesar_relaciones_temporales(
        self, resultado_llm: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Procesa las relaciones temporales detectadas por el LLM.

        Args:
            resultado_llm: Respuesta del LLM con relaciones temporales

        Returns:
            Diccionario con relaciones procesadas y estadísticas
        """
        logger.info("Procesando relaciones temporales")

        # Procesar relaciones hecho-hecho
        for rel in resultado_llm.get("hecho_relacionado", []):
            try:
                relacion = RelacionHechoHecho(
                    hecho_origen_id=rel["hecho_origen_id"],
                    hecho_destino_id=rel["hecho_destino_id"],
                    tipo_relacion=rel["tipo_relacion"],
                    fuerza_relacion=rel.get("fuerza_relacion", 5),
                    descripcion_relacion=rel.get("descripcion_relacion"),
                )
                self.relaciones_hecho_hecho.append(relacion)
            except Exception as e:
                logger.warning(f"Error procesando relación hecho-hecho: {e}")

        # Procesar contradicciones
        for cont in resultado_llm.get("contradicciones", []):
            try:
                contradiccion = Contradiccion(
                    hecho_principal_id=cont["hecho_principal_id"],
                    hecho_contradictorio_id=cont["hecho_contradictorio_id"],
                    tipo_contradiccion=cont["tipo_contradiccion"],
                    grado_contradiccion=cont.get("grado_contradiccion", 3),
                    descripcion=cont["descripcion"],
                )
                self.contradicciones.append(contradiccion)
            except Exception as e:
                logger.warning(f"Error procesando contradicción: {e}")

        return {
            "hecho_hecho_procesadas": len(self.relaciones_hecho_hecho),
            "contradicciones_detectadas": len(self.contradicciones),
        }

    def generar_grafo_relaciones(self) -> Dict[str, Any]:
        """
        Genera una representación de grafo de todas las relaciones.

        Returns:
            Diccionario con nodos y aristas del grafo
        """
        # Recopilar todos los nodos únicos
        nodos_hechos = set()
        nodos_entidades = set()

        # De relaciones hecho-entidad
        for rel in self.relaciones_hecho_entidad:
            nodos_hechos.add(rel.hecho_id)
            nodos_entidades.add(rel.entidad_id)

        # De relaciones entidad-entidad
        for rel in self.relaciones_entidad_entidad:
            nodos_entidades.add(rel.entidad_origen_id)
            nodos_entidades.add(rel.entidad_destino_id)

        # De relaciones hecho-hecho
        for rel in self.relaciones_hecho_hecho:
            nodos_hechos.add(rel.hecho_origen_id)
            nodos_hechos.add(rel.hecho_destino_id)

        # De contradicciones
        for cont in self.contradicciones:
            nodos_hechos.add(cont.hecho_principal_id)
            nodos_hechos.add(cont.hecho_contradictorio_id)

        # Construir grafo
        grafo = {
            "nodos": {
                "hechos": sorted(list(nodos_hechos)),
                "entidades": sorted(list(nodos_entidades)),
            },
            "aristas": {
                "hecho_entidad": [
                    {
                        "origen": f"hecho_{rel.hecho_id}",
                        "destino": f"entidad_{rel.entidad_id}",
                        "tipo": rel.tipo_relacion,
                        "peso": rel.relevancia_en_hecho,
                    }
                    for rel in self.relaciones_hecho_entidad
                ],
                "entidad_entidad": [
                    {
                        "origen": f"entidad_{rel.entidad_origen_id}",
                        "destino": f"entidad_{rel.entidad_destino_id}",
                        "tipo": rel.tipo_relacion,
                        "peso": rel.fuerza_relacion,
                    }
                    for rel in self.relaciones_entidad_entidad
                ],
                "hecho_hecho": [
                    {
                        "origen": f"hecho_{rel.hecho_origen_id}",
                        "destino": f"hecho_{rel.hecho_destino_id}",
                        "tipo": rel.tipo_relacion,
                        "peso": rel.fuerza_relacion,
                    }
                    for rel in self.relaciones_hecho_hecho
                ],
                "contradicciones": [
                    {
                        "origen": f"hecho_{cont.hecho_principal_id}",
                        "destino": f"hecho_{cont.hecho_contradictorio_id}",
                        "tipo": f"contradiccion_{cont.tipo_contradiccion}",
                        "peso": cont.grado_contradiccion,
                    }
                    for cont in self.contradicciones
                ],
            },
            "estadisticas": {
                "total_nodos": len(nodos_hechos) + len(nodos_entidades),
                "total_aristas": (
                    len(self.relaciones_hecho_entidad)
                    + len(self.relaciones_entidad_entidad)
                    + len(self.relaciones_hecho_hecho)
                    + len(self.contradicciones)
                ),
                "densidad": self._calcular_densidad_grafo(
                    len(nodos_hechos) + len(nodos_entidades),
                    len(self.relaciones_hecho_entidad)
                    + len(self.relaciones_entidad_entidad)
                    + len(self.relaciones_hecho_hecho),
                ),
            },
        }

        return grafo

    def _calcular_densidad_grafo(self, num_nodos: int, num_aristas: int) -> float:
        """
        Calcula la densidad del grafo.

        Args:
            num_nodos: Número de nodos
            num_aristas: Número de aristas

        Returns:
            Densidad entre 0 y 1
        """
        if num_nodos <= 1:
            return 0.0

        # Máximo de aristas posibles en grafo dirigido
        max_aristas = num_nodos * (num_nodos - 1)

        return num_aristas / max_aristas if max_aristas > 0 else 0.0

    def exportar_para_persistencia(self) -> Dict[str, Any]:
        """
        Exporta todas las relaciones en formato listo para persistir.

        Returns:
            Diccionario con todas las relaciones estructuradas
        """
        return {
            "relaciones_hecho_entidad": [
                {
                    "hecho_id": rel.hecho_id,
                    "entidad_id": rel.entidad_id,
                    "tipo_relacion": rel.tipo_relacion,
                    "relevancia": rel.relevancia_en_hecho,
                }
                for rel in self.relaciones_hecho_entidad
            ],
            "relaciones_entidad_entidad": [
                {
                    "entidad_origen_id": rel.entidad_origen_id,
                    "entidad_destino_id": rel.entidad_destino_id,
                    "tipo_relacion": rel.tipo_relacion,
                    "descripcion": rel.descripcion,
                    "fecha_inicio": rel.fecha_inicio,
                    "fecha_fin": rel.fecha_fin,
                    "fuerza": rel.fuerza_relacion,
                }
                for rel in self.relaciones_entidad_entidad
            ],
            "relaciones_hecho_hecho": [
                {
                    "hecho_origen_id": rel.hecho_origen_id,
                    "hecho_destino_id": rel.hecho_destino_id,
                    "tipo_relacion": rel.tipo_relacion,
                    "fuerza": rel.fuerza_relacion,
                    "descripcion": rel.descripcion_relacion,
                }
                for rel in self.relaciones_hecho_hecho
            ],
            "contradicciones": [
                {
                    "hecho_principal_id": cont.hecho_principal_id,
                    "hecho_contradictorio_id": cont.hecho_contradictorio_id,
                    "tipo": cont.tipo_contradiccion,
                    "grado": cont.grado_contradiccion,
                    "descripcion": cont.descripcion,
                }
                for cont in self.contradicciones
            ],
            "timestamp": datetime.now().isoformat(),
        }

    def generar_resumen_relaciones(self) -> str:
        """
        Genera un resumen textual de las relaciones detectadas.

        Returns:
            Resumen en texto
        """
        resumen_partes = []

        # Resumen de relaciones hecho-entidad
        if self.relaciones_hecho_entidad:
            tipos_he = {}
            for rel in self.relaciones_hecho_entidad:
                tipos_he[rel.tipo_relacion] = tipos_he.get(rel.tipo_relacion, 0) + 1

            resumen_partes.append(
                f"Relaciones hecho-entidad ({len(self.relaciones_hecho_entidad)}): "
                + ", ".join(f"{tipo}={count}" for tipo, count in tipos_he.items())
            )

        # Resumen de relaciones entidad-entidad
        if self.relaciones_entidad_entidad:
            tipos_ee = {}
            for rel in self.relaciones_entidad_entidad:
                tipos_ee[rel.tipo_relacion] = tipos_ee.get(rel.tipo_relacion, 0) + 1

            resumen_partes.append(
                f"Relaciones entidad-entidad ({len(self.relaciones_entidad_entidad)}): "
                + ", ".join(f"{tipo}={count}" for tipo, count in tipos_ee.items())
            )

        # Resumen de relaciones temporales
        if self.relaciones_hecho_hecho:
            tipos_hh = {}
            for rel in self.relaciones_hecho_hecho:
                tipos_hh[rel.tipo_relacion] = tipos_hh.get(rel.tipo_relacion, 0) + 1

            resumen_partes.append(
                f"Relaciones temporales ({len(self.relaciones_hecho_hecho)}): "
                + ", ".join(f"{tipo}={count}" for tipo, count in tipos_hh.items())
            )

        # Resumen de contradicciones
        if self.contradicciones:
            resumen_partes.append(
                f"Contradicciones detectadas: {len(self.contradicciones)}"
            )

        return (
            " | ".join(resumen_partes)
            if resumen_partes
            else "No se detectaron relaciones"
        )
