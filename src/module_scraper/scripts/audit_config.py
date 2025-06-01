#!/usr/bin/env python3
"""
Script de Auditoría Automática de Configuración - Module Scraper
Analiza settings.py y detecta posibles conflictos de integración.
"""

import sys
import os
from pathlib import Path
import importlib.util
import inspect
from collections import defaultdict
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class ConfigAuditor:
    """Auditor automático de configuración del module_scraper."""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.info = []
        self.settings = None
        
    def load_settings(self):
        """Carga el archivo settings.py."""
        try:
            settings_path = project_root / 'scraper_core' / 'settings.py'
            spec = importlib.util.spec_from_file_location("settings", settings_path)
            self.settings = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.settings)
            self.info.append("✅ Settings.py cargado exitosamente")
            return True
        except Exception as e:
            self.issues.append(f"❌ Error cargando settings.py: {e}")
            return False
    
    def analyze_middleware_stack(self):
        """Analiza el stack de middlewares por conflictos."""
        print("\n🔍 Analizando Stack de Middlewares...")
        
        # Downloader Middlewares
        downloader_mw = getattr(self.settings, 'DOWNLOADER_MIDDLEWARES', {})
        if downloader_mw:
            self.info.append(f"📊 {len(downloader_mw)} downloader middlewares configurados")
            
            # Verificar prioridades y conflictos
            priorities = [(name, priority) for name, priority in downloader_mw.items() if priority is not None]
            priorities.sort(key=lambda x: x[1])
            
            print("   Orden de ejecución (por prioridad):")
            for name, priority in priorities:
                status = "✅" if priority is not None else "❌"
                print(f"   {status} {priority}: {name.split('.')[-1]}")
            
            # Detectar conflictos conocidos
            self._check_middleware_conflicts(downloader_mw)
        else:
            self.warnings.append("⚠️ No hay downloader middlewares configurados")
        
        # Spider Middlewares
        spider_mw = getattr(self.settings, 'SPIDER_MIDDLEWARES', {})
        if spider_mw:
            self.info.append(f"📊 {len(spider_mw)} spider middlewares configurados")
        else:
            self.warnings.append("⚠️ No hay spider middlewares configurados")
    
    def _check_middleware_conflicts(self, middlewares):
        """Detecta conflictos específicos en middlewares."""
        mw_names = [name.split('.')[-1] for name in middlewares.keys()]
        
        # Conflicto: UserAgent vs RandomUserAgent
        if 'UserAgentMiddleware' in str(middlewares) and 'RandomUserAgentMiddleware' in str(middlewares):
            ua_disabled = middlewares.get('scrapy.downloadermiddlewares.useragent.UserAgentMiddleware') is None
            if not ua_disabled:
                self.issues.append("❌ CONFLICTO: UserAgentMiddleware debería estar deshabilitado cuando se usa RandomUserAgentMiddleware")
            else:
                self.info.append("✅ UserAgentMiddleware correctamente deshabilitado para RandomUserAgent")
        
        # Verificar prioridades críticas
        playwright_priority = None
        crawl_once_priority = None
        
        for name, priority in middlewares.items():
            if 'Playwright' in name and priority is not None:
                playwright_priority = priority
            if 'CrawlOnce' in name and priority is not None:
                crawl_once_priority = priority
        
        if playwright_priority and crawl_once_priority:
            if crawl_once_priority >= playwright_priority:
                self.warnings.append(f"⚠️ PRIORIDAD: CrawlOnce ({crawl_once_priority}) debería ejecutarse antes que Playwright ({playwright_priority})")
    
    def analyze_pipeline_stack(self):
        """Analiza el stack de pipelines por orden y compatibilidad."""
        print("\n🔍 Analizando Stack de Pipelines...")
        
        pipelines = getattr(self.settings, 'ITEM_PIPELINES', {})
        if pipelines:
            self.info.append(f"📊 {len(pipelines)} pipelines configurados")
            
            # Ordenar por prioridad
            ordered_pipelines = [(name, priority) for name, priority in pipelines.items()]
            ordered_pipelines.sort(key=lambda x: x[1])
            
            print("   Orden de procesamiento:")
            for name, priority in ordered_pipelines:
                pipeline_name = name.split('.')[-1]
                print(f"   ✅ {priority}: {pipeline_name}")
            
            # Verificar orden lógico
            self._check_pipeline_order(ordered_pipelines)
        else:
            self.warnings.append("⚠️ No hay pipelines configurados")
    
    def _check_pipeline_order(self, pipelines):
        """Verifica que el orden de pipelines sea lógico."""
        pipeline_names = [name.split('.')[-1] for name, _ in pipelines]
        
        # Orden recomendado: Cleaning → Validation → Storage
        cleaning_idx = next((i for i, name in enumerate(pipeline_names) if 'Clean' in name), None)
        validation_idx = next((i for i, name in enumerate(pipeline_names) if 'Valid' in name), None)
        storage_idx = next((i for i, name in enumerate(pipeline_names) if 'Storage' in name or 'Supabase' in name), None)
        
        if cleaning_idx is not None and validation_idx is not None:
            if cleaning_idx > validation_idx:
                self.warnings.append("⚠️ ORDEN: Cleaning pipeline debería ejecutarse antes que Validation")
            else:
                self.info.append("✅ Orden correcto: Cleaning → Validation")
        
        if validation_idx is not None and storage_idx is not None:
            if validation_idx > storage_idx:
                self.issues.append("❌ ORDEN CRÍTICO: Validation debe ejecutarse antes que Storage")
            else:
                self.info.append("✅ Orden correcto: Validation → Storage")
    
    def analyze_configuration_consistency(self):
        """Analiza consistencia en configuraciones."""
        print("\n🔍 Analizando Consistencia de Configuración...")
        
        # Playwright configuration
        playwright_configs = [
            'PLAYWRIGHT_MAX_RETRIES', 'PLAYWRIGHT_TIMEOUT', 'PLAYWRIGHT_ENABLE_FALLBACK',
            'USE_PLAYWRIGHT_FOR_EMPTY_CONTENT', 'PLAYWRIGHT_BROWSER_TYPE'
        ]
        
        playwright_found = any(hasattr(self.settings, config) for config in playwright_configs)
        playwright_middleware = any('Playwright' in str(mw) for mw in getattr(self.settings, 'DOWNLOADER_MIDDLEWARES', {}))
        
        if playwright_middleware and not playwright_found:
            self.warnings.append("⚠️ Playwright middleware configurado pero faltan configuraciones específicas")
        elif playwright_found and not playwright_middleware:
            self.warnings.append("⚠️ Configuraciones de Playwright encontradas pero middleware no habilitado")
        elif playwright_found and playwright_middleware:
            self.info.append("✅ Configuración de Playwright consistente")
        
        # CrawlOnce configuration
        crawl_once_configs = ['CRAWL_ONCE_ENABLED', 'CRAWL_ONCE_PATH', 'CRAWL_ONCE_DEFAULT']
        crawl_once_found = any(hasattr(self.settings, config) for config in crawl_once_configs)
        crawl_once_middleware = any('CrawlOnce' in str(mw) for mw in getattr(self.settings, 'DOWNLOADER_MIDDLEWARES', {}))
        
        if crawl_once_middleware and not crawl_once_found:
            self.warnings.append("⚠️ CrawlOnce middleware configurado pero faltan configuraciones específicas")
        elif crawl_once_found and not crawl_once_middleware:
            self.warnings.append("⚠️ Configuraciones de CrawlOnce encontradas pero middleware no habilitado")
        elif crawl_once_found and crawl_once_middleware:
            self.info.append("✅ Configuración de CrawlOnce consistente")
    
    def analyze_dependencies(self):
        """Analiza dependencies de requirements.txt."""
        print("\n🔍 Analizando Dependencies...")
        
        requirements_path = project_root / 'requirements.txt'
        if requirements_path.exists():
            with open(requirements_path, 'r') as f:
                requirements = f.read()
            
            # Check critical dependencies
            critical_deps = {
                'scrapy': 'Core framework',
                'scrapy-playwright': 'JavaScript rendering',
                'scrapy-user-agents': 'User agent rotation',
                'scrapy-crawl-once': 'Duplicate prevention',
                'spidermon': 'Monitoring',
                'supabase': 'Database integration'
            }
            
            for dep, description in critical_deps.items():
                if dep in requirements:
                    self.info.append(f"✅ {dep}: {description}")
                else:
                    self.warnings.append(f"⚠️ {dep} no encontrado: {description}")
        else:
            self.issues.append("❌ requirements.txt no encontrado")
    
    def analyze_environment_variables(self):
        """Analiza variables de entorno requeridas."""
        print("\n🔍 Analizando Variables de Entorno...")
        
        env_files = [
            project_root / 'config' / '.env.test.example',
            project_root / 'config' / '.env',
            project_root / '.env'
        ]
        
        found_env = False
        for env_file in env_files:
            if env_file.exists():
                found_env = True
                self.info.append(f"✅ Encontrado: {env_file.name}")
                break
        
        if not found_env:
            self.warnings.append("⚠️ No se encontraron archivos .env de configuración")
        
        # Check critical environment variables
        critical_env_vars = [
            'SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY',
            'LOG_LEVEL', 'ENVIRONMENT'
        ]
        
        for var in critical_env_vars:
            if hasattr(self.settings, var) or os.getenv(var):
                self.info.append(f"✅ Variable de entorno configurada: {var}")
            else:
                self.warnings.append(f"⚠️ Variable de entorno no encontrada: {var}")
    
    def generate_report(self):
        """Genera el reporte final de auditoría."""
        print("\n" + "="*80)
        print("📋 REPORTE DE AUDITORÍA DE CONFIGURACIÓN")
        print("="*80)
        
        # Resumen
        total_issues = len(self.issues)
        total_warnings = len(self.warnings)
        total_info = len(self.info)
        
        print(f"\n📊 RESUMEN:")
        print(f"   🔴 Issues críticos: {total_issues}")
        print(f"   🟡 Warnings: {total_warnings}")
        print(f"   🟢 Configuraciones correctas: {total_info}")
        
        # Issues críticos
        if self.issues:
            print(f"\n🔴 ISSUES CRÍTICOS ({len(self.issues)}):")
            for issue in self.issues:
                print(f"   {issue}")
        
        # Warnings
        if self.warnings:
            print(f"\n🟡 WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   {warning}")
        
        # Configuraciones correctas
        if self.info:
            print(f"\n🟢 CONFIGURACIONES CORRECTAS ({len(self.info)}):")
            for info in self.info:
                print(f"   {info}")
        
        # Recomendaciones
        print(f"\n💡 RECOMENDACIONES:")
        if total_issues == 0 and total_warnings == 0:
            print("   ✅ Configuración óptima. Proceder con tests de integración.")
        elif total_issues == 0:
            print("   ⚠️ Resolver warnings antes de deployment en producción.")
        else:
            print("   🔴 Resolver issues críticos antes de continuar.")
        
        print("\n🚀 PRÓXIMOS PASOS:")
        print("   1. Resolver issues y warnings identificados")
        print("   2. Ejecutar script_test_integration.py (Fase 2)")
        print("   3. Proceder con tests de escenarios reales (Fase 3)")
        
        return total_issues == 0

def main():
    """Función principal."""
    print("🔍 INICIANDO AUDITORÍA AUTOMÁTICA DE CONFIGURACIÓN")
    print("="*60)
    
    auditor = ConfigAuditor()
    
    # Cargar configuración
    if not auditor.load_settings():
        print("❌ Error crítico: No se pudo cargar settings.py")
        return False
    
    # Ejecutar análisis
    auditor.analyze_middleware_stack()
    auditor.analyze_pipeline_stack()
    auditor.analyze_configuration_consistency()
    auditor.analyze_dependencies()
    auditor.analyze_environment_variables()
    
    # Generar reporte
    success = auditor.generate_report()
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
