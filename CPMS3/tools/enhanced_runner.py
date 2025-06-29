#!/usr/bin/env python3
"""
CPMS3 Enhanced Runner - Runner mejorado con validación completa
"""

import sys
import os
import argparse
import tempfile
import yaml
from pathlib import Path
from datetime import datetime

# Importar módulos del sistema
sys.path.insert(0, str(Path(__file__).parent))
from preprocessor import PlanPreprocessor
from validator import PlanValidator, print_validation_report
from runner import CPMS3Runner


class EnhancedRunner:
    """Runner mejorado con validación pre-ejecución"""
    
    def __init__(self, plan_path: str, options: dict = None):
        self.plan_path = Path(plan_path)
        self.options = options or {}
        self.processed_plan = None
        
    def run(self) -> bool:
        """Ejecuta el plan con validación completa"""
        print("\n" + "="*70)
        print("🚀 CPMS3 Enhanced Runner v2.0")
        print("="*70)
        
        # 1. FASE DE PREPROCESAMIENTO
        print("\n📋 Fase 1: Preprocesamiento")
        print("-" * 40)
        
        preprocessor = PlanPreprocessor(self.plan_path)
        processed_plan, prep_warnings, prep_errors = preprocessor.process()
        
        if prep_errors:
            print(f"❌ Errores de preprocesamiento: {len(prep_errors)}")
            for error in prep_errors:
                print(f"   • {error}")
            return False
        
        print("✅ Plan preprocesado correctamente")
        
        if prep_warnings:
            print(f"⚠️  Advertencias: {len(prep_warnings)}")
            for warning in prep_warnings:
                print(f"   • {warning}")
        
        self.processed_plan = processed_plan
        
        # 2. FASE DE VALIDACIÓN
        print("\n📋 Fase 2: Validación de precondiciones")
        print("-" * 40)
        
        validator = PlanValidator(processed_plan)
        is_valid, val_errors, val_warnings, val_info = validator.validate()
        
        # Mostrar resumen de validación
        if val_errors:
            print(f"❌ Errores de validación: {len(val_errors)}")
            for error in val_errors[:5]:  # Mostrar máx 5
                print(f"   • {error}")
            if len(val_errors) > 5:
                print(f"   • ... y {len(val_errors) - 5} errores más")
        
        if val_warnings:
            print(f"⚠️  Advertencias: {len(val_warnings)}")
            for warning in val_warnings[:3]:  # Mostrar máx 3
                print(f"   • {warning}")
            if len(val_warnings) > 3:
                print(f"   • ... y {len(val_warnings) - 3} advertencias más")
        
        if self.options.get('verbose'):
            print(f"✅ Verificaciones exitosas: {len(val_info)}")
        
        # Decisión de continuar
        if not is_valid:
            print("\n❌ Plan no válido. Corrige los errores antes de ejecutar.")
            
            if self.options.get('save_report'):
                self._save_validation_report(val_errors, val_warnings, val_info)
            
            return False
        
        print("\n✅ Todas las validaciones pasaron")
        
        # Preguntar confirmación si hay advertencias
        if val_warnings and not self.options.get('force'):
            print(f"\n⚠️  Hay {len(val_warnings)} advertencias. ¿Continuar? (s/N): ", end='')
            response = input().strip().lower()
            if response != 's':
                print("Ejecución cancelada por el usuario.")
                return False
        
        # 3. FASE DE EJECUCIÓN
        print("\n📋 Fase 3: Ejecución del plan")
        print("-" * 40)
        
        # Guardar plan procesado si se solicita
        if self.options.get('save_processed'):
            processed_path = self.plan_path.with_suffix('.processed.yaml')
            with open(processed_path, 'w', encoding='utf-8') as f:
                yaml.dump(processed_plan, f, default_flow_style=False, allow_unicode=True)
            print(f"💾 Plan procesado guardado en: {processed_path}")
        
        # Usar archivo temporal para el runner
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
            yaml.dump(processed_plan, tmp, default_flow_style=False, allow_unicode=True)
            tmp_path = tmp.name
        
        try:
            # Configurar opciones para el runner
            if self.options.get('strict'):
                # Inyectar modo strict en el plan
                if 'config' not in processed_plan:
                    processed_plan['config'] = {}
                processed_plan['config']['strict_mode'] = True
            
            # Ejecutar con el runner original
            print("\n🚀 Iniciando ejecución...\n")
            runner = CPMS3Runner(tmp_path)
            success = runner.run()
            
            return success
            
        finally:
            # Limpiar archivo temporal
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    def _save_validation_report(self, errors, warnings, info):
        """Guarda reporte de validación en archivo"""
        report_path = self.plan_path.with_suffix('.validation-report.txt')
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"CPMS3 Validation Report\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Plan: {self.plan_path}\n")
            f.write("="*60 + "\n\n")
            
            if errors:
                f.write(f"ERRORS ({len(errors)}):\n")
                for error in errors:
                    f.write(f"  - {error}\n")
                f.write("\n")
            
            if warnings:
                f.write(f"WARNINGS ({len(warnings)}):\n")
                for warning in warnings:
                    f.write(f"  - {warning}\n")
                f.write("\n")
            
            if info:
                f.write(f"SUCCESSFUL CHECKS ({len(info)}):\n")
                for i in info:
                    f.write(f"  - {i}\n")
        
        print(f"\n📄 Reporte guardado en: {report_path}")


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='CPMS3 Enhanced Runner - Ejecución robusta de planes'
    )
    
    parser.add_argument(
        'plan',
        help='Ruta al archivo execution_plan.yaml'
    )
    
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Ejecutar incluso con advertencias'
    )
    
    parser.add_argument(
        '--strict', '-s',
        action='store_true',
        help='Modo estricto: falla si quedan variables sin resolver'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Mostrar información detallada'
    )
    
    parser.add_argument(
        '--save-processed',
        action='store_true',
        help='Guardar el plan procesado'
    )
    
    parser.add_argument(
        '--save-report',
        action='store_true',
        help='Guardar reporte de validación si falla'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Solo validar, no ejecutar'
    )
    
    args = parser.parse_args()
    
    # Verificar que el archivo existe
    if not Path(args.plan).exists():
        print(f"❌ Error: Archivo no encontrado: {args.plan}")
        sys.exit(1)
    
    # Configurar opciones
    options = {
        'force': args.force,
        'strict': args.strict,
        'verbose': args.verbose,
        'save_processed': args.save_processed,
        'save_report': args.save_report,
    }
    
    # Modo dry-run
    if args.dry_run:
        print("🔍 Modo dry-run: Solo validación\n")
        
        # Preprocesar
        preprocessor = PlanPreprocessor(args.plan)
        processed_plan, prep_warnings, prep_errors = preprocessor.process()
        
        if prep_errors:
            print("❌ Errores de preprocesamiento:")
            for error in prep_errors:
                print(f"   • {error}")
            sys.exit(1)
        
        # Validar
        validator = PlanValidator(processed_plan)
        is_valid, val_errors, val_warnings, val_info = validator.validate()
        
        print_validation_report(is_valid, val_errors, val_warnings, val_info)
        
        sys.exit(0 if is_valid else 1)
    
    # Ejecutar
    runner = EnhancedRunner(args.plan, options)
    success = runner.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()