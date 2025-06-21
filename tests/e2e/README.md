# Tests End-to-End (E2E)

Esta carpeta contiene los tests end-to-end que validan flujos completos del sistema "La Máquina de Noticias".

## 📁 Estructura

```
tests/e2e/
├── __init__.py
├── test_article_minimal_flow.py      # Flujo mínimo de un artículo
├── test_editorial_feedback_flow.py   # Flujo de feedback editorial
└── test_multiple_articles_flow.py    # Procesamiento múltiple
```

## 🧪 Tests Implementados

### 1. test_article_minimal_flow.py
Valida el recorrido completo de un artículo:
- **Scraper** → genera archivo .json.gz
- **Connector** → lee y envía a Pipeline
- **Pipeline** → procesa y extrae hechos
- **Database** → almacena en Supabase
- **Dashboard** → muestra artículo procesado

**Tests incluidos:**
- `test_article_minimal_flow()` - Flujo básico exitoso
- `test_article_minimal_flow_with_timing()` - Con medición de tiempos

### 2. test_editorial_feedback_flow.py
Valida el flujo de feedback editorial:
- Editor ve artículo con importancia automática
- Editor ajusta importancia via API
- Backend actualiza base de datos
- Dashboard refleja cambios
- Feedback se registra para mejora del algoritmo

**Tests incluidos:**
- `test_editorial_feedback_flow()` - Flujo básico de feedback
- `test_multiple_feedback_changes()` - Múltiples cambios secuenciales
- `test_feedback_validation_errors()` - Manejo de errores

### 3. test_multiple_articles_flow.py
Valida procesamiento concurrente:
- Scraper genera batch de 5+ artículos
- Connector valida todos
- Pipeline procesa en paralelo
- Dashboard muestra todos correctamente

**Tests incluidos:**
- `test_multiple_articles_flow()` - 5 artículos simultáneos
- `test_multiple_articles_with_failures()` - Manejo de fallos
- `test_concurrent_load_stress()` - Test de carga con múltiples batches

## 🚀 Ejecutar Tests

### Todos los tests E2E:
```bash
# Desde la carpeta tests/
pytest e2e/ -v -s

# O usando el script
python run_e2e_tests.py
```

### Un test específico:
```bash
pytest e2e/test_article_minimal_flow.py -v -s
```

### Con más detalle:
```bash
pytest e2e/ -v -s --tb=long
```

## 📊 Métricas Capturadas

Los tests E2E capturan:
- **Tiempos de procesamiento** por etapa
- **Tasas de éxito/fallo**
- **Throughput** (artículos/segundo)
- **Integridad de datos** en el flujo

## ⚠️ Consideraciones

1. **Mocks vs Real**: Los tests usan mocks para simular componentes. Para tests contra el sistema real, ajustar las implementaciones.

2. **Timeouts**: Los tests asumen tiempos de respuesta rápidos. En un sistema real, ajustar timeouts.

3. **Concurrencia**: Los tests de carga usan ThreadPoolExecutor. El sistema real puede usar asyncio o diferentes estrategias.

4. **Base de Datos**: Los tests simulan Supabase. Para tests reales, usar una BD de pruebas.

## 🔧 Extender Tests

Para agregar nuevos tests E2E:

1. Crear archivo `test_nuevo_flujo.py`
2. Implementar clase que simule el flujo
3. Agregar validaciones en cada etapa
4. Documentar el flujo testeado

Ejemplo:
```python
class NuevoFlujoE2E:
    def __init__(self):
        # Inicializar datos de prueba
        pass
    
    def etapa_1(self):
        # Simular primera etapa
        pass
    
    def etapa_2(self):
        # Simular segunda etapa
        pass

def test_nuevo_flujo():
    flow = NuevoFlujoE2E()
    # Ejecutar y validar flujo
```
