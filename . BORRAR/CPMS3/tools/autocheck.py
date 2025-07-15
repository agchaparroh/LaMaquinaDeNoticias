#!/usr/bin/env python3
"""
CPMS3 AutoCheck - Verificador 100% Automático
NO requiere input humano. Verificación determinista.
"""

import os
import sys
import subprocess
import re
import ast
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple

class AutoCheck:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.results = []
        
    def verify(self, verifications: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Ejecuta todas las verificaciones y retorna (success, detalles)"""
        all_passed = True
        details = []
        
        for check in verifications:
            check_type = check.get('type')
            passed, detail = self._run_check(check_type, check)
            
            self.results.append({
                'type': check_type,
                'passed': passed,
                'detail': detail
            })
            
            if not passed:
                all_passed = False
                details.append(f"❌ {check_type}: {detail}")
            else:
                details.append(f"✅ {check_type}: {detail}")
                
        return all_passed, details
    
    def _run_check(self, check_type: str, params: Dict) -> Tuple[bool, str]:
        """Ejecuta un check específico"""
        
        # Mapeo de tipos a métodos
        check_methods = {
            'file_exists': self._check_file_exists,
            'file_not_exists': self._check_file_not_exists,
            'file_contains': self._check_file_contains,
            'file_not_contains': self._check_file_not_contains,
            'syntax_valid': self._check_syntax_valid,
            'command_succeeds': self._check_command_succeeds,
            'command_fails': self._check_command_fails,
            'command_output_contains': self._check_command_output,
            'test_passes': self._check_test_passes,
            'test_output_contains': self._check_test_output,
            'no_test_failures': self._check_no_test_failures,
            'file_permissions': self._check_permissions,
            'process_running': self._check_process,
            'port_open': self._check_port,
            'api_endpoint_responds': self._check_api,
        }
        
        method = check_methods.get(check_type)
        if not method:
            return False, f"Tipo de check desconocido: {check_type}"
            
        try:
            return method(params)
        except Exception as e:
            return False, f"Error en check: {str(e)}"
    
    # ===== CHECKS DE ARCHIVOS =====
    
    def _check_file_exists(self, params: Dict) -> Tuple[bool, str]:
        path = self.base_path / params['path']
        exists = path.exists()
        return exists, f"Archivo {'existe' if exists else 'NO existe'}: {path}"
    
    def _check_file_not_exists(self, params: Dict) -> Tuple[bool, str]:
        path = self.base_path / params['path']
        not_exists = not path.exists()
        return not_exists, f"Archivo {'NO existe' if not_exists else 'todavía existe'}: {path}"
    
    def _check_file_contains(self, params: Dict) -> Tuple[bool, str]:
        path = self.base_path / params['path']
        text = params['text']
        
        if not path.exists():
            return False, f"Archivo no existe: {path}"
            
        content = path.read_text(encoding='utf-8')
        contains = text in content
        return contains, f"Archivo {'contiene' if contains else 'NO contiene'}: '{text[:50]}...'"
    
    def _check_file_not_contains(self, params: Dict) -> Tuple[bool, str]:
        path = self.base_path / params['path']
        text = params['text']
        
        if not path.exists():
            return False, f"Archivo no existe: {path}"
            
        content = path.read_text(encoding='utf-8')
        not_contains = text not in content
        return not_contains, f"Archivo {'NO contiene' if not_contains else 'todavía contiene'}: '{text[:50]}...'"
    
    # ===== CHECKS DE SINTAXIS =====
    
    def _check_syntax_valid(self, params: Dict) -> Tuple[bool, str]:
        path = self.base_path / params['path']
        language = params.get('language', 'python')
        
        if not path.exists():
            return False, f"Archivo no existe: {path}"
        
        if language == 'python':
            return self._check_python_syntax(path)
        elif language == 'javascript':
            return self._check_js_syntax(path)
        else:
            return False, f"Lenguaje no soportado: {language}"
    
    def _check_python_syntax(self, path: Path) -> Tuple[bool, str]:
        try:
            code = path.read_text(encoding='utf-8')
            ast.parse(code)
            return True, f"Sintaxis Python válida: {path.name}"
        except SyntaxError as e:
            return False, f"Error de sintaxis en línea {e.lineno}: {e.msg}"
    
    def _check_js_syntax(self, path: Path) -> Tuple[bool, str]:
        # Usar node para verificar sintaxis
        result = subprocess.run(
            ['node', '--check', str(path)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return True, f"Sintaxis JavaScript válida: {path.name}"
        else:
            return False, f"Error de sintaxis: {result.stderr}"
    
    # ===== CHECKS DE COMANDOS =====
    
    def _check_command_succeeds(self, params: Dict) -> Tuple[bool, str]:
        command = params['command']
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=self.base_path
        )
        success = result.returncode == 0
        return success, f"Comando {'exitoso' if success else 'falló'}: {command[:50]}..."
    
    def _check_command_fails(self, params: Dict) -> Tuple[bool, str]:
        command = params['command']
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=self.base_path
        )
        failed = result.returncode != 0
        return failed, f"Comando {'falló como esperado' if failed else 'NO falló'}: {command[:50]}..."
    
    def _check_command_output(self, params: Dict) -> Tuple[bool, str]:
        command = params['command']
        expected = params['contains']
        
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=self.base_path
        )
        
        output = result.stdout + result.stderr
        contains = expected in output
        return contains, f"Output {'contiene' if contains else 'NO contiene'}: '{expected[:50]}...'"
    
    # ===== CHECKS DE TESTS =====
    
    def _check_test_passes(self, params: Dict) -> Tuple[bool, str]:
        test_path = params.get('path', '')
        test_cmd = params.get('command', f'pytest {test_path}')
        
        result = subprocess.run(
            test_cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=self.base_path
        )
        
        passed = result.returncode == 0
        return passed, f"Tests {'pasaron' if passed else 'fallaron'}: {test_cmd}"
    
    def _check_test_output(self, params: Dict) -> Tuple[bool, str]:
        test_cmd = params['command']
        expected = params['text']
        
        result = subprocess.run(
            test_cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=self.base_path
        )
        
        output = result.stdout + result.stderr
        contains = expected in output
        return contains, f"Test output {'contiene' if contains else 'NO contiene'}: '{expected}'"
    
    def _check_no_test_failures(self, params: Dict) -> Tuple[bool, str]:
        test_cmd = params.get('command', 'pytest')
        
        result = subprocess.run(
            test_cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=self.base_path
        )
        
        output = result.stdout + result.stderr
        no_failures = 'failed' not in output.lower() and result.returncode == 0
        return no_failures, f"Tests {'sin fallos' if no_failures else 'CON FALLOS'}"
    
    # ===== CHECKS DE SISTEMA =====
    
    def _check_permissions(self, params: Dict) -> Tuple[bool, str]:
        path = self.base_path / params['path']
        expected = params['permissions']
        
        if not path.exists():
            return False, f"Archivo no existe: {path}"
        
        # Obtener permisos en octal
        stat_info = path.stat()
        current = oct(stat_info.st_mode)[-3:]
        
        matches = current == expected
        return matches, f"Permisos {'correctos' if matches else 'incorrectos'}: {current} {'==' if matches else '!='} {expected}"
    
    def _check_process(self, params: Dict) -> Tuple[bool, str]:
        process_name = params['name']
        
        result = subprocess.run(
            f"pgrep -f {process_name}",
            shell=True,
            capture_output=True
        )
        
        running = result.returncode == 0
        return running, f"Proceso '{process_name}' {'ejecutándose' if running else 'NO encontrado'}"
    
    def _check_port(self, params: Dict) -> Tuple[bool, str]:
        port = params['port']
        
        result = subprocess.run(
            f"nc -zv localhost {port}",
            shell=True,
            capture_output=True,
            text=True
        )
        
        open_port = result.returncode == 0
        return open_port, f"Puerto {port} {'abierto' if open_port else 'cerrado'}"
    
    def _check_api(self, params: Dict) -> Tuple[bool, str]:
        url = params['url']
        expected_status = params.get('expected_status', 200)
        
        try:
            import requests
            response = requests.get(url, timeout=5)
            success = response.status_code == expected_status
            return success, f"API {url}: status {response.status_code} {'==' if success else '!='} {expected_status}"
        except Exception as e:
            return False, f"API no responde: {str(e)}"
    
    def get_summary(self) -> str:
        """Retorna resumen de todos los checks"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r['passed'])
        
        summary = f"\n{'='*60}\n"
        summary += f"RESUMEN: {passed}/{total} checks pasaron\n"
        summary += f"{'='*60}\n"
        
        for result in self.results:
            emoji = "✅" if result['passed'] else "❌"
            summary += f"{emoji} {result['type']}: {result['detail']}\n"
            
        return summary


def main():
    """CLI para testing independiente"""
    if len(sys.argv) < 2:
        print("Uso: python autocheck.py <base_path> '<json_checks>'")
        sys.exit(1)
    
    base_path = sys.argv[1]
    checks_json = sys.argv[2] if len(sys.argv) > 2 else '[]'
    
    try:
        checks = json.loads(checks_json)
    except:
        print("Error parseando JSON de checks")
        sys.exit(1)
    
    checker = AutoCheck(base_path)
    success, details = checker.verify(checks)
    
    for detail in details:
        print(detail)
    
    print(checker.get_summary())
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()