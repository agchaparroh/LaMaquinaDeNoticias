# PRD: Hechos Relacionados en Dashboard Editorial

## 📋 Resumen Ejecutivo

**Producto**: La Máquina de Noticias - Dashboard Editorial  
**Funcionalidad**: Visualización de Hechos Noticiosos Relacionados  
**Fecha**: Enero 2025  
**Estado**: En Desarrollo  

## 🎯 Objetivo

Mejorar la comprensión contextual de los hechos noticiosos en el dashboard editorial mediante la incorporación de relaciones de primer grado entre hechos, permitiendo que los editores vean agrupados los hechos que están conectados causalmente, temporalmente o temáticamente.

## 🔍 Problema

Actualmente, el dashboard muestra los hechos noticiosos como elementos aislados en una lista plana. Esto dificulta:
- Entender el contexto completo de un evento noticioso
- Identificar cadenas de causa-efecto entre acontecimientos
- Detectar contradicciones entre diferentes fuentes
- Comprender la evolución temporal de un suceso

## 💡 Solución Propuesta

### Descripción General
Incorporar la tabla `hecho_relacionado` existente en la base de datos para mostrar hechos relacionados en primer grado agrupados visualmente en el dashboard. Esto permitirá que los editores vean de forma inmediata qué hechos están conectados entre sí.

### Características Principales

1. **Agrupación Visual de Hechos Relacionados**
   - Los hechos conectados se mostrarán juntos en el dashboard
   - Indicador visual del tipo de relación (consecuencia, contradictorio, etc.)
   - Fuerza de la relación representada visualmente (1-10)

2. **Tipos de Relaciones Soportadas**
   - Causal (causa-efecto)
   - Temporal (secuencia de eventos)
   - Contradictorio (versiones conflictivas)
   - Complementario (información adicional)

3. **Información de Contexto**
   - Descripción de la relación cuando esté disponible
   - Fecha de detección de la relación
   - Navegación entre hechos relacionados

## 📊 Modelo de Datos

### Tabla: `hecho_relacionado`
```sql
- hecho_origen_id (bigint): ID del hecho origen
- hecho_destino_id (bigint): ID del hecho destino
- tipo_relacion (varchar): Tipo de relación entre hechos
- fuerza_relacion (integer, 1-10): Intensidad de la relación
- descripcion_relacion (text): Descripción opcional
- fecha_deteccion (timestamp): Cuándo se detectó la relación
```

## 🔧 Implementación Técnica

### Backend
1. **Modelos Pydantic**: Crear estructura de datos validada
2. **Servicio de Consultas**: Extender para incluir relaciones
3. **API Endpoint**: Modificar respuesta para incluir agrupaciones

> **Nota sobre nginx_reverse_proxy**: No se requieren cambios en el proxy reverso. La configuración actual ya rutea correctamente las peticiones `/api/dashboard/*` al backend (puerto 8004), quitando el prefijo `/api`. El endpoint `/dashboard/hechos_revision` seguirá funcionando igual, solo cambiará la estructura de la respuesta para incluir relaciones.

## 📈 Métricas de Éxito

1. **Comprensión Mejorada**
   - Reducción del tiempo necesario para entender el contexto completo
   - Mayor facilidad para identificar noticias relacionadas

2. **Eficiencia Editorial**
   - Menos tiempo navegando entre hechos dispersos
   - Mejor capacidad para evaluar la veracidad con contexto completo

3. **Calidad de Contenido**
   - Detección más rápida de contradicciones
   - Mejor comprensión de cadenas causales

## 🚀 Fases de Desarrollo

### Backend (En Progreso)

#### 1.1 Crear Modelos de Datos Pydantic
- [ ] Crear directorio `src/models/` en module_dashboard_review_backend
- [ ] Implementar `models/__init__.py`
- [ ] Crear `models/requests.py`:
  - [ ] Definir clase `HechoFilterParams`
  - [ ] Definir clase `PaginationParams`
  - [ ] Añadir validaciones de rangos y tipos
- [ ] Crear `models/responses.py`:
  - [ ] Definir clase `HechoResponse` con todos los campos
  - [ ] Definir clase `HechoRelacionInfo`
  - [ ] Implementar `PaginatedResponse[T]` genérica
  - [ ] Crear `FilterOptionsResponse`
- [ ] Crear `models/domain.py`:
  - [ ] Mapear tabla `hecho_relacionado` a clase Pydantic
  - [ ] Definir enum `TipoRelacion`
  - [ ] Añadir validaciones de negocio

#### 1.2 Modificar Servicio de Hechos
- [ ] En `services/hechos_service.py`:
  - [ ] Importar nuevos modelos Pydantic
  - [ ] Crear método `get_relaciones_para_hechos(hecho_ids: List[int])`
  - [ ] Implementar query a tabla `hecho_relacionado`
  - [ ] Crear lógica de agrupación de hechos relacionados
  - [ ] Modificar `get_hechos_for_revision()`:
    - [ ] Extraer IDs después de query principal
    - [ ] Llamar a `get_relaciones_para_hechos()`
    - [ ] Combinar resultados con hechos
    - [ ] Mantener estructura de paginación

#### 1.3 Actualizar Endpoint API
- [ ] En `api/dashboard.py`:
  - [ ] Actualizar imports para usar nuevos modelos
  - [ ] Modificar response_model del endpoint
  - [ ] Ajustar manejo de errores para nuevos campos
  - [ ] Actualizar documentación del endpoint

#### 1.4 Testing de Integración Backend
- [ ] Crear tests unitarios para nuevos modelos
- [ ] Tests para método `get_relaciones_para_hechos()`
- [ ] Tests de integración para endpoint modificado
- [ ] Validar performance con datos de prueba
- [ ] Verificar manejo de casos edge (sin relaciones, relaciones circulares)


## ⚡ Consideraciones de Performance

- **Consultas Optimizadas**: Máximo 2 queries (hechos + relaciones)
- **Solo Primer Grado**: No recursión para evitar complejidad
- **Paginación Inteligente**: Aplicar antes de buscar relaciones
- **Índices en BD**: En campos hecho_origen_id y hecho_destino_id

## 🎨 Experiencia de Usuario

### Estado Actual
- Lista plana de hechos individuales
- Sin contexto visual de relaciones
- Navegación lineal página por página

### Estado Futuro
- Grupos visuales de hechos relacionados
- Indicadores claros de tipo y fuerza de relación
- Contexto inmediato sin navegación adicional

## 📝 Casos de Uso

1. **Editor revisa cadena de eventos**
   - Ve un hecho sobre "protestas en la capital"
   - Automáticamente ve agrupados: causa inicial, escalada, respuesta gubernamental
   - Evalúa todo el contexto antes de marcar importancia

2. **Verificación de contradicciones**
   - Dos medios reportan cifras diferentes del mismo evento
   - Sistema muestra ambos hechos como "contradictorios"
   - Editor puede evaluar y marcar cuál es más confiable

3. **Seguimiento de desarrollo noticioso**
   - Anuncio inicial → Reacciones → Consecuencias
   - Todo visible en un solo grupo
   - Comprensión inmediata de la línea temporal

## 🔒 Consideraciones de Seguridad

- Validación de permisos para ver relaciones
- No exposición de relaciones sensibles sin autorización
- Logs de auditoría para cambios en relaciones

## 📅 Timeline Estimado

- **Backend**: 2 horas (en progreso)
- **Testing**: 1 hora
- **Documentación**: 0.5 horas

**Total**: ~3.5 horas de desarrollo

## 🤝 Stakeholders

- **Usuarios Principales**: Editores y periodistas
- **Equipo Técnico**: Desarrolladores backend y frontend
- **Product Owner**: Responsable del dashboard editorial

## ✅ Criterios de Aceptación

1. Los hechos relacionados se obtienen correctamente de la BD
2. La API retorna hechos con sus relaciones incluidas
3. Performance no degradada (< 500ms adicionales)
4. Todos los tests pasan
5. Documentación actualizada

---

**Nota**: Este PRD se enfoca en la implementación backend para preparar los datos de relaciones de primer grado. La visualización y experiencia de usuario se definirán en una fase posterior. Futuras iteraciones podrían incluir relaciones de segundo grado o análisis automático de relaciones.