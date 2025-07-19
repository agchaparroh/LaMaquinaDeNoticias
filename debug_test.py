#!/usr/bin/env python3
"""Script de debug para verificar estado del código"""

import sys
import os
sys.path.insert(0, '/home/ec2-user/projects/LaMaquinaDeNoticias/src/module_pipeline')
os.chdir('/home/ec2-user/projects/LaMaquinaDeNoticias/src/module_pipeline')

from src.pipeline.pipeline_coordinator import PipelineCoordinator
from src.models.entrada import ArticuloProcesableItem, ArticuloInItem
from datetime import datetime, timezone

# Crear artículo de prueba
articulo_in = ArticuloInItem(
    articulo_id=9999,
    medio="Test Medio",
    area_geografica="Test Area",
    tipo_medio="Digital",
    titular="Test Titular",
    fecha_publicacion=datetime.now(timezone.utc),
    contenido_texto="Test contenido para debug",
    idioma="es",
    autor="Test Autor"
)

# Convertir a ArticuloProcesableItem
articulo = ArticuloProcesableItem.from_articulo_in_item(articulo_in)

print("=== DEBUG INFO ===")
print(f"ArticuloProcesableItem creado: {articulo.id_articulo}")
print(f"Tipo: {type(articulo).__name__}")

# Verificar PipelineCoordinator
coordinator = PipelineCoordinator()

# Verificar si el método tiene el código actualizado
import inspect
source = inspect.getsource(coordinator.ejecutar_pipeline_completo)
if "Detección de tipo de contenido" in source:
    print("✅ Código actualizado encontrado en ejecutar_pipeline_completo")
else:
    print("❌ Código NO actualizado en ejecutar_pipeline_completo")

# Verificar _generar_payload_articulo_completo
if hasattr(coordinator, '_generar_payload_articulo_completo'):
    print("✅ Método _generar_payload_articulo_completo existe")
else:
    print("❌ Método _generar_payload_articulo_completo NO existe")

# Verificar metadata
print("\n=== SIMULACIÓN DE METADATOS ===")
metadatos = {
    "tipo_contenido_original": type(articulo).__name__,
    "es_articulo_completo": isinstance(articulo, ArticuloProcesableItem),
    "articulo_original": articulo
}

print(f"es_articulo_completo: {metadatos['es_articulo_completo']}")
print(f"articulo_original presente: {metadatos.get('articulo_original') is not None}")
print(f"Tipo articulo_original: {type(metadatos.get('articulo_original')).__name__ if metadatos.get('articulo_original') else 'None'}")

# Test de condición
articulo_original_preserved = metadatos.get("articulo_original")
es_articulo_completo = metadatos.get("es_articulo_completo", False)

if articulo_original_preserved is not None and es_articulo_completo:
    print("\n✅ CONDICIÓN PARA ARTÍCULO SE CUMPLE")
else:
    print("\n❌ CONDICIÓN PARA ARTÍCULO NO SE CUMPLE")
    print(f"   articulo_original_preserved is not None: {articulo_original_preserved is not None}")
    print(f"   es_articulo_completo: {es_articulo_completo}")