from typing import Dict, Any, List, Optional, Set, TYPE_CHECKING
from loguru import logger
from pydantic import ValidationError # Asegurar que ValidationError esté importado
import hashlib
import json

if TYPE_CHECKING:
    from ..models.entrada import ArticuloProcesableItem

# Importar utilidades de validación
from ..utils.validation import (
    escape_html,
    validate_wikidata_uri,
    validate_numeric_value,
    validate_date_optional
)

# Importar los modelos Pydantic desde persistencia.py
from ..models.persistencia import (
    ArticuloPersistenciaPayload as PayloadCompletoArticulo,
    HechoExtraidoItem,
    EntidadAutonomaItem,
    CitaTextualExtraidaItem,
    DatoCuantitativoExtraidoItem,
    RelacionHechosItem,
    RelacionEntidadesItem,
    ContradiccionDetectadaItem,
    FragmentoPersistenciaPayload as PayloadCompletoFragmento
    # VinculacionExternaItem ha sido removido ya que el campo correspondiente espera List[Dict[str, Any]]
)

class PayloadBuilder:
    """
    Construye los payloads JSONB para las RPCs de Supabase
    a partir de los resultados del pipeline de procesamiento.
    """

    def __init__(self):
        self.logger = logger.bind(service="PayloadBuilder")
        self.logger.info("PayloadBuilder inicializado.")
    
    def _generar_checksum(self, data: Dict[str, Any]) -> str:
        """
        Genera un checksum MD5 de los datos críticos del payload.
        
        Args:
            data: Diccionario con los datos del payload
            
        Returns:
            str: Checksum MD5 en hexadecimal
        """
        # Serializar datos de manera determinística para checksum consistente
        json_str = json.dumps(data, sort_keys=True, ensure_ascii=True, default=str)
        return hashlib.md5(json_str.encode('utf-8')).hexdigest()
    
    def _log_detallado_errores(self, fase: str, errores: List[str]) -> None:
        """
        Registra errores de validación de manera detallada.
        
        Args:
            fase: Fase de validación donde ocurrieron los errores
            errores: Lista de mensajes de error
        """
        self.logger.error(f"Errores de validación en {fase}:")
        for i, error in enumerate(errores, 1):
            self.logger.error(f"  {i}. {error}")
    
    def _recolectar_ids_temporales(self, data: Dict[str, Any]) -> Dict[str, Set[str]]:
        """
        Recolecta todos los IDs temporales definidos en el payload.
        
        Args:
            data: Diccionario con los datos del payload
            
        Returns:
            Dict con sets de IDs temporales por tipo
        """
        ids = {
            'hechos': set(),
            'entidades': set(),
            'citas': set(),
            'datos': set()
        }
        
        # Recolectar IDs de hechos
        for hecho in data.get('hechos_extraidos', []):
            if 'id_temporal_hecho' in hecho:
                ids['hechos'].add(hecho['id_temporal_hecho'])
        
        # Recolectar IDs de entidades autónomas
        for entidad in data.get('entidades_autonomas', []):
            if 'id_temporal_entidad' in entidad:
                ids['entidades'].add(entidad['id_temporal_entidad'])
        
        # Recolectar IDs de entidades en hechos
        for hecho in data.get('hechos_extraidos', []):
            for entidad in hecho.get('entidades_del_hecho', []):
                if 'id_temporal_entidad' in entidad:
                    ids['entidades'].add(entidad['id_temporal_entidad'])
        
        # Recolectar IDs de citas
        for cita in data.get('citas_textuales_extraidas', []):
            if 'id_temporal_cita' in cita:
                ids['citas'].add(cita['id_temporal_cita'])
        
        # Recolectar IDs de datos cuantitativos
        for dato in data.get('datos_cuantitativos_extraidos', []):
            if 'id_temporal_dato' in dato:
                ids['datos'].add(dato['id_temporal_dato'])
        
        return ids
    
    def _validar_integridad_referencial(self, data: Dict[str, Any]) -> List[str]:
        """
        Valida que todos los IDs temporales referenciados existan.
        
        Args:
            data: Diccionario con los datos del payload
            
        Returns:
            Lista de errores encontrados
        """
        errores = []
        ids_existentes = self._recolectar_ids_temporales(data)
        
        # Validar referencias en relaciones de hechos
        for relacion in data.get('relaciones_hechos', []):
            origen_id = relacion.get('hecho_origen_id_temporal')
            destino_id = relacion.get('hecho_destino_id_temporal')
            
            if origen_id and origen_id not in ids_existentes['hechos']:
                errores.append(f"Relación hechos: ID origen '{origen_id}' no existe")
            if destino_id and destino_id not in ids_existentes['hechos']:
                errores.append(f"Relación hechos: ID destino '{destino_id}' no existe")
        
        # Validar referencias en relaciones de entidades
        for relacion in data.get('relaciones_entidades', []):
            origen_id = relacion.get('entidad_origen_id_temporal')
            destino_id = relacion.get('entidad_destino_id_temporal')
            
            if origen_id and origen_id not in ids_existentes['entidades']:
                errores.append(f"Relación entidades: ID origen '{origen_id}' no existe")
            if destino_id and destino_id not in ids_existentes['entidades']:
                errores.append(f"Relación entidades: ID destino '{destino_id}' no existe")
        
        # Validar referencias en contradicciones
        for contradiccion in data.get('contradicciones_detectadas', []):
            principal_id = contradiccion.get('hecho_principal_id_temporal')
            contradictorio_id = contradiccion.get('hecho_contradictorio_id_temporal')
            
            if principal_id and principal_id not in ids_existentes['hechos']:
                errores.append(f"Contradicción: ID principal '{principal_id}' no existe")
            if contradictorio_id and contradictorio_id not in ids_existentes['hechos']:
                errores.append(f"Contradicción: ID contradictorio '{contradictorio_id}' no existe")
        
        # Validar referencias en citas y datos cuantitativos
        for cita in data.get('citas_textuales_extraidas', []):
            hecho_id = cita.get('hecho_principal_relacionado_id_temporal')
            if hecho_id and hecho_id not in ids_existentes['hechos']:
                errores.append(f"Cita '{cita.get('id_temporal_cita', '?')}': hecho relacionado '{hecho_id}' no existe")
        
        for dato in data.get('datos_cuantitativos_extraidos', []):
            hecho_id = dato.get('hecho_principal_relacionado_id_temporal')
            if hecho_id and hecho_id not in ids_existentes['hechos']:
                errores.append(f"Dato cuantitativo '{dato.get('id_temporal_dato', '?')}': hecho relacionado '{hecho_id}' no existe")
        
        return errores
    
    def _validar_tipos_datos_db(self, data: Dict[str, Any], tipo_payload: str) -> List[str]:
        """
        Valida que los tipos de datos coincidan con el esquema de la base de datos.
        
        Args:
            data: Diccionario con los datos del payload
            tipo_payload: 'articulo' o 'fragmento'
            
        Returns:
            Lista de errores encontrados
        """
        errores = []
        
        # Validar campos de fecha
        campos_fecha = ['fecha_publicacion', 'fecha_procesamiento_pipeline', 'fecha_ingesta_sistema']
        if tipo_payload == 'fragmento':
            campos_fecha = ['fecha_procesamiento_pipeline_fragmento']
        
        for campo in campos_fecha:
            if campo in data and data[campo]:
                try:
                    validate_date_optional(data[campo])
                    # Si llegamos aquí, la fecha es válida
                except ValueError as e:
                    errores.append(f"Campo '{campo}': {str(e)}")
        
        # Validar arrays
        campos_array = ['etiquetas_fuente', 'categorias_asignadas_ia', 'palabras_clave_ia']
        for campo in campos_array:
            if campo in data and data[campo] is not None:
                if not isinstance(data[campo], list):
                    errores.append(f"Campo '{campo}' debe ser un array, recibido: {type(data[campo]).__name__}")
                elif not all(isinstance(item, str) for item in data[campo]):
                    errores.append(f"Campo '{campo}' debe contener solo strings")
        
        # Validar embeddings (vectors)
        if 'embedding_articulo_vector' in data and data['embedding_articulo_vector'] is not None:
            if not isinstance(data['embedding_articulo_vector'], list):
                errores.append(f"Campo 'embedding_articulo_vector' debe ser una lista de números")
            elif not all(isinstance(x, (int, float)) for x in data['embedding_articulo_vector']):
                errores.append(f"Campo 'embedding_articulo_vector' debe contener solo números")
        
        # Validar valores numéricos en listas
        for hecho in data.get('hechos_extraidos', []):
            if 'relevancia_hecho' in hecho:
                try:
                    validate_numeric_value(hecho['relevancia_hecho'], 0, 10)
                    # Si llegamos aquí, el valor es válido
                except ValueError as e:
                    errores.append(f"Hecho '{hecho.get('id_temporal_hecho', '?')}' relevancia: {str(e)}")
        
        for dato in data.get('datos_cuantitativos_extraidos', []):
            if 'valor_dato' in dato and isinstance(dato['valor_dato'], (int, float)):
                # Validar que el valor numérico sea razonable
                if abs(dato['valor_dato']) > 1e15:
                    errores.append(f"Dato cuantitativo '{dato.get('id_temporal_dato', '?')}': valor numérico muy grande")
        
        # Validar URIs de Wikidata en entidades
        for entidad in data.get('entidades_autonomas', []):
            if 'wikidata_uri' in entidad.get('metadata_entidad', {}):
                uri = entidad['metadata_entidad']['wikidata_uri']
                try:
                    validate_wikidata_uri(uri)
                    # Si llegamos aquí, la URI es válida
                except ValueError as e:
                    errores.append(f"Entidad '{entidad.get('nombre_entidad', '?')}': {str(e)}")
        
        return errores
    
    def _validar_payload_completo(self, payload_data: Dict[str, Any], tipo_payload: str) -> None:
        """
        Valida el payload completo antes de enviarlo a Supabase.
        
        Args:
            payload_data: Diccionario con todos los datos del payload
            tipo_payload: 'articulo' o 'fragmento'
            
        Raises:
            ValueError: Si hay errores de validación
        """
        errores_totales = []
        
        # 1. Validar integridad referencial
        errores_ref = self._validar_integridad_referencial(payload_data)
        if errores_ref:
            errores_totales.extend(errores_ref)
            self._log_detallado_errores("integridad referencial", errores_ref)
        
        # 2. Validar tipos de datos contra esquema DB
        errores_tipos = self._validar_tipos_datos_db(payload_data, tipo_payload)
        if errores_tipos:
            errores_totales.extend(errores_tipos)
            self._log_detallado_errores("tipos de datos", errores_tipos)
        
        # 3. Generar y registrar checksum
        checksum = self._generar_checksum(payload_data)
        self.logger.info(f"Checksum del payload {tipo_payload}: {checksum}")
        
        # Si hay errores, lanzar excepción con detalles
        if errores_totales:
            mensaje = f"Validación fallida para payload {tipo_payload}: {len(errores_totales)} errores encontrados"
            raise ValueError(mensaje)

    def construir_payload_articulo_from_model(
        self,
        articulo_model: 'ArticuloProcesableItem',
        resultado_procesamiento: Dict[str, Any],
        hechos_extraidos: Optional[List[Dict[str, Any]]] = None,
        entidades_extraidas: Optional[List[Dict[str, Any]]] = None,
        citas_extraidas: Optional[List[Dict[str, Any]]] = None,
        datos_extraidos: Optional[List[Dict[str, Any]]] = None,
        relaciones_hechos: Optional[List[Dict[str, Any]]] = None,
        relaciones_entidades: Optional[List[Dict[str, Any]]] = None,
        contradicciones_detectadas: Optional[List[Dict[str, Any]]] = None
    ) -> PayloadCompletoArticulo:
        """
        Construye el payload completo para artículo usando ArticuloProcesableItem.
        
        Args:
            articulo_model: Modelo ArticuloProcesableItem con metadatos del artículo
            resultado_procesamiento: Diccionario con resultados del procesamiento
            hechos_extraidos: Lista de hechos extraídos
            entidades_extraidas: Lista de entidades extraídas
            citas_extraidas: Lista de citas extraídas
            datos_extraidos: Lista de datos cuantitativos extraídos
            relaciones_hechos: Lista de relaciones entre hechos
            relaciones_entidades: Lista de relaciones entre entidades
            contradicciones_detectadas: Lista de contradicciones detectadas
            
        Returns:
            PayloadCompletoArticulo listo para RPC insertar_articulo_completo
        """
        self.logger.debug(f"Construyendo payload para artículo desde modelo: {articulo_model.id_articulo}")
        self.logger.debug(f"=== DEBUG construir_payload_articulo_from_model: entidades_extraidas tiene {len(entidades_extraidas) if entidades_extraidas else 0} elementos ===")
        if entidades_extraidas:
            self.logger.debug(f"=== DEBUG construir_payload_articulo_from_model: Primera entidad: {entidades_extraidas[0]} ===")
        
        # Extraer metadatos del artículo desde el modelo
        metadatos_articulo = {
            "url": articulo_model.url,
            "storage_path": None,  # Se puede añadir si es necesario
            "fuente_original": None,  # ArticuloProcesableItem no tiene este campo
            "medio": articulo_model.medio,
            "medio_url_principal": None,  # ArticuloProcesableItem no tiene este campo
            "area_geografica": articulo_model.area_geografica,  # Corregido: era pais
            "tipo_medio": articulo_model.tipo_medio,
            "titular": articulo_model.titular,  # Corregido: era titulo
            "fecha_publicacion": articulo_model.fecha_publicacion.isoformat() if articulo_model.fecha_publicacion else None,
            "autor": articulo_model.autor,
            "idioma_original": articulo_model.idioma,
            "seccion": articulo_model.seccion,
            "etiquetas_fuente": articulo_model.etiquetas_fuente or [],
            "es_opinion": articulo_model.es_opinion,
            "es_oficial": articulo_model.es_oficial,
            "contenido_texto_original": articulo_model.contenido_texto,
            "contenido_html_original": None,  # ArticuloProcesableItem no tiene este campo
            "metadata_original": articulo_model.metadata_adicional or {}
        }
        
        # Usar el método existente con los datos extraídos
        return self.construir_payload_articulo(
            metadatos_articulo_data=metadatos_articulo,
            procesamiento_articulo_data=resultado_procesamiento,
            hechos_extraidos_data=hechos_extraidos,
            entidades_autonomas_data=entidades_extraidas,
            citas_textuales_data=citas_extraidas,
            datos_cuantitativos_data=datos_extraidos,
            relaciones_hechos_data=relaciones_hechos,
            relaciones_entidades_data=relaciones_entidades,
            contradicciones_detectadas_data=contradicciones_detectadas
        )

    def construir_payload_articulo(
        self,
        metadatos_articulo_data: Dict[str, Any],
        procesamiento_articulo_data: Dict[str, Any],
        vinculacion_externa_data: Optional[Dict[str, Any]] = None,
        hechos_extraidos_data: Optional[List[Dict[str, Any]]] = None,
        entidades_autonomas_data: Optional[List[Dict[str, Any]]] = None,
        citas_textuales_data: Optional[List[Dict[str, Any]]] = None,
        datos_cuantitativos_data: Optional[List[Dict[str, Any]]] = None,
        relaciones_hechos_data: Optional[List[Dict[str, Any]]] = None,
        relaciones_entidades_data: Optional[List[Dict[str, Any]]] = None,
        contradicciones_detectadas_data: Optional[List[Dict[str, Any]]] = None
    ) -> PayloadCompletoArticulo:
        """
        Construye el payload completo para la RPC insertar_articulo_completo.
        """
        self.logger.debug("Construyendo payload para artículo completo.")
        try:
            payload_data = {**metadatos_articulo_data, **procesamiento_articulo_data}
            
            # Preparar datos para validación (como diccionarios)
            payload_data_para_validacion = payload_data.copy()
            
            # Agregar listas opcionales como diccionarios para validación
            if hechos_extraidos_data is not None:
                payload_data_para_validacion["hechos_extraidos"] = hechos_extraidos_data
            else:
                payload_data_para_validacion["hechos_extraidos"] = []
            
            if entidades_autonomas_data is not None:
                payload_data_para_validacion["entidades_autonomas"] = entidades_autonomas_data
            else:
                payload_data_para_validacion["entidades_autonomas"] = []
            
            if citas_textuales_data is not None:
                payload_data_para_validacion["citas_textuales_extraidas"] = citas_textuales_data
            else:
                payload_data_para_validacion["citas_textuales_extraidas"] = []
            
            if datos_cuantitativos_data is not None:
                payload_data_para_validacion["datos_cuantitativos_extraidos"] = datos_cuantitativos_data
            else:
                payload_data_para_validacion["datos_cuantitativos_extraidos"] = []
            
            if relaciones_hechos_data is not None:
                payload_data_para_validacion["relaciones_hechos"] = relaciones_hechos_data
            else:
                payload_data_para_validacion["relaciones_hechos"] = []
            
            if relaciones_entidades_data is not None:
                payload_data_para_validacion["relaciones_entidades"] = relaciones_entidades_data
            else:
                payload_data_para_validacion["relaciones_entidades"] = []
            
            if contradicciones_detectadas_data is not None:
                payload_data_para_validacion["contradicciones_detectadas"] = contradicciones_detectadas_data
            else:
                payload_data_para_validacion["contradicciones_detectadas"] = []
            
            # Validar payload completo ANTES de crear objetos Pydantic
            self._validar_payload_completo(payload_data_para_validacion, 'articulo')

            # vinculacion_externa_articulo field has been removed from ArticuloPersistenciaPayload
            # No longer setting this field

            # Procesar listas opcionales
            if hechos_extraidos_data is not None:
                payload_data["hechos_extraidos"] = [HechoExtraidoItem(**item) for item in hechos_extraidos_data]
            else:
                payload_data["hechos_extraidos"] = [] # Asegurar que el campo exista como lista vacía

            if entidades_autonomas_data is not None:
                self.logger.debug(f"=== DEBUG PayloadBuilder: Procesando {len(entidades_autonomas_data)} entidades ===")
                if entidades_autonomas_data:
                    self.logger.debug(f"=== DEBUG PayloadBuilder: Primera entidad recibida: {entidades_autonomas_data[0]} ===")
                    self.logger.debug(f"=== DEBUG PayloadBuilder: Keys de primera entidad: {list(entidades_autonomas_data[0].keys())} ===")
                
                payload_data["entidades_autonomas"] = [EntidadAutonomaItem(**item) for item in entidades_autonomas_data]
            else:
                payload_data["entidades_autonomas"] = []

            if citas_textuales_data is not None:
                payload_data["citas_textuales_extraidas"] = [CitaTextualExtraidaItem(**item) for item in citas_textuales_data]
            else:
                payload_data["citas_textuales_extraidas"] = []

            if datos_cuantitativos_data is not None:
                payload_data["datos_cuantitativos_extraidos"] = [DatoCuantitativoExtraidoItem(**item) for item in datos_cuantitativos_data]
            else:
                payload_data["datos_cuantitativos_extraidos"] = []
            
            if relaciones_hechos_data is not None:
                payload_data["relaciones_hechos"] = [RelacionHechosItem(**item) for item in relaciones_hechos_data]
            else:
                payload_data["relaciones_hechos"] = []

            if relaciones_entidades_data is not None:
                payload_data["relaciones_entidades"] = [RelacionEntidadesItem(**item) for item in relaciones_entidades_data]
            else:
                payload_data["relaciones_entidades"] = []

            if contradicciones_detectadas_data is not None:
                payload_data["contradicciones_detectadas"] = [ContradiccionDetectadaItem(**item) for item in contradicciones_detectadas_data]
            else:
                payload_data["contradicciones_detectadas"] = []
                
            # Crear el payload Pydantic
            payload_completo = PayloadCompletoArticulo(**payload_data)
            self.logger.info("Payload para artículo completo construido y validado exitosamente.")
            return payload_completo
        except ValidationError as e:
            self.logger.error(f"Error de validación Pydantic en payload del artículo: {e.errors()}")
            # Aquí podrías querer formatear 'e.errors()' de una manera más específica o registrar 'e.json()'
            raise ValueError(f"Error de validación Pydantic en payload del artículo: {e.errors()}")
        except Exception as e:
            self.logger.error(f"Error inesperado al construir payload del artículo: {e}")
            raise

    def construir_payload_fragmento(
        self,
        metadatos_fragmento_data: Dict[str, Any],
        resumen_generado_fragmento: Optional[str],
        estado_procesamiento_final_fragmento: str,
        fecha_procesamiento_pipeline_fragmento: str, # Requerido
        hechos_extraidos_data: Optional[List[Dict[str, Any]]] = None,
        entidades_autonomas_data: Optional[List[Dict[str, Any]]] = None,
        citas_textuales_data: Optional[List[Dict[str, Any]]] = None,
        datos_cuantitativos_data: Optional[List[Dict[str, Any]]] = None,
        relaciones_hechos_data: Optional[List[Dict[str, Any]]] = None,
        relaciones_entidades_data: Optional[List[Dict[str, Any]]] = None,
        contradicciones_detectadas_data: Optional[List[Dict[str, Any]]] = None
    ) -> PayloadCompletoFragmento:
        """
        Construye el payload completo para la RPC insertar_fragmento_completo.
        """
        self.logger.debug("Construyendo payload para fragmento completo.")
        try:
            payload_data = {
                **metadatos_fragmento_data,
                "resumen_generado_fragmento": resumen_generado_fragmento,
                "estado_procesamiento_final_fragmento": estado_procesamiento_final_fragmento,
                "fecha_procesamiento_pipeline_fragmento": fecha_procesamiento_pipeline_fragmento
            }
            
            # PARCHE TEMPORAL: Asegurar que id_fragmento esté presente en el nivel raíz
            # para facilitar su extracción en supabase_service
            # TODO: Remover cuando se implemente el sistema de chunking completo
            if 'id_fragmento' not in payload_data and metadatos_fragmento_data:
                # Buscar id_fragmento en metadatos
                for key, value in metadatos_fragmento_data.items():
                    if key == 'id_fragmento':
                        payload_data['id_fragmento'] = value
                        self.logger.debug(f"id_fragmento agregado al nivel raíz: {value}")
                        break
            
            # Preparar datos para validación (como diccionarios)
            payload_data_para_validacion = payload_data.copy()
            
            # Agregar listas opcionales como diccionarios para validación
            if hechos_extraidos_data is not None:
                payload_data_para_validacion["hechos_extraidos"] = hechos_extraidos_data
            else:
                payload_data_para_validacion["hechos_extraidos"] = []
            
            if entidades_autonomas_data is not None:
                payload_data_para_validacion["entidades_autonomas"] = entidades_autonomas_data
            else:
                payload_data_para_validacion["entidades_autonomas"] = []
            
            if citas_textuales_data is not None:
                payload_data_para_validacion["citas_textuales_extraidas"] = citas_textuales_data
            else:
                payload_data_para_validacion["citas_textuales_extraidas"] = []
            
            if datos_cuantitativos_data is not None:
                payload_data_para_validacion["datos_cuantitativos_extraidos"] = datos_cuantitativos_data
            else:
                payload_data_para_validacion["datos_cuantitativos_extraidos"] = []
            
            if relaciones_hechos_data is not None:
                payload_data_para_validacion["relaciones_hechos"] = relaciones_hechos_data
            else:
                payload_data_para_validacion["relaciones_hechos"] = []
            
            if relaciones_entidades_data is not None:
                payload_data_para_validacion["relaciones_entidades"] = relaciones_entidades_data
            else:
                payload_data_para_validacion["relaciones_entidades"] = []
            
            if contradicciones_detectadas_data is not None:
                payload_data_para_validacion["contradicciones_detectadas"] = contradicciones_detectadas_data
            else:
                payload_data_para_validacion["contradicciones_detectadas"] = []
            
            # Validar payload completo ANTES de crear objetos Pydantic
            self._validar_payload_completo(payload_data_para_validacion, 'fragmento')

            # Procesar listas opcionales
            if hechos_extraidos_data is not None:
                payload_data["hechos_extraidos"] = [HechoExtraidoItem(**item) for item in hechos_extraidos_data]
            else:
                payload_data["hechos_extraidos"] = []

            if entidades_autonomas_data is not None:
                payload_data["entidades_autonomas"] = [EntidadAutonomaItem(**item) for item in entidades_autonomas_data]
            else:
                payload_data["entidades_autonomas"] = []

            if citas_textuales_data is not None:
                payload_data["citas_textuales_extraidas"] = [CitaTextualExtraidaItem(**item) for item in citas_textuales_data]
            else:
                payload_data["citas_textuales_extraidas"] = []

            if datos_cuantitativos_data is not None:
                payload_data["datos_cuantitativos_extraidos"] = [DatoCuantitativoExtraidoItem(**item) for item in datos_cuantitativos_data]
            else:
                payload_data["datos_cuantitativos_extraidos"] = []
            
            if relaciones_hechos_data is not None:
                payload_data["relaciones_hechos"] = [RelacionHechosItem(**item) for item in relaciones_hechos_data]
            else:
                payload_data["relaciones_hechos"] = []

            if relaciones_entidades_data is not None:
                payload_data["relaciones_entidades"] = [RelacionEntidadesItem(**item) for item in relaciones_entidades_data]
            else:
                payload_data["relaciones_entidades"] = []

            if contradicciones_detectadas_data is not None:
                payload_data["contradicciones_detectadas"] = [ContradiccionDetectadaItem(**item) for item in contradicciones_detectadas_data]
            else:
                payload_data["contradicciones_detectadas"] = []
            
            payload_completo = PayloadCompletoFragmento(**payload_data)
            self.logger.info("Payload para fragmento completo construido y validado exitosamente.")
            return payload_completo
        except ValidationError as e:
            self.logger.error(f"Error de validación Pydantic en payload del fragmento: {e.errors()}")
            raise ValueError(f"Error de validación Pydantic en payload del fragmento: {e.errors()}")
        except Exception as e:
            self.logger.error(f"Error inesperado al construir payload del fragmento: {e}")
            raise

# Bloque de prueba (opcional, para desarrollo rápido)
if __name__ == '__main__':
    builder = PayloadBuilder()

    # Datos mock para artículo
    mock_metadatos_articulo = {
        "url": "http://ejemplo.com/noticia",
        "titular": "Un Gran Descubrimiento Científico",
        "medio": "Revista Ciencia Hoy",
        "fecha_publicacion": "2024-01-15",
        "autor": "Dr. Investigador",
        "idioma_original": "es",
        "contenido_texto_original": "Contenido del artículo de prueba"
    }
    mock_procesamiento_articulo = {
        "resumen_generado_pipeline": "Un resumen conciso del descubrimiento.",
        "palabras_clave_generadas": ["ciencia", "descubrimiento", "importante"],
        "sentimiento_general_articulo": "positivo",
        "embedding_articulo_vector": [0.1, 0.2, 0.3],
        "estado_procesamiento_final_pipeline": "completado_ok",
        "fecha_procesamiento_pipeline": "2024-01-15T12:00:00Z",
        "fecha_ingesta_sistema": "2024-01-15T11:00:00Z",
        "version_pipeline_aplicada": "1.0.0"
    }
    mock_hechos = [{
        "id_temporal_hecho": "hecho_1",
        "descripcion_hecho": "Se observó un fenómeno nuevo.",
        "tipo_hecho": "observacion"
    }]

    try:
        payload_articulo = builder.construir_payload_articulo(
            metadatos_articulo_data=mock_metadatos_articulo,
            procesamiento_articulo_data=mock_procesamiento_articulo,
            hechos_extraidos_data=mock_hechos
        )
        logger.info(f"Payload Artículo Generado: {payload_articulo.model_dump_json(indent=2)}")
    except ValueError as e:
        logger.error(f"Error en prueba de payload artículo: {e}")

    # Datos mock para fragmento
    mock_metadatos_fragmento = {
        "indice_secuencial_fragmento": 1,
        "titulo_seccion_fragmento": "Introducción al Fenómeno",
        "contenido_texto_original_fragmento": "Este es el primer fragmento...",
        "num_pagina_inicio_fragmento": 1,
        "num_pagina_fin_fragmento": 1
    }
    
    try:
        payload_fragmento = builder.construir_payload_fragmento(
            metadatos_fragmento_data=mock_metadatos_fragmento,
            resumen_generado_fragmento="Resumen del primer fragmento.",
            fecha_procesamiento_pipeline_fragmento="2024-01-15T12:05:00Z",
            estado_procesamiento_final_fragmento="completado_ok"
        )
        logger.info(f"Payload Fragmento Generado: {payload_fragmento.model_dump_json(indent=2)}")
    except ValueError as e:
        logger.error(f"Error en prueba de payload fragmento: {e}")
