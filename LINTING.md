# 🔧 Guía de Linting y Formateo de Código

Este proyecto implementa un sistema completo de linting y formateo de código para mantener la calidad y consistencia del código.

## 🎯 Herramientas Configuradas

### Para Python 🐍
- **Black**: Formateo automático de código
- **isort**: Organización automática de imports
- **Ruff**: Linting moderno y rápido (alternativa a flake8)
- **MyPy**: Type checking estático (opcional)

### Para TypeScript/React 📜
- **Prettier**: Formateo automático de código
- **ESLint**: Linting y detección de problemas

## 🚀 Uso Rápido

### Verificar todo el código
```bash
./run-linting.sh --check
```

### Corregir automáticamente
```bash
./run-linting.sh --fix
```

### Solo Python
```bash
./run-linting.sh --check --python
./run-linting.sh --fix --python
```

### Solo TypeScript
```bash
./run-linting.sh --check --typescript
./run-linting.sh --fix --typescript
```

## 📁 Configuración por Módulo

### Frontends TypeScript

Cada frontend tiene sus propios scripts npm:

```bash
# Dashboard Frontend
cd src/module_dashboard_review_frontend
npm run validate          # Prettier + ESLint + TypeScript + Tests
npm run format            # Aplicar Prettier
npm run format:check      # Verificar Prettier
npm run lint              # Ejecutar ESLint
npm run lint:fix          # Corregir con ESLint

# Spider Factory Frontend
cd src/module_spider_factory_frontend
npm run validate          # Todo junto
npm run format            # Aplicar Prettier
npm run lint:fix          # Corregir con ESLint
```

### Backends Python

La configuración está en `pyproject.toml` en la raíz:

```bash
# Formateo
black src/module_pipeline
black src/spider_factory

# Organización de imports
isort src/module_pipeline
isort src/spider_factory

# Linting
ruff check src/module_pipeline
ruff check --fix src/module_pipeline

# Type checking (opcional)
mypy src/module_pipeline
```

## ⚙️ Configuración

### Python (`pyproject.toml`)
```toml
[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311']

[tool.isort]
profile = "black"
line-length = 88

[tool.ruff]
line-length = 88
target-version = "py39"
```

### TypeScript (`.prettierrc`)
```json
{
  "semi": true,
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2
}
```

### ESLint (`eslint.config.js`)
- Configuración moderna con flat config
- TypeScript + React + Hooks
- Reglas personalizadas para el proyecto

## 🔄 Integración en CI/CD

El linting se ejecuta automáticamente en GitHub Actions:

1. **Code Quality** (primer paso)
   - Instala todas las herramientas
   - Ejecuta linting completo
   - Falla si hay errores de formato

2. **Tests** (después del linting)
   - Solo se ejecutan si el linting pasa
   - Garantiza código limpio antes de tests

## 📋 Estándares de Código

### Python
- **Línea máxima**: 88 caracteres (Black default)
- **Imports**: Organizados por categorías (stdlib, third-party, first-party)
- **Quotes**: Dobles preferidas por Black
- **Type hints**: Recomendados pero no obligatorios

### TypeScript/React
- **Línea máxima**: 80 caracteres
- **Quotes**: Single quotes para strings, JSX
- **Semicolons**: Obligatorios
- **Trailing commas**: En ES5+ (arrays, objects)
- **Arrow functions**: Parentheses solo cuando necesarios

## 🛠️ Instalación de Herramientas

### Python
```bash
pip install black isort ruff mypy
# O usar el requirements.txt del proyecto
pip install -r requirements.txt
```

### TypeScript
```bash
# Se instalan automáticamente con npm install en cada frontend
cd src/module_dashboard_review_frontend && npm install
cd src/module_spider_factory_frontend && npm install
```

## 🐛 Resolución de Problemas

### Error: "black no encontrado"
```bash
pip install black
# O
pip install -r requirements.txt
```

### Error: "ESLint no encontrado"
```bash
cd src/module_*_frontend
npm install
```

### Conflictos entre Black e isort
La configuración está sincronizada:
```toml
[tool.isort]
profile = "black"  # Compatibilidad automática
```

### Archivos ignorados
Los archivos se ignoran automáticamente:
- `node_modules/`
- `__pycache__/`
- `build/`, `dist/`
- `.venv/`, `venv/`
- Archivos de configuración (`*.config.js`)

## 📊 Reportes en CI

GitHub Actions genera reportes automáticos:
- ✅ **APROBADA**: Todo el código cumple estándares
- ❌ **FALLÓ**: Hay problemas que corregir

### Si falla el CI:
1. Ejecutar localmente: `./run-linting.sh --fix`
2. Revisar cambios: `git diff`
3. Commit y push: `git add . && git commit -m "fix: apply linting"`

## 🎯 Mejores Prácticas

### Desarrollo Local
1. **Antes de commit**: `./run-linting.sh --fix`
2. **Verificar cambios**: `git diff`
3. **Commit limpio**: Solo cambios de funcionalidad + formato

### Configuración IDE
**VS Code** (`settings.json`):
```json
{
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  }
}
```

**PyCharm**:
- External Tools → Black, isort
- Code Style → Python → Black compatible
- ESLint plugin habilitado

## 📈 Beneficios

- ✅ **Consistencia**: Código uniforme en todo el proyecto
- ✅ **Calidad**: Detección temprana de problemas
- ✅ **Productividad**: Menos tiempo en code reviews
- ✅ **Automatización**: CI/CD garantiza estándares
- ✅ **Onboarding**: Nuevos desarrolladores siguen estándares automáticamente

---

**💡 Tip**: Ejecuta `./run-linting.sh --help` para ver todas las opciones disponibles.