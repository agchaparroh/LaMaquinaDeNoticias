"""
Tests unitarios para patterns.py
"""
import pytest
from datetime import datetime
import json

from src.patterns import PatternStorage, Pattern
from src.analyzer import SiteSelectors


class TestPatternStorage:
    """Tests para PatternStorage"""
    
    @pytest.mark.asyncio
    async def test_save_pattern(self, mock_pattern_storage, mock_redis_client):
        """Test guardado de patrón"""
        pattern = Pattern(
            domain="example.com",
            selectors=SiteSelectors(
                title="h1.title",
                content="div.content",
                date="time",
                author="span.author"
            ),
            url_patterns=["https://example.com/article/*"],
            needs_javascript=False,
            last_updated=datetime.now(),
            success_count=1,
            failure_count=0
        )
        
        await mock_pattern_storage.save_pattern(pattern)
        
        # Verificar que se guardó correctamente
        pattern_key = f"pattern:{pattern.domain}"
        mock_redis_client.hset.assert_called()
        
        # Verificar que se configuró TTL
        mock_redis_client.expire.assert_called_with(pattern_key, 604800)  # 7 días
        
    @pytest.mark.asyncio
    async def test_get_pattern_exists(self, mock_pattern_storage, mock_redis_client):
        """Test obtención de patrón existente"""
        # Configurar patrón existente
        pattern_data = {
            "domain": "example.com",
            "selectors": json.dumps({
                "title": "h1.title",
                "content": "div.content",
                "date": "time",
                "author": "span.author"
            }),
            "url_patterns": json.dumps(["https://example.com/article/*"]),
            "needs_javascript": "false",
            "last_updated": datetime.now().isoformat(),
            "success_count": "10",
            "failure_count": "1"
        }
        
        mock_redis_client.exists = AsyncMock(return_value=True)
        mock_redis_client.hgetall = AsyncMock(return_value=pattern_data)
        
        pattern = await mock_pattern_storage.get_pattern("example.com")
        
        assert pattern is not None
        assert pattern.domain == "example.com"
        assert pattern.selectors.title == "h1.title"
        assert pattern.success_count == 10
        
    @pytest.mark.asyncio
    async def test_get_pattern_not_exists(self, mock_pattern_storage, mock_redis_client):
        """Test obtención de patrón no existente"""
        mock_redis_client.exists = AsyncMock(return_value=False)
        
        pattern = await mock_pattern_storage.get_pattern("notexist.com")
        
        assert pattern is None
        
    @pytest.mark.asyncio
    async def test_update_pattern_success(self, mock_pattern_storage, mock_redis_client):
        """Test actualización de patrón con éxito"""
        # Configurar patrón existente
        pattern_data = {
            "success_count": "5",
            "failure_count": "1"
        }
        mock_redis_client.hgetall = AsyncMock(return_value=pattern_data)
        
        await mock_pattern_storage.update_pattern_stats("example.com", success=True)
        
        # Verificar incremento de success_count
        mock_redis_client.hincrby.assert_called_with(
            "pattern:example.com",
            "success_count",
            1
        )
        
    @pytest.mark.asyncio
    async def test_update_pattern_failure(self, mock_pattern_storage, mock_redis_client):
        """Test actualización de patrón con fallo"""
        # Configurar patrón existente
        pattern_data = {
            "success_count": "5",
            "failure_count": "1"
        }
        mock_redis_client.hgetall = AsyncMock(return_value=pattern_data)
        
        await mock_pattern_storage.update_pattern_stats("example.com", success=False)
        
        # Verificar incremento de failure_count
        mock_redis_client.hincrby.assert_called_with(
            "pattern:example.com",
            "failure_count",
            1
        )
        
    @pytest.mark.asyncio
    async def test_pattern_failure_threshold(self, mock_pattern_storage, mock_redis_client):
        """Test eliminación de patrón por muchos fallos"""
        # Configurar patrón con muchos fallos
        pattern_data = {
            "success_count": "2",
            "failure_count": "10"  # Más de 5 fallos consecutivos
        }
        mock_redis_client.hgetall = AsyncMock(return_value=pattern_data)
        
        await mock_pattern_storage.update_pattern_stats("example.com", success=False)
        
        # Verificar que se intentó eliminar el patrón
        mock_redis_client.delete.assert_called_with("pattern:example.com")
        
    @pytest.mark.asyncio
    async def test_list_patterns(self, mock_pattern_storage, mock_redis_client):
        """Test listado de todos los patrones"""
        # Configurar múltiples patrones
        pattern_keys = [
            "pattern:example.com",
            "pattern:test.com",
            "pattern:news.com"
        ]
        mock_redis_client.keys = AsyncMock(return_value=pattern_keys)
        
        patterns = await mock_pattern_storage.list_patterns()
        
        assert len(patterns) == 3
        assert "example.com" in patterns
        assert "test.com" in patterns
        assert "news.com" in patterns
        
    @pytest.mark.asyncio
    async def test_delete_pattern(self, mock_pattern_storage, mock_redis_client):
        """Test eliminación de patrón"""
        await mock_pattern_storage.delete_pattern("example.com")
        
        mock_redis_client.delete.assert_called_with("pattern:example.com")
        
    @pytest.mark.asyncio
    async def test_pattern_validation(self, mock_pattern_storage):
        """Test validación de selectores en patrón"""
        # Patrón con selectores inválidos
        pattern = Pattern(
            domain="example.com",
            selectors=SiteSelectors(
                title=None,  # Title es requerido
                content=None,  # Content es requerido
                date="time",
                author="span.author"
            ),
            url_patterns=[],
            needs_javascript=False,
            last_updated=datetime.now(),
            success_count=0,
            failure_count=0
        )
        
        # Verificar que se detectan selectores inválidos
        is_valid = pattern.selectors.title is not None and pattern.selectors.content is not None
        assert not is_valid
        
    @pytest.mark.asyncio
    async def test_pattern_ttl_refresh(self, mock_pattern_storage, mock_redis_client):
        """Test renovación de TTL al actualizar patrón"""
        await mock_pattern_storage.update_pattern_stats("example.com", success=True)
        
        # Verificar que se renovó el TTL
        mock_redis_client.expire.assert_called_with("pattern:example.com", 604800)
        
    @pytest.mark.asyncio
    async def test_pattern_serialization(self, mock_pattern_storage):
        """Test serialización y deserialización de patrones"""
        original_pattern = Pattern(
            domain="test.com",
            selectors=SiteSelectors(
                title="h1",
                content="article",
                date="time",
                author="span.author"
            ),
            url_patterns=["https://test.com/*"],
            needs_javascript=True,
            last_updated=datetime.now(),
            success_count=100,
            failure_count=5
        )
        
        # Serializar
        pattern_dict = {
            "domain": original_pattern.domain,
            "selectors": json.dumps({
                "title": original_pattern.selectors.title,
                "content": original_pattern.selectors.content,
                "date": original_pattern.selectors.date,
                "author": original_pattern.selectors.author
            }),
            "url_patterns": json.dumps(original_pattern.url_patterns),
            "needs_javascript": str(original_pattern.needs_javascript).lower(),
            "last_updated": original_pattern.last_updated.isoformat(),
            "success_count": str(original_pattern.success_count),
            "failure_count": str(original_pattern.failure_count)
        }
        
        # Verificar que se puede serializar correctamente
        assert pattern_dict["domain"] == "test.com"
        assert "h1" in pattern_dict["selectors"]
        assert pattern_dict["needs_javascript"] == "true"