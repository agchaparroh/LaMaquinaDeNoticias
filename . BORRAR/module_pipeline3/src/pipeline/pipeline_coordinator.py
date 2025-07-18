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

from typing import Optional, Dict, Any, List
import uuid

# Importar sistema de logging
from ..utils.logging_config import get_logger, log_phase, LogContext

# Importar modelos
from ..models.entrada import FragmentoProcesableItem
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
from ..models.persistencia import FragmentoPersistenciaPayload

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
        fragmento: FragmentoProcesableItem,
        modelo_spacy: Optional[str] = None,
        request_id: Optional[str] = None,
        groq_api_key: Optional[str] = None,
        contexto_articulo: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta el pipeline completo de 7 fases para un fragmento.
        
        Args:
            fragmento: Fragmento a procesar
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
            
        # Manejar tanto formato ART-{ID} como UUIDs legacy
        if fragmento.id_fragmento.startswith("ART-"):
            # Formato de trazabilidad: mantener como string
            fragmento_id_str = fragmento.id_fragmento
            self.base_logger.info(f"Procesando fragmento con ID de trazabilidad: {fragmento_id_str}")
        else:
            # Formato UUID legacy: validar y mantener como string
            try:
                # Validar que sea un UUID válido
                uuid.UUID(fragmento.id_fragmento)
                fragmento_id_str = fragmento.id_fragmento
                self.base_logger.info(f"Procesando fragmento con UUID legacy: {fragmento_id_str}")
            except ValueError:
                self.base_logger.error(f"ID de fragmento inválido: {fragmento.id_fragmento}")
                raise ValueError(f"El ID del fragmento no es válido: {fragmento.id_fragmento}")
        
        # Crear contexto de logging para este pipeline
        log_context = LogContext(
            request_id=request_id,
            component="PipelineCoordinator",
            fragment_id=fragmento_id_str,
            metadata={
                "articulo_id": fragmento.id_articulo_fuente,
                "orden": fragmento.orden_en_articulo
            }
        )
        
        logger = log_context.get_logger()
        logger.info(f"Iniciando pipeline completo para fragmento {fragmento_id_str}")
        
        resultado = {
            "request_id": request_id,
            "fragmento_id": fragmento_id_str,
            "exito": False,
            "fase_completada": 0,
            "payload": None,
            "resultados_fases": {},
            "errores": [],
            "metadatos": {},
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
                    texto_original_fragmento=fragmento.texto_original,
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
                resultado["payload"] = self._crear_payload_no_relevante(fragmento, resultado_fase1)
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
            payload = self._generar_payload_completo_7_fases(
                fragmento=fragmento,
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
            
            hechos_data.append({
                "id_temporal_hecho": str(hecho.id_hecho),  # int → str
                "descripcion_hecho": hecho.texto_original_del_hecho,
                "tipo_hecho": hecho.metadata_hecho.tipo_hecho if hasattr(hecho.metadata_hecho, 'tipo_hecho') else "evento",
                "relevancia_hecho": int(hecho.confianza_extraccion * 10),  # 0.0-1.0 → 1-10
                "fecha_ocurrencia_hecho_inicio": fecha_inicio_iso,
                "fecha_ocurrencia_hecho_fin": fecha_fin_iso,
                "precision_temporal": hecho.metadata_hecho.precision_temporal if hasattr(hecho.metadata_hecho, 'precision_temporal') else None,
                "es_evento_futuro": hecho.metadata_hecho.es_futuro if hasattr(hecho.metadata_hecho, 'es_futuro') else None,
                "estado_programacion": hecho.metadata_hecho.estado_programacion if hasattr(hecho.metadata_hecho, 'estado_programacion') else None,
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
        
        # Convertir entidades procesadas (ya normalizadas)
        entidades_data = []
        for entidad in entidades:
            entidades_data.append({
                "id": str(entidad.id_entidad),  # int → str
                "nombre": entidad.nombre_entidad_normalizada or entidad.texto_entidad,
                "tipo": entidad.tipo_entidad,
                "descripcion": f"Entidad extraída con relevancia {entidad.relevancia_entidad}",
                "relevancia_entidad_articulo": int(entidad.relevancia_entidad * 10),
                "metadata_entidad": {
                    **(entidad.metadata_entidad.model_dump() if hasattr(entidad.metadata_entidad, 'model_dump') else {}),
                    "uri_wikidata": entidad.uri_wikidata,
                    "id_entidad_normalizada": str(entidad.id_entidad_normalizada) if entidad.id_entidad_normalizada else None,
                    "similitud_normalizacion": entidad.similitud_normalizacion
                }
            })
        
        # Convertir citas textuales
        citas_data = []
        for cita in citas:
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
