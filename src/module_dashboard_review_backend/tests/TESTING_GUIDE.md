# Testing Documentation - Dashboard Review Backend

## Overview

This module includes comprehensive testing coverage including:

- **Unit Tests**: Basic functionality testing with mocked dependencies
- **Performance Tests**: Response time, throughput, and resource usage
- **Concurrency Tests**: Thread safety and concurrent request handling
- **Load Tests**: Behavior under sustained and spike loads
- **Recovery Tests**: Resilience and recovery from failures
- **Integration Tests**: Real Supabase database testing

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_api/               # API endpoint tests
│   ├── test_dashboard.py   # Dashboard endpoints
│   └── test_feedback.py    # Feedback endpoints
├── test_services/          # Service layer tests
│   ├── test_feedback_service.py
│   ├── test_hechos_service.py
│   └── test_supabase_client.py
├── performance/           # Performance testing
│   └── test_api_performance.py
├── concurrency/          # Concurrency testing
│   └── test_concurrent_operations.py
├── load/                 # Load testing
│   └── test_load_scenarios.py
├── recovery/             # Recovery testing
│   └── test_recovery_scenarios.py
└── integration/          # Integration tests
    └── test_supabase_integration.py
```

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

### Run All Tests

```bash
# Run all tests with coverage
pytest

# Run with parallel execution
pytest -n auto

# Run with verbose output
pytest -v
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/test_api tests/test_services

# Performance tests
pytest tests/performance -m performance

# Concurrency tests
pytest tests/concurrency -m concurrency

# Load tests
pytest tests/load -m load

# Recovery tests
pytest tests/recovery -m recovery

# Integration tests (requires test database)
pytest tests/integration -m integration
```

### Run with Specific Markers

```bash
# Run only fast tests
pytest -m "not slow"

# Run performance and load tests
pytest -m "performance or load"

# Exclude integration tests
pytest -m "not integration"
```

## Test Categories

### 1. Performance Tests

Located in `tests/performance/test_api_performance.py`

Tests include:
- Response time measurements (P50, P95, P99)
- Memory usage tracking
- CPU usage patterns
- Response size impact
- Concurrent request performance
- Cache effectiveness
- Error handling performance

**Run performance tests:**
```bash
pytest tests/performance -v
```

**Key metrics tested:**
- Median response time < 100ms
- P95 response time < 200ms
- P99 response time < 500ms
- Memory growth < 50MB over 500 requests

### 2. Concurrency Tests

Located in `tests/concurrency/test_concurrent_operations.py`

Tests include:
- Concurrent read operations
- Concurrent write operations
- Read/write race conditions
- Singleton thread safety
- Request ordering
- Connection pool behavior

**Run concurrency tests:**
```bash
pytest tests/concurrency -v
```

**Key aspects tested:**
- Thread-safe singleton pattern
- No data corruption under concurrent access
- Proper handling of concurrent feedback submissions
- Connection pool management

### 3. Load Tests

Located in `tests/load/test_load_scenarios.py`

Tests include:
- Sustained normal load (50 RPS for 30s)
- Spike load (30 → 200 → 30 RPS)
- Sustained high load (150 RPS for 60s)
- Read-heavy workload (95% reads)
- Write-heavy workload (100% writes)
- Memory leak detection
- Connection exhaustion
- Cascading failure prevention

**Run load tests:**
```bash
pytest tests/load -v -s
```

**Key metrics:**
- >99% success rate at normal load
- >90% success rate during spikes
- <50% performance degradation under high load
- No memory leaks over extended runs

### 4. Recovery Tests

Located in `tests/recovery/test_recovery_scenarios.py`

Tests include:
- Database connection recovery
- Timeout handling
- Partial data recovery
- Connection pool recovery
- Service restart recovery
- Memory pressure recovery
- Cascading failure recovery
- Circuit breaker behavior

**Run recovery tests:**
```bash
pytest tests/recovery -v
```

**Key behaviors:**
- Automatic recovery after database outages
- Fast failure for timeouts
- Graceful degradation
- Circuit breaker prevents cascade failures

### 5. Integration Tests

Located in `tests/integration/test_supabase_integration.py`

**Requirements:**
- Set `TEST_SUPABASE_URL` environment variable
- Set `TEST_SUPABASE_KEY` environment variable
- Point to a test Supabase instance

Tests include:
- Real database connections
- Actual data operations
- Constraint validation
- Performance measurements
- Concurrent operations

**Run integration tests:**
```bash
# Set environment variables first
export TEST_SUPABASE_URL="https://your-test-project.supabase.co"
export TEST_SUPABASE_KEY="your-test-anon-key"

# Run tests
pytest tests/integration -v
```

## Coverage Reports

After running tests, coverage reports are available:

- **HTML Report**: `htmlcov/index.html`
- **Terminal Report**: Shown after test run
- **JSON Report**: `coverage.json`

View HTML coverage report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Performance Benchmarks

Expected performance benchmarks:

| Metric | Target | Actual |
|--------|--------|--------|
| Health Check | < 5ms | - |
| Simple Query | < 100ms | - |
| Filtered Query | < 150ms | - |
| Paginated Query | < 100ms | - |
| Feedback Submit | < 50ms | - |

## Load Testing with Locust

For more extensive load testing, use Locust:

```python
# locustfile.py
from locust import HttpUser, task, between

class DashboardUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def get_hechos(self):
        self.client.get("/dashboard/hechos_revision")
    
    @task(1)
    def get_filters(self):
        self.client.get("/dashboard/filtros/opciones")
    
    @task(1)
    def submit_feedback(self):
        self.client.post(
            "/dashboard/feedback/hecho/1/importancia_feedback",
            json={
                "importancia_editor_final": 8,
                "usuario_id_editor": "load_test"
            }
        )
```

Run Locust:
```bash
locust -f locustfile.py --host=http://localhost:8004
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run tests
      run: |
        pytest -v --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure `PYTHONPATH` includes project root
   ```bash
   export PYTHONPATH=$PYTHONPATH:.
   ```

2. **Async test failures**: Check `pytest-asyncio` is installed
   ```bash
   pip install pytest-asyncio
   ```

3. **Integration test skips**: Set test database credentials
   ```bash
   export TEST_SUPABASE_URL="..."
   export TEST_SUPABASE_KEY="..."
   ```

4. **Performance test variations**: Run multiple times for consistency
   ```bash
   pytest tests/performance --count=3
   ```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Cleanup**: Always clean up test data
3. **Mocking**: Mock external dependencies for unit tests
4. **Real Testing**: Use integration tests for critical paths
5. **Performance**: Set realistic performance targets
6. **Documentation**: Document expected vs actual metrics

## Future Improvements

1. **Contract Testing**: Add API contract tests
2. **Chaos Testing**: Introduce random failures
3. **Security Testing**: Add security-focused tests
4. **E2E Testing**: Full end-to-end scenarios
5. **Monitoring**: Integration with APM tools
