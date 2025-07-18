from typing import List, Optional, Tuple
from loguru import logger

# Importar SupabaseService para type hinting y posible instanciación
from .supabase_service import SupabaseService
# Importar excepciones personalizadas y decoradores
from ..utils.error_handling import (
    ValidationError, ProcessingError, SupabaseRPCError, ErrorPhase,
    retry_supabase_rpc, handle_normalization_error_fase4
)

class NormalizadorEntidades:
    """
    Servicio para normalizar entidades utilizando la función RPC buscar_entidad_similar
    del SupabaseService.
    """

    def __init__(self, supabase_service: SupabaseService):
        """
        Inicializa el NormalizadorEntidades.

        Args:
            supabase_service: Instancia del SupabaseService para interactuar con la DB.
        """
        self.supabase_service = supabase_service
        self.logger = logger.bind(service="NormalizadorEntidades")
        self.logger.info("NormalizadorEntidades inicializado.")

    @retry_supabase_rpc(connection_retries=1)  # Según documentación: 1 reintento para conexión
    def normalizar_entidad(
        self,
        nombre_entidad: str,
        tipo_entidad: Optional[str] = None,
        umbral_propio: Optional[float] = None,
        limite_resultados_propio: Optional[int] = 1
    ) -> Optional[dict]:
        """
        Normaliza una entidad dada utilizando el servicio Supabase.

        Args:
            nombre_entidad: El nombre de la entidad a normalizar.
            tipo_entidad: El tipo opcional de la entidad (PERSONA, ORGANIZACION, etc.).
            umbral_propio: Umbral de similitud específico para esta normalización.
                               Si es None, se usará un default interno (ej. 0.7).
            limite_resultados_propio: Límite de resultados para esta normalización.

        Returns:
            Un diccionario con la información de la entidad normalizada si se encuentra
            una coincidencia por encima del umbral, o datos indicando que es nueva.
            Ejemplo de retorno (entidad existente):
            {
                "id_entidad_normalizada": 123,
                "nombre_normalizado": "Nombre Canónico",
                "tipo_normalizado": "PERSONA",
                "score_similitud": 0.95,
                "es_nueva": False,
                "nombre_original": "Nombre Original",
                "tipo_original": "PERSONA"
            }
            Ejemplo de retorno (entidad nueva o no encontrada):
            {
                "nombre_original": "Nombre Nuevo",
                "tipo_original": "LUGAR",
                "es_nueva": True,
                "score_similitud": 0.0
            }
        """
        # Validación de entrada
        if not nombre_entidad or not nombre_entidad.strip():
            raise ValidationError(
                message="El nombre de la entidad no puede estar vacío",
                validation_errors=[{"field": "nombre_entidad", "error": "Empty or None"}],
                phase=ErrorPhase.FASE_4_NORMALIZACION
            )
        
        self.logger.debug(
            f"Intentando normalizar entidad: '{nombre_entidad}' (Tipo: {tipo_entidad})"
        )

        umbral_a_usar = umbral_propio if umbral_propio is not None else 0.7 # Default, ajustar si es necesario
        limite_a_usar = limite_resultados_propio if limite_resultados_propio is not None else 1

        try:
            resultados_similares: List[Tuple[int, str, str, float]] = self.supabase_service.buscar_entidad_similar(
                nombre=nombre_entidad,
                tipo_entidad=tipo_entidad,
                umbral_similitud=umbral_a_usar,
                limite_resultados=limite_a_usar
            )

            if resultados_similares:
                mejor_coincidencia = resultados_similares[0]
                id_norm, nombre_norm, tipo_norm, score_norm = mejor_coincidencia

                self.logger.info(
                    f"Entidad '{nombre_entidad}' normalizada a '{nombre_norm}' (ID: {id_norm}) "
                    f"con score {score_norm:.2f}."
                )
                return {
                    "id_entidad_normalizada": id_norm,
                    "nombre_normalizado": nombre_norm,
                    "tipo_normalizado": tipo_norm,
                    "score_similitud": score_norm,
                    "es_nueva": False,
                    "nombre_original": nombre_entidad,
                    "tipo_original": tipo_entidad # Guardar el tipo original también
                }
            else:
                self.logger.info(
                    f"No se encontró normalización para '{nombre_entidad}' (Tipo: {tipo_entidad}) "
                    f"con umbral {umbral_a_usar}. Considerada como nueva o por debajo del umbral."
                )
                return {
                    "nombre_original": nombre_entidad,
                    "tipo_original": tipo_entidad,
                    "es_nueva": True,
                    "score_similitud": 0.0
                }

        except (ConnectionError, TimeoutError) as e:
            # El decorador @retry_supabase_rpc manejará estos errores
            self.logger.error(
                f"Error de conexión durante la normalización de '{nombre_entidad}': {e}"
            )
            raise
        except SupabaseRPCError:
            # Ya es una excepción personalizada, re-lanzar
            raise
        except Exception as e:
            self.logger.error(
                f"Error inesperado durante la normalización de '{nombre_entidad}': {e}"
            )
            # Convertir a ProcessingError
            raise ProcessingError(
                message=f"Error al normalizar entidad '{nombre_entidad}': {str(e)}",
                phase=ErrorPhase.FASE_4_NORMALIZACION,
                processing_step="entity_normalization",
                fallback_used=False
            ) from e


if __name__ == '__main__':
    logger.add("normalizer_debug.log", rotation="5 MB", level="DEBUG")
    
    # Mock SupabaseService para pruebas locales
    class MockSupabaseService:
        def __init__(self):
            self.logger = logger.bind(service="MockSupabaseService")

        def buscar_entidad_similar(self, nombre: str, tipo_entidad: Optional[str] = None,
                                   umbral_similitud: float = 0.3, limite_resultados: int = 5):
            self.logger.info(f"[Mock] Buscando: '{nombre}', Tipo: {tipo_entidad}, Umbral: {umbral_similitud}, Limite: {limite_resultados}")
            if nombre.lower() == "juan pérez" and (tipo_entidad is None or tipo_entidad == "PERSONA"):
                if umbral_similitud <= 0.95:
                    return [(1, "Juan Pérez Oficial", "PERSONA", 0.95)]
            if nombre.lower() == "acme corp" and (tipo_entidad is None or tipo_entidad == "ORGANIZACION"):
                 if umbral_similitud <= 0.88:
                    return [(101, "ACME Corporation", "ORGANIZACION", 0.88)]
            if nombre.lower() == "madrid" and tipo_entidad == "LUGAR":
                 if umbral_similitud <= 0.99:
                    return [(202, "Madrid", "LUGAR", 0.99)]
            return []

    mock_service_instance = MockSupabaseService()
    normalizador = NormalizadorEntidades(supabase_service=mock_service_instance)

    # Pruebas
    test_cases = [
        ("Juan Pérez", "PERSONA", 0.7),
        ("ACME Corp", "ORGANIZACION", 0.7),
        ("Empresa Fantasma S.L.", "ORGANIZACION", 0.7),
        ("Madrid", "LUGAR", 0.9),
        ("Madrid", "PERSONA", 0.7), # No debería encontrar como persona
        ("Juan Pérez", "PERSONA", 0.96), # Debería ser nueva por umbral alto
    ]

    for nombre_test, tipo_test, umbral_test in test_cases:
        logger.info(f"\n--- Probando: '{nombre_test}', Tipo: {tipo_test}, Umbral: {umbral_test} ---")
        resultado = normalizador.normalizar_entidad(nombre_test, tipo_entidad=tipo_test, umbral_propio=umbral_test)
        logger.info(f"Resultado para '{nombre_test}': {resultado}")
