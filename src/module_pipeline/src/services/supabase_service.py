"""
Servicio de integración con Supabase para Module Pipeline
=========================================================

Este módulo implementa el patrón Singleton para gestionar la conexión con Supabase
y proporciona métodos específicos para las RPCs del pipeline de procesamiento.

Basado en el patrón establecido en module_scraper, adaptado para las necesidades
específicas del pipeline de procesamiento de artículos y fragmentos.
"""

from typing import Optional, Dict, Any, List, Tuple, Union
from functools import lru_cache
import time
import json
from supabase import create_client, Client
from ..utils.logging_config import get_logger

# Configurar logger para este módulo
logger = get_logger("SupabaseService")
from pydantic import BaseModel

from ..utils.config import SUPABASE_URL, SUPABASE_KEY, MAX_RETRIES, MAX_WAIT_SECONDS
# Importar excepciones personalizadas y decoradores
from ..utils.error_handling import (
    ValidationError, SupabaseRPCError, ErrorPhase,
    retry_supabase_rpc
)


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
            # Usar loguru con contexto de servicio
            self.logger = logger.bind(service="SupabaseService")
            
            # Validar credenciales
            if not SUPABASE_URL or not SUPABASE_KEY:
                self.logger.error("SUPABASE_URL y SUPABASE_KEY deben estar configuradas")
                raise ValidationError(
                    message="Credenciales de Supabase no encontradas en la configuración",
                    validation_errors=[
                        {"field": "SUPABASE_URL", "error": "Missing or empty"},
                        {"field": "SUPABASE_KEY", "error": "Missing or empty"}
                    ],
                    phase=ErrorPhase.GENERAL
                )
            
            try:
                # Crear cliente con configuración optimizada
                self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
                
                # Inicializar caché de consultas para optimización
                self._query_cache = {}
                self._cache_ttl = 300  # 5 minutos TTL para consultas de normalización
                self._batch_operations = []
                self._last_batch_time = time.time()
                self._batch_interval = 1.0  # 1 segundo para batch operations
                
                self.logger.info("Cliente Supabase inicializado exitosamente con optimizaciones")
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
            raise SupabaseRPCError(
                message="Cliente Supabase no inicializado",
                rpc_name="get_client",
                phase=ErrorPhase.GENERAL,
                is_connection_error=True
            )
        return self.client

    def _validar_estructura_payload(self, payload: Union[Dict[str, Any], BaseModel], tipo: str) -> Dict[str, Any]:
        """
        Valida la estructura básica del payload antes de enviarlo a Supabase.
        Convierte objetos Pydantic a diccionarios si es necesario.
        
        Args:
            payload: Payload a validar (puede ser dict o Pydantic model)
            tipo: 'articulo' o 'fragmento'
            
        Returns:
            El payload como diccionario
            
        Raises:
            ValidationError: Si la estructura es inválida
        """
        # Verificar que payload no sea None
        if payload is None:
            raise ValidationError(
                message="Payload no puede ser None",
                phase=ErrorPhase.GENERAL
            )
            
        # Convertir Pydantic a dict si es necesario
        if isinstance(payload, BaseModel):
            payload_dict = payload.model_dump()
        elif isinstance(payload, dict):
            payload_dict = payload
        else:
            raise ValidationError(
                message=f"Payload debe ser un diccionario o modelo Pydantic, recibido: {type(payload).__name__}",
                phase=ErrorPhase.GENERAL
            )
        
        # El resto de la validación continúa igual pero usando payload_dict
        payload = payload_dict
        
        # Retornar el payload como diccionario para que pueda ser usado en las validaciones
        # posteriores
        
        # Validar campos requeridos según el tipo
        campos_requeridos = []
        if tipo == 'articulo':
            campos_requeridos = ['url', 'titular', 'contenido_texto_original', 
                               'fecha_procesamiento_pipeline', 'estado_procesamiento_final_pipeline']
        elif tipo == 'fragmento':
            campos_requeridos = ['indice_secuencial_fragmento', 'contenido_texto_original_fragmento',
                               'fecha_procesamiento_pipeline_fragmento', 'estado_procesamiento_final_fragmento']
        
        campos_faltantes = [campo for campo in campos_requeridos if campo not in payload]
        if campos_faltantes:
            raise ValidationError(
                message=f"Campos requeridos faltantes en payload {tipo}",
                validation_errors=[{"field": campo, "error": "Missing required field"} for campo in campos_faltantes],
                phase=ErrorPhase.GENERAL
            )
        
        # Validar que las listas estén presentes (pueden estar vacías)
        listas_esperadas = ['hechos_extraidos', 'entidades_autonomas', 'citas_textuales_extraidas',
                           'datos_cuantitativos_extraidos', 'relaciones_hechos', 'relaciones_entidades',
                           'contradicciones_detectadas']
        
        for lista in listas_esperadas:
            if lista in payload and not isinstance(payload[lista], list):
                raise ValidationError(
                    message=f"Campo '{lista}' debe ser una lista",
                    validation_errors=[{"field": lista, "error": f"Expected list, got {type(payload[lista]).__name__}"}],
                    phase=ErrorPhase.GENERAL
                )
        
        return payload
    
    def _validar_respuesta_insercion(self, payload: Dict[str, Any], respuesta: Dict[str, Any], tipo: str) -> None:
        """
        Valida la respuesta de la RPC para detectar inconsistencias.
        
        Args:
            payload: Payload enviado
            respuesta: Respuesta de la RPC
            tipo: 'articulo' o 'fragmento'
        """
        # Validar conteos de elementos insertados
        elementos_enviados = {
            'hechos': len(payload.get('hechos_extraidos', [])),
            'entidades': len(payload.get('entidades_autonomas', [])),
            'citas': len(payload.get('citas_textuales_extraidas', [])),
            'datos': len(payload.get('datos_cuantitativos_extraidos', [])),
            'relaciones': len(payload.get('relaciones_hechos', [])) + len(payload.get('relaciones_entidades', []))
        }
        
        elementos_insertados = {
            'hechos': respuesta.get('hechos_insertados', 0),
            'entidades': respuesta.get('entidades_insertadas', 0),
            'citas': respuesta.get('citas_insertadas', 0),
            'datos': respuesta.get('datos_insertados', 0),
            'relaciones': respuesta.get('relaciones_insertadas', 0)
        }
        
        # Detectar discrepancias
        for elemento, enviados in elementos_enviados.items():
            insertados = elementos_insertados.get(elemento, 0)
            if enviados != insertados:
                self.logger.warning(
                    f"Discrepancia en {elemento}: enviados={enviados}, insertados={insertados}"
                )
        
        # Registrar warnings de la RPC si existen
        if 'warnings' in respuesta and respuesta['warnings']:
            self.logger.warning(f"Warnings de la RPC {tipo}:")
            for warning in respuesta['warnings']:
                self.logger.warning(f"  - {warning}")
    
    @retry_supabase_rpc(connection_retries=1)  # Según documentación: 1 reintento para conexión
    def insertar_articulo_completo(self, payload: Union[Dict[str, Any], BaseModel]) -> Optional[Dict[str, Any]]:
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
            
            # Validar estructura del payload y convertir a dict si es necesario
            payload_dict = self._validar_estructura_payload(payload, 'articulo')
            
            # Llamar RPC
            response = self.client.rpc(
                'insertar_articulo_completo',
                {'datos_json': payload_dict}
            ).execute()
            
            if response.data:
                result = response.data
                if isinstance(result, list) and len(result) > 0:
                    result = result[0]
                
                # Validar respuesta de inserción
                self._validar_respuesta_insercion(payload_dict, result, 'articulo')
                
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

    @retry_supabase_rpc(connection_retries=1)
    def actualizar_articulo_procesado(self, payload: Union[Dict[str, Any], BaseModel]) -> Optional[Dict[str, Any]]:
        """
        Llama a la RPC actualizar_articulo_procesado para actualizar un artículo existente
        con los resultados del procesamiento del pipeline.
        
        Args:
            payload: Diccionario con los datos del procesamiento.
                    Debe incluir 'articulo_id' y/o 'url' para identificar el artículo.
            
        Returns:
            Dict con el resultado de la actualización o None si falla
            {
                "status": "exito",
                "articulo_id": int,
                "hechos_insertados": int,
                "entidades_insertadas": int,
                "citas_insertadas": int,
                "datos_insertados": int,
                "relaciones_insertadas": int
            }
            
        Raises:
            Exception: Si falla la llamada RPC después de los reintentos
        """
        try:
            self.logger.info("Llamando RPC actualizar_articulo_procesado")
            
            # Validar que tengamos al menos un identificador
            self.logger.info(f"DEBUG - Tipo de payload recibido: {type(payload)}")
            self.logger.info(f"DEBUG - payload es None: {payload is None}")
            payload_dict = self._validar_estructura_payload(payload, 'articulo')
            self.logger.info(f"DEBUG - Tipo de payload_dict después de validar: {type(payload_dict)}")
            self.logger.info(f"DEBUG - payload_dict es None después de validar: {payload_dict is None}")
            
            if not payload_dict.get('articulo_id') and not payload_dict.get('url'):
                raise ValueError("Se requiere articulo_id o url para actualizar el artículo")
            
            # Log de identificadores
            if payload_dict.get('articulo_id'):
                self.logger.info(f"Actualizando artículo por ID: {payload_dict['articulo_id']}")
            else:
                self.logger.info(f"Actualizando artículo por URL: {payload_dict['url'][:50]}...")
            
            # Debug: Log completo del payload (temporal en INFO para debug)
            self.logger.info(f"DEBUG - Payload completo antes de RPC: {json.dumps(payload_dict, default=str)[:500]}...")
            self.logger.info(f"DEBUG - Tipo de payload_dict: {type(payload_dict)}")
            self.logger.info(f"DEBUG - payload_dict es None: {payload_dict is None}")
            
            # Validación adicional antes de llamar RPC
            if payload_dict is None:
                self.logger.error("payload_dict es None antes de llamar RPC")
                raise ValueError("El payload no puede ser None")
            
            # FILTRAR CAMPOS NULL - eliminar TODOS los campos que sean null
            # Esto es más seguro que listar campos específicos
            campos_a_eliminar = []
            for campo, valor in payload_dict.items():
                if valor is None:
                    self.logger.info(f"Eliminando campo {campo} con valor null del payload")
                    campos_a_eliminar.append(campo)
            
            # Eliminar campos null después de iterar (para evitar modificar dict durante iteración)
            for campo in campos_a_eliminar:
                del payload_dict[campo]
            
            # NUEVA FUNCIÓN: Limpiar nulls en objetos anidados
            def limpiar_nulls_profundo(obj):
                """Elimina recursivamente todos los campos null de objetos y arrays"""
                if isinstance(obj, dict):
                    return {k: limpiar_nulls_profundo(v) for k, v in obj.items() if v is not None}
                elif isinstance(obj, list):
                    return [limpiar_nulls_profundo(item) for item in obj if item is not None]
                else:
                    return obj
            
            # Aplicar limpieza profunda
            payload_dict = limpiar_nulls_profundo(payload_dict)
            
            # LOG COMPLETO DEL PAYLOAD DESPUÉS DE LIMPIEZA PROFUNDA
            self.logger.info(f"DEBUG - Payload FINAL después de limpieza profunda: {json.dumps(payload_dict, default=str)}")
            
            # Construir el parámetro para la RPC
            rpc_params = {'datos_json': payload_dict}
            
            # Log del parámetro completo
            self.logger.info(f"Llamando RPC con parámetros: {json.dumps(rpc_params, default=str)[:200]}...")
            
            # Llamar RPC
            response = self.client.rpc(
                'actualizar_articulo_procesado',
                rpc_params
            ).execute()
            
            if response.data:
                result = response.data
                if isinstance(result, list) and len(result) > 0:
                    result = result[0]
                
                # Verificar estado
                if result.get('status') == 'error':
                    self.logger.error(
                        f"Error en RPC: {result.get('mensaje')}. "
                        f"Código: {result.get('codigo_sql')}"
                    )
                    return None
                
                # Log de éxito
                self.logger.info(
                    f"Artículo actualizado exitosamente. "
                    f"ID: {result.get('articulo_id')}, "
                    f"Hechos: {result.get('hechos_insertados', 0)}, "
                    f"Entidades: {result.get('entidades_insertadas', 0)}, "
                    f"Citas: {result.get('citas_insertadas', 0)}"
                )
                
                return result
            else:
                self.logger.warning("RPC actualizar_articulo_procesado no retornó datos")
                return None
                
        except Exception as e:
            self.logger.error(f"Error en actualizar_articulo_procesado: {e}")
            raise

    @retry_supabase_rpc(connection_retries=1)  # Según documentación: 1 reintento para conexión
    def insertar_fragmento_completo(self, payload: Union[Dict[str, Any], BaseModel]) -> Optional[Dict[str, Any]]:
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
            
            # Validar estructura del payload y convertir a dict si es necesario
            payload_dict = self._validar_estructura_payload(payload, 'fragmento')
            
            # PARCHE TEMPORAL: Extraer fragmento_id para usarlo también como documento_id
            # En el sistema actual, procesamos artículos completos donde:
            # 1 artículo = 1 documento = 1 fragmento (sin chunking real)
            # TODO: Cuando se implemente el sistema de chunking para documentos largos,
            # documento_id deberá venir del proceso de ingesta que divide el documento
            # en múltiples fragmentos. Por ahora, usamos el mismo ID para ambos.
            fragmento_id = None
            if isinstance(payload_dict, dict):
                # Buscar id_fragmento en diferentes posibles ubicaciones
                if 'id_fragmento' in payload_dict:
                    fragmento_id = payload_dict['id_fragmento']
                elif 'fragmento' in payload_dict and isinstance(payload_dict['fragmento'], dict):
                    fragmento_id = payload_dict['fragmento'].get('id_fragmento')
                    
            if not fragmento_id:
                self.logger.warning("No se encontró id_fragmento en el payload, usando valor por defecto")
                fragmento_id = "unknown-fragment-id"
            
            # IMPORTANTE: La función SQL espera documento_id y fragmento_id DENTRO del JSON
            # no como parámetros separados
            # PARCHE TEMPORAL: Usar IDs ficticios numéricos ya que la función espera BIGINT
            # TODO: Resolver el problema de IDs string vs BIGINT cuando se implemente
            # el sistema real de fragmentos/documentos
            payload_dict['documento_id'] = 999999  # ID ficticio para documento
            payload_dict['fragmento_id'] = 999999  # ID ficticio para fragmento
            
            # Llamar RPC con la estructura correcta (igual que insertar_articulo_completo)
            response = self.client.rpc(
                'insertar_fragmento_completo',
                {'datos_json': payload_dict}  # Envolver en objeto con clave 'datos_json'
            ).execute()
            
            # Log detallado de la respuesta para debugging
            self.logger.debug(f"Respuesta RPC insertar_fragmento_completo: {response}")
            self.logger.debug(f"Tipo de response.data: {type(response.data)}")
            self.logger.debug(f"Contenido de response.data: {response.data}")
            
            if response.data:
                result = response.data
                if isinstance(result, list) and len(result) > 0:
                    result = result[0]
                
                # Validar que result sea un diccionario con la estructura esperada
                if not isinstance(result, dict):
                    self.logger.error(f"Respuesta RPC no es un diccionario: {type(result)}")
                    return None
                
                # Validar campos mínimos esperados
                if 'fragmento_id' not in result:
                    self.logger.warning("Respuesta RPC no contiene 'fragmento_id'")
                    self.logger.warning(f"Campos en respuesta: {list(result.keys())}")
                    
                    # Log el contenido completo para debugging
                    if 'status' in result and result['status'] == 'error':
                        self.logger.error(f"RPC retornó error: {result.get('mensaje', 'Sin mensaje')}")
                        self.logger.error(f"Código SQL: {result.get('codigo_sql', 'Sin código')}")
                        return None
                
                # Validar respuesta de inserción
                self._validar_respuesta_insercion(payload_dict, result, 'fragmento')
                
                self.logger.info(
                    f"Fragmento insertado exitosamente. "
                    f"ID: {result.get('fragmento_id')}, "
                    f"Hechos: {result.get('hechos_insertados', 0)}, "
                    f"Entidades: {result.get('entidades_insertadas', 0)}"
                )
                return result
            else:
                self.logger.warning("RPC insertar_fragmento_completo no retornó datos")
                # Log adicional para entender por qué no hay datos
                self.logger.warning(f"response completo: {response}")
                self.logger.warning(f"response.data es None o vacío: {response.data}")
                
                # Verificar si hay un error en la respuesta
                if hasattr(response, 'error') and response.error:
                    self.logger.error(f"Error en respuesta RPC: {response.error}")
                
                return None
                
        except Exception as e:
            self.logger.error(f"Error en insertar_fragmento_completo: {e}")
            raise

    @retry_supabase_rpc(connection_retries=1)  # Según documentación: 1 reintento para conexión
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

    @retry_supabase_rpc(connection_retries=1)  # Un reintento para test de conexión
    def test_connection(self) -> bool:
        """
        Prueba la conexión con Supabase ejecutando una consulta simple.
        
        Returns:
            bool: True si la conexión es exitosa
            
        Raises:
            SupabaseRPCError: Si falla la conexión después de reintentos
        """
        try:
            # Intentar una consulta simple para verificar conectividad
            response = self.client.table('entidades').select('id').limit(1).execute()
            self.logger.info("Prueba de conexión con Supabase exitosa")
            return True
        except Exception as e:
            self.logger.error(f"Fallo en prueba de conexión con Supabase: {e}")
            # El decorador manejará la conversión a SupabaseRPCError
            raise
    
    def _get_cached_query(self, cache_key: str) -> Optional[Any]:
        """
        Obtiene resultado de consulta desde caché si está disponible y no ha expirado.
        
        Args:
            cache_key: Clave única para la consulta
            
        Returns:
            Resultado cacheado o None si no existe/expiró
        """
        if cache_key not in self._query_cache:
            return None
            
        cached_data, timestamp = self._query_cache[cache_key]
        if time.time() - timestamp > self._cache_ttl:
            # Expirado, eliminar del caché
            del self._query_cache[cache_key]
            return None
            
        return cached_data
    
    def _set_cached_query(self, cache_key: str, result: Any) -> None:
        """
        Guarda resultado de consulta en caché.
        
        Args:
            cache_key: Clave única para la consulta
            result: Resultado a cachear
        """
        self._query_cache[cache_key] = (result, time.time())
        
        # Limpiar caché antiguo para evitar crecimiento ilimitado
        if len(self._query_cache) > 1000:
            current_time = time.time()
            expired_keys = [
                key for key, (_, timestamp) in self._query_cache.items()
                if current_time - timestamp > self._cache_ttl
            ]
            for key in expired_keys:
                del self._query_cache[key]
    
    @lru_cache(maxsize=512)
    def buscar_entidad_similar_cached(
        self,
        nombre_entidad: str,
        tipo_entidad: str,
        umbral_similitud: float = 0.8
    ) -> Tuple[List[Tuple[str, str, str, float]], ...]:
        """
        Versión cacheada de búsqueda de entidades similares.
        Usa LRU cache para entidades consultadas frecuentemente.
        """
        try:
            # Crear cache key específico
            cache_key = f"entidad_similar:{nombre_entidad}:{tipo_entidad}:{umbral_similitud}"
            
            # Verificar caché local primero
            cached_result = self._get_cached_query(cache_key)
            if cached_result is not None:
                self.logger.debug(f"Cache hit para búsqueda de entidad: {nombre_entidad}")
                return tuple(cached_result)  # Convertir a tuple para LRU cache
            
            # Ejecutar consulta
            result = self.buscar_entidad_similar(nombre_entidad, tipo_entidad, umbral_similitud)
            
            # Guardar en caché
            self._set_cached_query(cache_key, result)
            
            return tuple(result)
            
        except Exception as e:
            self.logger.error(f"Error en búsqueda cacheada de entidad: {e}")
            # Fallback a método original
            return tuple(self.buscar_entidad_similar(nombre_entidad, tipo_entidad, umbral_similitud))
    
    def batch_normalize_entities(self, entidades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normaliza múltiples entidades en una sola operación batch optimizada.
        
        Args:
            entidades: Lista de entidades a normalizar
            
        Returns:
            Lista de entidades normalizadas
        """
        if not entidades:
            return []
        
        try:
            # Agrupar por tipo para optimizar consultas
            entidades_por_tipo = {}
            for i, entidad in enumerate(entidades):
                tipo = entidad.get('tipo', 'UNKNOWN')
                if tipo not in entidades_por_tipo:
                    entidades_por_tipo[tipo] = []
                entidades_por_tipo[tipo].append((i, entidad))
            
            resultados = [None] * len(entidades)
            
            # Procesar cada tipo en batch
            for tipo, entidades_tipo in entidades_por_tipo.items():
                nombres = [ent['nombre'] for _, ent in entidades_tipo]
                
                # Preparar payload batch para RPC
                batch_payload = {
                    'entidades_nombres': nombres,
                    'tipo': tipo,
                    'umbral_similitud': 0.8
                }
                
                # Llamar RPC batch (asumiendo que existe una RPC optimizada)
                try:
                    response = self.client.rpc('normalizar_entidades_batch', batch_payload).execute()
                    batch_results = response.data if response.data else []
                    
                    # Asignar resultados a posiciones originales
                    for (original_idx, entidad), resultado in zip(entidades_tipo, batch_results):
                        if resultado:
                            resultados[original_idx] = {
                                **entidad,
                                'id_entidad_normalizada': resultado.get('id_entidad'),
                                'nombre_entidad_normalizada': resultado.get('nombre_normalizado'),
                                'similitud_normalizacion': resultado.get('similitud', 0.0),
                                'uri_wikidata': resultado.get('uri_wikidata')
                            }
                        else:
                            resultados[original_idx] = entidad
                            
                except Exception as e:
                    self.logger.warning(f"Batch normalization falló para tipo {tipo}, usando método individual: {e}")
                    # Fallback a normalización individual
                    for original_idx, entidad in entidades_tipo:
                        try:
                            # Usar método cacheado individual
                            similares = self.buscar_entidad_similar_cached(
                                entidad['nombre'], 
                                tipo,
                                0.8
                            )
                            if similares:
                                mejor_match = similares[0]
                                resultados[original_idx] = {
                                    **entidad,
                                    'id_entidad_normalizada': mejor_match[0],
                                    'nombre_entidad_normalizada': mejor_match[1],
                                    'similitud_normalizacion': mejor_match[3]
                                }
                            else:
                                resultados[original_idx] = entidad
                        except Exception:
                            resultados[original_idx] = entidad
            
            return [r for r in resultados if r is not None]
            
        except Exception as e:
            self.logger.error(f"Error en normalización batch: {e}")
            # Fallback completo a procesamiento individual
            return [self._normalize_single_entity(ent) for ent in entidades]
    
    def _normalize_single_entity(self, entidad: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza una entidad individual con manejo de errores."""
        try:
            similares = self.buscar_entidad_similar_cached(
                entidad['nombre'],
                entidad.get('tipo', 'UNKNOWN'),
                0.8
            )
            if similares:
                mejor_match = similares[0]
                return {
                    **entidad,
                    'id_entidad_normalizada': mejor_match[0],
                    'nombre_entidad_normalizada': mejor_match[1],
                    'similitud_normalizacion': mejor_match[3]
                }
        except Exception:
            pass
        return entidad


# Instancia global del servicio (patrón Singleton)
import threading

_supabase_service: Optional[SupabaseService] = None
_supabase_service_lock = threading.Lock()


def get_supabase_service() -> SupabaseService:
    """
    Obtiene la instancia singleton del servicio Supabase.
    
    Implementa double-check locking para thread-safety durante
    la inicialización inicial.
    
    Returns:
        SupabaseService: Instancia única del servicio
    """
    global _supabase_service
    if _supabase_service is None:
        with _supabase_service_lock:
            # Double-check locking pattern para evitar race conditions
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
