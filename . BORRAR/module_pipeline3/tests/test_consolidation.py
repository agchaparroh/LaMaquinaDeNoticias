"""
Test Suite: Consolidation Service - Sistema de Consolidación Cross-Chunk
=======================================================================

Suite de pruebas específica para el servicio de consolidación que valida:
- Consolidación de entidades duplicadas entre chunks
- Consolidación de hechos similares
- Consolidación de datos cuantitativos
- Consolidación de citas textuales
- Algoritmos de similitud y deduplicación
- Preservación de calidad y contexto
- Configuración de thresholds de similitud

Estas pruebas aseguran que el sistema de consolidación elimina duplicados
efectivamente mientras preserva la información más completa y precisa.
"""

import pytest
from unittest.mock import Mock, patch
from typing import List, Dict, Any
import json

# Imports del sistema de consolidación
from src.services.consolidation_service import ConsolidationService
from src.utils.similarity_algorithms import (
    calculate_text_similarity,
    calculate_entity_similarity, 
    calculate_semantic_similarity,
    normalize_text_for_comparison
)

# Imports de configuración
from src.config import pipeline_config, get_processing_config


# =============================================================================
# FIXTURES PARA DATOS DE PRUEBA
# =============================================================================

@pytest.fixture
def consolidation_service():
    """Instancia del servicio de consolidación."""
    return ConsolidationService()

@pytest.fixture
def entidades_duplicadas():
    """Entidades duplicadas para testing de consolidación."""
    return [
        # Chunk 1
        [
            {"id": 1, "nombre": "Juan Pérez", "tipo": "PERSONA", "descripcion": "Presidente"},
            {"id": 2, "nombre": "Ministerio de Economía", "tipo": "ORGANIZACION", "descripcion": "Organismo gubernamental"}
        ],
        # Chunk 2  
        [
            {"id": 3, "nombre": "Juan Perez", "tipo": "PERSONA", "descripcion": "Presidente de la República"},  # Sin tilde, más descripción
            {"id": 4, "nombre": "María González", "tipo": "PERSONA", "descripcion": "Ministra"}
        ],
        # Chunk 3
        [
            {"id": 5, "nombre": "J. Pérez", "tipo": "PERSONA", "descripcion": ""},  # Versión abreviada
            {"id": 6, "nombre": "Min. Economía", "tipo": "ORGANIZACION", "descripcion": ""}  # Versión abreviada
        ]
    ]

@pytest.fixture
def hechos_similares():
    """Hechos similares para testing de consolidación."""
    return [
        # Chunk 1
        [
            {"id": 1, "contenido": "El presidente se reunió con el ministro de economía", "tipo_hecho": "EVENTO", "fecha": "2024-01-15"},
            {"id": 2, "contenido": "Se anunció un aumento del presupuesto", "tipo_hecho": "ANUNCIO", "fecha": "2024-01-15"}
        ],
        # Chunk 2
        [
            {"id": 3, "contenido": "Reunión presidencial con ministro económico", "tipo_hecho": "EVENTO", "fecha": "2024-01-15"},  # Similar al ID 1
            {"id": 4, "contenido": "Nueva inversión en infraestructura", "tipo_hecho": "ANUNCIO", "fecha": "2024-01-15"}
        ],
        # Chunk 3
        [
            {"id": 5, "contenido": "El mandatario y el titular de economía se encontraron", "tipo_hecho": "EVENTO", "fecha": "2024-01-15"},  # Similar al ID 1
            {"id": 6, "contenido": "Incremento presupuestario aprobado", "tipo_hecho": "ANUNCIO", "fecha": "2024-01-15"}  # Similar al ID 2
        ]
    ]

@pytest.fixture
def datos_cuantitativos_duplicados():
    """Datos cuantitativos con duplicados para testing."""
    return [
        # Chunk 1
        [
            {"id": 1, "valor": "500 millones", "unidad": "pesos", "concepto": "inversión infraestructura", "contexto": "presupuesto adicional"},
            {"id": 2, "valor": "3.5", "unidad": "porcentaje", "concepto": "crecimiento PIB", "contexto": "este trimestre"}
        ],
        # Chunk 2
        [
            {"id": 3, "valor": "500000000", "unidad": "pesos", "concepto": "inversión en infraestructura", "contexto": "presupuesto extra"},  # Mismo valor, diferente formato
            {"id": 4, "valor": "2500", "unidad": "empleos", "concepto": "empleos directos", "contexto": "generados por inversión"}
        ],
        # Chunk 3
        [
            {"id": 5, "valor": "3.5%", "unidad": "", "concepto": "PIB", "contexto": "crecimiento trimestral"},  # Similar al ID 2
            {"id": 6, "valor": "4.2", "unidad": "porcentaje", "concepto": "inflación", "contexto": "mensual"}
        ]
    ]

@pytest.fixture
def citas_textuales_similares():
    """Citas textuales similares para testing."""
    return [
        # Chunk 1
        [
            {"id": 1, "texto": "Estamos comprometidos con el crecimiento", "autor": "Juan Pérez", "contexto": "rueda de prensa"},
            {"id": 2, "texto": "Esta medida estimulará la inversión privada", "autor": "María González", "contexto": "presentación"}
        ],
        # Chunk 2
        [
            {"id": 3, "texto": "Estamos comprometidos con el crecimiento económico", "autor": "Juan Perez", "contexto": "conferencia"},  # Similar pero más específica
            {"id": 4, "texto": "Queremos que las PyMEs sean el motor", "autor": "Roberto Silva", "contexto": "anuncio"}
        ],
        # Chunk 3
        [
            {"id": 5, "texto": "\"Estamos comprometidos con el crecimiento\"", "autor": "Presidente", "contexto": "declaraciones"},  # Con comillas y autor genérico
            {"id": 6, "texto": "La medida estimulará inversión", "autor": "González", "contexto": "rueda de prensa"}  # Parafraseo del ID 2
        ]
    ]


# =============================================================================
# TESTS DE CONSOLIDACIÓN DE ENTIDADES
# =============================================================================

class TestEntityConsolidation:
    """Tests de consolidación de entidades."""
    
    def test_consolidate_identical_entities(self, consolidation_service):
        """Test consolidación de entidades idénticas."""
        entidades_identicas = [
            [{"id": 1, "nombre": "Juan Pérez", "tipo": "PERSONA"}],
            [{"id": 2, "nombre": "Juan Pérez", "tipo": "PERSONA"}]
        ]
        
        resultado = consolidation_service.consolidate_entities(entidades_identicas)
        
        assert len(resultado) == 1, "Entidades idénticas deberían consolidarse en una"
        assert resultado[0]["nombre"] == "Juan Pérez"
        assert resultado[0]["id"] == 1  # Debería mantener el primer ID
    
    def test_consolidate_similar_entities_with_threshold(self, consolidation_service, entidades_duplicadas):
        """Test consolidación con threshold de similitud."""
        resultado = consolidation_service.consolidate_entities(entidades_duplicadas)
        
        # Debería consolidar Juan Pérez / Juan Perez / J. Pérez
        # Y Ministerio de Economía / Min. Economía
        assert len(resultado) == 3, "Deberían quedar 3 entidades: Juan Pérez consolidado, Ministerio consolidado, María González"
        
        # Verificar que se preservó la mejor información
        juan_perez = next((e for e in resultado if "Juan" in e["nombre"]), None)
        assert juan_perez is not None
        assert len(juan_perez["descripcion"]) > 0, "Debería preservar la descripción más completa"
    
    def test_preserve_best_quality_entity(self, consolidation_service):
        """Test que se preserva la entidad de mejor calidad."""
        entidades_calidad = [
            [{"id": 1, "nombre": "J.P.", "tipo": "PERSONA", "descripcion": ""}],
            [{"id": 2, "nombre": "Juan Pérez", "tipo": "PERSONA", "descripcion": "Presidente de la República Argentina"}]
        ]
        
        resultado = consolidation_service.consolidate_entities(entidades_calidad)
        
        assert len(resultado) == 1
        entity = resultado[0]
        assert entity["nombre"] == "Juan Pérez"  # Nombre completo
        assert len(entity["descripcion"]) > 10   # Descripción completa
    
    def test_entity_consolidation_preserves_relationships(self, consolidation_service):
        """Test que la consolidación preserva relaciones."""
        entidades_con_relaciones = [
            [{"id": 1, "nombre": "Juan Pérez", "tipo": "PERSONA", "cargo": "Presidente"}],
            [{"id": 2, "nombre": "Juan Perez", "tipo": "PERSONA", "organizacion": "Gobierno Nacional"}]
        ]
        
        resultado = consolidation_service.consolidate_entities(entidades_con_relaciones)
        
        assert len(resultado) == 1
        entity = resultado[0]
        # Debería combinar información de ambas entidades
        assert "cargo" in entity or "organizacion" in entity
    
    def test_different_entity_types_not_consolidated(self, consolidation_service):
        """Test que entidades de diferentes tipos no se consolidan."""
        entidades_diferentes = [
            [{"id": 1, "nombre": "Banco Nacional", "tipo": "ORGANIZACION"}],
            [{"id": 2, "nombre": "Banco Nacional", "tipo": "LUGAR"}]  # Mismo nombre, diferente tipo
        ]
        
        resultado = consolidation_service.consolidate_entities(entidades_diferentes)
        
        assert len(resultado) == 2, "Entidades de diferentes tipos no deberían consolidarse"


# =============================================================================
# TESTS DE CONSOLIDACIÓN DE HECHOS
# =============================================================================

class TestFactConsolidation:
    """Tests de consolidación de hechos."""
    
    def test_consolidate_similar_facts(self, consolidation_service, hechos_similares):
        """Test consolidación de hechos similares."""
        resultado = consolidation_service.consolidate_facts(hechos_similares)
        
        # Deberían consolidarse los hechos sobre reunión presidencial
        # Y posiblemente los de presupuesto/inversión
        assert len(resultado) < 6, "Algunos hechos similares deberían consolidarse"
        
        # Verificar que se mantiene información esencial
        contenidos = [h["contenido"] for h in resultado]
        assert any("reunión" in c.lower() or "encontraron" in c.lower() for c in contenidos)
    
    def test_facts_with_same_content_consolidated(self, consolidation_service):
        """Test que hechos con contenido idéntico se consolidan."""
        hechos_identicos = [
            [{"id": 1, "contenido": "Se anunció una nueva medida económica", "tipo_hecho": "ANUNCIO"}],
            [{"id": 2, "contenido": "Se anunció una nueva medida económica", "tipo_hecho": "ANUNCIO"}]
        ]
        
        resultado = consolidation_service.consolidate_facts(hechos_identicos)
        
        assert len(resultado) == 1, "Hechos idénticos deberían consolidarse"
    
    def test_facts_different_dates_not_consolidated(self, consolidation_service):
        """Test que hechos con fechas diferentes no se consolidan."""
        hechos_fechas_diferentes = [
            [{"id": 1, "contenido": "Reunión presidencial", "tipo_hecho": "EVENTO", "fecha": "2024-01-15"}],
            [{"id": 2, "contenido": "Reunión presidencial", "tipo_hecho": "EVENTO", "fecha": "2024-01-16"}]
        ]
        
        resultado = consolidation_service.consolidate_facts(hechos_fechas_diferentes)
        
        assert len(resultado) == 2, "Hechos con fechas diferentes no deberían consolidarse"
    
    def test_fact_consolidation_preserves_context(self, consolidation_service):
        """Test que la consolidación preserva contexto importante."""
        hechos_con_contexto = [
            [{"id": 1, "contenido": "Anuncio económico", "tipo_hecho": "ANUNCIO", "ubicacion": "Casa de Gobierno"}],
            [{"id": 2, "contenido": "Anuncio sobre economía", "tipo_hecho": "ANUNCIO", "participantes": ["Presidente", "Ministro"]}]
        ]
        
        resultado = consolidation_service.consolidate_facts(hechos_con_contexto)
        
        # Si se consolidan, debería preservar contexto de ambos
        if len(resultado) == 1:
            fact = resultado[0]
            assert "ubicacion" in fact or "participantes" in fact


# =============================================================================
# TESTS DE CONSOLIDACIÓN DE DATOS CUANTITATIVOS
# =============================================================================

class TestQuantitativeDataConsolidation:
    """Tests de consolidación de datos cuantitativos."""
    
    def test_consolidate_same_values_different_formats(self, consolidation_service, datos_cuantitativos_duplicados):
        """Test consolidación de valores iguales en diferentes formatos."""
        resultado = consolidation_service.consolidate_quantitative_data(datos_cuantitativos_duplicados)
        
        # 500 millones y 500000000 deberían consolidarse
        # 3.5% y 3.5 porcentaje deberían consolidarse
        valores_inversion = [d for d in resultado if "inversión" in d["concepto"].lower() or "infraestructura" in d["concepto"].lower()]
        assert len(valores_inversion) == 1, "Valores de inversión en diferentes formatos deberían consolidarse"
    
    def test_preserve_most_descriptive_data_format(self, consolidation_service):
        """Test que se preserva el formato más descriptivo."""
        datos_formatos = [
            [{"id": 1, "valor": "3.5", "unidad": "%", "concepto": "PIB", "contexto": ""}],
            [{"id": 2, "valor": "3.5", "unidad": "porcentaje", "concepto": "crecimiento PIB", "contexto": "trimestral"}]
        ]
        
        resultado = consolidation_service.consolidate_quantitative_data(datos_formatos)
        
        assert len(resultado) == 1
        data = resultado[0]
        assert data["unidad"] == "porcentaje"  # Más descriptivo que %
        assert len(data["concepto"]) > 3       # Concepto más descriptivo
        assert len(data["contexto"]) > 0       # Contexto preservado
    
    def test_different_values_not_consolidated(self, consolidation_service):
        """Test que valores diferentes no se consolidan."""
        datos_diferentes = [
            [{"id": 1, "valor": "3.5", "unidad": "porcentaje", "concepto": "PIB"}],
            [{"id": 2, "valor": "4.2", "unidad": "porcentaje", "concepto": "inflación"}]
        ]
        
        resultado = consolidation_service.consolidate_quantitative_data(datos_diferentes)
        
        assert len(resultado) == 2, "Valores diferentes no deberían consolidarse"
    
    def test_numerical_normalization(self, consolidation_service):
        """Test normalización numérica para comparación."""
        # Test de la función interna de normalización
        assert consolidation_service._normalize_numerical_value("500 millones") == 500000000
        assert consolidation_service._normalize_numerical_value("3.5%") == 3.5
        assert consolidation_service._normalize_numerical_value("2,500") == 2500


# =============================================================================
# TESTS DE CONSOLIDACIÓN DE CITAS TEXTUALES
# =============================================================================

class TestQuoteConsolidation:
    """Tests de consolidación de citas textuales."""
    
    def test_consolidate_similar_quotes(self, consolidation_service, citas_textuales_similares):
        """Test consolidación de citas similares."""
        resultado = consolidation_service.consolidate_quotes(citas_textuales_similares)
        
        # Citas sobre "comprometidos con el crecimiento" deberían consolidarse
        citas_crecimiento = [c for c in resultado if "crecimiento" in c["texto"].lower()]
        assert len(citas_crecimiento) == 1, "Citas similares sobre crecimiento deberían consolidarse"
    
    def test_preserve_exact_quote_text(self, consolidation_service):
        """Test que se preserva el texto exacto de la cita."""
        citas_precision = [
            [{"id": 1, "texto": "Estamos comprometidos", "autor": "Juan Pérez"}],
            [{"id": 2, "texto": "\"Estamos comprometidos con el crecimiento\"", "autor": "Juan Pérez"}]  # Más completa y con comillas
        ]
        
        resultado = consolidation_service.consolidate_quotes(citas_precision)
        
        assert len(resultado) == 1
        quote = resultado[0]
        assert "crecimiento" in quote["texto"], "Debería preservar la cita más completa"
        assert "\"" in quote["texto"], "Debería preservar las comillas"
    
    def test_quotes_different_authors_not_consolidated(self, consolidation_service):
        """Test que citas de diferentes autores no se consolidan."""
        citas_diferentes_autores = [
            [{"id": 1, "texto": "Estamos comprometidos", "autor": "Juan Pérez"}],
            [{"id": 2, "texto": "Estamos comprometidos", "autor": "María González"}]
        ]
        
        resultado = consolidation_service.consolidate_quotes(citas_diferentes_autores)
        
        assert len(resultado) == 2, "Citas del mismo texto pero diferentes autores no deberían consolidarse"
    
    def test_quote_context_preservation(self, consolidation_service):
        """Test preservación de contexto en citas."""
        citas_con_contexto = [
            [{"id": 1, "texto": "Medida importante", "autor": "Presidente", "contexto": "rueda de prensa", "fecha": "2024-01-15"}],
            [{"id": 2, "texto": "Medida muy importante", "autor": "Presidente", "contexto": "conferencia magistral", "fecha": "2024-01-15"}]
        ]
        
        resultado = consolidation_service.consolidate_quotes(citas_con_contexto)
        
        if len(resultado) == 1:
            quote = resultado[0]
            assert quote["contexto"] is not None
            assert quote["fecha"] is not None


# =============================================================================
# TESTS DE ALGORITMOS DE SIMILITUD
# =============================================================================

class TestSimilarityAlgorithms:
    """Tests de algoritmos de similitud."""
    
    def test_text_similarity_calculation(self):
        """Test cálculo de similitud textual."""
        text1 = "El presidente se reunió con el ministro"
        text2 = "Reunión presidencial con ministro"
        text3 = "Completamente diferente"
        
        sim_similar = calculate_text_similarity(text1, text2)
        sim_different = calculate_text_similarity(text1, text3)
        
        assert sim_similar > sim_different
        assert 0 <= sim_similar <= 1
        assert 0 <= sim_different <= 1
    
    def test_entity_similarity_with_normalization(self):
        """Test similitud de entidades con normalización."""
        entity1 = {"nombre": "Juan Pérez", "tipo": "PERSONA"}
        entity2 = {"nombre": "Juan Perez", "tipo": "PERSONA"}  # Sin tilde
        entity3 = {"nombre": "María González", "tipo": "PERSONA"}
        
        sim_similar = calculate_entity_similarity(entity1, entity2)
        sim_different = calculate_entity_similarity(entity1, entity3)
        
        assert sim_similar > sim_different
        assert sim_similar > 0.8  # Deberían ser muy similares
    
    def test_semantic_similarity_integration(self):
        """Test integración de similitud semántica."""
        if hasattr(calculate_semantic_similarity, '__call__'):
            text1 = "presidente"
            text2 = "mandatario"
            text3 = "computadora"
            
            sim_similar = calculate_semantic_similarity(text1, text2)
            sim_different = calculate_semantic_similarity(text1, text3)
            
            assert sim_similar > sim_different
    
    def test_text_normalization(self):
        """Test normalización de texto."""
        text_with_accents = "José María Azñar"
        text_without_accents = "Jose Maria Aznar"
        
        norm1 = normalize_text_for_comparison(text_with_accents)
        norm2 = normalize_text_for_comparison(text_without_accents)
        
        assert norm1.lower() == norm2.lower()  # Deberían normalizarse igual


# =============================================================================
# TESTS DE CONFIGURACIÓN Y THRESHOLDS
# =============================================================================

class TestConsolidationConfiguration:
    """Tests de configuración del sistema de consolidación."""
    
    def test_similarity_threshold_configuration(self, consolidation_service):
        """Test configuración del threshold de similitud."""
        config = get_processing_config()
        
        # Verificar que el threshold se puede leer
        original_threshold = consolidation_service.similarity_threshold
        assert 0 <= original_threshold <= 1
        
        # Verificar que se puede modificar
        consolidation_service.similarity_threshold = 0.9
        assert consolidation_service.similarity_threshold == 0.9
        
        # Restaurar
        consolidation_service.similarity_threshold = original_threshold
    
    def test_threshold_affects_consolidation_behavior(self, consolidation_service):
        """Test que el threshold afecta el comportamiento de consolidación."""
        entidades_moderamente_similares = [
            [{"id": 1, "nombre": "Juan Pérez", "tipo": "PERSONA"}],
            [{"id": 2, "nombre": "J. Pérez", "tipo": "PERSONA"}]
        ]
        
        # Con threshold bajo (permisivo)
        consolidation_service.similarity_threshold = 0.5
        resultado_permisivo = consolidation_service.consolidate_entities(entidades_moderamente_similares)
        
        # Con threshold alto (estricto)  
        consolidation_service.similarity_threshold = 0.95
        resultado_estricto = consolidation_service.consolidate_entities(entidades_moderamente_similares)
        
        # El threshold debería afectar si se consolidan o no
        assert len(resultado_permisivo) <= len(resultado_estricto)
    
    def test_configuration_validation(self, consolidation_service):
        """Test validación de configuración."""
        # Threshold inválido debería ser rechazado
        with pytest.raises(ValueError):
            consolidation_service.similarity_threshold = 1.5  # > 1.0
        
        with pytest.raises(ValueError):
            consolidation_service.similarity_threshold = -0.1  # < 0.0


# =============================================================================
# TESTS DE RENDIMIENTO DE CONSOLIDACIÓN
# =============================================================================

class TestConsolidationPerformance:
    """Tests de rendimiento del sistema de consolidación."""
    
    def test_consolidation_with_large_datasets(self, consolidation_service):
        """Test consolidación con datasets grandes."""
        # Generar dataset grande con duplicados
        large_entities = []
        for chunk in range(10):  # 10 chunks
            chunk_entities = []
            for i in range(50):  # 50 entidades por chunk
                chunk_entities.append({
                    "id": chunk * 50 + i + 1,
                    "nombre": f"Entidad {i % 10}",  # 10 nombres únicos -> duplicados
                    "tipo": "PERSONA"
                })
            large_entities.append(chunk_entities)
        
        # La consolidación debería completarse en tiempo razonable
        import time
        start_time = time.time()
        resultado = consolidation_service.consolidate_entities(large_entities)
        processing_time = time.time() - start_time
        
        # Verificar que se consolidaron correctamente
        assert len(resultado) == 10, "Deberían quedar 10 entidades únicas"
        assert processing_time < 5.0, f"Consolidación demasiado lenta: {processing_time:.2f}s"
    
    def test_memory_usage_during_consolidation(self, consolidation_service):
        """Test uso de memoria durante consolidación."""
        # Crear dataset que podría causar problemas de memoria
        memory_intensive_data = []
        for chunk in range(5):
            chunk_data = []
            for i in range(100):
                chunk_data.append({
                    "id": chunk * 100 + i + 1,
                    "nombre": f"Entidad con descripción muy larga que consume memoria {i}",
                    "tipo": "PERSONA",
                    "descripcion": "A" * 1000  # 1KB por descripción
                })
            memory_intensive_data.append(chunk_data)
        
        # La consolidación debería manejar esto sin problemas
        try:
            resultado = consolidation_service.consolidate_entities(memory_intensive_data)
            assert len(resultado) <= 500, "Consolidación completada exitosamente"
        except MemoryError:
            pytest.fail("Consolidación causó problemas de memoria")


# =============================================================================
# TESTS DE INTEGRACIÓN CONSOLIDACIÓN + PIPELINE
# =============================================================================

class TestConsolidationPipelineIntegration:
    """Tests de integración entre consolidación y pipeline."""
    
    def test_consolidation_maintains_sequential_ids(self, consolidation_service):
        """Test que la consolidación mantiene IDs secuenciales."""
        entidades_chunks = [
            [{"id": 1, "nombre": "Juan", "tipo": "PERSONA"}],
            [{"id": 5, "nombre": "María", "tipo": "PERSONA"}],  # Gap en IDs
            [{"id": 8, "nombre": "Carlos", "tipo": "PERSONA"}]
        ]
        
        resultado = consolidation_service.consolidate_entities(entidades_chunks)
        
        # Los IDs deberían ser secuenciales después de consolidación
        ids = [e["id"] for e in resultado]
        assert ids == list(range(1, len(resultado) + 1))
    
    def test_consolidation_preserves_metadata(self, consolidation_service):
        """Test que la consolidación preserva metadatos importantes."""
        entidades_con_metadata = [
            [{"id": 1, "nombre": "Juan", "tipo": "PERSONA", "_chunk_id": 0, "_confidence": 0.9}],
            [{"id": 2, "nombre": "Juan", "tipo": "PERSONA", "_chunk_id": 1, "_confidence": 0.95}]
        ]
        
        resultado = consolidation_service.consolidate_entities(entidades_con_metadata)
        
        assert len(resultado) == 1
        entity = resultado[0]
        # Debería preservar la mayor confianza y agregar información de chunks
        assert entity.get("_confidence", 0) >= 0.9
        assert "_consolidated_from_chunks" in entity or "_chunk_id" in entity


if __name__ == "__main__":
    # Ejecutar tests cuando se ejecuta directamente
    pytest.main([__file__, "-v", "--tb=short"])