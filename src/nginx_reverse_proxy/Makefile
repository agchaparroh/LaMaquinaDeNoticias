# Makefile - nginx_reverse_proxy simple operations
# Comandos útiles para desarrollo y deployment

.PHONY: help build deploy stop clean test logs status integrate test-unit test-integration test-all test-coverage

# Default target
help:
	@echo "🚀 nginx_reverse_proxy - Available Commands"
	@echo "==========================================="
	@echo ""
	@echo "📦 Build & Deploy:"
	@echo "  make build      - Build Docker image"
	@echo "  make deploy     - Deploy standalone"
	@echo "  make integrate  - Integrate with main docker-compose.yml"
	@echo ""
	@echo "🔧 Operations:"
	@echo "  make stop       - Stop container"
	@echo "  make clean      - Stop and remove container"
	@echo "  make restart    - Restart container"
	@echo ""
	@echo "🧪 Testing & Monitoring:"
	@echo "  make test       - Run health checks"
	@echo "  make test-all   - Run all pytest tests"
	@echo "  make test-unit  - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-coverage - Run tests with coverage report"
	@echo "  make logs       - Show container logs"
	@echo "  make status     - Show container status"
	@echo ""
	@echo "💡 Usage Examples:"
	@echo "  make deploy && make test    # Full deployment & test"
	@echo "  make test-all               # Run all pytest tests"
	@echo "  make logs                   # Monitor in real-time"

# Build Docker image
build:
	@echo "📦 Building nginx_reverse_proxy..."
	docker build -t nginx_reverse_proxy .
	@echo "✅ Build completed!"

# Deploy standalone
deploy:
	@echo "🚀 Deploying nginx_reverse_proxy..."
	chmod +x scripts/deploy.sh
	./scripts/deploy.sh

# Integrate with main system
integrate:
	@echo "🔗 Integrating with main system..."
	chmod +x scripts/integration.sh
	./scripts/integration.sh

# Stop container
stop:
	@echo "🛑 Stopping nginx_reverse_proxy..."
	-docker stop nginx_reverse_proxy
	@echo "✅ Container stopped"

# Clean up (stop + remove)
clean:
	@echo "🧹 Cleaning up nginx_reverse_proxy..."
	-docker stop nginx_reverse_proxy
	-docker rm nginx_reverse_proxy
	@echo "✅ Cleanup completed"

# Restart container
restart: stop
	@echo "🔄 Restarting nginx_reverse_proxy..."
	docker start nginx_reverse_proxy || make deploy
	@echo "✅ Container restarted"

# Run health checks
test:
	@echo "🧪 Running health checks..."
	@echo "Testing nginx health..."
	@curl -f http://localhost/nginx-health && echo "✅ Health: OK" || echo "❌ Health: FAILED"
	@echo "Testing API routing..."
	@curl -I http://localhost/api/ &>/dev/null && echo "✅ API: OK" || echo "⚠️  API: No backend"
	@echo "Testing frontend routing..."
	@curl -I http://localhost/ &>/dev/null && echo "✅ Frontend: OK" || echo "⚠️  Frontend: No frontend"

# Show logs
logs:
	@echo "📋 Showing nginx_reverse_proxy logs..."
	docker logs -f nginx_reverse_proxy

# Show status
status:
	@echo "📊 nginx_reverse_proxy Status:"
	@docker ps --filter "name=nginx_reverse_proxy" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Image}}" || echo "Container not running"
	@echo ""
	@echo "🌐 Endpoints:"
	@echo "  Health: http://localhost/nginx-health"
	@echo "  API:    http://localhost/api/"
	@echo "  Frontend: http://localhost/"

# Development helpers
dev-logs:
	@echo "📋 Development logs (access + error)..."
	@docker exec nginx_reverse_proxy sh -c "tail -f /var/log/nginx/access.log & tail -f /var/log/nginx/error.log" 2>/dev/null || echo "Container not running"

dev-shell:
	@echo "🐚 Opening shell in nginx container..."
	docker exec -it nginx_reverse_proxy sh

dev-config:
	@echo "🔧 Showing nginx configuration..."
	docker exec nginx_reverse_proxy cat /etc/nginx/nginx.conf

# Network operations
network-create:
	@echo "📡 Creating lamacquina_network..."
	docker network create lamacquina_network || echo "Network already exists"

network-inspect:
	@echo "🔍 Inspecting lamacquina_network..."
	docker network inspect lamacquina_network

# Quick operations
quick-deploy: build deploy test

quick-restart: stop deploy test

quick-clean: clean build deploy test

# Pytest test commands
test-deps:
	@echo "📦 Installing test dependencies..."
	@pip install -q -r requirements-test.txt 2>/dev/null || pip install -r requirements-test.txt

test-unit: test-deps
	@echo "📝 Running unit tests..."
	@pytest tests/unit/ -v --tb=short

test-integration: test-deps network-create
	@echo "🔗 Running integration tests..."
	@echo "⚠️  Note: This will create temporary containers"
	@pytest tests/integration/ -v --tb=short
	@echo "🧹 Cleaning up test containers..."
	@docker rm -f nginx_reverse_proxy_test mock_dashboard_backend mock_dashboard_frontend 2>/dev/null || true

test-all: test-deps network-create
	@echo "🧪 Running all tests..."
	@pytest tests/ -v --tb=short
	@echo "🧹 Cleaning up test containers..."
	@docker rm -f nginx_reverse_proxy_test mock_dashboard_backend mock_dashboard_frontend 2>/dev/null || true

test-coverage: test-deps network-create
	@echo "📊 Running tests with coverage..."
	@pytest tests/ --cov=. --cov-report=term-missing --cov-report=html
	@echo "🧹 Cleaning up test containers..."
	@docker rm -f nginx_reverse_proxy_test mock_dashboard_backend mock_dashboard_frontend 2>/dev/null || true
	@echo "📈 Coverage report generated in htmlcov/index.html"

test-clean:
	@echo "🧹 Cleaning test artifacts..."
	@docker rm -f nginx_reverse_proxy_test mock_dashboard_backend mock_dashboard_frontend 2>/dev/null || true
	@rm -rf .pytest_cache htmlcov .coverage 2>/dev/null || true
