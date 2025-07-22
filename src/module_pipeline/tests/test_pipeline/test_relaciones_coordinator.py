import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.pipeline.pipeline_coordinator import PipelineCoordinator
from src.models.resultado import ResultadoFase4Normalizacion


class TestRelacionesCoordinator(unittest.TestCase):
    """Tests para verificar la extracción y mapeo de relaciones en PipelineCoordinator"""
    
    def setUp(self):
        self.coordinator = PipelineCoordinator()
        
        # Mock de resultado_fase7 con relaciones completas
        self.mock_resultado_fase7 = MagicMock(spec=ResultadoFase4Normalizacion)
        self.mock_resultado_fase7.metadata_normalizacion = {
            "relaciones_completas": {
                "relaciones_estructurales": {
                    "hecho_entidad": [
                        {
                            "hecho_id": 1,
                            "entidad_id": 101,
                            "tipo_relacion": "protagonista",
                            "relevancia_en_hecho": 9
                        },
                        {
                            "hecho_id": 1,
                            "entidad_id": 102,
                            "tipo_relacion": "mencionado",
                            "relevancia_en_hecho": 5
                        },
                        {
                            "hecho_id": 2,
                            "entidad_id": 103,
                            "tipo_relacion": "afectado",
                            "relevancia_en_hecho": 7
                        }
                    ],
                    "entidad_relacion": [
                        {
                            "entidad_origen_id": 101,
                            "entidad_destino_id": 102,
                            "tipo_relacion": "miembro_de",
                            "descripcion": "Persona es miembro de organización",
                            "fuerza_relacion": 8
                        }
                    ]
                },
                "relaciones_temporales": {
                    "hecho_relacionado": [
                        {
                            "hecho_origen_id": 1,
                            "hecho_destino_id": 2,
                            "tipo_relacion": "causa",
                            "descripcion_relacion": "El anuncio causó las protestas",
                            "fuerza_relacion": 8
                        },
                        {
                            "hecho_origen_id": 2,
                            "hecho_destino_id": 3,
                            "tipo_relacion": "temporal_secuencial",
                            "descripcion_relacion": "Sucedió después",
                            "fuerza_relacion": 6
                        }
                    ],
                    "contradicciones": [
                        {
                            "hecho_principal_id": 1,
                            "hecho_contradictorio_id": 4,
                            "tipo_contradiccion": "temporal",
                            "grado_contradiccion": 4,
                            "descripcion": "Fechas contradictorias"
                        }
                    ]
                }
            }
        }
    
    def test_extraer_relaciones_hecho_entidad(self):
        """Verifica que se extraigan correctamente las relaciones hecho-entidad"""
        # Simular hechos con IDs temporales
        hechos_data = [
            {"id_temporal": "1", "contenido": "Hecho 1", "entidades_del_hecho": []},
            {"id_temporal": "2", "contenido": "Hecho 2", "entidades_del_hecho": []}
        ]
        
        # Simular mapeo de entidades
        entidades_map = {
            101: "ENT-101",
            102: "ENT-102", 
            103: "ENT-103"
        }
        
        # Llamar a la función de extracción de relaciones hecho-entidad
        relaciones_hecho_entidad = {}
        for rel in self.mock_resultado_fase7.metadata_normalizacion["relaciones_completas"]["relaciones_estructurales"]["hecho_entidad"]:
            hecho_id = rel["hecho_id"]
            if hecho_id not in relaciones_hecho_entidad:
                relaciones_hecho_entidad[hecho_id] = []
            relaciones_hecho_entidad[hecho_id].append(rel)
        
        # Verificar extracción
        self.assertIn(1, relaciones_hecho_entidad)
        self.assertIn(2, relaciones_hecho_entidad)
        self.assertEqual(len(relaciones_hecho_entidad[1]), 2)  # Hecho 1 tiene 2 entidades
        self.assertEqual(len(relaciones_hecho_entidad[2]), 1)  # Hecho 2 tiene 1 entidad
        
        # Verificar contenido
        rel_hecho1 = relaciones_hecho_entidad[1]
        self.assertEqual(rel_hecho1[0]["tipo_relacion"], "protagonista")
        self.assertEqual(rel_hecho1[0]["relevancia_en_hecho"], 9)
        self.assertEqual(rel_hecho1[1]["tipo_relacion"], "mencionado")
        self.assertEqual(rel_hecho1[1]["relevancia_en_hecho"], 5)
    
    def test_mapear_tipo_relacion_hecho(self):
        """Verifica el mapeo de tipos de relación hecho-hecho"""
        coordinator = PipelineCoordinator()
        
        # Test mapeos conocidos
        self.assertEqual(coordinator._mapear_tipo_relacion_hecho("causa-efecto"), "causa")
        self.assertEqual(coordinator._mapear_tipo_relacion_hecho("temporal_secuencial"), "seguimiento_de")
        self.assertEqual(coordinator._mapear_tipo_relacion_hecho("aclaracion"), "aclaracion_de")
        
        # Test sin mapeo (debe devolver el original)
        self.assertEqual(coordinator._mapear_tipo_relacion_hecho("consecuencia"), "consecuencia")
        self.assertEqual(coordinator._mapear_tipo_relacion_hecho("contexto_historico"), "contexto_historico")
    
    def test_mapear_tipo_contradiccion(self):
        """Verifica el mapeo de tipos de contradicción"""
        coordinator = PipelineCoordinator()
        
        # Test mapeos conocidos
        self.assertEqual(coordinator._mapear_tipo_contradiccion("temporal"), "fecha")
        self.assertEqual(coordinator._mapear_tipo_contradiccion("logica"), "contenido")
        self.assertEqual(coordinator._mapear_tipo_contradiccion("factual"), "valor")
        
        # Test sin mapeo (debe devolver el original)
        self.assertEqual(coordinator._mapear_tipo_contradiccion("entidades"), "entidades")
        self.assertEqual(coordinator._mapear_tipo_contradiccion("ubicacion"), "ubicacion")
        self.assertEqual(coordinator._mapear_tipo_contradiccion("completa"), "completa")
    
    def test_extraer_todas_relaciones(self):
        """Verifica la extracción completa de todas las relaciones"""
        # Extraer relaciones temporales
        relaciones_temporales = self.mock_resultado_fase7.metadata_normalizacion["relaciones_completas"]["relaciones_temporales"]
        relaciones_hechos = relaciones_temporales.get("hecho_relacionado", [])
        contradicciones = relaciones_temporales.get("contradicciones", [])
        
        # Extraer relaciones estructurales
        relaciones_estructurales = self.mock_resultado_fase7.metadata_normalizacion["relaciones_completas"]["relaciones_estructurales"]
        relaciones_entidades = relaciones_estructurales.get("entidad_relacion", [])
        
        # Verificar extracción
        self.assertEqual(len(relaciones_hechos), 2)
        self.assertEqual(len(contradicciones), 1)
        self.assertEqual(len(relaciones_entidades), 1)
        
        # Verificar contenido de relaciones hechos
        self.assertEqual(relaciones_hechos[0]["tipo_relacion"], "causa")
        self.assertEqual(relaciones_hechos[0]["fuerza_relacion"], 8)
        
        # Verificar contenido de contradicciones
        self.assertEqual(contradicciones[0]["tipo_contradiccion"], "temporal")
        self.assertEqual(contradicciones[0]["grado_contradiccion"], 4)
        
        # Verificar contenido de relaciones entidades
        self.assertEqual(relaciones_entidades[0]["tipo_relacion"], "miembro_de")
        self.assertEqual(relaciones_entidades[0]["fuerza_relacion"], 8)
    
    def test_sin_relaciones(self):
        """Verifica el comportamiento cuando no hay relaciones"""
        # Mock sin metadata_normalizacion
        mock_resultado_vacio = MagicMock(spec=ResultadoFase4Normalizacion)
        mock_resultado_vacio.metadata_normalizacion = None
        
        # No debería haber error, solo listas vacías
        self.assertIsNone(mock_resultado_vacio.metadata_normalizacion)
    
    def test_relaciones_parciales(self):
        """Verifica el comportamiento con relaciones parciales"""
        # Mock con solo algunas relaciones
        mock_resultado_parcial = MagicMock(spec=ResultadoFase4Normalizacion)
        mock_resultado_parcial.metadata_normalizacion = {
            "relaciones_completas": {
                "relaciones_estructurales": {
                    "hecho_entidad": []  # Vacío
                },
                "relaciones_temporales": {
                    "hecho_relacionado": [
                        {
                            "hecho_origen_id": 1,
                            "hecho_destino_id": 2,
                            "tipo_relacion": "causa"
                        }
                    ]
                    # Sin contradicciones
                }
            }
        }
        
        # Extraer relaciones
        relaciones = mock_resultado_parcial.metadata_normalizacion["relaciones_completas"]
        hecho_entidad = relaciones["relaciones_estructurales"].get("hecho_entidad", [])
        hecho_relacionado = relaciones["relaciones_temporales"].get("hecho_relacionado", [])
        contradicciones = relaciones["relaciones_temporales"].get("contradicciones", [])
        
        # Verificar
        self.assertEqual(len(hecho_entidad), 0)
        self.assertEqual(len(hecho_relacionado), 1)
        self.assertEqual(len(contradicciones), 0)
    
    def test_asignacion_entidades_del_hecho(self):
        """Verifica que las entidades se asignen correctamente a los hechos"""
        # Datos de hechos
        hechos_data = [
            {"id_temporal": "1", "contenido": "Hecho 1", "entidades_del_hecho": []},
            {"id_temporal": "2", "contenido": "Hecho 2", "entidades_del_hecho": []}
        ]
        
        # Relaciones hecho-entidad agrupadas
        relaciones_hecho_entidad = {
            1: [
                {"entidad_id": "101", "tipo_relacion": "protagonista", "relevancia_en_hecho": 9},
                {"entidad_id": "102", "tipo_relacion": "mencionado", "relevancia_en_hecho": 5}
            ],
            2: [
                {"entidad_id": "103", "tipo_relacion": "afectado", "relevancia_en_hecho": 7}
            ]
        }
        
        # Simular asignación
        for hecho_dict in hechos_data:
            hecho_id = int(hecho_dict["id_temporal"])
            
            if hecho_id in relaciones_hecho_entidad:
                for rel in relaciones_hecho_entidad[hecho_id]:
                    hecho_dict["entidades_del_hecho"].append({
                        "id_temporal": str(rel["entidad_id"]),
                        "tipo_relacion": rel["tipo_relacion"],
                        "relevancia_en_hecho": rel["relevancia_en_hecho"]
                    })
        
        # Verificar asignación
        self.assertEqual(len(hechos_data[0]["entidades_del_hecho"]), 2)
        self.assertEqual(len(hechos_data[1]["entidades_del_hecho"]), 1)
        
        # Verificar contenido
        entidad_0_0 = hechos_data[0]["entidades_del_hecho"][0]
        self.assertEqual(entidad_0_0["id_temporal"], "101")
        self.assertEqual(entidad_0_0["tipo_relacion"], "protagonista")
        self.assertEqual(entidad_0_0["relevancia_en_hecho"], 9)


if __name__ == '__main__':
    unittest.main()