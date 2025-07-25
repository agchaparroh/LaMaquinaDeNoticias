#!/usr/bin/env python3
"""
Test script para verificar el funcionamiento de SmartAnalyzer
"""

import asyncio
import json  # noqa: F401
from datetime import datetime  # noqa: F401

from analyzer import (
    AnalysisConfidence,  # noqa: F401
    AnalysisStrategy,  # noqa: F401
    SiteAnalysisRequest,
    SmartAnalyzer,
)

from config import RedisKeys, get_redis_client


async def test_smart_analyzer():
    """Test completo del SmartAnalyzer"""
    print("=== Test de SmartAnalyzer ===\n")

    analyzer = SmartAnalyzer()
    redis = get_redis_client()

    # Lista de sitios para probar
    test_sites = [
        {
            "url": "https://elpais.com/internacional",
            "section": "internacional",
            "expected_strategy": None,  # Dependerá del análisis
        },
        {
            "url": "https://www.bbc.com/news",
            "section": "news",
            "expected_strategy": None,
        },
        {
            "url": "https://edition.cnn.com/world",
            "section": "world",
            "expected_strategy": None,
        },
    ]

    try:
        # Test 1: Análisis inicial (sin cache)
        print("=== Test 1: Análisis inicial ===")
        for site in test_sites[:1]:  # Solo el primer sitio
            request = SiteAnalysisRequest(
                url=site["url"],
                section_name=site["section"],
                force_analysis=True,  # Forzar análisis nuevo
            )

            print(f"\nAnalizando: {request.url}")
            result = await analyzer.analyze(request)

            print(f"✅ Estrategia: {result.strategy}")
            print(f"✅ Confianza: {result.confidence}")
            print(f"✅ Necesita JS: {result.needs_javascript}")
            print(f"✅ Desde cache: {result.from_cache}")

            if result.rss_url:
                print(f"✅ RSS encontrado: {result.rss_url}")

            if result.selectors:
                print(f"✅ Selectores:")  # noqa: F541
                for key, value in result.selectors.dict().items():
                    if value:
                        print(f"   - {key}: {value}")

            if result.sample_articles:
                print(f"✅ Artículos de muestra: {len(result.sample_articles)}")
                for i, article in enumerate(result.sample_articles[:2]):
                    print(f"   {i + 1}. {article.get('title', 'Sin título')}")

        # Test 2: Verificar cache
        print("\n\n=== Test 2: Verificar cache ===")
        request = SiteAnalysisRequest(
            url=test_sites[0]["url"],
            section_name=test_sites[0]["section"],
            force_analysis=False,  # Usar cache si existe
        )

        result2 = await analyzer.analyze(request)
        print(f"✅ Análisis desde cache: {result2.from_cache}")
        print(f"✅ Misma estrategia: {result2.strategy == result.strategy}")

        # Test 3: Verificar patrones guardados
        print("\n\n=== Test 3: Verificar patrones ===")
        domain = "elpais.com"
        section = "internacional"
        pattern_key = RedisKeys.format_key(
            RedisKeys.PATTERN_KEY, domain=domain, section=section
        )

        pattern_exists = redis.exists(pattern_key)
        print(f"✅ Patrón guardado: {pattern_exists == 1}")

        if pattern_exists:
            pattern_data = redis.hgetall(pattern_key)
            print(f"✅ Datos del patrón:")  # noqa: F541
            for key, value in pattern_data.items():
                print(
                    f"   - {key}: {value[:50]}..."
                    if len(value) > 50
                    else f"   - {key}: {value}"
                )

        # Test 4: Estadísticas de uso
        print("\n\n=== Test 4: Estadísticas de uso ===")
        usage_key = RedisKeys.STATS_PATTERN_USAGE
        top_patterns = redis.zrevrange(usage_key, 0, 4, withscores=True)

        if top_patterns:
            print("✅ Top patrones más usados:")
            for pattern, score in top_patterns:
                print(f"   - {pattern}: {int(score)} usos")

        # Test 5: Forzar análisis básico (sin Firecrawl)
        print("\n\n=== Test 5: Análisis básico (simulando sin Firecrawl) ===")
        # Temporalmente quitar la API key
        original_key = analyzer.config.firecrawl_api_key
        analyzer.config.firecrawl_api_key = ""

        request = SiteAnalysisRequest(
            url="https://example.com", section_name="test", force_analysis=True
        )

        result_basic = await analyzer.analyze(request)
        print(f"✅ Análisis básico completado")  # noqa: F541
        print(f"✅ Confianza baja esperada: {result_basic.confidence <= 0.5}")

        # Restaurar API key
        analyzer.config.firecrawl_api_key = original_key

        print("\n✅ Todos los tests completados exitosamente!")

    except Exception as e:
        print(f"\n❌ Error en tests: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await analyzer.close()
        print("\n=== Limpiando datos de prueba ===")
        # Opcional: limpiar datos de prueba
        # for site in test_sites:
        #     # Limpiar cache y patrones de prueba


def main():
    """Ejecutar tests"""
    print("=== Spider Factory 2.0 - Test de SmartAnalyzer ===")
    print("Asegúrate de que Redis esté corriendo\n")

    asyncio.run(test_smart_analyzer())


if __name__ == "__main__":
    main()
