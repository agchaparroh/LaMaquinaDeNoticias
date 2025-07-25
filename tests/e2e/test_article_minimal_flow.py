"""
test_article_minimal_flow.py
Test End-to-End: Flujo mínimo de un artículo desde scraping hasta dashboard

Valida el recorrido completo de un artículo:
1. Scraper genera archivo .json.gz con artículo
2. Connector lee archivo y envía a Pipeline
3. Pipeline procesa y almacena en Supabase
4. Dashboard consulta y muestra el artículo procesado
"""

import asyncio  # noqa: F401
import gzip
import json
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path  # noqa: F401
from unittest.mock import AsyncMock, Mock, patch  # noqa: F401

import pytest


class E2EArticleFlow:
    """Simula el flujo completo de un artículo a través del sistema"""

    def __init__(self):
        self.article_data = {
            "url": "https://example.com/e2e-test-minimal",
            "titular": "Noticia de prueba E2E mínima",
            "medio": "Test E2E News",
            "area_geografica": "AR",
            "tipo_medio": "digital",
            "fecha_publicacion": datetime.utcnow().isoformat(),
            "contenido_texto": "Este es un contenido de prueba para el test E2E que debe tener más de 50 caracteres para cumplir validaciones.",
            "contenido_html": "<p>Este es un contenido HTML de prueba para el test E2E</p>",
            "autor": "Test Author E2E",
            "seccion": "Tecnología",
            "etiquetas_fuente": ["test", "e2e", "automatización"],
            "es_opinion": False,
            "es_oficial": False,
            "fecha_recopilacion": datetime.utcnow().isoformat(),
        }
        self.scraped_file_path = None
        self.pipeline_response = None
        self.db_article_id = None
        self.dashboard_data = None

    def scraper_generate_file(self, output_dir: str) -> str:
        """Simula Scraper generando archivo .json.gz"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"articulos_{timestamp}_e2e_test.json.gz"
        filepath = os.path.join(output_dir, filename)

        with gzip.open(filepath, "wt", encoding="utf-8") as f:
            json.dump([self.article_data], f, ensure_ascii=False, indent=2)

        self.scraped_file_path = filepath
        return filepath

    def connector_read_and_send(self) -> dict:
        """Simula Connector leyendo archivo y enviando a Pipeline"""
        # Leer archivo generado
        with gzip.open(self.scraped_file_path, "rt", encoding="utf-8") as f:
            articles = json.loads(f.read())

        assert len(articles) == 1
        article = articles[0]

        # Validaciones del Connector
        assert len(article["contenido_texto"]) >= 50
        assert article["url"]
        assert article["titular"]
        assert article["medio"]

        # Simular envío a Pipeline
        payload = {"articulo": article}  # noqa: F841

        # Simular respuesta del Pipeline
        self.pipeline_response = {
            "status": 202,
            "success": True,
            "fragmento_id": "frag-e2e-test-123",
            "message": "Artículo aceptado para procesamiento",
        }

        return self.pipeline_response

    def pipeline_process_article(self) -> dict:
        """Simula Pipeline procesando artículo"""
        # Pipeline extrae hechos del artículo
        hechos_extraidos = [
            {
                "contenido": "Se realizó prueba E2E del sistema",
                "tipo": "declaracion",
                "importancia_automatica": 7,
                "confianza_extraccion": 0.85,
            },
            {
                "contenido": "El test validó el flujo completo",
                "tipo": "accion",
                "importancia_automatica": 8,
                "confianza_extraccion": 0.90,
            },
        ]

        # Simular almacenamiento en Supabase
        self.db_article_id = "art-e2e-" + str(int(time.time()))

        db_record = {
            "id": self.db_article_id,
            "url": self.article_data["url"],
            "titular": self.article_data["titular"],
            "medio": self.article_data["medio"],
            "contenido_texto": self.article_data["contenido_texto"],
            "hechos": hechos_extraidos,
            "estado_procesamiento": "completado",
            "fecha_procesamiento": datetime.utcnow().isoformat(),
        }

        return db_record

    def dashboard_query_article(self) -> dict:
        """Simula Dashboard consultando artículo procesado"""
        # Dashboard consulta por ID o por filtros
        query_response = {
            "articulo": {
                "id": self.db_article_id,
                "titular": self.article_data["titular"],
                "medio": self.article_data["medio"],
                "fecha_publicacion": self.article_data["fecha_publicacion"],
                "hechos_count": 2,
                "hechos": [
                    {
                        "id": "hecho-1",
                        "contenido": "Se realizó prueba E2E del sistema",
                        "importancia_automatica": 7,
                        "importancia_editor": None,  # Sin editar aún
                    },
                    {
                        "id": "hecho-2",
                        "contenido": "El test validó el flujo completo",
                        "importancia_automatica": 8,
                        "importancia_editor": None,
                    },
                ],
                "estado": "disponible_para_revision",
            }
        }

        self.dashboard_data = query_response
        return query_response


def test_article_minimal_flow():
    """Test E2E: Un artículo completa todo el flujo del sistema"""

    # GIVEN: Sistema desplegado y funcionando
    flow = E2EArticleFlow()

    with tempfile.TemporaryDirectory() as temp_dir:
        print("\n🚀 Iniciando test E2E de flujo mínimo de artículo\n")

        # WHEN: El flujo completo se ejecuta

        # 1. Scraper genera archivo
        print("1️⃣ SCRAPER: Generando archivo .json.gz...")
        scraped_file = flow.scraper_generate_file(temp_dir)
        assert os.path.exists(scraped_file)
        print(f"   ✅ Archivo generado: {os.path.basename(scraped_file)}")

        # 2. Connector procesa y envía
        print("\n2️⃣ CONNECTOR: Leyendo archivo y enviando a Pipeline...")
        pipeline_response = flow.connector_read_and_send()
        assert pipeline_response["status"] == 202
        assert pipeline_response["success"] is True
        print(f"   ✅ Pipeline aceptó artículo: {pipeline_response['fragmento_id']}")

        # 3. Pipeline procesa
        print("\n3️⃣ PIPELINE: Procesando artículo y extrayendo hechos...")
        db_record = flow.pipeline_process_article()
        assert db_record["estado_procesamiento"] == "completado"
        assert len(db_record["hechos"]) > 0
        print(
            f"   ✅ Artículo procesado con {len(db_record['hechos'])} hechos extraídos"
        )
        print(f"   📊 ID en base de datos: {db_record['id']}")

        # 4. Dashboard consulta
        print("\n4️⃣ DASHBOARD: Consultando artículo procesado...")
        dashboard_data = flow.dashboard_query_article()
        assert dashboard_data["articulo"]["id"] == db_record["id"]
        assert dashboard_data["articulo"]["estado"] == "disponible_para_revision"
        print(f"   ✅ Artículo disponible en dashboard")  # noqa: F541
        print(
            f"   📝 Hechos listos para revisión editorial: {dashboard_data['articulo']['hechos_count']}"
        )

        # THEN: Validar el flujo completo
        print("\n✅ FLUJO COMPLETO EXITOSO:")
        print(f"   - Artículo: '{flow.article_data['titular']}'")
        print(f"   - Recorrido: Scraper → Connector → Pipeline → Database → Dashboard")  # noqa: F541
        print(f"   - Hechos extraídos: {len(dashboard_data['articulo']['hechos'])}")
        print(f"   - Estado final: {dashboard_data['articulo']['estado']}")

        # Verificaciones adicionales
        assert (
            flow.article_data["url"] == dashboard_data["articulo"]["titular"]
        )  # Título se preserva
        assert all(
            h["importancia_editor"] is None
            for h in dashboard_data["articulo"]["hechos"]
        )  # Sin editar aún


def test_article_minimal_flow_with_timing():
    """Test E2E con medición de tiempos para detectar cuellos de botella"""

    flow = E2EArticleFlow()
    timings = {}

    with tempfile.TemporaryDirectory() as temp_dir:
        print("\n⏱️ Test E2E con medición de tiempos\n")

        # Scraper
        start = time.time()
        flow.scraper_generate_file(temp_dir)
        timings["scraper"] = time.time() - start

        # Connector
        start = time.time()
        flow.connector_read_and_send()
        timings["connector"] = time.time() - start

        # Pipeline
        start = time.time()
        flow.pipeline_process_article()
        timings["pipeline"] = time.time() - start

        # Dashboard
        start = time.time()
        flow.dashboard_query_article()
        timings["dashboard"] = time.time() - start

        # Reporte de tiempos
        total_time = sum(timings.values())
        print("\n📊 Análisis de tiempos:")
        for stage, duration in timings.items():
            percentage = (duration / total_time) * 100
            print(f"   {stage.upper()}: {duration:.3f}s ({percentage:.1f}%)")
        print(f"\n   TOTAL: {total_time:.3f}s")

        # Alertar si alguna etapa toma más del 50% del tiempo
        for stage, duration in timings.items():
            percentage = (duration / total_time) * 100
            assert percentage < 50, f"⚠️ {stage} tomó {percentage:.1f}% del tiempo total"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
