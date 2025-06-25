# CPMS Workspace - Centro de Control de Proyectos

## Inicio Rápido

### Para Claude:
```
"Carga el proyecto [nombre] desde C:/Users/DELL/Desktop/PruebaWindsurfAI/LaMaquinaDeNoticias/CPMS-Workspace/projects"
```

### Para crear nuevo proyecto:
```
"Crea un nuevo proyecto CPMS llamado [nombre] para el código en [ruta]"
```

## Estructura
```
CPMS-Workspace/
├── CLAUDE.md          # Instrucciones para Claude
├── README.md          # Este archivo
├── docs/              # Documentación completa
│   └── CPMS-Sistema-Gestion-Proyectos-Claude.md
├── templates/         # Plantillas para nuevos proyectos
│   ├── project.yaml
│   ├── tasks.yaml
│   └── knowledge.md
└── projects/          # Todos los proyectos CPMS
    └── (vacío - aquí se crearán los proyectos)
```

## Proyectos Actuales
(Ninguno todavía)

## Cómo Funciona

1. **Cada proyecto** tiene su carpeta en `/projects/`
2. **El código real** está en otra ubicación (especificada en project.yaml)
3. **Claude lee** la configuración CPMS y navega al código
4. **Las sesiones** se guardan para mantener contexto

## Documentación

Ver `/docs/CPMS-Sistema-Gestion-Proyectos-Claude.md` para guía completa.