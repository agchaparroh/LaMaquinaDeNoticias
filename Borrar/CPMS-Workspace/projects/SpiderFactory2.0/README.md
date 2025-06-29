# Proyecto CPMS: Spider Factory 2.0

## Descripción
Sistema de generación automática de spiders para La Máquina de Noticias que reduce el tiempo de creación de 15-20 minutos a menos de 30 segundos.

## Uso del proyecto CPMS

Para cargar este proyecto en una nueva sesión de Claude:

```
"Carga proyecto SpiderFactory2.0 desde CPMS-Workspace/projects"
```

## Estructura del proyecto

- `project.yaml` - Configuración del proyecto
- `tasks.yaml` - 20 tareas organizadas en 4 fases
- `knowledge.md` - Decisiones arquitectónicas y patrones
- `sessions/` - Documentación y logs de sesiones

## Estado actual

- **Fase**: Planning
- **Tareas completadas**: 0/20
- **Duración estimada**: 20 días

## Stack tecnológico

### Backend
- FastAPI + Redis + Firecrawl + Jinja2

### Frontend  
- React + TypeScript + Material-UI + Vite

## Documentación importante

1. **Plan detallado**: `sessions/SPIDER_FACTORY_2.0_PLAN_DETALLADO.md`
2. **Documentación Context7**: `sessions/CONTEXT7_REFERENCE.md`
3. **Knowledge base**: `knowledge.md`

## Próximos pasos

1. Comenzar con TASK-001: Setup Redis y configuración
2. Consultar siempre Context7 antes de implementar
3. Actualizar status de tareas conforme se completen