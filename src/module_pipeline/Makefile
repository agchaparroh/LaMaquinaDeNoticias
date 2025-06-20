# Makefile for module_pipeline
# La Máquina de Noticias - Pipeline Module
# 
# Comandos disponibles:
#   make help     - Mostrar esta ayuda
#   make setup    - Configuración inicial del proyecto
#   make dev      - Ejecutar en modo desarrollo
#   make test     - Ejecutar tests
#   make build    - Construir imagen Docker
#   make deploy   - Desplegar con Docker Compose
#   make clean    - Limpiar archivos temporales

.PHONY: help setup dev test test-cov build deploy clean logs health metrics

# === CONFIGURACIÓN ===
DOCKER_IMAGE_NAME = lamaquina/module-pipeline
DOCKER_TAG = latest
PROJECT_NAME = module_pipeline
PYTHON = python3
PIP = pip3

# === COLORES PARA OUTPUT ===
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
NC = \033[0m # No Color

# === COMANDO POR DEFECTO ===
help: ## Mostrar esta ayuda
	@echo "$(BLUE)La Máquina de Noticias - Module Pipeline$(NC)"
	@echo "$(YELLOW)Comandos disponibles:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'

# === CONFIGURACIÓN INICIAL ===
setup: ## Configuración inicial del proyecto
	@echo "$(BLUE)🔧 Configurando proyecto module_pipeline...$(NC)"
	@echo "$(YELLOW)Verificando Python...$(NC)"
	@$(PYTHON) --version
	@echo "$(YELLOW)Creando entorno virtual...$(NC)"
	@$(PYTHON) -m venv venv
	@echo "$(YELLOW)Activando entorno e instalando dependencias...$(NC)"
	@if [ -f "venv/bin/activate" ]; then \
		. venv/bin/activate && $(PIP) install --upgrade pip && $(PIP) install -r requirements.txt; \
	else \
		. venv/Scripts/activate && $(PIP) install --upgrade pip && $(PIP) install -r requirements.txt; \
	fi
	@echo "$(YELLOW)Descargando modelos spaCy...$(NC)"
	@if [ -f "venv/bin/activate" ]; then \
		. venv/bin/activate && python -m spacy download es_core_news_lg && python -m spacy download en_core_web_sm; \
	else \
		. venv/Scripts/activate && python -m spacy download es_core_news_lg && python -m spacy download en_core_web_sm; \
	fi
	@echo "$(YELLOW)Creando archivo .env desde .env.example...$(NC)"
	@if [ ! -f ".env" ]; then cp .env.example .env; fi
	@echo "$(YELLOW)Creando directorios necesarios...$(NC)"
	@mkdir -p logs logs/development metrics
	@echo "$(GREEN)✅ Configuración inicial completada!$(NC)"
	@echo "$(YELLOW)📝 IMPORTANTE: Edita .env con tus API keys antes de continuar$(NC)"

# === DESARROLLO ===
dev: ## Ejecutar en modo desarrollo
	@echo "$(BLUE)🚀 Iniciando servidor de desarrollo...$(NC)"
	@if [ -f ".env" ]; then \
		echo "$(GREEN)Archivo .env encontrado$(NC)"; \
	else \
		echo "$(RED)❌ Archivo .env no encontrado. Ejecuta 'make setup' primero$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Iniciando FastAPI en http://localhost:8003$(NC)"
	@if [ -f "venv/bin/activate" ]; then \
		. venv/bin/activate && cd src && python main.py; \
	else \
		. venv/Scripts/activate && cd src && python main.py; \
	fi

dev-docker: ## Ejecutar en modo desarrollo con Docker
	@echo "$(BLUE)🐳 Iniciando con Docker Compose...$(NC)"
	@docker-compose up -d module-pipeline
	@echo "$(GREEN)✅ Servidor iniciado en http://localhost:8003$(NC)"
	@echo "$(YELLOW)📊 Métricas disponibles en http://localhost:8003/metrics$(NC)"

# === TESTING ===
test: ## Ejecutar tests
	@echo "$(BLUE)🧪 Ejecutando tests...$(NC)"
	@if [ -f "venv/bin/activate" ]; then \
		. venv/bin/activate && pytest; \
	else \
		. venv/Scripts/activate && pytest; \
	fi

test-cov: ## Ejecutar tests con cobertura
	@echo "$(BLUE)🧪 Ejecutando tests con reporte de cobertura...$(NC)"
	@if [ -f "venv/bin/activate" ]; then \
		. venv/bin/activate && pytest --cov=src --cov-report=html --cov-report=term; \
	else \
		. venv/Scripts/activate && pytest --cov=src --cov-report=html --cov-report=term; \
	fi
	@echo "$(GREEN)📊 Reporte HTML generado en htmlcov/index.html$(NC)"

test-specific: ## Ejecutar tests específicos (uso: make test-specific TEST=test_file.py)
	@echo "$(BLUE)🧪 Ejecutando test específico: $(TEST)$(NC)"
	@if [ -f "venv/bin/activate" ]; then \
		. venv/bin/activate && pytest $(TEST) -v; \
	else \
		. venv/Scripts/activate && pytest $(TEST) -v; \
	fi

# === DOCKER ===
build: ## Construir imagen Docker
	@echo "$(BLUE)🐳 Construyendo imagen Docker...$(NC)"
	@docker build -t $(DOCKER_IMAGE_NAME):$(DOCKER_TAG) .
	@echo "$(GREEN)✅ Imagen construida: $(DOCKER_IMAGE_NAME):$(DOCKER_TAG)$(NC)"

deploy: ## Desplegar con Docker Compose
	@echo "$(BLUE)🚀 Desplegando con Docker Compose...$(NC)"
	@if [ ! -f ".env" ]; then \
		echo "$(RED)❌ Archivo .env no encontrado$(NC)"; \
		exit 1; \
	fi
	@docker-compose up -d
	@echo "$(GREEN)✅ Servicios desplegados:$(NC)"
	@echo "  📡 Pipeline API: http://localhost:8003"
	@echo "  📊 Prometheus: http://localhost:9090"
	@echo "  📈 Grafana: http://localhost:3001"

deploy-prod: ## Desplegar solo el pipeline (sin monitoreo)
	@echo "$(BLUE)🚀 Desplegando pipeline en modo producción...$(NC)"
	@docker-compose up -d module-pipeline
	@echo "$(GREEN)✅ Pipeline desplegado en http://localhost:8003$(NC)"

# === OPERACIONES ===
logs: ## Ver logs del pipeline
	@echo "$(BLUE)📋 Mostrando logs del pipeline...$(NC)"
	@docker-compose logs -f module-pipeline

health: ## Verificar salud del sistema
	@echo "$(BLUE)🏥 Verificando salud del sistema...$(NC)"
	@curl -s http://localhost:8003/health | python -m json.tool || echo "$(RED)❌ Servicio no disponible$(NC)"
	@echo ""
	@curl -s http://localhost:8003/health/detailed | python -m json.tool || echo "$(RED)❌ Health check detallado no disponible$(NC)"

metrics: ## Ver métricas del sistema
	@echo "$(BLUE)📊 Métricas del sistema:$(NC)"
	@curl -s http://localhost:8003/metrics || echo "$(RED)❌ Métricas no disponibles$(NC)"

status: ## Ver estado del pipeline
	@echo "$(BLUE)⚙️ Estado del pipeline:$(NC)"
	@curl -s http://localhost:8003/monitoring/pipeline-status | python -m json.tool || echo "$(RED)❌ Estado no disponible$(NC)"

# === LIMPIEZA ===
clean: ## Limpiar archivos temporales
	@echo "$(BLUE)🧹 Limpiando archivos temporales...$(NC)"
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@find . -type f -name "*.tmp" -delete 2>/dev/null || true
	@rm -rf logs/*.log metrics/*.json 2>/dev/null || true
	@echo "$(GREEN)✅ Limpieza completada$(NC)"

clean-docker: ## Limpiar contenedores e imágenes Docker
	@echo "$(BLUE)🐳 Limpiando recursos Docker...$(NC)"
	@docker-compose down --remove-orphans
	@docker system prune -f
	@echo "$(GREEN)✅ Recursos Docker limpiados$(NC)"

# === UTILIDADES ===
shell: ## Abrir shell en el contenedor
	@echo "$(BLUE)🐚 Abriendo shell en el contenedor...$(NC)"
	@docker-compose exec module-pipeline /bin/bash

install-deps: ## Reinstalar dependencias
	@echo "$(BLUE)📦 Reinstalando dependencias...$(NC)"
	@if [ -f "venv/bin/activate" ]; then \
		. venv/bin/activate && $(PIP) install --upgrade pip && $(PIP) install -r requirements.txt; \
	else \
		. venv/Scripts/activate && $(PIP) install --upgrade pip && $(PIP) install -r requirements.txt; \
	fi

format: ## Formatear código con black
	@echo "$(BLUE)🎨 Formateando código...$(NC)"
	@if [ -f "venv/bin/activate" ]; then \
		. venv/bin/activate && black src/ tests/; \
	else \
		. venv/Scripts/activate && black src/ tests/; \
	fi

lint: ## Verificar código con flake8
	@echo "$(BLUE)🔍 Verificando código...$(NC)"
	@if [ -f "venv/bin/activate" ]; then \
		. venv/bin/activate && flake8 src/ tests/; \
	else \
		. venv/Scripts/activate && flake8 src/ tests/; \
	fi

# === INFORMACIÓN ===
info: ## Mostrar información del proyecto
	@echo "$(BLUE)📋 Información del proyecto:$(NC)"
	@echo "  $(YELLOW)Proyecto:$(NC) $(PROJECT_NAME)"
	@echo "  $(YELLOW)Imagen Docker:$(NC) $(DOCKER_IMAGE_NAME):$(DOCKER_TAG)"
	@echo "  $(YELLOW)Puerto API:$(NC) 8003"
	@echo "  $(YELLOW)Directorio:$(NC) $(PWD)"
	@echo "  $(YELLOW)Python:$(NC) $(shell $(PYTHON) --version 2>&1)"
	@echo "  $(YELLOW)Docker:$(NC) $(shell docker --version 2>&1 || echo 'No instalado')"
	@echo "  $(YELLOW)Docker Compose:$(NC) $(shell docker-compose --version 2>&1 || echo 'No instalado')"

# === DOCUMENTACIÓN ===
docs: ## Generar documentación
	@echo "$(BLUE)📚 La documentación está en README.md$(NC)"
	@echo "  📖 Estructura del proyecto: README.md"
	@echo "  🔧 Configuración: .env.example"
	@echo "  🧪 Tests: tests/README.md"
	@echo "  📊 API Docs: http://localhost:8003/docs (cuando esté ejecutándose)"

# === COMANDOS RÁPIDOS ===
up: deploy ## Alias para deploy
down: ## Detener todos los servicios
	@docker-compose down
	@echo "$(GREEN)✅ Servicios detenidos$(NC)"

restart: ## Reiniciar servicios
	@echo "$(BLUE)🔄 Reiniciando servicios...$(NC)"
	@docker-compose restart
	@echo "$(GREEN)✅ Servicios reiniciados$(NC)"
