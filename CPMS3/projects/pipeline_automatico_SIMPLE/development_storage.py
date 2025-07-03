"""
Servicio de almacenamiento para modo de desarrollo
"""

import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from ..core.logging_config import logger


class DevelopmentStorageService:
    def __init__(self, output_dir: str = "/data/development_outputs"):
        self.output_dir = Path(output_dir)
        logger.info(f"DevelopmentStorageService inicializado: {self.output_dir}")
    
    def insertar_fragmento_completo(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            timestamp = datetime.now().isoformat()
            fragmento_id = str(uuid.uuid4())
            
            # Guardar resultado final
            resultado_file = self._save_resultado_final(payload, fragmento_id, timestamp)
            
            # Actualizar métricas simples
            self._update_simple_metrics(payload, fragmento_id, timestamp)
            
            return {
                "fragmento_id": fragmento_id,
                "timestamp": timestamp,
                "modo": "desarrollo",
                "archivo_creado": resultado_file,
                "exito": True
            }
            
        except Exception as e:
            logger.error(f"Error almacenando fragmento: {str(e)}")
            return {
                "fragmento_id": None,
                "timestamp": datetime.now().isoformat(),
                "modo": "desarrollo", 
                "exito": False,
                "error": str(e)
            }
    
    def _save_resultado_final(self, payload: Dict, fragmento_id: str, timestamp: str) -> str:
        fecha = datetime.now().strftime('%Y-%m-%d')
        resultado_dir = self.output_dir / "03_resultados_finales" / "exitosos"
        resultado_dir.mkdir(parents=True, exist_ok=True)
        
        resultado_file = resultado_dir / f"resultado_{fragmento_id}.json"
        
        resultado_data = {
            "fragmento_id": fragmento_id,
            "timestamp": timestamp,
            "payload_completo": payload
        }
        
        with open(resultado_file, 'w', encoding='utf-8') as f:
            json.dump(resultado_data, f, ensure_ascii=False, indent=2)
        
        return str(resultado_file)
    
    def _update_simple_metrics(self, payload: Dict, fragmento_id: str, timestamp: str):
        # Actualizar content_quality.json de forma simple
        metrics_dir = self.output_dir / "04_metricas_rendimiento"
        content_file = metrics_dir / "content_quality.json"
        
        if not content_file.exists():
            with open(content_file, 'w') as f:
                json.dump({"metrics": []}, f)
        
        # Leer, añadir, escribir
        with open(content_file, 'r') as f:
            data = json.load(f)
        
        data["metrics"].append({
            "fragmento_id": fragmento_id,
            "timestamp": timestamp,
            "entidades_count": len(payload.get("entidades", [])),
            "hechos_count": len(payload.get("hechos", []))
        })
        
        with open(content_file, 'w') as f:
            json.dump(data, f, indent=2)