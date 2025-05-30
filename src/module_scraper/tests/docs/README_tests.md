# Tests de Integración de Supabase

Este directorio contiene los tests de integración para la funcionalidad de Supabase en el módulo scraper.

## Configuración

### 1. Configurar Credenciales de Prueba

Los tests requieren un proyecto Supabase separado para pruebas. Las credenciales deben configurarse en el archivo `config/.env.test`:

```bash
# Copiar el archivo de ejemplo
cp config/.env.test.example config/.env.test

# Editar con las credenciales del proyecto de prueba
# IMPORTANTE: NO usar el proyecto de producción para tests
```

El archivo `config/.env.test` debe contener:
```env
SUPABASE_URL=https://tu-proyecto-test.supabase.co
SUPABASE_KEY=tu-anon-key
SUPABASE_SERVICE_ROLE_KEY=tu-service-role-key
SUPABASE_STORAGE_BUCKET=test-articulos-html-integration
LOG_LEVEL=DEBUG
```

### 2. Instalar Dependencias de Prueba

```bash
pip install pytest pytest-mock
```

## Ejecutar Tests

### Opción 1: Usar el script de prueba

```bash
python run_integration_tests.py
```

### Opción 2: Usar pytest directamente

```bash
# Desde el directorio module_scraper
pytest tests/test_supabase_integration.py -v -s

# Para ejecutar un test específico
pytest tests/test_supabase_integration.py::TestSupabaseIntegration::test_process_item_success_scenario -v -s
```

### Opción 3: Usar unittest

```bash
# Desde el directorio module_scraper
python -m unittest tests.test_supabase_integration -v
```

## Estructura de los Tests

### Tests Implementados

1. **test_process_item_success_scenario**
   - Verifica el flujo completo de procesamiento exitoso
   - Confirma almacenamiento en base de datos y storage

2. **test_process_item_missing_required_fields**
   - Prueba el manejo de items con campos faltantes
   - Verifica que se capture el error correctamente

3. **test_process_item_empty_html_content**
   - Prueba el manejo de contenido HTML vacío
   - Verifica comportamiento con contenido vacío

4. **test_process_item_database_error**
   - Simula errores de base de datos
   - Verifica manejo de excepciones

5. **test_process_item_storage_error**
   - Simula errores de almacenamiento
   - Verifica manejo de excepciones de storage

6. **test_duplicate_article_handling**
   - Prueba el manejo de artículos duplicados
   - Verifica que upsert funcione correctamente

### Limpieza Automática

Los tests incluyen métodos `setUpClass` y `tearDownClass` que:
- Crean un bucket de prueba si no existe
- Limpian los datos de prueba después de la ejecución
- Eliminan archivos del storage de prueba

## Notas Importantes

1. **Proyecto de Prueba Separado**: Siempre usa un proyecto Supabase dedicado para pruebas
2. **Limpieza Manual**: En caso de falla, puede ser necesaria limpieza manual del bucket
3. **Credenciales**: Nunca commits las credenciales reales al repositorio

## Depuración

Si los tests fallan:

1. Verificar que las credenciales en `config/.env.test` son correctas
2. Verificar que el proyecto Supabase está activo
3. Revisar los logs con `LOG_LEVEL=DEBUG`
4. Ejecutar tests individuales para aislar problemas

## Integración Continua

Para CI/CD, las credenciales deben configurarse como variables de entorno:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
