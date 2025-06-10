"""
Servicio de Tracking de Jobs para Module Pipeline
=================================================

Este módulo implementa un servicio singleton para el seguimiento del estado
de trabajos de procesamiento. Almacena información de jobs en memoria con
thread-safety garantizado.

Características:
- Patrón Singleton para instancia única
- Almacenamiento in-memory con diccionario
- Thread-safety con threading.Lock
- Estados: pending, processing, completed, failed
- Limpieza automática de jobs antiguos
"""

import threading
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from uuid import uuid4
import time

# Importar utilidades de logging
from ..utils.logging_config import get_logger


class JobStatus:
    """Enumeración de estados posibles para un job."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobInfo:
    """
    Clase para almacenar información de un job.
    
    Attributes:
        job_id: Identificador único del job
        status: Estado actual del job
        created_at: Timestamp de creación
        updated_at: Timestamp de última actualización
        result: Resultado del procesamiento (opcional)
        error: Información de error si falló (opcional)
        metadata: Información adicional del job
    """
    
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.status = JobStatus.PENDING
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[Dict[str, Any]] = None
        self.metadata: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la información del job a diccionario."""
        return {
            "job_id": self.job_id,
            "status": self.status,
            "created_at": self.created_at.isoformat() + "Z",
            "updated_at": self.updated_at.isoformat() + "Z",
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata
        }


class JobTrackerService:
    """
    Servicio singleton para tracking de jobs de procesamiento.
    
    Gestiona el estado de trabajos de procesamiento con almacenamiento
    in-memory y garantías de thread-safety.
    
    Attributes:
        _instance: Instancia única del servicio
        _lock: Lock para thread-safety
        _jobs: Diccionario de jobs almacenados
        _initialized: Flag de inicialización
    """
    
    _instance: Optional['JobTrackerService'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'JobTrackerService':
        """
        Implementación del patrón Singleton.
        
        Returns:
            Instancia única de JobTrackerService
        """
        if cls._instance is None:
            with cls._lock:
                # Double-check locking pattern
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        Inicializa el servicio de tracking.
        
        Solo se ejecuta una vez gracias al patrón Singleton.
        """
        # Evitar re-inicialización
        if not hasattr(self, '_initialized'):
            # Logger con contexto
            self.logger = get_logger("JobTrackerService")
            
            # Almacenamiento de jobs
            self._jobs: Dict[str, JobInfo] = {}
            
            # Lock para operaciones thread-safe
            self._operation_lock = threading.Lock()
            
            # Configuración
            self._retention_minutes = 60  # Default: 1 hora
            self._max_jobs = 10000  # Límite de jobs en memoria
            
            # Flag de inicialización
            self._initialized = True
            
            self.logger.info(
                "JobTrackerService inicializado",
                retention_minutes=self._retention_minutes,
                max_jobs=self._max_jobs
            )
    
    def create_job(self, job_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Crea un nuevo job con estado inicial 'pending'.
        
        Args:
            job_id: ID del job (se genera uno si no se proporciona)
            metadata: Metadatos adicionales del job
            
        Returns:
            ID del job creado
            
        Raises:
            ValueError: Si el job_id ya existe
        """
        if job_id is None:
            job_id = f"JOB-{uuid4().hex[:12]}"
        
        with self._operation_lock:
            # Verificar que no existe
            if job_id in self._jobs:
                self.logger.warning(f"Intento de crear job duplicado: {job_id}")
                raise ValueError(f"Job con ID '{job_id}' ya existe")
            
            # Crear nuevo job
            job_info = JobInfo(job_id)
            if metadata:
                job_info.metadata = metadata
            
            # Almacenar
            self._jobs[job_id] = job_info
            
            # Log con contexto
            job_logger = self.logger.bind(job_id=job_id)
            job_logger.info(
                "Job creado",
                status=job_info.status,
                metadata_keys=list(metadata.keys()) if metadata else []
            )
            
            # Verificar límite de jobs
            if len(self._jobs) > self._max_jobs:
                self.logger.warning(
                    f"Límite de jobs excedido: {len(self._jobs)}/{self._max_jobs}. "
                    "Considerar ejecutar limpieza."
                )
            
            return job_id
    
    def update_status(
        self, 
        job_id: str, 
        status: str, 
        result: Optional[Dict[str, Any]] = None,
        error: Optional[Dict[str, Any]] = None,
        metadata_update: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Actualiza el estado de un job existente.
        
        Args:
            job_id: ID del job a actualizar
            status: Nuevo estado del job
            result: Resultado del procesamiento (para estado completed)
            error: Información de error (para estado failed)
            metadata_update: Metadatos adicionales a agregar
            
        Returns:
            True si se actualizó exitosamente, False si no existe el job
            
        Raises:
            ValueError: Si el estado no es válido
        """
        # Validar estado
        valid_states = [JobStatus.PENDING, JobStatus.PROCESSING, JobStatus.COMPLETED, JobStatus.FAILED]
        if status not in valid_states:
            raise ValueError(f"Estado inválido: {status}. Debe ser uno de: {valid_states}")
        
        with self._operation_lock:
            # Buscar job
            if job_id not in self._jobs:
                self.logger.warning(f"Intento de actualizar job inexistente: {job_id}")
                return False
            
            job_info = self._jobs[job_id]
            old_status = job_info.status
            
            # Actualizar campos
            job_info.status = status
            job_info.updated_at = datetime.utcnow()
            
            if result is not None:
                job_info.result = result
            
            if error is not None:
                job_info.error = error
            
            if metadata_update:
                job_info.metadata.update(metadata_update)
            
            # Log con contexto
            job_logger = self.logger.bind(job_id=job_id)
            job_logger.info(
                f"Job actualizado: {old_status} -> {status}",
                old_status=old_status,
                new_status=status,
                has_result=result is not None,
                has_error=error is not None
            )
            
            return True
    
    def get_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el estado actual de un job.
        
        Args:
            job_id: ID del job a consultar
            
        Returns:
            Diccionario con información del job o None si no existe
        """
        with self._operation_lock:
            if job_id not in self._jobs:
                self.logger.debug(f"Consulta de job inexistente: {job_id}")
                return None
            
            job_info = self._jobs[job_id]
            
            # Log de consulta
            self.logger.debug(
                f"Consulta de estado de job",
                job_id=job_id,
                status=job_info.status
            )
            
            return job_info.to_dict()
    
    def delete_job(self, job_id: str) -> bool:
        """
        Elimina un job del almacenamiento.
        
        Args:
            job_id: ID del job a eliminar
            
        Returns:
            True si se eliminó, False si no existía
        """
        with self._operation_lock:
            if job_id not in self._jobs:
                self.logger.debug(f"Intento de eliminar job inexistente: {job_id}")
                return False
            
            # Obtener info antes de eliminar para logging
            job_info = self._jobs[job_id]
            
            # Eliminar
            del self._jobs[job_id]
            
            self.logger.info(
                f"Job eliminado",
                job_id=job_id,
                status=job_info.status,
                age_minutes=(datetime.utcnow() - job_info.created_at).total_seconds() / 60
            )
            
            return True
    
    def cleanup_old_jobs(self, retention_minutes: Optional[int] = None) -> int:
        """
        Elimina jobs antiguos según el tiempo de retención.
        
        Args:
            retention_minutes: Minutos de retención (usa default si no se especifica)
            
        Returns:
            Número de jobs eliminados
        """
        if retention_minutes is None:
            retention_minutes = self._retention_minutes
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=retention_minutes)
        jobs_to_delete = []
        
        with self._operation_lock:
            # Identificar jobs a eliminar
            for job_id, job_info in self._jobs.items():
                # Solo eliminar jobs terminados (completed o failed)
                if job_info.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                    if job_info.updated_at < cutoff_time:
                        jobs_to_delete.append(job_id)
            
            # Eliminar jobs
            for job_id in jobs_to_delete:
                del self._jobs[job_id]
            
            # Log de limpieza
            if jobs_to_delete:
                self.logger.info(
                    f"Limpieza de jobs antiguos completada",
                    jobs_deleted=len(jobs_to_delete),
                    retention_minutes=retention_minutes,
                    remaining_jobs=len(self._jobs)
                )
            
            return len(jobs_to_delete)
    
    def get_all_jobs(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtiene todos los jobs o filtrados por estado.
        
        Args:
            status_filter: Estado para filtrar (opcional)
            
        Returns:
            Lista de diccionarios con información de jobs
        """
        with self._operation_lock:
            jobs = []
            
            for job_info in self._jobs.values():
                if status_filter is None or job_info.status == status_filter:
                    jobs.append(job_info.to_dict())
            
            self.logger.debug(
                f"Consulta de todos los jobs",
                total_jobs=len(self._jobs),
                filtered_jobs=len(jobs),
                status_filter=status_filter
            )
            
            return jobs
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del servicio.
        
        Returns:
            Diccionario con estadísticas actuales
        """
        with self._operation_lock:
            # Contar por estado
            status_counts = {
                JobStatus.PENDING: 0,
                JobStatus.PROCESSING: 0,
                JobStatus.COMPLETED: 0,
                JobStatus.FAILED: 0
            }
            
            oldest_job_age = None
            newest_job_age = None
            
            now = datetime.utcnow()
            
            for job_info in self._jobs.values():
                status_counts[job_info.status] += 1
                
                job_age = (now - job_info.created_at).total_seconds()
                
                if oldest_job_age is None or job_age > oldest_job_age:
                    oldest_job_age = job_age
                
                if newest_job_age is None or job_age < newest_job_age:
                    newest_job_age = job_age
            
            return {
                "total_jobs": len(self._jobs),
                "status_counts": status_counts,
                "oldest_job_age_seconds": oldest_job_age,
                "newest_job_age_seconds": newest_job_age,
                "retention_minutes": self._retention_minutes,
                "max_jobs_limit": self._max_jobs
            }
    
    def set_retention_minutes(self, minutes: int):
        """
        Actualiza el tiempo de retención de jobs.
        
        Args:
            minutes: Nuevos minutos de retención
        """
        if minutes < 1:
            raise ValueError("El tiempo de retención debe ser al menos 1 minuto")
        
        old_retention = self._retention_minutes
        self._retention_minutes = minutes
        
        self.logger.info(
            f"Tiempo de retención actualizado",
            old_retention=old_retention,
            new_retention=minutes
        )


# Función helper para obtener la instancia singleton
def get_job_tracker_service() -> JobTrackerService:
    """
    Obtiene la instancia singleton del servicio de tracking.
    
    Returns:
        Instancia única de JobTrackerService
    """
    return JobTrackerService()


# Prueba del módulo si se ejecuta directamente
if __name__ == '__main__':
    import asyncio
    
    print("=== Prueba de JobTrackerService ===\n")
    
    # Obtener servicio
    tracker = get_job_tracker_service()
    
    # Test 1: Crear job
    print("1. Creando job...")
    job_id = tracker.create_job(metadata={"source": "test", "type": "article"})
    print(f"   Job creado: {job_id}")
    
    # Test 2: Consultar estado
    print("\n2. Consultando estado...")
    status = tracker.get_status(job_id)
    print(f"   Estado: {status['status']}")
    print(f"   Creado: {status['created_at']}")
    
    # Test 3: Actualizar a processing
    print("\n3. Actualizando a processing...")
    tracker.update_status(job_id, JobStatus.PROCESSING)
    status = tracker.get_status(job_id)
    print(f"   Nuevo estado: {status['status']}")
    
    # Test 4: Simular procesamiento
    print("\n4. Simulando procesamiento...")
    time.sleep(1)
    
    # Test 5: Completar con resultado
    print("\n5. Completando job...")
    result = {
        "elementos_procesados": 42,
        "tiempo_segundos": 1.5,
        "fragmento_id": "test-fragment-123"
    }
    tracker.update_status(job_id, JobStatus.COMPLETED, result=result)
    status = tracker.get_status(job_id)
    print(f"   Estado final: {status['status']}")
    print(f"   Resultado: {status['result']}")
    
    # Test 6: Crear job fallido
    print("\n6. Creando job que fallará...")
    failed_job_id = tracker.create_job()
    tracker.update_status(failed_job_id, JobStatus.PROCESSING)
    tracker.update_status(
        failed_job_id, 
        JobStatus.FAILED,
        error={"mensaje": "Error de prueba", "tipo": "TestError"}
    )
    
    # Test 7: Estadísticas
    print("\n7. Obteniendo estadísticas...")
    stats = tracker.get_stats()
    print(f"   Total jobs: {stats['total_jobs']}")
    print(f"   Por estado: {stats['status_counts']}")
    
    # Test 8: Thread safety
    print("\n8. Probando thread-safety...")
    def create_jobs_concurrent():
        for i in range(5):
            tracker.create_job(metadata={"thread": threading.current_thread().name})
    
    threads = []
    for i in range(3):
        t = threading.Thread(target=create_jobs_concurrent)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    final_stats = tracker.get_stats()
    print(f"   Jobs después de threads: {final_stats['total_jobs']}")
    
    print("\n=== Prueba completada ===")
