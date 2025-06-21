import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_docker_network_connectivity import (
    check_container_in_network, 
    test_dns_resolution,
    test_port_connectivity,
    ALL_CONTAINERS
)

print("🔍 Ejecutando verificación manual de conectividad Docker...\n")

# Verificar red
print("=" * 60)
print("VERIFICACIÓN DE RED:")
print("=" * 60)
for container in ALL_CONTAINERS[:3]:  # Probar solo algunos
    in_network, message = check_container_in_network(container)
    print(message)

# Verificar DNS
print("\n" + "=" * 60)
print("RESOLUCIÓN DNS:")
print("=" * 60)
can_resolve, message = test_dns_resolution("lamacquina_connector", "module_pipeline")
print(message)

# Verificar puerto
print("\n" + "=" * 60)
print("CONECTIVIDAD DE PUERTO:")
print("=" * 60)
can_connect, message = test_port_connectivity("lamacquina_connector", "module_pipeline:8003")
print(message)

print("\n✅ Verificación de ejemplo completa")
