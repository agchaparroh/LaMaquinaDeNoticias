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

### Para validar un proyecto:
```bash
python validate_cpms_project.py projects/[nombre-proyecto]
```

## Estructura
```
CPMS-Workspace/
├── CLAUDE.md                      # Instrucciones y autonomía para Claude
├── README.md                      # Este archivo
├── validate_cpms_project.py       # Validador de proyectos CPMS
├── docs/                          # Documentación completa
│   ├── CPMS-Sistema-Gestion-Proyectos-Claude.md
│   ├── CPMS_AUTONOMOUS_EXECUTION_STANDARD.md
│   └── CPMS_TEMPLATE_IMPROVEMENTS.md
├── templates/                     # Plantillas mejoradas para nuevos proyectos
│   ├── project.yaml              # Con workflow_instructions
│   ├── tasks.yaml                # Con implementation_details
│   ├── workflow.md               # Guía de ejecución autónoma
│   ├── knowledge.md              # Base de conocimiento
│   └── check.py                  # Verificador de tareas
└── projects/                      # Todos los proyectos CPMS
    ├── SpiderFactory2.0/
    ├── SpiderFactoryCorrections/
    └── Proyectos pendientes/
```

## Proyectos Actuales
- **SpiderFactory2.0**: Sistema de generación de spiders (planning)
- **SpiderFactoryCorrections**: Correcciones del backend (development)

## Cómo Funciona

1. **Cada proyecto** tiene su carpeta en `/projects/`
2. **El código real** está en otra ubicación (especificada en project.yaml)
3. **Claude lee** la configuración CPMS y navega al código
4. **Las sesiones** se guardan para mantener contexto

## Documentación

Ver `/docs/CPMS-Sistema-Gestion-Proyectos-Claude.md` para guía completa.