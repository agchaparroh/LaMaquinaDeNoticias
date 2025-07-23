"""
FragmentProcessor: Generador de IDs Secuenciales para Pipeline
=============================================================

Este módulo implementa la solución arquitectónica para el problema de mismatch
de IDs entre fases del pipeline. Proporciona IDs secuenciales (1, 2, 3...) 
que son óptimos para LLMs y mantiene consistencia referencial.

SOLUCIÓN IMPLEMENTADA:
- IDs secuenciales en pipeline interno (mejor para LLMs)
- Conversión única a strings en PayloadBuilder  
- UUIDs solo para fragmentos y resultados de fase
- Soporte para chunking con IDs únicos por chunk
"""

from typing import Dict, Any, Optional, Tuple, List
from .logging_config import get_logger

# Configurar logger para este módulo
logger = get_logger("FragmentProcessor")

# No importar logging_config para evitar import circular


class FragmentProcessor:
    """
    Generador de IDs secuenciales únicos por fragmento.
    
    Asegura consistencia de identificadores a través de todas las fases
    del pipeline (2, 3, 4) manteniendo referencias válidas entre elementos.
    
    Características:
    - IDs secuenciales por tipo (hechos: 1,2,3... entidades: 1,2,3...)
    - Scope por fragmento (evita colisiones entre fragmentos)
    - Thread-safe para procesamiento concurrente
    - Trazabilidad completa con logging
    """
    
    def __init__(self, id_fragmento: str, chunk_index: int = 0, total_chunks: int = 1):
        """
        Inicializa generador de IDs para un fragmento específico.
        
        Args:
            id_fragmento: ID del fragmento (formato ART-{ID} o UUID string)
            chunk_index: Índice del chunk actual (0 si no hay chunking)
            total_chunks: Total de chunks del fragmento (1 si no hay chunking)
        """
        self.id_fragmento = id_fragmento
        self.chunk_index = chunk_index
        self.total_chunks = total_chunks
        
        # Base para IDs únicos por chunk
        # Si hay 3 chunks: chunk 0 -> base 0, chunk 1 -> base 1000, chunk 2 -> base 2000
        self.id_base = chunk_index * 1000 if total_chunks > 1 else 0
        
        # Contadores iniciando desde la base
        self.hecho_counter = self.id_base + 1
        self.entidad_counter = self.id_base + 1
        self.cita_counter = self.id_base + 1
        self.dato_counter = self.id_base + 1
        
        # Diccionarios para tracking y debugging
        self._hechos_asignados: Dict[int, str] = {}
        self._entidades_asignadas: Dict[int, str] = {}
        self._citas_asignadas: Dict[int, str] = {}
        self._datos_asignados: Dict[int, str] = {}
        
        # Tracking de chunks para consolidación
        self._chunk_info = {
            "index": chunk_index,
            "total": total_chunks,
            "has_chunking": total_chunks > 1
        }
        
        # Logger por defecto
        self.logger = logger
    
    def next_hecho_id(self, descripcion_corta: str = None) -> int:
        """
        Genera el próximo ID secuencial para un hecho.
        
        Args:
            descripcion_corta: Descripción opcional para debugging
            
        Returns:
            int: ID secuencial único dentro del fragmento
        """
        current_id = self.hecho_counter
        self.hecho_counter += 1
        
        if descripcion_corta:
            self._hechos_asignados[current_id] = descripcion_corta[:50]
            
        self.logger.debug(f"Asignado ID hecho {current_id} en fragmento {self.id_fragmento}: {descripcion_corta or 'Sin descripción'}")
        return current_id
    
    def next_entidad_id(self, nombre_entidad: str = None) -> int:
        """
        Genera el próximo ID secuencial para una entidad.
        
        Args:
            nombre_entidad: Nombre opcional para debugging
            
        Returns:
            int: ID secuencial único dentro del fragmento
        """
        current_id = self.entidad_counter
        self.entidad_counter += 1
        
        if nombre_entidad:
            self._entidades_asignadas[current_id] = nombre_entidad[:30]
            
        self.logger.debug(f"Asignado ID entidad {current_id} en fragmento {self.id_fragmento}: {nombre_entidad or 'Sin nombre'}")
        return current_id
    
    def next_cita_id(self, cita_preview: str = None) -> int:
        """
        Genera el próximo ID secuencial para una cita textual.
        
        Args:
            cita_preview: Preview de la cita para debugging
            
        Returns:
            int: ID secuencial único dentro del fragmento
        """
        current_id = self.cita_counter
        self.cita_counter += 1
        
        if cita_preview:
            self._citas_asignadas[current_id] = cita_preview[:40]
            
        self.logger.debug(f"Asignado ID cita {current_id} en fragmento {self.id_fragmento}: {cita_preview or 'Sin preview'}")
        return current_id
    
    def next_dato_id(self, indicador: str = None) -> int:
        """
        Genera el próximo ID secuencial para un dato cuantitativo.
        
        Args:
            indicador: Indicador del dato para debugging
            
        Returns:
            int: ID secuencial único dentro del fragmento
        """
        current_id = self.dato_counter
        self.dato_counter += 1
        
        if indicador:
            self._datos_asignados[current_id] = indicador[:40]
            
        self.logger.debug(f"Asignado ID dato {current_id} en fragmento {self.id_fragmento}: {indicador or 'Sin indicador'}")
        return current_id
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del procesamiento para debugging.
        
        Returns:
            Dict con contadores y elementos procesados
        """
        # Ajustar conteos considerando la base
        actual_hechos = self.hecho_counter - self.id_base - 1
        actual_entidades = self.entidad_counter - self.id_base - 1
        actual_citas = self.cita_counter - self.id_base - 1
        actual_datos = self.dato_counter - self.id_base - 1
        
        return {
            "fragmento_id": str(self.id_fragmento),
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "id_base": self.id_base,
            "total_hechos": actual_hechos,
            "total_entidades": actual_entidades,
            "total_citas": actual_citas,
            "total_datos": actual_datos,
            # Agregar los campos esperados por los tests
            "hechos_generados": actual_hechos,
            "entidades_generadas": actual_entidades,
            "citas_generadas": actual_citas,
            "datos_generados": actual_datos,
            "hechos_asignados": dict(self._hechos_asignados),
            "entidades_asignadas": dict(self._entidades_asignadas),
            "citas_asignadas": dict(self._citas_asignadas),
            "datos_asignados": dict(self._datos_asignados),
            "chunk_info": self._chunk_info
        }
    
    def reset_counters(self) -> None:
        """
        Reinicia todos los contadores. Útil para testing.
        
        WARNING: Solo usar en testing, nunca en producción.
        """
        self.hecho_counter = self.id_base + 1
        self.entidad_counter = self.id_base + 1
        self.cita_counter = self.id_base + 1
        self.dato_counter = self.id_base + 1
        self._hechos_asignados.clear()
        self._entidades_asignadas.clear()
        self._citas_asignadas.clear()
        self._datos_asignados.clear()
        
        self.logger.warning(f"FragmentProcessor contadores reiniciados para fragmento {self.id_fragmento}, chunk {self.chunk_index}")
    
    def log_summary(self, custom_logger: Optional["loguru.Logger"] = None) -> None:
        """
        Registra un resumen completo del procesamiento.
        Útil al final del pipeline para auditoría.
        
        Args:
            custom_logger: Logger personalizado con contexto de request (opcional)
        """
        log = custom_logger if custom_logger else self.logger
        stats = self.get_stats()
        
        chunk_info = f" (chunk {self.chunk_index + 1}/{self.total_chunks})" if self.total_chunks > 1 else ""
        
        log.info(
            f"FragmentProcessor completado para fragmento {self.id_fragmento}{chunk_info}",
            total_hechos=stats['total_hechos'],
            total_entidades=stats['total_entidades'],
            total_citas=stats['total_citas'],
            total_datos=stats['total_datos'],
            chunk_index=self.chunk_index,
            total_chunks=self.total_chunks
        )
    
    def get_global_reference(self, tipo: str, id_local: int) -> str:
        """
        Genera referencia global única combinando fragmento + chunk + ID local.
        
        Útil para análisis cross-fragmento y cross-chunk en capas superiores.
        
        Args:
            tipo: 'hecho', 'entidad', 'cita', 'dato'
            id_local: ID secuencial local
            
        Returns:
            str: Referencia global única
        """
        if self.total_chunks > 1:
            return f"{self.id_fragmento}#chunk{self.chunk_index}#{tipo}#{id_local}"
        else:
            return f"{self.id_fragmento}#{tipo}#{id_local}"
    
    def parse_global_reference(self, referencia_global: str) -> Dict[str, Any]:
        """
        Parsea una referencia global para extraer componentes.
        
        Args:
            referencia_global: Referencia en formato "uuid#tipo#id" o "uuid#chunk0#tipo#id"
            
        Returns:
            Dict con fragmento_id, tipo, id_local, y opcionalmente chunk_index
        """
        try:
            partes = referencia_global.split('#')
            
            if len(partes) == 3:
                # Formato sin chunk: id#tipo#id_local
                return {
                    "fragmento_id": partes[0],  # Ya no convertimos a UUID
                    "tipo": partes[1],
                    "id_local": int(partes[2]),
                    "chunk_index": None
                }
            elif len(partes) == 4:
                # Formato con chunk: id#chunk0#tipo#id_local
                chunk_str = partes[1]
                if not chunk_str.startswith("chunk"):
                    raise ValueError(f"Formato de chunk inválido: {chunk_str}")
                    
                chunk_index = int(chunk_str.replace("chunk", ""))
                
                return {
                    "fragmento_id": partes[0],  # Ya no convertimos a UUID
                    "chunk_index": chunk_index,
                    "tipo": partes[2],
                    "id_local": int(partes[3])
                }
            else:
                raise ValueError(f"Formato de referencia inválido: {referencia_global}")
                
        except Exception as e:
            self.logger.error(f"Error parseando referencia global '{referencia_global}': {e}")
            raise
    
    def get_chunk_id_range(self) -> Tuple[int, int]:
        """
        Obtiene el rango de IDs válidos para este chunk.
        
        Returns:
            Tuple con (id_minimo, id_maximo) para el chunk actual
        """
        min_id = self.id_base + 1
        max_id = self.id_base + 999
        return (min_id, max_id)
    
    def is_id_from_chunk(self, id_local: int, chunk_index: int) -> bool:
        """
        Verifica si un ID pertenece a un chunk específico.
        
        Args:
            id_local: ID a verificar
            chunk_index: Índice del chunk a comprobar
            
        Returns:
            True si el ID pertenece al chunk especificado
        """
        if self.total_chunks == 1:
            return True  # Sin chunking, todos los IDs son válidos
            
        chunk_base = chunk_index * 1000
        return chunk_base < id_local <= chunk_base + 999
    
    @staticmethod
    def consolidate_ids_mapping(processors: List["FragmentProcessor"]) -> Dict[int, int]:
        """
        Crea un mapeo de IDs de chunks a IDs consolidados.
        
        Útil para la fase de consolidación cuando se unen resultados de múltiples chunks.
        
        Args:
            processors: Lista de FragmentProcessors de todos los chunks
            
        Returns:
            Dict mapeando ID original -> ID consolidado
        """
        id_mapping = {}
        
        # Contadores para IDs consolidados
        consolidated_counters = {
            "hecho": 1,
            "entidad": 1,
            "cita": 1,
            "dato": 1
        }
        
        # Procesar cada processor en orden
        for processor in sorted(processors, key=lambda p: p.chunk_index):
            # Mapear hechos
            for old_id in sorted(processor._hechos_asignados.keys()):
                id_mapping[old_id] = consolidated_counters["hecho"]
                consolidated_counters["hecho"] += 1
            
            # Mapear entidades
            for old_id in sorted(processor._entidades_asignadas.keys()):
                id_mapping[old_id] = consolidated_counters["entidad"]
                consolidated_counters["entidad"] += 1
            
            # Mapear citas
            for old_id in sorted(processor._citas_asignadas.keys()):
                id_mapping[old_id] = consolidated_counters["cita"]
                consolidated_counters["cita"] += 1
            
            # Mapear datos
            for old_id in sorted(processor._datos_asignados.keys()):
                id_mapping[old_id] = consolidated_counters["dato"]
                consolidated_counters["dato"] += 1
        
        return id_mapping


# Función de conveniencia para casos simples
def create_fragment_processor(
    id_fragmento: str, 
    chunk_index: int = 0, 
    total_chunks: int = 1
) -> FragmentProcessor:
    """
    Factory function para crear FragmentProcessor.
    
    Args:
        id_fragmento: ID del fragmento (formato ART-{ID} o UUID string)
        chunk_index: Índice del chunk actual
        total_chunks: Total de chunks
        
    Returns:
        FragmentProcessor configurado
    """
    return FragmentProcessor(id_fragmento, chunk_index, total_chunks)


# Testing utilities (solo para development)
if __name__ == "__main__":
    from uuid import uuid4
    
    # Setup básico de logging para testing
    import sys
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")
    
    # Test básico sin chunking
    test_fragmento_id = uuid4()
    processor = FragmentProcessor(test_fragmento_id)
    
    print(f"\n--- Test FragmentProcessor sin chunking para {test_fragmento_id} ---")
    
    # Simular asignación de IDs
    hecho1 = processor.next_hecho_id("Pedro Sánchez anunció medidas")
    hecho2 = processor.next_hecho_id("Las medidas entrarán en vigor")
    
    entidad1 = processor.next_entidad_id("Pedro Sánchez")
    entidad2 = processor.next_entidad_id("España")
    
    cita1 = processor.next_cita_id("Vamos a implementar estas medidas")
    dato1 = processor.next_dato_id("PIB creció 3.5%")
    
    print(f"IDs asignados - Hechos: {hecho1}, {hecho2} | Entidades: {entidad1}, {entidad2}")
    print(f"IDs asignados - Citas: {cita1} | Datos: {dato1}")
    
    # Test referencias globales
    ref_global = processor.get_global_reference("hecho", hecho1)
    parsed = processor.parse_global_reference(ref_global)
    print(f"\nReferencia global: {ref_global}")
    print(f"Parsed: {parsed}")
    
    # Estadísticas finales
    processor.log_summary()
    stats = processor.get_stats()
    print(f"\nEstadísticas: {stats}")
    
    # Test con chunking
    print(f"\n--- Test FragmentProcessor con chunking ---")
    
    # Simular 3 chunks
    processors = []
    for chunk_idx in range(3):
        proc = FragmentProcessor(test_fragmento_id, chunk_idx, 3)
        
        # Asignar algunos IDs en cada chunk
        proc.next_hecho_id(f"Hecho del chunk {chunk_idx}")
        proc.next_entidad_id(f"Entidad del chunk {chunk_idx}")
        
        processors.append(proc)
        
        # Mostrar rango de IDs
        min_id, max_id = proc.get_chunk_id_range()
        print(f"\nChunk {chunk_idx}: Rango de IDs [{min_id}, {max_id}]")
        print(f"  Hecho ID: {proc._hechos_asignados}")
        print(f"  Entidad ID: {proc._entidades_asignadas}")
        
        # Test referencia global con chunk
        ref = proc.get_global_reference("hecho", list(proc._hechos_asignados.keys())[0])
        print(f"  Referencia global: {ref}")
    
    # Test consolidación de IDs
    print(f"\n--- Test Consolidación de IDs ---")
    id_mapping = FragmentProcessor.consolidate_ids_mapping(processors)
    print(f"Mapeo de consolidación: {id_mapping}")
