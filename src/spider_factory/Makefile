# Makefile para Spider Factory 2.0

.PHONY: help build up down logs shell clean test dev install

# Variables
DOCKER_COMPOSE = docker-compose
DOCKER_COMPOSE_DEV = docker-compose -f docker-compose.dev.yml
BACKEND_CONTAINER = spider_factory_backend
FRONTEND_CONTAINER = spider_factory_frontend
REDIS_CONTAINER = spider_factory_redis

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Docker commands
build: ## Construir imágenes Docker
	$(DOCKER_COMPOSE) build

up: ## Levantar todos los servicios
	$(DOCKER_COMPOSE) up -d

down: ## Detener todos los servicios
	$(DOCKER_COMPOSE) down

logs: ## Ver logs de todos los servicios
	$(DOCKER_COMPOSE) logs -f

logs-backend: ## Ver logs del backend
	$(DOCKER_COMPOSE) logs -f backend

logs-frontend: ## Ver logs del frontend
	$(DOCKER_COMPOSE) logs -f frontend

logs-redis: ## Ver logs de Redis
	$(DOCKER_COMPOSE) logs -f redis

shell-backend: ## Abrir shell en el contenedor backend
	docker exec -it $(BACKEND_CONTAINER) /bin/bash

shell-redis: ## Abrir Redis CLI
	docker exec -it $(REDIS_CONTAINER) redis-cli

# Development commands
dev: ## Levantar solo Redis para desarrollo local
	$(DOCKER_COMPOSE_DEV) up -d

dev-down: ## Detener Redis de desarrollo
	$(DOCKER_COMPOSE_DEV) down

install: ## Instalar dependencias locales
	pip install -r requirements.txt
	cd ../module_spider_factory_frontend && npm install

run-backend: ## Ejecutar backend localmente
	python api.py

run-frontend: ## Ejecutar frontend localmente
	cd ../module_spider_factory_frontend && npm run dev

# Testing
test-syntax: ## Ejecutar test de sintaxis
	python syntax_check.py

test-integration: ## Ejecutar test de integración
	python integration_test.py

test-real: ## Ejecutar test con sitios reales
	python test_real_sites.py

# Cleanup
clean: ## Limpiar archivos generados y logs
	rm -rf __pycache__
	rm -rf generated_spiders/*
	rm -rf logs/*
	rm -f *.json
	find . -name "*.pyc" -delete
	find . -name ".pytest_cache" -type d -exec rm -rf {} +

clean-docker: ## Limpiar volúmenes y contenedores Docker
	$(DOCKER_COMPOSE) down -v
	docker system prune -f

# Utilities
check-health: ## Verificar salud del sistema
	curl -s http://localhost:8000/health | python -m json.tool

create-env: ## Crear archivo .env desde ejemplo
	cp .env.example .env
	@echo "✅ Archivo .env creado. Por favor, edita las variables necesarias."

# Production
prod-build: ## Build para producción
	$(DOCKER_COMPOSE) build --no-cache

prod-up: ## Levantar en producción
	$(DOCKER_COMPOSE) up -d --remove-orphans

prod-restart: ## Reiniciar servicios en producción
	$(DOCKER_COMPOSE) restart

# Monitoring
stats: ## Ver estadísticas de contenedores
	docker stats $(BACKEND_CONTAINER) $(FRONTEND_CONTAINER) $(REDIS_CONTAINER)

ps: ## Ver estado de contenedores
	$(DOCKER_COMPOSE) ps