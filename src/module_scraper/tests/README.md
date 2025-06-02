# 🧪 TESTING DIRECTORY - LA MÁQUINA DE NOTICIAS

## 📁 Estructura Organizada

```
tests/
├── 📋 reports/                    # Informes de testing
├── 📦 archive/                    # Tests de desarrollo (8 archivos)
├── ✅ test_real_schema_fixed.py   # [ACTIVO] Test integración Supabase
├── ✅ test_updated_client.py      # [ACTIVO] Test SupabaseClient actualizado
├── 📄 TEST_INVENTORY.md           # Inventario completo de tests
└── 📄 README.md                   # Este archivo
```

## 🎯 Tests Principales (Usar estos)

### **Para Verificación de Sistema:**
```bash
# Test integración completa con Supabase
python tests/test_real_schema_fixed.py

# Test SupabaseClient actualizado (sin tabla medios)
python tests/test_updated_client.py
```

### **Para Verificación de Componentes:**
```bash
# En directorio principal (../scripts/)
python scripts/run_playwright_tests.py     # Playwright
python scripts/test_crawl_once_fixed.py    # Prevención duplicados
python scripts/test_user_agents_fast.py    # User agents
python scripts/test_rate_limiting.py       # Rate limiting
```

## 📊 Estado del Sistema

| Componente | Test | Estado | Puntuación |
|------------|------|--------|------------|
| Supabase Integration | `test_real_schema_fixed.py` | ✅ | 100% |
| SupabaseClient | `test_updated_client.py` | ✅ | 99% |
| Playwright | `../scripts/run_playwright_tests.py` | ✅ | 100% |
| User Agents | `../scripts/test_user_agents_fast.py` | ✅ | 93.3% |
| Duplicates Prevention | `../scripts/test_crawl_once_fixed.py` | ✅ | 100% |
| Rate Limiting | `../scripts/test_rate_limiting.py` | ✅ | 85% |

## 📋 Documentación

- **`reports/TEST_RESULTS_SUMMARY.md`** - Informe completo de resultados
- **`TEST_INVENTORY.md`** - Inventario y estado de todos los tests

## 📦 Archive

El directorio `archive/` contiene 8 tests de desarrollo que fueron útiles durante la fase de descubrimiento y configuración inicial. Se mantienen para referencia histórica.

## 🔄 Flujo de Testing Recomendado

### **Pre-deployment:**
1. Ejecutar tests principales (`test_real_schema_fixed.py`, `test_updated_client.py`)
2. Verificar componentes core en `../scripts/`
3. Revisar logs para errores

### **Post-deployment:**
1. Ejecutar tests en servidor
2. Verificar conectividad Supabase  
3. Monitorear logs de producción

## 🚀 Sistema Listo para Producción

✅ Todos los tests críticos pasados  
✅ Integración Supabase verificada  
✅ Componentes anti-detección operativos  
✅ Documentación completa generada  

---

**Última actualización:** Junio 2, 2025  
**Sistema:** La Máquina de Noticias - Module Scraper  
**Status:** READY FOR PRODUCTION
