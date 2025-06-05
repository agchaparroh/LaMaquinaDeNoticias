# 📦 Instrucciones de Instalación de Dependencias
## Module Pipeline - La Máquina de Noticias

**Fecha:** $(date)  
**Estado:** Versiones sincronizadas con ecosistema (ver `version_analysis.md`)

## 🎯 Objetivo

Instalar todas las dependencias del module_pipeline con versiones sincronizadas con `module_connector` y `module_scraper` para garantizar compatibilidad arquitectónica.

## 🔍 Verificación de Versiones Sincronizadas

Las siguientes librerías han sido sincronizadas con el ecosistema:

| Librería | Versión Final | Sincronizada con | Estado |
|----------|---------------|------------------|--------|
| `pydantic` | 2.11.5 | module_connector | ✅ Compatible |
| `tenacity` | 9.1.2 | module_connector | ✅ Compatible |
| `loguru` | 0.7.3 | module_connector | ✅ Compatible |
| `python-dotenv` | 1.1.0 | module_connector | ✅ Compatible |
| `supabase` | 2.15.2 | Versión avanzada | ✅ RPCs requeridas |

## 🚀 Instalación (Opción 1: Automática)

### Windows:
```cmd
# Navegar al directorio del proyecto
cd C:\Users\DELL\Desktop\PruebaWindsurfAI\LaMaquinaDeNoticias\src\module_pipeline

# Ejecutar script de instalación
install_dependencies.bat
```

### Linux/macOS:
```bash
# Navegar al directorio del proyecto
cd /path/to/module_pipeline

# Hacer ejecutable el script
chmod +x install_dependencies.sh

# Ejecutar script de instalación
./install_dependencies.sh
```

## 🔧 Instalación (Opción 2: Manual)

### Paso 1: Verificar entorno
```bash
# Verificar Python y entorno virtual
python verify_env.py
```

**Requisitos:**
- ✅ Python 3.8+
- ✅ Entorno virtual activo (recomendado)
- ✅ Archivo `requirements.txt` presente

### Paso 2: Instalar dependencias
```bash
# Instalar todas las dependencias
pip install -r requirements.txt
```

**Dependencias críticas que se instalarán:**
- `fastapi==0.116.2` - Framework web
- `groq==0.26.0` - SDK para procesamiento LLM
- `supabase==2.15.2` - Cliente para base de datos
- `pydantic==2.11.5` - Validación de datos (★ sincronizada)
- `tenacity==9.1.2` - Lógica de reintentos (★ sincronizada)
- `loguru==0.7.3` - Sistema de logging (★ sincronizada)

### Paso 3: Verificar instalación
```bash
# Generar archivo de auditoría
pip freeze > installed_versions.txt

# Verificar imports críticos
python -c "
critical_libs = ['fastapi', 'groq', 'supabase', 'pydantic', 'loguru', 'tenacity', 'httpx']
for lib in critical_libs:
    try:
        __import__(lib)
        print(f'✅ {lib}')
    except ImportError:
        print(f'❌ {lib}')
"
```

### Paso 4: Instalar modelos spaCy (opcional)
```bash
# Solo si USE_SPACY_FILTER=true en .env
python -m spacy download es_core_news_lg
python -m spacy download en_core_web_sm
```

### Paso 5: Verificación final
```bash
# Ejecutar script de verificación completa
python scripts/setup_env.py
```

## ✅ Criterios de Aceptación

Verificar que se cumplen todos estos criterios:

- [ ] **Instalación exitosa:** `pip install -r requirements.txt` sin errores
- [ ] **Versiones correctas:** Todas las librerías instaladas con versiones exactas de `requirements.txt`
- [ ] **No conflictos:** Sin advertencias de conflictos de versiones de pip
- [ ] **Imports exitosos:** Todas las librerías críticas se pueden importar
- [ ] **Auditoría generada:** Archivo `installed_versions.txt` creado
- [ ] **Scripts funcionales:** `scripts/setup_env.py` pasa todas las verificaciones
- [ ] **spaCy configurado:** Modelos instalados si `USE_SPACY_FILTER=true`

## 🔍 Troubleshooting

### Error: Conflictos de versiones
```bash
# Si pip reporta conflictos, verificar requirements.txt
pip check

# Reinstalar desde cero si es necesario
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

### Error: NumPy incompatible
```bash
# Asegurar que NumPy <2.0.0 por compatibilidad con spaCy
pip install "numpy>=1.21.0,<2.0.0"
pip install -r requirements.txt
```

### Error: Importación fallida
```bash
# Verificar entorno virtual activo
python -c "import sys; print('Virtual env:', hasattr(sys, 'real_prefix') or sys.base_prefix != sys.prefix)"

# Reinstalar librería específica
pip install --force-reinstall [libreria_con_problema]
```

## 📋 Archivos Generados

Después de la instalación exitosa, estos archivos estarán disponibles:

- `installed_versions.txt` - Auditoría completa de versiones instaladas
- `version_analysis.md` - Análisis de compatibilidad realizado
- `verify_env.py` - Script de verificación de entorno
- `install_dependencies.sh/.bat` - Scripts de instalación automatizada

## 🎯 Próximos Pasos

Una vez completada la instalación:

1. **Configurar variables de entorno:**
   ```bash
   # Editar .env con claves reales
   cp .env.example .env
   # Configurar: GROQ_API_KEY, SUPABASE_URL, SUPABASE_KEY
   ```

2. **Verificar conectividad:**
   ```bash
   python scripts/test_connections.py
   ```

3. **Proceder con Tarea 3:**
   - Crear configuración centralizada (`src/utils/config.py`)
   - Seguir con implementación de modelos Pydantic

## ⚠️ Notas Críticas

- **🔴 CRÍTICO:** No cambiar versiones manualmente después de instalación
- **🟡 IMPORTANTE:** Mantener `numpy<2.0.0` para compatibilidad con spaCy
- **🔵 INFO:** Versiones están sincronizadas con `module_connector` para máxima compatibilidad
- **🟢 SEGURO:** Todas las versiones han sido verificadas para Python 3.8+

---

**Documentación generada automáticamente durante Subtarea 2.3**  
**Para soporte:** Revisar `version_analysis.md` y logs de instalación
