"""
test_service_restart.py
Test de Resiliencia: Recuperación después de caída de servicios

Valida la recuperación del sistema cuando servicios se reinician:
1. Detección de servicios caídos
2. Reconexión automática
3. Procesamiento de trabajos pendientes
4. Sincronización de estado
5. Prevención de duplicados
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import json
import os
import tempfile


class ServiceRestartScenario:
    """Simula escenarios de caída y recuperación de servicios"""
    
    def __init__(self):
        self.services = {
            "scraper": {"status": "running", "restart_count": 0},
            "connector": {"status": "running", "restart_count": 0},
            "pipeline": {"status": "running", "restart_count": 0},
            "dashboard": {"status": "running", "restart_count": 0}
        }
        
        self.pending_work = {
            "scraper": [],
            "connector": [],
            "pipeline": []
        }
        
        self.processed_items = set()  # Para evitar duplicados
        self.recovery_log = []
        
    def simulate_service_crash(self, service_name: str):
        """Simula la caída de un servicio"""
        if service_name in self.services:
            self.services[service_name]["status"] = "crashed"
            self.recovery_log.append({
                "timestamp": datetime.utcnow().isoformat(),
                "event": "crash",
                "service": service_name
            })
            print(f"💥 Servicio {service_name} ha caído")
    
    def simulate_service_restart(self, service_name: str):
        """Simula el reinicio de un servicio"""
        if service_name in self.services and self.services[service_name]["status"] == "crashed":
            self.services[service_name]["status"] = "restarting"
            self.services[service_name]["restart_count"] += 1
            
            # Simular tiempo de inicio
            time.sleep(0.5)
            
            self.services[service_name]["status"] = "running"
            self.recovery_log.append({
                "timestamp": datetime.utcnow().isoformat(),
                "event": "restart",
                "service": service_name,
                "restart_count": self.services[service_name]["restart_count"]
            })
            print(f"🔄 Servicio {service_name} reiniciado (intento #{self.services[service_name]['restart_count']})")
    
    def add_pending_work(self, service: str, work_item: dict):
        """Agrega trabajo pendiente para un servicio"""
        if service in self.pending_work:
            self.pending_work[service].append(work_item)
    
    async def process_pending_work(self, service: str) -> dict:
        """Procesa trabajo pendiente después de recuperación"""
        if service not in self.pending_work:
            return {"processed": 0, "duplicates": 0}
        
        processed = 0
        duplicates = 0
        
        for item in self.pending_work[service]:
            item_id = item.get("id", str(item))
            
            if item_id in self.processed_items:
                duplicates += 1
                print(f"   ⚠️ Duplicado detectado: {item_id}")
            else:
                self.processed_items.add(item_id)
                processed += 1
                print(f"   ✅ Procesado: {item_id}")
        
        # Limpiar trabajo pendiente
        self.pending_work[service] = []
        
        return {"processed": processed, "duplicates": duplicates}


def test_connector_recovery_after_crash():
    """Test: Connector se recupera y procesa archivos pendientes"""
    
    scenario = ServiceRestartScenario()
    
    print("\n🔌 Test: Recuperación del Connector después de caída\n")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # GIVEN: Archivos pendientes cuando el Connector cae
        pending_files = []
        for i in range(3):
            filename = f"articulos_pending_{i+1}.json.gz"
            filepath = os.path.join(temp_dir, filename)
            with open(filepath, 'w') as f:
                f.write(f"test content {i+1}")
            pending_files.append(filename)
            
            # Agregar a trabajo pendiente
            scenario.add_pending_work("connector", {
                "id": filename,
                "path": filepath,
                "created_at": datetime.utcnow().isoformat()
            })
        
        print(f"📁 Creados {len(pending_files)} archivos pendientes")
        
        # WHEN: Connector cae y se reinicia
        print("\n1️⃣ Simulando caída del Connector...")
        scenario.simulate_service_crash("connector")
        assert scenario.services["connector"]["status"] == "crashed"
        
        # Simular que llegan más archivos mientras está caído
        print("\n2️⃣ Archivos acumulándose durante la caída...")
        for i in range(2):
            filename = f"articulos_during_crash_{i+1}.json.gz"
            scenario.add_pending_work("connector", {
                "id": filename,
                "created_at": datetime.utcnow().isoformat()
            })
        
        print(f"   📈 Total archivos pendientes: {len(scenario.pending_work['connector'])}")
        
        # Reiniciar servicio
        print("\n3️⃣ Reiniciando Connector...")
        scenario.simulate_service_restart("connector")
        assert scenario.services["connector"]["status"] == "running"
        
        # THEN: Procesar trabajo pendiente
        print("\n4️⃣ Procesando archivos pendientes...")
        results = asyncio.run(scenario.process_pending_work("connector"))
        
        print(f"\n📊 Resultados de recuperación:")
        print(f"   - Archivos procesados: {results['processed']}")
        print(f"   - Duplicados evitados: {results['duplicates']}")
        print(f"   - Estado del servicio: {scenario.services['connector']['status']}")
        
        assert results["processed"] == 5  # 3 originales + 2 durante caída
        assert results["duplicates"] == 0
        assert len(scenario.pending_work["connector"]) == 0  # Cola vacía


def test_pipeline_recovery_with_deduplication():
    """Test: Pipeline evita procesar artículos duplicados tras reinicio"""
    
    scenario = ServiceRestartScenario()
    
    print("\n🔄 Test: Pipeline con deduplicación tras reinicio\n")
    
    # GIVEN: Artículos en proceso cuando Pipeline cae
    articles_in_flight = [
        {"id": "art-001", "url": "https://example.com/1", "status": "processing"},
        {"id": "art-002", "url": "https://example.com/2", "status": "processing"},
        {"id": "art-003", "url": "https://example.com/3", "status": "completed"}
    ]
    
    # Simular que algunos ya fueron procesados
    scenario.processed_items.add("art-003")
    
    print("📝 Estado inicial:")
    print(f"   - Artículos en proceso: {len(articles_in_flight)}")
    print(f"   - Ya procesados: {len(scenario.processed_items)}")
    
    # WHEN: Pipeline cae durante procesamiento
    print("\n1️⃣ Pipeline cae durante procesamiento...")
    scenario.simulate_service_crash("pipeline")
    
    # Agregar artículos a reprocesar
    for article in articles_in_flight:
        scenario.add_pending_work("pipeline", article)
    
    # El Connector podría reenviar algunos artículos
    print("\n2️⃣ Connector reenvía artículos (posibles duplicados)...")
    scenario.add_pending_work("pipeline", {"id": "art-001", "url": "https://example.com/1"})  # Duplicado
    scenario.add_pending_work("pipeline", {"id": "art-004", "url": "https://example.com/4"})  # Nuevo
    
    # Reiniciar Pipeline
    print("\n3️⃣ Reiniciando Pipeline...")
    scenario.simulate_service_restart("pipeline")
    
    # THEN: Procesar con deduplicación
    print("\n4️⃣ Procesando con deduplicación...")
    results = asyncio.run(scenario.process_pending_work("pipeline"))
    
    print(f"\n📊 Resultados:")
    print(f"   - Procesados nuevos: {results['processed']}")
    print(f"   - Duplicados evitados: {results['duplicates']}")
    print(f"   - Total únicos procesados: {len(scenario.processed_items)}")
    
    assert results["processed"] == 3  # art-001, art-002, art-004
    assert results["duplicates"] == 2  # art-003 ya procesado, art-001 duplicado


def test_cascading_recovery():
    """Test: Recuperación en cascada cuando múltiples servicios caen"""
    
    scenario = ServiceRestartScenario()
    
    print("\n🌊 Test: Recuperación en cascada de múltiples servicios\n")
    
    async def simulate_cascading_failure():
        """Simula fallo en cascada y recuperación"""
        
        # 1. Pipeline cae primero
        print("💥 FALLO EN CASCADA:")
        print("1️⃣ Pipeline cae...")
        scenario.simulate_service_crash("pipeline")
        await asyncio.sleep(0.2)
        
        # 2. Connector detecta y también falla
        print("2️⃣ Connector detecta Pipeline caído y falla...")
        scenario.simulate_service_crash("connector")
        await asyncio.sleep(0.2)
        
        # 3. Dashboard pierde conexión
        print("3️⃣ Dashboard pierde conexión con backend...")
        scenario.simulate_service_crash("dashboard")
        
        # Estado del sistema
        crashed_services = [s for s, info in scenario.services.items() 
                          if info["status"] == "crashed"]
        print(f"\n⚠️ Servicios caídos: {', '.join(crashed_services)}")
        
        # RECUPERACIÓN EN ORDEN
        print("\n🔧 RECUPERACIÓN EN ORDEN:")
        
        # 1. Primero Pipeline (dependencia base)
        print("\n1️⃣ Recuperando Pipeline...")
        scenario.simulate_service_restart("pipeline")
        await asyncio.sleep(0.3)
        
        # 2. Luego Connector
        print("\n2️⃣ Recuperando Connector...")
        scenario.simulate_service_restart("connector")
        
        # Verificar que Connector espera a Pipeline
        print("   🔍 Connector verifica Pipeline...")
        if scenario.services["pipeline"]["status"] == "running":
            print("   ✅ Pipeline disponible - Connector puede proceder")
        
        await asyncio.sleep(0.3)
        
        # 3. Finalmente Dashboard
        print("\n3️⃣ Recuperando Dashboard...")
        scenario.simulate_service_restart("dashboard")
        
        return crashed_services
    
    crashed = asyncio.run(simulate_cascading_failure())
    
    # Verificar recuperación completa
    all_running = all(info["status"] == "running" 
                     for info in scenario.services.values())
    
    print(f"\n📊 Estado final del sistema:")
    for service, info in scenario.services.items():
        status_icon = "✅" if info["status"] == "running" else "❌"
        print(f"   {status_icon} {service}: {info['status']} (reinicios: {info['restart_count']})")
    
    assert all_running, "Todos los servicios deberían estar ejecutándose"
    assert len(crashed) == 3, "Tres servicios deberían haber caído"


def test_health_check_monitoring():
    """Test: Sistema de health checks para detección temprana"""
    
    print("\n🏥 Test: Monitoreo con health checks\n")
    
    class HealthMonitor:
        def __init__(self):
            self.health_checks = {}
            self.failure_threshold = 3
            self.check_interval = 1  # segundos
            
        async def check_service_health(self, service: str) -> dict:
            """Realiza health check de un servicio"""
            # Simular diferentes tipos de checks
            checks = {
                "ping": await self.ping_check(service),
                "memory": await self.memory_check(service),
                "response_time": await self.response_time_check(service)
            }
            
            # Calcular salud general
            healthy_checks = sum(1 for check in checks.values() if check["healthy"])
            overall_health = healthy_checks / len(checks)
            
            return {
                "service": service,
                "timestamp": datetime.utcnow().isoformat(),
                "overall_health": overall_health,
                "checks": checks,
                "status": "healthy" if overall_health > 0.6 else "unhealthy"
            }
        
        async def ping_check(self, service: str) -> dict:
            """Check de conectividad básica"""
            # Simular respuesta
            success = service != "pipeline" or time.time() % 3 != 0
            return {
                "healthy": success,
                "response_time_ms": 50 if success else None
            }
        
        async def memory_check(self, service: str) -> dict:
            """Check de uso de memoria"""
            # Simular uso de memoria
            memory_usage = 45 + (hash(service) % 40)
            return {
                "healthy": memory_usage < 80,
                "usage_percent": memory_usage
            }
        
        async def response_time_check(self, service: str) -> dict:
            """Check de tiempo de respuesta"""
            # Simular tiempo de respuesta variable
            base_time = 100
            if service == "pipeline":
                response_time = base_time + (time.time() % 200)
            else:
                response_time = base_time + (hash(service) % 50)
            
            return {
                "healthy": response_time < 250,
                "response_time_ms": response_time
            }
        
        async def monitor_services(self, services: list, duration: int = 5):
            """Monitorea servicios por un período"""
            monitoring_results = []
            
            for i in range(duration):
                print(f"\n🔍 Health check round {i+1}/{duration}")
                
                for service in services:
                    health = await self.check_service_health(service)
                    monitoring_results.append(health)
                    
                    status_icon = "✅" if health["status"] == "healthy" else "⚠️"
                    print(f"   {status_icon} {service}: {health['overall_health']:.0%} healthy")
                    
                    if health["status"] == "unhealthy":
                        failing_checks = [name for name, check in health["checks"].items() 
                                        if not check["healthy"]]
                        print(f"      ❌ Failing: {', '.join(failing_checks)}")
                
                await asyncio.sleep(self.check_interval)
            
            return monitoring_results
    
    monitor = HealthMonitor()
    services = ["connector", "pipeline", "dashboard"]
    
    # Ejecutar monitoreo
    results = asyncio.run(monitor.monitor_services(services, duration=3))
    
    # Analizar resultados
    unhealthy_count = sum(1 for r in results if r["status"] == "unhealthy")
    services_with_issues = set(r["service"] for r in results if r["status"] == "unhealthy")
    
    print(f"\n📊 Resumen de monitoreo:")
    print(f"   - Total health checks: {len(results)}")
    print(f"   - Checks no saludables: {unhealthy_count}")
    print(f"   - Servicios con problemas: {', '.join(services_with_issues) if services_with_issues else 'Ninguno'}")
    
    # Verificar que el monitoreo funciona
    assert len(results) == 9  # 3 servicios x 3 rounds
    assert any(r["overall_health"] < 1.0 for r in results)  # Al menos algún problema detectado


def test_state_synchronization_after_restart():
    """Test: Sincronización de estado después de reinicio"""
    
    print("\n🔄 Test: Sincronización de estado post-reinicio\n")
    
    class StateSynchronizer:
        def __init__(self):
            self.global_state = {
                "last_processed_article": "art-100",
                "processing_queue": ["art-101", "art-102", "art-103"],
                "completed_today": 245,
                "last_sync": datetime.utcnow()
            }
            self.service_states = {}
            
        def save_service_state(self, service: str, state: dict):
            """Guarda estado de un servicio antes de caída"""
            self.service_states[service] = {
                "state": state,
                "saved_at": datetime.utcnow()
            }
            print(f"💾 Estado guardado para {service}")
            
        def restore_service_state(self, service: str) -> dict:
            """Restaura estado de un servicio después de reinicio"""
            if service in self.service_states:
                saved = self.service_states[service]
                age = (datetime.utcnow() - saved["saved_at"]).total_seconds()
                
                if age < 300:  # Estado válido por 5 minutos
                    print(f"♻️ Estado restaurado para {service} (edad: {age:.0f}s)")
                    return saved["state"]
                else:
                    print(f"⚠️ Estado expirado para {service} (edad: {age:.0f}s)")
            
            return None
            
        async def sync_with_global_state(self, service: str, local_state: dict) -> dict:
            """Sincroniza estado local con estado global"""
            print(f"\n🔄 Sincronizando {service} con estado global...")
            
            # Detectar diferencias
            differences = []
            
            if "last_processed" in local_state:
                local_last = local_state["last_processed"]
                global_last = self.global_state["last_processed_article"]
                
                if local_last != global_last:
                    differences.append(f"last_processed: {local_last} → {global_last}")
                    local_state["last_processed"] = global_last
            
            if "queue" in local_state:
                local_queue = set(local_state["queue"])
                global_queue = set(self.global_state["processing_queue"])
                
                missing = global_queue - local_queue
                extra = local_queue - global_queue
                
                if missing:
                    differences.append(f"queue: +{len(missing)} items")
                    local_state["queue"].extend(missing)
                
                if extra:
                    differences.append(f"queue: -{len(extra)} items")
                    local_state["queue"] = [q for q in local_state["queue"] if q in global_queue]
            
            if differences:
                print(f"   📝 Diferencias encontradas: {', '.join(differences)}")
            else:
                print(f"   ✅ Estado ya sincronizado")
            
            return local_state
    
    sync = StateSynchronizer()
    
    # Simular estado del Connector antes de caer
    connector_state = {
        "last_processed": "art-098",  # Desactualizado
        "queue": ["art-101", "art-102"],  # Falta art-103
        "files_processed": 50
    }
    
    # 1. Guardar estado antes de caída
    print("1️⃣ Connector a punto de caer - guardando estado...")
    sync.save_service_state("connector", connector_state)
    
    # 2. Simular caída y reinicio
    print("\n2️⃣ Connector reiniciando...")
    time.sleep(1)  # Simular tiempo de reinicio
    
    # 3. Restaurar estado
    restored_state = sync.restore_service_state("connector")
    assert restored_state is not None
    print(f"   📂 Estado local restaurado: {restored_state}")
    
    # 4. Sincronizar con estado global
    synced_state = asyncio.run(sync.sync_with_global_state("connector", restored_state))
    
    print(f"\n📊 Estado final sincronizado:")
    print(f"   - last_processed: {synced_state['last_processed']}")
    print(f"   - queue: {synced_state['queue']}")
    print(f"   - files_processed: {synced_state['files_processed']}")
    
    # Verificaciones
    assert synced_state["last_processed"] == "art-100"
    assert len(synced_state["queue"]) == 3
    assert "art-103" in synced_state["queue"]


def test_graceful_shutdown_and_startup():
    """Test: Apagado y arranque elegante de servicios"""
    
    print("\n🎯 Test: Apagado y arranque elegante\n")
    
    class GracefulService:
        def __init__(self, name: str):
            self.name = name
            self.active_connections = []
            self.pending_tasks = []
            self.shutdown_timeout = 30  # segundos
            
        async def shutdown_gracefully(self) -> dict:
            """Apagado elegante del servicio"""
            print(f"\n🛑 Iniciando apagado elegante de {self.name}...")
            
            shutdown_steps = []
            
            # 1. Dejar de aceptar nuevas conexiones
            print("   1️⃣ Dejando de aceptar nuevas conexiones")
            shutdown_steps.append("stopped_accepting")
            
            # 2. Completar tareas en progreso
            if self.pending_tasks:
                print(f"   2️⃣ Completando {len(self.pending_tasks)} tareas pendientes...")
                completed = 0
                for task in self.pending_tasks[:]:  # Copiar lista
                    # Simular completar tarea
                    await asyncio.sleep(0.1)
                    self.pending_tasks.remove(task)
                    completed += 1
                    
                print(f"      ✅ {completed} tareas completadas")
                shutdown_steps.append("tasks_completed")
            
            # 3. Cerrar conexiones activas
            if self.active_connections:
                print(f"   3️⃣ Cerrando {len(self.active_connections)} conexiones activas...")
                for conn in self.active_connections[:]:
                    self.active_connections.remove(conn)
                shutdown_steps.append("connections_closed")
            
            # 4. Guardar estado
            print("   4️⃣ Guardando estado final...")
            final_state = {
                "shutdown_time": datetime.utcnow().isoformat(),
                "pending_tasks_saved": len(self.pending_tasks),
                "graceful": True
            }
            shutdown_steps.append("state_saved")
            
            print(f"   ✅ {self.name} apagado elegantemente")
            
            return {
                "steps_completed": shutdown_steps,
                "final_state": final_state
            }
        
        async def startup_with_recovery(self, previous_state: dict = None) -> dict:
            """Arranque con recuperación de estado previo"""
            print(f"\n🚀 Iniciando {self.name}...")
            
            startup_steps = []
            
            # 1. Cargar configuración
            print("   1️⃣ Cargando configuración...")
            startup_steps.append("config_loaded")
            
            # 2. Restaurar estado si existe
            if previous_state and previous_state.get("graceful"):
                print("   2️⃣ Detectado apagado elegante previo - restaurando estado...")
                if previous_state.get("pending_tasks_saved", 0) > 0:
                    print(f"      📋 Recuperando {previous_state['pending_tasks_saved']} tareas pendientes")
                startup_steps.append("state_restored")
            else:
                print("   2️⃣ Sin estado previo o apagado no fue elegante - inicio limpio")
                startup_steps.append("clean_start")
            
            # 3. Inicializar conexiones
            print("   3️⃣ Inicializando pool de conexiones...")
            await asyncio.sleep(0.2)  # Simular inicialización
            startup_steps.append("connections_initialized")
            
            # 4. Comenzar a aceptar requests
            print("   4️⃣ Listo para aceptar requests")
            startup_steps.append("accepting_requests")
            
            print(f"   ✅ {self.name} iniciado correctamente")
            
            return {
                "steps_completed": startup_steps,
                "ready": True
            }
    
    # Simular ciclo completo
    service = GracefulService("TestService")
    
    # Agregar trabajo activo
    service.pending_tasks = ["task1", "task2", "task3"]
    service.active_connections = ["conn1", "conn2"]
    
    # Apagado elegante
    shutdown_result = asyncio.run(service.shutdown_gracefully())
    
    # Verificar apagado completo
    assert len(shutdown_result["steps_completed"]) == 4
    assert shutdown_result["final_state"]["graceful"] is True
    
    # Simular reinicio
    print("\n" + "="*50)
    
    # Arranque con recuperación
    startup_result = asyncio.run(
        service.startup_with_recovery(shutdown_result["final_state"])
    )
    
    # Verificar arranque exitoso
    assert startup_result["ready"] is True
    assert "state_restored" in startup_result["steps_completed"]
    
    print("\n✅ Ciclo completo de apagado/arranque elegante completado")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
