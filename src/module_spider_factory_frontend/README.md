# Spider Factory 2.0 - Frontend

Sistema inteligente de generación de spiders para scraping de noticias.

## 🚀 Características

- **Wizard de Generación**: Interfaz paso a paso para crear spiders individuales
- **Carga Masiva**: Procesa múltiples sitios desde archivos CSV
- **Gestión de Patrones**: Administra y optimiza patrones de extracción
- **Actualizaciones en Tiempo Real**: WebSocket para progreso en vivo
- **Interfaz Moderna**: Material-UI con diseño responsive

## 📋 Requisitos Previos

- Node.js 18+
- npm o yarn
- Backend de Spider Factory 2.0 ejecutándose

## 🔧 Instalación

```bash
# Clonar el repositorio (si no lo has hecho)
git clone [url-del-repo]

# Navegar al directorio del frontend
cd src/module_spider_factory_frontend

# Instalar dependencias
npm install
```

## ⚙️ Configuración

Crear archivo `.env.local` en la raíz del proyecto:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## 🏃‍♂️ Ejecución

### Desarrollo

```bash
npm run dev
```

La aplicación estará disponible en `http://localhost:3000`

### Producción

```bash
# Construir para producción
npm run build

# Previsualizar build de producción
npm run preview
```

## 🧪 Testing

```bash
# Ejecutar tests
npm run test

# Tests con UI
npm run test:ui

# Coverage
npm run test:coverage
```

## 📁 Estructura del Proyecto

```
src/
├── components/          # Componentes React (Atomic Design)
│   ├── atoms/          # Componentes básicos
│   ├── molecules/      # Componentes compuestos
│   ├── organisms/      # Componentes complejos
│   └── templates/      # Layouts
├── pages/              # Páginas de la aplicación
├── hooks/              # Custom React hooks
├── services/           # Servicios API
├── theme/              # Configuración de Material-UI
└── utils/              # Utilidades

```

## 🎨 Componentes Principales

### Páginas

- **HomePage**: Dashboard principal con estadísticas
- **WizardPage**: Generación guiada de spiders
- **BulkUploadPage**: Procesamiento masivo vía CSV
- **PatternsPage**: Gestión de patrones de extracción

### Hooks Personalizados

- `useSpiderGeneration`: Lógica del wizard de generación
- `useBatchProcessing`: Manejo de procesamiento masivo
- `useWebSocket`: Conexión WebSocket para actualizaciones

### Servicios

- `api.ts`: Cliente Axios con interceptores
- `spiderFactory.service.ts`: Comunicación con el backend

## 🔌 API Endpoints

El frontend consume los siguientes endpoints del backend:

- `POST /analyze`: Análisis de sitios web
- `POST /generate`: Generación de spiders
- `POST /batch/analyze`: Análisis masivo
- `POST /batch/generate`: Generación masiva
- `GET /patterns/search`: Búsqueda de patrones
- `WS /ws/{session_id}`: WebSocket para actualizaciones

## 🚀 Deployment

### Docker

```dockerfile
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### Variables de Entorno

Para producción, configurar:

- `VITE_API_URL`: URL del backend API
- `VITE_WS_URL`: URL del WebSocket

## 🤝 Contribución

1. Fork el proyecto
2. Crear feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📝 Licencia

Este proyecto es parte de La Máquina de Noticias.