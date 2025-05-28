---
trigger: model_decision
description: Aplicar: cuando se codifique, se analicen interacciones de módulos, se busquen ubicaciones de archivos/directorios, o se necesite info del stack tecnológico/convenciones
---

## 0. Project Overview & Modules (La Máquina Specific)

-   **Project Name:** La Máquina de Noticias
-   **Goal:** Comprehensive platform for scraping, processing, reviewing, and interacting with news articles.
-   **Core Data & Services Platform:** Supabase
-   **Task Management:** TaskmasterAI. Config/tasks in `taskmaster/` (e.g., `taskmaster/tasks/tasks.json`).
-   **Key Modules:**
    -   **`module_scraper`**: Fetches news articles (Python, Scrapy).
        -   **Description:** Scrapy for site navigation, article identification, content/metadata extraction, HTML/data storage. Portia for visual spider creation.
        -   **Input:** URLs, sitemaps, Portia-generated Scrapy spiders (host `./data/portia_projects` -> container `/app/portia_spiders`).
        -   **Output:**
            -   `.json.gz` (`ArticuloInItem` data) to host `./data/scrapy_output/pending/` (container `/app/output/pending/`).
            -   `.html.gz` (original HTML) to Supabase Storage (`bucket-articulos-originales`).
        -   **Orchestration:** Triggered by `module_orchestration_agent` (Prefect).
    -   `module_connector`: Manages data connections and ingestion into the pipeline.
    -   `module_pipeline`: Core data processing (cleaning, enriching, storing articles).
    -   `module_orchestration_agent`: Coordinates module workflows (Prefect).
    -   `module_dashboard_review_backend`: Backend for news review dashboard.
    -   `module_dashboard_review_frontend`: Frontend UI for news review.
    -   `module_chat_interface_backend`: Backend for chat interface to query news.
    -   `module_chat_interface_frontend`: Frontend UI for chat interface.
    -   `module_dev_interface_backend`: Backend for developer/admin interface.
    -   `module_dev_interface_frontend`: Frontend UI for developer/admin interface.
    -   `nginx_reverse_proxy`: Manages incoming traffic (Nginx).

## 1. Core Backend Architecture (La Máquina Specific - Per Module)

*General structure for backend modules. `module_scraper` has Scrapy-specifics below.*

-   **`module_scraper` (Scrapy Specific Structure):**
    -   **Scrapy Project Root:** `module_scraper/la_maquina_scraper/` (adjust name if different)
    -   **Spiders:**
        -   Manual: `module_scraper/la_maquina_scraper/spiders/`
        -   Portia-generated (RO access): Host `./data/portia_projects` -> container `/app/portia_spiders`.
    -   **Item Pipelines:** `module_scraper/la_maquina_scraper/pipelines.py`
        -   Key: `CleaningPipeline`, `ValidacionPipeline`, `MemoriaProfundaPipeline` (Supabase upload), `JSONExportPipeline`.
    -   **Item Definitions (`ArticuloInItem`):** `module_scraper/la_maquina_scraper/items.py`
    -   **Settings:** `module_scraper/la_maquina_scraper/settings.py` (pipelines, middlewares like DeltaFetch, Playwright, User-Agent rotation, Spidermon, throttling: `DOWNLOAD_DELAY`, `AUTOTHROTTLE_ENABLED`, `CONCURRENT_REQUESTS_PER_DOMAIN`).
    -   **Middlewares:** Custom or configured in `settings.py` (e.g., Playwright, DeltaFetch, Retry).
    -   **DeltaFetch Dir:** `DELTAFETCH_DIR` env var (e.g., `/app/deltafetch_db/`), persistent volume.
    -   **Key External Libraries:** `Scrapy`, `scrapy-playwright`, `Playwright`, `supabase-py`, `scrapy-deltafetch`, `scrapy-fake-useragent`, `Spidermon`, `BeautifulSoup4`, `dateparser`, `langdetect`.
    -   **Dockerfile:** `module_scraper/Dockerfile` (base: `scrapinghub/scrapinghub-stack-scrapy`).

-   **Other Backend Modules (e.g., `module_pipeline`, `module_orchestration_agent`):**
    -   **Main Logic/Business Rules:** `[module_name]/src/services/` or `app/services/`
    -   **API Endpoints/Handlers (if applicable):**
        -   Routes: `[module_name]/src/routes/` or `app/api/`
        -   Controllers: `[module_name]/src/controllers/` or `app/handlers/`
    -   **Module-Specific Shared Utils:** `[module_name]/src/utils/`
    -   **Module-Specific Config:**
        -   Env Vars: Per module (e.g., `[module_name]/.env`), via `[module_name]/src/config/index.ts` (or Python eq.).
        -   Feature Flags: `[module_name]/src/config/featureFlags.ts` (or eq.).
        -   Service Configs: `[module_name]/src/config/services.ts` (or eq.).

-   **Project-Wide Shared Utilities (Backend):** `shared/utils/backend/`

## 2. Frontend Architecture (La Máquina Specific - Per Frontend Module)

-   *Not fully defined. Sections below are placeholders.*
-   **UI Components & Views:**
    -   Pages/Views: `[frontend_module_name]/src/pages/`
    -   Reusable Components: `[frontend_module_name]/src/components/common/`
-   **State Management:** `[Tool (e.g., Zustand, Redux)]` in `[frontend_module_name]/src/store/`
-   **Routing:** `[Tool (e.g., React Router)]` in `[frontend_module_name]/src/router/`
-   **API Client:** `[frontend_module_name]/src/services/api.ts`
-   **Assets & Styling:** `[frontend_module_name]/src/styles/global.css`

## 3. Data & Storage (La Máquina Specific)

-   **Primary DB (Supabase):** `PostgreSQL`
-   **Object Storage (`module_scraper` HTML originals):**
    -   Service: `Supabase Storage`
    -   Bucket: `bucket-articulos-originales` (`STORAGE_BUCKET_NAME` env var for `module_scraper`).
-   **Scraper JSON Output (pending for `module_connector`):**
    -   Location: Hos