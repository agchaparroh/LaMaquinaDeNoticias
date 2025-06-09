# INSTRUCCIONES RÁPIDAS PARA EJECUTAR TESTS

## 🚨 PROBLEMA DETECTADO: Error en script batch

El script `menu_tests_FIXED.bat` tiene problemas de sintaxis. 

## ✅ SOLUCIONES INMEDIATAS

### OPCIÓN 1: Usar scripts individuales (RECOMENDADO)
```batch
# Test de verificación básica
tests\ejecutar_test_simple.bat

# Test completo del pipeline
tests\ejecutar_test_completo_FIXED.bat

# Tests unitarios
tests\ejecutar_test_unitarios_FIXED.bat

# Tests de integración
tests\ejecutar_test_integracion_FIXED.bat

# TODOS los tests
tests\ejecutar_TODOS_tests_FIXED.bat
```

### OPCIÓN 2: Ejecución directa con Python
```bash
cd C:\Users\DELL\Desktop\PruebaWindsurfAI\LaMaquinaDeNoticias\src\module_pipeline

# Test de verificación
python tests\test_simple_verificacion.py

# Test completo
python tests\test_pipeline_completo_FIXED.py

# Tests unitarios
python tests\test_fases_individuales_FIXED.py

# Tests de integración
python tests\test_integracion_errores_FIXED.py
```

### OPCIÓN 3: PowerShell (mejor manejo de errores)
```powershell
.\tests\ejecutar_tests_FIXED.ps1
```

## 🎯 RECOMENDACIÓN

1. **Empieza con el test simple**:
   ```batch
   tests\ejecutar_test_simple.bat
   ```
   Esto verificará que la configuración básica funciona.

2. **Si el test simple funciona, ejecuta el pipeline completo**:
   ```batch
   tests\ejecutar_test_completo_FIXED.bat
   ```

3. **Para ver todos los tests de una vez**:
   ```batch
   tests\ejecutar_TODOS_tests_FIXED.bat
   ```

## 🔧 TROUBLESHOOTING

Si encuentras errores:

1. **Error "No se esperaba ..."**: Usa los scripts individuales en lugar del menú
2. **Error de imports**: Ejecuta primero `test_simple_verificacion.py`
3. **Error de dependencias**: Instala con `pip install -r requirements.txt`

Los archivos `*_FIXED.py` están diseñados para funcionar sin problemas si la estructura del proyecto está correcta.
