# CPMS 3.0 - Sistema de Ejecución Determinista

## 🎯 Una Regla Suprema
**Ejecuta el plan EXACTAMENTE como está escrito. Sin interpretaciones. Sin decisiones.**

## 📁 Un Archivo Para Gobernarlos
Todo proyecto CPMS3 tiene UN SOLO archivo: `execution_plan.yaml`

## 🤖 Cómo Usar CPMS3

```bash
# Cargar y ejecutar proyecto
"Ejecuta el proyecto [nombre] con CPMS3"

# Claude ejecutará:
python /path/to/CPMS3/tools/runner.py /path/to/project/execution_plan.yaml
```

## ⚡ Principios Fundamentales

### 1. DETERMINISMO ABSOLUTO
- Cada acción produce EXACTAMENTE un resultado
- Sin "usa tu criterio" o "si es necesario"
- Input A → Output B, siempre

### 2. VERIFICACIÓN AUTOMÁTICA
- CERO input humano
- Cada paso se auto-verifica
- Falla = Rollback automático

### 3. STAGING OBLIGATORIO
```yaml
# Cambios peligrosos van a staging
action: delete_file
staging: true  # Mueve a .staging/deleted/ en vez de borrar
```

### 4. EJECUCIÓN ATÓMICA
- O se completa TODO o NADA
- Estado consistente siempre
- Rollback automático ante fallos

## 🚀 Estructura de execution_plan.yaml

```yaml
meta:
  id: "PROJECT-001"
  goal: "Descripción del resultado EXACTO esperado"
  version: "3.0"

config:
  base_path: "/absolute/path/to/code"
  staging_dir: ".staging"
  max_retries: 3

steps:
  - id: "STEP-001"
    action: "create_file"
    path: "src/main.py"
    content: |
      # Código EXACTO, sin placeholders
      def main():
          print("Hello CPMS3")
    verify:
      - type: "file_exists"
        path: "src/main.py"
      - type: "file_contains"
        path: "src/main.py"
        text: "def main():"
      - type: "syntax_valid"
        language: "python"
    on_fail: "abort"  # abort | retry | skip
```

## 🛡️ Acciones Disponibles

### Archivos
- `create_file`: Crear con contenido exacto
- `modify_file`: Buscar/reemplazar determinista
- `delete_file`: Mover a staging (no borrar real)
- `move_file`: Mover con verificación

### Código
- `run_command`: Ejecutar con timeout
- `run_test`: Ejecutar y validar salida
- `install_package`: Con versión exacta

### Verificación
- `file_exists`: Existe archivo
- `file_contains`: Contiene texto exacto
- `command_succeeds`: Exit code 0
- `test_passes`: Test específico pasa

## 🚫 PROHIBIDO en CPMS3

1. **NO** archivos separados (tasks.yaml, workflow.md, etc.)
2. **NO** "mejores prácticas" - solo lo especificado
3. **NO** decisiones autónomas - ejecutar literal
4. **NO** confirmaciones humanas
5. **NO** interpretaciones del plan

## ✅ Comandos Autorizados (Sin Confirmación)

```python
# El runner.py ejecuta automáticamente:
- Cualquier comando en 'run_command'
- Tests especificados
- Creación/modificación de archivos
- Operaciones de staging
- Rollbacks necesarios
```

## 🎯 Ejemplo Mínimo Funcional

```yaml
meta:
  id: "HELLO-CPMS3"
  goal: "Crear script Hello World"

steps:
  - action: "create_file"
    path: "hello.py"
    content: |
      print("Hello from CPMS3!")
    verify:
      - type: "file_exists"
        path: "hello.py"
      
  - action: "run_command"
    command: "python hello.py"
    expect_output: "Hello from CPMS3!"
```

## 🔥 Por Qué CPMS3 es Superior

1. **UN archivo** vs 5+ archivos
2. **100% automático** vs confirmaciones manuales
3. **Determinista** vs "usa tu criterio"
4. **Atómico** vs estados parciales
5. **Conciso** vs verboso

---
**RECUERDA**: Si no está en execution_plan.yaml, NO lo hagas.