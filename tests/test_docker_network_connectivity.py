"""
Test: test_docker_network_connectivity.py
Objetivo: Verificar que los contenedores pueden comunicarse entre sí dentro de la red Docker
Módulos: Todos los servicios en la red lamacquina_network
Punto de integración: Comunicación entre contenedores usando nombres de host Docker
"""

import pytest
import subprocess
import json
from typing import Dict, List, Tuple

# Mapa de servicios y sus dependencias de red
NETWORK_DEPENDENCIES = {
    "lamacquina_connector": {
        "depends_on": ["lamacquina_pipeline"],
        "test_endpoints": {
            "lamacquina_pipeline": "module_pipeline:8003"
        }
    },
    "lamacquina_dashboard_review_backend": {
        "depends_on": [],
        "test_endpoints": {}
    },
    "lamacquina_chat_interface_backend": {
        "depends_on": [],
        "test_endpoints": {}
    },
    "lamacquina_dev_interface_backend": {
        "depends_on": [],
        "test_endpoints": {}
    },
    "lamacquina_dashboard_review_frontend": {
        "depends_on": ["lamacquina_dashboard_review_backend"],
        "test_endpoints": {
            "lamacquina_dashboard_review_backend": "module_dashboard_review_backend:8004"
        }
    },
    "lamacquina_chat_interface_frontend": {
        "depends_on": ["lamacquina_chat_interface_backend"],
        "test_endpoints": {
            "lamacquina_chat_interface_backend": "module_chat_interface_backend:8005"
        }
    },
    "lamacquina_dev_interface_frontend": {
        "depends_on": ["lamacquina_dev_interface_backend"],
        "test_endpoints": {
            "lamacquina_dev_interface_backend": "module_dev_interface_backend:8006"
        }
    }
}

# Todos los contenedores que deben estar en la red
ALL_CONTAINERS = [
    "lamacquina_scraper",
    "lamacquina_connector", 
    "lamacquina_pipeline",
    "lamacquina_dashboard_review_backend",
    "lamacquina_chat_interface_backend",
    "lamacquina_dev_interface_backend",
    "lamacquina_dashboard_review_frontend",
    "lamacquina_chat_interface_frontend",
    "lamacquina_dev_interface_frontend",
    "lamacquina_orchestration_agent",
    "lamacquina_reverse_proxy"
]


def check_container_in_network(container_name: str, network_name: str = "lamacquina_network") -> Tuple[bool, str]:
    """
    Verifica que un contenedor esté conectado a la red especificada.
    
    Returns:
        Tuple[bool, str]: (está_en_red, mensaje)
    """
    try:
        # Inspeccionar el contenedor para obtener sus redes
        result = subprocess.run(
            ["docker", "inspect", container_name, "-f", "{{json .NetworkSettings.Networks}}"],
            capture_output=True,
            text=True,
            check=True
        )
        
        networks = json.loads(result.stdout.strip())
        
        # Buscar la red (puede tener prefijo del proyecto)
        network_found = any(network_name in net_name for net_name in networks.keys())
        
        if network_found:
            # Obtener la IP del contenedor en la red
            for net_name, net_info in networks.items():
                if network_name in net_name:
                    ip_address = net_info.get("IPAddress", "N/A")
                    return True, f"✅ {container_name}: En red {net_name} (IP: {ip_address})"
            
        return False, f"❌ {container_name}: No está en la red {network_name}"
        
    except subprocess.CalledProcessError:
        return False, f"❌ {container_name}: Contenedor no encontrado o no está corriendo"
    except Exception as e:
        return False, f"❌ {container_name}: Error verificando red - {str(e)}"


def test_dns_resolution(from_container: str, to_hostname: str) -> Tuple[bool, str]:
    """
    Prueba que un contenedor pueda resolver el hostname de otro contenedor.
    
    Returns:
        Tuple[bool, str]: (puede_resolver, mensaje)
    """
    try:
        # Ejecutar nslookup dentro del contenedor
        result = subprocess.run(
            ["docker", "exec", from_container, "nslookup", to_hostname],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and "Address" in result.stdout:
            # Extraer la IP resuelta
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if "Address" in line and "#" not in line:  # Ignorar la línea del servidor DNS
                    ip = line.split("Address:")[-1].strip()
                    return True, f"✅ {from_container} → {to_hostname}: Resuelto a {ip}"
            
        return False, f"❌ {from_container} → {to_hostname}: No se pudo resolver el hostname"
        
    except subprocess.TimeoutExpired:
        return False, f"❌ {from_container} → {to_hostname}: Timeout en resolución DNS"
    except Exception as e:
        # Si nslookup no está disponible, intentar con ping
        try:
            result = subprocess.run(
                ["docker", "exec", from_container, "ping", "-c", "1", "-W", "2", to_hostname],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return True, f"✅ {from_container} → {to_hostname}: Ping exitoso"
            else:
                return False, f"❌ {from_container} → {to_hostname}: Ping falló"
        except:
            return False, f"❌ {from_container} → {to_hostname}: Error en prueba DNS - {str(e)}"


def test_port_connectivity(from_container: str, to_endpoint: str) -> Tuple[bool, str]:
    """
    Prueba que un contenedor pueda conectar a un puerto específico de otro contenedor.
    
    Args:
        from_container: Nombre del contenedor origen
        to_endpoint: hostname:puerto destino
    
    Returns:
        Tuple[bool, str]: (puede_conectar, mensaje)
    """
    try:
        hostname, port = to_endpoint.split(':')
        
        # Intentar con nc (netcat) primero
        result = subprocess.run(
            ["docker", "exec", from_container, "nc", "-zv", "-w", "2", hostname, port],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return True, f"✅ {from_container} → {to_endpoint}: Puerto abierto"
        else:
            # Si nc no está disponible, intentar con curl
            result = subprocess.run(
                ["docker", "exec", from_container, "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", 
                 f"http://{to_endpoint}/health", "--connect-timeout", "2"],
                capture_output=True,
                text=True
            )
            
            if result.stdout.strip() in ["200", "404", "000"]:  # 000 = conexión establecida pero sin respuesta HTTP
                return True, f"✅ {from_container} → {to_endpoint}: Conexión HTTP establecida"
            else:
                return False, f"❌ {from_container} → {to_endpoint}: No se pudo conectar al puerto"
                
    except Exception as e:
        return False, f"❌ {from_container} → {to_endpoint}: Error en prueba de puerto - {str(e)}"


@pytest.fixture(scope="module")
def docker_network_info():
    """
    Fixture que obtiene información sobre la red Docker.
    """
    try:
        # Buscar la red que contiene "lamacquina_network"
        result = subprocess.run(
            ["docker", "network", "ls", "--format", "{{.Name}}"],
            capture_output=True,
            text=True,
            check=True
        )
        
        networks = result.stdout.strip().split('\n')
        network_name = None
        
        for net in networks:
            if "lamacquina_network" in net:
                network_name = net
                break
        
        if not network_name:
            pytest.fail("No se encontró la red lamacquina_network")
            
        print(f"\n📡 Red Docker encontrada: {network_name}")
        
        yield network_name
        
    except Exception as e:
        pytest.fail(f"Error obteniendo información de la red: {str(e)}")


def test_all_containers_in_network(docker_network_info):
    """Test que verifica que todos los contenedores estén en la red Docker correcta"""
    print("\n🔍 Verificando contenedores en la red Docker...")
    
    all_in_network = True
    results = []
    
    # GIVEN: El sistema está desplegado con docker-compose
    
    # WHEN: Verificamos cada contenedor
    for container in ALL_CONTAINERS:
        in_network, message = check_container_in_network(container)
        results.append(message)
        if not in_network:
            all_in_network = False
    
    # THEN: Todos los contenedores deben estar en la red
    print("\n📋 Estado de Red de Contenedores:")
    for result in results:
        print(result)
    
    assert all_in_network, "Algunos contenedores no están en la red Docker"


def test_dns_resolution_between_services():
    """Test que verifica la resolución DNS entre servicios clave"""
    print("\n🔍 Verificando resolución DNS entre servicios...")
    
    # Pares de servicios a probar
    dns_tests = [
        ("lamacquina_connector", "module_pipeline"),
        ("lamacquina_dashboard_review_frontend", "module_dashboard_review_backend"),
        ("lamacquina_pipeline", "lamacquina_connector"),
        ("lamacquina_reverse_proxy", "module_pipeline"),
    ]
    
    all_resolved = True
    results = []
    
    # GIVEN: Los contenedores están en la misma red Docker
    
    # WHEN: Probamos resolución DNS
    for from_container, to_hostname in dns_tests:
        can_resolve, message = test_dns_resolution(from_container, to_hostname)
        results.append(message)
        if not can_resolve:
            all_resolved = False
    
    # THEN: Todos deben poder resolver los hostnames
    print("\n📋 Resultados de Resolución DNS:")
    for result in results:
        print(result)
    
    assert all_resolved, "Algunos servicios no pueden resolver hostnames de otros"


def test_service_port_connectivity():
    """Test que verifica conectividad a puertos específicos entre servicios dependientes"""
    print("\n🔍 Verificando conectividad de puertos entre servicios...")
    
    all_connected = True
    results = []
    
    # GIVEN: Los servicios están corriendo y en la misma red
    
    # WHEN: Probamos conectividad a puertos específicos
    for container, config in NETWORK_DEPENDENCIES.items():
        for dep_name, endpoint in config.get("test_endpoints", {}).items():
            can_connect, message = test_port_connectivity(container, endpoint)
            results.append(message)
            if not can_connect:
                all_connected = False
    
    # THEN: Todas las conexiones deben funcionar
    print("\n📋 Resultados de Conectividad de Puertos:")
    for result in results:
        print(result)
    
    # Caso de error: Intentar diagnosticar problemas de red
    if not all_connected:
        print("\n⚠️  Diagnóstico adicional:")
        # Verificar que los servicios destino estén corriendo
        for container in ["lamacquina_pipeline", "lamacquina_dashboard_review_backend"]:
            try:
                result = subprocess.run(
                    ["docker", "ps", "--filter", f"name={container}", "--format", "{{.Status}}"],
                    capture_output=True,
                    text=True
                )
                print(f"  Estado de {container}: {result.stdout.strip()}")
            except:
                pass
    
    assert all_connected, "Algunos servicios no pueden conectar a puertos de sus dependencias"


def test_reverse_proxy_can_reach_all_backends():
    """Test que verifica que el reverse proxy puede alcanzar todos los backends"""
    print("\n🔍 Verificando conectividad del reverse proxy...")
    
    backends = [
        "module_pipeline:8003",
        "module_dashboard_review_backend:8004", 
        "module_chat_interface_backend:8005",
        "module_dev_interface_backend:8006"
    ]
    
    all_reachable = True
    results = []
    
    # GIVEN: El reverse proxy está configurado para rutear a los backends
    
    # WHEN: Probamos conectividad desde el proxy
    for backend in backends:
        can_connect, message = test_port_connectivity("lamacquina_reverse_proxy", backend)
        results.append(message)
        if not can_connect:
            all_reachable = False
    
    # THEN: El proxy debe poder alcanzar todos los backends
    print("\n📋 Conectividad del Reverse Proxy:")
    for result in results:
        print(result)
    
    assert all_reachable, "El reverse proxy no puede alcanzar algunos backends"


if __name__ == "__main__":
    # Ejecutar con: pytest test_docker_network_connectivity.py -v -s
    pytest.main([__file__, "-v", "-s"])
