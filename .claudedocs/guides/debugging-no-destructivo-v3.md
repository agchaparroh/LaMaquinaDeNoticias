# 🚀 Guía Práctica de PRPs para Debugging No Destructivo v3.0

> **Propósito**: Crear PRPs efectivos para eliminar errores sin crear nuevos problemas  
> **Filosofía**: "Si funciona en producción, NO es un error"  
> **Enfoque**: Templates listos para copiar y ejecutar

---

## 🎯 DECISION TREE: ¿Necesito un PRP?

```mermaid
¿Error encontrado?
    ├─ NO → No hacer nada
    └─ SÍ → ¿Es paralizante?
            ├─ NO → Documentar y dejar
            └─ SÍ → ¿Es complejo?
                    ├─ NO → Fix directo (30 min)
                    └─ SÍ → CREAR PRP
```

### 🔴 Problemas Paralizantes (SÍ debuggear)
- **Servicio caído**: HTTP 500/502/503, crashes, timeouts
- **Funcionalidad rota**: Features que no responden
- **Pérdida de datos**: Información desaparece o se corrompe
- **Usuario bloqueado**: No puede hacer login o completar acciones
- **Seguridad comprometida**: Vulnerabilidad activa

### ✅ NO son Problemas (NO tocar)
- Warnings del linter
- Code smells funcionales
- Performance "mejorable"
- Tests <100% cobertura
- Deuda técnica sin impacto

---

## ⚖️ NORMAS FUNDAMENTALES DE DEBUGGING

### 🎯 Criterios para la Solución Correcta

Toda solución de debugging DEBE cumplir estos criterios:

#### 1. 🏗️ **ROBUSTEZ Y SOSTENIBILIDAD**
- La solución debe ser **sostenible a largo plazo**
- Prohibidos los parches temporales o "quick fixes"
- Si no puedes explicar por qué funcionará en 6 meses, no es la solución correcta

#### 2. 🚫 **NO ROTUNDO A LA SOBREINGENIERÍA**
- Buscamos implementación robusta y "a prueba de balas"
- SIN piezas móviles innecesarias que añadan complejidad
- Rechazar mejoras marginales que aumenten fragilidad
- **Lo sencillo es mejor**: Si necesitas más de 3 pasos para explicarlo, es demasiado complejo

#### 3. 🛡️ **SOLUCIONES NO DESTRUCTIVAS**
- VERIFICAR que conoces **perfectamente** el papel de la implementación anterior
- Asegurar que NO rompes ninguna funcionalidad existente
- Si no entiendes algo al 100%, NO lo toques
- Mejor dejar un bug conocido que crear 3 bugs nuevos

### 📏 Regla de Oro para Evaluar Soluciones

Antes de implementar cualquier fix, responde:

1. **¿Es simple?** → Si necesitas un diagrama, es demasiado complejo
2. **¿Es completo?** → Debe resolver TODAS las instancias del problema
3. **¿Es seguro?** → Cero posibilidad de romper funcionalidad existente
4. **¿Es sostenible?** → Funcionará sin mantenimiento adicional

**Si alguna respuesta es NO → Buscar otra solución**

### 🚨 Red Flags - Señales de Mala Solución

- 🔴 "Esto debería funcionar por ahora..."
- 🔴 "Es temporal hasta que..."
- 🔴 "No estoy seguro pero creo que..."
- 🔴 "Añadí esta validación por si acaso..."
- 🔴 "Refactoricé de paso para mejorar..."

---

## 📋 PRP TEMPLATE: Error Elimination Protocol

### Copy-Paste Template Básico

```markdown
# 🚨 PRP: Error Elimination - [MÓDULO/SERVICIO]
> **Fecha**: [YYYY-MM-DD]  
> **Tipo**: debugging-no-destructivo  
> **Prioridad**: CRITICAL

## 🎯 ACCIÓN INMEDIATA - [Error Actual]

### Paso Actual:
```bash
# [Comando específico a ejecutar AHORA]
```

## 📊 ESTADO ACTUAL
- **Errores encontrados**: 0
- **Errores resueltos**: 0  
- **Error en progreso**: NINGUNO
- **Tiempo estimado**: 2-4 horas

## 🤖 AUTOMATED TRIGGERS ACTIVOS

### Trigger Pattern Matching:
Si el error contiene: `["keyword argument", "has no attribute", "cannot import", "NameError", "signature mismatch"]`

**PROTOCOLO AUTOMÁTICO:**
1. ⛔ **STOP** - No hacer fix parcial
2. 🔍 **Task tool**: buscar patrón en TODA la codebase
3. 📊 **Mapear scope**: identificar TODOS los archivos afectados
4. 🔧 **MultiEdit**: aplicar cambios de una vez
5. ✅ **Test final**: validación completa

## 🏁 CRITERIOS DE FINALIZACIÓN

### ✅ Éxito (TODOS requeridos):
- [ ] Sistema operativo sin bloqueos
- [ ] Tests pasando sin regresiones
- [ ] Al menos 1 flujo end-to-end exitoso
- [ ] Cero errores CRITICAL/HIGH activos

### 🚨 Escalamiento (si ALGUNO ocurre):
- [ ] >10 errores críticos encontrados
- [ ] Cualquier error >1 hora de debug
- [ ] Problemas de infraestructura
- [ ] Performance degradada >50%

## 📚 REGISTRO HISTÓRICO
<details>
<summary>Ver historial de errores resueltos</summary>

### E001: [Descripción]
- **Encontrado**: [timestamp]
- **Resuelto**: [timestamp]
- **Solución**: [breve descripción]
- **Archivos**: [lista]

</details>

## ⚖️ NORMAS DE DEBUGGING (Recordatorio)
1. **Robustez**: Soluciones sostenibles, no parches
2. **Simplicidad**: No sobreingeniería, lo simple es mejor
3. **No destructivo**: Entender 100% antes de cambiar

## 📋 COMANDOS DE REFERENCIA

### Diagnóstico inicial:
```bash
# 1. Checkpoint
git checkout -b debug-[nombre]-$(date +%Y%m%d-%H%M)

# 2. Health check completo
curl -X GET http://localhost:8000/health -v

# 3. Logs últimos errores
docker logs [container] --tail 100 | grep -E "ERROR|CRITICAL"

# 4. Test base
pytest tests/ -v --tb=short
```

### TodoWrite Integration:
```bash
TodoWrite: "PRP Debug: Diagnóstico inicial [módulo]" (pending)
TodoWrite: "PRP Debug: Fix E001 - [descripción]" (in_progress)
```
```

---

## 🔧 PRP TEMPLATES ESPECIALIZADOS

### 🐛 Template: API Error 500 Debug

```markdown
# 🚨 PRP: API Error 500 - [Endpoint]

## 🎯 ACCIÓN INMEDIATA

```bash
# 1. Verificar servicio
curl -X POST http://localhost:8000/[endpoint] \
  -H "Content-Type: application/json" \
  -d '{"test": "minimal"}' \
  -v

# 2. Logs del error
docker logs [api-container] --tail 50 | grep -A10 -B10 "500"

# 3. Check BD
docker exec [db-container] psql -U user -d database -c "SELECT 1;"
```

## 🤖 PROTOCOLO ESPECÍFICO API 500

1. **Diagnóstico por capas**:
   ```bash
   # Capa 1: Conectividad
   nc -zv localhost 8000
   
   # Capa 2: API Health
   curl http://localhost:8000/health
   
   # Capa 3: BD Connection
   docker exec [api] python -c "from db import test_connection; test_connection()"
   
   # Capa 4: Endpoint específico
   curl -X POST http://localhost:8000/[endpoint] -d @test-minimal.json
   ```

2. **Si es timeout**:
   ```bash
   # Medir tiempos por fase
   docker logs [container] | grep "Fase" | tail -20
   ```

3. **Si es memory**:
   ```bash
   # Monitor en vivo
   docker stats [container] --no-stream
   ```
```

### 🔍 Template: Performance Degradation Debug

```markdown
# 🚨 PRP: Performance Degradation - [Servicio]

## 🎯 ACCIÓN INMEDIATA

```bash
# Benchmark actual vs esperado
time curl -X POST http://localhost:8000/process -d @test-standard.json

# Expected: <2s
# Actual: ??s
```

## 🤖 PROTOCOLO PERFORMANCE

1. **Identificar bottleneck**:
   ```bash
   # Timing por fase
   docker logs [container] | grep -E "Fase.*completada|elapsed" | tail -30
   ```

2. **Métricas de recursos**:
   ```bash
   # CPU/Memory en tiempo real durante request
   docker stats [container] &
   curl -X POST http://localhost:8000/process -d @test-heavy.json
   ```

3. **Query analysis** (si aplica):
   ```bash
   # Logs de queries lentas
   docker logs [db-container] | grep -E "duration: [0-9]{4,}"
   ```
```

### 🔄 Template: Funciona Local, Falla Producción

```markdown
# 🚨 PRP: Environment Mismatch Debug

## 🎯 ACCIÓN INMEDIATA

```bash
# Comparar configuraciones
diff -u .env.local .env.production

# Verificar versiones
docker exec [container] pip freeze > prod-deps.txt
pip freeze > local-deps.txt
diff -u local-deps.txt prod-deps.txt
```

## 🤖 PROTOCOLO ENV MISMATCH

1. **Detectar diferencias**:
   ```bash
   # Variables de entorno
   docker exec [prod-container] env | sort > prod-env.txt
   env | sort > local-env.txt
   diff -u local-env.txt prod-env.txt
   
   # Permisos de archivos
   docker exec [prod-container] ls -la /app/ > prod-perms.txt
   ```

2. **Replicar producción localmente**:
   ```bash
   # Usar exactamente la misma imagen
   docker pull [prod-image:tag]
   docker run --env-file .env.production [prod-image:tag]
   ```
```

---

## 🚀 AUTOMATED TRIGGERS FRAMEWORK

### 📌 Configuración de Triggers

```python
# automated_triggers.py
TRIGGER_PATTERNS = {
    "python": [
        "keyword argument",
        "has no attribute",
        "cannot import", 
        "NameError",
        "signature mismatch",
        "TypeError",
        "AttributeError"
    ],
    "javascript": [
        "Cannot read property",
        "is not a function",
        "undefined is not",
        "ReferenceError"
    ],
    "api": [
        "500 Internal",
        "502 Bad Gateway",
        "Connection refused",
        "timeout"
    ]
}

def should_trigger_systematic_search(error_message):
    for category, patterns in TRIGGER_PATTERNS.items():
        if any(pattern in error_message for pattern in patterns):
            return True, category
    return False, None
```

### 🎯 Protocolo de Ejecución

```bash
# Si trigger activado:
TRIGGERED=true
CATEGORY="python"  # o el que corresponda

# Búsqueda sistemática
if [ "$TRIGGERED" = true ]; then
    echo "🤖 AUTOMATED TRIGGER ACTIVATED: $CATEGORY"
    
    # 1. Búsqueda exhaustiva
    grep -r "el_patron_del_error" . --include="*.py" > affected_files.txt
    
    # 2. Análisis de impacto
    echo "Files affected: $(wc -l < affected_files.txt)"
    
    # 3. Fix sistemático
    # Usar MultiEdit con todos los archivos
fi
```

---

## 📊 EJEMPLOS DE PRPs EXITOSOS

### ✅ Caso 1: Pipeline Error E001-E004
```markdown
# Tiempo total: 45 minutos
# Errores resueltos: 4
# Ciclos por error: 1

## Clave del éxito:
1. Automated Triggers detectó patrón común
2. MultiEdit aplicó cambios a 12 archivos simultáneamente  
3. Un solo test final validó todo
```

### ✅ Caso 2: Memory Leak en Producción
```markdown
# Tiempo total: 2 horas
# Problema: OOM después de 1000 requests

## Solución efectiva:
1. Diagnóstico en vivo identificó acumulación en cache
2. Fix quirúrgico: límite de cache + TTL
3. Validación: 10,000 requests sin degradación
```

---

## 🎯 COMANDOS COPY-PASTE READY

### 🔍 Diagnóstico Inicial Completo
```bash
# Setup de debugging
mkdir -p .claudedocs/debugging/BUG-$(date +%Y%m%d-%H%M)
cd .claudedocs/debugging/BUG-$(date +%Y%m%d-%H%M)

# Captura estado inicial
echo "## Estado Inicial - $(date)" > 1-diagnostico.md
docker ps >> 1-diagnostico.md
docker logs [container] --tail 100 >> 1-diagnostico.md

# Test base
pytest tests/ -v --tb=short > test-baseline.txt 2>&1

# Crear checkpoint git
git checkout -b debug-$(date +%Y%m%d-%H%M)
git add -A && git commit -m "checkpoint: inicio debug $(date)"
```

### 🧪 Test en Vivo con Métricas
```bash
# Preparar datos de prueba
cat > test-minimal.json << 'EOF'
{"data": "test mínimo"}
EOF

cat > test-normal.json << 'EOF'
{"data": "Lorem ipsum dolor sit amet, consectetur adipiscing elit..."}
EOF

cat > test-heavy.json << 'EOF'
{"data": "[5000 palabras de contenido...]"}
EOF

# Ejecutar con métricas
for file in test-*.json; do
    echo "=== Testing with $file ==="
    time curl -X POST http://localhost:8000/process \
        -H "Content-Type: application/json" \
        -d @$file \
        -w "\nHTTP Code: %{http_code}\nTotal Time: %{time_total}s\n"
    echo ""
done
```

### 🔧 Fix Pattern Sistemático
```bash
# Cuando Automated Trigger se activa
PATTERN="el_patron_a_buscar"

# 1. Encontrar todos los afectados
find . -name "*.py" -type f -exec grep -l "$PATTERN" {} \; > affected_files.txt

# 2. Backup antes de cambios
tar -czf backup-$(date +%Y%m%d-%H%M).tar.gz $(cat affected_files.txt)

# 3. Preview de cambios
for file in $(cat affected_files.txt); do
    echo "=== $file ==="
    grep -n "$PATTERN" "$file"
done

# 4. Aplicar fix con confirmación
echo "Found $(wc -l < affected_files.txt) files. Proceed? [y/n]"
read confirm
if [ "$confirm" = "y" ]; then
    # MultiEdit aquí
fi
```

### ✅ Validación Final
```bash
# Script de validación completa
cat > validate_fix.sh << 'EOF'
#!/bin/bash
echo "🔍 Validación de Fix Completa"

# 1. Tests
echo "1️⃣ Running tests..."
pytest tests/ -v

# 2. Servicio activo
echo "2️⃣ Checking service..."
curl -s http://localhost:8000/health | jq .

# 3. Procesamiento E2E
echo "3️⃣ End-to-end test..."
curl -X POST http://localhost:8000/process \
    -d '{"data": "test"}' \
    -H "Content-Type: application/json"

# 4. No errores nuevos
echo "4️⃣ Checking for new errors..."
docker logs [container] --since 5m | grep -E "ERROR|CRITICAL" || echo "✅ No errors"

echo "✅ Validación completa"
EOF

chmod +x validate_fix.sh
./validate_fix.sh
```

---

## 🔗 INTEGRACIÓN CON TODOWRITE

### Setup Inicial
```bash
# Al comenzar PRP
TodoWrite << 'EOF'
[
  {
    "id": "debug-001",
    "content": "PRP Debug: Setup inicial y diagnóstico",
    "status": "in_progress",
    "priority": "high"
  }
]
EOF
```

### Por Cada Error
```bash
# Template para nuevo error
TodoWrite << 'EOF'
[
  {
    "id": "debug-e001",
    "content": "Fix E001: [descripción del error]",
    "status": "pending",
    "priority": "high"
  }
]
EOF
```

### Actualización de Estado
```bash
# Marcar como completado
TodoWrite update debug-e001 completed
```

---

## 📈 MÉTRICAS DE ÉXITO

### KPIs del PRP
- **Errores resueltos por ciclo**: Target = 1 (vs 3-5 sin metodología)
- **Tiempo por error**: <1 hora para 90% de casos
- **Regresiones introducidas**: 0
- **Cobertura de Automated Triggers**: >80% de errores comunes

### Dashboard de Progreso
```bash
# Generar reporte
cat > debug_report.sh << 'EOF'
#!/bin/bash
echo "📊 Debug Progress Report"
echo "======================="
echo "Errors found: $(grep -c "^### E[0-9]" .claudedocs/debugging/*/registro.md)"
echo "Errors fixed: $(grep -c "FIXED" .claudedocs/debugging/*/registro.md)"
echo "Time elapsed: $(git log --format="%ar" -1)"
echo "Files changed: $(git diff --name-only HEAD~1)"
EOF
```

---

## 🚨 EJEMPLOS: BUENAS vs MALAS SOLUCIONES

### ❌ MALA: Parche Temporal
```python
# Problema: user puede ser None
def get_user_name(user):
    # MALA SOLUCIÓN - parche temporal
    try:
        return user.name
    except:
        return "Unknown"  # 🔴 Oculta el problema real
```

### ✅ BUENA: Solución Robusta
```python
# BUENA SOLUCIÓN - manejo explícito
def get_user_name(user):
    if user is None:
        logger.warning("get_user_name called with None user")
        return None
    return user.name
```

### ❌ MALA: Sobreingeniería
```python
# Problema: validar email
# MALA SOLUCIÓN - demasiado compleja
class EmailValidatorFactory:
    def create_validator(self):
        return EmailValidatorStrategy(
            RegexValidator(),
            DNSValidator(),
            SMTPValidator()
        )  # 🔴 3 clases para validar 1 string
```

### ✅ BUENA: Simple y Efectiva
```python
# BUENA SOLUCIÓN - simple y clara
def is_valid_email(email):
    return bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email))
```

### ❌ MALA: Destructiva
```python
# Problema: optimizar queries
# MALA SOLUCIÓN - cambia comportamiento sin entender
def get_users():
    # return db.query(User).all()  # 🔴 Comentado sin entender
    return db.query(User).limit(100).all()  # "optimización"
```

### ✅ BUENA: Preserva Funcionalidad
```python
# BUENA SOLUCIÓN - añade opción sin romper
def get_users(limit=None):
    query = db.query(User)
    if limit:
        query = query.limit(limit)
    return query.all()
```

---

## 🎯 RESUMEN EJECUTIVO

### Para Crear un PRP de Debug Efectivo:

1. **Usa el Decision Tree** → ¿Es paralizante? ¿Es complejo? → PRP
2. **Aplica las NORMAS** → Robustez, Simplicidad, No destructivo
3. **Copia el template base** → Personaliza solo lo necesario
4. **Activa Automated Triggers** → Deja que detecte patrones
5. **Sigue los pasos específicos** → No te saltes ninguno
6. **Integra con TodoWrite** → Tracking automático
6. **Valida con el script final** → Confirma éxito completo

### Comandos Más Usados:
```bash
# Inicio rápido
git checkout -b debug-$(date +%Y%m%d-%H%M)
mkdir -p .claudedocs/debugging/BUG-$(date +%Y%m%d-%H%M)

# Diagnóstico
docker logs [container] --tail 100 | grep -E "ERROR|CRITICAL"
curl -X POST http://localhost:8000/[endpoint] -d @test.json -v

# Fix sistemático
find . -name "*.py" -exec grep -l "pattern" {} \; > affected.txt

# Validación
pytest tests/ -v && curl http://localhost:8000/health
```

---

> **"El mejor PRP es el que resuelve todo en un ciclo. Esta guía lo hace posible."**

*Debugging No Destructivo v3.0 | Optimizado para ejecución inmediata | La Máquina de Noticias*