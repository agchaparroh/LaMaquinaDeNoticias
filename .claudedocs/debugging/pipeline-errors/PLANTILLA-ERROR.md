# ERROR: [Título descriptivo del error]

## 📋 INFORMACIÓN GENERAL
- **ID**: ERROR-YYYYMMDD-HHMM
- **Fecha detección**: YYYY-MM-DD HH:MM
- **Fecha resolución**: YYYY-MM-DD HH:MM (o "En progreso")
- **Estado**: 🔴 ACTIVO | 🟡 EN INVESTIGACIÓN | ✅ RESUELTO
- **Severidad**: CRÍTICA | ALTA | MEDIA | BAJA
- **Impacto**: [Descripción del impacto en el sistema]

## 🔍 DESCRIPCIÓN DEL PROBLEMA

### Mensaje de error
```
[Mensaje de error completo tal como aparece en los logs]
Código: [Si aplica]
```

### Stack trace completo
```
[Stack trace completo si está disponible]
```

### Contexto
- **Componente afectado**: [Pipeline, Supabase, Docker, etc.]
- **Operación en curso**: [Qué estaba haciendo el sistema]
- **Datos de entrada**: [Tipo/tamaño de datos procesados]
- **Frecuencia**: [Primera vez, intermitente, constante]
- **Condiciones de reproducción**: [Cómo reproducir el error]

## 📊 ANÁLISIS PRP APLICADO

### PASO 1: CAPTURA COMPLETA
- **Logs capturados**: [Enlaces o referencias a logs]
- **Estado del sistema**: [CPU, memoria, conexiones]
- **Cambios recientes**: [Deploys, configuración, código]

### PASO 2: ANÁLISIS MULTI-DIMENSIONAL
- **Temporal**: [¿Cuándo empezó? ¿Patrón temporal?]
- **Causal**: [¿Qué cambió antes del error?]
- **Dependencias**: [Componentes involucrados y sus interacciones]
- **Datos**: [¿Específico a ciertos datos o general?]
- **Código**: [Asunciones del código que pueden estar fallando]

### PASO 3: HIPÓTESIS GENERADAS

#### Hipótesis A: [Título] - Probabilidad: XX%
- **Descripción**: [Explicación detallada]
- **Evidencia a favor**: 
  - [Punto 1]
  - [Punto 2]
- **Evidencia en contra**: 
  - [Punto 1]
  - [Punto 2]
- **Verificación realizada**: [Método y resultado]

#### Hipótesis B: [Título] - Probabilidad: XX%
- **Descripción**: [Explicación detallada]
- **Evidencia a favor**: 
  - [Punto 1]
  - [Punto 2]
- **Evidencia en contra**: 
  - [Punto 1]
  - [Punto 2]
- **Verificación realizada**: [Método y resultado]

#### Hipótesis C: [Título] - Probabilidad: XX%
- **Descripción**: [Explicación detallada]
- **Evidencia a favor**: 
  - [Punto 1]
  - [Punto 2]
- **Evidencia en contra**: 
  - [Punto 1]
  - [Punto 2]
- **Verificación realizada**: [Método y resultado]

### PASO 4: VERIFICACIÓN SISTEMÁTICA
```bash
# Comandos/scripts utilizados para verificar
[Comando 1]
[Comando 2]
```

**Resultados de verificación**:
1. Test A: [Descripción] → [Resultado]
2. Test B: [Descripción] → [Resultado]
3. Test C: [Descripción] → [Resultado]

### PASO 5: CAUSA RAÍZ IDENTIFICADA
[Explicación clara y concisa de la causa raíz del problema]

## 🛠️ SOLUCIÓN IMPLEMENTADA

### Descripción de la solución
[Explicación de qué se cambió y por qué]

### Cambios de código
```diff
- // Código problemático
- [líneas de código original]

+ // Código corregido
+ [líneas de código nuevo]
```

### Archivos modificados
- `path/to/file1.py` - [Descripción del cambio]
- `path/to/file2.py` - [Descripción del cambio]

### Verificación de la solución
- [ ] Error original no se reproduce
- [ ] Tests pasan exitosamente
- [ ] Sin efectos secundarios detectados
- [ ] Sistema cumple criterios de éxito

## 📈 RESULTADOS

### Métricas post-fix
- **Performance**: [Comparación antes/después]
- **Estabilidad**: [Mejoras observadas]
- **Persistencia en Supabase**: [Estado]

### Pruebas realizadas
1. [Prueba 1 y resultado]
2. [Prueba 2 y resultado]
3. [Prueba 3 y resultado]

## 💡 LECCIONES APRENDIDAS

1. **Técnica**: [Qué aprendimos sobre el sistema/código]
2. **Proceso**: [Qué aprendimos sobre el debugging]
3. **Prevención**: [Cómo evitar este error en el futuro]

## 🔗 REFERENCIAS

- **PR/Commit**: [Link al PR o commit con el fix]
- **Documentación relacionada**: [Links relevantes]
- **Issues relacionados**: [Si aplica]

---

*Documento generado siguiendo el protocolo PRP*