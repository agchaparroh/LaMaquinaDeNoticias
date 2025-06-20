# Tests para nginx_reverse_proxy

Este directorio contiene los tests automatizados para el módulo nginx_reverse_proxy.

## Estructura de Tests

```
tests/
├── __init__.py              # Paquete Python
├── conftest.py              # Fixtures compartidos
├── unit/                    # Tests unitarios
│   └── test_configuration.py # Tests de configuración
└── integration/             # Tests de integración
    ├── test_routing.py      # Tests de routing
    ├── test_security.py     # Tests de seguridad
    ├── test_docker.py       # Tests de Docker
    ├── test_performance.py  # Tests de performance
    └── test_error_handling.py # Tests de errores
```

## Requisitos

1. **Docker y Docker Compose** instalados y funcionando
2. **Python 3.8+** con pip
3. **Red Docker** `lamacquina_network` creada
4. **Puerto 80** disponible en el host

## Instalación

```bash
# Instalar dependencias de test
pip install -r requirements-test.txt
```

## Ejecución de Tests

### Ejecutar todos los tests
```bash
pytest tests/ -v
```

### Ejecutar solo tests unitarios
```bash
pytest tests/unit/ -v
```

### Ejecutar solo tests de integración
```bash
pytest tests/integration/ -v
```

### Ejecutar con cobertura
```bash
pytest tests/ --cov=. --cov-report=term-missing
```

### Ejecutar tests en paralelo
```bash
pytest tests/ -n auto -v
```

### Ejecutar un test específico
```bash
pytest tests/integration/test_routing.py::TestNginxRouting::test_api_health_routing -v
```

## Fixtures Disponibles

- `project_root`: Ruta al directorio raíz del módulo
- `nginx_config_file`: Ruta a nginx.conf
- `env_file`: Ruta al archivo .env
- `nginx_container_running`: Container nginx en ejecución
- `mock_backend_container`: Backend mock para tests
- `mock_frontend_container`: Frontend mock para tests
- `http_session`: Sesión HTTP reutilizable

## Categorías de Tests

### Tests Unitarios
- **Configuración**: Validan sintaxis y estructura de archivos
- No requieren Docker en ejecución
- Muy rápidos de ejecutar

### Tests de Integración
- **Routing**: Verifican redirección correcta de peticiones
- **Seguridad**: Validan headers y rate limiting
- **Docker**: Comprueban integración con containers
- **Performance**: Verifican optimizaciones
- **Errores**: Validan manejo de casos edge

## Notas Importantes

1. **Containers Mock**: Los tests crean containers temporales para simular backend y frontend
2. **Limpieza**: Los fixtures se encargan de limpiar recursos después de los tests
3. **Red Docker**: Se requiere que exista `lamacquina_network`
4. **Timeouts**: Algunos tests pueden tardar debido a esperas de containers

## Troubleshooting

### Error: Puerto 80 en uso
```bash
# Verificar qué está usando el puerto
sudo lsof -i :80
# O en Windows
netstat -ano | findstr :80
```

### Error: Red Docker no existe
```bash
docker network create lamacquina_network
```

### Error: Permisos de Docker
```bash
# Linux: Agregar usuario al grupo docker
sudo usermod -aG docker $USER
# Luego cerrar sesión y volver a entrar
```

### Tests lentos
- Usar `-n auto` para ejecución paralela
- Ejecutar solo la categoría necesaria
- Verificar que Docker tiene recursos suficientes

## Coverage Report

Para generar un reporte HTML de cobertura:
```bash
pytest tests/ --cov=. --cov-report=html
# Abrir htmlcov/index.html en el navegador
```

## CI/CD

Estos tests están diseñados para ejecutarse en pipelines CI/CD. Ejemplo para GitHub Actions:

```yaml
- name: Run nginx tests
  run: |
    cd src/nginx_reverse_proxy
    pip install -r requirements-test.txt
    pytest tests/ -v --tb=short
```
