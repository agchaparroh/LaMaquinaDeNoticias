"""
Servicio de integración con Supabase para Module Pipeline
=========================================================

Este módulo implementa el patrón Singleton para gestionar la conexión con Supabase
y proporciona métodos específicos para las RPCs del pipeline de procesamiento.

Basado en el patrón establecido en module_scraper, adaptado para las necesidades
específicas del pipeline de procesamiento de artículos y fragmentos.
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
from supabase import create_client, Client
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..utils.config import SUPABASE_URL, SUPABASE_KEY, MAX_RETRIES, MAX_WAIT_SECONDS


class SupabaseService:
    """
    Singleton para gestión de operaciones con Supabase.
    
    Proporciona métodos para:
    - Llamar RPCs específicas del pipeline
    - Manejar reintentos automáticos
    - Gestionar errores de manera consistente
    
    Attributes:
        client: Cliente Supabase inicializado
        logger: Logger configurado para el servicio
    """
    _instance: Optional['SupabaseService'] = None

    def __new__(cls, *args, **kwargs) -> 'SupabaseService':
        """Implementación del patrón Singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Inicializa el cliente de Supabase una sola vez.
        
        Raises:
            ValueError: Si las credenciales de Supabase no están configuradas
            Exception: Si falla la inicialización del cliente
        """
        if not hasattr(self, '_initialized'):
            self.logger = logging.getLogger(__name__)
            
            # Validar credenciales
            if not SUPABASE_URL or not SUPABASE_KEY:
                self.logger.error("SUPABASE_URL y SUPABASE_KEY deben estar configuradas")
                raise ValueError("Credenciales de Supabase no encontradas en la configuración")
            
            try:
                # Crear cliente
                self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
                self.logger.info("Cliente Supabase inicializado exitosamente")
            except Exception as e:
                self.logger.error(f"Error inicializando cliente Supabase: {e}")
                raise
            
            self._initialized = True

    def get_client(self) -> Client:
        """
        Retorna la instancia del cliente Supabase.
        
        Returns:
            Client: Cliente Supabase inicializado
            
        Raises:
            ConnectionError: Si el cliente no está inicializado
        """
        if not hasattr(self, 'client') or not self.client:
            self.logger.error("Cliente Supabase no está inicializado")
            raise ConnectionError("Cliente Supabase no inicializado")
        return self.client

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=MAX_WAIT_SECONDS),
        retry=retry_if_exception_type(Exception)
    )
    def insertar_articulo_completo(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Llama a la RPC insertar_articulo_completo para persistir un artículo procesado.
        
        Esta RPC maneja la inserción atómica de:
        - Información del artículo
        - Hechos extraídos
        - Entidades identificadas
        - Citas textuales
        - Datos cuantitativos
        - Relaciones entre elementos
        
        Args:
            payload: Diccionario JSONB con la estructura completa del artículo
                    según ArticuloPersistenciaPayload
        
        Returns:
            Dict con el resultado de la inserción o None si falla
            Estructura esperada:
            {
                "articulo_id": int,
                "hechos_insertados": int,
                "entidades_insertadas": int,
                "citas_insertadas": int,
                "datos_insertados": int,
                "relaciones_insertadas": int,
                "warnings": List[str]
            }
            
        Raises:
            Exception: Si falla la llamada RPC después de los reintentos
        """
        try:
            self.logger.info("Llamando RPC insertar_articulo_completo")
            
            # Llamar RPC
            response = self.client.rpc(
                'insertar_articulo_completo',
                {'datos_json': payload}
            ).execute()
            
            if response.data:
                result = response.data
                if isinstance(result, list) and len(result) > 0:
                    result = result[0]
                
                self.logger.info(
                    f"Artículo insertado exitosamente. "
                    f"ID: {result.get('articulo_id')}, "
                    f"Hechos: {result.get('hechos_insertados', 0)}, "
                    f"Entidades: {result.get('entidades_insertadas', 0)}"
                )
                return result
            else:
                self.logger.warning("RPC insertar_articulo_completo no retornó datos")
                return None
                
        except Exception as e:
            self.logger.error(f"Error en insertar_articulo_completo: {e}")
            raise

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=MAX_WAIT_SECONDS),
        retry=retry_if_exception_type(Exception)
    )
    def insertar_fragmento_completo(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Llama a la RPC insertar_fragmento_completo para persistir un fragmento procesado.
        
        Similar a insertar_articulo_completo pero para fragmentos de documentos extensos.
        
        Args:
            payload: Diccionario JSONB con la estructura completa del fragmento
                    según FragmentoPersistenciaPayload
        
        Returns:
            Dict con el resultado de la inserción o None si falla
            Estructura similar a insertar_articulo_completo pero con fragmento_id
            
        Raises:
            Exception: Si falla la llamada RPC después de los reintentos
        """
        try:
            self.logger.info("Llamando RPC insertar_fragmento_completo")
            
            # Llamar RPC
            response = self.client.rpc(
                'insertar_fragmento_completo',
                {'datos_json': payload}
            ).execute()
            
            if response.data:
                result = response.data
                if isinstance(result, list) and len(result) > 0:
                    result = result[0]
                
                self.logger.info(
                    f"Fragmento insertado exitosamente. "
                    f"ID: {result.get('fragmento_id')}, "
                    f"Hechos: {result.get('hechos_insertados', 0)}, "
                    f"Entidades: {result.get('entidades_insertadas', 0)}"
                )
                return result
            else:
                self.logger.warning("RPC insertar_fragmento_completo no retornó datos")
                return None
                
        except Exception as e:
            self.logger.error(f"Error en insertar_fragmento_completo: {e}")
            raise

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=MAX_WAIT_SECONDS),
        retry=retry_if_exception_type(Exception)
    )
    def buscar_entidad_similar(
        self, 
        nombre: str, 
        tipo_entidad: Optional[str] = None,
        umbral_similitud: float = 0.3,
        limite_resultados: int = 5
    ) -> List[Tuple[int, str, str, float]]:
        """
        Busca entidades similares en la base de datos usando la RPC buscar_entidad_similar.
        
        Utiliza búsqueda por similitud para encontrar entidades existentes que
        puedan corresponder a una entidad extraída del texto.
        
        Args:
            nombre: Nombre de la entidad a buscar
            tipo_entidad: Tipo de entidad (PERSONA, ORGANIZACION, LUGAR, etc.)
                         Si es None, busca en todos los tipos
            umbral_similitud: Umbral mínimo de similitud (0.0 a 1.0)
            limite_resultados: Número máximo de resultados a retornar
        
        Returns:
            Lista de tuplas (id, nombre, tipo, score) ordenadas por score descendente
            
        Raises:
            Exception: Si falla la llamada RPC después de los reintentos
        """
        try:
            self.logger.debug(
                f"Buscando entidad similar: '{nombre}', "
                f"tipo: {tipo_entidad}, umbral: {umbral_similitud}"
            )
            
            # Preparar parámetros
            params = {
                'nombre_busqueda': nombre,
                'umbral_similitud': umbral_similitud,
                'limite_resultados': limite_resultados
            }
            
            if tipo_entidad:
                params['tipo_entidad'] = tipo_entidad
            
            # Llamar RPC
            response = self.client.rpc('buscar_entidad_similar', params).execute()
            
            if response.data:
                results = []
                for row in response.data:
                    results.append((
                        row['id'],
                        row['nombre'],
                        row['tipo'],
                        row['score']
                    ))
                
                self.logger.debug(
                    f"Encontradas {len(results)} entidades similares para '{nombre}'"
                )
                return results
            else:
                self.logger.debug(f"No se encontraron entidades similares para '{nombre}'")
                return []
                
        except Exception as e:
            self.logger.error(f"Error en buscar_entidad_similar para '{nombre}': {e}")
            raise

    def test_connection(self) -> bool:
        """
        Prueba la conexión con Supabase ejecutando una consulta simple.
        
        Returns:
            bool: True si la conexión es exitosa, False en caso contrario
        """
        try:
            # Intentar una consulta simple para verificar conectividad
            response = self.client.table('entidades').select('id').limit(1).execute()
            self.logger.info("Prueba de conexión con Supabase exitosa")
            return True
        except Exception as e:
            self.logger.error(f"Fallo en prueba de conexión con Supabase: {e}")
            return False


# Instancia global del servicio (patrón Singleton)
_supabase_service: Optional[SupabaseService] = None


def get_supabase_service() -> SupabaseService:
    """
    Obtiene la instancia singleton del servicio Supabase.
    
    Returns:
        SupabaseService: Instancia única del servicio
    """
    global _supabase_service
    if _supabase_service is None:
        _supabase_service = SupabaseService()
    return _supabase_service


# Prueba del módulo si se ejecuta directamente
if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Probar inicialización
        service = get_supabase_service()
        print("✅ Servicio Supabase inicializado correctamente")
        
        # Probar conexión
        if service.test_connection():
            print("✅ Conexión con Supabase verificada")
        else:
            print("❌ Error en conexión con Supabase")
            
        # Probar búsqueda de entidad (ejemplo)
        print("\n🔍 Probando búsqueda de entidad similar...")
        resultados = service.buscar_entidad_similar(
            "Pedro Sanchez",  # Nombre con error intencional
            tipo_entidad="PERSONA",
            umbral_similitud=0.7
        )
        
        if resultados:
            print(f"Encontradas {len(resultados)} entidades similares:")
            for id_ent, nombre, tipo, score in resultados:
                print(f"  - {nombre} (ID: {id_ent}, Tipo: {tipo}, Score: {score:.2f})")
        else:
            print("No se encontraron entidades similares")
            
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
