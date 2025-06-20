# locustfile.py
"""
Configuración de Locust para tests de carga avanzados de nginx_reverse_proxy.
Uso: locust -f locustfile.py --host=http://localhost
"""

from locust import HttpUser, task, between
import random
import json


class DashboardUser(HttpUser):
    """
    Simula un usuario típico del Dashboard de La Máquina de Noticias.
    """
    wait_time = between(1, 3)  # Espera entre 1-3 segundos entre requests
    
    def on_start(self):
        """Inicialización del usuario."""
        self.user_id = random.randint(1000, 9999)
        self.session_data = {
            "user_id": self.user_id,
            "login_time": self.environment.runner.start_time
        }
    
    @task(3)
    def view_dashboard(self):
        """Visita la página principal del dashboard."""
        self.client.get("/")
    
    @task(2)
    def check_health(self):
        """Verifica el health check."""
        self.client.get("/nginx-health", name="health_check")
    
    @task(5)
    def api_get_news(self):
        """Obtiene lista de noticias via API."""
        params = {
            "limit": random.randint(10, 50),
            "offset": random.randint(0, 100)
        }
        
        with self.client.get(
            "/api/v1/news",
            params=params,
            catch_response=True,
            name="api_news"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list) or "items" in data:
                        response.success()
                    else:
                        response.failure("Respuesta no tiene formato esperado")
                except:
                    response.failure("Respuesta no es JSON válido")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(2)
    def api_search(self):
        """Realiza una búsqueda."""
        search_terms = ["política", "economía", "tecnología", "deportes", "cultura"]
        
        params = {
            "q": random.choice(search_terms),
            "type": "news",
            "limit": 20
        }
        
        self.client.get("/api/v1/search", params=params, name="api_search")
    
    @task(1)
    def api_post_action(self):
        """Envía una acción via POST."""
        data = {
            "action": "view",
            "resource_type": "news",
            "resource_id": random.randint(1, 1000),
            "user_id": self.user_id,
            "timestamp": int(self.environment.runner.start_time)
        }
        
        self.client.post(
            "/api/v1/actions",
            json=data,
            name="api_post_action"
        )
    
    @task(2)
    def navigate_spa(self):
        """Navega por rutas SPA."""
        spa_routes = [
            "/dashboard",
            "/reports",
            "/analytics",
            "/settings",
            "/news/latest",
            "/news/trending"
        ]
        
        route = random.choice(spa_routes)
        self.client.get(route, name="spa_navigation")
    
    @task(1)
    def load_static_resource(self):
        """Carga recursos estáticos."""
        static_resources = [
            "/static/css/main.css",
            "/static/js/main.js",
            "/static/js/vendor.js",
            "/favicon.ico",
            "/manifest.json"
        ]
        
        resource = random.choice(static_resources)
        self.client.get(resource, name="static_resource")


class APIUser(HttpUser):
    """
    Simula un cliente API que hace requests más intensivos.
    """
    wait_time = between(0.5, 1.5)  # Requests más frecuentes
    
    @task(10)
    def api_batch_request(self):
        """Hace requests batch al API."""
        endpoints = [
            "/api/v1/news",
            "/api/v1/analytics",
            "/api/v1/status"
        ]
        
        for endpoint in random.sample(endpoints, 2):
            self.client.get(endpoint, name=f"api_batch_{endpoint.split('/')[-1]}")
    
    @task(3)
    def api_heavy_query(self):
        """Hace queries pesadas al API."""
        params = {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "aggregation": "daily",
            "metrics": "views,shares,comments",
            "group_by": "category,source"
        }
        
        with self.client.get(
            "/api/v1/analytics/aggregate",
            params=params,
            timeout=30,
            catch_response=True,
            name="api_heavy_query"
        ) as response:
            if response.elapsed.total_seconds() > 5:
                response.failure(f"Query muy lenta: {response.elapsed.total_seconds()}s")
            elif response.status_code != 200:
                response.failure(f"Status: {response.status_code}")
            else:
                response.success()
    
    @task(2)
    def api_concurrent_posts(self):
        """Envía múltiples POSTs concurrentes."""
        for i in range(3):
            data = {
                "batch_id": f"{self.environment.runner.start_time}_{i}",
                "data": [{"id": j, "value": random.random()} for j in range(10)]
            }
            
            self.client.post(
                "/api/v1/batch",
                json=data,
                name="api_batch_post"
            )


class MobileUser(HttpUser):
    """
    Simula un usuario móvil con patrones de uso diferentes.
    """
    wait_time = between(2, 5)  # Interacciones más espaciadas
    
    def on_start(self):
        """Configura headers de dispositivo móvil."""
        self.client.headers.update({
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) Mobile/15E148"
        })
    
    @task(5)
    def mobile_dashboard(self):
        """Accede al dashboard móvil."""
        self.client.get("/", name="mobile_home")
    
    @task(3)
    def mobile_api_lite(self):
        """Hace requests API optimizados para móvil."""
        params = {
            "limit": 10,  # Menos items
            "fields": "id,title,summary",  # Menos campos
            "mobile": "true"
        }
        
        self.client.get("/api/v1/news", params=params, name="mobile_api")
    
    @task(1)
    def mobile_offline_check(self):
        """Verifica recursos para modo offline."""
        self.client.get("/service-worker.js", name="mobile_sw")
        self.client.get("/offline.html", name="mobile_offline")
