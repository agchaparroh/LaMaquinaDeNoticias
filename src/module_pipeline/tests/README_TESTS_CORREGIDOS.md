# TESTS DEL PIPELINE - DOCUMENTACIÓN ACTUALIZADA

## 🚨 PROBLEMAS DETECTADOS Y CORREGIDOS

### ❌ Problemas principales en los tests originales:

1. **Imports incorrectos y paths malformados**
   - Rutas relativas incorrectas al directorio `src`
   - Referencias a módulos inexistentes
   - Imports circulares

2. **Configuración de entorno deficiente**
   - Variables de entorno no configuradas antes de imports
   - Configuración de logging después de importar módulos que lo usan
   - Paths de Python mal configurados

3. **Mock patterns incorrectos**
   - Mocks que no coinciden con las firmas reales de las funciones
   - Referencias a funciones que no existen
   - Contextos de mock mal configurados

4. **Manejo de excepciones inconsistente**
   - Excepciones no capturadas correctamente
   - Fallbacks no implementados
   - Flujo de errores mal diseñado

5. **Referencias a clases inexistentes**
   - Imports de modelos que no están definidos
   - Uso de atributos inexistentes
   - Estructura de datos inconsistente

## ✅ VERSIONES CORREGIDAS

### 📁 Archivos nuevos (FUNCIONALES):

1. **`test_pipeline_completo_FIXED.py`**
   - ✅ Configuración de entorno antes de imports
   - ✅ Mocks realistas y funcionales
   - ✅ Manejo robusto de errores
   - ✅ Validaciones completas del pipeline

2. **`test_fases_individuales_FIXED.py`**
   - ✅ Tests unitarios independientes
   - ✅ Datos de entrada realistas
   - ✅ Validaciones específicas por fase
   - ✅ Mocks simplificados pero efectivos

3. **`test_integracion_errores_FIXED.py`**
   - ✅ Casos edge (texto vacío, muy corto, irrelevante)
   - ✅ Simulación de errores de API
   - ✅ Tests de coherencia de datos
   - ✅ Validación de fallbacks

4. **`menu_tests_FIXED.bat`**
   - ✅ Menú mejorado con opciones de comparación
   - ✅ Mejor manejo de rutas
   - ✅ Opciones para ejecutar versiones originales vs corregidas

5. **`ejecutar_tests_FIXED.ps1`**
   - ✅ Script PowerShell con manejo de errores
   - ✅ Verificación de dependencias
   - ✅ Reportes detallados de resultados

## 🔧 PRINCIPALES CORRECCIONES APLICADAS

### 1. Configuración de Entorno
```python
# ❌ ANTES (incorrecto)
from utils.fragment_processor import FragmentProcessor
os.environ["GROQ_API_KEY"] = "test"

# ✅ DESPUÉS (corregido)
os.environ["GROQ_API_KEY"] = "test"
sys.path.insert(0, str(src_path))
from utils.fragment_processor import FragmentProcessor
```

### 2. Mock Patterns
```python
# ❌ ANTES (incorrecto)
with mock.patch('fase_1_triaje.llamar_groq') as mock_groq:
    # función inexistente

# ✅ DESPUÉS (corregido)
with mock.patch('pipeline.fase_1_triaje._llamar_groq_api_triaje') as mock_groq:
    mock_groq.return_value = ("prompt", "respuesta_realista")
```

### 3. Manejo de Resultados
```python
# ❌ ANTES (incorrecto)
assert resultado.puntuacion > 0  # atributo inexistente

# ✅ DESPUÉS (corregido)
assert resultado.puntuacion_triaje is not None
assert isinstance(resultado.es_relevante, bool)
```

## 🎯 CÓMO EJECUTAR LOS TESTS CORREGIDOS

### Opción 1: Menu interactivo (Windows)
```batch
tests\menu_tests_FIXED.bat
```

### Opción 2: PowerShell (recomendado)
```powershell
.\tests\ejecutar_tests_FIXED.ps1
```

### Opción 3: Ejecución directa
```bash
# Test completo
python tests\test_pipeline_completo_FIXED.py

# Tests unitarios  
python tests\test_fases_individuales_FIXED.py

# Tests de integración
python tests\test_integracion_errores_FIXED.py
```

## 📊 COBERTURA DE TESTS

### Tests del Pipeline Completo:
- ✅ Ejecución secuencial de las 4 fases
- ✅ Coherencia de IDs entre fases
- ✅ Preservación de datos
- ✅ Integración con FragmentProcessor

### Tests Unitarios:
- ✅ Fase 1: Triaje y preprocesamiento
- ✅ Fase 2: Extracción de hechos y entidades
- ✅ Fase 3: Extracción de citas y datos cuantitativos
- ✅ Fase 4: Normalización y relaciones

### Tests de Integración:
- ✅ Casos edge (texto vacío, muy corto, irrelevante)
- ✅ Manejo de errores de API
- ✅ Respuestas malformadas del LLM
- ✅ Coherencia de datos entre fases
- ✅ Fallbacks y recuperación de errores

## 🛠️ DEPENDENCIAS VERIFICADAS

### Requeridas para los tests:
- ✅ Python 3.8+
- ✅ Todas las dependencias del `requirements.txt`
- ✅ Variables de entorno mockeadas automáticamente
- ✅ No requiere APIs reales (todo mockeado)

### Módulos internos verificados:
- ✅ `utils.fragment_processor`
- ✅ `pipeline.fase_1_triaje`
- ✅ `pipeline.fase_2_extraccion`
- ✅ `pipeline.fase_3_citas_datos`
- ✅ `pipeline.fase_4_normalizacion`
- ✅ `models.procesamiento`

## 🎉 RESULTADOS ESPERADOS

Al ejecutar los tests corregidos, deberías ver:

```
🧪 TEST DEL PIPELINE COMPLETO DE PROCESAMIENTO
===========================================================

🔍 FASE 1: TRIAJE Y PREPROCESAMIENTO
✅ Resultado: RELEVANTE
✅ Decisión: PROCESAR
✅ Categoría: POLÍTICA
✅ Puntuación: 24/25

📊 FASE 2: EXTRACCIÓN DE HECHOS Y ENTIDADES
✅ Hechos extraídos: 3
✅ Entidades extraídas: 3

💬 FASE 3: EXTRACCIÓN DE CITAS Y DATOS CUANTITATIVOS
✅ Citas textuales: 1
✅ Datos cuantitativos: 3

🔗 FASE 4: NORMALIZACIÓN Y RELACIONES
✅ Estado: COMPLETADO

🎉 ¡TEST EXITOSO! El pipeline funciona correctamente.
```

## 📝 NOTAS IMPORTANTES

1. **Los tests originales pueden seguir fallando** - usar las versiones `_FIXED`
2. **Todos los tests usan mocks** - no requieren APIs reales
3. **Los datos de prueba son realistas** - basados en casos de uso reales
4. **Los tests son independientes** - pueden ejecutarse por separado
5. **Incluyen validaciones exhaustivas** - verifican estructura y coherencia

## 🔍 PARA DEBUGGING

Si encuentras errores, verifica:

1. **Variables de entorno**: Los tests las configuran automáticamente
2. **Paths de Python**: Verificados automáticamente en cada test
3. **Dependencias**: Usa el verificador incluido en el PowerShell
4. **Estructura de directorios**: Debe coincidir con la documentada

Los tests corregidos son **completamente funcionales** y **no deberían fallar** si la estructura del proyecto está correcta.
