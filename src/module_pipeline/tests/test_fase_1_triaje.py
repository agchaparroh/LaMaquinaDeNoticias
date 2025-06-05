import sys
import os
import unittest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from dotenv import load_dotenv # Añadido para cargar .env
from datetime import datetime, timezone # Asegurarse que esté importado si se usa en mocks
# import spacy # No es necesario importar spacy directamente aquí si se mockea
# from groq import Groq, APIError # No es necesario si se mockea y no se instancia

# --- INICIO DE CÓDIGO DE DEPURACIÓN ---
print("-" * 50)
print(f"DEBUG: Iniciando la carga de test_fase_1_triaje.py")
print(f"DEBUG: __name__ en test_fase_1_triaje.py: {__name__}")
print(f"DEBUG: __package__ en test_fase_1_triaje.py: {__package__}")
print(f"DEBUG: Directorio de trabajo actual (CWD): {os.getcwd()}")
print(f"DEBUG: Contenido de sys.path:")
for i, path_entry in enumerate(sys.path):
    print(f"DEBUG: sys.path[{i}]: {path_entry}")
print("-" * 50)
# --- FIN DE CÓDIGO DE DEPURACIÓN ---

# Cargar variables de entorno para las pruebas
# Asumiendo que .env está en el directorio module_pipeline, un nivel arriba de tests
# y que las pruebas se ejecutan desde module_pipeline
dotenv_path = os.path.join(os.getcwd(), '.env') # Asume que .env está en el CWD (module_pipeline)
if not os.path.exists(dotenv_path):
    # Si no está en CWD, intentar un nivel arriba desde la ubicación del test file
    # Esto es más robusto si se ejecutan tests individualmente desde el dir 'tests'
    dotenv_path_alt = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(dotenv_path_alt):
        dotenv_path = dotenv_path_alt

print(f"DEBUG: Intentando cargar .env desde: {dotenv_path}")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    print(f"DEBUG: .env cargado desde {dotenv_path}")
else:
    print(f"DEBUG: Archivo .env no encontrado en {dotenv_path} (ni en alternativa)")


try:
    print("DEBUG: Intentando importar 'src.pipeline.fase_1_triaje'...")
    from src.pipeline.fase_1_triaje import ejecutar_fase_1, ErrorFase1
    print("DEBUG: Importación de 'src.pipeline.fase_1_triaje' EXITOSA.")
    
    print("DEBUG: Intentando importar 'src.models.procesamiento'...")
    from src.models.procesamiento import ResultadoFase1Triaje, MetadatosFase1Triaje
    print("DEBUG: Importación de 'src.models.procesamiento' EXITOSA.")
    
    # Si necesitas otras importaciones de tu proyecto, añádelas aquí con 'src.'
    # Ejemplo:
    # print("DEBUG: Intentando importar 'src.config.settings'...")
    # from src.config.settings import load_config # Si es necesario globalmente
    # print("DEBUG: Importación de 'src.config.settings' EXITOSA.")

except ImportError as e:
    print(f"DEBUG: ERROR DE IMPORTACIÓN CAPTURADO EN test_fase_1_triaje.py: {e}")
    print(f"DEBUG: Traceback del error de importación:")
    import traceback
    traceback.print_exc()
    raise


class TestFase1Triaje(unittest.TestCase):

    def setUp(self):
        """Configuración inicial para cada prueba."""
        self.id_fragmento = str(uuid4())
        self.texto_original = "Este es un texto de prueba."
        self.texto_limpio_es = "Este es un texto de prueba limpio."
        self.texto_limpio_en = "This is a clean test text."
        self.texto_traducido_mock = "This is a clean test text. (traducido)"

        # No es necesario mockear groq_config si las funciones que lo usan son mockeadas
        # o si la configuración se carga correctamente desde el .env y las funciones
        # internas de fase_1_triaje acceden a os.environ directamente.

        self.evaluacion_triaje_procesar_mock = {
            "decision": "PROCESAR",
            "total_puntuacion": 85,
            "justificacion": "Es relevante.",
            "tipo_articulo": "Noticia",
            "elementos_clave": ["clave1", "clave2"],
            "relevancia_geografica_score": 5,
            "relevancia_tematica_score": 4,
        }
        self.evaluacion_triaje_descartar_mock = {
            "decision": "DESCARTAR",
            "total_puntuacion": 10,
            "justificacion": "No es relevante.",
            "tipo_articulo": "Opinión",
            "elementos_clave": [],
        }

    @patch.dict(os.environ, {"GROQ_API_KEY": "test_key"})
    @patch('src.pipeline.fase_1_triaje._cargar_modelo_spacy')
    @patch('src.pipeline.fase_1_triaje._limpiar_texto')
    @patch('src.pipeline.fase_1_triaje._detectar_idioma')
    @patch('src.pipeline.fase_1_triaje._llamar_groq_api_triaje')
    @patch('src.pipeline.fase_1_triaje._parsear_respuesta_triaje')
    @patch('src.pipeline.fase_1_triaje._llamar_groq_api_traduccion')
    def test_texto_espanol_procesar_no_traduce(self, mock_llamar_traduccion, mock_parsear_triaje, 
                                             mock_llamar_triaje, mock_detectar_idioma, 
                                             mock_limpiar_texto, mock_cargar_modelo):
        """Prueba un texto en español que es procesado y no necesita traducción."""
        mock_nlp = MagicMock()
        # mock_nlp.lang = 'es' # No es necesario si _detectar_idioma es mockeado
        mock_cargar_modelo.return_value = mock_nlp
        mock_limpiar_texto.return_value = self.texto_limpio_es
        mock_detectar_idioma.return_value = "es"
        mock_llamar_triaje.return_value = ("prompt_usado_mock", "respuesta_llm_cruda_mock")
        mock_parsear_triaje.return_value = self.evaluacion_triaje_procesar_mock
        
        resultado = ejecutar_fase_1(self.id_fragmento, self.texto_original)

        self.assertIsInstance(resultado, ResultadoFase1Triaje)
        self.assertEqual(str(resultado.id_fragmento), self.id_fragmento)  # Convertir UUID a string
        self.assertEqual(resultado.metadatos_specificos_triaje.texto_limpio_utilizado, self.texto_limpio_es)
        self.assertEqual(resultado.metadatos_specificos_triaje.idioma_detectado_original, "es")
        self.assertEqual(resultado.decision_triaje, "PROCESAR")
        self.assertEqual(resultado.puntuacion_triaje, 85)
        self.assertEqual(resultado.texto_para_siguiente_fase, self.texto_limpio_es)  # Para español no traducido
        mock_llamar_traduccion.assert_not_called()
        mock_limpiar_texto.assert_called_once_with(self.texto_original, mock_nlp)
        mock_detectar_idioma.assert_called_once_with(self.texto_limpio_es, mock_nlp) # El texto limpio se pasa a detectar idioma
        mock_llamar_triaje.assert_called_once()
        mock_parsear_triaje.assert_called_once_with("respuesta_llm_cruda_mock")

    @patch.dict(os.environ, {"GROQ_API_KEY": "test_key"})
    @patch('src.pipeline.fase_1_triaje._cargar_modelo_spacy')
    @patch('src.pipeline.fase_1_triaje._limpiar_texto')
    @patch('src.pipeline.fase_1_triaje._detectar_idioma')
    @patch('src.pipeline.fase_1_triaje._llamar_groq_api_triaje')
    @patch('src.pipeline.fase_1_triaje._parsear_respuesta_triaje')
    @patch('src.pipeline.fase_1_triaje._llamar_groq_api_traduccion')
    def test_texto_ingles_procesar_si_traduce(self, mock_llamar_traduccion, mock_parsear_triaje, 
                                              mock_llamar_triaje, mock_detectar_idioma, 
                                              mock_limpiar_texto, mock_cargar_modelo):
        """Prueba un texto en inglés que es procesado y necesita traducción."""
        mock_nlp = MagicMock()
        mock_cargar_modelo.return_value = mock_nlp
        mock_limpiar_texto.return_value = self.texto_limpio_en
        mock_detectar_idioma.return_value = "en"
        mock_llamar_triaje.return_value = ("prompt_usado_mock", "respuesta_llm_cruda_mock")
        mock_parsear_triaje.return_value = self.evaluacion_triaje_procesar_mock
        mock_llamar_traduccion.return_value = self.texto_traducido_mock

        resultado = ejecutar_fase_1(self.id_fragmento, self.texto_original)

        self.assertIsInstance(resultado, ResultadoFase1Triaje)
        self.assertEqual(resultado.metadatos_specificos_triaje.texto_limpio_utilizado, self.texto_limpio_en)
        self.assertEqual(resultado.metadatos_specificos_triaje.idioma_detectado_original, "en")
        self.assertEqual(resultado.decision_triaje, "PROCESAR")
        self.assertEqual(resultado.texto_para_siguiente_fase, self.texto_traducido_mock)
        mock_llamar_traduccion.assert_called_once()

    @patch.dict(os.environ, {}, clear=True)
    @patch('src.pipeline.fase_1_triaje._cargar_modelo_spacy')
    @patch('src.pipeline.fase_1_triaje._limpiar_texto')
    @patch('src.pipeline.fase_1_triaje._detectar_idioma')
    def test_falta_api_key_lanza_excepcion(self, mock_detectar_idioma, mock_limpiar_texto, mock_cargar_modelo):
        """Prueba que se lanza ErrorFase1 si no hay GROQ_API_KEY."""
        mock_nlp = MagicMock()
        mock_cargar_modelo.return_value = mock_nlp
        mock_limpiar_texto.return_value = self.texto_limpio_es
        mock_detectar_idioma.return_value = "es"

        with self.assertRaisesRegex(ErrorFase1, "GROQ_API_KEY no configurada en variables de entorno."):
            ejecutar_fase_1(self.id_fragmento, self.texto_original)

    @patch.dict(os.environ, {"GROQ_API_KEY": "test_key"})
    @patch('src.pipeline.fase_1_triaje._cargar_modelo_spacy')
    @patch('src.pipeline.fase_1_triaje._limpiar_texto')
    @patch('src.pipeline.fase_1_triaje._detectar_idioma')
    @patch('src.pipeline.fase_1_triaje._llamar_groq_api_triaje')
    @patch('src.pipeline.fase_1_triaje._parsear_respuesta_triaje')
    @patch('src.pipeline.fase_1_triaje._llamar_groq_api_traduccion')
    def test_texto_ingles_descartar_no_traduce(self, mock_llamar_traduccion, mock_parsear_triaje, 
                                              mock_llamar_triaje, mock_detectar_idioma, 
                                              mock_limpiar_texto, mock_cargar_modelo):
        """Prueba que un texto en inglés marcado como DESCARTAR no intenta traducción."""
        mock_nlp = MagicMock()
        mock_cargar_modelo.return_value = mock_nlp
        mock_limpiar_texto.return_value = self.texto_limpio_en
        mock_detectar_idioma.return_value = "en"
        mock_llamar_triaje.return_value = ("prompt_usado_mock", "respuesta_llm_cruda_mock")
        mock_parsear_triaje.return_value = self.evaluacion_triaje_descartar_mock
        
        resultado = ejecutar_fase_1(self.id_fragmento, self.texto_original)

        self.assertEqual(resultado.decision_triaje, "DESCARTAR")
        self.assertIsNotNone(resultado.texto_para_siguiente_fase)  # Debería tener texto incluso si se descarta
        mock_llamar_traduccion.assert_not_called()

if __name__ == '__main__':
    unittest.main()