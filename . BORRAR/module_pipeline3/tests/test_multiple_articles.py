#!/usr/bin/env python3
"""
Test de procesamiento múltiple de artículos políticos
===================================================
Prueba varios artículos a la vez para diagnosticar el pipeline.
"""

import asyncio
import json  # noqa: F401
import sys
import time
from datetime import datetime  # noqa: F401
from uuid import uuid4  # noqa: F401

# Añadir el directorio src al path
sys.path.insert(0, "/app/src")

from src.controller import PipelineController
from src.utils.config import GROQ_API_KEY

# Artículos políticos de prueba
ARTICULOS_POLITICOS = [
    {
        "id": 2001,
        "url": "https://www.infobae.com/test/2025/07/17/gobierno-haiti-dimision",
        "medio": "Infobae",
        "tipo_medio": "otro",
        "titular": "El gobierno de Haití anuncia su dimisión tras crisis política",
        "fecha_publicacion": "2025-07-17T08:00:00Z",
        "autor": "Corresponsalía",
        "contenido_texto": """El primer ministro de Haití, Garry Conille, anunció oficialmente la dimisión de su gobierno tras una severa crisis política que ha sumido al país en la inestabilidad. La decisión se produce después de semanas de protestas y presión de la oposición que cuestionaba la legitimidad del ejecutivo.

En una declaración transmitida por televisión nacional, Conille explicó que "el país necesita un nuevo rumbo político" y que su gobierno había agotado todas las opciones para mantener la estabilidad. El primer ministro, quien asumió el cargo hace apenas seis meses, enfrentó múltiples desafíos incluyendo la crisis económica, la violencia de las pandillas y la falta de apoyo parlamentario.

La oposición política había exigido la renuncia del gobierno desde hace semanas, organizando manifestaciones masivas en Puerto Príncipe y otras ciudades principales. Los líderes opositores acusaron al ejecutivo de corrupción y de incapacidad para resolver los problemas fundamentales del país.

La crisis se agravó la semana pasada cuando el Parlamento haitiano rechazó el presupuesto nacional propuesto por el gobierno, dejando al país sin recursos para funcionar adecuadamente. Esta situación provocó huelgas en el sector público y paralizó servicios esenciales como salud y educación.""",
        "idioma": "es",
        "seccion": "politica",
        "area_geografica": "AMERICA",
    },
    {
        "id": 2002,
        "url": "https://www.infobae.com/test/2025/07/17/congreso-espana-reforma",
        "medio": "Infobae",
        "tipo_medio": "otro",
        "titular": "El Congreso español aprueba la polémica reforma del sistema judicial",
        "fecha_publicacion": "2025-07-17T09:30:00Z",
        "autor": "Madrid Corresponsal",
        "contenido_texto": """El Congreso de los Diputados de España aprobó ayer por estrecho margen la controvertida reforma del sistema judicial impulsada por el gobierno de coalición. La votación, que se extendió durante más de ocho horas, concluyó con 176 votos a favor, 171 en contra y tres abstenciones.

La reforma, que ha generado intensos debates durante los últimos meses, modifica sustancialmente el proceso de selección de jueces y magistrados del Tribunal Supremo. Los cambios incluyen la creación de un nuevo órgano de selección judicial y la modificación de los criterios de nombramiento para los altos cargos judiciales.

El ministro de Justicia, Félix Bolaños, defendió la reforma argumentando que "modernizará el sistema judicial español y lo hará más transparente y eficiente". Sin embargo, la oposición del Partido Popular y otros grupos parlamentarios denunciaron que la medida representa un "ataque a la independencia judicial".

La reforma también establece nuevos mecanismos de control y evaluación para los magistrados, así como cambios en el régimen disciplinario. Los críticos argumentan que estos cambios podrían politizar la justicia, mientras que el gobierno sostiene que aumentarán la rendición de cuentas.""",
        "idioma": "es",
        "seccion": "politica",
        "area_geografica": "EUROPA",
    },
    {
        "id": 2003,
        "url": "https://www.infobae.com/test/2025/07/17/presidente-colombia-reforma",
        "medio": "Infobae",
        "tipo_medio": "otro",
        "titular": "El presidente de Colombia presenta ambiciosa reforma tributaria",
        "fecha_publicacion": "2025-07-17T11:00:00Z",
        "autor": "Bogotá Redacción",
        "contenido_texto": """El presidente Gustavo Petro presentó oficialmente ante el Congreso colombiano una nueva reforma tributaria que busca recaudar recursos adicionales por valor de 50 billones de pesos colombianos durante los próximos cuatro años. La propuesta, considerada la más ambiciosa de su mandato, incluye cambios significativos en el sistema impositivo del país.

Entre las medidas más destacadas se encuentra el aumento del impuesto a las grandes fortunas, la creación de un gravamen especial a las transacciones financieras y la eliminación de beneficios tributarios para ciertos sectores empresariales. El gobierno argumenta que estos recursos son necesarios para financiar programas sociales y de infraestructura.

El ministro de Hacienda, Ricardo Bonilla, explicó que la reforma está diseñada para "reducir la desigualdad y generar mayor justicia fiscal en Colombia". La propuesta también incluye incentivos para pequeñas y medianas empresas, así como exenciones para los sectores más vulnerables de la población.

Sin embargo, los sectores empresariales han expresado preocupación por el impacto de las nuevas medidas en la competitividad del país. La Asociación Nacional de Empresarios de Colombia (ANDI) advirtió que algunos impuestos podrían desincentivar la inversión extranjera y afectar el crecimiento económico.""",
        "idioma": "es",
        "seccion": "politica",
        "area_geografica": "AMERICA",
    },
]


async def procesar_articulo_individual(controller, articulo, indice):
    """Procesa un artículo individual y retorna el resultado."""
    print(f"\n[ARTÍCULO {indice}] Iniciando procesamiento:")
    print(f"  ID: {articulo['id']}")
    print(f"  Título: {articulo['titular'][:60]}...")
    print(f"  Tamaño: {len(articulo['contenido_texto'])} caracteres")

    inicio = time.time()

    try:
        resultado = await controller.process_article(articulo)
        duracion = time.time() - inicio

        print(f"[ARTÍCULO {indice}] Completado en {duracion:.2f}s")
        print(f"  Éxito: {resultado.get('exito', False)}")
        print(f"  Fase: {resultado.get('fase_completada', 0)}/7")

        if resultado.get("persistencia"):
            persist = resultado["persistencia"]
            print(
                f"  Persistido: {persist.get('hechos_insertados', 0)} hechos, {persist.get('entidades_insertadas', 0)} entidades"
            )
        else:
            print(f"  Error persistencia: {resultado.get('errores', 'Desconocido')}")

        return {
            "indice": indice,
            "exito": resultado.get("exito", False),
            "duracion": duracion,
            "resultado": resultado,
        }

    except Exception as e:
        duracion = time.time() - inicio
        print(f"[ARTÍCULO {indice}] ERROR en {duracion:.2f}s: {str(e)}")
        return {"indice": indice, "exito": False, "duracion": duracion, "error": str(e)}


async def test_procesamiento_multiple():
    """Test de procesamiento múltiple simultáneo."""
    print("=== TEST DE PROCESAMIENTO MÚLTIPLE DE ARTÍCULOS POLÍTICOS ===")
    print(f"Artículos a procesar: {len(ARTICULOS_POLITICOS)}")

    controller = PipelineController()

    # Procesar todos los artículos EN PARALELO
    print("\n🚀 INICIANDO PROCESAMIENTO EN PARALELO...")
    inicio_total = time.time()

    # Crear tareas para todos los artículos
    tareas = []
    for i, articulo in enumerate(ARTICULOS_POLITICOS, 1):
        tarea = procesar_articulo_individual(controller, articulo, i)
        tareas.append(tarea)

    # Ejecutar todas las tareas en paralelo
    resultados = await asyncio.gather(*tareas, return_exceptions=True)

    duracion_total = time.time() - inicio_total

    # Analizar resultados
    print(f"\n📊 ANÁLISIS DE RESULTADOS (Tiempo total: {duracion_total:.2f}s)")
    print("=" * 60)

    exitosos = 0
    fallidos = 0
    total_hechos = 0
    total_entidades = 0

    for resultado in resultados:
        if isinstance(resultado, Exception):
            print(f"❌ Excepción: {resultado}")
            fallidos += 1
            continue

        indice = resultado["indice"]
        if resultado["exito"]:
            exitosos += 1
            print(f"✅ Artículo {indice}: ÉXITO ({resultado['duracion']:.2f}s)")

            # Extraer datos de persistencia
            if resultado["resultado"].get("persistencia"):
                persist = resultado["resultado"]["persistencia"]
                hechos = persist.get("hechos_insertados", 0)
                entidades = persist.get("entidades_insertadas", 0)
                total_hechos += hechos
                total_entidades += entidades
                print(f"   └─ Persistido: {hechos} hechos, {entidades} entidades")
        else:
            fallidos += 1
            print(f"❌ Artículo {indice}: FALLO ({resultado['duracion']:.2f}s)")
            if "error" in resultado:
                print(f"   └─ Error: {resultado['error']}")

    print(f"\n📈 RESUMEN FINAL:")  # noqa: F541
    print(f"   ✅ Exitosos: {exitosos}/{len(ARTICULOS_POLITICOS)}")
    print(f"   ❌ Fallidos: {fallidos}/{len(ARTICULOS_POLITICOS)}")
    print(
        f"   📊 Total datos persistidos: {total_hechos} hechos, {total_entidades} entidades"
    )
    print(
        f"   ⏱️  Tiempo promedio por artículo: {duracion_total / len(ARTICULOS_POLITICOS):.2f}s"
    )

    if exitosos > 0:
        print(f"\n🎯 EFICIENCIA DEL PARALELISMO:")  # noqa: F541
        tiempo_secuencial_estimado = sum(
            r.get("duracion", 0) for r in resultados if not isinstance(r, Exception)
        )
        print(f"   Tiempo secuencial estimado: {tiempo_secuencial_estimado:.2f}s")
        print(f"   Tiempo paralelo real: {duracion_total:.2f}s")
        print(
            f"   Mejora de rendimiento: {tiempo_secuencial_estimado / duracion_total:.1f}x"
        )

    return exitosos == len(ARTICULOS_POLITICOS)


if __name__ == "__main__":
    if not GROQ_API_KEY:
        print("ERROR: No se encontró GROQ_API_KEY")
        sys.exit(1)

    success = asyncio.run(test_procesamiento_multiple())

    print("\n" + "=" * 60)
    if success:
        print("🎉 TODOS LOS ARTÍCULOS PROCESADOS EXITOSAMENTE")
        sys.exit(0)
    else:
        print("⚠️  ALGUNOS ARTÍCULOS FALLARON - Ver detalles arriba")
        sys.exit(1)
