# ERROR 1: null value in column "nombre" of relation "entidades"

## Información del Error
- **Fecha/Hora**: 2025-07-19 07:44:10.755
- **ID Artículo**: 1100
- **Código SQL**: 23502 (NOT NULL constraint violation)
- **Tabla afectada**: entidades
- **Campo problemático**: nombre

## Contexto del Error
1. El spider ejecutó correctamente y almacenó el artículo con ID 1100
2. El connector procesó el archivo JSON y lo envió al pipeline
3. El pipeline procesó las 7 fases exitosamente:
   - ✅ Fase 1: Triaje
   - ✅ Fase 2: Simplificación
   - ✅ Fase 3: Extracción de 12 entidades
   - ✅ Fase 4: Extracción de 7 hechos
   - ✅ Fase 6: Citas (0 extraídas)
   - ✅ Fase 7: Normalización y relaciones
4. ❌ Error al persistir con RPC actualizar_articulo_procesado

## Entidades Procesadas
Según los logs:
- EEUU (ORGANIZACION)
- Steve Witkoff (PERSONA)
- Israe (LUGAR) [sic - parece truncado]
- Movimiento de Resistencia Islámica (Hamás) (ORGANIZACION)
- Franja de Gaza (LUGAR)
- Benjamin Netanyahu (PERSONA)
- Donald Trump (PERSONA)
- JD Vance (PERSONA)
- Mayedal Ansari (PERSONA)
- Qatar (LUGAR)
- Doha (LUGAR)
- Acuerdo de alto el fuego (EVENTO)

Total: 12 entidades (todas no normalizadas)

## Hipótesis del Problema

### Hipótesis A: Desajuste entre modelo y RPC
**Probabilidad**: ALTA
- El modelo del pipeline envía un campo diferente al que espera la RPC
- La RPC espera `nombre_entidad` pero recibe `nombre` o viceversa
- **Evidencia a favor**: Error específico menciona columna "nombre"
- **Forma de verificar**: Revisar payload builder y estructura esperada por RPC

### Hipótesis B: Entidad con nombre vacío
**Probabilidad**: MEDIA
- Una de las 12 entidades tiene nombre null o vacío
- El modelo permite null pero la BD no
- **Evidencia a favor**: El error es de constraint NOT NULL
- **Evidencia en contra**: Los logs muestran todas las entidades con nombres
- **Forma de verificar**: Imprimir payload completo antes de enviar

### Hipótesis C: Error en transformación de datos
**Probabilidad**: MEDIA
- Durante la construcción del payload se pierde el valor del nombre
- Problema en la serialización/deserialización
- **Evidencia a favor**: El procesamiento fue exitoso hasta la persistencia
- **Forma de verificar**: Debugging del payload builder

### Hipótesis D: Problema con caracteres especiales
**Probabilidad**: BAJA
- El nombre "Israe" aparece truncado en logs
- Posible problema con encoding o caracteres especiales
- **Evidencia en contra**: Otros nombres con caracteres especiales funcionan
- **Forma de verificar**: Revisar el payload con nombres problemáticos

## Próximos Pasos
1. Examinar el payload builder para ver cómo se estructuran las entidades
2. Revisar la RPC para confirmar qué campos espera exactamente
3. Añadir logging detallado del payload antes de enviarlo
4. Verificar si hay diferencias entre lo que envía el pipeline y lo que espera la RPC