# Estructura de Module Spider Factory Frontend

## 📁 Organización de Directorios

```
module_spider_factory_frontend/
├── 📄 Configuration Files/
│   ├── Dockerfile              # Imagen Docker del frontend
│   ├── nginx.conf             # Configuración Nginx para producción
│   ├── vite.config.ts         # Configuración de Vite
│   ├── tsconfig.json          # Configuración TypeScript principal
│   ├── tsconfig.node.json     # Configuración TypeScript para Node
│   └── .eslintrc.json         # Reglas de linting
│
├── 🌐 Application Root/
│   ├── index.html             # Punto de entrada HTML
│   ├── package.json           # Dependencias y scripts
│   └── README.md              # Documentación del módulo
│
├── 📂 public/
│   └── spider-icon.svg        # Icono de la aplicación
│
└── 📂 src/
    ├── 🎯 Entry Points/
    │   ├── main.tsx           # Punto de entrada React
    │   └── App.tsx            # Componente raíz
    │
    ├── 🧩 Components/
    │   ├── atoms/             # Componentes básicos reutilizables
    │   │   ├── CodeBlock.tsx
    │   │   ├── ConfirmDialog.tsx
    │   │   ├── EmptyState.tsx
    │   │   ├── ErrorMessage.tsx
    │   │   ├── FileUploadButton.tsx
    │   │   ├── LoadingSpinner.tsx
    │   │   ├── ProgressBar.tsx
    │   │   ├── StatusChip.tsx
    │   │   └── __tests__/
    │   │
    │   ├── molecules/         # ⚠️ VACÍO - Considerar eliminar
    │   │
    │   ├── organisms/         # Componentes complejos
    │   │   ├── BatchUploader/
    │   │   └── WizardSteps/
    │   │
    │   └── templates/
    │       └── MainLayout.tsx # Layout principal
    │
    ├── 📄 Pages/
    │   ├── HomePage.tsx       # Página principal
    │   ├── WizardPage.tsx     # Wizard de generación
    │   ├── BulkUploadPage.tsx # Carga masiva
    │   └── PatternsPage.tsx   # Gestión de patrones
    │
    ├── 🔧 Logic & Services/
    │   ├── hooks/             # Custom React hooks
    │   │   ├── useBatchProcessing.ts
    │   │   ├── useSpiderGeneration.ts
    │   │   └── useWebSocket.ts
    │   │
    │   └── services/          # Servicios API
    │       ├── api.ts         # Cliente Axios
    │       └── spiderFactory.service.ts
    │
    ├── 🎨 Styling/
    │   └── theme/
    │       └── index.ts       # Tema Material-UI
    │
    ├── 🧪 Testing/
    │   └── test/
    │       └── setup.ts       # Configuración de tests
    │
    └── 📂 Empty Directories/
        ├── assets/            # ⚠️ VACÍO - Para recursos estáticos
        ├── types/             # ⚠️ VACÍO - Para TypeScript types
        └── utils/             # ⚠️ VACÍO - Para utilidades
```

## 🏗️ Componentes Principales

### Atomic Design Implementation
- **Atoms** (8): Componentes básicos sin lógica de negocio
- **Molecules** (0): Carpeta vacía - NO SE USA
- **Organisms** (2): Componentes complejos con lógica
- **Templates** (1): Layout principal
- **Pages** (4): Páginas completas de la aplicación

### Páginas y Funcionalidades
1. **HomePage**: Dashboard principal con opciones
2. **WizardPage**: Generación paso a paso de spiders
3. **BulkUploadPage**: Procesamiento masivo vía CSV
4. **PatternsPage**: Visualización y gestión de patrones

### Hooks Personalizados
- **useSpiderGeneration**: Lógica del wizard de generación
- **useBatchProcessing**: Manejo de procesamiento masivo
- **useWebSocket**: Conexión WebSocket para tiempo real

## 🔄 Flujo de Datos

```
Pages → Hooks → Services → API Backend
  ↓        ↓         ↓          ↓
Components ← State ← Response ← WebSocket
```

## 📦 Tecnologías Utilizadas

- **React 18** con TypeScript
- **Vite** como build tool
- **Material-UI v5** para componentes UI
- **Axios** para peticiones HTTP
- **React Router v6** para navegación
- **Vitest** para testing

## ⚠️ Problemas Identificados

1. **Carpetas Vacías**:
   - `/src/assets/`
   - `/src/components/molecules/`
   - `/src/types/`
   - `/src/utils/`

2. **Console.log**: 19 instancias en el código

3. **Tests Limitados**: Solo 2 componentes con tests

4. **Sin archivo de lock**: Falta package-lock.json

## 🚀 Recomendaciones

1. **Eliminar carpetas vacías** o agregar contenido
2. **Remover console.log** en producción
3. **Agregar más tests** para mayor cobertura
4. **Generar package-lock.json** para consistencia
5. **Considerar simplificar** estructura si molecules no se usa

## 📝 Notas de Mantenimiento

- El proyecto usa Vite para desarrollo rápido con HMR
- Docker multi-stage build para optimización
- Nginx configurado para SPA con React Router
- WebSocket proxy configurado en `/ws`
- API proxy configurado en `/api`