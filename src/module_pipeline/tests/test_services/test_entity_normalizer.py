import unittest
from unittest.mock import MagicMock, patch
from typing import List, Optional, Tuple

# Ajustar la ruta de importación según la estructura del proyecto
# Asumiendo que 'src' es parte de PYTHONPATH o se maneja la ruta relativa
from src.services.entity_normalizer import NormalizadorEntidades
from src.services.supabase_service import SupabaseService # Para type hinting del mock

class TestNormalizadorEntidades(unittest.TestCase):

    def setUp(self):
        """Configura el mock de SupabaseService antes de cada prueba."""
        self.mock_supabase_service = MagicMock(spec=SupabaseService)
        self.normalizador = NormalizadorEntidades(supabase_service=self.mock_supabase_service)

    def test_normalizar_entidad_existente_encontrada(self):
        """
        Prueba la normalización cuando se encuentra una entidad existente
        por encima del umbral.
        """
        nombre_entidad_test = "Apple Inc."
        tipo_entidad_test = "ORGANIZACION"
        umbral_test = 0.7
        
        mock_response: List[Tuple[int, str, str, float]] = [
            (101, "Apple Inc.", "ORGANIZACION", 0.95)
        ]
        self.mock_supabase_service.buscar_entidad_similar.return_value = mock_response

        resultado = self.normalizador.normalizar_entidad(
            nombre_entidad_test,
            tipo_entidad=tipo_entidad_test,
            umbral_propio=umbral_test
        )

        self.mock_supabase_service.buscar_entidad_similar.assert_called_once_with(
            nombre=nombre_entidad_test,
            tipo_entidad=tipo_entidad_test,
            umbral_similitud=umbral_test,
            limite_resultados=1 
        )
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado["id_entidad_normalizada"], 101)
        self.assertEqual(resultado["nombre_normalizado"], "Apple Inc.")
        self.assertEqual(resultado["tipo_normalizado"], "ORGANIZACION")
        self.assertEqual(resultado["score_similitud"], 0.95)
        self.assertFalse(resultado["es_nueva"])
        self.assertEqual(resultado["nombre_original"], nombre_entidad_test)
        self.assertEqual(resultado["tipo_original"], tipo_entidad_test)

    def test_normalizar_entidad_no_encontrada_por_umbral_bajo(self):
        """
        Prueba la normalización cuando la entidad existe pero su score
        está por debajo del umbral_propio especificado.
        """
        nombre_entidad_test = "Empresa X"
        tipo_entidad_test = "ORGANIZACION"
        umbral_test = 0.9 # Umbral alto
        
        mock_response: List[Tuple[int, str, str, float]] = [] 
        self.mock_supabase_service.buscar_entidad_similar.return_value = mock_response

        resultado = self.normalizador.normalizar_entidad(
            nombre_entidad_test,
            tipo_entidad=tipo_entidad_test,
            umbral_propio=umbral_test
        )

        self.mock_supabase_service.buscar_entidad_similar.assert_called_once_with(
            nombre=nombre_entidad_test,
            tipo_entidad=tipo_entidad_test,
            umbral_similitud=umbral_test,
            limite_resultados=1
        )
        self.assertIsNotNone(resultado)
        self.assertTrue(resultado["es_nueva"])
        self.assertEqual(resultado["nombre_original"], nombre_entidad_test)
        self.assertEqual(resultado["tipo_original"], tipo_entidad_test)
        self.assertEqual(resultado["score_similitud"], 0.0)

    def test_normalizar_entidad_completamente_nueva(self):
        """
        Prueba la normalización cuando no se encuentra ninguna entidad similar.
        """
        nombre_entidad_test = "Innovaciones Futuras LLC"
        tipo_entidad_test = "ORGANIZACION"
        umbral_test = 0.7
        
        mock_response: List[Tuple[int, str, str, float]] = []
        self.mock_supabase_service.buscar_entidad_similar.return_value = mock_response

        resultado = self.normalizador.normalizar_entidad(
            nombre_entidad_test,
            tipo_entidad=tipo_entidad_test,
            umbral_propio=umbral_test
        )

        self.mock_supabase_service.buscar_entidad_similar.assert_called_once_with(
            nombre=nombre_entidad_test,
            tipo_entidad=tipo_entidad_test,
            umbral_similitud=umbral_test,
            limite_resultados=1
        )
        self.assertIsNotNone(resultado)
        self.assertTrue(resultado["es_nueva"])
        self.assertEqual(resultado["nombre_original"], nombre_entidad_test)
        self.assertEqual(resultado["tipo_original"], tipo_entidad_test)

    def test_normalizar_entidad_sin_tipo_especifico(self):
        """
        Prueba la normalización cuando no se especifica tipo_entidad.
        """
        nombre_entidad_test = "Satya Nadella"
        umbral_test = 0.7
        
        mock_response: List[Tuple[int, str, str, float]] = [
            (202, "Satya Nadella", "PERSONA", 0.99)
        ]
        self.mock_supabase_service.buscar_entidad_similar.return_value = mock_response

        resultado = self.normalizador.normalizar_entidad(
            nombre_entidad_test,
            umbral_propio=umbral_test
        )

        self.mock_supabase_service.buscar_entidad_similar.assert_called_once_with(
            nombre=nombre_entidad_test,
            tipo_entidad=None,
            umbral_similitud=umbral_test,
            limite_resultados=1
        )
        self.assertIsNotNone(resultado)
        self.assertFalse(resultado["es_nueva"])
        self.assertEqual(resultado["id_entidad_normalizada"], 202)
        self.assertEqual(resultado["nombre_normalizado"], "Satya Nadella")
        self.assertEqual(resultado["tipo_normalizado"], "PERSONA")

    def test_normalizar_entidad_error_en_supabase(self):
        """
        Prueba el manejo de excepciones si SupabaseService falla.
        """
        nombre_entidad_test = "Entidad Problematica"
        
        self.mock_supabase_service.buscar_entidad_similar.side_effect = Exception("Fallo RPC")

        with self.assertRaises(Exception) as context:
            self.normalizador.normalizar_entidad(nombre_entidad_test)
        
        self.assertTrue("Fallo RPC" in str(context.exception))

    def test_normalizar_multiples_resultados_devuelve_el_primero(self):
        """
        Prueba que si buscar_entidad_similar devuelve múltiples resultados
        (aunque limite_resultados_propio=1 es el default), se usa el primero.
        """
        nombre_entidad_test = "Microsoft"
        umbral_test = 0.6
        
        mock_response: List[Tuple[int, str, str, float]] = [
            (301, "Microsoft Corporation", "ORGANIZACION", 0.98),
            (302, "Microsoft Research", "ORGANIZACION", 0.85),
        ]
        self.mock_supabase_service.buscar_entidad_similar.return_value = mock_response
        
        resultado = self.normalizador.normalizar_entidad(
            nombre_entidad_test,
            umbral_propio=umbral_test,
            limite_resultados_propio=1
        )

        self.mock_supabase_service.buscar_entidad_similar.assert_called_once_with(
            nombre=nombre_entidad_test,
            tipo_entidad=None,
            umbral_similitud=umbral_test,
            limite_resultados=1
        )
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado["id_entidad_normalizada"], 301)
        self.assertEqual(resultado["nombre_normalizado"], "Microsoft Corporation")

if __name__ == '__main__':
    unittest.main()
