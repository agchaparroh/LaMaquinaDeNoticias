import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_all_services_health import check_service_health, check_container_running, SERVICES, WORKER_SERVICES

print("🔍 Ejecutando verificación manual de servicios...\n")

# Verificar servicios HTTP
print("=" * 60)
print("SERVICIOS HTTP:")
print("=" * 60)
for service_name, config in SERVICES.items():
    is_healthy, message = check_service_health(service_name, config)
    print(message)

# Verificar workers
print("\n" + "=" * 60)
print("SERVICIOS WORKER:")
print("=" * 60)
for service_name, container_name in WORKER_SERVICES.items():
    is_running, message = check_container_running(container_name)
    print(message)

print("\n✅ Verificación completa")
