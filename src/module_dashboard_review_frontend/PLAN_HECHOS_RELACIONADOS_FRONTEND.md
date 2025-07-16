# Plan de Implementación: Dashboard Contextualizado con Hechos Relacionados

## 📋 Resumen Ejecutivo

Este documento describe el plan para transformar el dashboard editorial de La Máquina de Noticias de una lista plana de hechos individuales a un sistema de **clusters contextualizados**, donde cada noticia se presenta con su línea temporal completa de eventos relacionados.

### 🎯 Visión
- **De**: Lista de hechos aislados sin contexto
- **A**: Historias completas con timeline cronológico
- **Beneficio**: Los editores comprenden el contexto completo de cada noticia de un vistazo

### Objetivos:
- Reducción del tiempo promedio para entender una historia (más contexto en menos espacio)
- Reducción de hechos mostrados en el Dashboard

### 🔑 Principios Clave
1. **Sin duplicados**: Cada hecho aparece una sola vez en el dashboard
2. **Protagonista único**: El hecho más importante lidera cada cluster
3. **Contexto cronológico**: Los hechos relacionados se muestran en orden temporal
4. **Interacción eficiente**: El contexto es expandible/colapsable
5. **Elementos estéticos** diferenciados para cada tipo de relación

## 🔍 Análisis del Estado Actual

### Backend ✅ COMPLETO
El backend ya tiene implementada toda la funcionalidad necesaria:

```python
# Endpoint funcionando
GET /api/dashboard/hechos_revision

# Respuesta incluye relaciones
{
  "items": [{
    "id": 123,
    "contenido": "Cumbre climática alcanza acuerdo histórico",
    "importancia": 10,
    "relaciones": [
      {
        "hecho_relacionado_id": 124,
        "tipo_relacion": "causa",
        "fuerza_relacion": 8,
        "direccion": "destino"
      }
    ]
  }]
}
```

### Frontend ❌ BRECHA IDENTIFICADA

El frontend actual:
- No tiene tipos TypeScript para relaciones
- No agrupa hechos relacionados
- Muestra todos los hechos como elementos independientes
- No evita duplicados en la presentación
Objetivos:

## ⚡ Consideraciones de Performance:

1. **Clustering en Frontend**: Evita múltiples llamadas al backend
2. **Memoización**: Clusters se recalculan solo cuando cambian datos
3. **Lazy Loading**: Timeline se renderiza solo al expandir
4. **Virtualización**: Para clusters con 20+ hechos relacionados


# PRECAUCIONES:

- La ampliación consiste **ÚNICA Y EXCLUSIVAMENTE** en lo que está aquí descrito. Nada más.
- No disponemos del MCP Magic.
- Existe un src/nginx_reverse_proxy para hacer de intermediario entre src/module_dashboard_review_backend y src/module_dashboard_review_frontend
- Buscamos una implementación que cumpla las siguientes características:
    - Solución **integral**: No buscamos una implementación por fases. El sistema todavía no está en producción, así que no es necesario planificar migraciones paulatinas e incrementales, (...). 
    - NO ROTUNDO A LA **SOBREINGENIERÍA**: Buscamos una implementación robusta y "a prueba de balas", sin piezas móviles innecesarias que añadan complejidad para conseguir mejoras marginales y que tengan facilidad para romperse. Lo sencillo es mejor. 
    - No debe ser una solución **destructiva**: Construimos sobre los cimientos que ya están implementado. No buscamos sustituir o destruir, sino mejorar.
    - Debe ser **sostenible a largo plazo**, evitando soluciones temporales o parches.