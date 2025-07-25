"""
Servicio de Consolidación Cross-Chunk
=====================================

Consolida elementos duplicados o equivalentes extraídos de diferentes chunks,
unificando entidades, hechos, datos y citas para generar listas únicas.
"""

import difflib
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple  # noqa: F401

from ..utils.logging_config import get_logger

# Configurar logger para este módulo
logger = get_logger("ConsolidationService")

from ..models.procesamiento import (  # noqa: E402
    CitaTextual,
    DatosCuantitativos,
    EntidadProcesada,
    HechoProcesado,
)
from ..utils.similarity_algorithms import (  # noqa: E402
    OptimizedSimilarityProcessor,
    consolidar_elementos_optimizado,
)


@dataclass
class ConsolidationConfig:
    """Configuración para el proceso de consolidación."""

    similarity_threshold: float = 0.85  # Umbral de similitud para considerar duplicados
    exact_match_weight: float = 0.4  # Peso para coincidencia exacta
    fuzzy_match_weight: float = 0.3  # Peso para coincidencia difusa
    context_match_weight: float = 0.3  # Peso para coincidencia de contexto
    enable_groq_validation: bool = False  # Usar Groq para casos ambiguos
    # Configuraciones de optimización
    max_comparisons_per_type: int = 5000  # Límite de comparaciones por tipo
    use_vectorized_similarity: bool = True  # Usar algoritmos vectorizados
    early_termination_enabled: bool = True  # Habilitar early termination
    batch_size: int = 100  # Tamaño de batch para procesamiento


class ConsolidationService:
    """
    Servicio para consolidar elementos extraídos de múltiples chunks.

    Utiliza algoritmos de similitud para identificar y fusionar elementos
    duplicados manteniendo la coherencia y completitud de la información.
    """

    def __init__(self, config: Optional[ConsolidationConfig] = None):
        """
        Inicializa el servicio de consolidación.

        Args:
            config: Configuración del servicio
        """
        self.config = config or ConsolidationConfig()
        self.similarity_processor = OptimizedSimilarityProcessor()
        self._performance_stats = {
            "total_consolidations": 0,
            "total_elements_processed": 0,
            "total_time_seconds": 0.0,
            "average_time_per_element": 0.0,
        }
        logger.info(
            f"ConsolidationService inicializado con umbral: {self.config.similarity_threshold}"
        )

    def consolidar_entidades(
        self, entidades_por_chunk: List[List[EntidadProcesada]]
    ) -> List[EntidadProcesada]:
        """
        Consolida entidades de múltiples chunks eliminando duplicados.

        Args:
            entidades_por_chunk: Lista de entidades por cada chunk

        Returns:
            Lista consolidada de entidades únicas
        """
        start_time = time.time()
        logger.info(f"Consolidando entidades de {len(entidades_por_chunk)} chunks")

        # Aplanar todas las entidades
        todas_entidades = []
        for chunk_idx, entidades in enumerate(entidades_por_chunk):
            for entidad in entidades:
                # Añadir metadata del chunk
                entidad._chunk_origen = chunk_idx
                todas_entidades.append(entidad)

        logger.info(f"Total entidades antes de consolidación: {len(todas_entidades)}")

        # Agrupar por tipo para optimizar comparaciones
        entidades_por_tipo = defaultdict(list)
        for entidad in todas_entidades:
            entidades_por_tipo[entidad.tipo].append(entidad)

        # Consolidar dentro de cada tipo usando algoritmos optimizados
        entidades_consolidadas = []
        for tipo, entidades in entidades_por_tipo.items():
            logger.debug(f"Consolidando {len(entidades)} entidades de tipo {tipo}")
            consolidadas_tipo = self._consolidar_entidades_optimizado(entidades, tipo)
            entidades_consolidadas.extend(consolidadas_tipo)

        # Reasignar IDs secuenciales
        for idx, entidad in enumerate(entidades_consolidadas, 1):
            entidad.id_entidad = idx

        # Actualizar estadísticas de rendimiento
        elapsed_time = time.time() - start_time
        self._update_performance_stats(len(todas_entidades), elapsed_time)

        reduction_percent = (
            (1 - len(entidades_consolidadas) / len(todas_entidades)) * 100
            if todas_entidades
            else 0
        )
        logger.info(
            f"Consolidación completada: {len(todas_entidades)} → {len(entidades_consolidadas)} "
            f"({reduction_percent:.1f}% reducción, {elapsed_time:.2f}s)"
        )

        return entidades_consolidadas

    def _consolidar_entidades_mismo_tipo(
        self, entidades: List[EntidadProcesada]
    ) -> List[EntidadProcesada]:
        """
        Consolida entidades del mismo tipo.

        Args:
            entidades: Lista de entidades del mismo tipo

        Returns:
            Lista consolidada
        """
        if len(entidades) <= 1:
            return entidades

        grupos_consolidados = []
        procesadas = set()

        for i, entidad1 in enumerate(entidades):
            if i in procesadas:
                continue

            # Iniciar grupo con entidad actual
            grupo = [entidad1]
            procesadas.add(i)

            # Buscar entidades similares
            for j, entidad2 in enumerate(entidades[i + 1 :], i + 1):
                if j in procesadas:
                    continue

                similitud = self._calcular_similitud_entidades(entidad1, entidad2)
                if similitud >= self.config.similarity_threshold:
                    grupo.append(entidad2)
                    procesadas.add(j)

            # Fusionar grupo en una sola entidad
            entidad_consolidada = self._fusionar_entidades(grupo)
            grupos_consolidados.append(entidad_consolidada)

        return grupos_consolidados

    def _calcular_similitud_entidades(
        self, entidad1: EntidadProcesada, entidad2: EntidadProcesada
    ) -> float:
        """
        Calcula similitud entre dos entidades.

        Args:
            entidad1: Primera entidad
            entidad2: Segunda entidad

        Returns:
            Score de similitud entre 0 y 1
        """
        # Similitud exacta del nombre
        if entidad1.nombre.lower() == entidad2.nombre.lower():
            return 1.0

        # Similitud difusa del nombre
        nombre_sim = difflib.SequenceMatcher(
            None, entidad1.nombre.lower(), entidad2.nombre.lower()
        ).ratio()

        # Verificar alias
        alias1 = set(entidad1.metadata_entidad.alias or [])
        alias2 = set(entidad2.metadata_entidad.alias or [])

        # Si el nombre de una está en los alias de la otra
        if entidad1.nombre in alias2 or entidad2.nombre in alias1:
            return 0.95

        # Similitud de alias
        alias_overlap = len(alias1.intersection(alias2)) / max(
            len(alias1.union(alias2)), 1
        )

        # Combinar scores con pesos
        score_final = nombre_sim * 0.6 + alias_overlap * 0.4

        return score_final

    def _fusionar_entidades(self, grupo: List[EntidadProcesada]) -> EntidadProcesada:
        """
        Fusiona un grupo de entidades duplicadas en una sola.

        Args:
            grupo: Lista de entidades a fusionar

        Returns:
            Entidad consolidada
        """
        if len(grupo) == 1:
            return grupo[0]

        # Usar la primera como base
        entidad_base = grupo[0]

        # Recopilar todos los alias únicos
        todos_alias = set()
        for entidad in grupo:
            todos_alias.add(entidad.nombre)
            if entidad.metadata_entidad.alias:
                todos_alias.update(entidad.metadata_entidad.alias)

        # Remover el nombre principal de los alias
        todos_alias.discard(entidad_base.nombre)

        # Actualizar metadatos
        entidad_base.metadata_entidad.alias = sorted(list(todos_alias))

        # Combinar descripciones si existen
        descripciones = []
        for entidad in grupo:
            if entidad.metadata_entidad.descripcion:
                descripciones.append(entidad.metadata_entidad.descripcion)

        if descripciones:
            entidad_base.metadata_entidad.descripcion = " - ".join(set(descripciones))

        # Usar la mayor relevancia
        entidad_base.relevancia = max(e.relevancia for e in grupo)

        return entidad_base

    def consolidar_hechos(
        self, hechos_por_chunk: List[List[HechoProcesado]]
    ) -> List[HechoProcesado]:
        """
        Consolida hechos de múltiples chunks eliminando duplicados.

        Args:
            hechos_por_chunk: Lista de hechos por cada chunk

        Returns:
            Lista consolidada de hechos únicos
        """
        logger.info(f"Consolidando hechos de {len(hechos_por_chunk)} chunks")

        # Aplanar todos los hechos
        todos_hechos = []
        for chunk_idx, hechos in enumerate(hechos_por_chunk):
            for hecho in hechos:
                hecho._chunk_origen = chunk_idx
                todos_hechos.append(hecho)

        logger.info(f"Total hechos antes de consolidación: {len(todos_hechos)}")

        # Consolidar hechos similares
        hechos_consolidados = self._consolidar_hechos_similares(todos_hechos)

        # Reasignar IDs secuenciales
        for idx, hecho in enumerate(hechos_consolidados, 1):
            hecho.id_hecho = idx

        logger.info(
            f"Total hechos después de consolidación: {len(hechos_consolidados)}"
        )
        return hechos_consolidados

    def _consolidar_hechos_similares(
        self, hechos: List[HechoProcesado]
    ) -> List[HechoProcesado]:
        """
        Consolida hechos similares.

        Args:
            hechos: Lista de hechos a consolidar

        Returns:
            Lista consolidada
        """
        if len(hechos) <= 1:
            return hechos

        grupos_consolidados = []
        procesados = set()

        for i, hecho1 in enumerate(hechos):
            if i in procesados:
                continue

            # Iniciar grupo
            grupo = [hecho1]
            procesados.add(i)

            # Buscar hechos similares
            for j, hecho2 in enumerate(hechos[i + 1 :], i + 1):
                if j in procesados:
                    continue

                similitud = self._calcular_similitud_hechos(hecho1, hecho2)
                if similitud >= self.config.similarity_threshold:
                    grupo.append(hecho2)
                    procesados.add(j)

            # Fusionar grupo
            hecho_consolidado = self._fusionar_hechos(grupo)
            grupos_consolidados.append(hecho_consolidado)

        return grupos_consolidados

    def _calcular_similitud_hechos(
        self, hecho1: HechoProcesado, hecho2: HechoProcesado
    ) -> float:
        """
        Calcula similitud entre dos hechos.

        Args:
            hecho1: Primer hecho
            hecho2: Segundo hecho

        Returns:
            Score de similitud entre 0 y 1
        """
        # Similitud del texto
        texto_sim = difflib.SequenceMatcher(
            None, hecho1.contenido.lower(), hecho2.contenido.lower()
        ).ratio()

        # Bonus si son del mismo tipo
        tipo_bonus = (
            0.1
            if (hecho1.metadata_hecho.tipo_hecho == hecho2.metadata_hecho.tipo_hecho)
            else 0
        )

        # Bonus si tienen fechas similares
        fecha_bonus = 0
        if hecho1.metadata_hecho.fecha_inicio and hecho2.metadata_hecho.fecha_inicio:
            if hecho1.metadata_hecho.fecha_inicio == hecho2.metadata_hecho.fecha_inicio:
                fecha_bonus = 0.1

        return min(texto_sim + tipo_bonus + fecha_bonus, 1.0)

    def _fusionar_hechos(self, grupo: List[HechoProcesado]) -> HechoProcesado:
        """
        Fusiona un grupo de hechos duplicados.

        Args:
            grupo: Lista de hechos a fusionar

        Returns:
            Hecho consolidado
        """
        if len(grupo) == 1:
            return grupo[0]

        # Usar el más largo como base
        hecho_base = max(grupo, key=lambda h: len(h.contenido))

        # Nota: campo confianza_extraccion eliminado del modelo HechoProcesado

        # Combinar vinculaciones a entidades
        todas_vinculaciones = set()
        for hecho in grupo:
            todas_vinculaciones.update(hecho.vinculado_a_entidades)
        hecho_base.vinculado_a_entidades = sorted(list(todas_vinculaciones))

        return hecho_base

    def consolidar_datos(
        self, datos_por_chunk: List[List[DatosCuantitativos]]
    ) -> List[DatosCuantitativos]:
        """
        Consolida datos cuantitativos de múltiples chunks.

        Args:
            datos_por_chunk: Lista de datos por cada chunk

        Returns:
            Lista consolidada de datos únicos
        """
        logger.info(f"Consolidando datos de {len(datos_por_chunk)} chunks")

        # Aplanar todos los datos
        todos_datos = []
        for datos in datos_por_chunk:
            todos_datos.extend(datos)

        logger.info(f"Total datos antes de consolidación: {len(todos_datos)}")

        # Los datos cuantitativos raramente son duplicados exactos
        # Solo consolidar si son idénticos en valor e indicador
        datos_unicos = []
        datos_vistos = set()

        for dato in todos_datos:
            # Crear clave única
            clave = (dato.indicador.lower(), dato.valor_numerico, dato.unidad)

            if clave not in datos_vistos:
                datos_vistos.add(clave)
                datos_unicos.append(dato)

        # Reasignar IDs
        for idx, dato in enumerate(datos_unicos, 1):
            dato.id_dato_cuantitativo = idx

        logger.info(f"Total datos después de consolidación: {len(datos_unicos)}")
        return datos_unicos

    def consolidar_citas(
        self, citas_por_chunk: List[List[CitaTextual]]
    ) -> List[CitaTextual]:
        """
        Consolida citas textuales de múltiples chunks.

        Args:
            citas_por_chunk: Lista de citas por cada chunk

        Returns:
            Lista consolidada de citas únicas
        """
        logger.info(f"Consolidando citas de {len(citas_por_chunk)} chunks")

        # Aplanar todas las citas
        todas_citas = []
        for citas in citas_por_chunk:
            todas_citas.extend(citas)

        logger.info(f"Total citas antes de consolidación: {len(todas_citas)}")

        # Consolidar citas idénticas o muy similares
        citas_consolidadas = self._consolidar_citas_similares(todas_citas)

        # Reasignar IDs
        for idx, cita in enumerate(citas_consolidadas, 1):
            cita.id_cita = idx

        logger.info(f"Total citas después de consolidación: {len(citas_consolidadas)}")
        return citas_consolidadas

    def _consolidar_citas_similares(
        self, citas: List[CitaTextual]
    ) -> List[CitaTextual]:
        """
        Consolida citas similares.

        Args:
            citas: Lista de citas a consolidar

        Returns:
            Lista consolidada
        """
        if len(citas) <= 1:
            return citas

        citas_unicas = []
        citas_vistas = set()

        for cita in citas:
            # Normalizar texto para comparación
            texto_norm = cita.cita.lower().strip()

            # Buscar si ya existe una cita muy similar
            es_duplicada = False
            for texto_existente in citas_vistas:
                similitud = difflib.SequenceMatcher(
                    None, texto_norm, texto_existente
                ).ratio()

                if similitud >= 0.95:  # Umbral alto para citas
                    es_duplicada = True
                    break

            if not es_duplicada:
                citas_vistas.add(texto_norm)
                citas_unicas.append(cita)

        return citas_unicas

    def actualizar_referencias_cruzadas(
        self,
        entidades: List[EntidadProcesada],
        hechos: List[HechoProcesado],
        datos: List[DatosCuantitativos],
        citas: List[CitaTextual],
        mapeo_ids: Dict[str, Dict[int, int]],
    ) -> None:
        """
        Actualiza las referencias cruzadas entre elementos después de la consolidación.

        Args:
            entidades: Entidades consolidadas
            hechos: Hechos consolidados
            datos: Datos consolidados
            citas: Citas consolidadas
            mapeo_ids: Mapeo de IDs antiguos a nuevos
        """
        logger.info("Actualizando referencias cruzadas post-consolidación")

        # Actualizar referencias en hechos
        for hecho in hechos:
            nuevas_vinculaciones = []
            for entidad_id in hecho.vinculado_a_entidades:
                nuevo_id = mapeo_ids.get("entidades", {}).get(entidad_id, entidad_id)
                nuevas_vinculaciones.append(nuevo_id)
            hecho.vinculado_a_entidades = nuevas_vinculaciones

        # Actualizar referencias en datos
        for dato in datos:
            if dato.metadata_dato.hecho_id_relacionado:
                dato.metadata_dato.hecho_id_relacionado = mapeo_ids.get(
                    "hechos", {}
                ).get(
                    dato.metadata_dato.hecho_id_relacionado,
                    dato.metadata_dato.hecho_id_relacionado,
                )

        # Actualizar referencias en citas
        for cita in citas:
            if cita.entidad_emisora_id:
                cita.entidad_emisora_id = mapeo_ids.get("entidades", {}).get(
                    cita.entidad_emisora_id, cita.entidad_emisora_id
                )

            if cita.metadata_cita.hecho_relacionado_id:
                cita.metadata_cita.hecho_relacionado_id = mapeo_ids.get(
                    "hechos", {}
                ).get(
                    cita.metadata_cita.hecho_relacionado_id,
                    cita.metadata_cita.hecho_relacionado_id,
                )

    # =====================================================================
    # MÉTODOS OPTIMIZADOS PARA PERFORMANCE
    # =====================================================================

    def _consolidar_entidades_optimizado(
        self, entidades: List[EntidadProcesada], tipo: str
    ) -> List[EntidadProcesada]:
        """
        Consolida entidades del mismo tipo usando algoritmos optimizados.

        Args:
            entidades: Lista de entidades del mismo tipo
            tipo: Tipo de entidad

        Returns:
            Lista consolidada
        """
        if len(entidades) <= 1:
            return entidades

        # Usar algoritmos optimizados si están habilitados
        if self.config.use_vectorized_similarity and len(entidades) > 10:
            return self._consolidar_con_algoritmos_vectorizados(entidades, tipo)
        else:
            return self._consolidar_entidades_mismo_tipo(entidades)

    def _consolidar_con_algoritmos_vectorizados(
        self, entidades: List[EntidadProcesada], tipo: str
    ) -> List[EntidadProcesada]:
        """
        Consolida usando algoritmos vectorizados optimizados.

        Args:
            entidades: Lista de entidades
            tipo: Tipo de entidad

        Returns:
            Lista consolidada
        """
        start_time = time.time()

        # Extraer textos para comparación
        textos_entidades = [entidad.nombre for entidad in entidades]

        # Usar algoritmo optimizado con early termination
        grupos_similares = consolidar_elementos_optimizado(
            textos_entidades,
            umbral=self.config.similarity_threshold,
            max_comparaciones=self.config.max_comparisons_per_type,
        )

        # Construir entidades consolidadas
        entidades_consolidadas = []
        for grupo in grupos_similares:
            if len(grupo) == 1:
                # Entidad única, agregar tal como está
                entidades_consolidadas.append(entidades[grupo[0]])
            else:
                # Fusionar entidades similares
                entidad_fusionada = self._fusionar_entidades_grupo(
                    [entidades[i] for i in grupo]
                )
                entidades_consolidadas.append(entidad_fusionada)

        elapsed_time = time.time() - start_time
        logger.debug(
            f"Consolidación vectorizada de {len(entidades)} entidades tipo {tipo}: "
            f"{len(entidades_consolidadas)} resultado, {elapsed_time:.3f}s"
        )

        return entidades_consolidadas

    def _fusionar_entidades_grupo(
        self, entidades: List[EntidadProcesada]
    ) -> EntidadProcesada:
        """
        Fusiona un grupo de entidades similares en una sola.

        Args:
            entidades: Grupo de entidades similares

        Returns:
            Entidad fusionada
        """
        if len(entidades) == 1:
            return entidades[0]

        # Usar la primera entidad como base
        entidad_base = entidades[0]

        # Fusionar datos de todas las entidades
        chunks_origen = set()
        relevancia_total = 0.0
        apariciones_total = 0

        for entidad in entidades:
            if hasattr(entidad, "_chunk_origen"):
                chunks_origen.add(entidad._chunk_origen)
            relevancia_total += entidad.relevancia
            # apariciones_entidad no existe en el modelo - usar contador simple
            apariciones_total += 1

        # Crear entidad fusionada
        entidad_fusionada = EntidadProcesada(
            id_entidad=entidad_base.id_entidad,
            nombre=entidad_base.nombre,
            tipo=entidad_base.tipo,
            relevancia=relevancia_total / len(entidades),  # Promedio
            id_fragmento_origen=entidad_base.id_fragmento_origen,  # CAMPO REQUERIDO
            metadata_entidad=entidad_base.metadata_entidad,
        )

        # Agregar metadata de chunks origen
        entidad_fusionada._chunks_origen = chunks_origen
        entidad_fusionada._elementos_fusionados = len(entidades)

        return entidad_fusionada

    def _update_performance_stats(
        self, elements_processed: int, elapsed_time: float
    ) -> None:
        """
        Actualiza estadísticas de rendimiento.

        Args:
            elements_processed: Número de elementos procesados
            elapsed_time: Tiempo transcurrido en segundos
        """
        self._performance_stats["total_consolidations"] += 1
        self._performance_stats["total_elements_processed"] += elements_processed
        self._performance_stats["total_time_seconds"] += elapsed_time

        if self._performance_stats["total_elements_processed"] > 0:
            self._performance_stats["average_time_per_element"] = (
                self._performance_stats["total_time_seconds"]
                / self._performance_stats["total_elements_processed"]
            )

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de rendimiento del servicio.

        Returns:
            Diccionario con estadísticas de performance
        """
        return self._performance_stats.copy()

    def reset_performance_stats(self) -> None:
        """Reinicia las estadísticas de rendimiento."""
        self._performance_stats = {
            "total_consolidations": 0,
            "total_elements_processed": 0,
            "total_time_seconds": 0.0,
            "average_time_per_element": 0.0,
        }
        logger.info("Referencias cruzadas actualizadas exitosamente")
