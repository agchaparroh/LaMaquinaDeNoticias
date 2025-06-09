"""
Test de integración para PipelineController
===========================================

Verifica el flujo completo del pipeline con mocks de servicios.
Ejecutar con: pytest tests/test_controller_integration.py -v
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from uuid import uuid4
import json

from src.controller import PipelineController
from src.models.procesamiento import (
    ResultadoFase1Triaje, ResultadoFase2Extraccion, 
    ResultadoFase3CitasDatos, ResultadoFase4Normalizacion,
    HechoProcesado, EntidadProcesada, CitaTextual, 
    DatosCuantitativos, MetadatosFase1Triaje
)
from src.models.metadatos import (
    MetadatosHecho, MetadatosEntidad, MetadatosCita, MetadatosDato
)


@pytest.fixture
def mock_groq_service():
    """Mock del servicio Groq para tests."""
    mock = Mock()
    # No necesitamos mockear métodos específicos aquí porque 
    # vamos a mockear las funciones ejecutar_fase_* directamente
    return mock


@pytest.fixture
def mock_supabase_service():
    """Mock del servicio Supabase para tests."""
    mock = Mock()
    
    # Mock de normalización de entidades
    mock.normalizar_entidad.return_value = {
        "id_entidad_normalizada": str(uuid4()),
        "nombre_normalizado": "Entidad Normalizada",
        "similitud": 0.95
    }
    
    # Mock de inserción exitosa
    mock.insertar_fragmento_completo.return_value = {
        "fragmento_id": str(uuid4()),
        "hechos_insertados": 2,
        "entidades_insertadas": 3,
        "citas_insertadas": 1,
        "datos_insertados": 1
    }
    
    return mock


@pytest.fixture
def sample_article_complete():
    """Artículo completo de prueba con todos los campos requeridos."""
    return {
        "medio": "El Test Diario",
        "pais_publicacion": "España",
        "tipo_medio": "Digital",
        "titular": "Importante avance científico en investigación del cambio climático",
        "fecha_publicacion": datetime.utcnow(),
        "contenido_texto": """
        Un equipo internacional de científicos ha logrado un importante avance en la comprensión
        del cambio climático. El Dr. Juan Pérez, líder del proyecto, declaró: "Este descubrimiento
        cambiará nuestra forma de entender el calentamiento global". 
        
        El estudio, que analizó datos de los últimos 50 años, encontró que la temperatura 
        media global ha aumentado 1.5 grados Celsius. Los investigadores predicen que para 2050,
        este aumento podría llegar a 3 grados si no se toman medidas urgentes.
        
        La Dra. María González, coautora del estudio, añadió: "Necesitamos actuar ahora para
        evitar consecuencias catastróficas". El informe será presentado en la próxima cumbre
        del clima en Madrid.
        """,
        "url": "https://eltestdiario.es/ciencia/cambio-climatico-avance",
        "autor": "Pedro Martínez",
        "idioma": "es",
        "seccion": "Ciencia",
        "es_opinion": False,
        "es_oficial": False,
        "metadata": {"tags": ["ciencia", "cambio climático", "investigación"]}
    }


@pytest.fixture
def sample_fragment_simple():
    """Fragmento simple de prueba."""
    return {
        "id_fragmento": "test_fragment_123",
        "texto_original": """
        El ministro de Economía anunció nuevas medidas para combatir la inflación.
        "Reduciremos el IVA en productos básicos", afirmó durante la rueda de prensa.
        Se espera que estas medidas beneficien a 10 millones de familias.
        """,
        "id_articulo_fuente": "articulo_economico_456",
        "orden_en_articulo": 0,
        "metadata_adicional": {
            "medio": "Economía Hoy",
            "fecha": "2024-01-20",
            "seccion": "Nacional"
        }
    }


@pytest.fixture
def mock_fase1_resultado():
    """Resultado mock de fase 1."""
    return ResultadoFase1Triaje(
        id_fragmento=uuid4(),
        es_relevante=True,
        decision_triaje="PROCESAR",
        justificacion_triaje="Artículo relevante sobre ciencia y cambio climático",
        categoria_principal="CIENCIA",
        palabras_clave_triaje=["cambio climático", "investigación", "temperatura"],
        puntuacion_triaje=22.0,
        texto_para_siguiente_fase="Texto limpio procesado...",
        metadatos_specificos_triaje=MetadatosFase1Triaje(
            nombre_modelo_triaje="mixtral-8x7b-32768",
            idioma_detectado_original="es",
            necesito_traduccion=False,
            notas_adicionales=None
        ),
        fecha_creacion=datetime.utcnow()
    )


@pytest.fixture
def mock_fase2_resultado():
    """Resultado mock de fase 2."""
    fragment_id = uuid4()
    
    hechos = [
        HechoProcesado(
            id_hecho=1,  # Debe ser entero
            id_fragmento_origen=fragment_id,  # Campo requerido
            texto_original_del_hecho="Un equipo internacional de científicos ha logrado un importante avance",
            confianza_extraccion=0.9,
            metadata_hecho=MetadatosHecho(tipo_hecho="SUCESO")
        ),
        HechoProcesado(
            id_hecho=2,  # Debe ser entero
            id_fragmento_origen=fragment_id,  # Campo requerido
            texto_original_del_hecho="La temperatura media global ha aumentado 1.5 grados Celsius",
            confianza_extraccion=0.95,
            metadata_hecho=MetadatosHecho(tipo_hecho="ANUNCIO", precision_temporal="exacta")
        )
    ]
    
    entidades = [
        EntidadProcesada(
            id_entidad=1,  # Debe ser entero
            id_fragmento_origen=fragment_id,  # Campo requerido
            texto_entidad="Dr. Juan Pérez",
            tipo_entidad="PERSONA",
            relevancia_entidad=0.8,
            metadata_entidad=MetadatosEntidad(tipo="PERSONA", descripcion_estructurada=["líder del proyecto"])
        ),
        EntidadProcesada(
            id_entidad=2,  # Debe ser entero
            id_fragmento_origen=fragment_id,  # Campo requerido
            texto_entidad="Dra. María González",
            tipo_entidad="PERSONA",
            relevancia_entidad=0.7,
            metadata_entidad=MetadatosEntidad(tipo="PERSONA", descripcion_estructurada=["coautora del estudio"])
        ),
        EntidadProcesada(
            id_entidad=3,  # Debe ser entero
            id_fragmento_origen=fragment_id,  # Campo requerido
            texto_entidad="Madrid",
            tipo_entidad="LUGAR",
            relevancia_entidad=0.6,
            metadata_entidad=MetadatosEntidad(tipo="LUGAR", descripcion_estructurada=["sede de la cumbre del clima"])
        )
    ]
    
    return ResultadoFase2Extraccion(
        id_fragmento=fragment_id,
        hechos_extraidos=hechos,
        entidades_extraidas=entidades,
        resumen_extraccion="Extracción exitosa de 2 hechos y 3 entidades",
        metadata_extraccion={"modelo": "mixtral-8x7b-32768"},
        fecha_creacion=datetime.utcnow()
    )


@pytest.fixture
def mock_fase3_resultado(mock_fase2_resultado):
    """Resultado mock de fase 3."""
    fragment_id = mock_fase2_resultado.id_fragmento
    
    citas = [
        CitaTextual(
            id_cita=1,  # Debe ser entero
            id_fragmento_origen=fragment_id,  # Campo requerido
            texto_cita="Este descubrimiento cambiará nuestra forma de entender el calentamiento global",
            persona_citada="Dr. Juan Pérez",
            id_entidad_citada=1,  # Debe ser entero, referencia a la entidad 1
            contexto_cita="Declaración sobre el impacto del descubrimiento",
            metadata_cita=MetadatosCita(contexto="Declaración sobre el impacto del descubrimiento", relevancia=5)
        )
    ]
    
    datos = [
        DatosCuantitativos(
            id_dato_cuantitativo=1,  # Debe ser entero
            id_fragmento_origen=fragment_id,  # Campo requerido
            descripcion_dato="Aumento de temperatura media global",
            valor_dato=1.5,
            unidad_dato="grados Celsius",
            fecha_dato="últimos 50 años",
            metadata_dato=MetadatosDato(categoria="ambiental", tipo_periodo="acumulado", tendencia="aumento")
        )
    ]
    
    return ResultadoFase3CitasDatos(
        id_fragmento=fragment_id,
        citas_textuales_extraidas=citas,
        datos_cuantitativos_extraidos=datos,
        metadata_citas_datos={"procesamiento": "exitoso"},
        fecha_creacion=datetime.utcnow()
    )


@pytest.fixture
def mock_fase4_resultado(mock_fase2_resultado):
    """Resultado mock de fase 4."""
    fragment_id = mock_fase2_resultado.id_fragmento
    
    # Copiar entidades y agregar normalización
    entidades_normalizadas = []
    for entidad in mock_fase2_resultado.entidades_extraidas:
        entidad_norm = EntidadProcesada(
            id_entidad=entidad.id_entidad,
            id_fragmento_origen=fragment_id,  # Campo requerido
            texto_entidad=entidad.texto_entidad,
            tipo_entidad=entidad.tipo_entidad,
            relevancia_entidad=entidad.relevancia_entidad,
            metadata_entidad=entidad.metadata_entidad,
            id_entidad_normalizada=uuid4(),
            nombre_entidad_normalizada=f"{entidad.texto_entidad} (Normalizado)",
            similitud_normalizacion=0.92
        )
        entidades_normalizadas.append(entidad_norm)
    
    # Agregar relaciones en metadata
    relaciones = {
        "hecho_hecho": [
            {
                "hecho_origen_id": 1,  # ID entero del hecho
                "hecho_destino_id": 2,  # ID entero del hecho
                "tipo_relacion": "causa",
                "fuerza_relacion": 7,
                "descripcion_relacion": "El avance científico revela el aumento de temperatura"
            }
        ],
        "entidad_entidad": [
            {
                "entidad_origen_id": 1,  # ID entero de la entidad
                "entidad_destino_id": 2,  # ID entero de la entidad
                "tipo_relacion": "colabora_con",
                "descripcion": "Colaboran en el mismo estudio",
                "fuerza_relacion": 8
            }
        ],
        "contradicciones": []
    }
    
    return ResultadoFase4Normalizacion(
        id_fragmento=fragment_id,
        entidades_normalizadas=entidades_normalizadas,
        resumen_normalizacion="Normalización completada con 3 entidades y 2 relaciones",
        estado_general_normalizacion="completado_ok",
        metadata_normalizacion={"relaciones": relaciones},
        fecha_creacion=datetime.utcnow()
    )


class TestPipelineControllerIntegration:
    """Tests de integración para el PipelineController."""
    
    @pytest.mark.asyncio
    async def test_process_article_complete_flow(
        self, 
        mock_groq_service, 
        mock_supabase_service,
        sample_article_complete,
        mock_fase1_resultado,
        mock_fase2_resultado,
        mock_fase3_resultado,
        mock_fase4_resultado
    ):
        """Test con artículo completo (process_article) - flujo exitoso."""
        
        # Configurar mocks para las fases
        with patch('src.controller.GroqService', return_value=mock_groq_service), \
             patch('src.controller.get_supabase_service', return_value=mock_supabase_service), \
             patch('src.pipeline.fase_1_triaje.ejecutar_fase_1', return_value=mock_fase1_resultado), \
             patch('src.pipeline.fase_2_extraccion.ejecutar_fase_2', return_value=mock_fase2_resultado), \
             patch('src.pipeline.fase_3_citas_datos.ejecutar_fase_3', return_value=mock_fase3_resultado), \
             patch('src.pipeline.fase_4_normalizacion.ejecutar_fase_4', return_value=mock_fase4_resultado), \
             patch('src.services.payload_builder.PayloadBuilder') as mock_payload_builder:
            
            # Configurar mock del PayloadBuilder
            mock_builder_instance = Mock()
            mock_payload = Mock()
            mock_payload.model_dump.return_value = {"payload": "test"}
            mock_builder_instance.construir_payload_fragmento.return_value = mock_payload
            mock_payload_builder.return_value = mock_builder_instance
            
            # Crear controller
            controller = PipelineController()
            
            # Ejecutar procesamiento
            resultado = await controller.process_article(sample_article_complete)
            
            # Verificaciones básicas
            assert resultado is not None
            assert resultado["tipo_procesamiento"] == "articulo_completo"
            assert resultado["numero_fragmentos"] == 1
            assert "articulo_original" in resultado
            assert resultado["articulo_original"]["medio"] == "El Test Diario"
            
            # Verificar que se ejecutaron todas las fases
            assert "fase_1_triaje" in resultado
            assert "fase_2_extraccion" in resultado
            assert "fase_3_citas_datos" in resultado
            assert "fase_4_normalizacion" in resultado
            
            # Verificar métricas
            assert "metricas" in resultado
            metricas = resultado["metricas"]
            assert "tiempos_fases" in metricas
            assert all(fase in metricas["tiempos_fases"] for fase in ["fase1", "fase2", "fase3", "fase4"])
            assert metricas["tasa_exito_general"] == 1.0  # Todas las fases exitosas
            
            # Verificar conteos de elementos
            assert metricas["conteos_elementos"]["hechos_extraidos"] == 2
            assert metricas["conteos_elementos"]["entidades_extraidas"] == 3
            assert metricas["conteos_elementos"]["citas_extraidas"] == 1
            assert metricas["conteos_elementos"]["datos_cuantitativos"] == 1
            assert metricas["conteos_elementos"]["relaciones_hecho_hecho"] == 1
            assert metricas["conteos_elementos"]["relaciones_entidad_entidad"] == 1
            
            # Verificar persistencia
            assert "persistencia" in resultado
            assert resultado["persistencia"]["exitosa"] == True
            assert resultado["persistencia"]["hechos_insertados"] == 2
            assert resultado["persistencia"]["entidades_insertadas"] == 3
            
            # Verificar que no hay advertencias
            assert resultado["procesamiento_parcial"] == False
            assert len(resultado.get("advertencias", [])) == 0
            
            # Verificar métricas del controller
            metrics = controller.get_metrics()
            assert metrics["articulos_procesados"] == 1
            assert metrics["fragmentos_procesados"] == 1
    
    
    @pytest.mark.asyncio
    async def test_process_fragment_direct_flow(
        self,
        mock_groq_service,
        mock_supabase_service,
        sample_fragment_simple,
        mock_fase1_resultado,
        mock_fase2_resultado,
        mock_fase3_resultado,
        mock_fase4_resultado
    ):
        """Test con fragmento (process_fragment) - flujo exitoso."""
        
        with patch('src.controller.GroqService', return_value=mock_groq_service), \
             patch('src.controller.get_supabase_service', return_value=mock_supabase_service), \
             patch('src.pipeline.fase_1_triaje.ejecutar_fase_1', return_value=mock_fase1_resultado), \
             patch('src.pipeline.fase_2_extraccion.ejecutar_fase_2', return_value=mock_fase2_resultado), \
             patch('src.pipeline.fase_3_citas_datos.ejecutar_fase_3', return_value=mock_fase3_resultado), \
             patch('src.pipeline.fase_4_normalizacion.ejecutar_fase_4', return_value=mock_fase4_resultado), \
             patch('src.services.payload_builder.PayloadBuilder') as mock_payload_builder:
            
            # Configurar mock del PayloadBuilder
            mock_builder_instance = Mock()
            mock_payload = Mock()
            mock_payload.model_dump.return_value = {"payload": "test"}
            mock_builder_instance.construir_payload_fragmento.return_value = mock_payload
            mock_payload_builder.return_value = mock_builder_instance
            
            # Crear controller
            controller = PipelineController()
            
            # Ejecutar procesamiento
            resultado = await controller.process_fragment(sample_fragment_simple)
            
            # Verificaciones básicas
            assert resultado is not None
            assert resultado["fragmento_id"] == "test_fragment_123"
            assert "request_id" in resultado
            assert resultado["request_id"].startswith("FRAG-")
            
            # Verificar que se ejecutaron todas las fases
            assert all(f"fase_{i}_" in str(resultado) for i in range(1, 5))
            
            # Verificar procesamiento exitoso
            assert resultado["procesamiento_exitoso"] == True
            assert resultado["procesamiento_parcial"] == False
            
            # Verificar processor stats
            assert "processor_stats" in resultado
            stats = resultado["processor_stats"]
            assert stats["hechos_generados"] == 2
            assert stats["entidades_generadas"] == 3
            assert stats["citas_generadas"] == 1
            assert stats["datos_generados"] == 1
    
    
    @pytest.mark.asyncio
    async def test_process_article_with_fase2_error_fallback(
        self,
        mock_groq_service,
        mock_supabase_service,
        sample_article_complete,
        mock_fase1_resultado,
        mock_fase3_resultado,
        mock_fase4_resultado
    ):
        """Test con error en fase 2 - verifica fallback."""
        
        # Simular error en fase 2
        error_fase2 = Exception("Error simulado en extracción")
        
        with patch('src.controller.GroqService', return_value=mock_groq_service), \
             patch('src.controller.get_supabase_service', return_value=mock_supabase_service), \
             patch('src.pipeline.fase_1_triaje.ejecutar_fase_1', return_value=mock_fase1_resultado), \
             patch('src.pipeline.fase_2_extraccion.ejecutar_fase_2', side_effect=error_fase2), \
             patch('src.pipeline.fase_3_citas_datos.ejecutar_fase_3', return_value=mock_fase3_resultado), \
             patch('src.pipeline.fase_4_normalizacion.ejecutar_fase_4', return_value=mock_fase4_resultado), \
             patch('src.services.payload_builder.PayloadBuilder') as mock_payload_builder:
            
            # Configurar mock del PayloadBuilder
            mock_builder_instance = Mock()
            mock_payload = Mock()
            mock_payload.model_dump.return_value = {"payload": "test"}
            mock_builder_instance.construir_payload_fragmento.return_value = mock_payload
            mock_payload_builder.return_value = mock_builder_instance
            
            # Crear controller
            controller = PipelineController()
            
            # Ejecutar procesamiento
            resultado = await controller.process_article(sample_article_complete)
            
            # Verificar que el procesamiento continuó con fallback
            assert resultado["procesamiento_exitoso"] == True
            assert resultado["procesamiento_parcial"] == True  # Indica uso de fallback
            
            # Verificar advertencias
            assert len(resultado["advertencias"]) > 0
            assert any("Fase 2 ejecutada con fallback" in adv for adv in resultado["advertencias"])
            
            # Verificar métricas
            metricas = resultado["metricas"]
            assert metricas["tasas_exito"]["fase2"] == False  # Fase 2 falló
            assert metricas["tasa_exito_general"] < 1.0  # No todas las fases exitosas
            
            # Verificar que fase 2 tiene datos de fallback
            fase2_data = resultado["fase_2_extraccion"]
            assert fase2_data["metadata_extraccion"]["es_fallback"] == True
            assert len(fase2_data["hechos_extraidos"]) >= 1  # Al menos el hecho del título
    
    
    @pytest.mark.asyncio
    async def test_process_fragment_all_phases_with_errors(
        self,
        mock_groq_service,
        mock_supabase_service,
        sample_fragment_simple
    ):
        """Test con errores en todas las fases - verifica fallbacks múltiples."""
        
        # Simular errores en todas las fases
        error_fase1 = RuntimeError("Error spaCy")
        error_fase2 = Exception("Error Groq extracción")
        error_fase3 = Exception("Error Groq citas")
        error_fase4 = Exception("Error normalización")
        
        # Importar las funciones desde su ubicación correcta
        with patch('src.controller.GroqService', return_value=mock_groq_service), \
             patch('src.controller.get_supabase_service', return_value=mock_supabase_service), \
             patch('src.pipeline.fase_1_triaje.ejecutar_fase_1', side_effect=error_fase1), \
             patch('src.pipeline.fase_2_extraccion.ejecutar_fase_2', side_effect=error_fase2), \
             patch('src.pipeline.fase_3_citas_datos.ejecutar_fase_3', side_effect=error_fase3), \
             patch('src.pipeline.fase_4_normalizacion.ejecutar_fase_4', side_effect=error_fase4), \
             patch('src.services.payload_builder.PayloadBuilder') as mock_payload_builder:
            
            # Configurar mock del PayloadBuilder
            mock_builder_instance = Mock()
            mock_payload = Mock()
            mock_payload.model_dump.return_value = {"payload": "test"}
            mock_builder_instance.construir_payload_fragmento.return_value = mock_payload
            mock_payload_builder.return_value = mock_builder_instance
            
            # Crear controller
            controller = PipelineController()
            
            # Ejecutar procesamiento
            resultado = await controller.process_fragment(sample_fragment_simple)
            
            # Verificar que el procesamiento se completó con múltiples fallbacks
            assert resultado["procesamiento_exitoso"] == True
            assert resultado["procesamiento_parcial"] == True
            
            # Verificar advertencias para cada fase
            advertencias = resultado["advertencias"]
            assert len(advertencias) >= 4  # Una advertencia por cada fase
            assert any("Fase 1 ejecutada con fallback" in adv for adv in advertencias)
            assert any("Fase 2 ejecutada con fallback" in adv for adv in advertencias)
            assert any("Fase 3 ejecutada con fallback" in adv for adv in advertencias)
            assert any("Fase 4 ejecutada con fallback" in adv for adv in advertencias)
            
            # Verificar métricas - todas las fases fallaron
            metricas = resultado["metricas"]
            assert all(not metricas["tasas_exito"][f"fase{i}"] for i in range(1, 5))
            assert metricas["tasa_exito_general"] == 0.0
            
            # Verificar métricas del controller
            metrics = controller.get_metrics()
            assert metrics["errores_totales"] >= 4
    
    
    @pytest.mark.asyncio
    async def test_process_article_persistence_error(
        self,
        mock_groq_service,
        mock_supabase_service,
        sample_article_complete,
        mock_fase1_resultado,
        mock_fase2_resultado,
        mock_fase3_resultado,
        mock_fase4_resultado
    ):
        """Test con error en persistencia - verifica manejo de error."""
        
        # Configurar error en persistencia
        mock_supabase_service.insertar_fragmento_completo.side_effect = Exception("Error de BD")
        
        with patch('src.controller.GroqService', return_value=mock_groq_service), \
             patch('src.controller.get_supabase_service', return_value=mock_supabase_service), \
             patch('src.pipeline.fase_1_triaje.ejecutar_fase_1', return_value=mock_fase1_resultado), \
             patch('src.pipeline.fase_2_extraccion.ejecutar_fase_2', return_value=mock_fase2_resultado), \
             patch('src.pipeline.fase_3_citas_datos.ejecutar_fase_3', return_value=mock_fase3_resultado), \
             patch('src.pipeline.fase_4_normalizacion.ejecutar_fase_4', return_value=mock_fase4_resultado), \
             patch('src.services.payload_builder.PayloadBuilder') as mock_payload_builder:
            
            # Configurar mock del PayloadBuilder
            mock_builder_instance = Mock()
            mock_payload = Mock()
            mock_payload.model_dump.return_value = {"payload": "test"}
            mock_builder_instance.construir_payload_fragmento.return_value = mock_payload
            mock_payload_builder.return_value = mock_builder_instance
            
            # Crear controller
            controller = PipelineController()
            
            # Ejecutar procesamiento
            resultado = await controller.process_article(sample_article_complete)
            
            # Verificar que el procesamiento se completó pero falló la persistencia
            assert resultado["procesamiento_exitoso"] == True
            assert "persistencia" in resultado
            assert resultado["persistencia"]["exitosa"] == False
            assert "Error de BD" in resultado["persistencia"]["error"]
            
            # Verificar advertencias
            assert any("Error en persistencia" in adv for adv in resultado.get("advertencias", []))
    
    
    @pytest.mark.asyncio
    async def test_process_fragment_no_facts_skip_persistence(
        self,
        mock_groq_service,
        mock_supabase_service,
        sample_fragment_simple,
        mock_fase1_resultado,
        mock_fase3_resultado,
        mock_fase4_resultado
    ):
        """Test sin hechos extraídos - verifica que se omite persistencia."""
        
        # Crear resultado de fase 2 sin hechos
        mock_fase2_sin_hechos = ResultadoFase2Extraccion(
            id_fragmento=uuid4(),
            hechos_extraidos=[],  # Sin hechos
            entidades_extraidas=[],  # Sin entidades
            resumen_extraccion="No se encontraron elementos relevantes",
            metadata_extraccion={"sin_contenido": True, "confianza": 0.1},
            fecha_creacion=datetime.utcnow()
        )
        
        with patch('src.controller.GroqService', return_value=mock_groq_service), \
             patch('src.controller.get_supabase_service', return_value=mock_supabase_service), \
             patch('src.pipeline.fase_1_triaje.ejecutar_fase_1', return_value=mock_fase1_resultado), \
             patch('src.pipeline.fase_2_extraccion.ejecutar_fase_2', return_value=mock_fase2_sin_hechos), \
             patch('src.pipeline.fase_3_citas_datos.ejecutar_fase_3', return_value=mock_fase3_resultado), \
             patch('src.pipeline.fase_4_normalizacion.ejecutar_fase_4', return_value=mock_fase4_resultado):
            
            # Crear controller
            controller = PipelineController()
            
            # Ejecutar procesamiento
            resultado = await controller.process_fragment(sample_fragment_simple)
            
            # Verificar que se omitió la persistencia
            assert "persistencia" in resultado
            assert resultado["persistencia"]["exitosa"] == False
            assert "No hay datos suficientes para persistir" in resultado["persistencia"]["mensaje"]
            
            # Verificar que no se llamó a insertar_fragmento_completo
            mock_supabase_service.insertar_fragmento_completo.assert_not_called()
    
    
    @pytest.mark.asyncio
    async def test_metrics_accumulation_multiple_articles(
        self,
        mock_groq_service,
        mock_supabase_service,
        sample_article_complete,
        mock_fase1_resultado,
        mock_fase2_resultado,
        mock_fase3_resultado,
        mock_fase4_resultado
    ):
        """Test de acumulación de métricas con múltiples artículos."""
        
        with patch('src.controller.GroqService', return_value=mock_groq_service), \
             patch('src.controller.get_supabase_service', return_value=mock_supabase_service), \
             patch('src.pipeline.fase_1_triaje.ejecutar_fase_1', return_value=mock_fase1_resultado), \
             patch('src.pipeline.fase_2_extraccion.ejecutar_fase_2', return_value=mock_fase2_resultado), \
             patch('src.pipeline.fase_3_citas_datos.ejecutar_fase_3', return_value=mock_fase3_resultado), \
             patch('src.pipeline.fase_4_normalizacion.ejecutar_fase_4', return_value=mock_fase4_resultado), \
             patch('src.services.payload_builder.PayloadBuilder') as mock_payload_builder:
            
            # Configurar mock del PayloadBuilder
            mock_builder_instance = Mock()
            mock_payload = Mock()
            mock_payload.model_dump.return_value = {"payload": "test"}
            mock_builder_instance.construir_payload_fragmento.return_value = mock_payload
            mock_payload_builder.return_value = mock_builder_instance
            
            # Crear controller
            controller = PipelineController()
            
            # Procesar 3 artículos
            for i in range(3):
                article = sample_article_complete.copy()
                article["titular"] = f"Artículo de prueba {i+1}"
                await controller.process_article(article)
            
            # Verificar métricas acumuladas
            metrics = controller.get_metrics()
            assert metrics["articulos_procesados"] == 3
            assert metrics["fragmentos_procesados"] == 3
            assert metrics["tiempo_total_procesamiento"] > 0
            assert metrics["tiempo_promedio_por_fragmento"] > 0
            assert metrics["tasa_error"] == 0.0  # Sin errores


# Función helper para ejecutar tests individualmente
def run_specific_test(test_name):
    """
    Ejecuta un test específico.
    Uso: python test_controller_integration.py TestPipelineControllerIntegration::test_process_article_complete_flow
    """
    import subprocess
    cmd = f"pytest {__file__}::{test_name} -v"
    subprocess.run(cmd, shell=True)


if __name__ == "__main__":
    # Si se ejecuta directamente, mostrar instrucciones
    print("Test de integración del PipelineController")
    print("==========================================")
    print("\nPara ejecutar todos los tests:")
    print("  pytest tests/test_controller_integration.py -v")
    print("\nPara ejecutar un test específico:")
    print("  pytest tests/test_controller_integration.py::TestPipelineControllerIntegration::test_process_article_complete_flow -v")
    print("\nTests disponibles:")
    print("  - test_process_article_complete_flow")
    print("  - test_process_fragment_direct_flow")
    print("  - test_process_article_with_fase2_error_fallback")
    print("  - test_process_fragment_all_phases_with_errors")
    print("  - test_process_article_persistence_error")
    print("  - test_process_fragment_no_facts_skip_persistence")
    print("  - test_metrics_accumulation_multiple_articles")
