#!/usr/bin/env python3
"""
CPMS3 Preprocessor - Prepara y valida planes antes de ejecución
"""

import yaml
import re
import copy
from pathlib import Path
from typing import Dict, Any, List, Tuple
import sys


class PlanPreprocessor:
    """Preprocesa planes de ejecución para garantizar determinismo"""
    
    def __init__(self, plan_path: str):
        self.plan_path = Path(plan_path)
        self.raw_plan = None
        self.processed_plan = None
        self.warnings = []
        self.errors = []
        
    def process(self) -> Tuple[Dict, List[str], List[str]]:
        """
        Procesa el plan y retorna (plan_procesado, advertencias, errores)
        """
        # 1. Cargar plan
        self._load_plan()
        if self.errors:
            return None, self.warnings, self.errors
        
        # 2. Copiar para no modificar original
        self.processed_plan = copy.deepcopy(self.raw_plan)
        
        # 3. Resolver variables
        self._resolve_all_variables()
        
        # 4. Normalizar patrones de texto
        self._normalize_text_patterns()
        
        # 5. Validar estructura
        self._validate_structure()
        
        return self.processed_plan, self.warnings, self.errors
    
    def _load_plan(self):
        """Carga el plan YAML con manejo de errores"""
        try:
            with open(self.plan_path, 'r', encoding='utf-8') as f:
                self.raw_plan = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.errors.append(f"Error de sintaxis YAML: {str(e)}")
        except FileNotFoundError:
            self.errors.append(f"Archivo no encontrado: {self.plan_path}")
        except Exception as e:
            self.errors.append(f"Error al cargar plan: {str(e)}")
    
    def _resolve_all_variables(self):
        """Resuelve todas las variables en el plan"""
        if not self.processed_plan:
            return
        
        # Obtener variables definidas
        constants = self.processed_plan.get('constants', {})
        config = self.processed_plan.get('config', {})
        
        # Variables del sistema
        system_vars = {
            'base_path': config.get('base_path', '/mnt/c/Users/DELL/Desktop/PruebaWindsurfAI/LaMaquinaDeNoticias'),
            'staging_dir': config.get('staging_dir', '.cpms3_staging'),
        }
        
        # Combinar todas las variables
        all_vars = {**system_vars, **constants}
        
        # Resolver variables en todo el plan
        self.processed_plan = self._resolve_in_dict(self.processed_plan, all_vars)
        
        # Verificar variables no resueltas
        unresolved = self._find_unresolved_variables(self.processed_plan)
        if unresolved:
            for var in unresolved:
                self.errors.append(f"Variable no resuelta: {var}")
    
    def _resolve_in_dict(self, obj: Any, variables: Dict[str, Any]) -> Any:
        """Resuelve variables recursivamente en cualquier estructura"""
        if isinstance(obj, dict):
            return {k: self._resolve_in_dict(v, variables) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._resolve_in_dict(item, variables) for item in obj]
        elif isinstance(obj, str):
            return self._resolve_string(obj, variables)
        else:
            return obj
    
    def _resolve_string(self, text: str, variables: Dict[str, Any]) -> str:
        """Resuelve variables en una cadena"""
        # Patrón para encontrar {variable}
        pattern = r'\{([^}]+)\}'
        
        def replacer(match):
            var_name = match.group(1)
            if var_name in variables:
                return str(variables[var_name])
            else:
                # Mantener la variable sin resolver para detectarla después
                return match.group(0)
        
        return re.sub(pattern, replacer, text)
    
    def _find_unresolved_variables(self, obj: Any, path: str = "") -> List[str]:
        """Encuentra todas las variables no resueltas"""
        unresolved = []
        
        if isinstance(obj, dict):
            for k, v in obj.items():
                unresolved.extend(self._find_unresolved_variables(v, f"{path}.{k}"))
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                unresolved.extend(self._find_unresolved_variables(item, f"{path}[{i}]"))
        elif isinstance(obj, str):
            # Buscar patrones {variable}
            matches = re.findall(r'\{([^}]+)\}', obj)
            for match in matches:
                unresolved.append(f"{{{match}}} en {path}")
        
        return unresolved
    
    def _normalize_text_patterns(self):
        """Normaliza patrones de búsqueda/reemplazo para mayor robustez"""
        if not self.processed_plan or 'steps' not in self.processed_plan:
            return
        
        for step in self.processed_plan.get('steps', []):
            if step.get('action') == 'modify_file' and 'changes' in step:
                for change in step['changes']:
                    if 'find' in change:
                        original = change['find']
                        normalized = self._normalize_text(change['find'])
                        if original != normalized:
                            self.warnings.append(
                                f"Step {step.get('id', '?')}: Patrón normalizado "
                                f"(espacios/saltos de línea)"
                            )
                        change['find'] = normalized
                    
                    if 'replace' in change:
                        change['replace'] = self._normalize_text(change['replace'])
    
    def _normalize_text(self, text: str) -> str:
        """
        Normaliza texto para búsqueda más robusta:
        - Convierte múltiples espacios en uno
        - Normaliza saltos de línea
        - Elimina espacios al final de líneas
        """
        if not isinstance(text, str):
            return text
        
        # Eliminar espacios al final de cada línea
        lines = [line.rstrip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        # Normalizar múltiples espacios (excepto en indentación)
        # Esto es más complejo para preservar la indentación de Python/YAML
        normalized_lines = []
        for line in lines:
            # Preservar indentación inicial
            indent = len(line) - len(line.lstrip())
            content = line[indent:]
            # Normalizar espacios en el contenido
            content = re.sub(r' +', ' ', content)
            normalized_lines.append(' ' * indent + content)
        
        return '\n'.join(normalized_lines)
    
    def _validate_structure(self):
        """Valida la estructura del plan"""
        if not self.processed_plan:
            return
        
        # Validar meta información
        if 'meta' not in self.processed_plan:
            self.errors.append("Falta sección 'meta' en el plan")
        else:
            meta = self.processed_plan['meta']
            required_meta = ['id', 'name', 'goal']
            for field in required_meta:
                if field not in meta:
                    self.errors.append(f"Falta campo requerido 'meta.{field}'")
        
        # Validar steps
        if 'steps' not in self.processed_plan:
            self.errors.append("Falta sección 'steps' en el plan")
        else:
            steps = self.processed_plan['steps']
            if not isinstance(steps, list):
                self.errors.append("'steps' debe ser una lista")
            else:
                for i, step in enumerate(steps):
                    self._validate_step(step, i)
    
    def _validate_step(self, step: Dict, index: int):
        """Valida un paso individual"""
        step_id = step.get('id', f'step_{index}')
        
        # Campos requeridos
        if 'action' not in step:
            self.errors.append(f"{step_id}: Falta campo 'action'")
            return
        
        action = step['action']
        
        # Validar según tipo de acción
        if action == 'create_file':
            if 'path' not in step:
                self.errors.append(f"{step_id}: create_file requiere 'path'")
            if 'content' not in step:
                self.errors.append(f"{step_id}: create_file requiere 'content'")
                
        elif action == 'modify_file':
            if 'path' not in step:
                self.errors.append(f"{step_id}: modify_file requiere 'path'")
            if 'changes' not in step:
                self.errors.append(f"{step_id}: modify_file requiere 'changes'")
            else:
                for j, change in enumerate(step['changes']):
                    if 'find' not in change:
                        self.errors.append(f"{step_id}: change[{j}] requiere 'find'")
                    if 'replace' not in change:
                        self.errors.append(f"{step_id}: change[{j}] requiere 'replace'")
                        
        elif action == 'run_command':
            if 'command' not in step:
                self.errors.append(f"{step_id}: run_command requiere 'command'")
        
        # Validar verificaciones si existen
        if 'verify' in step:
            self._validate_verifications(step['verify'], step_id)
    
    def _validate_verifications(self, verifications: List, step_id: str):
        """Valida las verificaciones de un paso"""
        if not isinstance(verifications, list):
            self.errors.append(f"{step_id}: 'verify' debe ser una lista")
            return
        
        for i, verify in enumerate(verifications):
            if 'type' not in verify:
                self.errors.append(f"{step_id}: verify[{i}] requiere 'type'")
                continue
            
            vtype = verify['type']
            
            # Validar según tipo
            if vtype in ['file_exists', 'file_not_exists', 'file_contains']:
                if 'path' not in verify:
                    self.errors.append(f"{step_id}: {vtype} requiere 'path'")
                    
            if vtype == 'file_contains':
                if 'text' not in verify:
                    self.errors.append(f"{step_id}: file_contains requiere 'text'")
                    
            if vtype in ['command_succeeds', 'command_fails']:
                if 'command' not in verify:
                    self.errors.append(f"{step_id}: {vtype} requiere 'command'")


def main():
    """Función principal para testing"""
    if len(sys.argv) != 2:
        print("Uso: python preprocessor.py <plan.yaml>")
        sys.exit(1)
    
    preprocessor = PlanPreprocessor(sys.argv[1])
    plan, warnings, errors = preprocessor.process()
    
    print("=== CPMS3 Preprocessor ===")
    print(f"\nArchivo: {sys.argv[1]}")
    
    if errors:
        print(f"\n❌ Errores encontrados: {len(errors)}")
        for error in errors:
            print(f"   - {error}")
    else:
        print("\n✅ Sin errores")
    
    if warnings:
        print(f"\n⚠️  Advertencias: {len(warnings)}")
        for warning in warnings:
            print(f"   - {warning}")
    
    if not errors:
        print("\n✅ Plan procesado correctamente")
        
        # Opcionalmente, guardar plan procesado
        output_path = Path(sys.argv[1]).with_suffix('.processed.yaml')
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(plan, f, default_flow_style=False, allow_unicode=True)
        print(f"   Guardado en: {output_path}")
    
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()