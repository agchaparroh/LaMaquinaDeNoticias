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

from typing import Optional, Dict, Any, List, Union
import uuid

# Importar sistema de logging
from ..utils.logging_config import get_logger, log_phase, LogContext

# Importar modelos
from ..models.entrada import FragmentoProcesableItem, ArticuloProcesableItem
from ..models.procesamiento import (
    ResultadoFase1Triaje,
    ResultadoFase2Extraccion,
    ResultadoFase3CitasDatos,
    ResultadoFase4Normalizacion,
    HechoProcesado,
    EntidadProcesada,
    DatosCuantitativos,
    CitaTextual
)
from ..models.simplificacion import ResultadoFase2Simplificacion
from ..models.persistencia import FragmentoPersistenciaPayload, ArticuloPersistenciaPayload

# Importar funciones de fases
from ..pipeline.fase_1_triaje import ejecutar_fase_1
from ..pipeline.fase_2_simplificacion import ejecutar_fase_2_simplificacion
from ..pipeline.fase_3_entidades import ejecutar_fase_3_entidades
from ..pipeline.fase_4_hechos import ejecutar_fase_4_hechos
from ..pipeline.fase_5_datos import ejecutar_fase_5_datos
from ..pipeline.fase_6_citas import ejecutar_fase_6_citas
from ..pipeline.fase_7_normalizacion import ejecutar_fase_7_completa

# Importar utilities
from ..utils.fragment_processor import FragmentProcessor
from ..services.payload_builder import PayloadBuilder
from ..services.consolidation_service import ConsolidationService
from ..services.chunking_service import ChunkingService
from ..config import get_spacy_model_name


class PipelineCoordinator:
    """
    Orquesta la ejecución completa del pipeline con 7 fases.
    
    Responsabilidades:
    1. Coordinar ejecución de 7 fases con flujo adaptativo
    2. Gestionar procesamiento de chunks en paralelo
    3. Consolidación cross-chunk cuando sea necesario
    4. Mantener consistencia de IDs secuenciales
    5. Gestionar estados de error y fallbacks
    6. Generar payload final para persistencia
    7. Logging y auditoria completa
    """
    
    def __init__(self):
        """Inicializa el coordinador del pipeline."""
        self.payload_builder = PayloadBuilder()
        self.consolidation_service = ConsolidationService()
        self.chunking_service = ChunkingService()
        self.base_logger = get_logger("PipelineCoordinator")
        self.base_logger.info("PipelineCoordinator inicializado con 7 fases")
    
    def ejecutar_pipeline_completo(
        self, 
        contenido: Union[FragmentoProcesableItem, ArticuloProcesableItem],
        modelo_spacy: Optional[str] = None,
        request_id: Optional[str] = None,
        groq_api_key: Optional[str] = None,
        contexto_articulo: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta el pipeline completo de 7 fases para un artículo o fragmento.
        
        Args:
            contenido: Artículo completo o fragmento a procesar
            modelo_spacy: Modelo spaCy para fase 1 (opcional, usa configuración)
            request_id: ID único de la request (se genera si no se proporciona)
            groq_api_key: API key de Groq para LLMs
            contexto_articulo: Contexto del artículo (titulo, fecha, fuente, etc)
            
        Returns:
            Dict con resultado completo incluyendo payload y metadatos
        """
        # Generar request_id si no se proporciona
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # === DETECCIÓN DE TIPO Y UNIFICACIÓN ===
        # Detectar tipo de contenido y extraer información común
        articulo_original = None  # Preservar el ArticuloProcesableItem original
        
        if isinstance(contenido, ArticuloProcesableItem):
            # Procesamiento de artículo completo
            articulo_original = contenido  # Preservar para uso posterior
            fragmento_id_str = contenido.id_articulo
            texto_original = contenido.contenido_texto
            id_articulo_fuente = contenido.id_articulo
            orden_en_articulo = 0  # Artículo completo
            
            # Obtener contexto del artículo si no se proporciona
            if contexto_articulo is None:
                contexto_articulo = contenido.get_processing_context()
            
            # Crear fragmento unificado para mantener compatibilidad con fases
            fragmento_unificado = FragmentoProcesableItem(
                id_fragmento=fragmento_id_str,
                texto_original=texto_original,
                id_articulo_fuente=id_articulo_fuente,
                orden_en_articulo=orden_en_articulo,
                metadata_adicional=contenido.metadata_adicional or {}
            )
            
            self.base_logger.info(f"Procesando artículo completo: {fragmento_id_str}")
            
        elif isinstance(contenido, FragmentoProcesableItem):
            # Procesamiento de fragmento (lógica actual)
            fragmento_unificado = contenido
            
            # Manejar tanto formato ART-{ID} como UUIDs legacy
            if contenido.id_fragmento.startswith("ART-"):
                # Formato de trazabilidad: mantener como string
                fragmento_id_str = contenido.id_fragmento
                self.base_logger.info(f"Procesando fragmento con ID de trazabilidad: {fragmento_id_str}")
            else:
                # Formato UUID legacy: validar y mantener como string
                try:
                    # Validar que sea un UUID válido
                    uuid.UUID(contenido.id_fragmento)
                    fragmento_id_str = contenido.id_fragmento
                    self.base_logger.info(f"Procesando fragmento con UUID legacy: {fragmento_id_str}")
                except ValueError:
                    self.base_logger.error(f"ID de fragmento inválido: {contenido.id_fragmento}")
                    raise ValueError(f"El ID del fragmento no es válido: {contenido.id_fragmento}")
                    
            # Extraer información para compatibilidad
            texto_original = contenido.texto_original
            id_articulo_fuente = contenido.id_articulo_fuente
            orden_en_articulo = contenido.orden_en_articulo
            
        else:
            raise ValueError(f"Tipo de contenido no soportado: {type(contenido)}. "
                           f"Debe ser ArticuloProcesableItem o FragmentoProcesableItem.")
        
        # Crear contexto de logging para este pipeline
        log_context = LogContext(
            request_id=request_id,
            component="PipelineCoordinator",
            fragment_id=fragmento_id_str,
            metadata={
                "articulo_id": id_articulo_fuente,
                "orden": orden_en_articulo,
                "content_type": type(contenido).__name__
            }
        )
        
        logger = log_context.get_logger()
        logger.info(f"Iniciando pipeline completo para {type(contenido).__name__}: {fragmento_id_str}")
        
        resultado = {
            "request_id": request_id,
            "fragmento_id": fragmento_id_str,
            "exito": False,
            "fase_completada": 0,
            "payload": None,
            "resultados_fases": {},
            "errores": [],
            "metadatos": {
                "tipo_contenido_original": type(contenido).__name__,
                "es_articulo_completo": isinstance(contenido, ArticuloProcesableItem),
                "articulo_id_fuente": id_articulo_fuente,
                "orden_en_articulo": orden_en_articulo,
                "articulo_original": articulo_original  # Preservar para uso posterior
            },
            "flujo_adaptativo": {
                "simplificacion_aplicada": False,
                "chunking_aplicado": False,
                "fase_5_ejecutada": False,
                "fase_6_ejecutada": False,
                "consolidacion_aplicada": False
            }
        }
        
        try:
            # === FASE 1: TRIAJE ===
            with log_phase("Fase1_Triaje", request_id, fragment_id=fragmento_id_str) as phase_logger:
                phase_logger.info("Ejecutando análisis de relevancia y filtrado")
                
                resultado_fase1 = ejecutar_fase_1(
                    id_fragmento_original=fragmento_id_str,  # Ahora pasamos string, no UUID
                    texto_original_fragmento=fragmento_unificado.texto_original,
                    modelo_spacy_nombre=modelo_spacy or get_spacy_model_name()
                )
                
                phase_logger.info(
                    "Triaje completado",
                    es_relevante=resultado_fase1.es_relevante,
                    justificacion=resultado_fase1.justificacion_triaje[:50] + "..." if resultado_fase1.justificacion_triaje else None
                )
            
            resultado["resultados_fases"]["fase_1"] = resultado_fase1
            resultado["fase_completada"] = 1
            
            # Verificar si el fragmento es relevante
            if not resultado_fase1.es_relevante:
                logger.info(
                    f"Fragmento marcado como no relevante. Pipeline terminado.",
                    razon=resultado_fase1.justificacion_triaje
                )
                resultado["exito"] = True
                resultado["payload"] = self._crear_payload_no_relevante(
                    fragmento_unificado, 
                    resultado_fase1,
                    es_articulo_completo=resultado["metadatos"]["es_articulo_completo"],
                    articulo_original=resultado["metadatos"].get("articulo_original")
                )
                return resultado
            
            # Analizar flujo adaptativo basado en análisis de Fase 1
            flujo_config = self._determinar_flujo_adaptativo(resultado_fase1)
            resultado["flujo_adaptativo"].update(flujo_config)
            
            # === INICIALIZAR FRAGMENT PROCESSOR ===
            processor = FragmentProcessor(fragmento_id_str)  # Ahora acepta string
            logger.debug("FragmentProcessor inicializado")
            
            # === DETERMINAR SI APLICAR CHUNKING ===
            chunks = []
            if flujo_config["chunking_aplicado"]:
                with log_phase("Chunking", request_id, fragment_id=fragmento_id_str) as phase_logger:
                    phase_logger.info("Aplicando chunking inteligente al texto")
                    chunks = self.chunking_service.dividir_en_chunks(
                        resultado_fase1.texto_para_siguiente_fase,
                        resultado_fase1.metadatos_specificos_triaje.analisis_contenido if resultado_fase1.metadatos_specificos_triaje else {}
                    )
                    phase_logger.info(f"Texto dividido en {len(chunks)} chunks")
                    resultado["metadatos"]["chunks_count"] = len(chunks)
            else:
                # Un solo chunk con todo el texto
                chunks = [resultado_fase1.texto_para_siguiente_fase]
            
            # === FASE 2: SIMPLIFICACIÓN (SI ES NECESARIA) ===
            resultados_simplificacion = []
            if flujo_config["simplificacion_aplicada"]:
                with log_phase("Fase2_Simplificacion", request_id, fragment_id=fragmento_id_str) as phase_logger:
                    phase_logger.info("Ejecutando simplificación de texto")
                    
                    for idx, chunk_texto in enumerate(chunks):
                        # Crear resultado temporal de triaje para cada chunk
                        resultado_triaje_chunk = ResultadoFase1Triaje(
                            id_fragmento=fragmento_id_str,  # Ahora acepta string
                            texto_para_siguiente_fase=chunk_texto,
                            es_relevante=True,
                            justificacion_triaje="Chunk de fragmento relevante",
                            metadatos_specificos_triaje=resultado_fase1.metadatos_specificos_triaje
                        )
                        
                        resultado_simplif = ejecutar_fase_2_simplificacion(
                            resultado_triaje_chunk,
                            fecha_articulo=contexto_articulo.get("fecha_publicacion") if contexto_articulo else None,
                            groq_api_key=groq_api_key
                        )
                        resultados_simplificacion.append(resultado_simplif)
                    
                    phase_logger.info(
                        "Simplificación completada",
                        chunks_simplificados=len(resultados_simplificacion)
                    )
                
                resultado["resultados_fases"]["fase_2"] = resultados_simplificacion
                resultado["fase_completada"] = 2
            else:
                # Si no hay simplificación, crear resultados mock
                for chunk_texto in chunks:
                    resultado_mock = ResultadoFase2Simplificacion(
                        id_fragmento=fragmento_id_str,  # Ahora acepta string
                        texto_simplificado=chunk_texto,
                        simplificacion_exitosa=True,
                        metadata_simplificacion={}
                    )
                    resultados_simplificacion.append(resultado_mock)
            
            # === FASES 3-6: EXTRACCIÓN POR CHUNKS ===
            # Procesamos cada chunk a través de las fases de extracción
            resultados_por_chunk = []
            
            for idx, resultado_simplif in enumerate(resultados_simplificacion):
                chunk_resultado = {
                    "chunk_idx": idx,
                    "entidades": [],
                    "hechos": [],
                    "datos": [],
                    "citas": []
                }
                
                # === FASE 3: EXTRACCIÓN DE ENTIDADES ===
                with log_phase(f"Fase3_Entidades_Chunk{idx}", request_id, fragment_id=fragmento_id_str) as phase_logger:
                    phase_logger.info(f"Extrayendo entidades del chunk {idx}")
                    
                    resultado_entidades = ejecutar_fase_3_entidades(
                        resultado_simplif,
                        contexto_articulo=contexto_articulo,
                        groq_api_key=groq_api_key
                    )
                    
                    if "entidades_extraidas" in resultado_entidades:
                        chunk_resultado["entidades"] = resultado_entidades["entidades_extraidas"]
                        phase_logger.info(f"Entidades extraídas: {len(chunk_resultado['entidades'])}")
                
                # === FASE 4: EXTRACCIÓN DE HECHOS ===
                with log_phase(f"Fase4_Hechos_Chunk{idx}", request_id, fragment_id=fragmento_id_str) as phase_logger:
                    phase_logger.info(f"Extrayendo hechos del chunk {idx}")
                    
                    resultado_hechos = ejecutar_fase_4_hechos(
                        resultado_simplif,
                        contexto_articulo=contexto_articulo,
                        groq_api_key=groq_api_key
                    )
                    
                    if "hechos_extraidos" in resultado_hechos:
                        chunk_resultado["hechos"] = resultado_hechos["hechos_extraidos"]
                        phase_logger.info(f"Hechos extraídos: {len(chunk_resultado['hechos'])}")
                
                # === FASE 5: EXTRACCIÓN DE DATOS (CONDICIONAL) ===
                if flujo_config["fase_5_ejecutada"]:
                    with log_phase(f"Fase5_Datos_Chunk{idx}", request_id, fragment_id=fragmento_id_str) as phase_logger:
                        phase_logger.info(f"Extrayendo datos cuantitativos del chunk {idx}")
                        
                        resultado_datos = ejecutar_fase_5_datos(
                            resultado_simplif,
                            chunk_resultado["hechos"],
                            chunk_resultado["entidades"],
                            contexto_articulo=contexto_articulo,
                            groq_api_key=groq_api_key
                        )
                        
                        if "datos_extraidos" in resultado_datos:
                            chunk_resultado["datos"] = resultado_datos["datos_extraidos"]
                            phase_logger.info(f"Datos extraídos: {len(chunk_resultado['datos'])}")
                
                # === FASE 6: EXTRACCIÓN DE CITAS (CONDICIONAL) ===
                if flujo_config["fase_6_ejecutada"]:
                    with log_phase(f"Fase6_Citas_Chunk{idx}", request_id, fragment_id=fragmento_id_str) as phase_logger:
                        phase_logger.info(f"Extrayendo citas del chunk {idx}")
                        
                        resultado_citas = ejecutar_fase_6_citas(
                            resultado_simplif,
                            chunk_resultado["hechos"],
                            chunk_resultado["entidades"],
                            contexto_articulo=contexto_articulo,
                            groq_api_key=groq_api_key
                        )
                        
                        if "citas_extraidas" in resultado_citas:
                            chunk_resultado["citas"] = resultado_citas["citas_extraidas"]
                            phase_logger.info(f"Citas extraídas: {len(chunk_resultado['citas'])}")
                
                resultados_por_chunk.append(chunk_resultado)
            
            resultado["fase_completada"] = 6
            
            # === CONSOLIDACIÓN CROSS-CHUNK (SI ES NECESARIA) ===
            if flujo_config["consolidacion_aplicada"] and len(resultados_por_chunk) > 1:
                with log_phase("Consolidacion_CrossChunk", request_id, fragment_id=fragmento_id_str) as phase_logger:
                    phase_logger.info("Aplicando consolidación cross-chunk")
                    
                    # Recopilar todos los elementos por tipo
                    todas_entidades = []
                    todos_hechos = []
                    todos_datos = []
                    todas_citas = []
                    
                    for chunk_res in resultados_por_chunk:
                        todas_entidades.extend(chunk_res["entidades"])
                        todos_hechos.extend(chunk_res["hechos"])
                        todos_datos.extend(chunk_res["datos"])
                        todas_citas.extend(chunk_res["citas"])
                    
                    # Aplicar consolidación
                    entidades_consolidadas = self.consolidation_service.consolidar_entidades(todas_entidades)
                    hechos_consolidados = self.consolidation_service.consolidar_hechos(todos_hechos)
                    datos_consolidados = self.consolidation_service.consolidar_datos(todos_datos)
                    citas_consolidadas = self.consolidation_service.consolidar_citas(todas_citas)
                    
                    phase_logger.info(
                        "Consolidación completada",
                        entidades_antes=len(todas_entidades),
                        entidades_despues=len(entidades_consolidadas),
                        hechos_antes=len(todos_hechos),
                        hechos_despues=len(hechos_consolidados)
                    )
            else:
                # Sin consolidación, usar todos los elementos
                entidades_consolidadas = [ent for chunk in resultados_por_chunk for ent in chunk["entidades"]]
                hechos_consolidados = [hecho for chunk in resultados_por_chunk for hecho in chunk["hechos"]]
                datos_consolidados = [dato for chunk in resultados_por_chunk for dato in chunk["datos"]]
                citas_consolidadas = [cita for chunk in resultados_por_chunk for cita in chunk["citas"]]
            
            # === FASE 7: NORMALIZACIÓN Y RELACIONES ===
            with log_phase("Fase7_Normalizacion_Relaciones", request_id, fragment_id=fragmento_id_str) as phase_logger:
                phase_logger.info("Iniciando normalización y detección de relaciones")
                
                # Obtener texto simplificado consolidado
                texto_simplificado_completo = " ".join([r.texto_simplificado for r in resultados_simplificacion])
                
                resultado_fase7 = ejecutar_fase_7_completa(
                    hechos=hechos_consolidados,
                    entidades=entidades_consolidadas,
                    datos=datos_consolidados,
                    citas=citas_consolidadas,
                    texto_simplificado=texto_simplificado_completo,
                    contexto_articulo=contexto_articulo or {},
                    groq_api_key=groq_api_key
                )
                
                phase_logger.info(
                    "Fase 7 completada",
                    entidades_normalizadas=len(resultado_fase7.entidades_normalizadas),
                    estado=resultado_fase7.estado_general_normalizacion,
                    relaciones_detectadas=resultado_fase7.metadata_normalizacion.get("relaciones_detectadas", {})
                )
            
            resultado["resultados_fases"]["fase_7"] = resultado_fase7
            resultado["fase_completada"] = 7
            
            # === GENERAR PAYLOAD FINAL ===
            logger.info("Generando payload final para persistencia")
            
            # Detectar si es artículo completo o fragmento
            articulo_original_preserved = resultado["metadatos"].get("articulo_original")
            es_articulo_completo = resultado["metadatos"].get("es_articulo_completo", False)
            
            logger.info(
                "Detección de tipo de contenido",
                articulo_original_presente=articulo_original_preserved is not None,
                es_articulo_completo=es_articulo_completo,
                tipo_articulo_original=type(articulo_original_preserved).__name__ if articulo_original_preserved else "None"
            )
            
            if articulo_original_preserved is not None and es_articulo_completo:
                logger.info("Generando payload para artículo completo")
                payload = self._generar_payload_articulo_completo(
                    articulo_original=articulo_original_preserved,
                    resultado_fase1=resultado_fase1,
                    resultados_simplificacion=resultados_simplificacion,
                    entidades=resultado_fase7.entidades_normalizadas,
                    hechos=hechos_consolidados,
                    datos=datos_consolidados,
                    citas=citas_consolidadas,
                    resultado_fase7=resultado_fase7,
                    processor=processor
                )
            else:
                logger.info("Generando payload para fragmento")
                payload = self._generar_payload_completo_7_fases(
                    fragmento=fragmento_unificado,
                    resultado_fase1=resultado_fase1,
                    resultados_simplificacion=resultados_simplificacion,
                    entidades=resultado_fase7.entidades_normalizadas,
                    hechos=hechos_consolidados,
                    datos=datos_consolidados,
                    citas=citas_consolidadas,
                    resultado_fase7=resultado_fase7,
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
            # Crear logger para error general del pipeline
            error_logger = get_logger("PipelineCoordinator", request_id)
            error_logger.error(
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
        resultado_fase1: ResultadoFase1Triaje,
        es_articulo_completo: bool = False,
        articulo_original: Optional[ArticuloProcesableItem] = None
    ) -> Union[FragmentoPersistenciaPayload, ArticuloPersistenciaPayload]:
        """Crea payload para contenido no relevante (artículos o fragmentos)."""
        
        # Si es un artículo completo, generar payload de artículo
        if es_articulo_completo and articulo_original is not None:
            from datetime import datetime, timezone
            
            # Crear resultado_procesamiento mínimo para artículo no relevante
            resultado_procesamiento = {
                "fecha_procesamiento_pipeline": datetime.now(timezone.utc).isoformat(),
                "estado_procesamiento_final_pipeline": "descartado_no_relevante",
                "resumen_generado_pipeline": "Artículo descartado por triaje como no relevante",
                "palabras_clave_generadas": [],
                "sentimiento_general_articulo": "neutral",  # Default para artículo no relevante
                "embedding_articulo_vector": None,
                "version_pipeline_aplicada": "1.0.0",
                "fecha_ingesta_sistema": articulo_original.fecha_recopilacion.isoformat() if articulo_original.fecha_recopilacion else datetime.now(timezone.utc).isoformat()
            }
            
            return self.payload_builder.construir_payload_articulo_from_model(
                articulo_model=articulo_original,
                resultado_procesamiento=resultado_procesamiento,
                hechos_extraidos=None,
                entidades_extraidas=None,
                citas_extraidas=None,
                datos_extraidos=None,
                relaciones_hechos=None,
                relaciones_entidades=None,
                contradicciones_detectadas=None
            )
        else:
            # Comportamiento original para fragmentos
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
    
    def _determinar_flujo_adaptativo(self, resultado_fase1: ResultadoFase1Triaje) -> Dict[str, bool]:
        """
        Determina qué fases ejecutar basándose en el análisis de Fase 1.
        
        Args:
            resultado_fase1: Resultado del triaje con análisis
            
        Returns:
            Configuración del flujo adaptativo
        """
        analisis = resultado_fase1.metadatos_specificos_triaje.analisis_contenido if resultado_fase1.metadatos_specificos_triaje else {}
        metricas = analisis
        
        # Determinar si necesita simplificación (basado en densidad de entidades)
        densidad_entidades = metricas.get("densidad_entidades", 0)
        simplificacion_necesaria = densidad_entidades > 10  # Más de 10 entidades por 100 tokens
        
        # Determinar si necesita chunking
        num_tokens = metricas.get("conteo_tokens", 0)
        chunking_necesario = num_tokens > 1000
        
        # Determinar si ejecutar Fase 5 (datos cuantitativos)
        numeros_detectados = metricas.get("conteo_datos", 0)
        fase_5_necesaria = numeros_detectados > 0
        
        # Determinar si ejecutar Fase 6 (citas)
        citas_potenciales = metricas.get("conteo_citas", 0)
        fase_6_necesaria = citas_potenciales > 0
        
        # Consolidación necesaria si hay chunking
        consolidacion_necesaria = chunking_necesario
        
        config = {
            "simplificacion_aplicada": simplificacion_necesaria,
            "chunking_aplicado": chunking_necesario,
            "fase_5_ejecutada": fase_5_necesaria,
            "fase_6_ejecutada": fase_6_necesaria,
            "consolidacion_aplicada": consolidacion_necesaria
        }
        
        self.base_logger.info(
            "Flujo adaptativo determinado",
            **config
        )
        
        return config
    
    def _construir_entidades_del_hecho(self, hecho: HechoProcesado, relaciones_hecho_entidad: List[Dict]) -> List[Dict]:
        """
        Construye la lista de entidades_del_hecho usando las relaciones detectadas por fase 7B.1.
        
        Args:
            hecho: El hecho procesado
            relaciones_hecho_entidad: Lista de relaciones hecho-entidad de fase 7B.1
            
        Returns:
            Lista de entidades del hecho con tipos de relación correctos
        """
        entidades_hecho = []
        
        # Buscar relaciones específicas para este hecho
        for relacion in relaciones_hecho_entidad:
            if relacion.get("hecho_id") == hecho.id_hecho:
                entidades_hecho.append({
                    "id_temporal": f"ENT-{relacion['entidad_id']}",
                    "tipo_relacion": relacion.get("tipo_relacion", "otro"),
                    "relevancia_en_hecho": relacion.get("relevancia_en_hecho", 5)
                })
        
        # Si no se encontraron relaciones específicas, usar fallback
        if not entidades_hecho:
            # Usar las entidades vinculadas originalmente pero con valores genéricos
            entidades_hecho = [
                {
                    "id_temporal": f"ENT-{ent_id}",
                    "tipo_relacion": "mencionado",  # Valor por defecto más apropiado
                    "relevancia_en_hecho": 5
                } for ent_id in hecho.vinculado_a_entidades
            ]
            
        return entidades_hecho
    
    def _generar_payload_completo_7_fases(
        self,
        fragmento: FragmentoProcesableItem,
        resultado_fase1: ResultadoFase1Triaje,
        resultados_simplificacion: List[ResultadoFase2Simplificacion],
        entidades: List[EntidadProcesada],
        hechos: List[HechoProcesado],
        datos: List[DatosCuantitativos],
        citas: List[CitaTextual],
        resultado_fase7: ResultadoFase4Normalizacion,
        processor: FragmentProcessor
    ) -> FragmentoPersistenciaPayload:
        """Genera el payload completo para persistencia con 7 fases."""
        
        # Convertir hechos procesados a formato de persistencia
        hechos_data = []
        for hecho in hechos:
            # Convertir fechas a formato ISO 8601 si existen
            fecha_inicio_iso = None
            fecha_fin_iso = None
            if hasattr(hecho.metadata_hecho, 'fecha_inicio') and hecho.metadata_hecho.fecha_inicio:
                fecha_inicio_iso = f"{hecho.metadata_hecho.fecha_inicio}T00:00:00Z"
            if hasattr(hecho.metadata_hecho, 'fecha_fin') and hecho.metadata_hecho.fecha_fin:
                fecha_fin_iso = f"{hecho.metadata_hecho.fecha_fin}T00:00:00Z"
            
            # PRP DEBUGGING: Verificar contenido antes del mapeo
            texto_hecho = getattr(hecho, 'texto_original_del_hecho', None)
            # Validación de texto del hecho
            if not texto_hecho or texto_hecho.strip() == "":
                self.base_logger.warning(f"Hecho {hecho.id_hecho} tiene texto vacío, omitiendo")
                continue  # SALTAR hechos vacíos
            
            hechos_data.append({
                "id_temporal": str(hecho.id_hecho),  # int → str
                "contenido": hecho.texto_original_del_hecho,
                "tipo_hecho": hecho.metadata_hecho.tipo_hecho if hasattr(hecho.metadata_hecho, 'tipo_hecho') else "SUCESO",
                "importancia": int(hecho.confianza_extraccion * 10),  # 0.0-1.0 → 1-10
                "fecha_ocurrencia_inicio": fecha_inicio_iso,
                "fecha_ocurrencia_fin": fecha_fin_iso,
                "precision_temporal": hecho.metadata_hecho.precision_temporal if hasattr(hecho.metadata_hecho, 'precision_temporal') else "desconocido",
                "metadata": {
                    "pais": hecho.metadata_hecho.pais if hasattr(hecho.metadata_hecho, 'pais') else [],
                    "region": hecho.metadata_hecho.region if hasattr(hecho.metadata_hecho, 'region') else [],
                    "ciudad": hecho.metadata_hecho.ciudad if hasattr(hecho.metadata_hecho, 'ciudad') else [],
                    "etiquetas": []  # TODO: Agregar lógica para extraer etiquetas
                },
                # Campos adicionales para lógica interna (no procesados por RPC pero útiles para HechoExtraidoItem)
                "es_evento_futuro": hecho.metadata_hecho.es_futuro if hasattr(hecho.metadata_hecho, 'es_futuro') else None,
                "estado_programacion": hecho.metadata_hecho.estado_programacion if hasattr(hecho.metadata_hecho, 'estado_programacion') else None,
                "detalle_complejo_hecho": hecho.metadata_hecho.model_dump() if hasattr(hecho.metadata_hecho, 'model_dump') else {},
                "entidades_del_hecho": self._construir_entidades_del_hecho(
                    hecho,
                    resultado_fase7.metadata_normalizacion.get("relaciones_completas", {})
                    .get("relaciones_estructurales", {})
                    .get("hecho_entidad", [])
                )
            })
        
        # Convertir entidades procesadas (ya normalizadas)
        entidades_data = []
        for entidad in entidades:
            entidades_data.append({
                "id": str(entidad.id_entidad),  # int → str
                "nombre": entidad.nombre_entidad_normalizada or entidad.texto_entidad,
                "tipo": entidad.tipo_entidad,
                "descripcion": f"Entidad extraída con relevancia {entidad.relevancia_entidad}",
                "relevancia": int(entidad.relevancia_entidad * 10),  # Cambio: relevancia_entidad_articulo → relevancia
                "metadata": {  # Cambio: metadata_entidad → metadata
                    **(entidad.metadata_entidad.model_dump() if hasattr(entidad.metadata_entidad, 'model_dump') else {}),
                    "uri_wikidata": entidad.uri_wikidata,
                    "id_entidad_normalizada": str(entidad.id_entidad_normalizada) if entidad.id_entidad_normalizada else None,
                    "similitud_normalizacion": entidad.similitud_normalizacion
                },
                # Campos adicionales para compatibilidad con procesamiento
                "id_entidad": entidad.id_entidad,
                "texto_entidad": entidad.texto_entidad,
                "tipo_entidad": entidad.tipo_entidad,
                "relevancia_entidad": entidad.relevancia_entidad,
                "metadata_entidad": entidad.metadata_entidad.model_dump() if hasattr(entidad.metadata_entidad, 'model_dump') else {}
            })
        
        # Convertir citas textuales
        citas_data = []
        for cita in citas:
            citas_data.append({
                "id_temporal_cita": str(cita.id_cita),  # int → str
                "cita": cita.texto_cita,  # ACTUALIZADO: texto_cita → cita
                "id_temporal_entidad_emisora": str(cita.id_entidad_citada) if cita.id_entidad_citada else None,
                "id_temporal_hecho_contexto": str(cita.metadata_cita.hecho_relacionado_id) if hasattr(cita.metadata_cita, 'hecho_relacionado_id') and cita.metadata_cita.hecho_relacionado_id else None,
                "fecha_cita": f"{cita.metadata_cita.fecha}T00:00:00Z" if hasattr(cita.metadata_cita, 'fecha') and cita.metadata_cita.fecha else None,
                "contexto": cita.contexto_cita,  # ACTUALIZADO: contexto_cita → contexto
                "relevancia": cita.metadata_cita.relevancia if hasattr(cita.metadata_cita, 'relevancia') else 3,  # ACTUALIZADO: relevancia_cita → relevancia, usar valor de metadata
                # Campo adicional para compatibilidad
                "nombre_entidad_emisora": cita.persona_citada
            })
        
        # Convertir datos cuantitativos  
        datos_data = []
        for dato in datos:
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
            resumen_generado_fragmento=resultado_fase7.resumen_normalizacion or "Fragmento procesado exitosamente con 7 fases",
            estado_procesamiento_final_fragmento="completado_ok",
            fecha_procesamiento_pipeline_fragmento=resultado_fase7.fecha_actualizacion.isoformat(),
            hechos_extraidos_data=hechos_data,
            entidades_autonomas_data=entidades_data,
            citas_textuales_data=citas_data,
            datos_cuantitativos_data=datos_data
        )
    
    def _generar_payload_articulo_completo(
        self,
        articulo_original: ArticuloProcesableItem,
        resultado_fase1: ResultadoFase1Triaje,
        resultados_simplificacion: List[ResultadoFase2Simplificacion],
        entidades: List[EntidadProcesada],
        hechos: List[HechoProcesado],
        datos: List[DatosCuantitativos],
        citas: List[CitaTextual],
        resultado_fase7: ResultadoFase4Normalizacion,
        processor: FragmentProcessor
    ) -> ArticuloPersistenciaPayload:
        """
        Genera el payload completo para persistencia de artículos completos.
        
        A diferencia del método para fragmentos, este preserva toda la metadata
        del artículo original y genera campos adicionales requeridos.
        """
        from datetime import datetime, timezone
        
        # Crear diccionario de resultado_procesamiento con campos requeridos
        resultado_procesamiento = {
            "fecha_procesamiento_pipeline": datetime.now(timezone.utc).isoformat(),
            "estado_procesamiento_final_pipeline": "completado_ok",
            "resumen_generado_pipeline": resultado_fase7.resumen_normalizacion or "Artículo procesado exitosamente con 7 fases",
            "palabras_clave_generadas": [],  # Se pueden extraer de las entidades
            "sentimiento_general_articulo": "neutral",  # Default para artículo procesado
            "embedding_articulo_vector": None,  # Placeholder para embeddings futuros
            "version_pipeline_aplicada": "1.0.0",
            "fecha_ingesta_sistema": articulo_original.fecha_recopilacion.isoformat() if articulo_original.fecha_recopilacion else datetime.now(timezone.utc).isoformat()
        }
        
        # Extraer palabras clave de las entidades más relevantes
        palabras_clave = []
        for entidad in sorted(entidades, key=lambda e: e.relevancia_entidad, reverse=True)[:10]:
            if entidad.nombre_entidad_normalizada:
                palabras_clave.append(entidad.nombre_entidad_normalizada)
            else:
                palabras_clave.append(entidad.texto_entidad)
        resultado_procesamiento["palabras_clave_generadas"] = palabras_clave
        
        # PRIMERO: Extraer relaciones del resultado_fase7 antes de construir hechos_data
        relaciones_hechos_data = []
        relaciones_entidades_data = []
        contradicciones_data = []
        relaciones_hecho_entidad = {}  # Diccionario para mapear hecho_id -> lista de relaciones con entidades
        
        if resultado_fase7 and hasattr(resultado_fase7, 'metadata_normalizacion') and resultado_fase7.metadata_normalizacion:
            metadata = resultado_fase7.metadata_normalizacion
            
            # Obtener relaciones completas
            relaciones_completas = metadata.get("relaciones_completas", {})
            
            # Extraer relaciones estructurales (hecho-entidad y entidad-entidad)
            relaciones_estructurales = relaciones_completas.get("relaciones_estructurales", {})
            if relaciones_estructurales:
                # Procesar relaciones hecho-entidad PRIMERO para usarlas en la construcción de hechos
                for rel in relaciones_estructurales.get("hecho_entidad", []):
                    hecho_id = rel.get("hecho_id")
                    if hecho_id:
                        if hecho_id not in relaciones_hecho_entidad:
                            relaciones_hecho_entidad[hecho_id] = []
                        relaciones_hecho_entidad[hecho_id].append({
                            "entidad_id": rel.get("entidad_id"),
                            "tipo_relacion": rel.get("tipo_relacion", "otro"),
                            "relevancia_en_hecho": rel.get("relevancia_en_hecho", 5)
                        })
                
                # Procesar relaciones entidad-entidad
                for rel in relaciones_estructurales.get("entidad_relacion", []):
                    relaciones_entidades_data.append({
                        "id_entidad_origen": str(rel.get("entidad_origen_id", "")),
                        "id_entidad_destino": str(rel.get("entidad_destino_id", "")),
                        "tipo_relacion": rel.get("tipo_relacion", ""),
                        "descripcion": rel.get("descripcion", ""),
                        "fuerza_relacion": rel.get("fuerza_relacion", 5)
                    })
            
            # Extraer relaciones temporales (hecho-hecho y contradicciones)
            relaciones_temporales = relaciones_completas.get("relaciones_temporales", {})
            if relaciones_temporales:
                # Relaciones hecho-hecho
                for rel in relaciones_temporales.get("hecho_relacionado", []):
                    relaciones_hechos_data.append({
                        "id_hecho_origen": str(rel.get("hecho_origen_id", "")),
                        "id_hecho_destino": str(rel.get("hecho_destino_id", "")),
                        "tipo_relacion": self._mapear_tipo_relacion_hecho(rel.get("tipo_relacion", "")),
                        "descripcion_relacion": rel.get("descripcion_relacion", ""),
                        "fuerza_relacion": rel.get("fuerza_relacion", 5)
                    })
                
                # Contradicciones
                for cont in relaciones_temporales.get("contradicciones", []):
                    contradicciones_data.append({
                        "id_hecho_principal": str(cont.get("hecho_principal_id", "")),
                        "id_hecho_contradictorio": str(cont.get("hecho_contradictorio_id", "")),
                        "tipo_contradiccion": self._mapear_tipo_contradiccion(cont.get("tipo_contradiccion", "")),
                        "grado_contradiccion": cont.get("grado_contradiccion", 3),
                        "descripcion": cont.get("descripcion", "")
                    })
        
        # SEGUNDO: Convertir datos al formato esperado usando las relaciones extraídas
        hechos_data = []
        # Procesar hechos
        for hecho in hechos:
            fecha_inicio_iso = None
            fecha_fin_iso = None
            if hasattr(hecho.metadata_hecho, 'fecha_inicio') and hecho.metadata_hecho.fecha_inicio:
                fecha_inicio_iso = f"{hecho.metadata_hecho.fecha_inicio}T00:00:00Z"
            if hasattr(hecho.metadata_hecho, 'fecha_fin') and hecho.metadata_hecho.fecha_fin:
                fecha_fin_iso = f"{hecho.metadata_hecho.fecha_fin}T00:00:00Z"
            
            # PRP DEBUGGING: Verificar contenido antes del mapeo (FRAGMENTOS)
            texto_hecho = getattr(hecho, 'texto_original_del_hecho', None)
            # Validación de texto del hecho
            if not texto_hecho or texto_hecho.strip() == "":
                self.base_logger.warning(f"Hecho {hecho.id_hecho} tiene texto vacío, omitiendo")
                continue  # SALTAR hechos vacíos
            
            hechos_data.append({
                "id_temporal": str(hecho.id_hecho),
                "contenido": hecho.texto_original_del_hecho,
                "tipo_hecho": hecho.metadata_hecho.tipo_hecho if hasattr(hecho.metadata_hecho, 'tipo_hecho') else "SUCESO",
                "importancia": int(hecho.confianza_extraccion * 10),
                "fecha_ocurrencia_inicio": fecha_inicio_iso,
                "fecha_ocurrencia_fin": fecha_fin_iso,
                "precision_temporal": hecho.metadata_hecho.precision_temporal if hasattr(hecho.metadata_hecho, 'precision_temporal') else "desconocido",
                "metadata": {
                    "pais": hecho.metadata_hecho.pais if hasattr(hecho.metadata_hecho, 'pais') else [],
                    "region": hecho.metadata_hecho.region if hasattr(hecho.metadata_hecho, 'region') else [],
                    "ciudad": hecho.metadata_hecho.ciudad if hasattr(hecho.metadata_hecho, 'ciudad') else [],
                    "etiquetas": []  # TODO: Agregar lógica para extraer etiquetas
                },
                # Campos adicionales para lógica interna
                "es_evento_futuro": hecho.metadata_hecho.es_futuro if hasattr(hecho.metadata_hecho, 'es_futuro') else None,
                "estado_programacion": hecho.metadata_hecho.estado_programacion if hasattr(hecho.metadata_hecho, 'estado_programacion') else None,
                "detalle_complejo_hecho": hecho.metadata_hecho.model_dump() if hasattr(hecho.metadata_hecho, 'model_dump') else {},
                "entidades_del_hecho": []  # Se llenará después con las relaciones reales
            })
        
        entidades_data = []
        # Construir datos de entidades
        for idx, entidad in enumerate(entidades):
            entidad_dict = {
                "id": str(entidad.id_entidad),
                "nombre": entidad.nombre_entidad_normalizada or entidad.texto_entidad,
                "tipo": entidad.tipo_entidad,
                "descripcion": f"Entidad extraída con relevancia {entidad.relevancia_entidad}",
                "relevancia": int(entidad.relevancia_entidad * 10),  # Cambio: relevancia_entidad_articulo → relevancia
                "metadata": {  # Cambio: metadata_entidad → metadata
                    **(entidad.metadata_entidad.model_dump() if hasattr(entidad.metadata_entidad, 'model_dump') else {}),
                    "uri_wikidata": entidad.uri_wikidata,
                    "id_entidad_normalizada": str(entidad.id_entidad_normalizada) if entidad.id_entidad_normalizada else None,
                    "similitud_normalizacion": entidad.similitud_normalizacion
                },
                # Campos adicionales para compatibilidad con procesamiento
                "id_entidad": entidad.id_entidad,
                "texto_entidad": entidad.texto_entidad,
                "tipo_entidad": entidad.tipo_entidad,
                "relevancia_entidad": entidad.relevancia_entidad,
                "metadata_entidad": entidad.metadata_entidad.model_dump() if hasattr(entidad.metadata_entidad, 'model_dump') else {}
            }
            # Entidad procesada
            entidades_data.append(entidad_dict)
        
        # TERCERO: Poblar entidades_del_hecho usando las relaciones reales
        for hecho_dict in hechos_data:
            hecho_id = int(hecho_dict["id_temporal"])  # Convertir a int para comparar
            
            # Buscar relaciones hecho-entidad para este hecho
            if hecho_id in relaciones_hecho_entidad:
                for rel in relaciones_hecho_entidad[hecho_id]:
                    entidad_id = rel["entidad_id"]
                    
                    # Construir el item según el nuevo modelo EntidadEnHechoItem
                    hecho_dict["entidades_del_hecho"].append({
                        "id_temporal": str(entidad_id),  # Cambio: id_temporal_entidad → id_temporal
                        "tipo_relacion": rel["tipo_relacion"],
                        "relevancia_en_hecho": rel["relevancia_en_hecho"]
                    })
            
            # Si no hay relaciones detectadas, usar las de vinculado_a_entidades como fallback
            if not hecho_dict["entidades_del_hecho"]:
                # Buscar el hecho original
                hecho_original = next((h for h in hechos if str(h.id_hecho) == hecho_dict["id_temporal"]), None)
                if hecho_original and hasattr(hecho_original, 'vinculado_a_entidades'):
                    for ent_id in hecho_original.vinculado_a_entidades:
                        hecho_dict["entidades_del_hecho"].append({
                            "id_temporal": str(ent_id),
                            "tipo_relacion": "otro",  # Default
                            "relevancia_en_hecho": 5  # Default
                        })
        
        citas_data = []
        for cita in citas:
            citas_data.append({
                "id_temporal_cita": str(cita.id_cita),
                "cita": cita.texto_cita,  # ACTUALIZADO: texto_cita → cita
                "id_temporal_entidad_emisora": str(cita.id_entidad_citada) if cita.id_entidad_citada else None,
                "id_temporal_hecho_contexto": str(cita.metadata_cita.hecho_relacionado_id) if hasattr(cita.metadata_cita, 'hecho_relacionado_id') and cita.metadata_cita.hecho_relacionado_id else None,
                "fecha_cita": f"{cita.metadata_cita.fecha}T00:00:00Z" if hasattr(cita.metadata_cita, 'fecha') and cita.metadata_cita.fecha else None,
                "contexto": cita.contexto_cita,  # ACTUALIZADO: contexto_cita → contexto
                "relevancia": cita.metadata_cita.relevancia if hasattr(cita.metadata_cita, 'relevancia') else 3,  # ACTUALIZADO
                "nombre_entidad_emisora": cita.persona_citada
            })
        
        datos_data = []
        for dato in datos:
            # Obtener ID del hecho relacionado si existe
            id_temporal_hecho = "0"  # Default si no hay hecho relacionado
            # TODO: Implementar mapeo real cuando se tenga la relación dato-hecho
            
            datos_data.append({
                # Campos principales alineados con RPC
                "id_temporal_hecho": id_temporal_hecho,
                "indicador": dato.descripcion_dato,  # Cambio: descripcion_dato → indicador
                "categoria": dato.metadata_dato.categoria if hasattr(dato.metadata_dato, 'categoria') else "otro",
                "valor_numerico": dato.valor_dato,  # Cambio: valor_dato → valor_numerico
                "unidad": dato.unidad_dato,  # Cambio: unidad_dato → unidad
                "ambito_geografico": dato.metadata_dato.ambito_geografico if hasattr(dato.metadata_dato, 'ambito_geografico') else [],
                "periodo_referencia_inicio": dato.metadata_dato.periodo.inicio if hasattr(dato.metadata_dato, 'periodo') and dato.metadata_dato.periodo else None,
                "periodo_referencia_fin": dato.metadata_dato.periodo.fin if hasattr(dato.metadata_dato, 'periodo') and dato.metadata_dato.periodo else None,
                "tendencia": dato.metadata_dato.tendencia if hasattr(dato.metadata_dato, 'tendencia') else None,
                
                # Campos temporales
                "id_temporal_dato": str(dato.id_dato_cuantitativo),
                
                # Campos adicionales para compatibilidad con DatosCuantitativos
                "id_dato_cuantitativo": dato.id_dato_cuantitativo,
                "descripcion_dato": dato.descripcion_dato,
                "valor_dato": dato.valor_dato,
                "unidad_dato": dato.unidad_dato,
                "fecha_dato": dato.fecha_dato,
                "contexto_dato": f"Extraído del artículo {articulo_original.id_articulo}",
                "relevancia_dato": 5,  # Default
                
                # Campos adicionales no procesados por RPC pero disponibles
                "tipo_periodo": dato.metadata_dato.tipo_periodo if hasattr(dato.metadata_dato, 'tipo_periodo') else None,
                "valor_anterior": dato.metadata_dato.valor_anterior if hasattr(dato.metadata_dato, 'valor_anterior') else None,
                "variacion_absoluta": dato.metadata_dato.variacion_absoluta if hasattr(dato.metadata_dato, 'variacion_absoluta') else None,
                "variacion_porcentual": dato.metadata_dato.variacion_porcentual if hasattr(dato.metadata_dato, 'variacion_porcentual') else None
            })
        # Construir payload usando el builder
        return self.payload_builder.construir_payload_articulo_from_model(
            articulo_model=articulo_original,
            resultado_procesamiento=resultado_procesamiento,
            hechos_extraidos=hechos_data,
            entidades_extraidas=entidades_data,
            citas_extraidas=citas_data,
            datos_extraidos=datos_data,
            relaciones_hechos=relaciones_hechos_data,
            relaciones_entidades=relaciones_entidades_data,
            contradicciones_detectadas=contradicciones_data
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
    
    # === MÉTODOS DE COMPATIBILIDAD ===
    
    def ejecutar_pipeline_completo_fragmento(
        self, 
        fragmento: FragmentoProcesableItem,
        modelo_spacy: Optional[str] = None,
        request_id: Optional[str] = None,
        groq_api_key: Optional[str] = None,
        contexto_articulo: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Método de compatibilidad para procesamiento de fragmentos.
        
        Este método mantiene la interfaz anterior para código existente
        que específicamente procesa fragmentos.
        
        Args:
            fragmento: Fragmento a procesar
            modelo_spacy: Modelo spaCy para fase 1 (opcional)
            request_id: ID único de la request (opcional)
            groq_api_key: API key de Groq para LLMs
            contexto_articulo: Contexto del artículo (opcional)
            
        Returns:
            Dict con resultado completo incluyendo payload y metadatos
        """
        return self.ejecutar_pipeline_completo(
            contenido=fragmento,
            modelo_spacy=modelo_spacy,
            request_id=request_id,
            groq_api_key=groq_api_key,
            contexto_articulo=contexto_articulo
        )
    
    def ejecutar_pipeline_completo_articulo(
        self, 
        articulo: ArticuloProcesableItem,
        modelo_spacy: Optional[str] = None,
        request_id: Optional[str] = None,
        groq_api_key: Optional[str] = None,
        contexto_articulo: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Método específico para procesamiento de artículos completos.
        
        Args:
            articulo: Artículo completo a procesar
            modelo_spacy: Modelo spaCy para fase 1 (opcional)
            request_id: ID único de la request (opcional)
            groq_api_key: API key de Groq para LLMs
            contexto_articulo: Contexto del artículo (opcional, se obtiene del artículo)
            
        Returns:
            Dict con resultado completo incluyendo payload y metadatos
        """
        return self.ejecutar_pipeline_completo(
            contenido=articulo,
            modelo_spacy=modelo_spacy,
            request_id=request_id,
            groq_api_key=groq_api_key,
            contexto_articulo=contexto_articulo
        )
    
    def _mapear_tipo_relacion_hecho(self, tipo_original: str) -> str:
        """
        Mapea tipos de relación hecho-hecho del formato LLM al esperado por BD.
        """
        mapeo = {
            # Mapeos directos
            "causa": "causa",
            "consecuencia": "consecuencia",
            "contexto_historico": "contexto_historico",
            "respuesta_a": "respuesta_a",
            "version_alternativa": "version_alternativa",
            "seguimiento_de": "seguimiento_de",
            
            # Mapeos que requieren transformación
            "causa-efecto": "causa",
            "temporal_secuencial": "seguimiento_de",
            "aclaracion": "aclaracion_de",
            "aclaracion_de": "aclaracion_de"
        }
        return mapeo.get(tipo_original, tipo_original)
    
    def _mapear_tipo_contradiccion(self, tipo_original: str) -> str:
        """
        Mapea tipos de contradicción del formato LLM al esperado por BD.
        """
        mapeo = {
            # Mapeos directos
            "fecha": "fecha",
            "contenido": "contenido",
            "entidades": "entidades",
            "ubicacion": "ubicacion",
            "valor": "valor",
            "completa": "completa",
            
            # Mapeos que requieren transformación
            "temporal": "fecha",
            "logica": "contenido",
            "factual": "valor"
        }
        return mapeo.get(tipo_original, "contenido")  # Default a contenido


# Factory function para conveniencia
def create_pipeline_coordinator() -> PipelineCoordinator:
    """Crea una instancia del coordinador del pipeline."""
    return PipelineCoordinator()


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
