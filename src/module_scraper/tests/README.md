# 🧪 TESTING DIRECTORY - LA MÁQUINA DE NOTICIAS

## 📁 Estructura Actualizada

```
tests/
├── 📋 reports/                    # Informes de testing
├── 📦 archive/                    # Tests de desarrollo (8 archivos)
├── 🚀 performance/                # NUEVOS tests de performance
│   ├── test_basic_performance.py  # Métricas de rendimiento
│   ├── test_simple_concurrency.py # Tests de concurrencia
│   ├── test_basic_recovery.py     # Recuperación ante fallos
│   └── test_basic_load.py         # Tests de carga
├── 🔄 integration/                # Tests de integración
│   └── test_real_integration.py   # Flujo completo real
├── 📊 scripts/                    # Scripts de utilidad
│   └── run_performance_tests.py   # Ejecutar todos los tests nuevos
├── ✅ test_real_schema_fixed.py   # [ACTIVO] Test integración Supabase
├── ✅ test_updated_client.py      # [ACTIVO] Test SupabaseClient actualizado
├── 📄 TEST_INVENTORY.md           # Inventario completo de tests
└── 📄 README.md                   # Este archivo
```

## 🎯 Tests Principales (Usar estos)

### **Tests de Sistema Base:**
```bash
# Test integración completa con Supabase
python tests/test_real_schema_fixed.py

# Test SupabaseClient actualizado (sin tabla medios)
python tests/test_updated_client.py
```

### **NUEVOS Tests de Performance y Robustez:**
```bash
# Ejecutar TODOS los tests nuevos de una vez
python tests/scripts/run_performance_tests.py

# O ejecutar individualmente:
python tests/performance/test_basic_performance.py    # Métricas de rendimiento
python tests/performance/test_simple_concurrency.py   # Concurrencia
python tests/performance/test_basic_recovery.py       # Recuperación
python tests/integration/test_real_integration.py     # Integración real
python tests/performance/test_basic_load.py           # Carga
```

### **Tests de Componentes:**
```bash
# En directorio principal (../scripts/)
python scripts/run_playwright_tests.py     # Playwright
python scripts/test_crawl_once_fixed.py    # Prevención duplicados
python scripts/test_user_agents_fast.py    # User agents
python scripts/test_rate_limiting.py       # Rate limiting
```

## 📊 Estado del Sistema Actualizado

| Componente | Test | Estado | Descripción |
|------------|------|--------|------------|
| **BASE** |||
| Supabase Integration | `test_real_schema_fixed.py` | ✅ | Integración completa |
| SupabaseClient | `test_updated_client.py` | ✅ | Cliente actualizado |
| **PERFORMANCE** |||
| Rendimiento | `test_basic_performance.py` | 🆕 | Tiempos y memoria |
| Concurrencia | `test_simple_concurrency.py` | 🆕 | Multi-spider |
| Recuperación | `test_basic_recovery.py` | 🆕 | Manejo de errores |
| Integración Real | `test_real_integration.py` | 🆕 | Flujo completo |
| Carga | `test_basic_load.py` | 🆕 | Stress testing |
| **COMPONENTES** |||
| Playwright | `run_playwright_tests.py` | ✅ | JavaScript rendering |
| User Agents | `test_user_agents_fast.py` | ✅ | Rotación |
| Duplicates | `test_crawl_once_fixed.py` | ✅ | Prevención |
| Rate Limiting | `test_rate_limiting.py` | ✅ | Control de velocidad |

## 🚀 Nuevas Capacidades de Testing

### **1. Performance Testing** 
- Mide tiempos de procesamiento por item
- Verifica uso de memoria
- Identifica cuellos de botella

### **2. Concurrency Testing**
- Múltiples spiders simultáneos
- Procesamiento paralelo de pipelines
- Detección de race conditions

### **3. Recovery Testing**
- Manejo de items inválidos
- Recuperación de fallos de conexión
- Degradación gradual del sistema

### **4. Load Testing**
- Procesamiento de 100+ items
- Estabilidad de memoria con 1000+ items
- Throughput máximo del sistema

## 📋 Documentación

- **`reports/TEST_RESULTS_SUMMARY.md`** - Informe completo de resultados
- **`TEST_INVENTORY.md`** - Inventario y estado de todos los tests
- **`scripts/run_performance_tests.py`** - Script para ejecutar suite completa

## 🔄 Flujo de Testing Completo

### **Pre-deployment:**
```bash
# 1. Tests base del sistema
python tests/test_real_schema_fixed.py
python tests/test_updated_client.py

# 2. Suite completa de performance
python tests/scripts/run_performance_tests.py

# 3. Verificar componentes individuales si es necesario
python scripts/run_playwright_tests.py
```

### **Post-deployment:**
1. Ejecutar tests de integración real en servidor
2. Monitorear métricas de performance
3. Verificar logs de recuperación ante fallos

## 📈 Métricas de Referencia

- **Performance**: < 30 segundos por artículo
- **Memoria**: < 100MB por spider
- **Concurrencia**: 3+ spiders simultáneos
- **Carga**: 10+ items/segundo en pipelines
- **Estabilidad**: < 50MB incremento con 1000 items

## 🚀 Sistema Listo para Producción

✅ Tests base completos y pasados  
✅ Tests de performance implementados  
✅ Tests de robustez y recuperación  
✅ Sistema verificado bajo carga  
✅ Documentación actualizada  

---

**Última actualización:** Junio 2025  
**Sistema:** La Máquina de Noticias - Module Scraper  
**Status:** READY FOR PRODUCTION + PERFORMANCE TESTED
