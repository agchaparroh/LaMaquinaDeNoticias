# Análisis de Constraints de Base de Datos
## La Máquina de Noticias - Documentación de Validaciones

### 1. TABLA: articulos

#### CHECK constraints:
- `articulos_puntuacion_relevancia_check`: puntuacion_relevancia BETWEEN 0 AND 10
- `check_storage_path_format`: storage_path debe seguir patrón: `^[^/]+/\d{4}/\d{2}/\d{2}/[^/]+\.(html|txt)\.gz$`

---

### 2. TABLA: entidades

#### CHECK constraints:
- `entidades_relevancia_check`: relevancia BETWEEN 1 AND 10

#### Campos requeridos (NOT NULL):
- id, nombre, tipo, relevancia

**⚠️ NOTA: No hay constraint para tipos válidos de entidad**

---

### 3. TABLA: hechos

#### CHECK constraints:
- `hechos_importancia_check`: importancia BETWEEN 1 AND 10
- `hechos_tipo_hecho_check`: tipo_hecho IN ('SUCESO', 'ANUNCIO', 'DECLARACION', 'BIOGRAFIA', 'CONCEPTO', 'NORMATIVA', 'EVENTO')
- `hechos_precision_temporal_check`: precision_temporal IN ('exacta', 'dia', 'semana', 'mes', 'trimestre', 'año', 'decada', 'periodo', 'desconocido')
- `hechos_estado_programacion_check`: estado_programacion IN ('programado', 'confirmado', 'cancelado', 'modificado', 'realizado', NULL)
- `hechos_evaluacion_editorial_check`: evaluacion_editorial IN ('pendiente_revision_editorial', 'verificado_ok_editorial', 'declarado_falso_editorial')
- `hechos_consenso_fuentes_check`: consenso_fuentes IN ('pendiente_analisis_fuentes', 'confirmado_multiples_fuentes', 'sin_confirmacion_suficiente_fuentes', 'en_disputa_por_hechos_contradictorios')
- `hechos_confiabilidad_programacion_check`: confiabilidad_programacion BETWEEN 1 AND 5

---

### 4. TABLA: hecho_entidad

#### CHECK constraints:
- `hecho_entidad_relevancia_en_hecho_check`: relevancia_en_hecho BETWEEN 1 AND 10
- `hecho_entidad_tipo_relacion_check`: tipo_relacion IN ('protagonista', 'mencionado', 'afectado', 'declarante', 'ubicacion', 'contexto', 'victima', 'agresor', 'organizador', 'participante', 'otro')

---

### 5. TABLA: entidad_relacion

#### CHECK constraints:
- `entidad_relacion_fuerza_relacion_check`: fuerza_relacion BETWEEN 1 AND 10
- `entidad_relacion_tipo_relacion_check`: tipo_relacion IN ('miembro_de', 'subsidiaria_de', 'aliado_con', 'opositor_a', 'sucesor_de', 'predecesor_de', 'casado_con', 'familiar_de', 'empleado_de')
- `check_different_related_entities`: entidad_origen_id != entidad_destino_id

---

### 6. TABLA: hecho_relacionado

#### CHECK constraints:
- `hecho_relacionado_fuerza_relacion_check`: fuerza_relacion BETWEEN 1 AND 10
- `hecho_relacionado_tipo_relacion_check`: tipo_relacion IN ('causa', 'consecuencia', 'contexto_historico', 'respuesta_a', 'aclaracion_de', 'version_alternativa', 'seguimiento_de')
- `check_different_related_hechos`: (hecho_origen_id != hecho_destino_id) OR (fecha_ocurrencia_origen != fecha_ocurrencia_destino)

---

### 7. TABLA: datos_cuantitativos

#### CHECK constraints:
- `datos_cuantitativos_categoria_check`: categoria IN ('económico', 'demográfico', 'electoral', 'social', 'presupuestario', 'sanitario', 'ambiental', 'conflicto', 'otro')
- `datos_cuantitativos_tipo_periodo_check`: tipo_periodo IN ('anual', 'trimestral', 'mensual', 'semanal', 'diario', 'puntual', 'acumulado', NULL)
- `datos_cuantitativos_tendencia_check`: tendencia IN ('aumento', 'disminución', 'estable', NULL)

---

### 8. TABLA: citas_textuales

#### CHECK constraints:
- `citas_textuales_relevancia_check`: relevancia BETWEEN 1 AND 5

---

### 9. TABLA: contradicciones

#### CHECK constraints:
- `contradicciones_grado_contradiccion_check`: grado_contradiccion BETWEEN 1 AND 5
- `contradicciones_tipo_contradiccion_check`: tipo_contradiccion IN ('fecha', 'contenido', 'entidades', 'ubicacion', 'valor', 'completa')
- `contradicciones_estado_resolucion_check`: estado_resolucion IN ('pendiente', 'analizada', 'resuelta', 'ignorada')
- `check_different_hechos`: (hecho_principal_id != hecho_contradictorio_id) OR (fecha_ocurrencia_principal != fecha_ocurrencia_contradictoria)

---

## 🚨 RESUMEN DE VALIDACIONES CRÍTICAS

### Rangos numéricos:
- Relevancia entidades: 1-10
- Importancia hechos: 1-10  
- Relevancia en hecho_entidad: 1-10
- Fuerza relación: 1-10
- Relevancia citas: 1-5
- Grado contradicción: 1-5
- Confiabilidad programación: 1-5

### Enums críticos para el pipeline:
1. **tipo_hecho**: SUCESO, ANUNCIO, DECLARACION, BIOGRAFIA, CONCEPTO, NORMATIVA, EVENTO
2. **precision_temporal**: exacta, dia, semana, mes, trimestre, año, decada, periodo, desconocido
3. **categoria_datos**: económico, demográfico, electoral, social, presupuestario, sanitario, ambiental, conflicto, otro
4. **tipo_periodo**: anual, trimestral, mensual, semanal, diario, puntual, acumulado
5. **tipo_relacion_entidad**: miembro_de, subsidiaria_de, aliado_con, opositor_a, sucesor_de, predecesor_de, casado_con, familiar_de, empleado_de
6. **tipo_relacion_hecho_entidad**: protagonista, mencionado, afectado, declarante, ubicacion, contexto, victima, agresor, organizador, participante, otro
7. **tipo_relacion_hechos**: causa, consecuencia, contexto_historico, respuesta_a, aclaracion_de, version_alternativa, seguimiento_de
8. **tipo_contradiccion**: fecha, contenido, entidades, ubicacion, valor, completa