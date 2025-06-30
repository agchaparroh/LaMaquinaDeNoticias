/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_WS_URL: string
  readonly VITE_BASE_PATH?: string
  readonly VITE_ENV: string
  // Añadir más variables de entorno según sea necesario
  readonly VITE_APP_NAME?: string
  readonly VITE_APP_VERSION?: string
  readonly VITE_ENABLE_ANALYTICS?: string
  readonly VITE_SENTRY_DSN?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

// Declaraciones de módulos para archivos que TypeScript no reconoce por defecto
declare module '*.svg' {
  import React = require('react')
  export const ReactComponent: React.FC<React.SVGProps<SVGSVGElement>>
  const src: string
  export default src
}

declare module '*.jpg' {
  const content: string
  export default content
}

declare module '*.jpeg' {
  const content: string
  export default content
}

declare module '*.png' {
  const content: string
  export default content
}

declare module '*.gif' {
  const content: string
  export default content
}

declare module '*.webp' {
  const content: string
  export default content
}

// Declaración para archivos CSS modules
declare module '*.module.css' {
  const classes: { readonly [key: string]: string }
  export default classes
}

declare module '*.module.scss' {
  const classes: { readonly [key: string]: string }
  export default classes
}

// Declaración para archivos JSON
declare module '*.json' {
  const value: any
  export default value
}

// Declaración para Web Workers
declare module '*?worker' {
  const workerConstructor: {
    new (): Worker
  }
  export default workerConstructor
}

// Declaración para importaciones inline
declare module '*?inline' {
  const content: string
  export default content
}

declare module '*?url' {
  const content: string
  export default content
}

// Augmentación del módulo Theme de MUI
declare module '@mui/material/styles' {
  interface Theme {
    // Añadir propiedades personalizadas al tema si es necesario
  }
  
  interface ThemeOptions {
    // Añadir opciones personalizadas al tema si es necesario
  }
}

// Augmentación para paleta personalizada
declare module '@mui/material/styles/createPalette' {
  interface Palette {
    // Añadir colores personalizados si es necesario
  }
  
  interface PaletteOptions {
    // Añadir opciones de colores personalizados si es necesario
  }
}