# Test de Validación CPMS3

Este ejemplo demuestra las capacidades de validación y manejo de errores del Enhanced Runner.

## 🎯 Propósito

Este plan de ejecución contiene **errores intencionales** para mostrar cómo el sistema los detecta y reporta.

## 🧪 Casos de Prueba Incluidos

1. **Variables no resueltas** - `{undefined_location}`
2. **Archivo inexistente** - Intenta modificar un archivo que no existe
3. **Patrón no encontrado** - Busca texto con formato incorrecto
4. **Búsqueda normalizada** - Demuestra la búsqueda inteligente
5. **Comando inexistente** - Intenta ejecutar un comando que no existe
6. **Sintaxis inválida** - Crea archivo Python con errores de sintaxis
7. **Caso exitoso** - Demuestra que los casos válidos funcionan

## 🚀 Cómo Ejecutar

### 1. Con Runner Original (errores en tiempo de ejecución):
```bash
python ../../tools/runner.py execution_plan.yaml
```
Verás los errores a medida que ocurren durante la ejecución.

### 2. Con Enhanced Runner (validación previa):
```bash
python ../../tools/enhanced_runner.py execution_plan.yaml
```
Verás TODOS los problemas detectados ANTES de ejecutar.

### 3. Modo Dry-Run (solo validación):
```bash
python ../../tools/enhanced_runner.py execution_plan.yaml --dry-run
```
Solo valida sin ejecutar nada.

### 4. Modo Strict (rechaza variables no resueltas):
```bash
python ../../tools/enhanced_runner.py execution_plan.yaml --strict
```
Falla inmediatamente si encuentra `{undefined_location}`.

## 📊 Output Esperado

### Con Enhanced Runner:
```
📋 Fase 1: Preprocesamiento
----------------------------------------
❌ Errores de preprocesamiento: 1
   • Variable no resuelta: {undefined_location} en .steps[0].command

📋 Fase 2: Validación de precondiciones
----------------------------------------
❌ Errores de validación: 3
   • STEP-002: Archivo a modificar no existe: archivo_que_no_existe.py
   • STEP-006: Comando no encontrado: comando_imaginario
   • STEP-007: Error de sintaxis Python en línea 4: invalid syntax

⚠️  Advertencias: 2
   • STEP-004: Patrón encontrado solo con normalización
   • STEP-007: Archivo a crear ya existe: syntax_error.py
```

## 🔍 Lecciones Aprendidas

1. **Validación temprana**: Detecta problemas antes de hacer cambios
2. **Mensajes claros**: Cada error incluye contexto útil
3. **Búsqueda inteligente**: Maneja variaciones de espacios/formato
4. **Modo strict**: Garantiza que no queden variables sin resolver
5. **Staging seguro**: Los archivos "borrados" van a `.cpms3_staging/deleted/`

## 🛠️ Personalización

Puedes modificar este plan para probar otros escenarios:
- Añadir más variables no definidas
- Probar con diferentes tipos de archivos
- Experimentar con patrones de búsqueda complejos
- Verificar el comportamiento del rollback

---

💡 **Tip**: Este ejemplo es perfecto para entender cómo CPMS3 maneja los errores y por qué el Enhanced Runner es la forma recomendada de ejecutar planes.