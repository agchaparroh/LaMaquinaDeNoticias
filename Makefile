# Makefile principal - La Máquina de Noticias
# Optimizado para hooks de Claude Code

.PHONY: help lint-file format-file lint-all format-all install-tools

# Colores para output
GREEN = \033[0;32m
YELLOW = \033[1;33m
NC = \033[0m

help:
	@echo "$(GREEN)La Máquina de Noticias - Comandos de Linting$(NC)"
	@echo "  make format-file FILE=<path>  - Formatear archivo específico"
	@echo "  make lint-file FILE=<path>    - Verificar archivo específico"
	@echo "  make format-all               - Formatear todo el proyecto"
	@echo "  make lint-all                 - Verificar todo el proyecto"
	@echo "  make install-tools            - Instalar herramientas de linting"

# === COMANDOS PARA HOOKS (por archivo) ===
format-file:
	@if [ -z "$(FILE)" ]; then \
		echo "$(YELLOW)Uso: make format-file FILE=<path>$(NC)"; \
		exit 1; \
	fi
	@if echo "$(FILE)" | grep -qE "\.(py)$$"; then \
		echo "$(GREEN)Formateando Python: $(FILE)$(NC)"; \
		black "$(FILE)" 2>/dev/null || true; \
		ruff check --fix "$(FILE)" --select I 2>/dev/null || true; \
	elif echo "$(FILE)" | grep -qE "\.(js|jsx|ts|tsx)$$"; then \
		echo "$(GREEN)Formateando JS/TS: $(FILE)$(NC)"; \
		dir=$$(dirname "$(FILE)"); \
		if [ -f "$$dir/../package.json" ]; then \
			cd "$$dir/.." && npm run format -- "$(FILE)" 2>/dev/null || true; \
		fi; \
	fi

lint-file:
	@if [ -z "$(FILE)" ]; then \
		echo "$(YELLOW)Uso: make lint-file FILE=<path>$(NC)"; \
		exit 1; \
	fi
	@if echo "$(FILE)" | grep -qE "\.(py)$$"; then \
		echo "$(GREEN)Verificando Python: $(FILE)$(NC)"; \
		ruff check "$(FILE)" 2>/dev/null || true; \
	elif echo "$(FILE)" | grep -qE "\.(js|jsx|ts|tsx)$$"; then \
		echo "$(GREEN)Verificando JS/TS: $(FILE)$(NC)"; \
		dir=$$(dirname "$(FILE)"); \
		if [ -f "$$dir/../package.json" ]; then \
			cd "$$dir/.." && npm run lint -- "$(FILE)" 2>/dev/null || true; \
		fi; \
	fi

# === COMANDOS PARA TODO EL PROYECTO ===
format-all:
	@echo "$(GREEN)Formateando archivos Python...$(NC)"
	@black src/ tests/ 2>/dev/null || echo "$(YELLOW)Black no instalado$(NC)"
	@ruff check --fix src/ tests/ --select I 2>/dev/null || echo "$(YELLOW)Ruff no instalado$(NC)"
	@echo "$(GREEN)Formateando archivos JS/TS...$(NC)"
	@for dir in src/module_dashboard_review_frontend src/module_spider_factory_frontend; do \
		if [ -d "$$dir" ]; then \
			echo "  Procesando $$dir..."; \
			cd "$$dir" && npm run format 2>/dev/null || true; \
			cd - > /dev/null; \
		fi; \
	done

lint-all:
	@echo "$(GREEN)Verificando archivos Python...$(NC)"
	@ruff check src/ tests/ 2>/dev/null || echo "$(YELLOW)Ruff no instalado$(NC)"
	@echo "$(GREEN)Verificando archivos JS/TS...$(NC)"
	@for dir in src/module_dashboard_review_frontend src/module_spider_factory_frontend; do \
		if [ -d "$$dir" ]; then \
			echo "  Procesando $$dir..."; \
			cd "$$dir" && npm run lint 2>/dev/null || true; \
			cd - > /dev/null; \
		fi; \
	done

# === INSTALACIÓN DE HERRAMIENTAS ===
install-tools:
	@echo "$(GREEN)Instalando herramientas de linting...$(NC)"
	@echo "$(YELLOW)Instalando herramientas Python...$(NC)"
	@pip install black ruff --upgrade
	@echo "$(YELLOW)Instalando dependencias en módulos JS/TS...$(NC)"
	@for dir in src/module_dashboard_review_frontend src/module_spider_factory_frontend; do \
		if [ -d "$$dir" ]; then \
			echo "  Instalando en $$dir..."; \
			cd "$$dir" && npm install; \
			cd - > /dev/null; \
		fi; \
	done
	@echo "$(GREEN)✅ Herramientas instaladas$(NC)"

# === COMANDOS RÁPIDOS ===
fix: format-all
check: lint-all