# La Máquina de Noticias

Sistema integral para recopilar, procesar, analizar y consultar información periodística usando IA.

## Descripción

Este proyecto está diseñado para ser una herramienta poderosa para periodistas, permitiendo la extracción de conocimiento estructurado desde grandes volúmenes de texto.

## Estructura del Proyecto

El sistema se organiza en varios componentes principales:

**Directorios Clave:**

- `src/`: Contiene el código fuente principal de los diferentes módulos de la aplicación.
- `Base de Datos_SUPABASE/`: Incluye esquemas, migraciones, y documentación esencial relacionada con la configuración y estructura de la base de datos del proyecto en Supabase.
- `docs/`: Documentación general del proyecto, diagramas de arquitectura, y guías de usuario.
- `scripts/`: Scripts útiles para desarrollo, despliegue, o mantenimiento.
- `taskmaster/`: Configuración y tareas para TaskmasterAI, si se utiliza para la gestión del proyecto.

**Módulos Dockerizados:**
El núcleo funcional del sistema está compuesto por varios módulos, cada uno operando como un contenedor Docker:

- `module_scraper`: Encargado de la recopilación de artículos.
- `module_connector`: Gestiona la comunicación con la base de datos (Supabase).
- `module_pipeline`: Procesa el texto utilizando LLMs para extraer información.
- `module_dashboard_review_backend` / `frontend`: Interfaz para la revisión editorial.
- `module_chat_interface_backend` / `frontend`: Interfaz de chat para consultas en lenguaje natural.
- `module_dev_interface_backend` / `frontend`: Interfaz para desarrolladores (monitorización, etc.).
- `module_orchestration_agent`: Agente de Prefect para la orquestación de flujos de trabajo.
- `nginx_reverse_proxy`: Proxy inverso para enrutar el tráfico a los servicios.
- `module_maintenance_scripts`: Scripts para tareas de mantenimiento (no es un servicio continuo).

## Puesta en Marcha (Desarrollo)

1. **Clonar el repositorio.**
2. **Configurar las variables de entorno:** Copia `.env.example` a `.env` y rellena los valores necesarios. Asegúrate de revisar la configuración específica para la conexión a Supabase detallada en la carpeta `Base de Datos_SUPABASE/`.
3. **Construir y levantar los contenedores:**

   ```bash
   docker-compose up --build -d
   ```

4. **Acceder a los servicios a través del reverse proxy** (normalmente `http://localhost`).

## Base de Datos

Este proyecto utiliza Supabase como proveedor de base de datos PostgreSQL y almacenamiento.
Toda la información relevante para la estructura, migraciones y configuración específica de la base de datos del proyecto en Supabase se encuentra en la carpeta `Base de Datos_SUPABASE/`.

## Contribuir

(Instrucciones para contribuir)
