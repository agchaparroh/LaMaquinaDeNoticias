"""
SpacyAnalyzer: Análisis de Contenido con spaCy
==============================================

Componente que realiza análisis profundo del contenido usando spaCy
para extraer métricas que guían las decisiones del pipeline adaptativo.
"""

import hashlib
import re
from collections import Counter
from functools import lru_cache  # noqa: F401
from typing import Any, Dict, List, Optional, Tuple

try:
    import spacy
    from spacy.language import Language
    from spacy.tokens import Doc, Token
except ImportError:
    spacy = None
    Language = None
    Doc = None
    Token = None

from loguru import logger

from ..models.analisis import AnalisisComponentes


class SpacyAnalyzer:
    """
    Analizador de contenido usando spaCy.

    Extrae métricas del texto que se usan para tomar decisiones
    adaptativas sobre el flujo del pipeline y estrategias de chunking.
    """

    def __init__(self, nlp_model: Optional[Language] = None):
        """
        Inicializa el analizador.

        Args:
            nlp_model: Modelo spaCy precargado (opcional)
        """
        self.nlp = nlp_model
        self._model_cache = {}
        self._analysis_cache = {}  # Caché para análisis completos
        self._cache_max_size = 1000

        # Patrones compilados para mejor performance
        self.quote_pattern = re.compile(r'["«]([^"»]+)["»]')
        self.interview_pattern = re.compile(
            r"^(P:|R:|Pregunta:|Respuesta:|\-)", re.MULTILINE
        )
        self.number_pattern = re.compile(
            r"\b\d+(?:[.,]\d+)*\s*(?:%|€|\$|millones?|miles?|euros?|dólares?)"
        )
        self.date_pattern = re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}\b")
        self.money_pattern = re.compile(
            r"[€$]\s*\d+(?:[.,]\d+)*|(?:\d+(?:[.,]\d+)*\s*(?:euros?|dólares?))"
        )
        self.percent_pattern = re.compile(r"\b\d+(?:[.,]\d+)*\s*%")

        logger.info("SpacyAnalyzer inicializado")

    def _get_nlp_model(self, model_name: str = "es_core_news_lg") -> Optional[Language]:
        """Obtiene o carga el modelo spaCy."""
        if self.nlp:
            return self.nlp

        if not spacy:
            logger.warning("spaCy no está instalado. Análisis limitado.")
            return None

        if model_name not in self._model_cache:
            try:
                self._model_cache[model_name] = spacy.load(model_name)
                logger.debug(f"Modelo spaCy '{model_name}' cargado para análisis")
            except Exception as e:
                logger.warning(f"No se pudo cargar modelo spaCy '{model_name}': {e}")
                return None

        return self._model_cache.get(model_name)

    def _get_text_hash(self, texto: str) -> str:
        """Genera hash del texto para usar como clave de caché."""
        return hashlib.md5(texto.encode("utf-8")).hexdigest()[:16]

    def _get_cached_analysis(self, text_hash: str) -> Optional[AnalisisComponentes]:
        """Obtiene análisis desde caché si existe."""
        return self._analysis_cache.get(text_hash)

    def _set_cached_analysis(
        self, text_hash: str, analysis: AnalisisComponentes
    ) -> None:
        """Guarda análisis en caché con límite de tamaño."""
        if len(self._analysis_cache) >= self._cache_max_size:
            # Eliminar 20% de entradas más antiguas (simple LRU aproximado)
            keys_to_remove = list(self._analysis_cache.keys())[
                : self._cache_max_size // 5
            ]
            for key in keys_to_remove:
                del self._analysis_cache[key]

        self._analysis_cache[text_hash] = analysis

    def analizar_contenido(
        self, texto: str, modelo_nombre: str = "es_core_news_lg"
    ) -> AnalisisComponentes:
        """
        Analiza el contenido del texto y extrae métricas con caché optimizado.

        Args:
            texto: Texto a analizar
            modelo_nombre: Nombre del modelo spaCy a usar

        Returns:
            AnalisisComponentes con todas las métricas extraídas
        """
        if not texto or not texto.strip():
            return AnalisisComponentes()

        # Verificar caché primero
        text_hash = self._get_text_hash(texto)
        cached_analysis = self._get_cached_analysis(text_hash)
        if cached_analysis is not None:
            logger.debug(f"Cache hit para análisis de texto ({len(texto)} chars)")
            return cached_analysis

        # Inicializar resultado
        analisis = AnalisisComponentes()

        # Métricas básicas que no requieren spaCy
        analisis.longitud_caracteres = len(texto)
        analisis = self._analizar_patrones_basicos(texto, analisis)

        # Análisis con spaCy si está disponible
        nlp = self._get_nlp_model(modelo_nombre)
        if nlp:
            analisis = self._analizar_con_spacy(texto, nlp, analisis)
        else:
            # Fallback sin spaCy
            analisis = self._analizar_sin_spacy(texto, analisis)

        # Calcular densidades
        if analisis.conteo_tokens > 0:
            analisis.densidad_entidades = (
                analisis.conteo_entidades / analisis.conteo_tokens
            ) * 100
            analisis.densidad_numerica = (
                analisis.conteo_datos / analisis.conteo_tokens
            ) * 100

        # Guardar en caché
        self._set_cached_analysis(text_hash, analisis)
        logger.debug(f"Análisis guardado en caché para texto de {len(texto)} chars")

        return analisis

    def _analizar_patrones_basicos(
        self, texto: str, analisis: AnalisisComponentes
    ) -> AnalisisComponentes:
        """Analiza patrones usando regex."""
        # Detectar formato de entrevista
        entrevista_matches = self.interview_pattern.findall(texto)
        analisis.es_entrevista = len(entrevista_matches) > 3

        # Contar citas
        citas = self.quote_pattern.findall(texto)
        analisis.conteo_citas = len(citas)

        # Detectar números y unidades
        numeros = self.number_pattern.findall(texto)
        analisis.conteo_datos = len(numeros)

        # Detectar tipos específicos de datos
        analisis.tiene_fechas = bool(self.date_pattern.search(texto))
        analisis.tiene_monedas = bool(self.money_pattern.search(texto))
        analisis.tiene_porcentajes = bool(self.percent_pattern.search(texto))

        # Contar párrafos (aproximado)
        parrafos = [p.strip() for p in texto.split("\n\n") if p.strip()]
        analisis.conteo_parrafos = len(parrafos)

        return analisis

    def _analizar_con_spacy(
        self, texto: str, nlp: Language, analisis: AnalisisComponentes
    ) -> AnalisisComponentes:
        """Realiza análisis profundo con spaCy."""
        # Procesar texto
        doc = nlp(texto)

        # Conteos básicos
        analisis.conteo_tokens = len(doc)
        analisis.conteo_oraciones = len(list(doc.sents))

        # Análisis de entidades
        entidades = list(doc.ents)
        analisis.conteo_entidades = len(entidades)

        # Conteo por tipo de entidad
        tipo_counter = Counter(ent.label_ for ent in entidades)
        analisis.entidades_por_tipo = dict(tipo_counter)

        # Análisis por oración
        max_ents_por_oracion = 0
        total_tokens_oraciones = 0

        for sent in doc.sents:
            sent_ents = [
                ent
                for ent in entidades
                if ent.start >= sent.start and ent.end <= sent.end
            ]
            max_ents_por_oracion = max(max_ents_por_oracion, len(sent_ents))
            total_tokens_oraciones += len(sent)

        analisis.max_entidades_por_oracion = max_ents_por_oracion

        if analisis.conteo_oraciones > 0:
            analisis.promedio_tokens_por_oracion = (
                total_tokens_oraciones / analisis.conteo_oraciones
            )

        # Análisis adicional de datos numéricos
        numeros_adicionales = self._contar_numeros_spacy(doc)
        analisis.conteo_datos = max(analisis.conteo_datos, numeros_adicionales)

        return analisis

    def _analizar_sin_spacy(
        self, texto: str, analisis: AnalisisComponentes
    ) -> AnalisisComponentes:
        """Análisis fallback sin spaCy."""
        # Estimaciones básicas
        palabras = texto.split()
        analisis.conteo_tokens = len(palabras)

        # Estimar oraciones por puntuación
        oraciones = re.split(r"[.!?]+", texto)
        analisis.conteo_oraciones = len([o for o in oraciones if o.strip()])

        if analisis.conteo_oraciones > 0:
            analisis.promedio_tokens_por_oracion = (
                analisis.conteo_tokens / analisis.conteo_oraciones
            )

        # Detección básica de entidades (muy limitada)
        # Buscar palabras en mayúsculas que podrían ser nombres propios
        palabras_mayusculas = [
            p for p in palabras if p and p[0].isupper() and len(p) > 1
        ]
        analisis.conteo_entidades = (
            len(palabras_mayusculas) // 2
        )  # Estimación conservadora

        return analisis

    def _contar_numeros_spacy(self, doc: Doc) -> int:
        """Cuenta números con unidades usando análisis de tokens."""
        count = 0
        tokens = list(doc)

        for i, token in enumerate(tokens):
            if token.like_num or token.pos_ == "NUM":
                # Verificar si el siguiente token es una unidad
                if i + 1 < len(tokens):
                    next_token = tokens[i + 1]
                    if (
                        next_token.text.lower()
                        in ["%", "euros", "dólares", "millones", "miles", "€", "$"]
                        or next_token.pos_ == "NOUN"
                        and any(
                            unit in next_token.text.lower()
                            for unit in ["metro", "kilo", "litro", "año"]
                        )
                    ):
                        count += 1

        return count

    def sugerir_estrategia_chunking(
        self, analisis: AnalisisComponentes
    ) -> Dict[str, Any]:
        """
        Sugiere estrategia de chunking basada en el análisis.

        Args:
            analisis: Resultado del análisis de contenido

        Returns:
            Dict con recomendaciones de chunking
        """
        sugerencias = {
            "requiere_chunking": False,
            "chunk_size_recomendado": 3000,
            "overlap_recomendado": 200,
            "estrategia": "general",
            "razon": "",
        }

        # Determinar si requiere chunking
        razones = []

        if analisis.longitud_caracteres > 6000:
            sugerencias["requiere_chunking"] = True
            razones.append("texto muy largo")

        if analisis.conteo_entidades > 30:
            sugerencias["requiere_chunking"] = True
            razones.append("muchas entidades")
            sugerencias["estrategia"] = "entities"

        if analisis.es_entrevista or analisis.conteo_citas > 20:
            sugerencias["requiere_chunking"] = True
            razones.append("formato entrevista o muchas citas")
            sugerencias["estrategia"] = "quotes"
            sugerencias["chunk_size_recomendado"] = 2000

        if analisis.conteo_datos > 30:
            sugerencias["requiere_chunking"] = True
            razones.append("muchos datos numéricos")
            sugerencias["estrategia"] = "data"
            sugerencias["chunk_size_recomendado"] = 4000

        if analisis.max_entidades_por_oracion > 5:
            sugerencias["requiere_chunking"] = True
            razones.append("alta densidad de entidades por oración")
            sugerencias["overlap_recomendado"] = 300

        sugerencias["razon"] = (
            "; ".join(razones) if razones else "contenido dentro de límites normales"
        )

        return sugerencias

    def validar_metricas(self, analisis: AnalisisComponentes) -> Tuple[bool, List[str]]:
        """
        Valida que las métricas del análisis sean coherentes.

        Args:
            analisis: Análisis a validar

        Returns:
            Tuple de (es_valido, lista_de_advertencias)
        """
        advertencias = []

        # Validaciones básicas
        if analisis.conteo_tokens > 0 and analisis.conteo_oraciones == 0:
            advertencias.append("Tokens detectados pero sin oraciones")

        if analisis.conteo_entidades > analisis.conteo_tokens:
            advertencias.append("Más entidades que tokens (posible error)")

        if analisis.promedio_tokens_por_oracion > 100:
            advertencias.append("Oraciones extremadamente largas detectadas")

        if analisis.densidad_entidades > 50:
            advertencias.append("Densidad de entidades inusualmente alta")

        es_valido = len(advertencias) == 0

        return es_valido, advertencias


# Función de conveniencia
def create_spacy_analyzer(nlp_model: Optional[Language] = None) -> SpacyAnalyzer:
    """Factory function para crear SpacyAnalyzer."""
    return SpacyAnalyzer(nlp_model)
