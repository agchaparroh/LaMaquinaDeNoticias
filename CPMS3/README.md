# CPMS3 - Sistema de Ejecución Determinista

## 🚀 ¿Qué es CPMS3?

CPMS3 es la evolución del sistema CPMS, diseñado para ejecutar proyectos complejos de forma **100% automática y determinista**.

### Características Principales:
- **UN archivo** (`execution_plan.yaml`) contiene TODO el proyecto
- **CERO intervención humana** - Verificación completamente automática
- **Ejecución determinista** - Mismo input = Mismo output, siempre
- **Staging seguro** - Cambios peligrosos van a staging, no se ejecutan directamente
- **Rollback automático** - Si algo falla, restaura el estado anterior

## 📁 Estructura

```
CPMS3/
├── CPMS3.md           # Filosofía y reglas del sistema
├── README.md          # Este archivo
├── templates/         # Plantilla para nuevos proyectos
│   └── execution_plan.yaml
├── tools/             # Herramientas del sistema
│   ├── runner.py      # Ejecutor principal (mejorado con modo strict)
│   ├── enhanced_runner.py # 🆕 Runner mejorado con validación completa
│   ├── preprocessor.py    # 🆕 Preprocesador de planes
│   ├── validator.py       # 🆕 Validador de precondiciones
│   ├── autocheck.py   # Verificador automático
│   └── staging.py     # Gestor de cambios seguros
├── examples/          # Ejemplos funcionales
│   └── hello-world/   # Proyecto de demostración
└── projects/          # Tus proyectos aquí
```

## 🎯 Uso Rápido

### Para Claude:
```
"Ejecuta el proyecto [nombre] con CPMS3"
```

### Manualmente:
```bash
# Opción 1: Runner original (rápido, sin validación previa)
python /path/to/CPMS3/tools/runner.py /path/to/project/execution_plan.yaml

# Opción 2: Enhanced Runner (RECOMENDADO - con validación completa)
python /path/to/CPMS3/tools/enhanced_runner.py /path/to/project/execution_plan.yaml
```

## 🚨 NUEVO: Enhanced Runner (v2.0)

El **Enhanced Runner** es la forma recomendada de ejecutar planes CPMS3. Añade una capa de validación exhaustiva ANTES de ejecutar cualquier cambio:

### Características:
- ✅ **Preprocesamiento**: Resuelve todas las variables antes de ejecutar
- ✅ **Validación completa**: Verifica archivos, patrones y comandos
- ✅ **Modo strict**: Falla si quedan variables sin resolver
- ✅ **Búsqueda inteligente**: Maneja variaciones de espacios/saltos de línea
- ✅ **Mensajes mejorados**: Errores con contexto y sugerencias

### Uso del Enhanced Runner:
```bash
# Ejecución básica con validación
python enhanced_runner.py execution_plan.yaml

# Modo strict (falla si hay variables no resueltas)
python enhanced_runner.py execution_plan.yaml --strict

# Ejecutar incluso con advertencias
python enhanced_runner.py execution_plan.yaml --force

# Solo validar sin ejecutar (dry-run)
python enhanced_runner.py execution_plan.yaml --dry-run

# Guardar plan procesado y reporte
python enhanced_runner.py execution_plan.yaml --save-processed --save-report
```

### Fases de Ejecución:
1. **Preprocesamiento**: Resuelve variables y normaliza patrones
2. **Validación**: Verifica que todo esté listo para ejecutar
3. **Ejecución**: Lanza el runner con el plan validado

### Ejemplo de Output:
```
🚀 CPMS3 Enhanced Runner v2.0
======================================================================

📋 Fase 1: Preprocesamiento
----------------------------------------
✅ Plan preprocesado correctamente
⚠️  Advertencias: 2
   • Step STEP-004: Patrón normalizado (espacios/saltos de línea)
   • Step STEP-011: Patrón normalizado (espacios/saltos de línea)

📋 Fase 2: Validación de precondiciones
----------------------------------------
✅ Todas las validaciones pasaron

📋 Fase 3: Ejecución del plan
----------------------------------------
🚀 Iniciando ejecución...
```

## 📝 Crear un Proyecto CPMS3

1. Copia `templates/execution_plan.yaml` a tu proyecto
2. Define los pasos exactos a ejecutar
3. Incluye verificaciones para cada paso
4. Ejecuta con el runner

## 🔍 Ejemplo Completo

Ver `examples/hello-world/execution_plan.yaml` para un ejemplo funcional que:
- Crea estructura de proyecto Python
- Implementa código con tests
- Ejecuta verificaciones automáticas
- Demuestra staging seguro

## ⚡ Ventajas sobre CPMS Original

| CPMS Original | CPMS3 |
|---------------|-------|
| 5+ archivos (project.yaml, tasks.yaml, etc.) | 1 archivo (execution_plan.yaml) |
| Requiere confirmación humana | 100% automático |
| "Usa tu mejor criterio" | Ejecución determinista exacta |
| Verificación manual con input | Verificación automática completa |
| Sin manejo de errores | Rollback automático |

## 🛡️ Seguridad

- **Staging obligatorio** para operaciones destructivas
- **Backups automáticos** antes de modificaciones
- **Rollback** si algo falla
- **Sin borrado real** - Los archivos se mueven a `.cpms3_staging/deleted/`

## 🤖 Para Desarrolladores

### Acciones Disponibles:
- `create_file` - Crear archivo con contenido exacto
- `modify_file` - Buscar/reemplazar determinista
- `delete_file` - Mover a staging (seguro)
- `run_command` - Ejecutar con timeout
- `run_test` - Ejecutar y validar tests

### Verificaciones Disponibles:
- `file_exists` / `file_not_exists`
- `file_contains` / `file_not_contains`
- `syntax_valid` - Validar sintaxis Python/JS
- `command_succeeds` / `command_fails`
- `test_passes` - Tests exitosos

## 🔧 Solución de Problemas

### Error: "Variable no resuelta: {variable_name}"
**Causa**: Una variable en el plan no está definida en `constants` o `config`.
**Solución**: 
- Añade la variable a la sección `constants` del plan
- O usa `--dry-run` para ver todas las variables no resueltas

### Error: "Texto no encontrado"
**Causa**: El patrón de búsqueda no coincide exactamente con el archivo.
**Solución**:
- El Enhanced Runner normaliza espacios automáticamente
- Verifica saltos de línea y espacios extras
- Usa el mensaje de error que sugiere texto similar

### Error: "Archivo no existe"
**Causa**: Intentas modificar un archivo que no existe.
**Solución**:
- Verifica la ruta del archivo
- Asegúrate de que los pasos anteriores crearon el archivo
- Usa rutas relativas al `base_path`

### Advertencia: "Comando no encontrado"
**Causa**: El comando no está instalado o no está en el PATH.
**Solución**:
- Instala el comando necesario
- Usa la ruta completa al ejecutable
- Verifica que el comando funciona manualmente primero

## 📊 Filosofía

1. **Determinismo**: Cada acción produce exactamente un resultado
2. **Automatización**: Cero decisiones humanas durante ejecución
3. **Seguridad**: Nunca modificar/borrar sin posibilidad de rollback
4. **Simplicidad**: Un archivo, una verdad
5. **Fail-Fast**: Detectar problemas antes de hacer cambios

---

**CPMS3 v2.0**: Ejecución determinista con validación inteligente.