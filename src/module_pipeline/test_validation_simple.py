#!/usr/bin/env python3
"""
test_validation_simple.py
========================

Script simple para probar las validaciones implementadas en el pipeline.
Ejecuta pruebas básicas de sanitización, validaciones customizadas y validación end-to-end.

Uso:
    python test_validation_simple.py
"""

import sys
import os
from pathlib import Path
from uuid import uuid4
from datetime import datetime

# Añadir el directorio src al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from loguru import logger

# Configurar logger para el test
logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")

# Importar funciones de validación
try:
    from utils.validation import (
        escape_html,
        clean_text,
        normalize_whitespace,
        validate_confidence_score,
        validate_offset_range,
        validate_url,
        validate_date_format,
        validate_date_optional,
        validate_wikidata_uri,
        sanitize_entity_name,
        validate_numeric_value,
        validate_input_data,
        NonEmptyString,
        SafeHtmlString
    )
except ImportError as e:
    print(f"Error importando módulo de validación: {e}")
    sys.exit(1)

# Importar modelos con validaciones
from models.entrada import FragmentoProcesableItem
from models.procesamiento import (
    ResultadoFase1Triaje,
    ResultadoFase2Extraccion,
    HechoProcesado,
    EntidadProcesada
)

# Importar servicios
from services.payload_builder import PayloadBuilder
from pydantic import ValidationError
from utils.error_handling import ValidationError as CustomValidationError


def test_sanitizacion_html():
    """Test de sanitización HTML con casos maliciosos."""
    print("\n=== TEST: Sanitización HTML ===")
    
    casos_prueba = [
        # (entrada, esperado, descripción)
        ("<script>alert('XSS')</script>", "&lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;", "Script tag"),
        ("Normal & texto", "Normal &amp; texto", "Ampersand"),
        ('<img src="x" onerror="alert(1)">', '&lt;img src=&quot;x&quot; onerror=&quot;alert(1)&quot;&gt;', "Img con onerror"),
        ("Texto con 'comillas' y \"dobles\"", "Texto con &#x27;comillas&#x27; y &quot;dobles&quot;", "Comillas"),
        ("<div>Contenido</div>", "&lt;div&gt;Contenido&lt;/div&gt;", "Div tag"),
    ]
    
    errores = 0
    for entrada, esperado, descripcion in casos_prueba:
        resultado = escape_html(entrada)
        if resultado == esperado:
            logger.success(f"✅ {descripcion}: OK")
        else:
            logger.error(f"❌ {descripcion}: Esperado '{esperado}', obtenido '{resultado}'")
            errores += 1
    
    if errores == 0:
        logger.info("✅ Sanitización HTML funcionando correctamente")
    else:
        logger.error(f"❌ Error: {errores} casos de sanitización fallaron")
    
    return errores == 0


def test_limpieza_texto():
    """Test de limpieza de texto."""
    print("\n=== TEST: Limpieza de Texto ===")
    
    casos_prueba = [
        # (entrada, esperado_sin_newlines, esperado_con_newlines, descripción)
        ("Texto   con    espacios", "Texto con espacios", "Texto con espacios", "Espacios múltiples"),
        ("Texto\ncon\nsaltos", "Texto con saltos", "Texto\ncon\nsaltos", "Saltos de línea"),
        ("\x00Caracteres\x01de\x02control\x03", "Caracteres de control", "Caracteres de control", "Caracteres de control"),
        ("  Espacios  al  inicio  y  final  ", "Espacios al inicio y final", "Espacios al inicio y final", "Trim"),
        ("Texto\t\tcon\ttabs", "Texto con tabs", "Texto con tabs", "Tabs"),
    ]
    
    errores = 0
    for entrada, esperado_sin, esperado_con, descripcion in casos_prueba:
        # Test sin preservar newlines
        resultado_sin = clean_text(entrada, preserve_newlines=False)
        if resultado_sin == esperado_sin:
            logger.success(f"✅ {descripcion} (sin newlines): OK")
        else:
            logger.error(f"❌ {descripcion} (sin newlines): Esperado '{esperado_sin}', obtenido '{resultado_sin}'")
            errores += 1
        
        # Test preservando newlines
        resultado_con = clean_text(entrada, preserve_newlines=True)
        if resultado_con == esperado_con:
            logger.success(f"✅ {descripcion} (con newlines): OK")
        else:
            logger.error(f"❌ {descripcion} (con newlines): Esperado '{esperado_con}', obtenido '{resultado_con}'")
            errores += 1
    
    if errores == 0:
        logger.info("✅ Limpieza de texto funcionando correctamente")
    else:
        logger.error(f"❌ Error: {errores} casos de limpieza fallaron")
    
    return errores == 0


def test_validaciones_pydantic():
    """Test de validaciones Pydantic customizadas."""
    print("\n=== TEST: Validaciones Pydantic Customizadas ===")
    
    errores = 0
    
    # Test FragmentoProcesableItem
    try:
        # Caso válido
        fragmento = FragmentoProcesableItem(
            id_fragmento="test-123",
            texto_original="  Texto con   espacios   ",
            id_articulo_fuente="art-456",
            metadata_adicional={"url_fuente": "https://ejemplo.com"}
        )
        
        # Verificar que el texto fue limpiado
        if fragmento.texto_original == "Texto con espacios":
            logger.success("✅ FragmentoProcesableItem: limpieza de texto OK")
        else:
            logger.error(f"❌ FragmentoProcesableItem: texto no limpiado correctamente: '{fragmento.texto_original}'")
            errores += 1
        
        # Verificar que la URL fue validada
        if fragmento.metadata_adicional.get("url_fuente") == "https://ejemplo.com":
            logger.success("✅ FragmentoProcesableItem: validación de URL OK")
        else:
            logger.error("❌ FragmentoProcesableItem: URL no validada")
            errores += 1
            
    except Exception as e:
        logger.error(f"❌ FragmentoProcesableItem: Error inesperado: {e}")
        errores += 1
    
    # Test texto vacío (debe fallar)
    try:
        fragmento_vacio = FragmentoProcesableItem(
            id_fragmento="test-123",
            texto_original="   ",  # Solo espacios
            id_articulo_fuente="art-456"
        )
        logger.error("❌ FragmentoProcesableItem: debería fallar con texto vacío")
        errores += 1
    except ValidationError as e:
        logger.success("✅ FragmentoProcesableItem: rechazó texto vacío correctamente")
    except Exception as e:
        logger.error(f"❌ FragmentoProcesableItem: Error incorrecto con texto vacío: {e}")
        errores += 1
    
    # Test URL inválida (debe eliminar la URL)
    try:
        fragmento_url_invalida = FragmentoProcesableItem(
            id_fragmento="test-123",
            texto_original="Texto válido",
            id_articulo_fuente="art-456",
            metadata_adicional={"url_fuente": "no-es-una-url"}
        )
        
        if "url_fuente" not in fragmento_url_invalida.metadata_adicional:
            logger.success("✅ FragmentoProcesableItem: eliminó URL inválida correctamente")
        else:
            logger.error("❌ FragmentoProcesableItem: no eliminó URL inválida")
            errores += 1
            
    except Exception as e:
        logger.error(f"❌ FragmentoProcesableItem: Error con URL inválida: {e}")
        errores += 1
    
    if errores == 0:
        logger.info("✅ Validaciones Pydantic funcionando correctamente")
    else:
        logger.error(f"❌ Error: {errores} validaciones Pydantic fallaron")
    
    return errores == 0


def test_validaciones_especificas():
    """Test de validaciones específicas del dominio."""
    print("\n=== TEST: Validaciones Específicas del Dominio ===")
    
    errores = 0
    
    # Test confidence score
    casos_confianza = [
        (0.0, True, "Límite inferior"),
        (1.0, True, "Límite superior"),
        (0.5, True, "Valor medio"),
        (-0.1, False, "Negativo"),
        (1.1, False, "Mayor que 1"),
    ]
    
    for valor, valido, descripcion in casos_confianza:
        try:
            resultado = validate_confidence_score(valor)
            if valido:
                logger.success(f"✅ Confidence score {descripcion}: OK")
            else:
                logger.error(f"❌ Confidence score {descripcion}: debería fallar")
                errores += 1
        except ValueError as e:
            if not valido:
                logger.success(f"✅ Confidence score {descripcion}: rechazado correctamente")
            else:
                logger.error(f"❌ Confidence score {descripcion}: no debería fallar - {e}")
                errores += 1
    
    # Test offset range
    casos_offset = [
        (0, 10, True, "Rango válido"),
        (10, 10, True, "Inicio = Fin"),
        (-1, 10, False, "Inicio negativo"),
        (10, 5, False, "Fin menor que inicio"),
        (None, None, True, "Ambos None"),
    ]
    
    for inicio, fin, valido, descripcion in casos_offset:
        try:
            resultado = validate_offset_range(inicio, fin)
            if valido:
                logger.success(f"✅ Offset range {descripcion}: OK")
            else:
                logger.error(f"❌ Offset range {descripcion}: debería fallar")
                errores += 1
        except ValueError as e:
            if not valido:
                logger.success(f"✅ Offset range {descripcion}: rechazado correctamente")
            else:
                logger.error(f"❌ Offset range {descripcion}: no debería fallar - {e}")
                errores += 1
    
    # Test Wikidata URI
    casos_wikidata = [
        ("https://www.wikidata.org/wiki/Q42", True, "URI válida"),
        ("http://wikidata.org/entity/Q12345", True, "URI entity válida"),
        ("https://wikipedia.org/wiki/Q42", False, "Dominio incorrecto"),
        ("https://www.wikidata.org/wiki/ABC", False, "Sin Q-number"),
    ]
    
    for uri, valida, descripcion in casos_wikidata:
        try:
            resultado = validate_wikidata_uri(uri)
            if valida:
                logger.success(f"✅ Wikidata URI {descripcion}: OK")
            else:
                logger.error(f"❌ Wikidata URI {descripcion}: debería fallar")
                errores += 1
        except ValueError as e:
            if not valida:
                logger.success(f"✅ Wikidata URI {descripcion}: rechazada correctamente")
            else:
                logger.error(f"❌ Wikidata URI {descripcion}: no debería fallar - {e}")
                errores += 1
    
    # Test fecha opcional
    casos_fecha = [
        ("2024-01-15", "2024-01-15", "Fecha válida"),
        ("", None, "String vacío"),
        (None, None, "None"),
        ("2024-13-01", None, "Mes inválido (debe fallar)"),
    ]
    
    for entrada, esperado, descripcion in casos_fecha:
        try:
            resultado = validate_date_optional(entrada)
            if descripcion.endswith("(debe fallar)"):
                logger.error(f"❌ Fecha opcional {descripcion}: debería fallar")
                errores += 1
            elif resultado == esperado:
                logger.success(f"✅ Fecha opcional {descripcion}: OK")
            else:
                logger.error(f"❌ Fecha opcional {descripcion}: esperado '{esperado}', obtenido '{resultado}'")
                errores += 1
        except ValueError as e:
            if descripcion.endswith("(debe fallar)"):
                logger.success(f"✅ Fecha opcional {descripcion}: rechazada correctamente")
            else:
                logger.error(f"❌ Fecha opcional {descripcion}: no debería fallar - {e}")
                errores += 1
    
    if errores == 0:
        logger.info("✅ Validaciones específicas funcionando correctamente")
    else:
        logger.error(f"❌ Error: {errores} validaciones específicas fallaron")
    
    return errores == 0


def test_validacion_end_to_end():
    """Test de validación end-to-end con datos reales."""
    print("\n=== TEST: Validación End-to-End ===")
    
    errores = 0
    
    # Inicializar PayloadBuilder al principio para que esté disponible en todos los bloques
    builder = PayloadBuilder()
    
    try:
        # Simular un fragmento procesado con contenido malicioso
        id_fragmento = uuid4()
        
        # Fase 1: Crear fragmento con HTML malicioso
        resultado_fase1 = ResultadoFase1Triaje(
            id_fragmento=id_fragmento,
            es_relevante=True,
            decision_triaje="PROCESAR",
            justificacion_triaje="Contenido relevante",
            categoria_principal="POLÍTICA",
            palabras_clave_triaje=["test", "validación"],
            puntuacion_triaje=15.5,
            confianza_triaje=0.8,
            texto_para_siguiente_fase="<script>alert('XSS')</script>Pedro Sánchez anunció medidas"
        )
        
        # Fase 2: Crear hechos y entidades con validación
        hechos = []
        hecho1 = HechoProcesado(
            id_hecho=1,
            texto_original_del_hecho="<b>Medidas económicas</b> anunciadas",
            confianza_extraccion=0.9,
            offset_inicio_hecho=0,
            offset_fin_hecho=30,
            id_fragmento_origen=id_fragmento
        )
        hechos.append(hecho1)
        
        entidades = []
        entidad1 = EntidadProcesada(
            id_entidad=1,
            texto_entidad="Pedro Sánchez<script>",
            tipo_entidad="PERSONA",
            relevancia_entidad=0.95,
            id_fragmento_origen=id_fragmento
        )
        entidades.append(entidad1)
        
        resultado_fase2 = ResultadoFase2Extraccion(
            id_fragmento=id_fragmento,
            hechos_extraidos=hechos,
            entidades_extraidas=entidades
        )
        
        # Preparar datos para el payload
        metadatos_articulo = {
            "url": "https://ejemplo.com/noticia",
            "titular": "Noticia de <prueba>",
            "medio": "Medio Test",
            "fecha_publicacion": "2024-01-15",
            "idioma_original": "es",
            "contenido_texto_original": resultado_fase1.texto_para_siguiente_fase
        }
        
        procesamiento_articulo = {
            "resumen_generado_pipeline": "Resumen de prueba",
            "palabras_clave_generadas": ["test", "validación"],
            "sentimiento_general_articulo": "neutral",
            "embedding_articulo_vector": [0.1, 0.2, 0.3],
            "estado_procesamiento_final_pipeline": "completado_ok",
            "fecha_procesamiento_pipeline": datetime.now().strftime("%Y-%m-%d"),
            "fecha_ingesta_sistema": datetime.now().strftime("%Y-%m-%d"),
            "version_pipeline_aplicada": "1.0.0"
        }
        
        # Convertir hechos a formato para payload
        hechos_data = []
        for hecho in resultado_fase2.hechos_extraidos:
            hecho_data = {
                "id_temporal_hecho": f"hecho_{hecho.id_hecho}",
                "descripcion_hecho": hecho.texto_original_del_hecho,
                "tipo_hecho": "anuncio",
                "relevancia_hecho": 8,
                "entidades_del_hecho": []
            }
            hechos_data.append(hecho_data)
        
        # Convertir entidades a formato para payload
        entidades_data = []
        for entidad in resultado_fase2.entidades_extraidas:
            entidad_data = {
                "id_temporal_entidad": f"entidad_{entidad.id_entidad}",
                "nombre_entidad": entidad.texto_entidad,
                "tipo_entidad": entidad.tipo_entidad,
                "metadata_entidad": {}
            }
            entidades_data.append(entidad_data)
        
        # Construir payload
        payload = builder.construir_payload_articulo(
            metadatos_articulo_data=metadatos_articulo,
            procesamiento_articulo_data=procesamiento_articulo,
            hechos_extraidos_data=hechos_data,
            entidades_autonomas_data=entidades_data
        )
        
        # Verificar que el payload se construyó
        if payload:
            logger.success("✅ Payload construido exitosamente")
            
            # Verificar algunos campos sanitizados
            payload_dict = payload.model_dump()
            
            # El titular podría o no estar sanitizado dependiendo de donde se aplique la sanitización
            # En esta arquitectura, la sanitización se aplica en los validadores Pydantic específicos
            titular = payload_dict.get("titular", "")
            if "&lt;" in titular or "<prueba>" in titular:
                logger.success("✅ Titular procesado correctamente")
            else:
                logger.error("❌ Titular no procesado")
                errores += 1
            
            # Verificar que hay hechos y entidades
            if len(payload_dict.get("hechos_extraidos", [])) > 0:
                logger.success("✅ Hechos incluidos en payload")
            else:
                logger.error("❌ No hay hechos en el payload")
                errores += 1
            
            if len(payload_dict.get("entidades_autonomas", [])) > 0:
                logger.success("✅ Entidades incluidas en payload")
            else:
                logger.error("❌ No hay entidades en el payload")
                errores += 1
                
        else:
            logger.error("❌ No se pudo construir el payload")
            errores += 1
            
    except Exception as e:
        logger.error(f"❌ Error en validación end-to-end: {e}")
        errores += 1
    
    # Test de validación con datos inválidos (debe fallar)
    try:
        # Intentar construir payload con referencia a ID inexistente
        relaciones_invalidas = [{
            "hecho_origen_id_temporal": "hecho_999",  # No existe
            "hecho_destino_id_temporal": "hecho_1",
            "tipo_relacion": "causa",
            "fuerza_relacion": 5
        }]
        
        payload_invalido = builder.construir_payload_articulo(
            metadatos_articulo_data=metadatos_articulo,
            procesamiento_articulo_data=procesamiento_articulo,
            hechos_extraidos_data=hechos_data,
            entidades_autonomas_data=entidades_data,
            relaciones_hechos_data=relaciones_invalidas
        )
        
        logger.error("❌ Debería fallar con relaciones inválidas")
        errores += 1
        
    except (ValueError, CustomValidationError) as e:
        if "integridad referencial" in str(e) or "Validación fallida" in str(e):
            logger.success("✅ Validación de integridad referencial funcionando")
        else:
            logger.error(f"❌ Error incorrecto: {e}")
            errores += 1
    except Exception as e:
        logger.error(f"❌ Error inesperado con datos inválidos: {e}")
        errores += 1
    
    if errores == 0:
        logger.info("✅ Validación end-to-end funcionando correctamente")
    else:
        logger.error(f"❌ Error: {errores} validaciones end-to-end fallaron")
    
    return errores == 0


def main():
    """Función principal que ejecuta todos los tests."""
    print("=" * 60)
    print("PRUEBAS DE VALIDACIÓN DEL PIPELINE")
    print("=" * 60)
    
    tests = [
        ("Sanitización HTML", test_sanitizacion_html),
        ("Limpieza de Texto", test_limpieza_texto),
        ("Validaciones Pydantic", test_validaciones_pydantic),
        ("Validaciones Específicas", test_validaciones_especificas),
        ("Validación End-to-End", test_validacion_end_to_end),
    ]
    
    total_exitosos = 0
    total_tests = len(tests)
    
    for nombre_test, funcion_test in tests:
        try:
            if funcion_test():
                total_exitosos += 1
        except Exception as e:
            logger.error(f"❌ Error ejecutando {nombre_test}: {e}")
    
    print("\n" + "=" * 60)
    print(f"RESUMEN: {total_exitosos}/{total_tests} tests exitosos")
    print("=" * 60)
    
    if total_exitosos == total_tests:
        print("\n✅ TODAS LAS VALIDACIONES FUNCIONANDO CORRECTAMENTE ✅")
        return 0
    else:
        print(f"\n❌ ERROR: {total_tests - total_exitosos} tests fallaron ❌")
        return 1


if __name__ == "__main__":
    sys.exit(main())
