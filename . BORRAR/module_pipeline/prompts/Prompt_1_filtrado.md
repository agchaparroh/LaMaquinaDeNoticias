# Evaluación Inicial para Procesamiento de Artículos

Evalúa si este artículo periodístico cumple con los criterios para nuestro sistema de análisis estructurado. Sigue estos pasos en orden para maximizar la eficiencia:

# ARTÍCULO A EVALUAR

Título: {{TITULO}}
Medio: {{MEDIO}}
País: {{PAIS}}
Fecha de publicación: {{FECHA_PUB}}

CONTENIDO:
{{CONTENIDO}}

## PASO 1: VERIFICAR CRITERIOS DE EXCLUSIÓN

Evalúa si el artículo se centra PRINCIPALMENTE en alguno de estos temas:
- Sucesos cotidianos locales (crímenes comunes, accidentes)
- Deportes (excepto con dimensión política clara)
- Entretenimiento y espectáculos (farándula, cine, música, etc.)
- Economía rutinaria (resultados empresariales estándar, fluctuaciones bursátiles diarias)
- Ciencia y tecnología sin conexión con políticas públicas
- Estilo de vida (viajes, gastronomía, bienestar)
- Contenido promocional o publicitario
- Pseudociencia y creencias sin base factual

Si el artículo pertenece a alguna de estas categorías, marca EXCLUSIÓN: SÍ y finaliza el análisis con decisión DESCARTAR.

## PASO 2: IDENTIFICAR TIPO DE ARTÍCULO

Si el artículo no fue excluido en el paso 1, clasifícalo en UNA de estas categorías:
- NOTICIA: Reporta hechos recientes con estructura informativa básica
- ENTREVISTA: Formato de preguntas y respuestas o declaraciones extensas de una o más personas
- OPINIÓN: Presenta el punto de vista del autor sobre un tema
- ANÁLISIS: Examina en profundidad un tema con contexto y múltiples perspectivas
- CRÓNICA: Narración secuencial de eventos con elementos descriptivos
- REPORTAJE: Investigación en profundidad con múltiples fuentes y contexto extenso

NOTA: Si el artículo es de OPINIÓN, considera si tiene un valor informativo o analítico excepcional antes de continuar. Los artículos de opinión estándar generalmente deberían ser descartados.

## PASO 3: EVALUAR CRITERIOS DE RELEVANCIA

Si el artículo pasó los filtros anteriores, evalúa cada criterio en una escala de 1-5 (donde 1=muy bajo, 5=muy alto):

### 1. RELEVANCIA GEOGRÁFICA [1-5]
¿El artículo se relaciona directamente con uno o más de los 23 países/territorios del ámbito hispánico?
(Argentina, Bolivia, Chile, Colombia, Costa Rica, Cuba, Ecuador, El Salvador, España, Filipinas, Guatemala, Guinea Ecuatorial, Honduras, México, Nicaragua, Panamá, Paraguay, Perú, Puerto Rico, República Dominicana, Sáhara Occidental, Uruguay, Venezuela)

### 2. RELEVANCIA TEMÁTICA [1-5]
¿El artículo se centra en alguno de estos temas prioritarios relacionados con el ámbito hispánico (países mencionados anteriormente)?
- **Política nacional/internacional**: Actividad gubernamental, legislativa, electoral, crisis políticas, diplomacia
- **Conflictos y seguridad**: Conflictos armados, crisis sociales, protestas relevantes, crimen organizado con implicaciones políticas
- **Economía política**: Decisiones gubernamentales económicas, crisis, acuerdos comerciales, debates sobre modelos económicos
- **Justicia y legalidad**: Casos judiciales de alto perfil, cambios legislativos significativos, actividad de altos tribunales
- **Sociedad y derechos**: Derechos humanos, movimientos sociales con impacto político, políticas sociales clave
- **Contexto y análisis**: Análisis geopolítico, histórico o explicativos sobre la región hispánica

### 3. DENSIDAD FACTUAL [1-5]
¿Contiene hechos concretos, verificables y datables?
- Alta (4-5): Múltiples hechos con fechas, lugares y actores precisos
- Media (3): Algunos hechos concretos mezclados con generalidades
- Baja (1-2): Principalmente opiniones, especulaciones o descripciones vagas

### 4. COMPLEJIDAD RELACIONAL [1-5]
¿Existen conexiones significativas entre eventos, actores o instituciones?
- Alta (4-5): Red compleja de causas-efectos, actores interrelacionados, contexto institucional
- Media (3): Algunas relaciones básicas entre elementos
- Baja (1-2): Elementos aislados sin conexiones significativas

### 5. VALOR INFORMATIVO [1-5]
¿Aporta contenido sustancial sobre asuntos de interés público?
- Alto (4-5): Información detallada sobre temas de trascendencia política/social/económica
- Medio (3): Información básica sobre temas relevantes
- Bajo (1-2): Información trivial, superficial o principalmente promocional

## PASO 4: TOMAR DECISIÓN

Basándote en la suma de puntuaciones (rango 5-25):
- **PROCESAR** (17-25): Artículo de alto valor informativo en temas prioritarios
- **CONSIDERAR** (12-16): Artículo con valor moderado, evaluar disponibilidad de recursos
- **DESCARTAR** (<12): Artículo de bajo valor informativo para nuestro sistema

## FORMATO DE RESPUESTA
```
EVALUACIÓN DE ARTÍCULO: [Titular]

EXCLUSIÓN: [SÍ/NO] - [Si es SÍ, indicar categoría y finalizar]

TIPO DE ARTÍCULO: [NOTICIA/ENTREVISTA/OPINIÓN/ANÁLISIS/CRÓNICA/REPORTAJE]

PUNTUACIONES:
- Relevancia geográfica: [1-5] - [País(es) principal(es)]
- Relevancia temática: [1-5] - [Tema principal identificado]
- Densidad factual: [1-5]
- Complejidad relacional: [1-5]
- Valor informativo: [1-5]

TOTAL: [Suma] / 25

DECISIÓN: [PROCESAR/CONSIDERAR/DESCARTAR]

JUSTIFICACIÓN: [2-3 frases concisas]

SI PROCEDE ANÁLISIS, ELEMENTOS CLAVE:
- [3-5 elementos informativos principales]
```

NOTA FINAL: Este proceso está diseñado para identificar eficientemente contenido sustancial sobre temas sociopolíticos, económicos y de derechos en el ámbito hispánico. La estructura secuencial permite descartar rápidamente contenido irrelevante y evaluar con mayor profundidad solo los artículos potencialmente valiosos.