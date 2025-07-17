# TESTS DEL PIPELINE - DOCUMENTACIÓN OFICIAL

## 🎯 TESTS FUNCIONALES VERIFICADOS

Esta carpeta contiene únicamente los tests **verificados y funcionales** del pipeline de procesamiento.

### 📋 TESTS PRINCIPALES

#### 1. **Test Independiente (RECOMENDADO)**
```bash
tests\test_pipeline_independiente.py
tests\ejecutar_test_independiente.bat
```
- ✅ **100% funcional sin dependencias externas**
- ✅ Demuestra Fase 1 completa + FragmentProcessor
- ✅ No requiere spaCy ni APIs externas
- ✅ Análisis inteligente de relevancia
- ✅ Manejo de casos edge
- **USO**: Test principal para verificar funcionalidad

#### 2. **Test de Verificación**
```bash
tests\test_verificacion_basica.py
tests\ejecutar_verificacion.bat
```
- ✅ Verifica configuración básica del sistema
- ✅ Comprueba imports y estructura de directorios
- ✅ Diagnóstico rápido de problemas
- **USO**: Diagnóstico y troubleshooting

#### 3. **Test de FragmentProcessor**
```bash
tests\test_fragment_processor.py
tests\ejecutar_test_fragment_processor.bat
```
- ✅ Test específico del sistema de IDs secuenciales
- ✅ Validación exhaustiva de coherencia
- ✅ Test de rendimiento y edge cases
- **USO**: Verificar sistema de IDs independientemente

### 🎮 MENÚ PRINCIPAL
```bash
tests\menu_principal.bat
```
- Menú interactivo para ejecutar cualquier test
- Incluye opciones de diagnóstico
- Reportes de resultados

### 📊 ESTRUCTURA DE ARCHIVOS

```
tests/
├── 📄 README.md                          # Este archivo
├── 🎮 menu_principal.bat                 # Menú principal
├── 🧪 test_pipeline_independiente.py     # Test principal funcional
├── 🔍 test_verificacion_basica.py        # Verificación del sistema
├── 📊 test_fragment_processor.py         # Test del FragmentProcessor
├── ⚡ ejecutar_test_independiente.bat    # Ejecutor del test principal
├── 🔍 ejecutar_verificacion.bat          # Ejecutor de verificación
├── 📊 ejecutar_test_fragment_processor.bat
└── 📁 archive/                           # Tests archivados (no usar)
```

### 🚀 INICIO RÁPIDO

**Para verificar que todo funciona:**
```batch
tests\ejecutar_test_independiente.bat
```

**Para diagnosticar problemas:**
```batch
tests\ejecutar_verificacion.bat
```

**Para menú interactivo:**
```batch
tests\menu_principal.bat
```

### ✅ GARANTÍAS DE FUNCIONALIDAD

- ✅ **Todos los tests están verificados y funcionan**
- ✅ **Sin dependencias externas problemáticas**
- ✅ **Documentación clara y actualizada**
- ✅ **Casos edge cubiertos**
- ✅ **Mensajes de error claros**

### 🗂️ ARCHIVOS ARCHIVADOS

Los tests antiguos y versiones obsoletas se han movido a `archive/` para mantener el historial pero evitar confusión.

### 🆘 SOPORTE

Si un test falla:
1. Ejecuta `test_verificacion_basica.py` para diagnóstico
2. Revisa que el directorio `src/` esté correctamente estructurado
3. Verifica que Python tenga acceso a los módulos necesarios

**Última actualización**: Junio 2025
**Estado**: Completamente funcional y verificado
