# La Máquina de Noticias

Este proyecto es un sistema integral para la recopilación, procesamiento y análisis de noticias. Está diseñado para ser una herramienta poderosa para periodistas, permitiendo la extracción de conocimiento estructurado desde grandes volúmenes de texto. Incluye módulos para la extracción de datos (web scraping), un pipeline de procesamiento, una base de datos para almacenar la información y varias interfaces para la interacción y revisión de datos.

## 🏗️ Arquitectura Modular

El proyecto sigue una arquitectura modular donde cada componente tiene responsabilidades específicas y bien definidas:

### **Módulos del Sistema:**

1. **`module_scraper`** - Sistema de recopilación de noticias (Scrapy)
2. **`module_connector`** - Conector entre scraper y pipeline  
3. **`module_pipeline`** - Pipeline principal de procesamiento con LLMs
4. **`module_maintenance_scripts`** - Scripts de mantenimiento ("IA Nocturna")
5. **`module_orchestration_agent`** - Orquestación y scheduling (Prefect)
6. **`nginx_reverse_proxy`** - Proxy reverso y balanceador
7. **`module_dashboard_review_backend/frontend`** - Dashboard para periodistas
8. **`module_chat_interface_backend/frontend`** - Interfaz de investigación
9. **`module_dev_interface_backend/frontend`** - Herramientas de desarrollo

## 📋 Gestión de Proyectos con TaskMaster-AI

### **División de Proyectos**

Para una gestión más eficiente, el proyecto se divide en **dos proyectos TaskMaster-AI independientes pero complementarios**:

#### **🎯 Proyecto Principal** (Orquestación y Arquitectura General)
- **Ubicación:** `C:\Users\DELL\Desktop\Prueba con Windsurf AI\La Máquina de Noticias\`
- **Enfoque:** Desarrollo de módulos principales, integración, y despliegue

#### **🎯 Proyecto module_scraper** (Desarrollo Específico Scraper)
- **Ubicación:** `C:\Users\DELL\Desktop\Prueba con Windsurf AI\La Máquina de Noticias\src\module_scraper\`
- **Enfoque:** Desarrollo específico del sistema de scraping

## 📁 Arquitectura del Directorio

El proyecto está estructurado de la siguiente manera:

### **Directorios Principales:**
-   **`.github/`** - Flujos de trabajo y configuraciones GitHub Actions
-   **`.venv/`** - Entorno virtual de Python aislado
-   **`Base de datos_SUPABASE/`** - Scripts SQL, migraciones y documentación BD
    -   `documentación/` - Arquitectura de BD, seguridad, etc.
    -   `migrations/` - Scripts de versioning del esquema
    -   `scripts/` - Scripts de mantenimiento (embeddings, etc.)
-   **`docs/`** - Documentación completa del proyecto
    -   `Arquitectura/` - Documentos de arquitectura técnica
    -   `Componentes/` - Descripción de módulos principales
    -   `En detalle/` - Documentación específica de componentes
    -   `Guías/` - Guías prácticas para desarrolladores
    -   `Prompts/` - Prompts de IA del sistema
    -   `Revisiones/` - Informes de auditoría y revisión

### **Código Fuente (`src/`):**
-   **`module_scraper/`** - Sistema Scrapy (68.6% completado)
-   **`module_connector/`** - Conector scraper→pipeline (próximo)
-   **`module_pipeline/`** - Pipeline de procesamiento LLM
-   **`module_maintenance_scripts/`** - Scripts "IA Nocturna"
-   **`module_orchestration_agent/`** - Orquestación Prefect
-   **`nginx_reverse_proxy/`** - Proxy reverso
-   **`module_dashboard_review_backend/`** - API dashboard periodistas
-   **`module_dashboard_review_frontend/`** - UI dashboard periodistas  
-   **`module_chat_interface_backend/`** - API chat investigación
-   **`module_chat_interface_frontend/`** - UI chat investigación
-   **`module_dev_interface_backend/`** - API herramientas dev
-   **`module_dev_interface_frontend/`** - UI herramientas dev

### **Gestión y Control:**
-   **`tasks/`** - Archivos TaskMaster-AI del proyecto principal
    -   `tasks.json` - Estado actual del progreso general
    -   `task_001.txt` a `task_015.txt` - Archivos individuales
-   **`tests/`** - Pruebas de integración inter-módulos

### **Archivos de Configuración:**
-   `.gitignore` - Archivos ignorados por Git
-   `docker-compose.yml` - Servicios Docker del sistema completo
-   `requirements.txt` - Dependencias Python del proyecto principal
-   `README.md` - Este archivo de documentación