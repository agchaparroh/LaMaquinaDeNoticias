#!/bin/bash
# Script para monitorear logs del pipeline
echo "=== Monitoreando logs del pipeline ==="
echo "Buscando errores RPC y procesamiento exitoso..."
echo "----------------------------------------"
cd /home/ec2-user/projects/LaMaquinaDeNoticias/src/module_pipeline
docker-compose logs -f module-pipeline | grep -E "(ERROR.*actualizar_articulo|argument 1: key must not be null|Artículo actualizado exitosamente|estado_procesamiento.*completado|RPC actualizar_articulo_procesado)"