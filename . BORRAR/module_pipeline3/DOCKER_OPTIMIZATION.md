# Optimización de Docker para module_pipeline

## 🎯 Objetivo
Reducir el tamaño del contenedor Docker de **7GB a ~2-2.5GB** (reducción del 65-70%)

## 📊 Análisis del Problema

### Tamaño Original: ~7GB
- **Modelos spaCy grandes**: 581MB (es_core_news_lg: 568MB + en_core_web_sm: 13MB)
- **Dependencias de desarrollo**: ~200MB (pytest, mocks, etc.)
- **Archivos innecesarios**: ~200MB (logs, tests, docs)
- **Capas Docker no optimizadas**: ~500MB
- **Librerías no utilizadas**: ~200MB

## 🛠️ Cambios Implementados

### 1. **.dockerignore Mejorado**
- **Archivo**: `.dockerignore`
- **Impacto**: Reduce ~200MB del contexto de build
- **Cambios clave**:
  - Excluye logs (`logs/`, `*.log`, `*.log.gz`)
  - Excluye tests (`tests/`, `*test*.py`)
  - Excluye documentación (`docs/`, `*.md`)
  - Excluye archivos de desarrollo

### 2. **Requirements de Producción**
- **Archivo**: `requirements-prod.txt`
- **Impacto**: Reduce ~200MB en dependencias
- **Cambios clave**:
  - Eliminadas: pytest, pytest-mock, pytest-asyncio
  - Eliminadas: sentence-transformers (no usado, +2GB con PyTorch)
  - Eliminada: tiktoken (tokenización OpenAI no usada)
  - Consolidado: solo langdetect (removido langid duplicado)

### 3. **Dockerfile Optimizado**
- **Archivo**: `Dockerfile.optimized`
- **Impacto**: Reduce ~2-3GB total
- **Características**:
  - Multi-stage build (separa compilación de runtime)
  - Wheels pre-compilados
  - Modelos spaCy medianos (`es_core_news_md` 47MB vs `lg` 568MB)
  - Limpieza agresiva de cache
  - Optimizaciones de Python (`PYTHONOPTIMIZE=1`)

### 4. **Dockerfile Alpine (Ultra-ligero)**
- **Archivo**: `Dockerfile.alpine`
- **Impacto**: Reduce hasta ~5GB (imagen de 1.5-2GB)
- **Características**:
  - Base Alpine Linux (~5MB vs ~45MB slim)
  - Modelos spaCy pequeños (`sm` ~14MB)
  - Python optimizado (`-O` flag, `PYTHONOPTIMIZE=2`)
  - **Advertencia**: Puede tener problemas de compatibilidad

## 📋 Guía de Implementación

### Opción 1: Reemplazo Directo (Recomendado)
```bash
# Hacer backup del Dockerfile original
cp Dockerfile Dockerfile.original

# Usar el Dockerfile optimizado
cp Dockerfile.optimized Dockerfile

# Construir con el nuevo Dockerfile
docker build -t module_pipeline:optimized .

# Probar
docker run -p 8003:8003 module_pipeline:optimized
```

### Opción 2: Build Específico
```bash
# Construir versión optimizada sin modificar el original
docker build -f Dockerfile.optimized -t module_pipeline:optimized .

# O versión Alpine para máxima reducción
docker build -f Dockerfile.alpine -t module_pipeline:alpine .
```

### Opción 3: Actualizar docker-compose.yml
```yaml
module_pipeline:
  build:
    context: .
    dockerfile: Dockerfile.optimized  # o Dockerfile.alpine
  # ... resto de la configuración
```

## 🔄 Proceso de Migración

1. **Testing Local**:
   ```bash
   # Construir imagen optimizada
   docker build -f Dockerfile.optimized -t module_pipeline:test .
   
   # Verificar tamaño
   docker images | grep module_pipeline
   
   # Ejecutar tests básicos
   docker run -p 8003:8003 module_pipeline:test
   curl http://localhost:8003/health
   ```

2. **Verificar Funcionalidad**:
   - Health check: `/health`
   - Procesar artículo de prueba
   - Verificar logs
   - Comprobar métricas

3. **Rollback si es necesario**:
   ```bash
   cp Dockerfile.original Dockerfile
   docker build -t module_pipeline:latest .
   ```

## 📈 Resultados Esperados

| Métrica | Original | Optimizado | Alpine |
|---------|----------|------------|---------|
| Tamaño Imagen | ~7GB | ~2-2.5GB | ~1.5-2GB |
| Tiempo Build | ~10min | ~7min | ~15min* |
| Tiempo Inicio | ~30s | ~20s | ~25s |
| Uso RAM | ~750MB | ~650MB | ~600MB |

*Alpine tarda más en compilar debido a musl libc

## ⚠️ Consideraciones

### Modelos spaCy
- **Original**: `es_core_news_lg` (568MB) - máxima precisión
- **Optimizado**: `es_core_news_md` (47MB) - buena precisión (~2-3% menos)
- **Alpine**: `es_core_news_sm` (14MB) - precisión básica (~5-7% menos)

### Compatibilidad Alpine
- Algunas librerías Python pueden tener problemas con musl libc
- Operaciones matemáticas pueden ser ~10-15% más lentas
- Recomendado solo para ambientes con restricciones severas de espacio

### Monitoreo Post-Despliegue
1. Verificar métricas de performance
2. Monitorear logs de errores
3. Comparar tiempos de procesamiento
4. Validar calidad de extracción

## 🚀 Optimizaciones Adicionales (Futuras)

1. **Modelos como Volúmenes**:
   ```yaml
   volumes:
     - spacy_models:/app/models
   ```
   Reduciría ~600MB adicionales

2. **Distroless Images**:
   Usar imágenes distroless de Google para seguridad y tamaño

3. **Compilación AOT**:
   Usar Nuitka o Cython para compilar Python a binario

4. **Separación de Servicios**:
   Mover spaCy a un microservicio separado

## 📝 Checklist de Implementación

- [ ] Backup del Dockerfile original
- [ ] Implementar .dockerignore
- [ ] Crear requirements-prod.txt
- [ ] Elegir Dockerfile (optimized o alpine)
- [ ] Construir imagen de prueba
- [ ] Ejecutar tests de funcionalidad
- [ ] Verificar reducción de tamaño
- [ ] Actualizar documentación
- [ ] Desplegar en staging
- [ ] Monitorear performance
- [ ] Desplegar en producción

## 🆘 Troubleshooting

**Problema**: Error al instalar dependencias en Alpine
- **Solución**: Agregar dependencias de compilación necesarias en el builder

**Problema**: Modelo spaCy no encontrado
- **Solución**: Verificar que el modelo se descarga correctamente en el Dockerfile

**Problema**: Performance degradada
- **Solución**: Considerar usar `es_core_news_md` en lugar de `sm`

**Problema**: Errores de importación
- **Solución**: Verificar que todas las dependencias están en requirements-prod.txt