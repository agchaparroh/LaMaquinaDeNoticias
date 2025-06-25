"""
Tests unitarios para PatternStorage
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch
import json

from src.patterns import PatternStorage, Pattern, PatternStatus
from src.analyzer import AnalysisStrategy, SiteSelectors


class TestPatternStorage:
    """Tests para el sistema de almacenamiento de patrones"""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock de Redis para tests"""
        return Mock()
    
    @pytest.fixture
    def pattern_storage(self, mock_redis):
        """Instancia de PatternStorage con Redis mockeado"""
        with patch('src.patterns.get_redis_client', return_value=mock_redis):
            return PatternStorage()
    
    @pytest.fixture
    def sample_pattern(self):
        """Patrón de ejemplo para tests"""
        return Pattern(
            domain="example.com",
            section="noticias",
            strategy=AnalysisStrategy.SCRAPING,
            selectors=SiteSelectors(
                title="h1.article-title",
                content="div.article-content",
                date="time.publish-date",
                author="span.author-name"
            ),
            confidence=0.85,
            needs_javascript=False
        )
    
    def test_save_pattern(self, pattern_storage, mock_redis, sample_pattern):
        """Test guardar un patrón nuevo"""
        # Configurar mocks
        mock_redis.hset.return_value = True
        mock_redis.sadd.return_value = 1
        mock_redis.set.return_value = True
        
        # Ejecutar
        saved_pattern = pattern_storage.save_pattern(sample_pattern)
        
        # Verificar
        assert saved_pattern.id == sample_pattern.id
        assert mock_redis.hset.called
        assert mock_redis.sadd.called
        
    def test_get_pattern_by_domain_section(self, pattern_storage, mock_redis):
        """Test obtener patrón por dominio y sección"""
        # Configurar mock
        pattern_data = {
            "id": "test-123",
            "domain": "example.com",
            "section": "noticias",
            "strategy": "scraping",
            "confidence": "0.85",
            "needs_javascript": "false",
            "status": "active",
            "usage_count": "10",
            "success_count": "9",
            "failure_count": "1",
            "success_rate": "0.9",
            "created_at": datetime.now().isoformat(),
            "version": "1"
        }
        mock_redis.smembers.return_value = {"test-123"}
        mock_redis.hgetall.return_value = pattern_data
        
        # Ejecutar
        patterns = pattern_storage.get_patterns_by_domain_section("example.com", "noticias")
        
        # Verificar
        assert len(patterns) == 1
        assert patterns[0].domain == "example.com"
        assert patterns[0].section == "noticias"
        
    def test_update_pattern_stats(self, pattern_storage, mock_redis, sample_pattern):
        """Test actualizar estadísticas de un patrón"""
        # Configurar mock
        mock_redis.hgetall.return_value = sample_pattern.to_redis_hash()
        mock_redis.hset.return_value = True
        
        # Ejecutar - éxito
        pattern_storage.update_pattern_stats(sample_pattern.id, success=True)
        
        # Verificar
        assert mock_redis.hincrby.called
        assert mock_redis.hset.called
        
    def test_search_patterns(self, pattern_storage, mock_redis):
        """Test búsqueda de patrones con filtros"""
        # Configurar mock
        pattern_ids = {"pattern-1", "pattern-2"}
        mock_redis.scan_iter.return_value = [f"pattern:{pid}" for pid in pattern_ids]
        
        pattern_data = {
            "id": "pattern-1",
            "domain": "news.com",
            "section": "politics",
            "strategy": "rss",
            "confidence": "0.9",
            "status": "active",
            "success_rate": "0.95",
            "created_at": datetime.now().isoformat(),
            "usage_count": "100",
            "success_count": "95",
            "failure_count": "5",
            "needs_javascript": "false",
            "version": "1"
        }
        mock_redis.hgetall.return_value = pattern_data
        
        # Ejecutar
        results = pattern_storage.search_patterns(
            min_confidence=0.8,
            status=PatternStatus.ACTIVE
        )
        
        # Verificar
        assert len(results) > 0
        assert all(p.confidence >= 0.8 for p in results)
        assert all(p.status == PatternStatus.ACTIVE for p in results)
        
    def test_get_popular_patterns(self, pattern_storage, mock_redis):
        """Test obtener patrones más populares"""
        # Configurar mock
        mock_redis.zrevrange.return_value = [
            ("pattern:popular-1", 150.0),
            ("pattern:popular-2", 100.0)
        ]
        
        pattern_data = {
            "id": "popular-1",
            "domain": "popular-news.com",
            "section": "home",
            "strategy": "scraping",
            "confidence": "0.92",
            "status": "active",
            "usage_count": "150",
            "success_count": "140",
            "failure_count": "10",
            "success_rate": "0.933",
            "created_at": datetime.now().isoformat(),
            "needs_javascript": "true",
            "version": "2"
        }
        mock_redis.hgetall.return_value = pattern_data
        
        # Ejecutar
        popular = pattern_storage.get_popular_patterns(limit=5)
        
        # Verificar
        assert len(popular) <= 5
        assert mock_redis.zrevrange.called
        
    def test_deprecate_pattern(self, pattern_storage, mock_redis):
        """Test deprecar un patrón"""
        # Configurar mock
        pattern_data = {
            "id": "old-pattern",
            "domain": "old-site.com",
            "status": "active"
        }
        mock_redis.hgetall.return_value = pattern_data
        mock_redis.hset.return_value = True
        
        # Ejecutar
        result = pattern_storage.deprecate_pattern("old-pattern", "Site redesigned")
        
        # Verificar
        assert result is True
        mock_redis.hset.assert_called()
        
    def test_pattern_versioning(self, pattern_storage, mock_redis, sample_pattern):
        """Test sistema de versionado de patrones"""
        # Configurar mock
        old_pattern_data = sample_pattern.to_redis_hash()
        mock_redis.hgetall.return_value = old_pattern_data
        mock_redis.hset.return_value = True
        
        # Crear nueva versión con cambios
        new_selectors = SiteSelectors(
            title="h2.title-new",
            content="article.content-new"
        )
        
        # Ejecutar
        updated = pattern_storage.update_pattern(
            sample_pattern.id,
            selectors=new_selectors
        )
        
        # Verificar
        assert mock_redis.hset.called
        # La nueva versión debe incrementarse
        
    def test_cache_invalidation(self, pattern_storage, mock_redis):
        """Test invalidación de cache cuando se actualiza un patrón"""
        # Configurar mock
        mock_redis.delete.return_value = 1
        
        # Ejecutar
        pattern_storage.invalidate_pattern_cache("example.com", "noticias")
        
        # Verificar
        assert mock_redis.delete.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])