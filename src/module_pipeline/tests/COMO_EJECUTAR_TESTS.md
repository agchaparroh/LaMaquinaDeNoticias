# Instrucciones para ejecutar los tests

## Requisitos previos

Antes de ejecutar los tests, asegúrate de tener instaladas las dependencias necesarias:

```bash
cd C:\Users\DELL\Desktop\PruebaWindsurfAI\LaMaquinaDeNoticias\src\module_pipeline
pip install -r requirements.txt
```

Si faltan algunas dependencias específicas para los tests, instálalas con:

```bash
pip install loguru pydantic
```

## Ejecutar los tests

### Opción más fácil: Usar el menú

Simplemente ejecuta:

```bash
tests\menu_tests.bat
```

Y selecciona la opción que desees:
- **Opción 1**: Test completo que simula el procesamiento de un artículo real
- **Opción 2**: Tests unitarios rápidos de cada fase
- **Opción 3**: Tests de casos edge y manejo de errores
- **Opción 4**: Ejecutar todos los tests anteriores
- **Opción 5**: Salir

### Ejecutar tests individuales

Si prefieres ejecutar un test específico:

```bash
# Test completo del pipeline
python tests\test_pipeline_completo.py

# Tests unitarios
python tests\test_fases_individuales.py

# Tests de integración
python tests\test_integracion_errores.py
```

## ¿Qué hacen estos tests?

### 1. Test completo (`test_pipeline_completo.py`)
- Simula el procesamiento de un artículo de noticias real
- Ejecuta las 4 fases en secuencia
- Muestra resultados detallados paso a paso
- Verifica que los IDs se mantienen coherentes

### 2. Tests unitarios (`test_fases_individuales.py`)
- Prueba cada fase de forma aislada
- Más rápido que el test completo
- Útil para debugging de fases específicas

### 3. Tests de integración (`test_integracion_errores.py`)
- Verifica el manejo de errores
- Prueba casos edge como:
  - Textos vacíos
  - Errores de API
  - JSON malformado
  - Referencias inválidas
- Asegura que los fallbacks funcionan

## Notas importantes

1. **No necesitas API keys reales**: Los tests usan mocks para simular las respuestas de Groq
2. **No necesitas base de datos**: La normalización de entidades está mockeada
3. **Los tests son independientes**: Puedes ejecutar cualquiera sin configuración previa
4. **Son rápidos**: Todos los tests deberían completarse en segundos

## Si algo falla

Si encuentras errores al ejecutar los tests:

1. Verifica que estés en el directorio correcto:
   ```
   C:\Users\DELL\Desktop\PruebaWindsurfAI\LaMaquinaDeNoticias\src\module_pipeline
   ```

2. Asegúrate de que Python puede encontrar los módulos:
   - El test automáticamente agrega `src` al path de Python
   - Si falla, verifica que la estructura de directorios sea correcta

3. Revisa los logs de error:
   - Los tests muestran información detallada cuando algo falla
   - Busca el traceback completo al final del error

## Resultado esperado

Si todo funciona correctamente, verás:
- ✅ Marcas verdes indicando éxito
- 📊 Estadísticas de elementos procesados
- 🎉 Mensaje final de éxito

¡Eso es todo! Los tests están diseñados para ser simples y no requerir configuración compleja.
