#!/usr/bin/env python3
"""
Test de verificación de técnicas de evasión implementadas
"""

import os
import sys

# Añadir paths necesarios
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../module_scraper"))


def test_headers_configuration():
    """Verifica que los headers están configurados correctamente"""
    print("\n=== Testing Headers HTTP ===")
    try:
        from scraper_core.settings import DEFAULT_REQUEST_HEADERS

        required_headers = [
            "Sec-Fetch-Dest",
            "Sec-Fetch-Mode",
            "Cache-Control",
            "Accept-Encoding",
        ]

        for header in required_headers:
            if header in DEFAULT_REQUEST_HEADERS:
                print(f"✓ {header}: {DEFAULT_REQUEST_HEADERS[header]}")
            else:
                print(f"✗ {header}: NO ENCONTRADO")
                return False

        print("✓ Headers HTTP configurados correctamente")
        return True

    except ImportError as e:
        print(f"✗ Error importando settings: {e}")
        return False


def test_user_agents():
    """Verifica la lista de User Agents"""
    print("\n=== Testing User Agents ===")
    try:
        from scraper_core.utils import user_agents

        print(f"✓ Desktop agents: {len(user_agents.DESKTOP_AGENTS)}")
        print(f"✓ Mobile agents: {len(user_agents.MOBILE_AGENTS)}")
        print(f"✓ Total agents: {len(user_agents.ALL_USER_AGENTS)}")

        # Test funciones
        desktop_ua = user_agents.get_desktop_agent()
        print(f"✓ Desktop UA sample: {desktop_ua[:50]}...")

        return True

    except ImportError as e:
        print(f"✗ Error importando user_agents: {e}")
        return False


def test_referer_middleware():
    """Verifica configuración de Referer"""
    print("\n=== Testing Referer Configuration ===")
    try:
        from scraper_core.settings import (
            DOWNLOADER_MIDDLEWARES,
            REFERER_ENABLED,
            REFERRER_POLICY,
        )

        print(f"✓ REFERER_ENABLED: {REFERER_ENABLED}")
        print(f"✓ REFERRER_POLICY: {REFERRER_POLICY}")

        # Verificar SmartRefererMiddleware
        smart_referer = None
        for middleware, priority in DOWNLOADER_MIDDLEWARES.items():
            if "SmartRefererMiddleware" in middleware:
                smart_referer = (middleware, priority)
                break

        if smart_referer:
            print(
                f"✓ SmartRefererMiddleware: {smart_referer[0]} (priority: {smart_referer[1]})"
            )
        else:
            print("✗ SmartRefererMiddleware no encontrado")
            return False

        return True

    except ImportError as e:
        print(f"✗ Error verificando referer: {e}")
        return False


def main():
    """Ejecuta todos los tests"""
    print("=" * 50)
    print("Testing Técnicas de Evasión - Spider Factory")
    print("=" * 50)

    results = []

    # Test 1: Headers
    results.append(("Headers HTTP", test_headers_configuration()))

    # Test 2: User Agents
    results.append(("User Agents", test_user_agents()))

    # Test 3: Referer
    results.append(("Referer Middleware", test_referer_middleware()))

    # Resumen
    print("\n" + "=" * 50)
    print("RESUMEN DE TESTS")
    print("=" * 50)

    passed = 0
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\nTotal: {passed}/{len(results)} tests pasaron")

    # Exit code
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
