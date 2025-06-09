"""
Main Processing Controller - La Máquina de Noticias Pipeline
===========================================================

Este módulo contiene el controlador principal que orquesta todas las fases
del pipeline de procesamiento de artículos y fragmentos.

Orquesta la ejecución secuencial de las 4 fases:
1. Triaje y preprocesamiento
2. Extracción de elementos básicos  
3. Extracción de citas y datos cuantitativos
4. Normalización, vinculación y relaciones
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import time
import threading
from loguru import logger

# Importar servicios existentes
from .services.groq_service import GroqService
from .services.supabase_service import get_supabase_service, SupabaseService
# Importar FragmentProcessor para gestión coherente de IDs
from .utils.fragment_processor import FragmentProcessor
# Importar utilidades de logging estructurado
from .utils.logging_config import get_logger, log_phase
# Importar JobTrackerService para procesamiento asíncrono
from .services.job_tracker_service import get_job_tracker_service, JobStatus


class PipelineController:
    """
    Controlador principal del pipeline de procesamiento.
    
    Coordina la ejecución de las 4 fases del pipeline y la persistencia
    de resultados en Supabase.
    
    Attributes:
        groq_service: Referencia al servicio de Groq
        supabase_service: Referencia al servicio de Supabase (Singleton)
    """
    
    def __init__(self):
        """
        Inicializa el controlador con referencias a servicios existentes.
        
        No realiza validaciones complejas, confía en que los servicios
        manejen su propia configuración y errores.
        """
        # Logger estructurado con contexto
        self.logger = get_logger("PipelineController")
        self.logger.info("Inicializando PipelineController")
        
        # Solo referencias a los servicios existentes
        # GroqService se inicializa cuando se necesita
        self.groq_service: Optional[GroqService] = None
        
        # SupabaseService usa patrón Singleton
        self.supabase_service: Optional[SupabaseService] = None
        
        # Inicializar contadores de métricas
        self.metrics = {
            "articulos_procesados": 0,
            "fragmentos_procesados": 0,
            "tiempo_total_procesamiento": 0.0,
            "errores_totales": 0
        }
        
        # Lock para proteger las métricas compartidas (thread-safety)
        self._metrics_lock = threading.Lock()
        
        self.logger.info("PipelineController inicializado correctamente")
    
    def _get_groq_service(self) -> GroqService:
        """
        Obtiene una instancia del servicio Groq, inicializándola si es necesario.
        
        Returns:
            Instancia del servicio Groq
            
        Note:
            GroqService no es singleton, se crea una nueva instancia si no existe
        """
        if self.groq_service is None:
            self.logger.debug("Inicializando GroqService por primera vez")
            self.groq_service = GroqService()
        return self.groq_service
    
    def _get_supabase_service(self) -> SupabaseService:
        """
        Obtiene la instancia singleton del servicio Supabase.
        
        Returns:
            Instancia del servicio Supabase
            
        Note:
            Usa la función helper get_supabase_service() para obtener el singleton
        """
        if self.supabase_service is None:
            self.logger.debug("Obteniendo instancia singleton de SupabaseService")
            self.supabase_service = get_supabase_service()
        return self.supabase_service
    
    async def process_article(self, articulo_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa un artículo completo a través del pipeline.
        
        Por ahora, trata el artículo completo como un único fragmento según la
        documentación Context7 sección 4.2 y 5.3.
        
        Args:
            articulo_data: Datos del artículo según ArticuloInItem model.
                Campos requeridos:
                - medio: str
                - pais_publicacion: str
                - tipo_medio: str
                - titular: str
                - fecha_publicacion: datetime
                - contenido_texto: str
            
        Returns:
            Resultado del procesamiento con IDs de persistencia
            
        Note:
            Para artículos largos (>10,000 caracteres), se recomienda usar
            BackgroundTasks de FastAPI. Una futura versión `process_article_async`
            podría implementarse para manejar estos casos de forma asíncrona.
        """
        # Usar request_id pasado desde el endpoint, o generar uno si no existe
        from uuid import uuid4
        request_id = articulo_data.get('request_id', f"ART-{uuid4().hex[:8]}")
        
        # Logger con contexto estructurado
        article_logger = self.logger.bind(
            request_id=request_id,
            medio=articulo_data.get('medio', 'unknown'),
            titular=articulo_data.get('titular', '')[:50]
        )
        
        article_logger.info("Iniciando procesamiento de artículo")
        
        # Validar campos requeridos según ArticuloInItem
        campos_requeridos = ['medio', 'pais_publicacion', 'tipo_medio', 'titular', 'fecha_publicacion', 'contenido_texto']
        campos_faltantes = [campo for campo in campos_requeridos if campo not in articulo_data]
        if campos_faltantes:
            # Usar ValidationError personalizada en lugar de ValueError genérico
            from .utils.error_handling import ValidationError as CustomValidationError, ErrorPhase
            raise CustomValidationError(
                message=f"Campos requeridos faltantes en articulo_data",
                validation_errors=[
                    {"field": campo, "message": f"Campo '{campo}' es requerido"}
                    for campo in campos_faltantes
                ],
                phase=ErrorPhase.GENERAL,
                article_id=articulo_data.get('url', 'unknown')
            )
        
        # Extraer campos principales del artículo
        articulo_id = articulo_data.get('url', f"articulo_{articulo_data['medio']}_{articulo_data['fecha_publicacion']}")
        contenido = articulo_data['contenido_texto']
        
        article_logger.debug(
            f"Artículo recibido",
            articulo_id=articulo_id,
            longitud_contenido=len(contenido)
        )
        
        # Crear FragmentoProcesableItem desde el artículo completo
        # Según Context7 5.3: "El procesamiento se divide en fases secuenciales"
        fragmento_data = {
            "id_fragmento": f"{articulo_id}_fragmento_unico",
            "texto_original": contenido,
            "id_articulo_fuente": str(articulo_id),
            "orden_en_articulo": 0,  # Único fragmento
            "request_id": request_id,  # Pasar el request_id al fragmento
            "metadata_adicional": {
                # Incluir metadatos relevantes del artículo
                "es_articulo_completo": True,
                "fragmentado": False,
                "medio": articulo_data['medio'],
                "pais_publicacion": articulo_data['pais_publicacion'],
                "tipo_medio": articulo_data['tipo_medio'],
                "titular": articulo_data['titular'],
                "fecha_publicacion": str(articulo_data['fecha_publicacion']),
                "autor": articulo_data.get('autor'),
                "idioma": articulo_data.get('idioma', 'es'),
                "seccion": articulo_data.get('seccion'),
                "es_opinion": articulo_data.get('es_opinion', False),
                "es_oficial": articulo_data.get('es_oficial', False),
                "metadata_original": articulo_data.get('metadata', {})
            }
        }
        
        article_logger.debug("Artículo convertido a FragmentoProcesableItem con todos los metadatos")
        
        # Medir tiempo de procesamiento del artículo
        tiempo_inicio = time.time()
        
        # Llamar process_fragment() una vez
        resultado = await self.process_fragment(fragmento_data)
        
        # Calcular tiempo total
        tiempo_procesamiento = time.time() - tiempo_inicio
        
        # Agregar metadata específica del artículo al resultado
        resultado["tipo_procesamiento"] = "articulo_completo"
        resultado["articulo_original"] = {
            "medio": articulo_data['medio'],
            "titular": articulo_data['titular'],
            "fecha_publicacion": str(articulo_data['fecha_publicacion']),
            "url": articulo_data.get('url')
        }
        resultado["numero_fragmentos"] = 1
        resultado["tiempo_procesamiento_articulo"] = tiempo_procesamiento
        
        # Agregar información sobre el tamaño del artículo (subtarea 20.5)
        resultado["metricas_contenido"] = {
            "longitud_caracteres": len(contenido),
            "es_articulo_largo": len(contenido) > 10_000,
            "threshold_articulo_largo": 10_000,
            "tiempo_por_caracter_ms": (tiempo_procesamiento * 1000) / len(contenido) if len(contenido) > 0 else 0
        }
        
        # Actualizar métricas globales (thread-safe)
        with self._metrics_lock:
            self.metrics["articulos_procesados"] += 1
        
        # Propagar advertencias si las hay
        if "advertencias" in resultado and len(resultado["advertencias"]) > 0:
            article_logger.warning(
                f"Artículo procesado con advertencias",
                advertencias_count=len(resultado['advertencias']),
                advertencias=resultado['advertencias']
            )
        
        # Actualizar campos que el pipeline debe generar según Context7
        resultado["campos_generados"] = {
            "resumen": "Pendiente de Fase 2",
            "categorias_asignadas": [],
            "puntuacion_relevancia": None,
            "nota": "Estos campos serán generados cuando se implementen las fases correspondientes"
        }
        
        # Log final con estado de procesamiento
        if resultado.get("procesamiento_parcial", False):
            article_logger.info(
                f"Procesamiento de artículo completado CON ADVERTENCIAS",
                tiempo_segundos=tiempo_procesamiento,
                advertencias_count=len(resultado.get('advertencias', [])),
                persistencia_exitosa=resultado.get('persistencia', {}).get('exitosa', False)
            )
        else:
            article_logger.info(
                f"Procesamiento de artículo completado exitosamente",
                tiempo_segundos=tiempo_procesamiento,
                persistencia_exitosa=resultado.get('persistencia', {}).get('exitosa', False),
                elementos_procesados={
                    "hechos": resultado.get('metricas', {}).get('conteos_elementos', {}).get('hechos_extraidos', 0),
                    "entidades": resultado.get('metricas', {}).get('conteos_elementos', {}).get('entidades_extraidas', 0)
                }
            )
        
        # Retornar el resultado directamente
        return resultado
    
    async def process_fragment(self, fragmento_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa un fragmento de documento a través del pipeline.
        
        Args:
            fragmento_data: Datos del fragmento según FragmentoProcesableItem model
            
        Returns:
            Resultado del procesamiento con IDs de persistencia
        """
        # Iniciar medición de tiempo total
        tiempo_inicio_total = time.time()
        
        # Usar request_id pasado o generar uno para este procesamiento
        from uuid import uuid4
        request_id = fragmento_data.get('request_id', f"FRAG-{uuid4().hex[:8]}")
        
        # Logger con contexto estructurado
        fragment_logger = self.logger.bind(
            request_id=request_id,
            fragment_id=fragmento_data.get('id_fragmento', 'unknown')
        )
        
        fragment_logger.info("Iniciando procesamiento de fragmento")
        
        # Validar entrada con FragmentoProcesableItem
        from .models.entrada import FragmentoProcesableItem
        try:
            fragmento = FragmentoProcesableItem(**fragmento_data)
            fragment_logger.debug(f"Fragmento validado: ID={fragmento.id_fragmento}")
        except Exception as e:
            # Capturar errores de validación de Pydantic y convertir a ValidationError personalizada
            from .utils.error_handling import ValidationError as CustomValidationError, ErrorPhase
            raise CustomValidationError(
                message="Error validando datos del fragmento",
                validation_errors=[
                    {"message": str(e)}
                ],
                phase=ErrorPhase.GENERAL,
                article_id=fragmento_data.get('id_fragmento', 'unknown')
            ) from e
        
        # Importar modelos necesarios para las fases
        from .models.procesamiento import (
            ResultadoFase2Extraccion, ResultadoFase3CitasDatos, 
            ResultadoFase4Normalizacion, HechoProcesado, EntidadProcesada,
            CitaTextual, DatosCuantitativos
        )
        from .pipeline.fase_1_triaje import ejecutar_fase_1
        from uuid import UUID, uuid4
        
        # Importar utilidades de manejo de errores
        from .utils.error_handling import (
            ProcessingError, GroqAPIError, SupabaseRPCError,
            ErrorPhase, handle_spacy_load_error_fase1,
            handle_groq_relevance_error_fase1, handle_groq_extraction_error_fase2,
            handle_groq_citas_error_fase3, handle_normalization_error_fase4,
            handle_groq_relations_error_fase4
        )
        
        # Convertir id_fragmento a UUID para las fases
        fragment_uuid = uuid4()
        fragment_logger.debug(f"UUID generado para fragmento: {fragment_uuid}")
        
        # Crear FragmentProcessor para mantener coherencia de IDs
        processor = FragmentProcessor(fragment_uuid)
        fragment_logger.debug(f"FragmentProcessor creado para fragmento {fragment_uuid}")
        
        # Inicializar lista de advertencias para el resultado final
        advertencias = []
        
        # Inicializar métricas del pipeline
        metricas_pipeline = {
            "tiempos_fases": {},
            "conteos_elementos": {},
            "tasas_exito": {}
        }
        
        # --- FASE 1: Triaje ---
        tiempo_inicio_fase1 = time.time()
        with log_phase("Fase1_Triaje", request_id, fragment_id=str(fragment_uuid)) as fase1_logger:
            resultado_fase1 = None
            try:
                resultado_fase1 = ejecutar_fase_1(
                    id_fragmento_original=fragment_uuid,
                    texto_original_fragmento=fragmento.texto_original
                )
                tiempo_fase1 = time.time() - tiempo_inicio_fase1
                metricas_pipeline["tiempos_fases"]["fase1"] = tiempo_fase1
                metricas_pipeline["tasas_exito"]["fase1"] = True
                
                fase1_logger.info(
                    f"Fase 1 completada exitosamente",
                    relevante=resultado_fase1.es_relevante,
                    tiempo_segundos=tiempo_fase1,
                    longitud_texto=len(fragmento.texto_original)
                )
            except Exception as e:
                tiempo_fase1 = time.time() - tiempo_inicio_fase1
                metricas_pipeline["tiempos_fases"]["fase1"] = tiempo_fase1
                metricas_pipeline["tasas_exito"]["fase1"] = False
                
                fase1_logger.error(f"Error en Fase 1: {str(e)}", tiempo_segundos=tiempo_fase1)
                # Usar fallback - aceptar artículo según política
                from .models.procesamiento import ResultadoFase1Triaje
                fallback_data = handle_spacy_load_error_fase1(
                    article_id=str(fragment_uuid),
                    model_name="es_core_news_sm",
                    exception=e
                )
                # Usar el texto original como texto para siguiente fase
                fallback_data["texto_para_siguiente_fase"] = fragmento.texto_original
                resultado_fase1 = ResultadoFase1Triaje(**fallback_data)
                advertencias.append(f"Fase 1 ejecutada con fallback: {str(e)}")
                fase1_logger.warning(f"Fase 1 usando fallback para fragmento {fragment_uuid}")
        
        # --- FASE 2: Extracción ---
        tiempo_inicio_fase2 = time.time()
        with log_phase("Fase2_Extraccion", request_id, fragment_id=str(fragment_uuid)) as fase2_logger:
            # Importar la función ejecutar_fase_2
            from .pipeline.fase_2_extraccion import ejecutar_fase_2
            
            resultado_fase2 = None
            try:
                resultado_fase2 = ejecutar_fase_2(
                    resultado_fase_1=resultado_fase1,
                    processor=processor  # Pasar el processor para IDs coherentes
                )
                tiempo_fase2 = time.time() - tiempo_inicio_fase2
                metricas_pipeline["tiempos_fases"]["fase2"] = tiempo_fase2
                metricas_pipeline["tasas_exito"]["fase2"] = True
                metricas_pipeline["conteos_elementos"]["hechos_extraidos"] = len(resultado_fase2.hechos_extraidos)
                metricas_pipeline["conteos_elementos"]["entidades_extraidas"] = len(resultado_fase2.entidades_extraidas)
                
                fase2_logger.info(
                    f"Fase 2 completada exitosamente",
                    hechos_extraidos=len(resultado_fase2.hechos_extraidos),
                    entidades_extraidas=len(resultado_fase2.entidades_extraidas),
                    tiempo_segundos=tiempo_fase2
                )
            except Exception as e:
                tiempo_fase2 = time.time() - tiempo_inicio_fase2
                metricas_pipeline["tiempos_fases"]["fase2"] = tiempo_fase2
                metricas_pipeline["tasas_exito"]["fase2"] = False
                
                fase2_logger.error(f"Error en Fase 2: {str(e)}", tiempo_segundos=tiempo_fase2)
                # Usar fallback - crear hecho básico del título
                fallback_data = handle_groq_extraction_error_fase2(
                    article_id=str(fragment_uuid),
                    titulo=fragmento.metadata_adicional.get("titular", "Sin título"),
                    medio=fragmento.metadata_adicional.get("medio", "Desconocido"),
                    exception=e
                )
                
                # Crear objetos Pydantic desde el fallback
                # datetime ya está importada al inicio del archivo
                hechos_fallback = [
                    HechoProcesado(
                        id_hecho=h["id_hecho"],
                        id_fragmento_origen=fragment_uuid,  # Campo requerido
                        texto_original_del_hecho=h["texto_original_del_hecho"],
                        confianza_extraccion=0.5,
                        metadata_hecho=h.get("metadata_hecho", {})
                    )
                    for h in fallback_data["hechos_extraidos"]
                ]
                
                entidades_fallback = [
                    EntidadProcesada(
                        id_entidad=e["id_entidad"],
                        id_fragmento_origen=fragment_uuid,  # Campo requerido
                        texto_entidad=e["texto_entidad"],
                        tipo_entidad=e["tipo_entidad"],
                        relevancia_entidad=0.5,
                        metadata_entidad=e.get("metadata_entidad", {})
                    )
                    for e in fallback_data["entidades_extraidas"]
                ]
                
                resultado_fase2 = ResultadoFase2Extraccion(
                    id_fragmento=fragment_uuid,
                    hechos_extraidos=hechos_fallback,
                    entidades_extraidas=entidades_fallback,
                    resumen_extraccion="Extracción básica por fallback",
                    metadata_extraccion={"es_fallback": True, "error": str(e)},
                    fecha_creacion=datetime.utcnow()
                )
                
                # Actualizar métricas con valores de fallback
                metricas_pipeline["conteos_elementos"]["hechos_extraidos"] = len(hechos_fallback)
                metricas_pipeline["conteos_elementos"]["entidades_extraidas"] = len(entidades_fallback)
                
                advertencias.extend(fallback_data.get("advertencias", []))
                advertencias.append(f"Fase 2 ejecutada con fallback: {str(e)}")
                fase2_logger.warning(f"Fase 2 usando fallback para fragmento {fragment_uuid}")
        
        # --- FASE 3: Citas y Datos ---
        tiempo_inicio_fase3 = time.time()
        with log_phase("Fase3_CitasDatos", request_id, fragment_id=str(fragment_uuid)) as fase3_logger:
            # Importar la función ejecutar_fase_3
            from .pipeline.fase_3_citas_datos import ejecutar_fase_3
            
            resultado_fase3 = None
            try:
                resultado_fase3 = ejecutar_fase_3(
                    resultado_fase_2=resultado_fase2,
                    processor=processor,  # Pasar el processor para IDs coherentes
                    resultado_fase_1=resultado_fase1  # Pasar fase 1 para acceso al texto original
                )
                tiempo_fase3 = time.time() - tiempo_inicio_fase3
                metricas_pipeline["tiempos_fases"]["fase3"] = tiempo_fase3
                metricas_pipeline["tasas_exito"]["fase3"] = True
                metricas_pipeline["conteos_elementos"]["citas_extraidas"] = len(resultado_fase3.citas_textuales_extraidas)
                metricas_pipeline["conteos_elementos"]["datos_cuantitativos"] = len(resultado_fase3.datos_cuantitativos_extraidos)
                
                fase3_logger.info(
                    f"Fase 3 completada exitosamente",
                    citas_extraidas=len(resultado_fase3.citas_textuales_extraidas),
                    datos_cuantitativos=len(resultado_fase3.datos_cuantitativos_extraidos),
                    tiempo_segundos=tiempo_fase3
                )
            except Exception as e:
                tiempo_fase3 = time.time() - tiempo_inicio_fase3
                metricas_pipeline["tiempos_fases"]["fase3"] = tiempo_fase3
                metricas_pipeline["tasas_exito"]["fase3"] = False
                
                fase3_logger.error(f"Error en Fase 3: {str(e)}", tiempo_segundos=tiempo_fase3)
                # Usar fallback - continuar sin citas ni datos (no es crítico)
                fallback_data = handle_groq_citas_error_fase3(
                    article_id=str(fragment_uuid),
                    exception=e
                )
                
                from datetime import datetime
                resultado_fase3 = ResultadoFase3CitasDatos(
                    id_fragmento=fragment_uuid,
                    citas_textuales_extraidas=[],  # Sin citas
                    datos_cuantitativos_extraidos=[],  # Sin datos
                    resumen_citas_datos="Sin citas ni datos extraídos (fallback)",
                    metadata_citas_datos={"es_fallback": True, "error": str(e)},
                    fecha_creacion=datetime.utcnow()
                )
                
                # Actualizar métricas con valores de fallback
                metricas_pipeline["conteos_elementos"]["citas_extraidas"] = 0
                metricas_pipeline["conteos_elementos"]["datos_cuantitativos"] = 0
                
                advertencias.extend(fallback_data.get("advertencias_citas_datos", []))
                advertencias.append(f"Fase 3 ejecutada con fallback: {str(e)}")
                fase3_logger.warning(f"Fase 3 usando fallback para fragmento {fragment_uuid}")
        
        # --- FASE 4: Normalización ---
        tiempo_inicio_fase4 = time.time()
        with log_phase("Fase4_Normalizacion", request_id, fragment_id=str(fragment_uuid)) as fase4_logger:
            # Importar la función ejecutar_fase_4
            from .pipeline.fase_4_normalizacion import ejecutar_fase_4
            
            # Obtener servicio de Supabase para normalización
            supabase_service = self._get_supabase_service()
            
            resultado_fase4 = None
            try:
                resultado_fase4 = ejecutar_fase_4(
                    processor=processor,  # Pasar el processor primero como indica la firma
                    resultado_fase_1=resultado_fase1,
                    resultado_fase_2=resultado_fase2,
                    resultado_fase_3=resultado_fase3,
                    supabase_service=supabase_service  # Para normalización de entidades
                )
                tiempo_fase4 = time.time() - tiempo_inicio_fase4
                metricas_pipeline["tiempos_fases"]["fase4"] = tiempo_fase4
                metricas_pipeline["tasas_exito"]["fase4"] = True
                
                # Contar elementos normalizados y relaciones
                relaciones_metadata = resultado_fase4.metadata_normalizacion.get("relaciones", {})
                metricas_pipeline["conteos_elementos"]["entidades_normalizadas"] = len(resultado_fase4.entidades_normalizadas)
                metricas_pipeline["conteos_elementos"]["relaciones_hecho_hecho"] = len(relaciones_metadata.get("hecho_hecho", []))
                metricas_pipeline["conteos_elementos"]["relaciones_entidad_entidad"] = len(relaciones_metadata.get("entidad_entidad", []))
                metricas_pipeline["conteos_elementos"]["contradicciones"] = len(relaciones_metadata.get("contradicciones", []))
                
                fase4_logger.info(
                    f"Fase 4 completada exitosamente",
                    estado=resultado_fase4.estado_general_normalizacion,
                    entidades_normalizadas=len(resultado_fase4.entidades_normalizadas),
                    relaciones_detectadas=len(relaciones_metadata.get("hecho_hecho", [])) + len(relaciones_metadata.get("entidad_entidad", [])),
                    tiempo_segundos=tiempo_fase4
                )
            except Exception as e:
                tiempo_fase4 = time.time() - tiempo_inicio_fase4
                metricas_pipeline["tiempos_fases"]["fase4"] = tiempo_fase4
                metricas_pipeline["tasas_exito"]["fase4"] = False
                
                fase4_logger.error(f"Error en Fase 4: {str(e)}", tiempo_segundos=tiempo_fase4)
                # Usar fallback - tratar todas las entidades como nuevas
                from datetime import datetime
                
                # Copiar entidades de fase 2 sin normalización
                entidades_sin_normalizar = []
                for entidad in resultado_fase2.entidades_extraidas:
                    entidad_copia = EntidadProcesada(
                        id_entidad=entidad.id_entidad,
                        texto_entidad=entidad.texto_entidad,
                        tipo_entidad=entidad.tipo_entidad,
                        relevancia_entidad=entidad.relevancia_entidad,
                        metadata_entidad=entidad.metadata_entidad,
                        id_entidad_normalizada=None,  # Sin normalización
                        nombre_entidad_normalizada=None,
                        similitud_normalizacion=0.0
                    )
                    entidades_sin_normalizar.append(entidad_copia)
                
                # Usar fallback para relaciones también
                relaciones_fallback = handle_groq_relations_error_fase4(
                    article_id=str(fragment_uuid),
                    exception=e
                )
                
                resultado_fase4 = ResultadoFase4Normalizacion(
                    id_fragmento=fragment_uuid,
                    entidades_normalizadas=entidades_sin_normalizar,
                    relaciones_hecho_entidad=[],
                    relaciones_hecho_hecho=[],
                    relaciones_entidad_entidad=[],
                    contradicciones_detectadas=[],
                    indices_relaciones=relaciones_fallback["indices"],
                    resumen_normalizacion="Normalización básica por fallback (sin relaciones)",
                    estado_general_normalizacion="completado_con_advertencias",
                    metadata_normalizacion={
                        "es_fallback": True,
                        "error": str(e),
                        "relaciones": {"hecho_hecho": [], "entidad_entidad": [], "contradicciones": []}
                    },
                    fecha_creacion=datetime.utcnow()
                )
                
                # Actualizar métricas con valores de fallback
                metricas_pipeline["conteos_elementos"]["entidades_normalizadas"] = len(entidades_sin_normalizar)
                metricas_pipeline["conteos_elementos"]["relaciones_hecho_hecho"] = 0
                metricas_pipeline["conteos_elementos"]["relaciones_entidad_entidad"] = 0
                metricas_pipeline["conteos_elementos"]["contradicciones"] = 0
                
                advertencias.append(f"Fase 4 ejecutada con fallback: {str(e)}")
                fase4_logger.warning(f"Fase 4 usando fallback para fragmento {fragment_uuid}")
        
        # Calcular tiempo total de procesamiento
        tiempo_total_pipeline = time.time() - tiempo_inicio_total
        metricas_pipeline["tiempo_total_segundos"] = tiempo_total_pipeline
        
        # Calcular tasa de éxito general
        fases_exitosas = sum(1 for exito in metricas_pipeline["tasas_exito"].values() if exito)
        total_fases = len(metricas_pipeline["tasas_exito"])
        metricas_pipeline["tasa_exito_general"] = fases_exitosas / total_fases if total_fases > 0 else 0.0
        
        # Actualizar contadores globales (thread-safe)
        with self._metrics_lock:
            self.metrics["fragmentos_procesados"] += 1
            self.metrics["tiempo_total_procesamiento"] += tiempo_total_pipeline
            if len(advertencias) > 0:
                self.metrics["errores_totales"] += len(advertencias)
        
        # Retornar diccionario simple con todos los resultados
        resultado_pipeline = {
            "fragmento_id": fragmento.id_fragmento,
            "fragmento_uuid": str(fragment_uuid),
            "request_id": request_id,
            "fase_1_triaje": resultado_fase1.model_dump() if resultado_fase1 else {},
            "fase_2_extraccion": resultado_fase2.model_dump() if resultado_fase2 else {},
            "fase_3_citas_datos": resultado_fase3.model_dump() if resultado_fase3 else {},
            "fase_4_normalizacion": resultado_fase4.model_dump() if resultado_fase4 else {},
            "procesamiento_exitoso": True,  # True aunque haya usado fallbacks
            "procesamiento_parcial": len(advertencias) > 0,  # Indica si hubo fallbacks
            "advertencias": advertencias,  # Lista de advertencias acumuladas
            "timestamp": resultado_fase1.fecha_creacion.isoformat() if resultado_fase1 else datetime.utcnow().isoformat(),
            "processor_stats": processor.get_stats(),  # Añadir estadísticas del processor
            "metricas": metricas_pipeline  # Añadir métricas del pipeline
        }
        
        # Log de resumen del processor
        processor.log_summary()
        
        # Log final con métricas completas
        fragment_logger.info(
            "Pipeline de fragmento completado",
            tiempo_total_segundos=tiempo_total_pipeline,
            tasa_exito_general=metricas_pipeline["tasa_exito_general"],
            elementos_procesados={
                "hechos": metricas_pipeline["conteos_elementos"].get("hechos_extraidos", 0),
                "entidades": metricas_pipeline["conteos_elementos"].get("entidades_extraidas", 0),
                "citas": metricas_pipeline["conteos_elementos"].get("citas_extraidas", 0),
                "datos_cuantitativos": metricas_pipeline["conteos_elementos"].get("datos_cuantitativos", 0),
                "relaciones": metricas_pipeline["conteos_elementos"].get("relaciones_hecho_hecho", 0) + 
                             metricas_pipeline["conteos_elementos"].get("relaciones_entidad_entidad", 0)
            },
            advertencias_count=len(advertencias)
        )
        
        # --- INTEGRACIÓN CON PERSISTENCIA ---
        # Según subtarea 19.4: Integración Mínima con Persistencia
        tiempo_inicio_persistencia = time.time()
        fragment_logger.info("Iniciando persistencia del fragmento procesado")
        
        # Solo intentar persistir si hay datos válidos de al menos fase 2
        if not resultado_fase2 or len(resultado_fase2.hechos_extraidos) == 0:
            fragment_logger.warning("No hay datos suficientes para persistir. Omitiendo persistencia.")
            resultado_pipeline["persistencia"] = {
                "exitosa": False,
                "mensaje": "No hay datos suficientes para persistir (sin hechos extraídos)",
                "advertencia": "Pipeline ejecutado pero sin datos para almacenar",
                "tiempo_segundos": 0
            }
            return resultado_pipeline
        
        try:
            # Importar PayloadBuilder
            from .services.payload_builder import PayloadBuilder
            
            # Crear instancia del builder
            builder = PayloadBuilder()
            
            # Preparar datos para el payload
            # Metadatos del fragmento
            metadatos_fragmento = {
                "indice_secuencial_fragmento": fragmento.orden_en_articulo or 0,
                "titulo_seccion_fragmento": fragmento.metadata_adicional.get("titulo_seccion"),
                "contenido_texto_original_fragmento": fragmento.texto_original,
                "num_pagina_inicio_fragmento": fragmento.metadata_adicional.get("pagina_inicio"),
                "num_pagina_fin_fragmento": fragmento.metadata_adicional.get("pagina_fin")
            }
            
            # Resumen y estado - usar resumen más completo
            resumen_fragmento = f"{resultado_fase2.resumen_extraccion}. {resultado_fase4.resumen_normalizacion}"
            estado_final = "completado_ok" if resultado_fase1.es_relevante else "completado_no_relevante"
            fecha_procesamiento = datetime.utcnow().isoformat() + "Z"
            
            # Preparar datos de hechos extraídos
            hechos_extraidos_data = [
                {
                    "id_hecho": hecho.id_hecho,
                    "texto_original_del_hecho": hecho.texto_original_del_hecho,
                    "confianza_extraccion": hecho.confianza_extraccion,
                    "metadata_hecho": hecho.metadata_hecho.model_dump() if hecho.metadata_hecho else {}
                }
                for hecho in resultado_fase2.hechos_extraidos
            ]
            
            # Preparar datos de entidades
            entidades_autonomas_data = [
                {
                    "id_entidad": entidad.id_entidad,
                    "texto_entidad": entidad.texto_entidad,
                    "tipo_entidad": entidad.tipo_entidad,
                    "relevancia_entidad": entidad.relevancia_entidad,
                    "metadata_entidad": entidad.metadata_entidad.model_dump() if entidad.metadata_entidad else {},
                    "id_entidad_normalizada": str(entidad.id_entidad_normalizada) if entidad.id_entidad_normalizada else None,
                    "nombre_entidad_normalizada": entidad.nombre_entidad_normalizada,
                    "similitud_normalizacion": entidad.similitud_normalizacion
                }
                for entidad in resultado_fase4.entidades_normalizadas  # Usar las normalizadas de fase 4
            ]
            
            # Preparar datos de citas
            citas_textuales_data = [
                {
                    "id_cita": cita.id_cita,
                    "texto_cita": cita.texto_cita,
                    "persona_citada": cita.persona_citada,
                    "id_entidad_citada": cita.id_entidad_citada,
                    "contexto_cita": cita.contexto_cita,
                    "metadata_cita": cita.metadata_cita.model_dump() if cita.metadata_cita else {}
                }
                for cita in resultado_fase3.citas_textuales_extraidas
            ]
            
            # Preparar datos cuantitativos
            datos_cuantitativos_data = [
                {
                    "id_dato_cuantitativo": dato.id_dato_cuantitativo,
                    "descripcion_dato": dato.descripcion_dato,
                    "valor_dato": dato.valor_dato,
                    "unidad_dato": dato.unidad_dato,
                    "fecha_dato": dato.fecha_dato,
                    "metadata_dato": dato.metadata_dato.model_dump() if dato.metadata_dato else {}
                }
                for dato in resultado_fase3.datos_cuantitativos_extraidos
            ]
            
            # Extraer relaciones del metadata de fase 4 (si existen)
            relaciones_metadata = resultado_fase4.metadata_normalizacion.get("relaciones", {})
            
            # NOTA: Las relaciones hecho-entidad no se persisten en la tabla de relaciones
            # porque ya están embebidas en cada hecho con el campo "entidades_del_hecho"
            # Sin embargo, podríamos loguearlas para referencia
            relaciones_hecho_entidad = relaciones_metadata.get("hecho_entidad", [])
            if relaciones_hecho_entidad:
                fragment_logger.debug(
                    f"Relaciones hecho-entidad encontradas: {len(relaciones_hecho_entidad)} "
                    "(ya incluidas en estructura de hechos)"
                )
            
            # Mapear relaciones hecho-hecho al formato esperado por RPC
            relaciones_hechos_data = []
            for rel in relaciones_metadata.get("hecho_hecho", []):
                relacion_mapeada = {
                    "hecho_origen_id_temporal": str(rel.get("hecho_origen_id")),
                    "hecho_destino_id_temporal": str(rel.get("hecho_destino_id")),
                    "tipo_relacion": rel.get("tipo_relacion", "desconocido"),
                    "fuerza_relacion": rel.get("fuerza_relacion", 5),
                    "descripcion_relacion": rel.get("descripcion_relacion", "")
                }
                relaciones_hechos_data.append(relacion_mapeada)
            
            # Mapear relaciones entidad-entidad al formato esperado por RPC
            relaciones_entidades_data = []
            for rel in relaciones_metadata.get("entidad_entidad", []):
                relacion_mapeada = {
                    "entidad_origen_id_temporal": str(rel.get("entidad_origen_id")),
                    "entidad_destino_id_temporal": str(rel.get("entidad_destino_id")),
                    "tipo_relacion": rel.get("tipo_relacion", "desconocido"),
                    "descripcion_relacion": rel.get("descripcion", ""),
                    "fecha_inicio_relacion": rel.get("fecha_inicio"),
                    "fecha_fin_relacion": rel.get("fecha_fin"),
                    "fuerza_relacion": rel.get("fuerza_relacion", 5)
                }
                relaciones_entidades_data.append(relacion_mapeada)
            
            # Mapear contradicciones al formato esperado por RPC
            contradicciones_detectadas_data = []
            for cont in relaciones_metadata.get("contradicciones", []):
                contradiccion_mapeada = {
                    "hecho_principal_id_temporal": str(cont.get("hecho_principal_id")),
                    "hecho_contradictorio_id_temporal": str(cont.get("hecho_contradictorio_id")),
                    "tipo_contradiccion": cont.get("tipo_contradiccion", "desconocido"),
                    "grado_contradiccion": cont.get("grado_contradiccion", 3),
                    "descripcion_contradiccion": cont.get("descripcion", "")
                }
                contradicciones_detectadas_data.append(contradiccion_mapeada)
            
            # Log de relaciones a persistir
            fragment_logger.info(
                f"Relaciones a persistir",
                relaciones_hechos=len(relaciones_hechos_data),
                relaciones_entidades=len(relaciones_entidades_data),
                contradicciones=len(contradicciones_detectadas_data)
            )
            
            # Construir payload usando PayloadBuilder
            payload_fragmento = builder.construir_payload_fragmento(
                metadatos_fragmento_data=metadatos_fragmento,
                resumen_generado_fragmento=resumen_fragmento,
                estado_procesamiento_final_fragmento=estado_final,
                fecha_procesamiento_pipeline_fragmento=fecha_procesamiento,
                hechos_extraidos_data=hechos_extraidos_data,
                entidades_autonomas_data=entidades_autonomas_data,
                citas_textuales_data=citas_textuales_data,
                datos_cuantitativos_data=datos_cuantitativos_data,
                relaciones_hechos_data=relaciones_hechos_data,
                relaciones_entidades_data=relaciones_entidades_data,
                contradicciones_detectadas_data=contradicciones_detectadas_data
            )
            
            fragment_logger.debug("Payload construido exitosamente")
            
            # Obtener servicio de Supabase
            supabase_service = self._get_supabase_service()
            
            # Convertir payload a diccionario para la RPC
            payload_dict = payload_fragmento.model_dump()
            
            # Llamar a insertar_fragmento_completo
            fragment_logger.info("Llamando RPC insertar_fragmento_completo")
            resultado_persistencia = supabase_service.insertar_fragmento_completo(payload_dict)
            
            if resultado_persistencia:
                tiempo_persistencia = time.time() - tiempo_inicio_persistencia
                
                fragment_logger.info(
                    f"Fragmento persistido exitosamente",
                    fragmento_id=resultado_persistencia.get('fragmento_id'),
                    tiempo_segundos=tiempo_persistencia
                )
                
                # Agregar IDs de persistencia al resultado
                resultado_pipeline["persistencia"] = {
                    "exitosa": True,
                    "fragmento_id": resultado_persistencia.get('fragmento_id'),
                    "hechos_insertados": resultado_persistencia.get('hechos_insertados', 0),
                    "entidades_insertadas": resultado_persistencia.get('entidades_insertadas', 0),
                    "citas_insertadas": resultado_persistencia.get('citas_insertadas', 0),
                    "datos_insertados": resultado_persistencia.get('datos_insertados', 0),
                    "relaciones_hechos_insertadas": len(relaciones_hechos_data),
                    "relaciones_entidades_insertadas": len(relaciones_entidades_data),
                    "contradicciones_insertadas": len(contradicciones_detectadas_data),
                    "tiempo_segundos": tiempo_persistencia
                }
                
                # Log detallado de relaciones persistidas
                if relaciones_hechos_data or relaciones_entidades_data or contradicciones_detectadas_data:
                    fragment_logger.info(
                        f"Relaciones persistidas exitosamente",
                        relaciones_hecho_hecho=len(relaciones_hechos_data),
                        relaciones_entidad_entidad=len(relaciones_entidades_data),
                        contradicciones=len(contradicciones_detectadas_data)
                    )
            else:
                tiempo_persistencia = time.time() - tiempo_inicio_persistencia
                fragment_logger.warning("RPC insertar_fragmento_completo no retornó datos")
                resultado_pipeline["persistencia"] = {
                    "exitosa": False,
                    "mensaje": "No se obtuvieron datos de la RPC",
                    "tiempo_segundos": tiempo_persistencia
                }
                
        except Exception as e:
            tiempo_persistencia = time.time() - tiempo_inicio_persistencia
            
            # Si falla, loguear el error y retornar el resultado sin IDs de BD
            fragment_logger.error(
                f"Error durante la persistencia: {str(e)}",
                tiempo_segundos=tiempo_persistencia,
                error_type=type(e).__name__
            )
            
            # Intentar guardar en tabla de errores si es crítico
            from .utils.error_handling import handle_persistence_error_fase5
            error_result = handle_persistence_error_fase5(
                article_id=str(fragment_uuid),
                datos_completos=resultado_pipeline,
                exception=e
            )
            
            resultado_pipeline["persistencia"] = {
                "exitosa": False,
                "error": str(e),
                "mensaje": "El fragmento fue procesado pero no se pudo persistir",
                "error_handling": error_result,
                "tiempo_segundos": tiempo_persistencia
            }
            
            advertencias.append(f"Error en persistencia: {str(e)}")
            resultado_pipeline["advertencias"] = advertencias
            
            # Actualizar métricas de error (thread-safe)
            with self._metrics_lock:
                self.metrics["errores_totales"] += 1
        
        return resultado_pipeline
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Obtiene las métricas globales del controller.
        
        Returns:
            Diccionario con métricas acumuladas
        """
        # Obtener métricas de forma thread-safe
        with self._metrics_lock:
            # Copiar valores para evitar problemas de concurrencia
            articulos = self.metrics["articulos_procesados"]
            fragmentos = self.metrics["fragmentos_procesados"]
            tiempo_total = self.metrics["tiempo_total_procesamiento"]
            errores = self.metrics["errores_totales"]
        
        # Calcular métricas derivadas fuera del lock
        tiempo_promedio = 0.0
        if fragmentos > 0:
            tiempo_promedio = tiempo_total / fragmentos
        
        return {
            "articulos_procesados": articulos,
            "fragmentos_procesados": fragmentos,
            "tiempo_total_procesamiento": tiempo_total,
            "tiempo_promedio_por_fragmento": tiempo_promedio,
            "errores_totales": errores,
            "tasa_error": errores / max(fragmentos, 1)
        }
    
    async def _process_article_background(self, articulo_data: Dict[str, Any], job_id: str) -> None:
        """
        Procesa un artículo en segundo plano actualizando el job tracker.
        
        Este método es llamado por FastAPI BackgroundTasks para procesamiento asíncrono
        de artículos largos. Actualiza el estado del job durante todo el proceso.
        
        Args:
            articulo_data: Datos del artículo a procesar
            job_id: ID del job para tracking del estado
            
        Note:
            - Actualiza job tracker al inicio (PROCESSING)
            - Actualiza job tracker al completar (COMPLETED) o fallar (FAILED)
            - Maneja todos los errores y los reporta en el job tracker
        """
        # Obtener instancia del job tracker
        job_tracker = get_job_tracker_service()
        
        # Logger con contexto
        bg_logger = self.logger.bind(
            job_id=job_id,
            medio=articulo_data.get('medio', 'unknown'),
            process_type="article_background"
        )
        
        bg_logger.info("Iniciando procesamiento de artículo en background")
        
        try:
            # Actualizar estado a PROCESSING
            job_tracker.update_status(
                job_id=job_id,
                status=JobStatus.PROCESSING,
                metadata_update={
                    "start_time": datetime.utcnow().isoformat() + "Z",
                    "content_length": len(articulo_data.get('contenido_texto', '')),
                    "medio": articulo_data.get('medio'),
                    "titular": articulo_data.get('titular', '')[:100]
                }
            )
            
            # Llamar al método síncrono de procesamiento
            resultado = await self.process_article(articulo_data)
            
            # Actualizar estado a COMPLETED con el resultado
            job_tracker.update_status(
                job_id=job_id,
                status=JobStatus.COMPLETED,
                result=resultado,
                metadata_update={
                    "end_time": datetime.utcnow().isoformat() + "Z",
                    "processing_time_seconds": resultado.get("tiempo_procesamiento_articulo", 0),
                    "elementos_procesados": {
                        "hechos": resultado.get('metricas', {}).get('conteos_elementos', {}).get('hechos_extraidos', 0),
                        "entidades": resultado.get('metricas', {}).get('conteos_elementos', {}).get('entidades_extraidas', 0)
                    },
                    "persistencia_exitosa": resultado.get('persistencia', {}).get('exitosa', False)
                }
            )
            
            bg_logger.info(
                "Procesamiento de artículo en background completado exitosamente",
                tiempo_segundos=resultado.get("tiempo_procesamiento_articulo", 0),
                elementos_procesados=resultado.get('metricas', {}).get('conteos_elementos', {})
            )
            
        except Exception as e:
            # Log del error
            bg_logger.error(
                f"Error en procesamiento de artículo en background: {str(e)}",
                error_type=type(e).__name__
            )
            
            # Actualizar estado a FAILED con información del error
            job_tracker.update_status(
                job_id=job_id,
                status=JobStatus.FAILED,
                error={
                    "tipo": type(e).__name__,
                    "mensaje": str(e),
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                },
                metadata_update={
                    "end_time": datetime.utcnow().isoformat() + "Z",
                    "error_phase": "article_processing"
                }
            )
            
            # Re-lanzar la excepción para que quede registrada
            raise
    
    async def _process_fragment_background(self, fragmento_data: Dict[str, Any], job_id: str) -> None:
        """
        Procesa un fragmento en segundo plano actualizando el job tracker.
        
        Este método es llamado por FastAPI BackgroundTasks para procesamiento asíncrono
        de fragmentos largos. Actualiza el estado del job durante todo el proceso.
        
        Args:
            fragmento_data: Datos del fragmento a procesar
            job_id: ID del job para tracking del estado
            
        Note:
            - Actualiza job tracker al inicio (PROCESSING)
            - Actualiza job tracker al completar (COMPLETED) o fallar (FAILED)
            - Maneja todos los errores y los reporta en el job tracker
        """
        # Obtener instancia del job tracker
        job_tracker = get_job_tracker_service()
        
        # Logger con contexto
        bg_logger = self.logger.bind(
            job_id=job_id,
            fragment_id=fragmento_data.get('id_fragmento', 'unknown'),
            process_type="fragment_background"
        )
        
        bg_logger.info("Iniciando procesamiento de fragmento en background")
        
        try:
            # Actualizar estado a PROCESSING
            job_tracker.update_status(
                job_id=job_id,
                status=JobStatus.PROCESSING,
                metadata_update={
                    "start_time": datetime.utcnow().isoformat() + "Z",
                    "content_length": len(fragmento_data.get('texto_original', '')),
                    "fragment_id": fragmento_data.get('id_fragmento'),
                    "source_article_id": fragmento_data.get('id_articulo_fuente')
                }
            )
            
            # Llamar al método síncrono de procesamiento
            resultado = await self.process_fragment(fragmento_data)
            
            # Calcular tiempo total desde métricas si está disponible
            tiempo_total = resultado.get('metricas', {}).get('tiempo_total_segundos', 0)
            
            # Actualizar estado a COMPLETED con el resultado
            job_tracker.update_status(
                job_id=job_id,
                status=JobStatus.COMPLETED,
                result=resultado,
                metadata_update={
                    "end_time": datetime.utcnow().isoformat() + "Z",
                    "processing_time_seconds": tiempo_total,
                    "elementos_procesados": {
                        "hechos": resultado.get('metricas', {}).get('conteos_elementos', {}).get('hechos_extraidos', 0),
                        "entidades": resultado.get('metricas', {}).get('conteos_elementos', {}).get('entidades_extraidas', 0),
                        "citas": resultado.get('metricas', {}).get('conteos_elementos', {}).get('citas_extraidas', 0),
                        "datos_cuantitativos": resultado.get('metricas', {}).get('conteos_elementos', {}).get('datos_cuantitativos', 0)
                    },
                    "persistencia_exitosa": resultado.get('persistencia', {}).get('exitosa', False),
                    "procesamiento_parcial": resultado.get('procesamiento_parcial', False)
                }
            )
            
            bg_logger.info(
                "Procesamiento de fragmento en background completado",
                tiempo_segundos=tiempo_total,
                procesamiento_parcial=resultado.get('procesamiento_parcial', False),
                advertencias_count=len(resultado.get('advertencias', []))
            )
            
        except Exception as e:
            # Log del error
            bg_logger.error(
                f"Error en procesamiento de fragmento en background: {str(e)}",
                error_type=type(e).__name__
            )
            
            # Actualizar estado a FAILED con información del error
            job_tracker.update_status(
                job_id=job_id,
                status=JobStatus.FAILED,
                error={
                    "tipo": type(e).__name__,
                    "mensaje": str(e),
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                },
                metadata_update={
                    "end_time": datetime.utcnow().isoformat() + "Z",
                    "error_phase": "fragment_processing"
                }
            )
            
            # Re-lanzar la excepción para que quede registrada
            raise
