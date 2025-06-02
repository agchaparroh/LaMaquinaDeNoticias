# 📁 INVENTARIO DE ARCHIVOS DE TEST

## 🗂️ Estructura Actual

```
tests/
├── reports/                     # 📋 Informes y documentación
│   └── TEST_RESULTS_SUMMARY.md  # Informe principal de resultados
├── archive/                     # 📦 Tests archivados (mantener para referencia)
│   ├── test_supabase_simple.py    # Test básico de Supabase
│   ├── test_supabase_direct.py    # Test directo de conexión
│   ├── test_supabase_discovery.py # Descubrimiento de estructura BD
│   ├── test_table_structure.py    # Análisis estructura tablas
│   ├── test_service_role.py       # Test con service role key
│   ├── test_exact_structure.py    # Test estructura exacta
│   ├── test_direct_insertion.py   # Test inserción directa
│   └── test_real_schema.py        # Test schema real (primera versión)
├── test_real_schema_fixed.py   # ✅ Test final schema Supabase
├── test_updated_client.py       # ✅ Test SupabaseClient actualizado
└── __init__.py
```

## 📊 Estado de Archivos

### ✅ **ARCHIVOS ACTIVOS (Mantener)**
- `test_real_schema_fixed.py` - **CRÍTICO**: Verificación schema Supabase
- `test_updated_client.py` - **CRÍTICO**: Test SupabaseClient sin medios
- `reports/TEST_RESULTS_SUMMARY.md` - **DOCUMENTACIÓN**: Informe principal

### 📦 **ARCHIVOS ARCHIVADOS (Referencia)**
- `archive/test_supabase_*.py` - Tests de descubrimiento y desarrollo
- `archive/test_*_structure.py` - Tests de análisis de estructura
- `archive/test_direct_*.py` - Tests de inserción directa

### 🗑️ **ARCHIVOS PARA ELIMINAR (Opcionales)**
- Ninguno - todos tienen valor histórico o de referencia

## 🔧 Scripts en Directorio Principal

### ✅ **SCRIPTS PRINCIPALES (src/module_scraper/scripts/)**
- `verify_config.py` - Verificación configuraciones básicas
- `verify_logging_fixed.py` - Test sistema de logging  
- `run_playwright_tests.py` - Tests Playwright completos
- `test_user_agents_fast.py` - Test rotación user agents
- `test_rate_limiting.py` - Test políticas rate limiting
- `test_crawl_once_fixed.py` - Test prevención duplicados

## 📋 Uso Recomendado

### **Para Testing de Regresión:**
```bash
# Tests críticos de verificación
python tests/test_real_schema_fixed.py
python tests/test_updated_client.py

# Tests de componentes principales  
python scripts/run_playwright_tests.py
python scripts/test_crawl_once_fixed.py
```

### **Para Debugging:**
```bash
# Consultar archivos en archive/ para casos específicos
python tests/archive/test_supabase_simple.py
```

### **Para Documentación:**
- Consultar `reports/TEST_RESULTS_SUMMARY.md` para estado completo
- Revisar este archivo para inventario de tests disponibles

## 🎯 Próximos Tests Recomendados

### **A Desarrollar:**
1. `test_content_extraction.py` - Test extracción contenido real
2. `test_spider_specific.py` - Test spiders por medio específico  
3. `test_production_pipeline.py` - Test pipeline completo end-to-end
4. `test_error_recovery.py` - Test recuperación de errores
5. `test_performance_load.py` - Test carga y rendimiento

### **Para Integración Continua:**
1. `test_regression_suite.py` - Suite completa de regresión
2. `test_deployment_verification.py` - Verificación post-deployment
3. `test_monitoring_alerts.py` - Test sistema de alertas

---

**Última actualización:** Junio 2, 2025  
**Mantenido por:** Testing Session  
**Propósito:** Organización y documentación de tests del sistema
