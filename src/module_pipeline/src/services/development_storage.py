"""
Servicio de almacenamiento para modo de desarrollo
Implementación EXACTA según Pipeline_Automatico_Modo_Desarrollo.md
"""

import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from ..core.logging_config import logger


class DevelopmentStorageService:
    def __init__(self, output_dir: str = "/pruebas_pipeline/development_outputs"):
        self.output_dir = Path(output_dir)
        logger.info(f"DevelopmentStorageService inicializado: {self.output_dir}")
    
    def insertar_fragmento_completo(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            timestamp = datetime.now().isoformat()
            fragmento_id = str(uuid.uuid4())
            fecha = datetime.now().strftime('%Y-%m-%d')
            
            # 1. Guardar en 01_articulos_extraidos/por_fecha/
            self._save_articulo_extraido(payload, fragmento_id, fecha)
            
            # 2. Guardar en 02_fases_pipeline/
            self._save_fases_pipeline(payload, fragmento_id)
            
            # 3. Guardar en 03_resultados_finales/
            self._save_resultado_final(payload, fragmento_id, timestamp)
            
            # 4. Actualizar métricas en 04_metricas_rendimiento/
            self._update_metrics(payload, fragmento_id, timestamp)
            
            return {
                "fragmento_id": fragmento_id,
                "timestamp": timestamp,
                "modo": "desarrollo",
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
    
    def _save_articulo_extraido(self, payload: Dict, fragmento_id: str, fecha: str):
        """Guardar en 01_articulos_extraidos/por_fecha/"""
        fecha_dir = self.output_dir / "01_articulos_extraidos" / "por_fecha" / fecha
        fecha_dir.mkdir(parents=True, exist_ok=True)
        
        articulo_data = {
            "fragmento_id": fragmento_id,
            "contenido_original": payload.get("contenido_original", ""),
            "titulo": payload.get("titulo", ""),
            "url": payload.get("url", ""),
            "fuente": payload.get("fuente", "")
        }
        
        with open(fecha_dir / f"articulo_{fragmento_id}.json", 'w', encoding='utf-8') as f:
            json.dump(articulo_data, f, ensure_ascii=False, indent=2)
    
    def _save_fases_pipeline(self, payload: Dict, fragmento_id: str):
        """Guardar en 02_fases_pipeline/ TODAS las fases según especificación"""
        
        # FASE 1: TRIAJE
        fase1_dir = self.output_dir / "02_fases_pipeline" / "fase_1_triaje"
        if "idioma" in payload:
            (fase1_dir / "idioma_detectado").mkdir(parents=True, exist_ok=True)
            with open(fase1_dir / "idioma_detectado" / f"idioma_{fragmento_id}.json", 'w', encoding='utf-8') as f:
                json.dump({"fragmento_id": fragmento_id, "idioma": payload["idioma"]}, f, ensure_ascii=False, indent=2)
        
        if "relevancia" in payload:
            (fase1_dir / "relevancia_evaluada").mkdir(parents=True, exist_ok=True)
            with open(fase1_dir / "relevancia_evaluada" / f"relevancia_{fragmento_id}.json", 'w', encoding='utf-8') as f:
                json.dump({"fragmento_id": fragmento_id, "relevancia": payload["relevancia"]}, f, ensure_ascii=False, indent=2)
        
        if "contenido_limpio" in payload:
            (fase1_dir / "contenido_limpio").mkdir(parents=True, exist_ok=True)
            with open(fase1_dir / "contenido_limpio" / f"contenido_{fragmento_id}.json", 'w', encoding='utf-8') as f:
                json.dump({"fragmento_id": fragmento_id, "contenido_limpio": payload["contenido_limpio"]}, f, ensure_ascii=False, indent=2)
        
        # FASE 2: ELEMENTOS BÁSICOS
        fase2_dir = self.output_dir / "02_fases_pipeline" / "fase_2_elementos_basicos"
        
        if "entidades" in payload:
            (fase2_dir / "entidades_identificadas").mkdir(parents=True, exist_ok=True)
            with open(fase2_dir / "entidades_identificadas" / f"entidades_{fragmento_id}.json", 'w', encoding='utf-8') as f:
                json.dump({"fragmento_id": fragmento_id, "entidades": payload["entidades"]}, f, ensure_ascii=False, indent=2)
        
        if "hechos" in payload:
            (fase2_dir / "hechos_extraidos").mkdir(parents=True, exist_ok=True)
            with open(fase2_dir / "hechos_extraidos" / f"hechos_{fragmento_id}.json", 'w', encoding='utf-8') as f:
                json.dump({"fragmento_id": fragmento_id, "hechos": payload["hechos"]}, f, ensure_ascii=False, indent=2)
        
        if "clasificacion" in payload:
            (fase2_dir / "clasificacion_asignada").mkdir(parents=True, exist_ok=True)
            with open(fase2_dir / "clasificacion_asignada" / f"clasificacion_{fragmento_id}.json", 'w', encoding='utf-8') as f:
                json.dump({"fragmento_id": fragmento_id, "clasificacion": payload["clasificacion"]}, f, ensure_ascii=False, indent=2)
        
        # FASE 3: CITAS Y DATOS
        fase3_dir = self.output_dir / "02_fases_pipeline" / "fase_3_citas_datos"
        
        if "citas" in payload:
            (fase3_dir / "citas_textuales").mkdir(parents=True, exist_ok=True)
            with open(fase3_dir / "citas_textuales" / f"citas_{fragmento_id}.json", 'w', encoding='utf-8') as f:
                json.dump({"fragmento_id": fragmento_id, "citas": payload["citas"]}, f, ensure_ascii=False, indent=2)
        
        if "datos_cuantitativos" in payload:
            (fase3_dir / "datos_cuantitativos").mkdir(parents=True, exist_ok=True)
            with open(fase3_dir / "datos_cuantitativos" / f"datos_{fragmento_id}.json", 'w', encoding='utf-8') as f:
                json.dump({"fragmento_id": fragmento_id, "datos_cuantitativos": payload["datos_cuantitativos"]}, f, ensure_ascii=False, indent=2)
        
        if "fuentes" in payload:
            (fase3_dir / "fuentes_referenciadas").mkdir(parents=True, exist_ok=True)
            with open(fase3_dir / "fuentes_referenciadas" / f"fuentes_{fragmento_id}.json", 'w', encoding='utf-8') as f:
                json.dump({"fragmento_id": fragmento_id, "fuentes": payload["fuentes"]}, f, ensure_ascii=False, indent=2)
        
        # FASE 4: NORMALIZACIÓN
        fase4_dir = self.output_dir / "02_fases_pipeline" / "fase_4_normalizacion"
        
        if "entidades_vinculadas" in payload:
            (fase4_dir / "entidades_vinculadas").mkdir(parents=True, exist_ok=True)
            with open(fase4_dir / "entidades_vinculadas" / f"vinculadas_{fragmento_id}.json", 'w', encoding='utf-8') as f:
                json.dump({"fragmento_id": fragmento_id, "entidades_vinculadas": payload["entidades_vinculadas"]}, f, ensure_ascii=False, indent=2)
        
        if "relaciones" in payload:
            (fase4_dir / "relaciones_detectadas").mkdir(parents=True, exist_ok=True)
            with open(fase4_dir / "relaciones_detectadas" / f"relaciones_{fragmento_id}.json", 'w', encoding='utf-8') as f:
                json.dump({"fragmento_id": fragmento_id, "relaciones": payload["relaciones"]}, f, ensure_ascii=False, indent=2)
        
        if "metadatos" in payload:
            (fase4_dir / "metadatos_enriquecidos").mkdir(parents=True, exist_ok=True)
            with open(fase4_dir / "metadatos_enriquecidos" / f"metadatos_{fragmento_id}.json", 'w', encoding='utf-8') as f:
                json.dump({"fragmento_id": fragmento_id, "metadatos": payload["metadatos"]}, f, ensure_ascii=False, indent=2)
    
    def _save_resultado_final(self, payload: Dict, fragmento_id: str, timestamp: str):
        """Guardar en 03_resultados_finales/"""
        has_errors = bool(payload.get("errores") or payload.get("error_detalle"))
        subfolder = "fallidos" if has_errors else "exitosos"
        
        resultado_dir = self.output_dir / "03_resultados_finales" / subfolder
        resultado_data = {
            "fragmento_id": fragmento_id,
            "timestamp": timestamp,
            "payload_completo": payload
        }
        
        with open(resultado_dir / f"resultado_{fragmento_id}.json", 'w', encoding='utf-8') as f:
            json.dump(resultado_data, f, ensure_ascii=False, indent=2)
    
    def _update_metrics(self, payload: Dict, fragmento_id: str, timestamp: str):
        """Actualizar métricas EXACTAS en 04_metricas_rendimiento/"""
        metrics_dir = self.output_dir / "04_metricas_rendimiento"
        
        # content_quality.json
        content_file = metrics_dir / "content_quality.json"
        if content_file.exists():
            with open(content_file, 'r') as f:
                data = json.load(f)
        else:
            data = {"metrics": []}
        
        data["metrics"].append({
            "fragmento_id": fragmento_id,
            "timestamp": timestamp,
            "entidades_count": len(payload.get("entidades", [])),
            "hechos_count": len(payload.get("hechos", [])),
            "citas_count": len(payload.get("citas", []))
        })
        
        with open(content_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # spider_stats.json
        spider_file = metrics_dir / "spider_stats.json"
        fuente = payload.get("fuente", "unknown")
        if spider_file.exists():
            with open(spider_file, 'r') as f:
                data = json.load(f)
        else:
            data = {"spiders": {}}
        
        if fuente not in data["spiders"]:
            data["spiders"][fuente] = {"total": 0, "successful": 0}
        
        data["spiders"][fuente]["total"] += 1
        if not payload.get("errores"):
            data["spiders"][fuente]["successful"] += 1
        
        with open(spider_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # pipeline_timing.json
        timing_file = metrics_dir / "pipeline_timing.json"
        if timing_file.exists():
            with open(timing_file, 'r') as f:
                data = json.load(f)
        else:
            data = {"timing_metrics": []}
        
        data["timing_metrics"].append({
            "fragmento_id": fragmento_id,
            "timestamp": timestamp,
            "processing_time": payload.get("processing_time", 0),
            "fase_1_time": payload.get("fase_1_time", 0),
            "fase_2_time": payload.get("fase_2_time", 0),
            "fase_3_time": payload.get("fase_3_time", 0),
            "fase_4_time": payload.get("fase_4_time", 0)
        })
        
        with open(timing_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # error_analysis.json
        error_file = metrics_dir / "error_analysis.json"
        if error_file.exists():
            with open(error_file, 'r') as f:
                data = json.load(f)
        else:
            data = {"errors": []}
        
        if payload.get("errores") or payload.get("error_detalle"):
            data["errors"].append({
                "fragmento_id": fragmento_id,
                "timestamp": timestamp,
                "error_type": payload.get("error_type", "unknown"),
                "error_message": payload.get("error_detalle", payload.get("errores", "")),
                "fase_error": payload.get("fase_error", "unknown")
            })
            
            with open(error_file, 'w') as f:
                json.dump(data, f, indent=2)