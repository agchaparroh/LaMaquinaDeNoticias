from typing import Dict, Any, List, Optional
from loguru import logger
from pydantic import ValidationError # Asegurar que ValidationError esté importado

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

            # vinculacion_externa_articulo field has been removed from ArticuloPersistenciaPayload
            # No longer setting this field

            # Procesar listas opcionales
            if hechos_extraidos_data is not None:
                payload_data["hechos_extraidos"] = [HechoExtraidoItem(**item) for item in hechos_extraidos_data]
            else:
                payload_data["hechos_extraidos"] = [] # Asegurar que el campo exista como lista vacía

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
                
            # Crear el payload Pydantic
            payload_completo = PayloadCompletoArticulo(**payload_data)
            self.logger.info("Payload para artículo completo construido exitosamente.")
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
            self.logger.info("Payload para fragmento completo construido exitosamente.")
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
