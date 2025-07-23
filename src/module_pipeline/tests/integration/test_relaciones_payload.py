import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from typing import Dict, Any, List

from ...src.services.payload_builder import PayloadBuilder
from ...src.models.persistencia import (
    ArticuloPersistenciaPayload,
    RelacionHechosItem,
    RelacionEntidadesItem,
    ContradiccionDetectadaItem,
    HechoExtraidoItem,
    EntidadAutonomaItem
)

class TestRelacionesPayload(unittest.TestCase):
    """Tests específicos para validar el manejo de relaciones en PayloadBuilder"""
    
    def setUp(self):
        self.builder = PayloadBuilder()
        self.fecha_actual = datetime.now(timezone.utc).isoformat()
        
        # Datos básicos para el artículo
        self.metadatos_articulo = {
            "url": "http://test.com/articulo",
            "titular": "Artículo con Relaciones",
            "medio": "Test Media",
            "fecha_publicacion": self.fecha_actual,
            "contenido_texto_original": "Contenido de prueba"
        }
        
        self.procesamiento_articulo = {
            "estado_procesamiento_final_pipeline": "completado_ok",
            "fecha_procesamiento_pipeline": self.fecha_actual,
            "fecha_ingesta_sistema": self.fecha_actual
        }
        
        # Hechos de prueba
        self.hechos_data = [
            {
                "id_temporal": "HECHO-1",
                "contenido": "Primer hecho de prueba",
                "tipo_hecho": "SUCESO"
            },
            {
                "id_temporal": "HECHO-2", 
                "contenido": "Segundo hecho de prueba",
                "tipo_hecho": "ANUNCIO"
            },
            {
                "id_temporal": "HECHO-3",
                "contenido": "Tercer hecho contradictorio",
                "tipo_hecho": "SUCESO"
            }
        ]
        
        # Entidades de prueba
        self.entidades_data = [
            {
                "id": "ENT-1",
                "nombre": "Entidad Uno",
                "tipo": "ORGANIZACION",
                "relevancia": 8
            },
            {
                "id": "ENT-2",
                "nombre": "Entidad Dos", 
                "tipo": "PERSONA",
                "relevancia": 7
            }
        ]
    
    def test_relaciones_hechos_mapeo_correcto(self):
        """Verifica que las relaciones hecho-hecho se mapeen correctamente"""
        relaciones_hechos = [
            {
                "hecho_origen_id": 1,
                "hecho_destino_id": 2,
                "tipo_relacion": "causa",
                "descripcion_relacion": "El hecho 1 causó el hecho 2",
                "fuerza_relacion": 8
            }
        ]
        
        payload = self.builder.construir_payload_articulo(
            metadatos_articulo_data=self.metadatos_articulo,
            procesamiento_articulo_data=self.procesamiento_articulo,
            hechos_extraidos_data=self.hechos_data,
            relaciones_hechos_data=relaciones_hechos
        )
        
        self.assertEqual(len(payload.relaciones_hechos), 1)
        relacion = payload.relaciones_hechos[0]
        self.assertEqual(relacion.id_hecho_origen, "1")
        self.assertEqual(relacion.id_hecho_destino, "2")
        self.assertEqual(relacion.tipo_relacion, "causa")
        self.assertEqual(relacion.descripcion_relacion, "El hecho 1 causó el hecho 2")
        self.assertEqual(relacion.fuerza_relacion, 8)
    
    def test_relaciones_entidades_mapeo_correcto(self):
        """Verifica que las relaciones entidad-entidad se mapeen correctamente"""
        relaciones_entidades = [
            {
                "entidad_origen_id": "ENT-1",
                "entidad_destino_id": "ENT-2",
                "tipo_relacion": "miembro_de",
                "descripcion": "ENT-2 es miembro de ENT-1",
                "fuerza_relacion": 7
            }
        ]
        
        payload = self.builder.construir_payload_articulo(
            metadatos_articulo_data=self.metadatos_articulo,
            procesamiento_articulo_data=self.procesamiento_articulo,
            entidades_autonomas_data=self.entidades_data,
            relaciones_entidades_data=relaciones_entidades
        )
        
        self.assertEqual(len(payload.relaciones_entidades), 1)
        relacion = payload.relaciones_entidades[0]
        self.assertEqual(relacion.id_entidad_origen, "ENT-1")
        self.assertEqual(relacion.id_entidad_destino, "ENT-2")
        self.assertEqual(relacion.tipo_relacion, "miembro_de")
        self.assertEqual(relacion.descripcion, "ENT-2 es miembro de ENT-1")
        self.assertEqual(relacion.fuerza_relacion, 7)
    
    def test_contradicciones_mapeo_correcto(self):
        """Verifica que las contradicciones se mapeen correctamente"""
        contradicciones = [
            {
                "hecho_principal_id": 1,
                "hecho_contradictorio_id": 3,
                "tipo_contradiccion": "contenido",
                "grado_contradiccion": 4,
                "descripcion": "Los hechos presentan información contradictoria"
            }
        ]
        
        payload = self.builder.construir_payload_articulo(
            metadatos_articulo_data=self.metadatos_articulo,
            procesamiento_articulo_data=self.procesamiento_articulo,
            hechos_extraidos_data=self.hechos_data,
            contradicciones_detectadas_data=contradicciones
        )
        
        self.assertEqual(len(payload.contradicciones_detectadas), 1)
        contradiccion = payload.contradicciones_detectadas[0]
        self.assertEqual(contradiccion.id_hecho_principal, "1")
        self.assertEqual(contradiccion.id_hecho_contradictorio, "3")
        self.assertEqual(contradiccion.tipo_contradiccion, "contenido")
        self.assertEqual(contradiccion.grado_contradiccion, 4)
        self.assertEqual(contradiccion.descripcion, "Los hechos presentan información contradictoria")
    
    def test_mapeo_campos_alternativos_relaciones_hechos(self):
        """Verifica que se manejen nombres de campos alternativos en relaciones hecho-hecho"""
        relaciones_hechos = [
            {
                "id_hecho_origen": "HECHO-1",  # Usando el nombre esperado por RPC
                "id_hecho_destino": "HECHO-2",
                "tipo_relacion": "seguimiento_de",
                "descripcion": "Es un seguimiento",  # Sin sufijo _relacion
                "fuerza_relacion": 6
            }
        ]
        
        payload = self.builder.construir_payload_articulo(
            metadatos_articulo_data=self.metadatos_articulo,
            procesamiento_articulo_data=self.procesamiento_articulo,
            hechos_extraidos_data=self.hechos_data,
            relaciones_hechos_data=relaciones_hechos
        )
        
        relacion = payload.relaciones_hechos[0]
        self.assertEqual(relacion.id_hecho_origen, "HECHO-1")
        self.assertEqual(relacion.id_hecho_destino, "HECHO-2")
        self.assertEqual(relacion.descripcion_relacion, "Es un seguimiento")
    
    def test_valores_default_relaciones(self):
        """Verifica que se apliquen valores por defecto correctamente"""
        relaciones_hechos = [
            {
                "hecho_origen_id": 1,
                "hecho_destino_id": 2,
                "tipo_relacion": "causa"
                # Sin descripcion_relacion ni fuerza_relacion
            }
        ]
        
        contradicciones = [
            {
                "hecho_principal_id": 1,
                "hecho_contradictorio_id": 3
                # Sin tipo_contradiccion, grado_contradiccion ni descripcion
            }
        ]
        
        payload = self.builder.construir_payload_articulo(
            metadatos_articulo_data=self.metadatos_articulo,
            procesamiento_articulo_data=self.procesamiento_articulo,
            hechos_extraidos_data=self.hechos_data,
            relaciones_hechos_data=relaciones_hechos,
            contradicciones_detectadas_data=contradicciones
        )
        
        # Verificar defaults en relaciones hechos
        relacion = payload.relaciones_hechos[0]
        self.assertEqual(relacion.fuerza_relacion, 5)  # Default
        self.assertEqual(relacion.descripcion_relacion, "")  # String vacío por mapeo
        
        # Verificar defaults en contradicciones
        contradiccion = payload.contradicciones_detectadas[0]
        self.assertEqual(contradiccion.tipo_contradiccion, "contenido")  # Default
        self.assertEqual(contradiccion.grado_contradiccion, 3)  # Default
        self.assertEqual(contradiccion.descripcion, "")  # String vacío por mapeo
    
    def test_validacion_integridad_referencial(self):
        """Verifica que se validen las referencias a IDs existentes"""
        # Relaciones con IDs que no existen en hechos
        relaciones_invalidas = [
            {
                "id_hecho_origen": "HECHO-99",  # No existe
                "id_hecho_destino": "HECHO-100",  # No existe
                "tipo_relacion": "causa"
            }
        ]
        
        # La validación debería fallar
        with self.assertRaises(ValueError) as context:
            self.builder.construir_payload_articulo(
                metadatos_articulo_data=self.metadatos_articulo,
                procesamiento_articulo_data=self.procesamiento_articulo,
                hechos_extraidos_data=self.hechos_data,
                relaciones_hechos_data=relaciones_invalidas
            )
        
        self.assertIn("Validación fallida", str(context.exception))
        self.assertIn("HECHO-99", str(context.exception))
        self.assertIn("HECHO-100", str(context.exception))
    
    def test_relaciones_vacias(self):
        """Verifica que el payload funcione sin relaciones"""
        payload = self.builder.construir_payload_articulo(
            metadatos_articulo_data=self.metadatos_articulo,
            procesamiento_articulo_data=self.procesamiento_articulo,
            hechos_extraidos_data=self.hechos_data,
            entidades_autonomas_data=self.entidades_data
            # Sin relaciones
        )
        
        self.assertEqual(len(payload.relaciones_hechos), 0)
        self.assertEqual(len(payload.relaciones_entidades), 0)
        self.assertEqual(len(payload.contradicciones_detectadas), 0)
    
    def test_multiples_relaciones(self):
        """Verifica el manejo de múltiples relaciones simultáneas"""
        relaciones_hechos = [
            {
                "hecho_origen_id": 1,
                "hecho_destino_id": 2,
                "tipo_relacion": "causa",
                "fuerza_relacion": 8
            },
            {
                "hecho_origen_id": 2,
                "hecho_destino_id": 3,
                "tipo_relacion": "consecuencia",
                "fuerza_relacion": 6
            }
        ]
        
        relaciones_entidades = [
            {
                "entidad_origen_id": "ENT-1",
                "entidad_destino_id": "ENT-2",
                "tipo_relacion": "aliado_con",
                "fuerza_relacion": 7
            }
        ]
        
        contradicciones = [
            {
                "hecho_principal_id": 1,
                "hecho_contradictorio_id": 3,
                "tipo_contradiccion": "fecha",
                "grado_contradiccion": 5
            }
        ]
        
        payload = self.builder.construir_payload_articulo(
            metadatos_articulo_data=self.metadatos_articulo,
            procesamiento_articulo_data=self.procesamiento_articulo,
            hechos_extraidos_data=self.hechos_data,
            entidades_autonomas_data=self.entidades_data,
            relaciones_hechos_data=relaciones_hechos,
            relaciones_entidades_data=relaciones_entidades,
            contradicciones_detectadas_data=contradicciones
        )
        
        self.assertEqual(len(payload.relaciones_hechos), 2)
        self.assertEqual(len(payload.relaciones_entidades), 1)
        self.assertEqual(len(payload.contradicciones_detectadas), 1)
        
        # Verificar que todas las relaciones se serializan correctamente
        json_output = payload.model_dump_json()
        self.assertIn("relaciones_hechos", json_output)
        self.assertIn("relaciones_entidades", json_output)
        self.assertIn("contradicciones_detectadas", json_output)


if __name__ == '__main__':
    unittest.main()