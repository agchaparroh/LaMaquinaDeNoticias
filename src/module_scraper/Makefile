# Makefile para el módulo scraper
.PHONY: help test test-unit test-integration test-spiders test-e2e test-all coverage clean install docker-build docker-test lint format check-format validate-spiders

# Variables
PYTHON := python
PIP := pip
PYTEST := pytest
PROJECT := module_scraper

# Colores
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Mostrar esta ayuda
	@echo "$(GREEN)Comandos disponibles para $(PROJECT):$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Instalar dependencias
	@echo "$(GREEN)Instalando dependencias...$(NC)"
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt 2>/dev/null || true
	playwright install chromium

test: ## Ejecutar todos los tests
	@echo "$(GREEN)Ejecutando todos los tests...$(NC)"
	$(PYTHON) run_all_tests.py

test-unit: ## Ejecutar solo tests unitarios
	@echo "$(GREEN)Ejecutando tests unitarios...$(NC)"
	$(PYTEST) tests/unit/ -v

test-integration: ## Ejecutar solo tests de integración
	@echo "$(GREEN)Ejecutando tests de integración...$(NC)"
	$(PYTEST) tests/integration/ -v -m integration

test-spiders: ## Ejecutar tests de spiders
	@echo "$(GREEN)Ejecutando tests de spiders...$(NC)"
	$(PYTHON) tests/test_spiders/run_spider_tests.py --report

test-e2e: ## Ejecutar tests end-to-end
	@echo "$(GREEN)Ejecutando tests E2E...$(NC)"
	$(PYTEST) tests/e2e/ -v

test-middlewares: ## Ejecutar tests de middlewares
	@echo "$(GREEN)Ejecutando tests de middlewares...$(NC)"
	$(PYTEST) tests/test_middlewares/ -v

test-error: ## Ejecutar tests de error handling
	@echo "$(GREEN)Ejecutando tests de error handling...$(NC)"
	$(PYTEST) tests/test_error_handling/ -v

test-fast: ## Ejecutar tests rápidos (sin los marcados como slow)
	@echo "$(GREEN)Ejecutando tests rápidos...$(NC)"
	$(PYTEST) tests/ -v -m "not slow"

coverage: ## Generar reporte de cobertura
	@echo "$(GREEN)Generando reporte de cobertura...$(NC)"
	$(PYTHON) run_all_tests.py --coverage --html
	@echo "$(YELLOW)Reporte HTML disponible en: htmlcov/index.html$(NC)"

coverage-report: ## Mostrar reporte de cobertura en terminal
	@echo "$(GREEN)Reporte de cobertura:$(NC)"
	$(PYTEST) tests/ --cov=scraper_core --cov-report=term-missing

validate-spiders: ## Validar conformidad de todos los spiders
	@echo "$(GREEN)Validando todos los spiders...$(NC)"
	$(PYTHON) tests/test_spiders/run_spider_tests.py --report

validate-spider: ## Validar un spider específico (usar: make validate-spider SPIDER=nombre)
	@echo "$(GREEN)Validando spider: $(SPIDER)$(NC)"
	$(PYTHON) tests/test_spiders/run_spider_tests.py --spider $(SPIDER)

clean: ## Limpiar archivos temporales y cache
	@echo "$(GREEN)Limpiando archivos temporales...$(NC)"
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '.pytest_cache' -delete
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf test-results.xml
	rm -rf .scrapy/

docker-build: ## Construir imagen Docker
	@echo "$(GREEN)Construyendo imagen Docker...$(NC)"
	docker-compose build scraper

docker-test: ## Ejecutar tests en Docker
	@echo "$(GREEN)Ejecutando tests en Docker...$(NC)"
	docker-compose --profile test up scraper-test

docker-shell: ## Abrir shell en contenedor Docker
	@echo "$(GREEN)Abriendo shell en contenedor...$(NC)"
	docker-compose --profile dev run --rm scraper-dev bash

lint: ## Ejecutar linters
	@echo "$(GREEN)Ejecutando linters...$(NC)"
	flake8 scraper_core/ tests/ --max-line-length=120 --exclude=__pycache__
	pylint scraper_core/ tests/ --disable=C0114,C0115,C0116 || true

format: ## Formatear código con black
	@echo "$(GREEN)Formateando código...$(NC)"
	black scraper_core/ tests/ --line-length=120

check-format: ## Verificar formato sin cambiar archivos
	@echo "$(GREEN)Verificando formato...$(NC)"
	black scraper_core/ tests/ --line-length=120 --check

run-spider: ## Ejecutar un spider (usar: make run-spider SPIDER=nombre)
	@echo "$(GREEN)Ejecutando spider: $(SPIDER)$(NC)"
	scrapy crawl $(SPIDER) -L INFO

list-spiders: ## Listar todos los spiders disponibles
	@echo "$(GREEN)Spiders disponibles:$(NC)"
	scrapy list

check-settings: ## Verificar configuración de Scrapy
	@echo "$(GREEN)Verificando configuración...$(NC)"
	scrapy check

shell: ## Abrir shell de Scrapy (usar: make shell URL=https://example.com)
	@echo "$(GREEN)Abriendo shell de Scrapy...$(NC)"
	scrapy shell "$(URL)"

# Targets de desarrollo
dev-install: install ## Instalar dependencias de desarrollo
	@echo "$(GREEN)Instalando herramientas de desarrollo...$(NC)"
	$(PIP) install black flake8 pylint pytest-watch

watch-tests: ## Ejecutar tests en modo watch
	@echo "$(GREEN)Ejecutando tests en modo watch...$(NC)"
	ptw tests/ -- -v

# Estadísticas
stats: ## Mostrar estadísticas del proyecto
	@echo "$(GREEN)Estadísticas del proyecto:$(NC)"
	@echo "Archivos Python: $$(find scraper_core tests -name '*.py' | wc -l)"
	@echo "Líneas de código: $$(find scraper_core -name '*.py' -exec cat {} \; | wc -l)"
	@echo "Líneas de tests: $$(find tests -name '*.py' -exec cat {} \; | wc -l)"
	@echo "Spiders: $$(scrapy list | wc -l)"
