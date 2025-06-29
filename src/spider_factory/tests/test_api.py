"""
Tests unitarios para API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
import json

from src.api import app
from src.analyzer import AnalysisResult, AnalysisStrategy, SiteSelectors


class TestAPI:
    """Tests para endpoints de la API"""
    
    @pytest.fixture
    def client(self):
        """Cliente de test para FastAPI"""
        return TestClient(app)
        
    def test_health_check(self, client):
        """Test endpoint de health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        
    @patch('src.api.SmartAnalyzer')
    def test_analyze_endpoint_success(self, mock_analyzer_class, client):
        """Test endpoint /analyze exitoso"""
        # Configurar mock
        mock_analyzer = Mock()
        mock_analyzer.analyze_site = AsyncMock(return_value=AnalysisResult(
            url="https://example.com/news",
            domain="example.com",
            strategy=AnalysisStrategy.RSS,
            confidence=0.95,
            rss_url="https://example.com/feed.rss",
            selectors=None,
            needs_javascript=False,
            url_patterns=[],
            sample_articles=[],
            from_cache=False,
            medio="Example News",
            seccion="Internacional",
            area_geografica="GLOBAL",
            tipo_medio="diario",
            frecuencia_minutos=60
        ))
        mock_analyzer_class.return_value = mock_analyzer
        
        # Hacer petición
        response = client.post("/analyze", json={
            "url": "https://example.com/news",
            "medio": "Example News",
            "seccion": "Internacional",
            "area_geografica": "GLOBAL",
            "tipo_medio": "diario"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["strategy"] == "RSS"
        assert data["rss_url"] == "https://example.com/feed.rss"
        
    @patch('src.api.SmartAnalyzer')
    def test_analyze_endpoint_backward_compatibility(self, mock_analyzer_class, client):
        """Test compatibilidad hacia atrás del endpoint /analyze"""
        # Configurar mock
        mock_analyzer = Mock()
        mock_analyzer.analyze_site = AsyncMock(return_value=AnalysisResult(
            url="https://example.com",
            domain="example.com",
            strategy=AnalysisStrategy.SCRAPING,
            confidence=0.85,
            rss_url=None,
            selectors=SiteSelectors(
                title="h1",
                content="article",
                date="time",
                author="span.author"
            ),
            needs_javascript=False,
            url_patterns=[],
            sample_articles=[],
            from_cache=False,
            medio="Example",
            seccion="General",
            area_geografica="GLOBAL",
            tipo_medio="diario",
            frecuencia_minutos=60
        ))
        mock_analyzer_class.return_value = mock_analyzer
        
        # Petición con formato antiguo (solo name)
        response = client.post("/analyze", json={
            "url": "https://example.com",
            "name": "old_style_name"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["strategy"] == "SCRAPING"
        
    @patch('src.api.SpiderGenerator')
    @patch('src.api.SmartAnalyzer')
    def test_generate_endpoint_success(self, mock_analyzer_class, mock_generator_class, client):
        """Test endpoint /generate exitoso"""
        # Configurar mocks
        mock_analyzer = Mock()
        mock_generator = Mock()
        
        analysis_result = AnalysisResult(
            url="https://example.com/news",
            domain="example.com",
            strategy=AnalysisStrategy.RSS,
            confidence=0.95,
            rss_url="https://example.com/feed.rss",
            selectors=None,
            needs_javascript=False,
            url_patterns=[],
            sample_articles=[],
            from_cache=False,
            medio="Example News",
            seccion="Internacional",
            area_geografica="GLOBAL",
            tipo_medio="diario",
            frecuencia_minutos=60
        )
        
        mock_analyzer.analyze_site = AsyncMock(return_value=analysis_result)
        mock_generator.generate_spider = Mock(return_value="# Generated spider code")
        mock_generator.save_spider = Mock(return_value="/output/example_news_internacional.py")
        
        mock_analyzer_class.return_value = mock_analyzer
        mock_generator_class.return_value = mock_generator
        
        # Hacer petición
        response = client.post("/generate", json={
            "medio": "Example News",
            "seccion": "Internacional",
            "area_geografica": "GLOBAL",
            "tipo_medio": "diario",
            "url": "https://example.com/news"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["spider_name"] == "example_news_internacional"
        assert data["file_path"] == "/output/example_news_internacional.py"
        assert "# Generated spider code" in data["code"]
        
    @patch('src.api.get_redis_client')
    def test_check_duplicate_endpoint(self, mock_redis_func, client):
        """Test endpoint /check-duplicate"""
        # Configurar mock de Redis
        mock_redis = AsyncMock()
        mock_redis.exists = AsyncMock(return_value=True)
        mock_redis_func.return_value = mock_redis
        
        # Verificar duplicado existente
        response = client.post("/check-duplicate", json={
            "medio": "El País",
            "seccion": "Internacional"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is True
        assert data["spider_name"] == "el_pais_internacional"
        
        # Verificar no duplicado
        mock_redis.exists = AsyncMock(return_value=False)
        
        response = client.post("/check-duplicate", json={
            "medio": "New Site",
            "seccion": "News"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is False
        assert data["spider_name"] == "new_site_news"
        
    def test_analyze_invalid_request(self, client):
        """Test endpoint /analyze con request inválido"""
        # Sin URL
        response = client.post("/analyze", json={
            "medio": "Test"
        })
        
        assert response.status_code == 422  # Validation error
        
    def test_generate_invalid_area_geografica(self, client):
        """Test endpoint /generate con área geográfica inválida"""
        response = client.post("/generate", json={
            "medio": "Test",
            "seccion": "Test",
            "area_geografica": "INVALID_AREA",
            "tipo_medio": "diario",
            "url": "https://test.com"
        })
        
        assert response.status_code == 422
        
    @patch('src.api.Metrics')
    def test_metrics_endpoint(self, mock_metrics_class, client):
        """Test endpoint /metrics"""
        # Configurar mock
        mock_metrics = Mock()
        mock_metrics.get_all_metrics = AsyncMock(return_value={
            "analysis_count": 100,
            "spider_count": 50,
            "cache_hits": 30,
            "average_analysis_time": 15.5
        })
        mock_metrics_class.return_value = mock_metrics
        
        response = client.get("/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_count"] == 100
        assert data["spider_count"] == 50
        
    @patch('src.api.Metrics')
    def test_metrics_summary_endpoint(self, mock_metrics_class, client):
        """Test endpoint /metrics/summary"""
        # Configurar mock
        mock_metrics = Mock()
        mock_metrics.get_summary = AsyncMock(return_value={
            "total_analyses": 1000,
            "total_spiders": 500,
            "cache_hit_rate": 0.75,
            "average_time_saved": 18.5,
            "most_analyzed_domains": ["example.com", "test.com"]
        })
        mock_metrics_class.return_value = mock_metrics
        
        response = client.get("/metrics/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert data["cache_hit_rate"] == 0.75
        assert "example.com" in data["most_analyzed_domains"]
        
    @patch('src.api.PerformanceValidator')
    def test_metrics_performance_endpoint(self, mock_validator_class, client):
        """Test endpoint /metrics/performance"""
        # Configurar mock
        mock_validator = Mock()
        mock_validator.validate_kpis = AsyncMock(return_value={
            "rss_time_ok": True,
            "first_time_ok": True,
            "cache_time_ok": True,
            "reduction_ok": True,
            "overall_ok": True,
            "metrics": {
                "avg_rss_time": 3.5,
                "avg_first_time": 18.2,
                "avg_cache_time": 1.8,
                "time_reduction": 98.5
            }
        })
        mock_validator_class.return_value = mock_validator
        
        response = client.get("/metrics/performance")
        
        assert response.status_code == 200
        data = response.json()
        assert data["overall_ok"] is True
        assert data["metrics"]["time_reduction"] == 98.5
        
    def test_websocket_endpoint(self, client):
        """Test WebSocket endpoint básico"""
        # Nota: TestClient de FastAPI tiene soporte limitado para WebSockets
        # Este es un test básico de conexión
        with pytest.raises(Exception):
            # Se espera que falle porque no es una conexión WebSocket real
            with client.websocket_connect("/ws") as websocket:
                websocket.send_text("test")
                
    def test_cors_headers(self, client):
        """Test headers CORS"""
        response = client.options("/analyze")
        
        # Verificar que CORS esté configurado
        assert "access-control-allow-origin" in response.headers or \
               "Access-Control-Allow-Origin" in response.headers