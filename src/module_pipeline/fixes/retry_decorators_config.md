# Guía de Configuración de Decoradores de Retry
## Module Pipeline - La Máquina de Noticias

### Configuraciones Actuales

#### 1. **@retry_groq_api**
- **Max Attempts**: 2 (máximo 3 intentos totales incluyendo el inicial)
- **Wait Time**: 5 segundos fijos + jitter aleatorio de 0-1 segundo
- **Aplicable a**: Todas las llamadas a la API de Groq
- **Excepciones que disparan retry**:
  - APIConnectionError
  - RateLimitError
  - APIStatusError
  - TimeoutError
  - ConnectionError

**Justificación**: 
- Groq es crítico para el procesamiento pero no queremos sobrecargar la API
- El jitter ayuda a distribuir la carga cuando múltiples workers reintentan
- 5 segundos permite que problemas transitorios se resuelvan

#### 2. **@retry_supabase_rpc**
- **Connection Retries**: 1 (máximo 2 intentos totales)
- **Validation Retries**: 0 (sin reintentos)
- **Wait Time**: 2 segundos fijos (hardcoded)
- **Aplicable a**: Todas las llamadas RPC a Supabase
- **Comportamiento diferenciado**:
  - ConnectionError/TimeoutError: Reintenta 1 vez
  - ValueError/Exception general: No reintenta

**Justificación**:
- Los errores de validación no se resuelven reintentando
- Los errores de conexión son típicamente transitorios
- Menor tiempo de espera porque Supabase es local/regional

### Parámetros Ajustados por Criticidad

#### Fase 1 - Triaje (CRÍTICA)
- Groq API para relevancia: Usa configuración estándar
- Fallback: Acepta el artículo si falla

#### Fase 2 - Extracción (CRÍTICA)
- Groq API para extracción: Usa configuración estándar
- Fallback: Crea hecho básico del título

#### Fase 3 - Citas y Datos (NO CRÍTICA)
- Groq API para citas: Usa configuración estándar
- Fallback: Continúa sin citas/datos

#### Fase 4 - Normalización (SEMI-CRÍTICA)
- Supabase RPC: Usa configuración estándar
- Groq API para relaciones: Usa configuración estándar
- Fallback: Trata entidades como nuevas

#### Fase 5 - Persistencia (CRÍTICA)
- Supabase RPC: Usa configuración estándar
- Fallback: Guarda en tabla de errores

### Logging Integrado

Todos los decoradores ahora incluyen:
- `before_log`: Registra intentos de retry (nivel WARNING)
- `after_log`: Registra éxitos después de retry (nivel INFO)
- Conversión automática a excepciones personalizadas con support_code

### Recomendaciones de Uso

1. **No modificar** los parámetros por defecto a menos que sea absolutamente necesario
2. **Siempre** usar los decoradores en métodos que llamen a servicios externos
3. **Nunca** usar decoradores en operaciones locales o de memoria
4. **Documentar** cualquier cambio en los parámetros con justificación clara

### Verificación de Funcionamiento

Ejecutar el script de verificación:
```bash
python tests/test_retry_decorators_verify.py
```

Este script verifica:
- ✅ Groq reintenta correctamente con los tiempos configurados
- ✅ Supabase diferencia entre errores de conexión y validación
- ✅ Las excepciones personalizadas se generan correctamente
- ✅ El logging funciona en todos los casos
