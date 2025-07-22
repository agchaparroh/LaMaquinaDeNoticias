# 🔴 ERROR: GroqAPIError missing phase parameter
## 📅 Fecha: 2025-01-22 05:50

### 🎯 Problema
- **Error**: `GroqAPIError.__init__() missing 1 required positional argument: 'phase'`
- **Impacto**: Fase 4 falla completamente, no se extraen hechos
- **Consecuencia**: Pipeline genera relaciones sobre hechos inexistentes

### 🔍 Diagnóstico
1. **Síntoma inicial**: "Payload contiene: 0 hechos, 5 relaciones"
2. **Causa raíz**: GroqAPIError en fase_4_hechos.py llamado sin parámetro `phase`
3. **Efecto cascada**:
   - Fase 4 falla → 0 hechos extraídos
   - Fase 7B genera 5 relaciones sin verificar que existan hechos
   - PayloadBuilder valida y encuentra IDs inexistentes

### 💡 Solución Implementada
```python
# Antes:
raise GroqAPIError(f"Error al extraer hechos después de {max_retries} intentos: {str(e)}")

# Después:
raise GroqAPIError(
    f"Error al extraer hechos después de {max_retries} intentos: {str(e)}",
    phase=ErrorPhase.EXTRACTION
)
```

### ✅ Resultados
- Fase 4 ahora completa: "6 hechos extraídos"
- Payload correcto: "6 hechos, 5 relaciones"
- IDs disponibles: {'1', '3', '6', '5', '2', '4'}
- Checksum generado exitosamente

### 📊 Métricas
- Tiempo de diagnóstico: 45 minutos
- Archivos afectados: 2 (fase_4_hechos.py corregido, otros 5 pendientes)
- Impacto: Crítico - bloqueaba todo el pipeline

### 🔧 Trabajo Pendiente
- Corregir el mismo error en otras fases (fase_1, fase_2, fase_3, fase_5, fase_6)
- Investigar nuevo error: "Se requiere articulo_id o url"

### 📝 Lecciones Aprendidas
1. Los errores de API deben incluir siempre el contexto de fase
2. El pipeline no debería continuar si una fase crítica falla
3. Fase 7 debería validar que existan hechos antes de generar relaciones