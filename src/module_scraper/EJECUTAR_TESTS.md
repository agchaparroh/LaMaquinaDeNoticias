# Module Scraper - Ejecución de Tests

## Configuración Rápida

### 1. Preparación del entorno

```bash
# Navegar al directorio del módulo
cd "C:\Users\DELL\Desktop\Prueba con Windsurf AI\La Máquina de Noticias\src\module_scraper"

# Activar el entorno virtual (si lo tienes)
# O instalar dependencias
pip install -r requirements.txt
```

### 2. Verificar la configuración

```bash
# Ejecutar diagnóstico
python tests/diagnostico.py
```

Este script verificará:
- Que existe el archivo `.env.test` con las credenciales
- Que todas las importaciones funcionan
- Que hay conexión con Supabase
- Que existe el bucket de prueba

### 3. Ejecutar los tests

#### Opción A: Con unittest (recomendado, no requiere pytest)
```bash
python tests/run_unittest.py
```

#### Opción B: Ejecutar un test específico
```bash
python -m unittest tests.test_supabase_integration.TestSupabaseIntegration.test_process_item_success_scenario -v
```

#### Opción C: Con pytest (si lo tienes instalado)
```bash
pytest tests/test_supabase_integration.py -v -s
```

## Estructura de Tests

Los tests implementados verifican:

1. **test_process_item_success_scenario**: Flujo completo exitoso
2. **test_process_item_missing_required_fields**: Manejo de campos faltantes
3. **test_process_item_empty_html_content**: Manejo de HTML vacío
4. **test_process_item_database_error**: Simulación de errores de BD
5. **test_process_item_storage_error**: Simulación de errores de storage
6. **test_duplicate_article_handling**: Manejo de duplicados

## Solución de Problemas

### Error: "No module named 'scraper_core'"
```bash
# Asegúrate de estar en el directorio correcto
cd "C:\Users\DELL\Desktop\Prueba con Windsurf AI\La Máquina de Noticias\src\module_scraper"
```

### Error: "SUPABASE_URL not configured"
```bash
# Verifica que existe .env.test
# Y que contiene las credenciales correctas
cat .env.test
```

### Error de conexión con Supabase
- Verifica que el proyecto Supabase está activo
- Verifica que las credenciales son correctas
- Asegúrate de usar el SERVICE_ROLE_KEY, no el ANON_KEY

## Resultados Esperados

Si todo funciona correctamente, deberías ver:
```
test_process_item_success_scenario ... ok
test_process_item_missing_required_fields ... ok
test_process_item_empty_html_content ... ok
test_process_item_database_error ... ok
test_process_item_storage_error ... ok
test_duplicate_article_handling ... ok

----------------------------------------------------------------------
Ran 6 tests in X.XXXs

OK
```
