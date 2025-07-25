"""
Schema Validator para Pipeline de 7 Fases
========================================

Valida la coherencia de los esquemas JSON entre las diferentes fases
del pipeline, asegurando que los datos fluyan correctamente.
"""

import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field, validator  # noqa: F401

from .logging_config import get_logger

# Configurar logger para este módulo
logger = get_logger("SchemaValidator")


class TipoEntidad(str, Enum):
    """Tipos de entidad coherentes con los prompts."""

    PERSONA = "PERSONA"
    ORGANIZACION = "ORGANIZACION"
    INSTITUCION = "INSTITUCION"
    LUGAR = "LUGAR"
    EVENTO = "EVENTO"
    NORMATIVA = "NORMATIVA"
    CONCEPTO = "CONCEPTO"


class TipoHecho(str, Enum):
    """Tipos de hecho coherentes con los prompts."""

    SUCESO = "SUCESO"
    ANUNCIO = "ANUNCIO"
    DECLARACION = "DECLARACION"
    BIOGRAFIA = "BIOGRAFIA"
    CONCEPTO = "CONCEPTO"
    NORMATIVA = "NORMATIVA"
    EVENTO = "EVENTO"


class TipoDato(str, Enum):
    """Tipos de dato cuantitativo."""

    ECONOMICO = "ECONOMICO"
    DEMOGRAFICO = "DEMOGRAFICO"
    ESTADISTICO = "ESTADISTICO"
    TEMPORAL = "TEMPORAL"
    OTRO = "OTRO"


class TipoCita(str, Enum):
    """Tipos de cita textual."""

    DIRECTA = "DIRECTA"
    INDIRECTA = "INDIRECTA"
    PARCIAL = "PARCIAL"


class SchemaValidator:
    """
    Valida esquemas JSON de las diferentes fases del pipeline.

    Responsabilidades:
    - Validar formato de IDs (secuenciales vs UUID)
    - Verificar tipos coherentes entre fases
    - Validar referencias cruzadas
    - Asegurar formato de fechas consistente
    """

    # Mapeo de tipos de entidad LLM a tipos internos
    TIPO_ENTIDAD_MAP = {
        "PERSONA": "PER",
        "ORGANIZACION": "ORG",
        "INSTITUCION": "ORG",
        "LUGAR": "LOC",
        "EVENTO": "EVENT",
        "NORMATIVA": "LAW",
        "CONCEPTO": "MISC",
    }

    # Mapeo inverso
    TIPO_INTERNO_MAP = {
        "PER": "PERSONA",
        "ORG": "ORGANIZACION",
        "LOC": "LUGAR",
        "EVENT": "EVENTO",
        "LAW": "NORMATIVA",
        "MISC": "CONCEPTO",
    }

    def __init__(self):
        """Inicializa el validador."""
        self.ids_vistos: Dict[str, Set[int]] = {
            "entidades": set(),
            "hechos": set(),
            "datos": set(),
            "citas": set(),
        }
        self.errores: List[str] = []
        self.advertencias: List[str] = []

    def validar_id_secuencial(self, id_valor: Any, tipo: str) -> bool:
        """
        Valida que un ID sea secuencial y único.

        Args:
            id_valor: Valor del ID a validar
            tipo: Tipo de elemento (entidades, hechos, etc)

        Returns:
            True si el ID es válido
        """
        # Verificar que sea entero
        if not isinstance(id_valor, int):
            self.errores.append(f"ID de {tipo} no es entero: {id_valor}")
            return False

        # Verificar que sea positivo
        if id_valor <= 0:
            self.errores.append(f"ID de {tipo} no es positivo: {id_valor}")
            return False

        # Verificar unicidad
        if id_valor in self.ids_vistos[tipo]:
            self.errores.append(f"ID duplicado en {tipo}: {id_valor}")
            return False

        self.ids_vistos[tipo].add(id_valor)
        return True

    def validar_fecha(self, fecha: Any, campo: str) -> bool:
        """
        Valida formato de fecha YYYY-MM-DD.

        Args:
            fecha: Valor de fecha a validar
            campo: Nombre del campo para mensajes

        Returns:
            True si la fecha es válida
        """
        if fecha is None:
            return True  # null es válido

        if not isinstance(fecha, str):
            self.errores.append(f"Fecha en {campo} no es string: {fecha}")
            return False

        # Validar formato YYYY-MM-DD
        patron = r"^\d{4}-\d{2}-\d{2}$"
        if not re.match(patron, fecha):
            self.errores.append(f"Fecha en {campo} con formato incorrecto: {fecha}")
            return False

        # Validar que sea fecha válida
        try:
            datetime.strptime(fecha, "%Y-%m-%d")
        except ValueError:
            self.errores.append(f"Fecha inválida en {campo}: {fecha}")
            return False

        return True

    def validar_entidades(self, entidades: List[Dict[str, Any]]) -> bool:
        """
        Valida esquema de entidades (Fase 3).

        Args:
            entidades: Lista de entidades extraídas

        Returns:
            True si todas las entidades son válidas
        """
        valido = True

        for idx, entidad in enumerate(entidades):
            # Validar ID
            if "id" not in entidad:
                self.errores.append(f"Entidad {idx} sin ID")
                valido = False
            elif not self.validar_id_secuencial(entidad["id"], "entidades"):
                valido = False

            # Validar campos requeridos
            campos_requeridos = ["nombre", "tipo"]
            for campo in campos_requeridos:
                if campo not in entidad:
                    self.errores.append(
                        f"Entidad {entidad.get('id', idx)} sin campo {campo}"
                    )
                    valido = False

            # Validar tipo
            if "tipo" in entidad:
                if entidad["tipo"] not in [t.value for t in TipoEntidad]:
                    self.errores.append(
                        f"Tipo inválido en entidad {entidad.get('id', idx)}: {entidad['tipo']}"
                    )
                    valido = False

            # Validar alias como array
            if "alias" in entidad and not isinstance(entidad["alias"], list):
                self.errores.append(
                    f"Alias no es array en entidad {entidad.get('id', idx)}"
                )
                valido = False

            # Validar fechas
            for campo_fecha in ["fecha_nacimiento", "fecha_disolucion"]:
                if campo_fecha in entidad:
                    self.validar_fecha(
                        entidad[campo_fecha],
                        f"entidad {entidad.get('id', idx)}.{campo_fecha}",
                    )

            # Validar descripción con guiones
            if "descripcion" in entidad and entidad["descripcion"]:
                if not entidad["descripcion"].startswith("-"):
                    self.advertencias.append(
                        f"Descripción de entidad {entidad.get('id', idx)} no empieza con guión"
                    )

        return valido

    def validar_hechos(self, hechos: List[Dict[str, Any]]) -> bool:
        """
        Valida esquema de hechos (Fase 4).

        Args:
            hechos: Lista de hechos extraídos

        Returns:
            True si todos los hechos son válidos
        """
        valido = True

        for idx, hecho in enumerate(hechos):
            # Validar ID
            if "id" not in hecho:
                self.errores.append(f"Hecho {idx} sin ID")
                valido = False
            elif not self.validar_id_secuencial(hecho["id"], "hechos"):
                valido = False

            # Validar campos requeridos
            campos_requeridos = ["contenido", "fecha", "tipo_hecho"]
            for campo in campos_requeridos:
                if campo not in hecho:
                    self.errores.append(
                        f"Hecho {hecho.get('id', idx)} sin campo {campo}"
                    )
                    valido = False

            # Validar tipo
            if "tipo_hecho" in hecho:
                if hecho["tipo_hecho"] not in [t.value for t in TipoHecho]:
                    self.errores.append(
                        f"Tipo inválido en hecho {hecho.get('id', idx)}: {hecho['tipo_hecho']}"
                    )
                    valido = False

            # Validar objeto fecha
            if "fecha" in hecho:
                if not isinstance(hecho["fecha"], dict):
                    self.errores.append(
                        f"Fecha no es objeto en hecho {hecho.get('id', idx)}"
                    )
                    valido = False
                else:
                    if "inicio" not in hecho["fecha"] or "fin" not in hecho["fecha"]:
                        self.errores.append(
                            f"Fecha sin inicio/fin en hecho {hecho.get('id', idx)}"
                        )
                        valido = False
                    else:
                        self.validar_fecha(
                            hecho["fecha"]["inicio"],
                            f"hecho {hecho.get('id', idx)}.fecha.inicio",
                        )
                        self.validar_fecha(
                            hecho["fecha"]["fin"],
                            f"hecho {hecho.get('id', idx)}.fecha.fin",
                        )

            # Validar arrays de ubicación
            for campo_array in ["pais", "region", "ciudad"]:
                if campo_array in hecho and not isinstance(hecho[campo_array], list):
                    self.errores.append(
                        f"{campo_array} no es array en hecho {hecho.get('id', idx)}"
                    )
                    valido = False

            # Validar booleano
            if "es_futuro" in hecho and not isinstance(hecho["es_futuro"], bool):
                self.errores.append(
                    f"es_futuro no es booleano en hecho {hecho.get('id', idx)}"
                )
                valido = False

        return valido

    def validar_datos(self, datos: List[Dict[str, Any]]) -> bool:
        """
        Valida esquema de datos cuantitativos (Fase 5).

        Args:
            datos: Lista de datos extraídos

        Returns:
            True si todos los datos son válidos
        """
        valido = True

        for idx, dato in enumerate(datos):
            # Validar ID
            if "id" not in dato:
                self.errores.append(f"Dato {idx} sin ID")
                valido = False
            elif not self.validar_id_secuencial(dato["id"], "datos"):
                valido = False

            # Validar campos requeridos
            campos_requeridos = ["descripcion", "valor", "unidad"]
            for campo in campos_requeridos:
                if campo not in dato:
                    self.errores.append(f"Dato {dato.get('id', idx)} sin campo {campo}")
                    valido = False

            # Validar valor numérico
            if "valor" in dato:
                if not isinstance(dato["valor"], (int, float)):
                    self.errores.append(
                        f"Valor no numérico en dato {dato.get('id', idx)}: {dato['valor']}"
                    )
                    valido = False

            # Validar tipo
            if "tipo_dato" in dato:
                if dato["tipo_dato"] not in [t.value for t in TipoDato]:
                    self.advertencias.append(
                        f"Tipo no estándar en dato {dato.get('id', idx)}: {dato['tipo_dato']}"
                    )

            # Validar fecha
            if "fecha" in dato:
                self.validar_fecha(dato["fecha"], f"dato {dato.get('id', idx)}.fecha")

        return valido

    def validar_citas(self, citas: List[Dict[str, Any]]) -> bool:
        """
        Valida esquema de citas (Fase 6).

        Args:
            citas: Lista de citas extraídas

        Returns:
            True si todas las citas son válidas
        """
        valido = True

        for idx, cita in enumerate(citas):
            # Validar ID
            if "id" not in cita:
                self.errores.append(f"Cita {idx} sin ID")
                valido = False
            elif not self.validar_id_secuencial(cita["id"], "citas"):
                valido = False

            # Validar campos requeridos
            campos_requeridos = ["cita", "persona_citada"]
            for campo in campos_requeridos:
                if campo not in cita:
                    self.errores.append(f"Cita {cita.get('id', idx)} sin campo {campo}")
                    valido = False

            # Validar tipo
            if "tipo_cita" in cita:
                if cita["tipo_cita"] not in [t.value for t in TipoCita]:
                    self.advertencias.append(
                        f"Tipo no estándar en cita {cita.get('id', idx)}: {cita['tipo_cita']}"
                    )

            # Validar referencia a entidad
            if "entidad_id" in cita and cita["entidad_id"] is not None:
                if not isinstance(cita["entidad_id"], int):
                    self.errores.append(
                        f"entidad_id no es entero en cita {cita.get('id', idx)}: {cita['entidad_id']}"
                    )
                    valido = False
                elif cita["entidad_id"] not in self.ids_vistos["entidades"]:
                    self.advertencias.append(
                        f"Cita {cita.get('id', idx)} referencia entidad inexistente: {cita['entidad_id']}"
                    )

        return valido

    def validar_relaciones_estructurales(self, relaciones: Dict[str, Any]) -> bool:
        """
        Valida esquema de relaciones estructurales (Fase 7B.1).

        Args:
            relaciones: Diccionario con relaciones estructurales

        Returns:
            True si todas las relaciones son válidas
        """
        valido = True

        # Validar relaciones hecho-entidad
        if "hecho_entidad" in relaciones:
            for idx, rel in enumerate(relaciones["hecho_entidad"]):
                # Validar referencias
                if (
                    "hecho_id" in rel
                    and rel["hecho_id"] not in self.ids_vistos["hechos"]
                ):
                    self.advertencias.append(
                        f"Relación hecho-entidad {idx} referencia hecho inexistente: {rel['hecho_id']}"
                    )
                if (
                    "entidad_id" in rel
                    and rel["entidad_id"] not in self.ids_vistos["entidades"]
                ):
                    self.advertencias.append(
                        f"Relación hecho-entidad {idx} referencia entidad inexistente: {rel['entidad_id']}"
                    )

                # Validar relevancia
                if "relevancia_en_hecho" in rel:
                    if (
                        not isinstance(rel["relevancia_en_hecho"], int)
                        or rel["relevancia_en_hecho"] < 1
                        or rel["relevancia_en_hecho"] > 10
                    ):
                        self.errores.append(
                            f"Relevancia inválida en relación hecho-entidad {idx}: {rel['relevancia_en_hecho']}"
                        )
                        valido = False

        # Validar relaciones entidad-entidad
        if "entidad_relacion" in relaciones:
            for idx, rel in enumerate(relaciones["entidad_relacion"]):
                # Validar referencias
                if (
                    "entidad_origen_id" in rel
                    and rel["entidad_origen_id"] not in self.ids_vistos["entidades"]
                ):
                    self.advertencias.append(
                        f"Relación entidad-entidad {idx} referencia origen inexistente: {rel['entidad_origen_id']}"
                    )
                if (
                    "entidad_destino_id" in rel
                    and rel["entidad_destino_id"] not in self.ids_vistos["entidades"]
                ):
                    self.advertencias.append(
                        f"Relación entidad-entidad {idx} referencia destino inexistente: {rel['entidad_destino_id']}"
                    )

                # Validar fechas
                for campo_fecha in ["fecha_inicio", "fecha_fin"]:
                    if campo_fecha in rel:
                        self.validar_fecha(
                            rel[campo_fecha],
                            f"relación entidad-entidad {idx}.{campo_fecha}",
                        )

        return valido

    def validar_relaciones_temporales(self, relaciones: Dict[str, Any]) -> bool:
        """
        Valida esquema de relaciones temporales (Fase 7B.2).

        Args:
            relaciones: Diccionario con relaciones temporales

        Returns:
            True si todas las relaciones son válidas
        """
        valido = True

        # Validar relaciones hecho-hecho
        if "hecho_relacionado" in relaciones:
            for idx, rel in enumerate(relaciones["hecho_relacionado"]):
                # Validar referencias
                if (
                    "hecho_origen_id" in rel
                    and rel["hecho_origen_id"] not in self.ids_vistos["hechos"]
                ):
                    self.advertencias.append(
                        f"Relación hecho-hecho {idx} referencia origen inexistente: {rel['hecho_origen_id']}"
                    )
                if (
                    "hecho_destino_id" in rel
                    and rel["hecho_destino_id"] not in self.ids_vistos["hechos"]
                ):
                    self.advertencias.append(
                        f"Relación hecho-hecho {idx} referencia destino inexistente: {rel['hecho_destino_id']}"
                    )

        # Validar contradicciones
        if "contradicciones" in relaciones:
            for idx, cont in enumerate(relaciones["contradicciones"]):
                # Validar referencias
                if (
                    "hecho_principal_id" in cont
                    and cont["hecho_principal_id"] not in self.ids_vistos["hechos"]
                ):
                    self.advertencias.append(
                        f"Contradicción {idx} referencia principal inexistente: {cont['hecho_principal_id']}"
                    )
                if (
                    "hecho_contradictorio_id" in cont
                    and cont["hecho_contradictorio_id"] not in self.ids_vistos["hechos"]
                ):
                    self.advertencias.append(
                        f"Contradicción {idx} referencia contradictorio inexistente: {cont['hecho_contradictorio_id']}"
                    )

                # Validar grado
                if "grado_contradiccion" in cont:
                    if (
                        not isinstance(cont["grado_contradiccion"], int)
                        or cont["grado_contradiccion"] < 1
                        or cont["grado_contradiccion"] > 5
                    ):
                        self.errores.append(
                            f"Grado inválido en contradicción {idx}: {cont['grado_contradiccion']}"
                        )
                        valido = False

        return valido

    def validar_pipeline_completo(
        self, resultado: Dict[str, Any]
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Valida el resultado completo del pipeline de 7 fases.

        Args:
            resultado: Diccionario con todos los resultados del pipeline

        Returns:
            Tupla (es_valido, errores, advertencias)
        """
        # Resetear estado
        self.ids_vistos = {
            "entidades": set(),
            "hechos": set(),
            "datos": set(),
            "citas": set(),
        }
        self.errores = []
        self.advertencias = []

        valido = True

        # Validar cada fase si está presente
        if "entidades" in resultado:
            valido &= self.validar_entidades(resultado["entidades"])

        if "hechos" in resultado:
            valido &= self.validar_hechos(resultado["hechos"])

        if "datos" in resultado:
            valido &= self.validar_datos(resultado["datos"])

        if "citas" in resultado:
            valido &= self.validar_citas(resultado["citas"])

        if "relaciones_estructurales" in resultado:
            valido &= self.validar_relaciones_estructurales(
                resultado["relaciones_estructurales"]
            )

        if "relaciones_temporales" in resultado:
            valido &= self.validar_relaciones_temporales(
                resultado["relaciones_temporales"]
            )

        # Log resumen
        if self.errores:
            logger.error(f"Validación con {len(self.errores)} errores")
        if self.advertencias:
            logger.warning(f"Validación con {len(self.advertencias)} advertencias")

        return valido, self.errores, self.advertencias

    @staticmethod
    def convertir_tipo_entidad_a_interno(tipo_llm: str) -> str:
        """
        Convierte tipo de entidad del LLM a tipo interno.

        Args:
            tipo_llm: Tipo devuelto por el LLM

        Returns:
            Tipo interno correspondiente
        """
        return SchemaValidator.TIPO_ENTIDAD_MAP.get(tipo_llm, "MISC")

    @staticmethod
    def convertir_tipo_interno_a_entidad(tipo_interno: str) -> str:
        """
        Convierte tipo interno a tipo de entidad del LLM.

        Args:
            tipo_interno: Tipo interno

        Returns:
            Tipo LLM correspondiente
        """
        return SchemaValidator.TIPO_INTERNO_MAP.get(tipo_interno, "CONCEPTO")

    @staticmethod
    def normalizar_descripcion_entidad(descripcion: Optional[str]) -> Optional[str]:
        """
        Normaliza descripción de entidad (quita guiones).

        Args:
            descripcion: Descripción con formato de guiones

        Returns:
            Descripción normalizada
        """
        if not descripcion:
            return None

        # Quitar guiones al inicio de cada línea
        lineas = descripcion.split("\n")
        lineas_normalizadas = []

        for linea in lineas:
            linea = linea.strip()
            if linea.startswith("-"):
                linea = linea[1:].strip()
            if linea:
                lineas_normalizadas.append(linea)

        return ". ".join(lineas_normalizadas) if lineas_normalizadas else None


# Funciones de utilidad
def validar_resultado_fase(
    fase: int, resultado: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Valida el resultado de una fase específica.

    Args:
        fase: Número de fase (1-7)
        resultado: Resultado de la fase

    Returns:
        Tupla (es_valido, errores)
    """
    validator = SchemaValidator()  # noqa: F811

    if fase == 3:
        valido = validator.validar_entidades(resultado.get("entidades", []))
    elif fase == 4:
        valido = validator.validar_hechos(resultado.get("hechos", []))
    elif fase == 5:
        valido = validator.validar_datos(resultado.get("datos", []))
    elif fase == 6:
        valido = validator.validar_citas(resultado.get("citas", []))
    elif fase == 7:
        valido = True
        if "relaciones_estructurales" in resultado:
            valido &= validator.validar_relaciones_estructurales(
                resultado["relaciones_estructurales"]
            )
        if "relaciones_temporales" in resultado:
            valido &= validator.validar_relaciones_temporales(
                resultado["relaciones_temporales"]
            )
    else:
        return True, []  # Fases 1 y 2 no tienen esquema específico

    return valido, validator.errores


def asegurar_coherencia_ids(
    elementos: List[Dict[str, Any]], tipo: str
) -> List[Dict[str, Any]]:
    """
    Asegura que los IDs sean secuenciales empezando desde 1.

    Args:
        elementos: Lista de elementos con IDs
        tipo: Tipo de elemento para logging

    Returns:
        Lista con IDs corregidos
    """
    elementos_corregidos = []

    for idx, elemento in enumerate(elementos, 1):
        elemento_copia = elemento.copy()
        if "id" in elemento_copia:
            if elemento_copia["id"] != idx:
                logger.debug(
                    f"Corrigiendo ID de {tipo}: {elemento_copia['id']} -> {idx}"
                )
        elemento_copia["id"] = idx
        elementos_corregidos.append(elemento_copia)

    return elementos_corregidos
