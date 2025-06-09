"""
PipelineCoordinator: Orquestación del Pipeline con IDs Secuenciales
==================================================================

Este módulo implementa la coordinación completa del pipeline de procesamiento
aplicando nuestra solución arquitectónica de IDs secuenciales.

SOLUCIÓN IMPLEMENTADA:
- Coordinación entre todas las fases (1-4)
- Uso consistente de FragmentProcessor para IDs secuenciales
- Conversión final a formato de persistencia
- Manejo robusto de errores y fallbacks
"""

from typing import Optional, Dict, Any
from uuid import UUID
import uuid

# Importar sistema de logging
from ..utils.logging_config import get_logger, log_phase, LogContext

# Importar modelos
from ..models.entrada import FragmentoProcesableItem
from ..models.procesamiento import (
    ResultadoFase1Triaje,
    ResultadoFase2Extraccion,
    ResultadoFase3CitasDatos,
    ResultadoFase4Normalizacion
)
from ..models.persistencia import FragmentoPersistenciaPayload

# Importar funciones de fases
from ..pipeline.fase_1_triaje import ejecutar_fase_1
# from ..pipeline.fase_2_extraccion import ejecutar_fase_2
# from ..pipeline.fase_3_citas_datos import ejecutar_fase_3
# from ..pipeline.fase_4_normalizacion import ejecutar_fase_4

# Importar utilities
from ..utils.fragment_processor import FragmentProcessor
from ..services.payload_builder import PayloadBuilder


class PipelineCoordinator:
    """
    Orquesta la ejecución completa del pipeline con IDs secuenciales.
    
    Responsabilidades:
    1. Coordinar ejecución secuencial de fases 1-4
    2. Mantener consistencia de IDs secuenciales
    3. Gestionar estados de error y fallbacks
    4. Generar payload final para persistencia
    5. Logging y auditoria completa
    """
    
    def __init__(self):
        """Inicializa el coordinador del pipeline."""
        self.payload_builder = PayloadBuilder()
        self.base_logger = get_logger("PipelineCoordinator")
        self.base_logger.info("PipelineCoordinator inicializado")
    
    def ejecutar_pipeline_completo(
        self, 
        fragmento: FragmentoProcesableItem,
        modelo_spacy: str = "es_core_news_sm",
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta el pipeline completo para un fragmento.
        
        Args:
            fragmento: Fragmento a procesar
            modelo_spacy: Modelo spaCy para fase 1
            request_id: ID único de la request (se genera si no se proporciona)
            
        Returns:
            Dict con resultado completo incluyendo payload y metadatos
        """
        # Generar request_id si no se proporciona
        if not request_id:
            request_id = str(uuid.uuid4())
            
        fragmento_uuid = UUID(fragmento.id_fragmento)
        
        # Crear contexto de logging para este pipeline
        log_context = LogContext(
            request_id=request_id,
            component="PipelineCoordinator",
            fragment_id=str(fragmento_uuid),
            metadata={
                "articulo_id": fragmento.id_articulo_fuente,
                "orden": fragmento.orden_en_articulo
            }
        )
        
        logger = log_context.get_logger()
        logger.info(f"Iniciando pipeline completo para fragmento {fragmento_uuid}")
        
        resultado = {
            "request_id": request_id,
            "fragmento_id": str(fragmento_uuid),
            "exito": False,
            "fase_completada": 0,
            "payload": None,
            "resultados_fases": {},
            "errores": [],
            "metadatos": {}
        }
        
        try:
            # === FASE 1: TRIAJE ===
            with log_phase("Fase1_Triaje", request_id, fragment_id=str(fragmento_uuid)) as phase_logger:
                phase_logger.info("Ejecutando análisis de relevancia y filtrado")
                
                resultado_fase1 = ejecutar_fase_1(
                    id_fragmento_original=fragmento_uuid,
                    texto_original_fragmento=fragmento.texto_original,
                    modelo_spacy_nombre=modelo_spacy
                )
                
                phase_logger.info(
                    "Triaje completado",
                    es_relevante=resultado_fase1.es_relevante,
                    justificacion=resultado_fase1.justificacion_relevancia[:50] + "..." if resultado_fase1.justificacion_relevancia else None
                )
            
            resultado["resultados_fases"]["fase_1"] = resultado_fase1
            resultado["fase_completada"] = 1
            
            # Verificar si el fragmento es relevante
            if not resultado_fase1.es_relevante:
                logger.info(
                    f"Fragmento marcado como no relevante. Pipeline terminado.",
                    razon=resultado_fase1.justificacion_relevancia
                )
                resultado["exito"] = True
                resultado["payload"] = self._crear_payload_no_relevante(fragmento, resultado_fase1)
                return resultado
            
            # === INICIALIZAR FRAGMENT PROCESSOR ===
            processor = FragmentProcessor(fragmento_uuid)
            logger.debug("FragmentProcessor inicializado")
            
            # === FASE 2: EXTRACCIÓN ===
            with log_phase("Fase2_Extraccion", request_id, fragment_id=str(fragmento_uuid)) as phase_logger:
                phase_logger.info("Iniciando extracción de elementos básicos")
                
                # TODO: Implementar cuando fase_2_extraccion esté lista
                # resultado_fase2 = ejecutar_fase_2(resultado_fase1, processor)
                resultado_fase2 = self._mock_fase_2(resultado_fase1, processor)
                
                phase_logger.info(
                    "Extracción completada",
                    hechos_extraidos=len(resultado_fase2.hechos_extraidos),
                    entidades_extraidas=len(resultado_fase2.entidades_extraidas)
                )
            
            resultado["resultados_fases"]["fase_2"] = resultado_fase2
            resultado["fase_completada"] = 2
            
            # === FASE 3: CITAS Y DATOS ===
            with log_phase("Fase3_CitasDatos", request_id, fragment_id=str(fragmento_uuid)) as phase_logger:
                phase_logger.info("Iniciando extracción de citas y datos cuantitativos")
                
                # TODO: Implementar cuando fase_3_citas_datos esté lista
                # resultado_fase3 = ejecutar_fase_3(resultado_fase2, processor)
                resultado_fase3 = self._mock_fase_3(resultado_fase2, processor)
                
                phase_logger.info(
                    "Extracción de citas/datos completada",
                    citas_extraidas=len(resultado_fase3.citas_textuales_extraidas),
                    datos_extraidos=len(resultado_fase3.datos_cuantitativos_extraidos)
                )
            
            resultado["resultados_fases"]["fase_3"] = resultado_fase3
            resultado["fase_completada"] = 3
            
            # === FASE 4: NORMALIZACIÓN ===
            with log_phase("Fase4_Normalizacion", request_id, fragment_id=str(fragmento_uuid)) as phase_logger:
                phase_logger.info("Iniciando normalización y vinculación de entidades")
                
                # TODO: Implementar cuando fase_4_normalizacion esté lista
                # resultado_fase4 = ejecutar_fase_4(resultado_fase3, processor)
                resultado_fase4 = self._mock_fase_4(resultado_fase3, processor)
                
                phase_logger.info(
                    "Normalización completada",
                    entidades_normalizadas=len(resultado_fase4.entidades_normalizadas),
                    estado=resultado_fase4.estado_general_normalizacion
                )
            
            resultado["resultados_fases"]["fase_4"] = resultado_fase4
            resultado["fase_completada"] = 4
            
            # === GENERAR PAYLOAD FINAL ===
            logger.info("Generando payload final para persistencia")
            payload = self._generar_payload_completo(
                fragmento=fragmento,
                resultado_fase1=resultado_fase1,
                resultado_fase2=resultado_fase2,
                resultado_fase3=resultado_fase3,
                resultado_fase4=resultado_fase4,
                processor=processor
            )
            
            resultado["payload"] = payload
            resultado["exito"] = True
            
            # Estadísticas del processor
            stats = processor.get_stats()
            resultado["metadatos"]["processor_stats"] = stats
            
            logger.info(
                "Pipeline completo exitoso",
                total_hechos=stats["total_hechos"],
                total_entidades=stats["total_entidades"],
                total_citas=stats["total_citas"],
                total_datos=stats["total_datos"]
            )
            
            # Log summary del processor con contexto de request
            processor_logger = get_logger("FragmentProcessor", request_id)
            processor.log_summary(processor_logger)
            
        except Exception as e:
            logger.error(
                f"Error en pipeline: {str(e)}",
                error_type=type(e).__name__,
                fase_alcanzada=resultado["fase_completada"]
            )
            resultado["errores"].append(str(e))
            resultado["exito"] = False
            
        return resultado
    
    def _crear_payload_no_relevante(
        self, 
        fragmento: FragmentoProcesableItem, 
        resultado_fase1: ResultadoFase1Triaje
    ) -> FragmentoPersistenciaPayload:
        """Crea payload para fragmentos no relevantes."""
        return self.payload_builder.construir_payload_fragmento(
            metadatos_fragmento_data={
                "indice_secuencial_fragmento": fragmento.orden_en_articulo or 0,
                "titulo_seccion_fragmento": None,
                "contenido_texto_original_fragmento": fragmento.texto_original,
                "num_pagina_inicio_fragmento": None,
                "num_pagina_fin_fragmento": None
            },
            resumen_generado_fragmento="Fragmento descartado por triaje como no relevante",
            estado_procesamiento_final_fragmento="descartado_no_relevante",
            fecha_procesamiento_pipeline_fragmento=resultado_fase1.fecha_actualizacion.isoformat()
        )
    
    def _generar_payload_completo(
        self,
        fragmento: FragmentoProcesableItem,
        resultado_fase1: ResultadoFase1Triaje,
        resultado_fase2: ResultadoFase2Extraccion,
        resultado_fase3: ResultadoFase3CitasDatos,
        resultado_fase4: ResultadoFase4Normalizacion,
        processor: FragmentProcessor
    ) -> FragmentoPersistenciaPayload:
        """Genera el payload completo para persistencia."""
        
        # Convertir hechos procesados a formato de persistencia
        hechos_data = []
        for hecho in resultado_fase2.hechos_extraidos:
            hechos_data.append({
                "id_temporal_hecho": str(hecho.id_hecho),  # int → str
                "descripcion_hecho": hecho.texto_original_del_hecho,
                "tipo_hecho": "evento",  # Mapear según sea necesario
                "relevancia_hecho": int(hecho.confianza_extraccion * 10),  # 0.0-1.0 → 1-10
                "detalle_complejo_hecho": hecho.metadata_hecho.model_dump() if hasattr(hecho.metadata_hecho, 'model_dump') else {},
                "entidades_del_hecho": [
                    {
                        "id_temporal_entidad": str(ent_id),
                        "nombre_entidad": f"Entidad_{ent_id}",  # Placeholder
                        "tipo_entidad": "MENCIONADA",
                        "rol_en_hecho": "relacionada"
                    } for ent_id in hecho.vinculado_a_entidades
                ]
            })
        
        # Convertir entidades procesadas
        entidades_data = []
        for entidad in resultado_fase2.entidades_extraidas:
            entidades_data.append({
                "id_temporal_entidad": str(entidad.id_entidad),  # int → str
                "nombre_entidad": entidad.texto_entidad,
                "tipo_entidad": entidad.tipo_entidad,
                "descripcion_entidad": f"Entidad extraída con relevancia {entidad.relevancia_entidad}",
                "relevancia_entidad_articulo": int(entidad.relevancia_entidad * 10),
                "metadata_entidad": entidad.metadata_entidad.model_dump() if hasattr(entidad.metadata_entidad, 'model_dump') else {}
            })
        
        # Convertir citas textuales
        citas_data = []
        for cita in resultado_fase3.citas_textuales_extraidas:
            citas_data.append({
                "id_temporal_cita": str(cita.id_cita),  # int → str
                "texto_cita": cita.texto_cita,
                "entidad_emisora_id_temporal": str(cita.id_entidad_citada) if cita.id_entidad_citada else None,
                "nombre_entidad_emisora": cita.persona_citada,
                "contexto_cita": cita.contexto_cita,
                "relevancia_cita": 5  # Default
            })
        
        # Convertir datos cuantitativos  
        datos_data = []
        for dato in resultado_fase3.datos_cuantitativos_extraidos:
            datos_data.append({
                "id_temporal_dato": str(dato.id_dato_cuantitativo),  # int → str
                "descripcion_dato": dato.descripcion_dato,
                "valor_dato": dato.valor_dato,
                "unidad_dato": dato.unidad_dato,
                "fecha_dato": dato.fecha_dato,
                "contexto_dato": f"Extraído del fragmento {fragmento.id_fragmento}",
                "relevancia_dato": 5  # Default
            })
        
        return self.payload_builder.construir_payload_fragmento(
            metadatos_fragmento_data={
                "indice_secuencial_fragmento": fragmento.orden_en_articulo or 0,
                "titulo_seccion_fragmento": None,
                "contenido_texto_original_fragmento": fragmento.texto_original,
                "num_pagina_inicio_fragmento": None,
                "num_pagina_fin_fragmento": None
            },
            resumen_generado_fragmento=resultado_fase2.resumen_extraccion or "Fragmento procesado exitosamente",
            estado_procesamiento_final_fragmento="completado_ok",
            fecha_procesamiento_pipeline_fragmento=resultado_fase4.fecha_actualizacion.isoformat(),
            hechos_extraidos_data=hechos_data,
            entidades_autonomas_data=entidades_data,
            citas_textuales_data=citas_data,
            datos_cuantitativos_data=datos_data
        )
    
    # === MÉTODOS MOCK PARA FASES AÚN NO IMPLEMENTADAS ===
    # TODO: Remover cuando las fases reales estén implementadas
    
    def _mock_fase_2(self, resultado_fase1: ResultadoFase1Triaje, processor: FragmentProcessor) -> ResultadoFase2Extraccion:
        """Mock de Fase 2 para testing del coordinador."""
        from datetime import datetime, timezone
        
        # Crear hechos mock con IDs secuenciales
        hechos_mock = []
        entidades_mock = []
        
        # Mock simple basado en texto
        if "anunció" in resultado_fase1.texto_para_siguiente_fase or "":
            from ..models.procesamiento import HechoProcesado, EntidadProcesada, MetadatosHecho, MetadatosEntidad
            
            # Mock hecho
            hecho_mock = HechoProcesado(
                id_hecho=processor.next_hecho_id("Anuncio mock"),
                texto_original_del_hecho="Mock: Se anunció algo importante",
                confianza_extraccion=0.8,
                id_fragmento_origen=resultado_fase1.id_fragmento,
                metadata_hecho=MetadatosHecho()
            )
            hechos_mock.append(hecho_mock)
            
            # Mock entidad
            entidad_mock = EntidadProcesada(
                id_entidad=processor.next_entidad_id("Entidad mock"),
                texto_entidad="Mock Entity",
                tipo_entidad="PERSONA",
                relevancia_entidad=0.7,
                id_fragmento_origen=resultado_fase1.id_fragmento,
                metadata_entidad=MetadatosEntidad()
            )
            entidades_mock.append(entidad_mock)
        
        return ResultadoFase2Extraccion(
            id_fragmento=resultado_fase1.id_fragmento,
            hechos_extraidos=hechos_mock,
            entidades_extraidas=entidades_mock,
            resumen_extraccion="Mock: Extracción completada"
        )
    
    def _mock_fase_3(self, resultado_fase2: ResultadoFase2Extraccion, processor: FragmentProcessor) -> ResultadoFase3CitasDatos:
        """Mock de Fase 3 para testing del coordinador."""
        citas_mock = []
        datos_mock = []
        
        if resultado_fase2.hechos_extraidos:
            from ..models.procesamiento import CitaTextual, DatosCuantitativos, MetadatosCita, MetadatosDato
            
            # Mock cita
            cita_mock = CitaTextual(
                id_cita=processor.next_cita_id("Cita mock"),
                texto_cita="Mock: Esta es una cita de ejemplo",
                id_fragmento_origen=resultado_fase2.id_fragmento,
                metadata_cita=MetadatosCita()
            )
            citas_mock.append(cita_mock)
            
            # Mock dato
            dato_mock = DatosCuantitativos(
                id_dato_cuantitativo=processor.next_dato_id("Dato mock"),
                descripcion_dato="Mock: Porcentaje de ejemplo",
                valor_dato=42.5,
                unidad_dato="porcentaje",
                id_fragmento_origen=resultado_fase2.id_fragmento,
                metadata_dato=MetadatosDato()
            )
            datos_mock.append(dato_mock)
        
        return ResultadoFase3CitasDatos(
            id_fragmento=resultado_fase2.id_fragmento,
            citas_textuales_extraidas=citas_mock,
            datos_cuantitativos_extraidos=datos_mock
        )
    
    def _mock_fase_4(self, resultado_fase3: ResultadoFase3CitasDatos, processor: FragmentProcessor) -> ResultadoFase4Normalizacion:
        """Mock de Fase 4 para testing del coordinador."""
        return ResultadoFase4Normalizacion(
            id_fragmento=resultado_fase3.id_fragmento,
            entidades_normalizadas=[],  # Mock vacío
            estado_general_normalizacion="Mock_Completo"
        )


# Factory function para conveniencia
def create_pipeline_coordinator() -> PipelineCoordinator:
    """Crea una instancia del coordinador del pipeline."""
    return PipelineCoordinator()


# Testing
if __name__ == "__main__":
    from uuid import uuid4
    
    # El sistema de logging ya está configurado mediante logging_config
    
    # Test básico
    coordinator = PipelineCoordinator()
    
    # Mock fragment
    fragmento_test = FragmentoProcesableItem(
        id_fragmento=str(uuid4()),
        texto_original="Pedro Sánchez anunció nuevas medidas económicas para España.",
        id_articulo_fuente="test_article",
        orden_en_articulo=1
    )
    
    print(f"\n--- Test Pipeline Coordinator ---")
    print(f"Fragmento test: {fragmento_test.id_fragmento}")
    
    # Ejecutar pipeline (usará mocks para fases 2-4)
    resultado = coordinator.ejecutar_pipeline_completo(fragmento_test)
    
    print(f"\nResultado:")
    print(f"  Éxito: {resultado['exito']}")
    print(f"  Fase completada: {resultado['fase_completada']}")
    print(f"  Errores: {resultado['errores']}")
    
    if resultado.get('metadatos', {}).get('processor_stats'):
        stats = resultado['metadatos']['processor_stats']
        print(f"  Stats Processor:")
        print(f"    Hechos: {stats['total_hechos']}")
        print(f"    Entidades: {stats['total_entidades']}")
        print(f"    Citas: {stats['total_citas']}")
        print(f"    Datos: {stats['total_datos']}")
