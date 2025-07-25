"""
WebSocket manager para actualizaciones en tiempo real.
Maneja conexiones WebSocket y broadcasting de mensajes.
"""

import json  # noqa: F401
import logging
from datetime import datetime
from typing import Dict, Set
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect  # noqa: F401

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Gestor de conexiones WebSocket para broadcasting de actualizaciones."""

    def __init__(self):
        # Diccionario de conexiones activas por sesión
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Mapeo de WebSocket a session_id para limpieza
        self.websocket_sessions: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, session_id: str = None) -> str:
        """
        Acepta una nueva conexión WebSocket.

        Args:
            websocket: Conexión WebSocket
            session_id: ID de sesión opcional, se genera uno si no se proporciona

        Returns:
            str: ID de sesión asignado
        """
        await websocket.accept()

        if session_id is None:
            session_id = str(uuid4())

        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()

        self.active_connections[session_id].add(websocket)
        self.websocket_sessions[websocket] = session_id

        logger.info(f"Cliente conectado a sesión {session_id}")

        # Enviar mensaje de bienvenida
        await self.send_personal_message(
            {
                "type": "connection",
                "status": "connected",
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
            websocket,
        )

        return session_id

    def disconnect(self, websocket: WebSocket):
        """
        Elimina una conexión WebSocket.

        Args:
            websocket: Conexión WebSocket a eliminar
        """
        session_id = self.websocket_sessions.get(websocket)

        if session_id:
            self.active_connections[session_id].discard(websocket)

            # Si no quedan conexiones en la sesión, eliminarla
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

            del self.websocket_sessions[websocket]
            logger.info(f"Cliente desconectado de sesión {session_id}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """
        Envía un mensaje a una conexión específica.

        Args:
            message: Diccionario con el mensaje
            websocket: Conexión WebSocket destino
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error enviando mensaje personal: {e}")

    async def broadcast_to_session(self, message: dict, session_id: str):
        """
        Envía un mensaje a todas las conexiones de una sesión.

        Args:
            message: Diccionario con el mensaje
            session_id: ID de la sesión
        """
        if session_id in self.active_connections:
            disconnected = []

            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting a conexión: {e}")
                    disconnected.append(connection)

            # Limpiar conexiones fallidas
            for conn in disconnected:
                self.disconnect(conn)

    async def broadcast_batch_progress(
        self,
        session_id: str,
        batch_id: str,
        current_item: int,
        total_items: int,
        item_status: dict,
    ):
        """
        Envía actualización de progreso de procesamiento batch.

        Args:
            session_id: ID de la sesión
            batch_id: ID del batch
            current_item: Número del item actual
            total_items: Total de items
            item_status: Estado del item actual
        """
        message = {
            "type": "batch_progress",
            "batch_id": batch_id,
            "progress": {
                "current": current_item,
                "total": total_items,
                "percentage": round((current_item / total_items) * 100, 2),
            },
            "item": item_status,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self.broadcast_to_session(message, session_id)

    async def broadcast_analysis_progress(
        self,
        session_id: str,
        site_url: str,
        stage: str,
        progress: int,
        details: dict = None,
    ):
        """
        Envía actualización de progreso de análisis.

        Args:
            session_id: ID de la sesión
            site_url: URL del sitio siendo analizado
            stage: Etapa del análisis
            progress: Porcentaje de progreso (0-100)
            details: Detalles adicionales
        """
        message = {
            "type": "analysis_progress",
            "site_url": site_url,
            "stage": stage,
            "progress": progress,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self.broadcast_to_session(message, session_id)

    async def broadcast_generation_complete(
        self,
        session_id: str,
        spider_name: str,
        file_path: str,
        download_url: str = None,
    ):
        """
        Notifica que la generación de un spider se completó.

        Args:
            session_id: ID de la sesión
            spider_name: Nombre del spider
            file_path: Ruta del archivo generado
            download_url: URL de descarga opcional
        """
        message = {
            "type": "generation_complete",
            "spider_name": spider_name,
            "file_path": file_path,
            "download_url": download_url,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self.broadcast_to_session(message, session_id)

    async def broadcast_error(
        self, session_id: str, error_type: str, error_message: str, context: dict = None
    ):
        """
        Envía notificación de error.

        Args:
            session_id: ID de la sesión
            error_type: Tipo de error
            error_message: Mensaje de error
            context: Contexto adicional
        """
        message = {
            "type": "error",
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {},
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self.broadcast_to_session(message, session_id)


# Instancia global del manager
manager = ConnectionManager()
