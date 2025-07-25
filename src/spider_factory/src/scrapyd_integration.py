"""
Integración con Scrapyd para programación automática de spiders
"""

import json
from datetime import datetime
from typing import Dict, List, Optional  # noqa: F401

import httpx

from src.config import settings  # noqa: F401
from src.logging_config import logger


class ScrapydIntegration:
    """Maneja la integración con Scrapyd para ejecución automática de spiders"""

    def __init__(self, scrapyd_url: str = "http://scrapyd:6800"):
        self.scrapyd_url = scrapyd_url
        self.project_name = "lamaquina"

    async def register_spider_in_scrapyd(
        self,
        spider_name: str,
        frecuencia_minutos: int,
        medio: str,
        seccion: str,
        area_geografica: str,
        tipo_medio: str,
    ) -> Dict[str, any]:
        """
        Registra un spider en Scrapyd para ejecución automática

        Args:
            spider_name: Nombre del spider (formato: medio_seccion)
            frecuencia_minutos: Frecuencia de ejecución en minutos
            medio: Nombre del medio
            seccion: Sección del medio
            area_geografica: Área geográfica
            tipo_medio: Tipo de medio (diario|revista|agencia)

        Returns:
            Dict con el resultado del registro
        """
        try:
            # Verificar que el spider existe
            spider_exists = await self.check_spider_exists(spider_name)
            if not spider_exists:
                return {
                    "success": False,
                    "error": f"Spider {spider_name} no existe en el proyecto",
                }

            # Programar spider en Scrapyd
            schedule_data = {
                "project": self.project_name,
                "spider": spider_name,
                "settings": {
                    "SPIDER_MEDIO": medio,
                    "SPIDER_SECCION": seccion,
                    "SPIDER_AREA_GEOGRAFICA": area_geografica,
                    "SPIDER_TIPO_MEDIO": tipo_medio,
                    "SPIDER_FRECUENCIA": frecuencia_minutos,
                    "LOG_LEVEL": "INFO",
                    "CLOSESPIDER_TIMEOUT": 1800,  # 30 minutos máximo
                    "DOWNLOAD_TIMEOUT": 30,
                    "CONCURRENT_REQUESTS": 16,
                    "AUTOTHROTTLE_ENABLED": True,
                    "AUTOTHROTTLE_TARGET_CONCURRENCY": 2.0,
                },
            }

            # Agregar el spider a la cola de Scrapyd
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.scrapyd_url}/schedule.json", data=schedule_data
                )

                if response.status_code == 200:
                    result = response.json()

                    if result.get("status") == "ok":
                        job_id = result.get("jobid")
                        logger.info(
                            f"Spider {spider_name} programado en Scrapyd con job_id: {job_id}"
                        )

                        # Guardar información de programación
                        await self._save_schedule_info(
                            spider_name, job_id, frecuencia_minutos
                        )

                        return {
                            "success": True,
                            "job_id": job_id,
                            "spider_name": spider_name,
                            "frecuencia_minutos": frecuencia_minutos,
                            "next_run": self._calculate_next_run(frecuencia_minutos),
                        }
                    else:
                        error_msg = result.get("message", "Error desconocido")
                        logger.error(f"Error programando spider: {error_msg}")
                        return {"success": False, "error": error_msg}
                else:
                    logger.error(
                        f"Error HTTP {response.status_code} al contactar Scrapyd"
                    )
                    return {
                        "success": False,
                        "error": f"Error HTTP {response.status_code}",
                    }

        except Exception as e:
            logger.error(f"Error registrando spider en Scrapyd: {e}")
            return {"success": False, "error": str(e)}

    async def check_spider_exists(self, spider_name: str) -> bool:
        """
        Verifica si un spider existe en el proyecto Scrapyd

        Args:
            spider_name: Nombre del spider

        Returns:
            True si existe, False si no
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.scrapyd_url}/listspiders.json",
                    params={"project": self.project_name},
                )

                if response.status_code == 200:
                    data = response.json()
                    spiders = data.get("spiders", [])
                    return spider_name in spiders

        except Exception as e:
            logger.error(f"Error verificando spider: {e}")

        return False

    async def list_scheduled_jobs(self) -> List[Dict]:
        """
        Lista todos los trabajos programados en Scrapyd

        Returns:
            Lista de trabajos programados
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.scrapyd_url}/listjobs.json",
                    params={"project": self.project_name},
                )

                if response.status_code == 200:
                    data = response.json()

                    jobs = []
                    # Combinar trabajos pendientes y en ejecución
                    jobs.extend(data.get("pending", []))
                    jobs.extend(data.get("running", []))

                    return jobs

        except Exception as e:
            logger.error(f"Error listando trabajos: {e}")

        return []

    async def cancel_spider_job(self, job_id: str) -> bool:
        """
        Cancela un trabajo de spider en Scrapyd

        Args:
            job_id: ID del trabajo a cancelar

        Returns:
            True si se canceló exitosamente
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.scrapyd_url}/cancel.json",
                    data={"project": self.project_name, "job": job_id},
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("status") == "ok"

        except Exception as e:
            logger.error(f"Error cancelando trabajo: {e}")

        return False

    async def get_spider_stats(self, spider_name: str) -> Dict:
        """
        Obtiene estadísticas de ejecución de un spider

        Args:
            spider_name: Nombre del spider

        Returns:
            Dict con estadísticas del spider
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.scrapyd_url}/listjobs.json",
                    params={"project": self.project_name},
                )

                if response.status_code == 200:
                    data = response.json()

                    # Buscar trabajos del spider
                    finished_jobs = [
                        job
                        for job in data.get("finished", [])
                        if job.get("spider") == spider_name
                    ]

                    # Calcular estadísticas
                    total_runs = len(finished_jobs)
                    successful_runs = sum(
                        1
                        for job in finished_jobs
                        if job.get("end_reason") == "finished"
                    )

                    # Tiempos de ejecución
                    execution_times = []
                    for job in finished_jobs[-10:]:  # Últimas 10 ejecuciones
                        if job.get("start_time") and job.get("end_time"):
                            start = datetime.fromisoformat(job["start_time"])
                            end = datetime.fromisoformat(job["end_time"])
                            duration = (end - start).total_seconds()
                            execution_times.append(duration)

                    avg_execution_time = (
                        sum(execution_times) / len(execution_times)
                        if execution_times
                        else 0
                    )

                    return {
                        "spider_name": spider_name,
                        "total_runs": total_runs,
                        "successful_runs": successful_runs,
                        "success_rate": successful_runs / total_runs
                        if total_runs > 0
                        else 0,
                        "average_execution_time": avg_execution_time,
                        "last_run": finished_jobs[0] if finished_jobs else None,
                    }

        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")

        return {}

    async def _save_schedule_info(
        self, spider_name: str, job_id: str, frecuencia_minutos: int
    ):
        """Guarda información de programación en Redis"""
        try:
            from src.redis_pool import get_redis_client

            redis = await get_redis_client()

            schedule_info = {
                "spider_name": spider_name,
                "job_id": job_id,
                "frecuencia_minutos": frecuencia_minutos,
                "registered_at": datetime.now().isoformat(),
                "next_run": self._calculate_next_run(frecuencia_minutos),
            }

            await redis.hset(
                f"spider_schedules",  # noqa: F541
                spider_name,
                json.dumps(schedule_info),
            )

        except Exception as e:
            logger.error(f"Error guardando información de programación: {e}")

    def _calculate_next_run(self, frecuencia_minutos: int) -> str:
        """Calcula la próxima ejecución basada en la frecuencia"""
        from datetime import timedelta

        next_run = datetime.now() + timedelta(minutes=frecuencia_minutos)
        return next_run.isoformat()


# Función helper para uso directo
async def register_spider_in_scrapyd(
    spider_name: str,
    frecuencia_minutos: int,
    medio: str = None,
    seccion: str = None,
    area_geografica: str = "GLOBAL",
    tipo_medio: str = "diario",
) -> Dict:
    """
    Registra un spider en Scrapyd para ejecución automática

    Ejemplo:
        result = await register_spider_in_scrapyd(
            spider_name="el_pais_internacional",
            frecuencia_minutos=60,
            medio="El País",
            seccion="Internacional",
            area_geografica="ESPAÑA",
            tipo_medio="diario"
        )
    """
    # Extraer medio y sección del nombre si no se proporcionan
    if not medio or not seccion:
        parts = spider_name.split("_")
        if len(parts) >= 2:
            medio = medio or parts[0].replace("_", " ").title()
            seccion = seccion or "_".join(parts[1:]).replace("_", " ").title()
        else:
            raise ValueError(
                "No se puede determinar medio y sección del nombre del spider"
            )

    integration = ScrapydIntegration()
    return await integration.register_spider_in_scrapyd(
        spider_name=spider_name,
        frecuencia_minutos=frecuencia_minutos,
        medio=medio,
        seccion=seccion,
        area_geografica=area_geografica,
        tipo_medio=tipo_medio,
    )
