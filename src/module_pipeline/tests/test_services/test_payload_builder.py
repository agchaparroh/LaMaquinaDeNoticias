import unittest
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List, Optional
from pydantic import ValidationError
import datetime

# Ajustar la ruta de importación según la estructura del proyecto
# Asumiendo que test_payload_builder.py está en tests/test_services/
# y payload_builder.py está en src/services/
# y persistencia.py está en src/models/
from src.services.payload_builder import PayloadBuilder
from src.models.persistencia import (
    ArticuloPersistenciaPayload as PayloadCompletoArticulo,
    FragmentoPersistenciaPayload as PayloadCompletoFragmento,
    HechoExtraidoItem
    # ... importar otros modelos necesarios para las aserciones
    # PayloadMetadatosArticulo y PayloadProcesamientoArticulo no se importan porque no son clases separadas
)

# Datos de prueba comunes
MOCK_FECHA_PROCESAMIENTO = datetime.datetime.now(datetime.timezone.utc).isoformat()
MOCK_RESUMEN_FRAGMENTO = "Resumen del fragmento de prueba."

MOCK_METADATOS_ARTICULO_DATA = {
    "url": "http://ejemplo.com/noticia1",
    "titular": "Título del Artículo de Prueba",
    "medio": "Fuente de Noticias Test",
    "fecha_publicacion": MOCK_FECHA_PROCESAMIENTO,
    "autor": "Autor Test",
    "idioma_original": "es",
    "contenido_texto_original": "Este es el contenido completo del artículo de prueba.",
    "fuente_original": "test-src-001",
    "storage_path": "/path/to/local/copy.html",
    "etiquetas_fuente": ["test", "artículo"],
    "es_opinion": False,
    "es_oficial": False,
    "metadata_original": {"clave": "valor"}
}

MOCK_PROCESAMIENTO_ARTICULO_DATA = {
    "resumen_generado_pipeline": "Este es un resumen generado del artículo.",
    "palabras_clave_generadas": ["prueba", "generado"],
    "sentimiento_general_articulo": "neutral",
    "embedding_articulo_vector": [0.1, 0.2, 0.3, 0.4, 0.5],
    "estado_procesamiento_final_pipeline": "completado_ok",
    "fecha_procesamiento_pipeline": MOCK_FECHA_PROCESAMIENTO,
    "version_pipeline_aplicada": "v1.0-test",
    "fecha_ingesta_sistema": MOCK_FECHA_PROCESAMIENTO,
    "error_detalle_pipeline": None,
}

MOCK_HECHOS_DATA = [{
    "id_temporal_hecho": "hecho_temp_001",
    "descripcion_hecho": "Un hecho importante ocurrió durante la prueba.",
    "tipo_hecho": "evento_prueba",
    "subtipo_hecho": "subevento_payload",
    "fecha_ocurrencia_hecho_inicio": MOCK_FECHA_PROCESAMIENTO,
    "lugar_ocurrencia_hecho": "Sala de Pruebas",
    "relevancia_hecho": 8,
    "contexto_adicional_hecho": "El reporte indica que un hecho importante ocurrió.",
    "entidades_del_hecho": [{
        "id_temporal_entidad": "ent_temp_001",
        "nombre_entidad": "PayloadBuilder",
        "tipo_entidad": "ComponenteSoftware",
        "rol_en_hecho": "sujeto_principal"
    }]
}]

MOCK_METADATOS_FRAGMENTO_DATA = {
    "indice_secuencial_fragmento": 1,
    "titulo_seccion_fragmento": "Sección de Prueba del Fragmento",
    "contenido_texto_original_fragmento": "Este es el contenido del fragmento de prueba.",
    "num_pagina_inicio_fragmento": 1,
    "num_pagina_fin_fragmento": 1
}


class TestPayloadBuilder(unittest.TestCase):

    def setUp(self):
        self.builder = PayloadBuilder()

    def test_construir_payload_articulo_completo_ok(self):
        payload = self.builder.construir_payload_articulo(
            metadatos_articulo_data=MOCK_METADATOS_ARTICULO_DATA,
            procesamiento_articulo_data=MOCK_PROCESAMIENTO_ARTICULO_DATA,
            hechos_extraidos_data=MOCK_HECHOS_DATA
            # Se pueden añadir más datos mock para otros campos opcionales
        )
        self.assertIsInstance(payload, PayloadCompletoArticulo)
        self.assertEqual(payload.titular, MOCK_METADATOS_ARTICULO_DATA["titular"]) # Acceder directamente al campo 'titular'
        self.assertEqual(len(payload.hechos_extraidos), 1)
        self.assertEqual(payload.hechos_extraidos[0].id_temporal_hecho, "hecho_temp_001")
        # Verificar que se puede serializar a JSON (Pydantic lo hace)
        self.assertTrue(payload.model_dump_json())

    def test_construir_payload_articulo_solo_requeridos_ok(self):
        # Prueba con solo los campos que no tienen default en Payload*Articulo
        # y que son pasados directamente (no listas opcionales)
        payload = self.builder.construir_payload_articulo(
            metadatos_articulo_data=MOCK_METADATOS_ARTICULO_DATA,
            procesamiento_articulo_data=MOCK_PROCESAMIENTO_ARTICULO_DATA
            # Todos los demás son listas opcionales o PayloadVinculacionExternaArticulo que es opcional
        )
        self.assertIsInstance(payload, PayloadCompletoArticulo)
        self.assertEqual(payload.url, MOCK_METADATOS_ARTICULO_DATA["url"]) # Acceder directamente al campo 'url'
        self.assertEqual(payload.resumen_generado_pipeline, MOCK_PROCESAMIENTO_ARTICULO_DATA["resumen_generado_pipeline"]) # Acceder directamente al campo 'resumen_generado_pipeline'
        self.assertEqual(len(payload.hechos_extraidos), 0) # Debería ser lista vacía por default
        # vinculacion_externa_articulo field has been removed from the model
        self.assertTrue(payload.model_dump_json())

    def test_construir_payload_articulo_datos_invalidos_metadatos(self):
        invalid_metadatos = MOCK_METADATOS_ARTICULO_DATA.copy()
        invalid_metadatos["url_original_articulo"] = "esto-no-es-un-url-valido" # Asumiendo HttpUrl, aunque el modelo actual usa str
        
        # Si el modelo Pydantic PayloadMetadatosArticulo usa HttpUrl para url_original_articulo,
        # esto debería fallar. Si es solo `str`, Pydantic no lo validará como URL.
        # Por ahora, el modelo usa `str`, así que esta prueba específica de URL no fallará por Pydantic.
        # Para probar una falla real con `str`, podríamos omitir un campo requerido.
        
        del invalid_metadatos["titular"] # Campo requerido, el nombre correcto es 'titular'
        with self.assertRaises(ValueError) as context: # Error de construcción por Pydantic
            self.builder.construir_payload_articulo(
                metadatos_articulo_data=invalid_metadatos,
                procesamiento_articulo_data=MOCK_PROCESAMIENTO_ARTICULO_DATA
            )
        self.assertIn("Error de validación Pydantic en payload del artículo", str(context.exception))
        self.assertIn("titular", str(context.exception).lower()) # El campo en el modelo Pydantic es 'titular'

    def test_construir_payload_articulo_datos_invalidos_hecho(self):
        invalid_hechos = [{
            # Falta id_temporal_hecho que es requerido en HechoExtraidoItem
            "descripcion_hecho": "Un hecho sin ID." 
        }]
        with self.assertRaises(ValueError) as context:
            self.builder.construir_payload_articulo(
                metadatos_articulo_data=MOCK_METADATOS_ARTICULO_DATA,
                procesamiento_articulo_data=MOCK_PROCESAMIENTO_ARTICULO_DATA,
                hechos_extraidos_data=invalid_hechos
            )
        self.assertIn("Error de validación Pydantic en payload del artículo", str(context.exception))
        self.assertIn("'loc': ('id_temporal_hecho',)", str(context.exception)) # Verifica que el error es sobre el campo 'id_temporal_hecho'
        self.assertIn("Field required", str(context.exception)) # Verifica el tipo de error de Pydantic

    def test_construir_payload_fragmento_completo_ok(self):
        payload = self.builder.construir_payload_fragmento(
            metadatos_fragmento_data=MOCK_METADATOS_FRAGMENTO_DATA,
            resumen_generado_fragmento="Resumen del fragmento de prueba.",
            estado_procesamiento_final_fragmento="completado_fragmento_ok",
            fecha_procesamiento_pipeline_fragmento=MOCK_FECHA_PROCESAMIENTO,
            hechos_extraidos_data=MOCK_HECHOS_DATA # Reutilizando mock de hechos
        )
        self.assertIsInstance(payload, PayloadCompletoFragmento)
        self.assertEqual(payload.indice_secuencial_fragmento, MOCK_METADATOS_FRAGMENTO_DATA["indice_secuencial_fragmento"]) # Verificar un campo que sí existe
        self.assertEqual(payload.contenido_texto_original_fragmento, MOCK_METADATOS_FRAGMENTO_DATA["contenido_texto_original_fragmento"])
        self.assertEqual(payload.resumen_generado_fragmento, "Resumen del fragmento de prueba.")
        self.assertEqual(len(payload.hechos_extraidos), 1)
        self.assertTrue(payload.model_dump_json())

    def test_construir_payload_fragmento_solo_requeridos_ok(self):
        payload = self.builder.construir_payload_fragmento(
            metadatos_fragmento_data=MOCK_METADATOS_FRAGMENTO_DATA,
            resumen_generado_fragmento=None, # Es Optional[str] pero es argumento posicional
            estado_procesamiento_final_fragmento="completado_minimo", # Requerido
            fecha_procesamiento_pipeline_fragmento=MOCK_FECHA_PROCESAMIENTO # Requerido
        )
        self.assertIsInstance(payload, PayloadCompletoFragmento)
        self.assertEqual(payload.indice_secuencial_fragmento, MOCK_METADATOS_FRAGMENTO_DATA["indice_secuencial_fragmento"]) # Verificar un campo que sí existe en FragmentoPersistenciaPayload
        self.assertIsNone(payload.resumen_generado_fragmento)
        self.assertEqual(len(payload.hechos_extraidos), 0)
        self.assertTrue(payload.model_dump_json())

    def test_construir_payload_fragmento_datos_invalidos_metadatos(self):
        invalid_metadatos_fragmento = MOCK_METADATOS_FRAGMENTO_DATA.copy()
        del invalid_metadatos_fragmento["contenido_texto_original_fragmento"] # Campo requerido por FragmentoPersistenciaPayload

        with self.assertRaises(ValueError) as context:
            self.builder.construir_payload_fragmento(
                metadatos_fragmento_data=invalid_metadatos_fragmento,
                resumen_generado_fragmento=None, # Argumento posicional requerido
                estado_procesamiento_final_fragmento="completado_con_error", # Argumento posicional requerido
                fecha_procesamiento_pipeline_fragmento=MOCK_FECHA_PROCESAMIENTO
            )
        self.assertIn("Error de validación Pydantic en payload del fragmento", str(context.exception))
        self.assertIn("contenido_texto_original_fragmento", str(context.exception).lower())

if __name__ == '__main__':
    unittest.main()
