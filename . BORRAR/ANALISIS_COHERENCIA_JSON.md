# ANÁLISIS CRÍTICO DE COHERENCIA JSON: PIPELINE 7 FASES

## QUÉ PROBLEMA ESTAMOS RESOLVIENDO

El pipeline de 7 fases tiene **inconsistencias graves** entre lo que los prompts piden a los LLMs, lo que el código procesa, y lo que se guarda en la base de datos. Esto causa errores, pérdida de datos y mal funcionamiento del sistema.

## EL FLUJO COMPLETO DE DATOS

### ENTRADA: Desde module_connector
```
ArticuloInItem {
  medio: "El País"
  titular: "Título del artículo"
  fecha_publicacion: "2024-05-15T10:00:00Z"
  contenido_texto: "Texto completo del artículo..."
  area_geografica: "España"
  tipo_medio: "Diario Digital"
  // ... otros campos
}
```

### PROCESAMIENTO: Lo que cada fase hace

**FASE 1 (Triaje)**: No usa JSON, solo decide si procesar o no
**FASE 2 (Simplificación)**: No usa JSON, solo convierte texto complejo → texto simple

**FASE 3 (Entidades)**: AQUÍ EMPIEZAN LOS PROBLEMAS
**FASE 4 (Hechos)**: MÁS PROBLEMAS
**FASE 5 (Datos)**: REFERENCIAS ROTAS
**FASE 6 (Citas)**: REFERENCIAS ROTAS
**FASE 7 (Relaciones)**: Más consistente pero hereda problemas anteriores

### SALIDA: Lo que se guarda en base de datos
```
FragmentoPersistenciaPayload {
  hechos_extraidos: HechoExtraidoItem[]
  entidades_autonomas: EntidadAutonomaItem[]
  citas_textuales_extraidas: CitaTextualExtraidaItem[]
  datos_cuantitativos_extraidos: DatoCuantitativoExtraidoItem[]
  // ... relaciones
}
```

## PROBLEMAS CRÍTICOS ENCONTRADOS

### PROBLEMA 1: REFERENCIAS ROTAS EN PROMPTS
**Ubicación**: `Datos.md` y `Citas.md`

**Qué dice el prompt de Datos.md**:
```
**Hechos identificados:**
{{Fase6_Hechos}}

**Entidades identificadas:**
{{Fase5_Entidades}}
```

**POR QUÉ ESTÁ MAL**: En el pipeline de 7 fases:
- Los hechos los extrae la **Fase 4**, no la Fase 6
- Las entidades las extrae la **Fase 3**, no la Fase 5

**DEBE SER**:
```
**Hechos identificados:**
{{Fase4_Hechos}}

**Entidades identificadas:**
{{Fase3_Entidades}}
```

**LO MISMO PASA EN**: `Citas.md` - tiene las mismas referencias incorrectas.

### PROBLEMA 2: NOMBRES DE CAMPOS COMPLETAMENTE DIFERENTES

**Lo que el prompt de Entidades.md pide**:
```json
{
  "entidades": [
    {
      "id": 1,
      "nombre": "Nicolás Maduro",
      "alias": [],
      "tipo": "PERSONA",
      "descripcion": "- presidente de Venezuela",
      "fecha_nacimiento": null,
      "fecha_disolucion": null
    }
  ]
}
```

**Lo que se guarda en base de datos** (persistencia.py):
```json
{
  "entidades_autonomas": [
    {
      "id_temporal_entidad": "1",
      "nombre_entidad": "Nicolás Maduro",
      "alias_entidad": [],
      "tipo_entidad": "PERSONA",
      "descripcion_entidad": "presidente de Venezuela",
      // NO HAY fecha_nacimiento ni fecha_disolucion
    }
  ]
}
```

**RESULTADO**: El código tiene que hacer conversiones manuales complicadas y se pierden datos.

### PROBLEMA 3: ESTRUCTURAS DE FECHAS INCONSISTENTES

**Entidades** (prompt):
```json
"fecha_nacimiento": "2024-05-15"  // string simple
```

**Hechos** (prompt):
```json
"fecha": {
  "inicio": "2024-05-15",
  "fin": "2024-05-15"
}  // objeto complejo
```

**Datos** (prompt):
```json
"periodo": {
  "inicio": "2024-05-15",
  "fin": "2024-05-15"
}  // igual que hechos pero se llama "periodo"
```

**Citas** (prompt):
```json
"fecha": "2024-05-15"  // string simple otra vez
```

**NO HAY LÓGICA**: Cada fase usa un formato diferente para las fechas.

### PROBLEMA 4: IDs NO SECUENCIALES EN EJEMPLOS

**En el prompt de Entidades.md**, el ejemplo muestra:
```json
{"id": 1}, {"id": 2}, {"id": 4}, {"id": 5}, {"id": 6}
```

**FALTA EL ID 3**. Esto confunde a los LLMs sobre cómo generar IDs secuenciales.

### PROBLEMA 5: MAPEO MANUAL COMPLEJO

El código tiene que hacer conversiones como:
```python
# Desde lo que devuelve el LLM
llm_entidad = {
  "id": 1,
  "nombre": "Juan García",
  "tipo": "PERSONA"
}

# A lo que espera la persistencia
db_entidad = {
  "id_temporal_entidad": "1",
  "nombre_entidad": "Juan García", 
  "tipo_entidad": "PERSONA"
}
```

**ESTO ES INNECESARIO** si los esquemas fueran coherentes.

### PROBLEMA 6: CAMPOS PERDIDOS EN LA CONVERSIÓN

**Los prompts definen campos que no existen en persistencia**:
- `fecha_nacimiento` y `fecha_disolucion` de entidades
- `precision_temporal`, `es_futuro`, `estado_programacion` de hechos
- Muchos campos de datos cuantitativos

**RESULTADO**: Se extraen pero se pierden al guardar.

## QUÉ HAY QUE ARREGLAR

### URGENTE (ROMPE EL PIPELINE):

1. **Corregir referencias en prompts**:
   - `Datos.md`: Cambiar `{{Fase6_Hechos}}` → `{{Fase4_Hechos}}`
   - `Datos.md`: Cambiar `{{Fase5_Entidades}}` → `{{Fase3_Entidades}}`
   - `Citas.md`: Los mismos cambios

2. **Corregir ejemplo de IDs**:
   - En `Entidades.md`: Cambiar IDs [1,2,4,5,6] → [1,2,3,4,5]

3. **Verificar que el código mapee correctamente**:
   - Los names de variables en el pipeline coordinator deben coincidir

### IMPORTANTE (MEJORA LA COHERENCIA):

4. **Unificar nombres de campos**:
   - Decidir si usar `id` o `id_temporal_entidad`
   - Decidir si usar `nombre` o `nombre_entidad`
   - Aplicar consistentemente

5. **Estandarizar fechas**:
   - OPCIÓN A: Todo string simple "YYYY-MM-DD"
   - OPCIÓN B: Todo objeto {"inicio": "YYYY-MM-DD", "fin": "YYYY-MM-DD"}

6. **Agregar campos perdidos a persistencia**:
   - `fecha_nacimiento`, `fecha_disolucion` en entidades
   - `precision_temporal`, `es_futuro` en hechos

### RECOMENDADO (OPTIMIZACIÓN):

7. **Crear validadores automáticos**:
   - Que verifiquen que las referencias entre fases existen
   - Que validen formatos de fecha consistentes
   - Que garanticen IDs secuenciales

## CÓMO AFECTA AL FUNCIONAMIENTO

### SI NO SE ARREGLA:

- **Fase 5 (Datos)** no puede referenciar hechos porque busca `{{Fase6_Hechos}}` que no existe
- **Fase 6 (Citas)** no puede referenciar entidades por la misma razón
- **Las relaciones (Fase 7)** funcionan mal porque los IDs no coinciden
- **La consolidación cross-chunk** falla porque los esquemas son inconsistentes

### SI SE ARREGLA:

- El pipeline funciona de extremo a extremo sin conversiones manuales
- Los datos se preservan completamente
- Las referencias entre fases funcionan correctamente
- El código es más simple y mantenible

## IMPLEMENTACIÓN PRÁCTICA

### CAMBIOS MÍNIMOS (PARA QUE FUNCIONE):

1. Editar 2 líneas en `Datos.md`:
   ```
   - {{Fase6_Hechos}} → {{Fase4_Hechos}}
   - {{Fase5_Entidades}} → {{Fase3_Entidades}}
   ```

2. Editar 2 líneas en `Citas.md`: lo mismo

3. Corregir ejemplo en `Entidades.md`: IDs secuenciales

### CAMBIOS COMPLETOS (PARA COHERENCIA TOTAL):

4. Actualizar persistencia.py para incluir todos los campos de los prompts
5. Actualizar prompts para usar nombres de campos consistentes  
6. Crear funciones de mapeo automático entre esquemas

## CONCLUSIÓN

**El problema principal no es técnico, es de coordinación**: Los prompts, el código, y la base de datos fueron diseñados por separado sin un esquema unificado.

**La solución urgente** es arreglar las referencias rotas en los prompts (cambio de 10 minutos).

**La solución completa** es rediseñar los esquemas para que sean coherentes en toda la pipeline (cambio de 1-2 días).

Sin estos cambios, el pipeline de 7 fases **no puede funcionar correctamente**.

---

# APÉNDICE: INVESTIGACIÓN EXHAUSTIVA DE BASE DE DATOS SUPABASE

## METODOLOGÍA DE INVESTIGACIÓN

Para resolver definitivamente los problemas 2, 3, 5 y 6, se realizó una **investigación exhaustiva del esquema real de la base de datos Supabase**. Esta investigación tiene como objetivo determinar qué campos existen realmente en la base de datos para usar como "fuente de verdad" y corregir las inconsistencias identificadas.

### PROCESO DE INVESTIGACIÓN EJECUTADO

1. **Conexión a base de datos**: Proyecto Supabase `aukbzqbcvbsnjdhflyvr`
2. **Análisis sistemático de tablas**: Se ejecutaron consultas SQL para extraer esquemas completos
3. **Comparación con modelos Python**: Confrontación entre esquema real vs modelos de persistencia
4. **Verificación de campos "perdidos"**: Validación de existencia de campos mencionados en prompts

## HALLAZGOS CRÍTICOS: ESQUEMA REAL DE BASE DE DATOS

### TABLA `entidades` - ESQUEMA COMPLETO
```sql
-- Campos encontrados en la base de datos real:
id                  bigint                NOT NULL (PK)
nombre              character varying     NOT NULL
tipo                character varying     NOT NULL  
descripcion         text                  NULL
alias               ARRAY                 NULL
fecha_nacimiento    tstzrange            NULL      ← ¡EXISTE!
fecha_disolucion    tstzrange            NULL      ← ¡EXISTE!
articulo_id         bigint               NULL (FK)
documento_id        bigint               NULL (FK)
fragmento_id        bigint               NULL (FK)
fecha_registro      timestamp with time zone NOT NULL
embedding           vector               NULL
```

**REVELACIÓN CRÍTICA**: Los campos `fecha_nacimiento` y `fecha_disolucion` **SÍ EXISTEN** en la base de datos como tipo `tstzrange` (PostgreSQL timestamp range). El PROBLEMA 6 estaba basado en información incorrecta.

### TABLA `hechos` - ESQUEMA COMPLETO
```sql
-- Campos encontrados en la base de datos real:
id                     bigint                     NOT NULL (PK)
descripcion            text                       NOT NULL
tipo_hecho             character varying          NULL
subtipo_hecho          character varying          NULL
fecha_ocurrencia       tstzrange                 NULL
lugar_ocurrencia       character varying          NULL
relevancia             integer                    NULL
contexto_adicional     text                       NULL
precision_temporal     character varying          NULL      ← ¡EXISTE!
es_evento_futuro       boolean                    NULL      ← ¡EXISTE!
estado_programacion    character varying          NULL      ← ¡EXISTE!
articulo_id            bigint                     NULL (FK)
documento_id           bigint                     NULL (FK)
fragmento_id           bigint                     NULL (FK)
fecha_registro         timestamp with time zone  NOT NULL
embedding              vector                     NULL
```

**REVELACIÓN CRÍTICA**: Los campos `precision_temporal`, `es_evento_futuro` y `estado_programacion` **SÍ EXISTEN** en la base de datos. Nota importante: el campo se llama `es_evento_futuro`, no `es_futuro` como aparece en algunos prompts.

### TABLA `citas_textuales` - ESQUEMA COMPLETO
```sql
-- Campos encontrados en la base de datos real:
id                          bigint                     NOT NULL (PK)
texto_cita                  text                       NOT NULL
entidad_emisora_id          bigint                     NULL (FK)
cargo_entidad_emisora       character varying          NULL
fecha_cita                  timestamp with time zone  NULL      ← ¡EXISTE!
contexto                    text                       NULL
relevancia                  integer                    NULL
hecho_principal_id          bigint                     NULL (FK)
articulo_id                 bigint                     NULL (FK)
documento_id                bigint                     NULL (FK)
fragmento_id                bigint                     NULL (FK)
fecha_registro              timestamp with time zone  NOT NULL
```

**REVELACIÓN CRÍTICA**: El campo `fecha_cita` **SÍ EXISTE** como `timestamp with time zone`.

### TABLA `datos_cuantitativos` - ESQUEMA COMPLETO
```sql
-- Campos encontrados en la base de datos real:
id                         bigint                     NOT NULL (PK)
hecho_id                   bigint                     NULL (FK)
articulo_id                bigint                     NULL (FK)
indicador                  character varying          NOT NULL
categoria                  character varying          NOT NULL      ← ¡EXISTE!
valor_numerico             numeric                    NOT NULL
unidad                     character varying          NOT NULL
ambito_geografico          ARRAY                      NOT NULL
periodo_referencia_inicio  date                       NULL
periodo_referencia_fin     date                       NULL
tipo_periodo               character varying          NULL          ← ¡EXISTE!
valor_anterior             numeric                    NULL          ← ¡EXISTE!
variacion_absoluta         numeric                    NULL          ← ¡EXISTE!
variacion_porcentual       numeric                    NULL          ← ¡EXISTE!
tendencia                  character varying          NULL          ← ¡EXISTE!
fuente_especifica          character varying          NULL
segmento_poblacion         character varying          NULL
notas                      text                       NULL
fecha_registro             timestamp with time zone  NOT NULL
embedding                  vector                     NULL
documento_id               bigint                     NULL (FK)
fragmento_id               bigint                     NULL (FK)
```

**REVELACIÓN CRÍTICA**: TODOS los campos mencionados en el prompt de datos cuantitativos **SÍ EXISTEN** en la base de datos: `categoria`, `tipo_periodo`, `valor_anterior`, `variacion_absoluta`, `variacion_porcentual`, `tendencia`.

## ANÁLISIS COMPARATIVO: PROMPTS vs MODELOS vs BASE DE DATOS

### ENTIDADES - COMPARACIÓN EXHAUSTIVA

| Campo | Prompt Entidades.md | Modelo persistencia.py | DB Real | Estado |
|-------|-------------------|----------------------|---------|--------|
| `id` | ✅ `id: 1` | ❌ `id_temporal_entidad: "1"` | ✅ `id: bigint` | **INCOHERENCIA** |
| `nombre` | ✅ `nombre: "Juan"` | ❌ `nombre_entidad: "Juan"` | ✅ `nombre: varchar` | **INCOHERENCIA** |
| `tipo` | ✅ `tipo: "PERSONA"` | ❌ `tipo_entidad: "PERSONA"` | ✅ `tipo: varchar` | **INCOHERENCIA** |
| `descripcion` | ✅ `descripcion: "texto"` | ❌ `descripcion_entidad: "texto"` | ✅ `descripcion: text` | **INCOHERENCIA** |
| `alias` | ✅ `alias: []` | ❌ `alias_entidad: []` | ✅ `alias: ARRAY` | **INCOHERENCIA** |
| `fecha_nacimiento` | ✅ `fecha_nacimiento: "2024-01-01"` | ❌ **FALTA** | ✅ `fecha_nacimiento: tstzrange` | **CAMPO PERDIDO** |
| `fecha_disolucion` | ✅ `fecha_disolucion: "2024-12-31"` | ❌ **FALTA** | ✅ `fecha_disolucion: tstzrange` | **CAMPO PERDIDO** |

**DIAGNÓSTICO**: El problema NO es que los campos no existan en la DB, sino que:
1. Los modelos de persistencia usan nombres completamente diferentes (`nombre` vs `nombre_entidad`)
2. Los modelos de persistencia NO INCLUYEN campos que SÍ existen en la DB
3. Esto fuerza conversiones manuales innecesarias y pérdida de datos

### HECHOS - COMPARACIÓN EXHAUSTIVA

| Campo | Prompt Hechos.md | Modelo persistencia.py | DB Real | Estado |
|-------|-----------------|----------------------|---------|--------|
| `precision_temporal` | ✅ Mencionado | ❌ **FALTA** | ✅ `precision_temporal: varchar` | **CAMPO PERDIDO** |
| `es_futuro` | ✅ `es_futuro: true` | ❌ **FALTA** | ⚠️ `es_evento_futuro: boolean` | **NOMBRE INCONSISTENTE** |
| `estado_programacion` | ✅ Mencionado | ❌ **FALTA** | ✅ `estado_programacion: varchar` | **CAMPO PERDIDO** |
| `fecha` | ✅ `fecha: {inicio, fin}` | ✅ `fecha_ocurrencia_hecho_inicio/fin` | ✅ `fecha_ocurrencia: tstzrange` | **FORMATO INCONSISTENTE** |

**DIAGNÓSTICO**: La base de datos tiene TODOS los campos, pero:
1. Los modelos de persistencia no los incluyen
2. Hay diferencias menores en nombres (`es_futuro` vs `es_evento_futuro`)
3. Los tipos de fecha son inconsistentes entre prompts y DB

### DATOS CUANTITATIVOS - COMPARACIÓN EXHAUSTIVA

| Campo | Prompt Datos.md | Modelo persistencia.py | DB Real | Estado |
|-------|----------------|----------------------|---------|--------|
| `categoria` | ✅ Mencionado | ❌ **FALTA** | ✅ `categoria: varchar` | **CAMPO PERDIDO** |
| `tipo_periodo` | ✅ Mencionado | ❌ **FALTA** | ✅ `tipo_periodo: varchar` | **CAMPO PERDIDO** |
| `tendencia` | ✅ Mencionado | ❌ **FALTA** | ✅ `tendencia: varchar` | **CAMPO PERDIDO** |
| `valor_anterior` | ✅ Mencionado | ❌ **FALTA** | ✅ `valor_anterior: numeric` | **CAMPO PERDIDO** |
| `variacion_absoluta` | ✅ Mencionado | ❌ **FALTA** | ✅ `variacion_absoluta: numeric` | **CAMPO PERDIDO** |
| `variacion_porcentual` | ✅ Mencionado | ❌ **FALTA** | ✅ `variacion_porcentual: numeric` | **CAMPO PERDIDO** |
| `periodo` | ✅ `periodo: {inicio, fin}` | ❌ **FALTA** | ✅ `periodo_referencia_inicio/fin: date` | **FORMATO INCONSISTENTE** |

**DIAGNÓSTICO**: La base de datos tiene TODO lo que piden los prompts, pero los modelos de persistencia NO incluyen ninguno de estos campos específicos.

## REVISIÓN CRÍTICA DE PROBLEMAS ORIGINALES

### PROBLEMA 2: NOMBRES DE CAMPOS - DIAGNÓSTICO ACTUALIZADO

**ANTES (ANÁLISIS INICIAL)**: "Los nombres de campos son completamente diferentes"
**DESPUÉS (INVESTIGACIÓN COMPLETA)**: 

La base de datos usa los nombres **CORRECTOS** que coinciden con los prompts:
- DB: `nombre`, Prompt: `nombre` ✅
- DB: `tipo`, Prompt: `tipo` ✅  
- DB: `descripcion`, Prompt: `descripcion` ✅

El problema está en **persistencia.py** que usa nombres artificiales:
- Modelo: `nombre_entidad` (❌ INCORRECTO)
- Modelo: `tipo_entidad` (❌ INCORRECTO)
- Modelo: `descripcion_entidad` (❌ INCORRECTO)

**SOLUCIÓN REAL**: Cambiar persistencia.py para usar los nombres de la DB, no inventar nombres nuevos.

### PROBLEMA 3: ESTRUCTURAS DE FECHAS - DIAGNÓSTICO ACTUALIZADO

**INVESTIGACIÓN DE TIPOS DE FECHA EN DB**:
- `entidades.fecha_nacimiento/fecha_disolucion`: `tstzrange` (rango de timestamps)
- `hechos.fecha_ocurrencia`: `tstzrange` (rango de timestamps)
- `citas_textuales.fecha_cita`: `timestamp with time zone` (timestamp único)
- `datos_cuantitativos.periodo_referencia_inicio/fin`: `date` (fechas separadas)

**DIAGNÓSTICO**: La base de datos es CONSISTENTE en su manejo de fechas:
- Para eventos que pueden tener duración: usa `tstzrange`
- Para eventos puntuales: usa `timestamp with time zone`
- Para periodos de referencia: usa `date` por separado

El problema está en que los **prompts no entienden los tipos de PostgreSQL** y usan formatos inconsistentes.

### PROBLEMA 6: CAMPOS PERDIDOS - CORRECCIÓN MAYOR

**ANTES (ANÁLISIS INCORRECTO)**:
> "Los prompts definen campos que no existen en persistencia:
> - fecha_nacimiento y fecha_disolucion de entidades
> - precision_temporal, es_futuro, estado_programacion de hechos"

**DESPUÉS (REALIDAD CONFIRMADA)**:
✅ **TODOS ESTOS CAMPOS EXISTEN EN LA BASE DE DATOS**

La investigación revela que el problema NO es que los campos no existan, sino que:
1. **Los modelos de persistencia.py están INCOMPLETOS**
2. **No incluyen campos que SÍ existen en la DB**
3. **Esto causa pérdida de datos durante la persistencia**

### PROBLEMA 5: MAPEO MANUAL COMPLEJO - CAUSA RAÍZ IDENTIFICADA

El mapeo manual existe porque **persistencia.py usa nombres incorrectos**:

```python
# LLM devuelve (correcto según DB):
{"nombre": "Juan García", "tipo": "PERSONA"}

# persistencia.py espera (incorrecto):
{"nombre_entidad": "Juan García", "tipo_entidad": "PERSONA"}

# DB real espera (correcto):
{"nombre": "Juan García", "tipo": "PERSONA"}
```

**CAUSA RAÍZ**: persistencia.py fue diseñado sin consultar el esquema real de la DB.

## ESTRATEGIA DE SOLUCIÓN DEFINITIVA

### PRINCIPIO FUNDAMENTAL
**LA BASE DE DATOS ES LA FUENTE DE VERDAD ABSOLUTA**

Todos los demás componentes (prompts, modelos, mapeos) deben alinearse con el esquema de la base de datos, no al revés.

### PLAN DE CORRECCIÓN BASADO EN INVESTIGACIÓN

#### FASE 1: CORRECCIÓN INMEDIATA (5 minutos)
1. **Problema 1**: Corregir referencias rotas en prompts
2. **Problema 4**: Corregir IDs no secuenciales en ejemplos

#### FASE 2: ALINEACIÓN CON BASE DE DATOS (30 minutos)
3. **Corregir persistencia.py**:
   - Cambiar `nombre_entidad` → `nombre` (coincide con DB)
   - Cambiar `tipo_entidad` → `tipo` (coincide con DB)
   - Cambiar `descripcion_entidad` → `descripcion` (coincide con DB)
   - Agregar `fecha_nacimiento` y `fecha_disolucion` que SÍ existen en DB

4. **Agregar campos perdidos a modelos**:
   - `precision_temporal`, `es_evento_futuro`, `estado_programacion` en hechos
   - `categoria`, `tipo_periodo`, `tendencia`, etc. en datos cuantitativos

5. **Estandarizar nombres de campos**:
   - Usar `es_evento_futuro` (DB) en lugar de `es_futuro` (prompt)
   - Sincronizar todos los nombres con la DB real

#### FASE 3: OPTIMIZACIÓN DE FECHAS (15 minutos)
6. **Estandarizar formatos de fecha en prompts**:
   - Para `tstzrange`: Usar strings "YYYY-MM-DD" (PostgreSQL convierte automáticamente)
   - Para `timestamp`: Usar strings "YYYY-MM-DDTHH:MM:SSZ"
   - Para `date`: Usar strings "YYYY-MM-DD"

## IMPACTO ESPERADO DE LA CORRECCIÓN

### ANTES (ESTADO ACTUAL PROBLEMÁTICO):
- ❌ Modelos usan nombres incorrectos (`nombre_entidad` vs `nombre`)
- ❌ Campos existentes en DB se pierden porque no están en modelos
- ❌ Mapeos manuales complejos e innecesarios
- ❌ Referencias rotas entre fases
- ❌ Inconsistencias de formato de fecha

### DESPUÉS (ESTADO OBJETIVO):
- ✅ Modelos usan nombres exactos de la DB
- ✅ TODOS los campos de la DB están incluidos en modelos
- ✅ Mapeo directo sin conversiones manuales
- ✅ Referencias correctas entre fases
- ✅ Formatos de fecha consistentes y compatibles con PostgreSQL

## CONCLUSIONES DE LA INVESTIGACIÓN

### HALLAZGO PRINCIPAL
**La base de datos Supabase está BIEN DISEÑADA y contiene TODOS los campos necesarios**. El problema no está en la DB, sino en que:

1. **Los modelos Python están desactualizados** respecto al esquema real
2. **Se inventaron nombres de campos** en lugar de usar los de la DB
3. **Nunca se hizo una sincronización** entre código y esquema de BD

### RECOMENDACIÓN ESTRATÉGICA
- **NO CAMBIAR LA BASE DE DATOS**: Está correctamente diseñada
- **ACTUALIZAR TODOS LOS MODELOS**: Para que coincidan exactamente con la DB
- **ELIMINAR MAPEOS MANUALES**: Usar nombres directos de la DB
- **IMPLEMENTAR VALIDACIÓN AUTOMÁTICA**: Para que esto no vuelva a pasar

### TIEMPO DE IMPLEMENTACIÓN ESTIMADO
- **Correcciones urgentes**: 5 minutos
- **Alineación completa con DB**: 45 minutos
- **Pruebas y validación**: 15 minutos
- **TOTAL**: 65 minutos para resolver todos los problemas de coherencia

Esta investigación demuestra que la solución es más simple de lo inicialmente estimado, porque **la base de datos ya tiene todo lo necesario**.