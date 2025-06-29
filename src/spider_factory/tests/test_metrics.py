"""
Tests unitarios para metrics.py
"""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta
import json

from src.metrics import Metrics
from src.performance_metrics import PerformanceValidator


class TestMetrics:
    """Tests para sistema de métricas"""
    
    @pytest.mark.asyncio
    async def test_record_analysis(self, mock_metrics, mock_redis_client):
        """Test registro de análisis"""
        await mock_metrics.record_analysis(
            domain="example.com",
            strategy="RSS",
            time_taken=5.2,
            from_cache=False
        )
        
        # Verificar incrementos
        mock_redis_client.incr.assert_any_call("metrics:analysis_count")
        mock_redis_client.incr.assert_any_call("metrics:strategy:RSS")
        
        # Verificar tiempo registrado
        mock_redis_client.lpush.assert_called()
        
    @pytest.mark.asyncio
    async def test_record_spider_generation(self, mock_metrics, mock_redis_client):
        """Test registro de generación de spider"""
        await mock_metrics.record_spider_generation(
            spider_name="test_spider",
            medio="Test News",
            seccion="Local",
            time_taken=2.5
        )
        
        mock_redis_client.incr.assert_any_call("metrics:spider_count")
        mock_redis_client.hset.assert_called()
        
    @pytest.mark.asyncio
    async def test_get_cache_hit_rate(self, mock_metrics, mock_redis_client):
        """Test cálculo de tasa de aciertos de cache"""
        # Configurar contadores
        mock_redis_client.get = AsyncMock(side_effect=lambda key: {
            "metrics:cache_hits": "30",
            "metrics:analysis_count": "100"
        }.get(key, "0"))
        
        rate = await mock_metrics.get_cache_hit_rate()
        
        assert rate == 0.3  # 30/100
        
    @pytest.mark.asyncio
    async def test_get_cache_hit_rate_no_analyses(self, mock_metrics, mock_redis_client):
        """Test tasa de cache cuando no hay análisis"""
        mock_redis_client.get = AsyncMock(return_value="0")
        
        rate = await mock_metrics.get_cache_hit_rate()
        
        assert rate == 0.0
        
    @pytest.mark.asyncio
    async def test_get_average_time_saved(self, mock_metrics, mock_redis_client):
        """Test cálculo de tiempo promedio ahorrado"""
        # Tiempos de primera vez
        first_times = ["20.5", "18.3", "22.1"]
        # Tiempos de cache
        cache_times = ["1.5", "1.8", "2.0"]
        
        mock_redis_client.lrange = AsyncMock(side_effect=[
            first_times,
            cache_times
        ])
        
        time_saved = await mock_metrics.get_average_time_saved()
        
        # Promedio primera vez: ~20.3
        # Promedio cache: ~1.77
        # Ahorro: ~18.53
        assert time_saved > 18
        assert time_saved < 19
        
    @pytest.mark.asyncio
    async def test_get_spider_success_rate(self, mock_metrics, mock_redis_client):
        """Test cálculo de tasa de éxito de spiders"""
        # Configurar datos de spiders
        spiders_data = {
            "spider1": json.dumps({"success_count": 10, "error_count": 2}),
            "spider2": json.dumps({"success_count": 20, "error_count": 5}),
            "spider3": json.dumps({"success_count": 15, "error_count": 0})
        }
        
        mock_redis_client.hgetall = AsyncMock(return_value=spiders_data)
        
        rate = await mock_metrics.get_spider_success_rate()
        
        # Total éxitos: 45, Total errores: 7
        # Tasa: 45 / (45 + 7) = 0.865
        assert rate > 0.86
        assert rate < 0.87
        
    @pytest.mark.asyncio
    async def test_get_most_analyzed_domains(self, mock_metrics, mock_redis_client):
        """Test obtención de dominios más analizados"""
        domains_data = {
            "example.com": "25",
            "test.com": "15",
            "news.com": "30",
            "blog.com": "5"
        }
        
        mock_redis_client.hgetall = AsyncMock(return_value=domains_data)
        
        top_domains = await mock_metrics.get_most_analyzed_domains(top_n=3)
        
        assert len(top_domains) == 3
        assert top_domains[0] == ("news.com", 30)
        assert top_domains[1] == ("example.com", 25)
        assert top_domains[2] == ("test.com", 15)
        
    @pytest.mark.asyncio
    async def test_start_end_timer(self, mock_metrics, mock_redis_client):
        """Test medición de tiempo con timer"""
        start_time = await mock_metrics.start_timer("test_operation")
        
        # Simular operación
        await asyncio.sleep(0.1)
        
        elapsed = await mock_metrics.end_timer("test_operation", start_time)
        
        assert elapsed >= 0.1
        assert elapsed < 0.2
        
        # Verificar que se registró
        mock_redis_client.lpush.assert_called()
        
    @pytest.mark.asyncio
    async def test_get_all_metrics(self, mock_metrics, mock_redis_client):
        """Test obtención de todas las métricas"""
        # Configurar respuestas mock
        mock_redis_client.get = AsyncMock(side_effect=lambda key: {
            "metrics:analysis_count": "100",
            "metrics:spider_count": "50",
            "metrics:cache_hits": "30"
        }.get(key, "0"))
        
        mock_redis_client.lrange = AsyncMock(return_value=["5.2", "3.8", "4.5"])
        mock_redis_client.hgetall = AsyncMock(return_value={})
        
        metrics = await mock_metrics.get_all_metrics()
        
        assert metrics["analysis_count"] == 100
        assert metrics["spider_count"] == 50
        assert metrics["cache_hits"] == 30
        assert "average_analysis_time" in metrics
        
    @pytest.mark.asyncio
    async def test_get_summary(self, mock_metrics, mock_redis_client):
        """Test resumen de métricas"""
        # Configurar mocks para summary
        mock_metrics.get_cache_hit_rate = AsyncMock(return_value=0.75)
        mock_metrics.get_average_time_saved = AsyncMock(return_value=18.5)
        mock_metrics.get_spider_success_rate = AsyncMock(return_value=0.92)
        mock_metrics.get_most_analyzed_domains = AsyncMock(return_value=[
            ("example.com", 50),
            ("test.com", 30)
        ])
        
        mock_redis_client.get = AsyncMock(side_effect=lambda key: {
            "metrics:analysis_count": "1000",
            "metrics:spider_count": "500"
        }.get(key, "0"))
        
        summary = await mock_metrics.get_summary()
        
        assert summary["total_analyses"] == 1000
        assert summary["total_spiders"] == 500
        assert summary["cache_hit_rate"] == 0.75
        assert summary["average_time_saved"] == 18.5
        assert summary["spider_success_rate"] == 0.92
        assert len(summary["most_analyzed_domains"]) == 2


class TestPerformanceValidator:
    """Tests para validador de performance"""
    
    @pytest.mark.asyncio
    async def test_validate_kpis_all_ok(self, mock_redis_client):
        """Test validación cuando todos los KPIs están OK"""
        # Configurar tiempos que cumplen KPIs
        mock_redis_client.lrange = AsyncMock(side_effect=[
            ["3.5", "4.0", "4.5"],  # RSS times (< 5s)
            ["18.0", "19.0", "20.0"],  # First times (< 20s)
            ["1.5", "1.8", "1.9"]  # Cache times (< 2s)
        ])
        
        validator = PerformanceValidator(mock_redis_client)
        result = await validator.validate_kpis()
        
        assert result["rss_time_ok"] is True
        assert result["first_time_ok"] is True
        assert result["cache_time_ok"] is True
        assert result["reduction_ok"] is True
        assert result["overall_ok"] is True
        
    @pytest.mark.asyncio
    async def test_validate_kpis_rss_fail(self, mock_redis_client):
        """Test validación cuando RSS excede tiempo"""
        # RSS time > 5s
        mock_redis_client.lrange = AsyncMock(side_effect=[
            ["6.0", "7.0", "5.5"],  # RSS times (> 5s)
            ["18.0", "19.0", "20.0"],
            ["1.5", "1.8", "1.9"]
        ])
        
        validator = PerformanceValidator(mock_redis_client)
        result = await validator.validate_kpis()
        
        assert result["rss_time_ok"] is False
        assert result["overall_ok"] is False
        
    @pytest.mark.asyncio
    async def test_validate_kpis_reduction_fail(self, mock_redis_client):
        """Test validación cuando reducción es insuficiente"""
        # Cache time no es suficientemente menor que first time
        mock_redis_client.lrange = AsyncMock(side_effect=[
            ["4.0", "4.5", "3.5"],
            ["10.0", "12.0", "11.0"],  # First time bajo
            ["5.0", "6.0", "5.5"]  # Cache time alto
        ])
        
        validator = PerformanceValidator(mock_redis_client)
        result = await validator.validate_kpis()
        
        assert result["reduction_ok"] is False
        assert result["overall_ok"] is False
        
    @pytest.mark.asyncio
    async def test_calculate_time_reduction(self, mock_redis_client):
        """Test cálculo de porcentaje de reducción de tiempo"""
        validator = PerformanceValidator(mock_redis_client)
        
        # 20s a 1s = 95% reducción
        reduction = validator._calculate_time_reduction(20.0, 1.0)
        assert reduction == 95.0
        
        # 10s a 2s = 80% reducción
        reduction = validator._calculate_time_reduction(10.0, 2.0)
        assert reduction == 80.0
        
        # Casos edge
        reduction = validator._calculate_time_reduction(0.0, 1.0)
        assert reduction == 0.0
        
    @pytest.mark.asyncio
    async def test_get_performance_metrics(self, mock_redis_client):
        """Test obtención de métricas de performance"""
        mock_redis_client.lrange = AsyncMock(side_effect=[
            ["3.5", "4.0", "4.5"],
            ["18.0", "19.0", "20.0"],
            ["1.5", "1.8", "1.9"]
        ])
        
        validator = PerformanceValidator(mock_redis_client)
        metrics = await validator.get_performance_metrics()
        
        assert "avg_rss_time" in metrics
        assert "avg_first_time" in metrics
        assert "avg_cache_time" in metrics
        assert "time_reduction_percentage" in metrics
        
        assert metrics["avg_rss_time"] == 4.0
        assert metrics["avg_first_time"] == 19.0
        assert metrics["avg_cache_time"] < 2.0


# Importar asyncio para el sleep en tests
import asyncio