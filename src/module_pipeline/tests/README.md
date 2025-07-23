# Tests del Module Pipeline 🧪

Este directorio contiene la suite completa de tests para el pipeline de procesamiento de noticias.

## 📁 Estructura de Tests (Reorganizada - Enero 2025)

```
tests/
├── unit/              # Tests unitarios para componentes individuales
│   ├── controller/    # Tests del controlador principal
│   ├── models/        # Tests de modelos Pydantic
│   ├── services/      # Tests de servicios (Groq, Supabase, etc.)
│   ├── utils/         # Tests de utilidades
│   └── pipeline/      # Tests de fases individuales del pipeline
│
├── integration/       # Tests de integración entre componentes
├── api/              # Tests de endpoints HTTP/FastAPI
├── performance/      # Tests de rendimiento y carga
├── functional/       # Tests funcionales del sistema completo
├── regression/       # Tests de regresión para bugs específicos
└── mocks/           # Fixtures y mocks compartidos
```

## 🚀 Ejecutar Tests

### Ejecutar todos los tests
```bash
# Desde el directorio tests/
python run_complete_test_suite.py

# O usando pytest directamente
pytest -v

# En Windows
ejecutar_tests_completos.bat
```

### Ejecutar tests por categoría
```bash
# Solo tests unitarios
pytest unit/ -v

# Solo tests de integración
pytest integration/ -v

# Solo tests de API
pytest api/ -v

# Tests de una fase específica
pytest unit/pipeline/test_fase_1_triaje.py -v
```

### Ejecutar con cobertura
```bash
# Generar reporte de cobertura
pytest --cov=../src --cov-report=html

# Ver cobertura en terminal
pytest --cov=../src --cov-report=term-missing
```

## 📋 Categorías de Tests

### Unit Tests (`unit/`)
Tests aislados de componentes individuales con dependencias mockeadas:
- **controller/**: Lógica del controlador y procesamiento de fragmentos
- **models/**: Validación de modelos Pydantic y transformaciones
- **services/**: Servicios externos (Groq API, Supabase, chunking, etc.)
- **utils/**: Utilidades como parsers, validadores, manejo de errores
- **pipeline/**: Fases individuales del pipeline (triaje, simplificación, etc.)

### Integration Tests (`integration/`)
Tests que verifican la interacción entre múltiples componentes:
- Flujo completo de las 7 fases
- Integración de chunking y consolidación
- Coordinación entre servicios
- Persistencia end-to-end

### API Tests (`api/`)
Tests de endpoints HTTP:
- `/procesar_articulo`
- `/procesar_fragmento`
- `/health` y `/metrics`
- Validación de requests/responses

### Performance Tests (`performance/`)
Tests de rendimiento y escalabilidad:
- Procesamiento asíncrono
- Concurrencia y paralelización
- Carga con múltiples artículos
- Métricas de rendimiento

### Functional Tests (`functional/`)
Tests del sistema completo en escenarios reales:
- Job tracking
- Sistema de monitoreo
- Recuperación de errores
- Detección de capas de persistencia

### Regression Tests (`regression/`)
Tests específicos para bugs resueltos:
- Error E012 y sus variantes
- Error E004 del pipeline
- Manejo integral de errores
- Casos edge específicos

## 🛠️ Configuración

### Variables de entorno para tests
```bash
# En .env.test o exportar antes de ejecutar
export ENVIRONMENT=test
export LOG_LEVEL=DEBUG
export GROQ_API_KEY=test_key
export SUPABASE_URL=http://localhost:54321
export SUPABASE_KEY=test_key
```

### Fixtures compartidos
Ver `conftest.py` para fixtures de pytest disponibles globalmente.

### Mocks
El directorio `mocks/` contiene modelos y datos de prueba reutilizables.

## 📊 Métricas de Calidad

- **Cobertura objetivo**: >80%
- **Tiempo máximo por test unitario**: 1s
- **Tiempo máximo por test de integración**: 10s
- **Tests de regresión**: Deben pasar siempre antes de merge

## 🔍 Debugging Tests

### Ejecutar test específico con output detallado
```bash
pytest path/to/test_file.py::test_function_name -vvs --log-cli-level=DEBUG
```

### Ejecutar con breakpoint
```python
# En el test
import pdb; pdb.set_trace()
```

### Ver logs durante ejecución
```bash
pytest -s --log-cli-level=INFO
```

## 🤝 Contribuir

1. Agregar tests para toda funcionalidad nueva
2. Mantener tests existentes pasando
3. Seguir convención de nombres: `test_<componente>_<funcionalidad>.py`
4. Documentar fixtures y mocks nuevos
5. Actualizar este README si se agregan nuevas categorías

## ⚠️ Notas Importantes

- Los tests de integración pueden requerir servicios externos (Groq, Supabase)
- Usar mocks para tests unitarios, no hacer llamadas reales a APIs
- Los tests de performance pueden ser lentos, excluir en CI si necesario
- Mantener independencia entre tests (no compartir estado)

**Última actualización**: Enero 2025
**Estado**: Reorganizado y estructurado
