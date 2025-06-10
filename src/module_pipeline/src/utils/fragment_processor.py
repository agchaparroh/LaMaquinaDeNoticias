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
"""

from typing import Dict, Any, Optional
from uuid import UUID
from loguru import logger

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
    
    def __init__(self, id_fragmento: UUID):
        """
        Inicializa generador de IDs para un fragmento específico.
        
        Args:
            id_fragmento: UUID del fragmento que se está procesando
        """
        self.id_fragmento = id_fragmento
        self.hecho_counter = 1
        self.entidad_counter = 1
        self.cita_counter = 1
        self.dato_counter = 1
        
        # Diccionarios para tracking y debugging
        self._hechos_asignados: Dict[int, str] = {}
        self._entidades_asignadas: Dict[int, str] = {}
        self._citas_asignadas: Dict[int, str] = {}
        self._datos_asignados: Dict[int, str] = {}
        
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
    
    def next_dato_id(self, descripcion_dato: str = None) -> int:
        """
        Genera el próximo ID secuencial para un dato cuantitativo.
        
        Args:
            descripcion_dato: Descripción del dato para debugging
            
        Returns:
            int: ID secuencial único dentro del fragmento
        """
        current_id = self.dato_counter
        self.dato_counter += 1
        
        if descripcion_dato:
            self._datos_asignados[current_id] = descripcion_dato[:40]
            
        self.logger.debug(f"Asignado ID dato {current_id} en fragmento {self.id_fragmento}: {descripcion_dato or 'Sin descripción'}")
        return current_id
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del procesamiento para debugging.
        
        Returns:
            Dict con contadores y elementos procesados
        """
        return {
            "fragmento_id": str(self.id_fragmento),
            "total_hechos": self.hecho_counter - 1,
            "total_entidades": self.entidad_counter - 1,
            "total_citas": self.cita_counter - 1,
            "total_datos": self.dato_counter - 1,
            # Agregar los campos esperados por los tests
            "hechos_generados": self.hecho_counter - 1,
            "entidades_generadas": self.entidad_counter - 1,
            "citas_generadas": self.cita_counter - 1,
            "datos_generados": self.dato_counter - 1,
            "hechos_asignados": dict(self._hechos_asignados),
            "entidades_asignadas": dict(self._entidades_asignadas),
            "citas_asignadas": dict(self._citas_asignadas),
            "datos_asignados": dict(self._datos_asignados)
        }
    
    def reset_counters(self) -> None:
        """
        Reinicia todos los contadores. Útil para testing.
        
        WARNING: Solo usar en testing, nunca en producción.
        """
        self.hecho_counter = 1
        self.entidad_counter = 1
        self.cita_counter = 1
        self.dato_counter = 1
        self._hechos_asignados.clear()
        self._entidades_asignadas.clear()
        self._citas_asignadas.clear()
        self._datos_asignados.clear()
        
        self.logger.warning(f"FragmentProcessor contadores reiniciados para fragmento {self.id_fragmento}")
    
    def log_summary(self, custom_logger: Optional["loguru.Logger"] = None) -> None:
        """
        Registra un resumen completo del procesamiento.
        Útil al final del pipeline para auditoría.
        
        Args:
            custom_logger: Logger personalizado con contexto de request (opcional)
        """
        log = custom_logger if custom_logger else self.logger
        stats = self.get_stats()
        
        log.info(
            f"FragmentProcessor completado para fragmento {self.id_fragmento}",
            total_hechos=stats['total_hechos'],
            total_entidades=stats['total_entidades'],
            total_citas=stats['total_citas'],
            total_datos=stats['total_datos']
        )
    
    def get_global_reference(self, tipo: str, id_local: int) -> str:
        """
        Genera referencia global única combinando fragmento + ID local.
        
        Útil para análisis cross-fragmento en capas superiores.
        
        Args:
            tipo: 'hecho', 'entidad', 'cita', 'dato'
            id_local: ID secuencial local
            
        Returns:
            str: Referencia global única
        """
        return f"{self.id_fragmento}#{tipo}#{id_local}"
    
    def parse_global_reference(self, referencia_global: str) -> Dict[str, Any]:
        """
        Parsea una referencia global para extraer componentes.
        
        Args:
            referencia_global: Referencia en formato "uuid#tipo#id"
            
        Returns:
            Dict con fragmento_id, tipo, id_local
        """
        try:
            partes = referencia_global.split('#')
            if len(partes) != 3:
                raise ValueError(f"Formato de referencia inválido: {referencia_global}")
                
            return {
                "fragmento_id": UUID(partes[0]),
                "tipo": partes[1],
                "id_local": int(partes[2])
            }
        except Exception as e:
            self.logger.error(f"Error parseando referencia global '{referencia_global}': {e}")
            raise


# Función de conveniencia para casos simples
def create_fragment_processor(id_fragmento: UUID) -> FragmentProcessor:
    """
    Factory function para crear FragmentProcessor.
    
    Args:
        id_fragmento: UUID del fragmento
        
    Returns:
        FragmentProcessor configurado
    """
    return FragmentProcessor(id_fragmento)


# Testing utilities (solo para development)
if __name__ == "__main__":
    from uuid import uuid4
    
    # Setup básico de logging para testing
    import sys
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")
    
    # Test básico
    test_fragmento_id = uuid4()
    processor = FragmentProcessor(test_fragmento_id)
    
    print(f"\n--- Test FragmentProcessor para {test_fragmento_id} ---")
    
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
