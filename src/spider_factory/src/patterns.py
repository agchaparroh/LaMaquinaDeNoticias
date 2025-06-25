"""
PatternStorage - Sistema de almacenamiento y gestión de patrones en Redis

Gestiona los patrones de extracción descubiertos para cada medio/sección,
permitiendo reutilización y mejora continua del sistema.
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
import uuid

from pydantic import BaseModel, Field, validator
import redis

from .config import get_redis_client, RedisKeys, config
from .analyzer import AnalysisStrategy, SiteSelectors


logger = logging.getLogger(__name__)


class PatternStatus(str, Enum):
    """Estado de un patrón"""
    ACTIVE = "active"         # En uso activo
    TESTING = "testing"       # En periodo de prueba
    DEPRECATED = "deprecated" # Obsoleto pero no eliminado
    FAILED = "failed"        # Marcado como fallido


class PatternMetadata(BaseModel):
    """Metadatos adicionales del patrón"""
    area_geografica: Optional[str] = None
    tipo_medio: Optional[str] = None  # diario, revista, agencia
    comentarios: Optional[str] = None
    frecuencia_actualizacion: Optional[str] = None
    ultimo_error: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class Pattern(BaseModel):
    """Modelo completo de un patrón"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    domain: str
    section: str
    strategy: AnalysisStrategy
    selectors: Optional[SiteSelectors] = None
    confidence: float = Field(ge=0.0, le=1.0)
    needs_javascript: bool = False
    status: PatternStatus = PatternStatus.TESTING
    
    # Estadísticas
    usage_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    success_rate: float = 0.0
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    
    # Metadata
    metadata: PatternMetadata = Field(default_factory=PatternMetadata)
    
    # Versioning
    version: int = 1
    previous_versions: List[Dict] = Field(default_factory=list)
    
    @validator('success_rate', always=True)
    def calculate_success_rate(cls, v, values):
        total = values.get('success_count', 0) + values.get('failure_count', 0)
        if total > 0:
            return round(values.get('success_count', 0) / total, 3)
        return 0.0
    
    @validator('confidence')
    def validate_confidence(cls, v):
        return round(v, 2)
    
    def to_redis_hash(self) -> Dict[str, str]:
        """Convierte el patrón a formato hash de Redis"""
        data = {
            "id": self.id,
            "domain": self.domain,
            "section": self.section,
            "strategy": self.strategy.value,
            "confidence": str(self.confidence),
            "needs_javascript": str(self.needs_javascript).lower(),
            "status": self.status.value,
            "usage_count": str(self.usage_count),
            "success_count": str(self.success_count),
            "failure_count": str(self.failure_count),
            "success_rate": str(self.success_rate),
            "created_at": self.created_at.isoformat(),
            "version": str(self.version)
        }
        
        if self.selectors:
            data["selectors"] = json.dumps(self.selectors.dict())
        
        if self.last_used:
            data["last_used"] = self.last_used.isoformat()
        
        if self.last_updated:
            data["last_updated"] = self.last_updated.isoformat()
        
        if self.metadata:
            data["metadata"] = json.dumps(self.metadata.dict())
        
        if self.previous_versions:
            data["previous_versions"] = json.dumps(self.previous_versions)
        
        return data
    
    @classmethod
    def from_redis_hash(cls, data: Dict[str, str]) -> 'Pattern':
        """Crea un Pattern desde datos de Redis"""
        # Procesar campos especiales
        if 'selectors' in data and data['selectors']:
            data['selectors'] = SiteSelectors(**json.loads(data['selectors']))
        
        if 'metadata' in data and data['metadata']:
            data['metadata'] = PatternMetadata(**json.loads(data['metadata']))
        
        if 'previous_versions' in data and data['previous_versions']:
            data['previous_versions'] = json.loads(data['previous_versions'])
        
        # Convertir tipos
        data['confidence'] = float(data.get('confidence', 0.7))
        data['needs_javascript'] = data.get('needs_javascript', '').lower() == 'true'
        data['usage_count'] = int(data.get('usage_count', 0))
        data['success_count'] = int(data.get('success_count', 0))
        data['failure_count'] = int(data.get('failure_count', 0))
        data['success_rate'] = float(data.get('success_rate', 0.0))
        data['version'] = int(data.get('version', 1))
        
        # Parsear fechas
        if 'created_at' in data:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'last_used' in data:
            data['last_used'] = datetime.fromisoformat(data['last_used'])
        if 'last_updated' in data:
            data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        
        return cls(**data)


class PatternStorage:
    """
    Gestiona el almacenamiento y recuperación de patrones en Redis
    Usa estructuras de datos optimizadas para búsquedas eficientes
    """
    
    def __init__(self):
        self.redis = get_redis_client()
        self.config = config
    
    def save_pattern(self, pattern: Pattern) -> bool:
        """
        Guarda o actualiza un patrón en Redis
        """
        try:
            # Clave principal del patrón
            pattern_key = RedisKeys.format_key(
                RedisKeys.PATTERN_KEY,
                domain=pattern.domain,
                section=pattern.section
            )
            
            # Si existe, guardar versión anterior
            existing = self.get_pattern(pattern.domain, pattern.section)
            if existing:
                pattern.version = existing.version + 1
                pattern.previous_versions = existing.previous_versions[-4:]  # Mantener últimas 5 versiones
                pattern.previous_versions.append({
                    "version": existing.version,
                    "confidence": existing.confidence,
                    "updated_at": datetime.now().isoformat(),
                    "selectors": existing.selectors.dict() if existing.selectors else None
                })
            
            pattern.last_updated = datetime.now()
            
            # Guardar en hash
            self.redis.hset(pattern_key, mapping=pattern.to_redis_hash())
            
            # Actualizar índices
            self._update_indices(pattern)
            
            # Actualizar estadísticas globales
            self.redis.incr(RedisKeys.STATS_PATTERN_COUNT)
            
            logger.info(f"Patrón guardado: {pattern.domain}/{pattern.section} v{pattern.version}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando patrón: {e}")
            return False
    
    def get_pattern(self, domain: str, section: str) -> Optional[Pattern]:
        """
        Obtiene un patrón específico
        """
        pattern_key = RedisKeys.format_key(
            RedisKeys.PATTERN_KEY,
            domain=domain,
            section=section
        )
        
        data = self.redis.hgetall(pattern_key)
        if data:
            try:
                return Pattern.from_redis_hash(data)
            except Exception as e:
                logger.error(f"Error deserializando patrón {domain}/{section}: {e}")
        
        return None
    
    def get_patterns_by_domain(self, domain: str) -> List[Pattern]:
        """
        Obtiene todos los patrones de un dominio
        """
        patterns = []
        
        # Obtener secciones del dominio
        domain_key = RedisKeys.format_key(
            RedisKeys.PATTERNS_BY_DOMAIN,
            domain=domain
        )
        sections = self.redis.smembers(domain_key)
        
        for section in sections:
            pattern = self.get_pattern(domain, section)
            if pattern:
                patterns.append(pattern)
        
        return patterns
    
    def search_patterns(
        self, 
        status: Optional[PatternStatus] = None,
        min_confidence: Optional[float] = None,
        strategy: Optional[AnalysisStrategy] = None,
        limit: int = 100
    ) -> List[Pattern]:
        """
        Busca patrones según criterios
        """
        patterns = []
        
        # Obtener todos los patrones (optimización futura: usar índices)
        pattern_keys = self.redis.keys(f"{RedisKeys.PATTERNS_PREFIX}:*:*")
        
        for key in pattern_keys[:limit * 2]:  # Procesar más para aplicar filtros
            # Saltar claves que no son patrones individuales
            if any(x in key for x in ['domain:', 'confidence:', 'status:']):
                continue
            
            data = self.redis.hgetall(key)
            if data:
                try:
                    pattern = Pattern.from_redis_hash(data)
                    
                    # Aplicar filtros
                    if status and pattern.status != status:
                        continue
                    if min_confidence and pattern.confidence < min_confidence:
                        continue
                    if strategy and pattern.strategy != strategy:
                        continue
                    
                    patterns.append(pattern)
                    
                    if len(patterns) >= limit:
                        break
                        
                except Exception as e:
                    logger.error(f"Error procesando patrón {key}: {e}")
        
        # Ordenar por success_rate descendente
        patterns.sort(key=lambda p: p.success_rate, reverse=True)
        
        return patterns
    
    def update_pattern_stats(
        self, 
        domain: str, 
        section: str, 
        success: bool,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Actualiza estadísticas de uso de un patrón
        """
        pattern = self.get_pattern(domain, section)
        if not pattern:
            return False
        
        try:
            pattern_key = RedisKeys.format_key(
                RedisKeys.PATTERN_KEY,
                domain=domain,
                section=section
            )
            
            # Actualizar contadores
            pattern.usage_count += 1
            pattern.last_used = datetime.now()
            
            if success:
                pattern.success_count += 1
            else:
                pattern.failure_count += 1
                if error_message:
                    pattern.metadata.ultimo_error = error_message
            
            # Recalcular success_rate
            total = pattern.success_count + pattern.failure_count
            pattern.success_rate = round(pattern.success_count / total, 3) if total > 0 else 0.0
            
            # Actualizar confianza basada en éxito
            if pattern.usage_count > 5:  # Después de 5 usos
                if pattern.success_rate >= 0.9:
                    pattern.confidence = min(0.95, pattern.confidence + 0.05)
                elif pattern.success_rate < 0.5:
                    pattern.confidence = max(0.3, pattern.confidence - 0.1)
                    if pattern.success_rate < 0.3:
                        pattern.status = PatternStatus.FAILED
            
            # Guardar actualizaciones
            self.redis.hset(pattern_key, mapping={
                "usage_count": str(pattern.usage_count),
                "success_count": str(pattern.success_count),
                "failure_count": str(pattern.failure_count),
                "success_rate": str(pattern.success_rate),
                "confidence": str(pattern.confidence),
                "last_used": pattern.last_used.isoformat(),
                "status": pattern.status.value
            })
            
            if error_message:
                self.redis.hset(pattern_key, "metadata", json.dumps(pattern.metadata.dict()))
            
            # Actualizar ranking global
            usage_key = RedisKeys.STATS_PATTERN_USAGE
            self.redis.zadd(usage_key, {f"{domain}:{section}": pattern.usage_count})
            
            logger.info(f"Stats actualizadas para {domain}/{section}: éxito={success}, rate={pattern.success_rate}")
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando stats: {e}")
            return False
    
    def deprecate_pattern(self, domain: str, section: str, reason: str = "") -> bool:
        """
        Marca un patrón como deprecado
        """
        pattern = self.get_pattern(domain, section)
        if not pattern:
            return False
        
        pattern_key = RedisKeys.format_key(
            RedisKeys.PATTERN_KEY,
            domain=domain,
            section=section
        )
        
        self.redis.hset(pattern_key, mapping={
            "status": PatternStatus.DEPRECATED.value,
            "last_updated": datetime.now().isoformat(),
            "metadata": json.dumps({
                **pattern.metadata.dict(),
                "deprecation_reason": reason
            })
        })
        
        logger.info(f"Patrón deprecado: {domain}/{section} - {reason}")
        return True
    
    def get_top_patterns(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Obtiene los patrones más usados
        """
        usage_key = RedisKeys.STATS_PATTERN_USAGE
        top_patterns = self.redis.zrevrange(usage_key, 0, limit - 1, withscores=True)
        
        return [(pattern, int(score)) for pattern, score in top_patterns]
    
    def get_pattern_history(self, domain: str, section: str) -> List[Dict]:
        """
        Obtiene el historial de versiones de un patrón
        """
        pattern = self.get_pattern(domain, section)
        if not pattern:
            return []
        
        history = pattern.previous_versions.copy()
        
        # Agregar versión actual
        history.append({
            "version": pattern.version,
            "confidence": pattern.confidence,
            "created_at": pattern.created_at.isoformat(),
            "is_current": True,
            "selectors": pattern.selectors.dict() if pattern.selectors else None
        })
        
        return history
    
    def cleanup_failed_patterns(self, threshold: float = 0.3) -> int:
        """
        Limpia patrones con baja tasa de éxito
        """
        cleaned = 0
        patterns = self.search_patterns()
        
        for pattern in patterns:
            if pattern.usage_count > 10 and pattern.success_rate < threshold:
                if self.deprecate_pattern(
                    pattern.domain, 
                    pattern.section, 
                    f"Baja tasa de éxito: {pattern.success_rate}"
                ):
                    cleaned += 1
        
        logger.info(f"Limpieza completada: {cleaned} patrones deprecados")
        return cleaned
    
    def export_patterns(self, status: Optional[PatternStatus] = None) -> Dict:
        """
        Exporta patrones para backup o análisis
        """
        patterns = self.search_patterns(status=status or PatternStatus.ACTIVE)
        
        return {
            "export_date": datetime.now().isoformat(),
            "total_patterns": len(patterns),
            "patterns": [pattern.dict() for pattern in patterns]
        }
    
    def import_patterns(self, data: Dict) -> Tuple[int, int]:
        """
        Importa patrones desde un export
        """
        imported = 0
        failed = 0
        
        for pattern_data in data.get('patterns', []):
            try:
                # Convertir fechas de string a datetime
                for date_field in ['created_at', 'last_used', 'last_updated']:
                    if date_field in pattern_data and pattern_data[date_field]:
                        pattern_data[date_field] = datetime.fromisoformat(pattern_data[date_field])
                
                pattern = Pattern(**pattern_data)
                if self.save_pattern(pattern):
                    imported += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Error importando patrón: {e}")
                failed += 1
        
        logger.info(f"Importación completada: {imported} exitosos, {failed} fallidos")
        return imported, failed
    
    def _update_indices(self, pattern: Pattern):
        """
        Actualiza índices secundarios para búsquedas eficientes
        """
        # Índice por dominio
        domain_key = RedisKeys.format_key(
            RedisKeys.PATTERNS_BY_DOMAIN,
            domain=pattern.domain
        )
        self.redis.sadd(domain_key, pattern.section)
        
        # Índice por status (futuro)
        # status_key = f"{RedisKeys.PATTERNS_PREFIX}:status:{pattern.status.value}"
        # self.redis.sadd(status_key, f"{pattern.domain}:{pattern.section}")
        
        # Índice por estrategia (futuro)
        # strategy_key = f"{RedisKeys.PATTERNS_PREFIX}:strategy:{pattern.strategy.value}"
        # self.redis.sadd(strategy_key, f"{pattern.domain}:{pattern.section}")


# Función auxiliar para testing
def test_pattern_storage():
    """Test básico del sistema de patrones"""
    storage = PatternStorage()
    
    # Crear patrón de prueba
    test_pattern = Pattern(
        domain="example.com",
        section="news",
        strategy=AnalysisStrategy.SCRAPING,
        confidence=0.85,
        selectors=SiteSelectors(
            title="h1.title",
            content="div.content",
            date="time.published"
        ),
        metadata=PatternMetadata(
            area_geografica="ESPAÑA",
            tipo_medio="diario",
            comentarios="Patrón de prueba"
        )
    )
    
    # Guardar
    print("Guardando patrón...")
    saved = storage.save_pattern(test_pattern)
    print(f"Guardado: {saved}")
    
    # Recuperar
    print("\nRecuperando patrón...")
    retrieved = storage.get_pattern("example.com", "news")
    if retrieved:
        print(f"Recuperado: {retrieved.domain}/{retrieved.section} v{retrieved.version}")
    
    # Actualizar stats
    print("\nActualizando estadísticas...")
    storage.update_pattern_stats("example.com", "news", success=True)
    storage.update_pattern_stats("example.com", "news", success=True)
    storage.update_pattern_stats("example.com", "news", success=False, error_message="Test error")
    
    # Ver stats actualizadas
    updated = storage.get_pattern("example.com", "news")
    if updated:
        print(f"Stats: usage={updated.usage_count}, success_rate={updated.success_rate}")
    
    # Top patterns
    print("\nTop patrones:")
    for pattern_id, count in storage.get_top_patterns(5):
        print(f"  {pattern_id}: {count} usos")
    
    print("\nTest completado!")


if __name__ == "__main__":
    test_pattern_storage()