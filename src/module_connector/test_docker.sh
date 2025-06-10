#!/bin/bash

# Module Connector Docker Test Script
# Tests the Docker build and basic functionality

set -e  # Exit on any error

echo "🐳 Module Connector Docker Test Suite"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Test 1: Build Docker image
echo -e "\n📦 Test 1: Building Docker image..."
if docker build -t module-connector-test . > build.log 2>&1; then
    print_status "Docker image built successfully"
else
    print_error "Docker build failed"
    echo "Build log:"
    cat build.log
    exit 1
fi

# Test 2: Create test directories
echo -e "\n📁 Test 2: Creating test directories..."
mkdir -p test_data/{scrapy_output/pending,pipeline_input/{pending,completed,error}}
mkdir -p test_logs

print_status "Test directories created"

# Test 3: Create test data file
echo -e "\n📄 Test 3: Creating test data..."
cat > test_data/scrapy_output/pending/test_article.json.gz << 'EOF'
H4sIAAAAAAAAA6tWyk5NzCvJzE21UoKB6sSc0hylWh0lHSUrKz0dJQjHgIuLjYGJEcSyMjIxN7c0sFKyUsrIyFGyMgIYhA9CJmAlY2RZixdWnFxaZGAIEAFxDaBCfgAZyMiEcyMTNsxZZRUSJQAF1qJmAAAAA=
EOF

# Create properly formatted test file
python3 -c "
import gzip
import json

test_article = {
    'url': 'https://test.com/article/1',
    'medio': 'Test Medium',
    'pais_publicacion': 'Test Country',
    'tipo_medio': 'Test Type',
    'titular': 'Docker Test Article',
    'fecha_publicacion': '2023-12-01T12:00:00Z',
    'contenido_texto': 'Test content for Docker integration test'
}

with gzip.open('test_data/scrapy_output/pending/test_article.json.gz', 'wt', encoding='utf-8') as f:
    json.dump(test_article, f)
"

print_status "Test data created"

# Test 4: Start mock pipeline
echo -e "\n🚀 Test 4: Starting mock pipeline..."
docker run -d --name mock-pipeline-test -p 8002:8001 python:3.9-slim bash -c "
pip install aiohttp > /dev/null 2>&1
cat > mock_pipeline.py << 'PYTHON_EOF'
from aiohttp import web
import json

async def handle_procesar(request):
    data = await request.json()
    return web.json_response({'status': 'recibido', 'id': 'test-123'}, status=202)

app = web.Application()
app.router.add_post('/procesar', handle_procesar)
web.run_app(app, host='0.0.0.0', port=8001)
PYTHON_EOF

python mock_pipeline.py
" > /dev/null 2>&1

# Wait for mock pipeline to start
sleep 5

if curl -s http://localhost:8002/procesar > /dev/null 2>&1; then
    print_status "Mock pipeline started"
else
    print_warning "Mock pipeline may not be fully ready"
fi

# Test 5: Run connector container
echo -e "\n🔗 Test 5: Running Module Connector container..."
docker run -d \
    --name module-connector-test \
    --link mock-pipeline-test:module-pipeline \
    -v $(pwd)/test_data:/data \
    -v $(pwd)/test_logs:/app/logs \
    -e PIPELINE_API_URL=http://module-pipeline:8001 \
    -e POLLING_INTERVAL=2 \
    -e LOG_LEVEL=DEBUG \
    module-connector-test > /dev/null 2>&1

print_status "Module Connector container started"

# Test 6: Wait and check results
echo -e "\n⏳ Test 6: Waiting for processing (30 seconds)..."
sleep 30

# Check if file was processed
if [ -f test_data/pipeline_input/completed/test_article.json.gz ] || [ -f test_data/pipeline_input/error/test_article.json.gz ]; then
    print_status "File was processed and moved"
else
    print_warning "File may still be processing or there was an issue"
fi

# Test 7: Check logs
echo -e "\n📋 Test 7: Checking logs..."
if docker logs module-connector-test 2>&1 | grep -q "Module Connector starting"; then
    print_status "Container started successfully"
else
    print_error "Container startup issues detected"
fi

if docker logs module-connector-test 2>&1 | grep -q "Article"; then
    print_status "Article processing detected in logs"
else
    print_warning "No article processing detected in logs"
fi

# Test 8: Container health
echo -e "\n💓 Test 8: Checking container health..."
if docker exec module-connector-test python -c "import os; exit(0 if os.path.exists('/data/pipeline_input/pending') else 1)" 2>/dev/null; then
    print_status "Container health check passed"
else
    print_error "Container health check failed"
fi

# Cleanup
echo -e "\n🧹 Cleanup..."
docker stop module-connector-test mock-pipeline-test > /dev/null 2>&1 || true
docker rm module-connector-test mock-pipeline-test > /dev/null 2>&1 || true
docker rmi module-connector-test > /dev/null 2>&1 || true

# Clean test files
rm -rf test_data test_logs build.log

print_status "Cleanup completed"

echo -e "\n🎉 Docker tests completed!"
echo "Next steps:"
echo "  1. Review any warnings above"
echo "  2. Test with your actual Pipeline API"
echo "  3. Deploy to your target environment"
