# Guía de Criterios de Importancia para Hechos en la Máquina de Noticias

**Versión:** 1.0  
**Fecha:** [Fecha Actual]  
**Propietarios:** Equipo de Producto, Estrategia Editorial, Equipo de ML

## 1. Introducción y Propósito

Este documento sirve como una guía conceptual para definir, entender y refinar la noción de "importancia" (asignada en una escala del 1 al 10) para los hechos procesados por la Máquina de Noticias. Su propósito es:

- Alinear la asignación automática de importancia con los objetivos editoriales y las necesidades de los periodistas.
    
- Proporcionar un marco de referencia para el diseño y entrenamiento del modelo de Machine Learning (ML) responsable de asignar la importancia contextual a los hechos.
    
- Facilitar la consistencia en la evaluación manual de la importancia por parte del equipo editorial.
    
- Guiar la interpretación de la importancia de los hechos en las distintas interfaces del sistema.
    

**Este documento NO es una especificación técnica para la implementación directa en el pipeline, sino una guía de principios y criterios que informarán dicha implementación y el entrenamiento del modelo de ML.**

## 2. Definición de "Importancia"

En el contexto de la Máquina de Noticias, la **importancia de un hecho** es una medida de su relevancia, significancia y potencial impacto o interés para los objetivos de investigación periodística y análisis de actualidad que persigue el sistema. Se evalúa en una escala del 1 (muy baja importancia) al 10 (máxima importancia).

Un hecho "importante" es aquel que:

- Tiene una alta probabilidad de ser relevante para múltiples Hilos Narrativos.
    
- Puede señalar un cambio significativo en una situación o tendencia.
    
- Involucra a actores o temas de alto perfil o de interés estratégico.
    
- Aporta información novedosa, crítica o difícil de obtener.
    
- Tiene el potencial de generar investigaciones periodísticas más profundas.
    

## 3. Principios Generales de Evaluación de Importancia

Al evaluar la importancia de un hecho, se deben considerar los siguientes principios generales:

- **Relevancia para la Audiencia y Objetivos Editoriales:** ¿Cuán pertinente es este hecho para los temas y regiones que cubre la Máquina de Noticias y para los intereses de sus usuarios (periodistas)?
    
- **Impacto Potencial:** ¿Cuál es el alcance o las consecuencias (sociales, políticas, económicas, humanas) del hecho? Un hecho que afecta a muchas personas o tiene implicaciones significativas a largo plazo tiende a ser más importante.
    
- **Novedad y Carácter Inesperado:** ¿El hecho representa una novedad, un desarrollo inesperado, o una desviación de las tendencias conocidas? La información sorprendente o que cambia el paradigma suele ser más importante.
    
- **Implicación de Actores Clave:** La participación de figuras públicas prominentes, instituciones relevantes u organizaciones influyentes puede aumentar la importancia de un hecho.
    
- **Profundidad Informativa:** ¿El hecho aporta detalles sustanciales y verificables, o es una mención superficial? Hechos bien fundamentados y detallados suelen ser más valiosos.
    
- **Contribución a Narrativas Existentes o Emergentes:** ¿El hecho se integra, contradice o impulsa significativamente Hilos Narrativos activos o podría ser el germen de uno nuevo?
    
- **Urgencia o Sensibilidad Temporal:** ¿El hecho requiere atención inmediata o tiene una ventana de relevancia temporal corta?
    

## 4. Factores para la Asignación de Importancia (Consideraciones para el Modelo de ML y Evaluación Editorial)

El sistema de asignación de importancia (tanto el modelo de ML como la validación editorial) debe considerar una combinación de factores intrínsecos al hecho y factores contextuales.

### 4.1. Factores Intrínsecos al Hecho

Estos son atributos inherentes al hecho mismo, extraídos directamente de su contenido y metadatos iniciales:

- **Tipo de Hecho:**
    
    - SUCESO: La importancia puede variar enormemente (desde un accidente menor hasta un atentado). Se deben considerar la escala y las consecuencias.
        
    - ANUNCIO: Anuncios de políticas importantes, nombramientos clave, o decisiones estratégicas suelen ser de alta importancia.
        
    - DECLARACION: La importancia depende de quién declara (actor clave) y sobre qué tema. Declaraciones que revelan información nueva o cambian posturas son más importantes.
        
    - NORMATIVA: La promulgación o modificación de leyes o tratados significativos suele tener alta importancia.
        
    - EVENTO: Eventos programados de alto perfil (cumbres, elecciones) o eventos no programados con gran impacto (desastres naturales significativos).
        
    - BIOGRAFIA, CONCEPTO: Su importancia depende de la relevancia del sujeto o concepto para la actualidad o Hilos Narrativos.
        
- **Magnitud/Escala:** (Cuando aplique y sea extraíble)
    
    - Número de personas afectadas (víctimas, participantes, beneficiarios).
        
    - Impacto económico (montos financieros, porcentaje del PIB).
        
    - Extensión geográfica del impacto.
        
- **Precisión y Verificabilidad:** Hechos con fechas, lugares y actores claramente definidos suelen ser más procesables y, por ende, potencialmente más importantes si cumplen otros criterios.
    
- **Ubicación Geográfica (País, Región, Ciudad):** La relevancia en función de los países prioritarios para el sistema.
    
- **Entidades Involucradas:**
    
    - **Tipo de Entidades:** (Jefes de Estado, Ministros, grandes corporaciones, ONGs internacionales vs. actores locales menos conocidos).
        
    - **Número y Diversidad de Entidades Clave:** Hechos que conectan múltiples actores relevantes.
        
- **Fuente Original del Hecho:** (Aunque la importancia es del hecho, no de la fuente)
    
    - ¿Proviene de una fuente oficial, un medio de alta reputación, una investigación exclusiva? (Esto puede influir en la confianza inicial, que se separa de la importancia, pero un hecho exclusivo de una fuente reputada puede ser más "importante" de seguir).
        
- **Contenido Explícito del Hecho:**
    
    - Uso de palabras clave asociadas a crisis, cambios significativos, hitos.
        
    - Mención de cifras o datos cuantitativos impactantes.
        

### 4.2. Factores Contextuales (Derivados de tendencias_contexto_diario y otras análisis)

Estos factores reflejan cómo el hecho se sitúa dentro del panorama informativo más amplio en un momento dado:

- **Tendencias Temáticas (etiquetas_tendencia):**
    
    - Si las etiquetas principales del hecho coinciden con temas que están actualmente en "auge" (alto score o cambio porcentual positivo en tendencias_temas).
        
- **Relevancia de Entidades (entidades_tendencia):**
    
    - Si las entidades clave del hecho están entre las "entidades calientes" (alto score_relevancia en entidades_relevantes_recientes).
        
- **Proximidad a Eventos Programados Relevantes (eventos_proximos_relevantes):**
    
    - Si el hecho es un precursor, una reacción o está directamente relacionado con un evento futuro importante y de alta prioridad de cobertura.
        
- **Relación con Hilos Narrativos Activos (hilos_activos_calientes):**
    
    - Si el hecho parece encajar o impactar significativamente en Hilos Narrativos que están actualmente "activos" o tienen alta relevancia editorial.
        
    - Un hecho que inicia un nuevo hilo potencialmente importante.
        
- **Combinaciones Clave de Interés (combinaciones_clave_importantes):**
    
    - Si el hecho ocurre en una combinación de país(es) y tema(s) que el sistema (o los editores) han identificado como de particular importancia contextual en ese momento.
        
- **Volumen y Velocidad de Información Similar:** Un aumento súbito en hechos relacionados con el mismo tema o evento puede indicar una escalada de importancia.
    
- **Conexión con Hechos Previos Importantes:** Si el hecho es una secuela directa, una consecuencia o una respuesta a un hecho anterior ya catalogado como muy importante.
    

## 5. Escala de Importancia (Guía General)

- **Importancia 8-10 (Muy Alta / Crítica):**
    
    - Hechos de gran impacto y trascendencia (ej. inicio de un conflicto, caída de un gobierno, aprobación de una ley transformadora, gran desastre natural con consecuencias políticas).
        
    - Anuncios o declaraciones de actores primarios que cambian significativamente una situación o política.
        
    - Hitos clave en Hilos Narrativos de máxima prioridad editorial.
        
    - Eventos que requieren cobertura y análisis inmediato y profundo.
        
- **Importancia 5-7 (Alta / Significativa):**
    
    - Hechos relevantes que desarrollan narrativas importantes, pero no necesariamente disruptivos.
        
    - Declaraciones importantes de actores secundarios o sobre aspectos específicos de un tema mayor.
        
    - Resultados electorales, informes significativos, avances en negociaciones clave.
        
    - Eventos programados de seguimiento prioritario.
        
- **Importancia 3-4 (Media / Contextual):**
    
    - Hechos que aportan contexto o detalles a narrativas existentes, pero no son centrales.
        
    - Declaraciones rutinarias, seguimiento de procesos en curso.
        
    - Información útil para completar el panorama, pero no necesariamente para destacar individualmente.
        
- **Importancia 1-2 (Baja / Monitoreo):**
    
    - Hechos de relevancia marginal, muy localizados sin trascendencia mayor, o información de seguimiento de bajo impacto.
        
    - Pueden ser útiles para análisis agregados o para detectar señales débiles a largo plazo, pero no requieren atención prioritaria individual.
        

## 6. Proceso de Feedback y Refinamiento del Modelo de ML

La asignación de importancia por el modelo de ML será un proceso iterativo y de aprendizaje:

1. **Asignación Inicial por el Pipeline:** El module_pipeline asignará una importancia_asignada_sistema utilizando el modelo de ML entrenado, basándose en los factores intrínsecos y el tendencias_contexto_diario.
    
2. **Revisión Editorial:** Los editores, a través del module_dashboard_review, revisarán los hechos.
    
    - Si la importancia asignada por el sistema es correcta y el editor interactúa significativamente con el hecho (ej. lo valida, lo vincula a un hilo), esto se considerará un "acierto" implícito.
        
    - Si el editor ajusta explícitamente la importancia, este valor se registrará como importancia_editor_final.
        
3. **Registro de Feedback:** Todas estas interacciones (ajustes explícitos y "aciertos" implícitos a través de la interacción) se registrarán en la tabla feedback_importancia_hechos.
    
4. **Reentrenamiento Periódico:** El script importancia_model_trainer.py utilizará los datos de feedback_importancia_hechos y los correspondientes registros históricos de tendencias_contexto_diario para reentrenar y mejorar el modelo de ML.
    
5. **Revisión de esta Guía:** Esta guía se revisará periódicamente (ej. trimestralmente) por los equipos de Producto, Editorial y ML para asegurar que los criterios sigan alineados con los objetivos del sistema y para incorporar nuevos aprendizajes.
    

## 7. Consideraciones Adicionales

- **Subjetividad Inherente:** La "importancia" siempre tendrá un componente subjetivo. El objetivo del sistema es aprender los patrones de esta subjetividad editorial y ser una herramienta de apoyo eficiente.
    
- **Evolución de Criterios:** Lo que se considera importante puede cambiar con el tiempo, según la evolución del panorama informativo y los focos editoriales. El sistema de reentrenamiento busca adaptarse a estos cambios.
    
- **Evitar Sesgos:** Durante el entrenamiento del modelo y la revisión de esta guía, se debe prestar atención a evitar la introducción o perpetuación de sesgos indeseados.
    

---