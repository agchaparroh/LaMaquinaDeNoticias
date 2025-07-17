"""
Algoritmos de Similitud para Consolidación
==========================================

Implementa algoritmos de similitud para detectar elementos duplicados
o equivalentes durante la consolidación cross-chunk.
"""

from typing import List, Tuple, Set, Optional, Dict
import difflib
import re
from collections import Counter
import unicodedata
# Importar numpy si está disponible, sino usar math básico
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    import math
    HAS_NUMPY = False
from functools import lru_cache
from loguru import logger


@lru_cache(maxsize=2048)
def normalizar_texto(texto: str) -> str:
    """
    Normaliza texto para comparación con caché LRU.
    
    Elimina acentos, convierte a minúsculas, remueve puntuación extra.
    
    Args:
        texto: Texto a normalizar
        
    Returns:
        Texto normalizado
    """
    # Convertir a minúsculas
    texto = texto.lower()
    
    # Eliminar acentos
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    
    # Reemplazar múltiples espacios por uno solo
    texto = re.sub(r'\s+', ' ', texto)
    
    # Eliminar puntuación al inicio y final
    texto = texto.strip(' .,;:!?¿¡"\'')
    
    return texto


def similitud_exacta(texto1: str, texto2: str) -> float:
    """
    Calcula similitud exacta entre dos textos.
    
    Args:
        texto1: Primer texto
        texto2: Segundo texto
        
    Returns:
        1.0 si son idénticos, 0.0 si no
    """
    return 1.0 if normalizar_texto(texto1) == normalizar_texto(texto2) else 0.0


def similitud_difusa(texto1: str, texto2: str) -> float:
    """
    Calcula similitud difusa usando SequenceMatcher.
    
    Args:
        texto1: Primer texto
        texto2: Segundo texto
        
    Returns:
        Score de similitud entre 0 y 1
    """
    texto1_norm = normalizar_texto(texto1)
    texto2_norm = normalizar_texto(texto2)
    
    return difflib.SequenceMatcher(None, texto1_norm, texto2_norm).ratio()


def similitud_jaccard(texto1: str, texto2: str, usar_palabras: bool = True) -> float:
    """
    Calcula el coeficiente de Jaccard entre dos textos.
    
    Args:
        texto1: Primer texto
        texto2: Segundo texto
        usar_palabras: Si True usa palabras, si False usa caracteres
        
    Returns:
        Score de similitud entre 0 y 1
    """
    texto1_norm = normalizar_texto(texto1)
    texto2_norm = normalizar_texto(texto2)
    
    if usar_palabras:
        # Dividir en palabras
        set1 = set(texto1_norm.split())
        set2 = set(texto2_norm.split())
    else:
        # Usar caracteres
        set1 = set(texto1_norm)
        set2 = set(texto2_norm)
    
    # Evitar división por cero
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0
    
    interseccion = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    return interseccion / union


def similitud_coseno_palabras(texto1: str, texto2: str) -> float:
    """
    Calcula similitud del coseno basada en frecuencia de palabras.
    
    Args:
        texto1: Primer texto
        texto2: Segundo texto
        
    Returns:
        Score de similitud entre 0 y 1
    """
    texto1_norm = normalizar_texto(texto1)
    texto2_norm = normalizar_texto(texto2)
    
    # Tokenizar
    palabras1 = texto1_norm.split()
    palabras2 = texto2_norm.split()
    
    # Contar frecuencias
    freq1 = Counter(palabras1)
    freq2 = Counter(palabras2)
    
    # Vocabulario único
    vocabulario = set(freq1.keys()).union(set(freq2.keys()))
    
    # Vectores de frecuencia
    vec1 = [freq1.get(palabra, 0) for palabra in vocabulario]
    vec2 = [freq2.get(palabra, 0) for palabra in vocabulario]
    
    # Producto punto
    producto_punto = sum(a * b for a, b in zip(vec1, vec2))
    
    # Magnitudes
    mag1 = sum(a * a for a in vec1) ** 0.5
    mag2 = sum(b * b for b in vec2) ** 0.5
    
    # Evitar división por cero
    if mag1 == 0 or mag2 == 0:
        return 0.0
    
    return producto_punto / (mag1 * mag2)


def detectar_subsecuencia(texto_corto: str, texto_largo: str) -> bool:
    """
    Detecta si un texto es subsecuencia del otro.
    
    Útil para detectar cuando un elemento es versión resumida de otro.
    
    Args:
        texto_corto: Texto más corto
        texto_largo: Texto más largo
        
    Returns:
        True si texto_corto es subsecuencia de texto_largo
    """
    corto_norm = normalizar_texto(texto_corto)
    largo_norm = normalizar_texto(texto_largo)
    
    # Si el corto es muy pequeño, no considerar
    if len(corto_norm) < 10:
        return False
    
    # Buscar si el texto corto está contenido
    return corto_norm in largo_norm


def similitud_nombres_propios(nombre1: str, nombre2: str) -> float:
    """
    Calcula similitud especializada para nombres propios.
    
    Considera iniciales, apellidos, orden de palabras.
    
    Args:
        nombre1: Primer nombre
        nombre2: Segundo nombre
        
    Returns:
        Score de similitud entre 0 y 1
    """
    # Normalizar pero mantener capitalización para detectar iniciales
    nombre1_parts = nombre1.strip().split()
    nombre2_parts = nombre2.strip().split()
    
    # Caso exacto
    if nombre1.lower() == nombre2.lower():
        return 1.0
    
    # Verificar si uno contiene al otro
    if nombre1.lower() in nombre2.lower() or nombre2.lower() in nombre1.lower():
        return 0.9
    
    # Comparar partes (palabras)
    set1 = set(p.lower() for p in nombre1_parts)
    set2 = set(p.lower() for p in nombre2_parts)
    
    # Intersección de partes
    comunes = len(set1.intersection(set2))
    total = len(set1.union(set2))
    
    if total == 0:
        return 0.0
    
    base_score = comunes / total
    
    # Bonus si comparten el primer o último elemento (nombre/apellido)
    bonus = 0
    if nombre1_parts and nombre2_parts:
        if nombre1_parts[0].lower() == nombre2_parts[0].lower():
            bonus += 0.1
        if nombre1_parts[-1].lower() == nombre2_parts[-1].lower():
            bonus += 0.1
    
    return min(base_score + bonus, 1.0)


def similitud_fechas(fecha1: Optional[str], fecha2: Optional[str]) -> float:
    """
    Calcula similitud entre fechas.
    
    Args:
        fecha1: Primera fecha (formato YYYY-MM-DD)
        fecha2: Segunda fecha
        
    Returns:
        Score de similitud entre 0 y 1
    """
    if not fecha1 or not fecha2:
        return 0.0
    
    if fecha1 == fecha2:
        return 1.0
    
    # Extraer componentes
    try:
        partes1 = fecha1.split('-')
        partes2 = fecha2.split('-')
        
        # Mismo año
        if len(partes1) >= 1 and len(partes2) >= 1:
            if partes1[0] == partes2[0]:
                # Mismo año y mes
                if len(partes1) >= 2 and len(partes2) >= 2:
                    if partes1[1] == partes2[1]:
                        return 0.8  # Mismo mes
                return 0.5  # Mismo año
    except:
        pass
    
    return 0.0


def similitud_listas(lista1: List[str], lista2: List[str]) -> float:
    """
    Calcula similitud entre dos listas de strings.
    
    Args:
        lista1: Primera lista
        lista2: Segunda lista
        
    Returns:
        Score de similitud entre 0 y 1
    """
    if not lista1 and not lista2:
        return 1.0
    if not lista1 or not lista2:
        return 0.0
    
    # Normalizar elementos
    set1 = set(normalizar_texto(elem) for elem in lista1)
    set2 = set(normalizar_texto(elem) for elem in lista2)
    
    interseccion = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    return interseccion / union if union > 0 else 0.0


def calcular_similitud_compuesta(
    texto1: str,
    texto2: str,
    pesos: Optional[dict] = None
) -> float:
    """
    Calcula una similitud compuesta usando múltiples algoritmos.
    
    Args:
        texto1: Primer texto
        texto2: Segundo texto
        pesos: Diccionario con pesos para cada algoritmo
        
    Returns:
        Score de similitud ponderado entre 0 y 1
    """
    if pesos is None:
        pesos = {
            'exacta': 0.3,
            'difusa': 0.3,
            'jaccard': 0.2,
            'coseno': 0.2
        }
    
    # Calcular similitudes
    scores = {
        'exacta': similitud_exacta(texto1, texto2),
        'difusa': similitud_difusa(texto1, texto2),
        'jaccard': similitud_jaccard(texto1, texto2),
        'coseno': similitud_coseno_palabras(texto1, texto2)
    }
    
    # Ponderar
    score_final = sum(
        scores[algo] * peso 
        for algo, peso in pesos.items() 
        if algo in scores
    )
    
    return min(score_final, 1.0)


def encontrar_grupos_similares(
    elementos: List[str],
    umbral: float = 0.85,
    algoritmo: str = 'compuesta'
) -> List[List[int]]:
    """
    Encuentra grupos de elementos similares.
    
    Args:
        elementos: Lista de textos a agrupar
        umbral: Umbral de similitud para agrupar
        algoritmo: Algoritmo a usar ('exacta', 'difusa', 'jaccard', 'coseno', 'compuesta')
        
    Returns:
        Lista de grupos, donde cada grupo es una lista de índices
    """
    n = len(elementos)
    if n == 0:
        return []
    
    # Seleccionar función de similitud
    funciones = {
        'exacta': similitud_exacta,
        'difusa': similitud_difusa,
        'jaccard': similitud_jaccard,
        'coseno': similitud_coseno_palabras,
        'compuesta': calcular_similitud_compuesta
    }
    
    func_similitud = funciones.get(algoritmo, calcular_similitud_compuesta)
    
    # Matriz de similitud
    grupos = []
    asignados = set()
    
    for i in range(n):
        if i in asignados:
            continue
        
        # Nuevo grupo
        grupo_actual = [i]
        asignados.add(i)
        
        # Buscar elementos similares
        for j in range(i + 1, n):
            if j in asignados:
                continue
            
            similitud = func_similitud(elementos[i], elementos[j])
            if similitud >= umbral:
                grupo_actual.append(j)
                asignados.add(j)
        
        grupos.append(grupo_actual)
    
    return grupos


# Funciones auxiliares para debugging
def analizar_similitudes(texto1: str, texto2: str) -> dict:
    """
    Analiza similitudes entre dos textos usando todos los algoritmos.
    
    Útil para debugging y ajuste de umbrales.
    
    Args:
        texto1: Primer texto
        texto2: Segundo texto
        
    Returns:
        Diccionario con scores de cada algoritmo
    """
    return {
        'exacta': similitud_exacta(texto1, texto2),
        'difusa': similitud_difusa(texto1, texto2),
        'jaccard_palabras': similitud_jaccard(texto1, texto2, usar_palabras=True),
        'jaccard_chars': similitud_jaccard(texto1, texto2, usar_palabras=False),
        'coseno': similitud_coseno_palabras(texto1, texto2),
        'es_subsecuencia': detectar_subsecuencia(min(texto1, texto2, key=len), 
                                                 max(texto1, texto2, key=len)),
        'longitud_ratio': len(texto1) / len(texto2) if len(texto2) > 0 else 0
    }


# =====================================================================
# ALGORITMOS OPTIMIZADOS PARA PERFORMANCE
# =====================================================================

class OptimizedSimilarityProcessor:
    """
    Procesador optimizado de similitudes con técnicas avanzadas:
    - Vectorización con NumPy
    - Early termination
    - Índices invertidos
    - Batch processing
    """
    
    def __init__(self):
        self._inverted_index: Dict[str, Set[int]] = {}
        self._word_vectors: Dict[str, np.ndarray] = {}
        self._document_cache: Dict[str, np.ndarray] = {}
    
    def build_inverted_index(self, texts: List[str]) -> None:
        """
        Construye índice invertido para búsqueda rápida.
        
        Args:
            texts: Lista de textos para indexar
        """
        self._inverted_index.clear()
        
        for i, text in enumerate(texts):
            words = set(normalizar_texto(text).split())
            for word in words:
                if word not in self._inverted_index:
                    self._inverted_index[word] = set()
                self._inverted_index[word].add(i)
    
    def get_candidates_fast(self, query_text: str, min_threshold: float = 0.1) -> Set[int]:
        """
        Obtiene candidatos rápidamente usando índice invertido.
        
        Args:
            query_text: Texto de consulta
            min_threshold: Umbral mínimo para considerar candidato
            
        Returns:
            Set de índices candidatos
        """
        query_words = set(normalizar_texto(query_text).split())
        if not query_words:
            return set()
        
        # Encontrar documentos que comparten al menos una palabra
        candidates = set()
        for word in query_words:
            if word in self._inverted_index:
                candidates.update(self._inverted_index[word])
        
        return candidates
    
    @lru_cache(maxsize=1024)
    def text_to_vector(self, text: str) -> tuple:
        """
        Convierte texto a vector de características para comparación rápida.
        Retorna tuple para compatibilidad con LRU cache.
        """
        words = normalizar_texto(text).split()
        if not words:
            return tuple([0.0] * 100)  # Vector cero
        
        # Características simples pero efectivas
        features = []
        
        # Longitud normalizada
        features.append(min(len(text) / 1000.0, 1.0))
        
        # Distribución de longitud de palabras
        word_lengths = [len(w) for w in words]
        if HAS_NUMPY:
            features.append(np.mean(word_lengths) / 20.0)  # Promedio normalizado
            features.append(np.std(word_lengths) / 10.0)   # Std normalizado
        else:
            avg_len = sum(word_lengths) / len(word_lengths)
            var = sum((x - avg_len) ** 2 for x in word_lengths) / len(word_lengths)
            std_len = math.sqrt(var)
            features.append(avg_len / 20.0)
            features.append(std_len / 10.0)
        
        # Vocabulario único
        unique_ratio = len(set(words)) / len(words)
        features.append(unique_ratio)
        
        # Frecuencias de n-gramas más comunes (simplificado)
        bigrams = [words[i:i+2] for i in range(len(words)-1)]
        bigram_counter = Counter(' '.join(bg) for bg in bigrams)
        
        # Top 10 bigrams como features
        top_bigrams = bigram_counter.most_common(10)
        bigram_features = [count / len(bigrams) if bigrams else 0.0 
                          for _, count in top_bigrams]
        features.extend(bigram_features)
        
        # Rellenar hasta 100 features
        while len(features) < 100:
            features.append(0.0)
        
        return tuple(features[:100])
    
    def vectorized_similarity_batch(
        self, 
        texts: List[str], 
        query_text: str,
        threshold: float = 0.7
    ) -> List[Tuple[int, float]]:
        """
        Calcula similitudes en batch usando vectorización.
        
        Args:
            texts: Lista de textos a comparar
            query_text: Texto de consulta
            threshold: Umbral de similitud
            
        Returns:
            Lista de (índice, similitud) que superan el umbral
        """
        if not texts:
            return []
        
        # Obtener candidatos usando índice invertido
        candidates = self.get_candidates_fast(query_text, threshold * 0.5)
        if not candidates:
            return []
        
        # Vectorizar query
        query_vector = list(self.text_to_vector(query_text))
        
        # Vectorizar candidatos y calcular similitudes
        candidate_indices = []
        similarities = []
        
        for idx in candidates:
            if idx < len(texts):
                candidate_vector = list(self.text_to_vector(texts[idx]))
                
                # Calcular similitud coseno manualmente
                if HAS_NUMPY:
                    query_array = np.array(query_vector)
                    candidate_array = np.array(candidate_vector)
                    
                    query_norm = np.linalg.norm(query_array)
                    candidate_norm = np.linalg.norm(candidate_array)
                    
                    if query_norm > 0 and candidate_norm > 0:
                        dot_product = np.dot(query_array, candidate_array)
                        similarity = dot_product / (query_norm * candidate_norm)
                    else:
                        similarity = 0.0
                else:
                    # Versión sin numpy
                    dot_product = sum(a * b for a, b in zip(query_vector, candidate_vector))
                    query_norm = math.sqrt(sum(a * a for a in query_vector))
                    candidate_norm = math.sqrt(sum(b * b for b in candidate_vector))
                    
                    if query_norm > 0 and candidate_norm > 0:
                        similarity = dot_product / (query_norm * candidate_norm)
                    else:
                        similarity = 0.0
                
                if similarity >= threshold:
                    candidate_indices.append(idx)
                    similarities.append(similarity)
        
        # Combinar y ordenar resultados
        results = list(zip(candidate_indices, similarities))
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results
    
    def consolidate_with_early_termination(
        self,
        elements: List[str],
        threshold: float = 0.85,
        max_comparisons: int = 10000
    ) -> List[List[int]]:
        """
        Consolida elementos con early termination para mejor performance.
        
        Args:
            elements: Lista de elementos a consolidar
            threshold: Umbral de similitud
            max_comparisons: Máximo número de comparaciones
            
        Returns:
            Lista de grupos de índices similares
        """
        if not elements:
            return []
        
        # Construir índice invertido
        self.build_inverted_index(elements)
        
        groups = []
        assigned = set()
        comparisons_made = 0
        
        for i, element in enumerate(elements):
            if i in assigned or comparisons_made >= max_comparisons:
                if comparisons_made >= max_comparisons:
                    logger.warning(f"Early termination: alcanzado límite de {max_comparisons} comparaciones")
                break
            
            # Obtener candidatos similares usando vectorización
            similar_candidates = self.vectorized_similarity_batch(
                elements, element, threshold
            )
            
            # Filtrar candidatos no asignados
            group = [i]
            assigned.add(i)
            
            for candidate_idx, similarity in similar_candidates:
                if candidate_idx != i and candidate_idx not in assigned:
                    group.append(candidate_idx)
                    assigned.add(candidate_idx)
                    comparisons_made += 1
                    
                    if comparisons_made >= max_comparisons:
                        break
            
            if len(group) > 1:
                groups.append(group)
            
            comparisons_made += len(similar_candidates)
        
        logger.debug(f"Consolidación completada: {len(groups)} grupos, {comparisons_made} comparaciones")
        return groups


# Instancia global del procesador optimizado
_similarity_processor = OptimizedSimilarityProcessor()


def consolidar_elementos_optimizado(
    elementos: List[str],
    umbral: float = 0.85,
    max_comparaciones: int = 10000
) -> List[List[int]]:
    """
    Función de conveniencia para consolidación optimizada.
    
    Args:
        elementos: Lista de elementos a consolidar
        umbral: Umbral de similitud
        max_comparaciones: Máximo número de comparaciones
        
    Returns:
        Lista de grupos de índices similares
    """
    return _similarity_processor.consolidate_with_early_termination(
        elementos, umbral, max_comparaciones
    )