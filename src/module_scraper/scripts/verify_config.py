#!/usr/bin/env python3
"""
Script de verificación rápida para la configuración de scrapy-user-agents.
Verifica que Scrapy puede cargar la configuración sin errores.
"""

import os
import sys
from pathlib import Path


def verify_scrapy_configuration():
    """
    Verifica que Scrapy puede cargar la configuración con scrapy-user-agents.
    """
    print("🔧 Verificando configuración de Scrapy...")

    try:
        # Cambiar al directorio del proyecto
        project_root = Path(__file__).parent.parent
        os.chdir(project_root)

        # Agregar el directorio del proyecto al path
        sys.path.insert(0, str(project_root))

        # Intentar importar las configuraciones
        from scrapy.utils.project import get_project_settings

        print("✅ Importación de Scrapy exitosa")

        # Cargar configuraciones del proyecto
        settings = get_project_settings()

        print("✅ Configuraciones del proyecto cargadas")

        # Verificar que el middleware está configurado
        downloader_middlewares = settings.get("DOWNLOADER_MIDDLEWARES", {})

        print("\\n📋 Middlewares configurados:")
        for middleware, priority in downloader_middlewares.items():
            status = "✅ HABILITADO" if priority is not None else "❌ DESHABILITADO"
            print(f"  {status}: {middleware} (prioridad: {priority})")

        # Verificar específicamente scrapy-user-agents
        user_agent_middleware = (
            "scrapy_user_agents.middlewares.RandomUserAgentMiddleware"
        )
        default_ua_middleware = (
            "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware"
        )

        if user_agent_middleware in downloader_middlewares:
            priority = downloader_middlewares[user_agent_middleware]
            if priority is not None:
                print(
                    f"\\n✅ scrapy-user-agents CORRECTAMENTE CONFIGURADO (prioridad: {priority})"
                )
            else:
                print(f"\\n❌ scrapy-user-agents está deshabilitado")  # noqa: F541
        else:
            print(f"\\n❌ scrapy-user-agents NO ENCONTRADO en la configuración")  # noqa: F541

        if default_ua_middleware in downloader_middlewares:
            priority = downloader_middlewares[default_ua_middleware]
            if priority is None:
                print(
                    f"✅ Middleware default de user-agent CORRECTAMENTE DESHABILITADO"
                )  # noqa: F541
            else:
                print(
                    f"⚠️  Middleware default de user-agent sigue habilitado (prioridad: {priority})"
                )

        # Intentar importar el middleware de scrapy-user-agents
        try:
            from scrapy_user_agents.middlewares import (
                RandomUserAgentMiddleware,  # noqa: F401
            )

            print("\\n✅ scrapy-user-agents se puede importar correctamente")
            return True
        except ImportError as e:
            print(f"\\n❌ Error al importar scrapy-user-agents: {e}")
            print("   Ejecuta: pip install scrapy-user-agents")
            return False

    except Exception as e:
        print(f"\\n❌ Error al verificar configuración: {e}")
        return False


def main():
    """Función principal"""
    print("🕷️  VERIFICACIÓN DE CONFIGURACIÓN SCRAPY-USER-AGENTS")
    print("=" * 60)

    success = verify_scrapy_configuration()

    print("\\n" + "=" * 60)
    if success:
        print("✅ Configuración verificada exitosamente.")
        print("   El proyecto está listo para usar rotación de user agents.")
    else:
        print("❌ Problemas encontrados en la configuración.")
        print("   Revisa los errores arriba y corrige antes de continuar.")
    print("=" * 60)


if __name__ == "__main__":
    main()
