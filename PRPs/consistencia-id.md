name: "Sistema de Consistencia de IDs - Implementación de Trazabilidad End-to-End"
description: |
  Implementar un sistema consistente de identificación que conecte los artículos desde su extracción en el scraper hasta su persistencia final, eliminando la dependencia de UUIDs temporales y utilizando los IDs de base de datos existentes para mantener trazabilidad completa.

## Goal
Establecer un flujo de identificación consistente donde el ID BIGSERIAL generado por la base de datos al guardar un artículo sea propagado a través de todo el pipeline, permitiendo trazabilidad completa y eliminando el error "invalid input syntax for type bigint" en la persistencia.

## Why
**Problemas actuales:**
- El pipeline genera UUIDs temporales sin conocer el ID real del artículo
- Se pierde la trazabilidad entre el artículo original y sus datos procesados
- Error crítico al intentar persistir: "invalid input syntax for type bigint"
- Imposibilidad de relacionar los datos procesados con el artículo fuente
- Complejidad innecesaria con múltiples sistemas de identificación

**Valor del cambio:**
- Trazabilidad completa desde scraping hasta persistencia
- Eliminación de errores de tipo de datos
- Simplificación del sistema de identificación
- Capacidad de auditoría y debugging mejorada
- Preparación para análisis de datos históricos

## What
**Comportamiento esperado:**
1. El scraper guarda un artículo y obtiene su ID BIGSERIAL
2. Este ID se incluye en el archivo JSON.gz que genera
3. El connector lee el ID y lo pasa al pipeline
4. El pipeline usa este ID en lugar de generar UUIDs
5. La persistencia usa la RPC correcta según el tipo de contenido

**Requisitos técnicos:**
- Modificar scraper para incluir `articulo_id` en output
- Actualizar modelo del connector para aceptar el campo
- Adaptar pipeline para usar ID existente con fallback a UUID
- Cambiar lógica de persistencia para usar RPC apropiada
- Mantener compatibilidad con archivos sin ID

### Success Criteria
- [ ] El scraper incluye el ID del artículo en los archivos JSON.gz generados
- [ ] El connector pasa correctamente el ID al pipeline sin modificaciones
- [ ] El pipeline usa el ID del artículo cuando está disponible (fallback a UUID)
- [ ] La persistencia detecta si es artículo o fragmento y usa la RPC correcta
- [ ] Los artículos se persisten exitosamente con datos vinculados al ID original
- [ ] Los tests end-to-end pasan con el nuevo flujo de IDs
- [ ] No hay regresión en el procesamiento de archivos legacy sin ID

## All Needed Context

### Arquitectura actual del flujo de datos
```
Scraper → BD (genera ID) → JSON.gz (sin ID) → Connector → Pipeline (genera UUID) → Error
```

### Arquitectura objetivo
```
Scraper → BD (genera ID) → JSON.gz (con ID) → Connector → Pipeline (usa ID) → Éxito
```

### Referencias de código clave
- **Scraper storage**: `src/module_scraper/scraper_core/pipelines/storage.py:274` - Donde se obtiene el ID
- **Connector model**: `src/module_connector/src/models.py` - Modelo ArticuloInItem
- **Pipeline controller**: `src/module_pipeline/src/controller.py:187` - Generación de UUID
- **Persistencia**: `src/module_pipeline/src/controller.py:_persistir_resultado_7_fases` - Llamada RPC

### Esquema de base de datos
- Tabla `articulos`: usa `id BIGSERIAL PRIMARY KEY`
- Tabla `documentos_extensos`: usa `id BIGSERIAL PRIMARY KEY`
- RPC `insertar_articulo_completo`: espera datos de artículo
- RPC `insertar_fragmento_completo`: espera `documento_id` BIGINT

### Documentación relevante
- Flujo de ID: `/docs/MAPA_FLUJO_ID_FRAGMENTO.md`
- Diagnóstico: `/docs/DIAGNOSTICO_ID_FRAGMENTO.md`

## Implementation Blueprint

### Phase 1: Fix Immediate Persistence Error
**Command**: `/fix --bug --minimal --uc`
**Persona**: `--persona-backend`
**Task**: Cambiar RPC de persistencia para usar la función correcta

1. Modificar `_persistir_resultado_7_fases` en controller.py
2. Detectar si es artículo mediante `metadata_adicional.es_articulo_completo`
3. Usar `insertar_articulo_completo` para artículos
4. Mantener `insertar_fragmento_completo` para fragmentos reales

**Remember:** Simple and solid is better
**Validation**: 
```bash
/test --integration "test_article_persistence" --coverage
```

### Phase 2: Scraper ID Propagation
**Command**: `/improve --feature --backwards-compatible`
**Persona**: `--persona-backend`
**Task**: Modificar scraper para incluir article_id en output

1. En `storage.py` después de `upserted_data = self._upsert_articulo_with_retry()`
2. Extraer ID: `articulo_id = upserted_data[0].get('id') if upserted_data else None`
3. Añadir al adapter: `if articulo_id: adapter['articulo_id'] = articulo_id`
4. Verificar que se incluye en JSON output

**Remember:** Simple and solid is better
**Validation**:
```bash
/analyze --data-flow "scraper output JSON" --verify "articulo_id field present"
```

### Phase 3: Connector Model Update
**Command**: `/build --model --extend`
**Persona**: `--persona-backend`
**Task**: Actualizar ArticuloInItem para incluir articulo_id

1. Añadir campo: `articulo_id: Optional[int] = Field(None, description="ID del artículo en la BD")`
2. Validar que el connector no modifica el campo
3. Verificar propagación al pipeline

**Remember:** Simple and solid is better
**Validation**:
```bash
/test --unit "test_connector_model_with_id" --mock-data
```

### Phase 4: Pipeline ID Usage
**Command**: `/refactor --logic --safe`
**Persona**: `--persona-senior-dev`
**Task**: Modificar pipeline para usar article_id cuando esté disponible

1. En `process_article`, extraer: `articulo_id = articulo_data.get('articulo_id')`
2. Condicional para ID de fragmento:
   ```python
   if articulo_id:
       fragmento_data["id_fragmento"] = f"ART-{articulo_id}"
   else:
       fragmento_data["id_fragmento"] = str(uuid.uuid4())
   ```
3. Añadir logging para trazabilidad

**Remember:** Simple and solid is better
**Validation**:
```bash
/scan --code-flow "article_id propagation" --trace
```

### Phase 5: End-to-End Testing
**Command**: `/test --e2e --comprehensive`
**Persona**: `--persona-qa`
**Task**: Probar el perfecto funcionamiento del sistema de ID's desde el scraper hasta la persistencia en Supabase, pasando por el module_pipeline. Prueba sobre el terreno: el sistema id es perfectamente funcional.

**Remember:** Simple and solid is better
**Validation**:
```bash
/run --test-suite "e2e_id_consistency" --coverage --report
```

### Phase 6: Documentation & Deployment
**Command**: `/document --architecture --flow`
**Persona**: `--persona-architect`
**Task**: Documentar el nuevo flujo de IDs

1. Actualizar diagrama de arquitectura
2. Documentar decisiones de diseño
3. Crear guía de migración
4. Preparar notas de release

**Validation**:
```bash
/review --docs "ID flow documentation" --checklist
```

## Validation Loop

### Unit Tests
```bash
# Scraper ID extraction
/test --unit "test_scraper_includes_article_id" --file "test_storage.py"

# Connector model validation  
/test --unit "test_connector_article_model" --file "test_models.py"

# Pipeline ID handling
/test --unit "test_pipeline_id_usage" --file "test_controller.py"
```

### Integration Tests
```bash
# Scraper to Connector flow
/test --integration "test_scraper_connector_id_flow" --trace

# Connector to Pipeline flow
/test --integration "test_connector_pipeline_id_flow" --trace

# Pipeline persistence
/test --integration "test_pipeline_persistence_with_id" --db
```

### End-to-End Tests
```bash
# Complete flow with new article
/test --e2e "test_complete_flow_with_article_id" --real-data

# Backward compatibility
/test --e2e "test_legacy_files_without_id" --mock-legacy

# Performance impact
/test --performance "test_id_propagation_overhead" --metrics
```

### Manual Validation
```bash
# Process single article and verify ID flow
/run --debug "process_single_article" --trace-id --verbose

# Check database consistency
/query --sql "SELECT a.id, COUNT(h.id) FROM articulos a LEFT JOIN hechos h ON h.articulo_id = a.id GROUP BY a.id"
```

## Risk Mitigation

### Backward Compatibility
- Fallback to UUID when article_id not present
- Support for legacy JSON files without ID
- Gradual rollout with feature flag if needed

### Data Integrity
- Validate ID types at each boundary
- Log ID transitions for debugging
- Implement ID format validation

### Performance
- No additional database queries
- Minimal overhead (passing existing data)
- Benchmark before/after implementation

## Rollback Plan
1. Revert pipeline to UUID generation
2. Keep scraper changes (harmless addition)
3. Document known issues for future fix

## Confidence Score: 9/10

High confidence due to:
- Clear problem identification
- Simple solution (pass existing data)
- No architectural changes needed
- Extensive test coverage planned
- Backward compatibility maintained

Minor deduction for:
- Multiple module changes required
- Coordination between teams needed