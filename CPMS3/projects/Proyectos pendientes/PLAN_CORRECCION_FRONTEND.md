# PLAN DETALLADO DE CORRECCIÓN - FRONTEND SPIDER FACTORY 2.0

## 📋 RESUMEN EJECUTIVO

Este plan detalla todas las correcciones y mejoras necesarias para alinear el frontend de Spider Factory con el plan original documentado en SPIDER_FACTORY_2.0_PLAN_DETALLADO.md. Aunque el frontend tiene una base funcional, le faltan características críticas para la experiencia de usuario completa.

**Fecha de creación**: 2025-01-27  
**Tiempo estimado**: 8-10 días  
**Prioridad**: ALTA  

---

## 🎯 OBJETIVOS PRINCIPALES

1. Completar el wizard con todos los campos requeridos
2. Implementar validación en tiempo real
3. Mejorar visualización de datos con DataGrid
4. Agregar características UX faltantes
5. Aumentar cobertura de tests
6. Optimizar la experiencia del usuario

---

## 1. CORRECCIONES CRÍTICAS DEL WIZARD

### 📄 **WizardPage.tsx y SiteInfoStep.tsx**

#### 1.1 Actualizar campos del formulario según plan original
**Campos faltantes en Step 1 - Información básica:**
- `medio` (actualmente usa "name") - RENOMBRAR
- `area_geografica` - Dropdown con opciones: ESPAÑA, ARGENTINA, MÉXICO, etc.
- `tipo_medio` - Dropdown: "diario", "revista", "agencia"
- `frecuencia_minutos` - Dropdown con opciones: 15, 30, 60, 120, 1440
- `comentarios` - Campo de texto opcional multilinea

**Implementación necesaria:**
```typescript
// Definir opciones
const AREAS_GEOGRAFICAS = [
  'ESPAÑA', 'ARGENTINA', 'MÉXICO', 'COLOMBIA', 'CHILE', 
  'PERÚ', 'VENEZUELA', 'ECUADOR', 'BOLIVIA', 'PARAGUAY',
  'URUGUAY', 'COSTA RICA', 'PANAMÁ', 'GUATEMALA', 'HONDURAS',
  'EL SALVADOR', 'NICARAGUA', 'REPÚBLICA DOMINICANA', 'PUERTO RICO',
  'CUBA', 'ESTADOS UNIDOS', 'BRASIL', 'PORTUGAL', 'INTERNACIONAL'
];

const TIPOS_MEDIO = [
  { value: 'diario', label: 'Diario' },
  { value: 'revista', label: 'Revista' },
  { value: 'agencia', label: 'Agencia de noticias' }
];

const FRECUENCIAS = [
  { value: 15, label: 'Cada 15 minutos' },
  { value: 30, label: 'Cada 30 minutos' },
  { value: 60, label: 'Cada hora' },
  { value: 120, label: 'Cada 2 horas' },
  { value: 240, label: 'Cada 4 horas' },
  { value: 720, label: 'Cada 12 horas' },
  { value: 1440, label: 'Una vez al día' }
];
```

#### 1.2 Agregar Step 2 - URLs y sección (FALTANTE)
**Crear nuevo componente `SectionUrlStep.tsx`:**
- Campo `seccion` - Nombre de la sección a monitorear
- Campo `url` - URL de la sección (ya existe pero moverlo aquí)
- Checkbox `tiene_rss` - ¿El sitio tiene RSS?
- Campo `rss_url` - URL del RSS (condicional si tiene_rss = true)

#### 1.3 Implementar validación con react-hook-form
**En todos los steps del wizard:**
```typescript
import { useForm, Controller } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';

// Schema de validación
const schema = yup.object({
  medio: yup.string().required('El nombre del medio es obligatorio'),
  seccion: yup.string().required('La sección es obligatoria'),
  area_geografica: yup.string().required('El área geográfica es obligatoria'),
  tipo_medio: yup.string().oneOf(['diario', 'revista', 'agencia']).required(),
  url: yup.string().url('URL inválida').required('La URL es obligatoria'),
  frecuencia_minutos: yup.number().positive().integer(),
  rss_url: yup.string().url('URL inválida').when('tiene_rss', {
    is: true,
    then: yup.string().required('La URL del RSS es obligatoria')
  })
});
```

---

## 2. MEJORAS EN VISUALIZACIÓN DE DATOS

### 📄 **BatchProcessingStatus.tsx**

#### 2.1 Implementar DataGrid de Material-UI
**Reemplazar List con DataGrid:**
```typescript
import { DataGrid, GridColDef } from '@mui/x-data-grid';

const columns: GridColDef[] = [
  { field: 'medio', headerName: 'Medio', width: 150 },
  { field: 'seccion', headerName: 'Sección', width: 120 },
  { field: 'url', headerName: 'URL', width: 250 },
  { field: 'area_geografica', headerName: 'Área', width: 100 },
  { field: 'tipo_medio', headerName: 'Tipo', width: 100 },
  { 
    field: 'status', 
    headerName: 'Estado', 
    width: 120,
    renderCell: (params) => <StatusChip status={params.value} />
  },
  {
    field: 'progress',
    headerName: 'Progreso',
    width: 150,
    renderCell: (params) => <LinearProgress variant="determinate" value={params.value} />
  }
];
```

#### 2.2 Agregar funcionalidades de tabla
- Ordenamiento por columnas
- Filtros por estado
- Paginación (10, 25, 50 items)
- Selección múltiple para acciones batch
- Exportar resultados a CSV

### 📄 **BatchUploader.tsx**

#### 2.3 Actualizar template CSV
**Cambiar el template según plan:**
```typescript
const TEMPLATE_CSV = `medio,seccion,url,area_geografica,tipo_medio,frecuencia_minutos,rss_url
El País,Internacional,https://elpais.com/internacional,ESPAÑA,diario,60,
La Nación,Economía,https://lanacion.com.ar/economia,ARGENTINA,diario,30,https://...
El Universal,Política,https://eluniversal.com.mx/politica,MÉXICO,diario,60,`;
```

#### 2.4 Agregar validación de CSV
- Validar columnas obligatorias
- Validar valores de tipo_medio
- Validar URLs
- Mostrar errores por fila

---

## 3. PREVIEW Y VISUALIZACIÓN DE ANÁLISIS

### 📄 **AnalysisStep.tsx**

#### 3.1 Implementar preview en tiempo real
**Mostrar artículos detectados durante el análisis:**
```typescript
// Componente de preview de artículos
const ArticlePreview = ({ articles }) => (
  <Box>
    <Typography variant="h6">Artículos detectados:</Typography>
    {articles.map((article, index) => (
      <Card key={index} sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="subtitle1">{article.title}</Typography>
          <Typography variant="body2" color="text.secondary">
            {article.date} - {article.excerpt}
          </Typography>
        </CardContent>
      </Card>
    ))}
  </Box>
);
```

#### 3.2 Agregar indicadores de progreso detallados
- Paso actual del análisis (Detectando RSS, Analizando estructura, etc.)
- Tiempo transcurrido
- Estimación de tiempo restante

### 📄 **CodeBlock.tsx**

#### 3.3 Implementar syntax highlighting
**Usar Prism.js o react-syntax-highlighter:**
```typescript
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

const CodeBlock = ({ code, language = 'python' }) => (
  <SyntaxHighlighter 
    language={language} 
    style={vscDarkPlus}
    showLineNumbers
    customStyle={{ borderRadius: 8 }}
  >
    {code}
  </SyntaxHighlighter>
);
```

---

## 4. SISTEMA DE NOTIFICACIONES

### 📄 **Crear NotificationProvider.tsx**

#### 4.1 Implementar Context para notificaciones
```typescript
import { createContext, useContext, useState } from 'react';
import { Snackbar, Alert } from '@mui/material';

interface Notification {
  id: string;
  message: string;
  severity: 'success' | 'error' | 'warning' | 'info';
}

const NotificationContext = createContext({});

export const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  
  const showNotification = (message: string, severity: 'success' | 'error' | 'warning' | 'info') => {
    // Lógica de notificación
  };
  
  return (
    <NotificationContext.Provider value={{ showNotification }}>
      {children}
      {/* Snackbars */}
    </NotificationContext.Provider>
  );
};
```

#### 4.2 Hook useNotification
```typescript
export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within NotificationProvider');
  }
  return context;
};
```

---

## 5. GESTIÓN DE ESTADO SIMPLE

### 📄 **Gestión sin librerías adicionales**

#### 5.1 Estado local para el wizard
```typescript
// En WizardPage.tsx - Estado local simple
const [wizardData, setWizardData] = useState<WizardData>({
  medio: '',
  seccion: '',
  url: '',
  area_geografica: '',
  tipo_medio: 'diario',
  frecuencia_minutos: 60,
  rss_url: '',
  comentarios: ''
});

// Actualizar datos
const updateWizardData = (updates: Partial<WizardData>) => {
  setWizardData(prev => ({ ...prev, ...updates }));
};
```

#### 5.2 Hook personalizado para localStorage
```typescript
// hooks/useLocalStorage.ts
function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error(`Error loading ${key}:`, error);
      return initialValue;
    }
  });

  const setValue = (value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.error(`Error saving ${key}:`, error);
    }
  };

  return [storedValue, setValue] as const;
}

// Uso en componentes
const [wizardDraft, setWizardDraft] = useLocalStorage('wizard-draft', {});
const [userPreferences, setUserPreferences] = useLocalStorage('preferences', {
  theme: 'light',
  lastAreaGeografica: '',
  lastTipoMedio: 'diario'
});
```

#### 5.3 React Query para datos del servidor
```typescript
// Historial de spiders generados
const { data: generatedSpiders } = useQuery({
  queryKey: ['generated-spiders'],
  queryFn: () => spiderFactoryService.getHistory(),
  staleTime: 5 * 60 * 1000, // Cache por 5 minutos
  cacheTime: 10 * 60 * 1000 // Mantener en cache 10 minutos
});

// Guardar localmente como backup
const saveSpiderLocally = (spider: GeneratedSpider) => {
  const history = JSON.parse(localStorage.getItem('spider-history') || '[]');
  history.unshift({
    ...spider,
    generatedAt: new Date().toISOString()
  });
  // Mantener solo los últimos 50
  localStorage.setItem('spider-history', JSON.stringify(history.slice(0, 50)));
};
```

---

## 6. NUEVAS PÁGINAS Y CARACTERÍSTICAS

### 📄 **Crear HistoryPage.tsx**

#### 6.1 Página de historial de spiders generados
```typescript
const HistoryPage = () => {
  // Obtener historial del backend con React Query
  const { data: spiderHistory, isLoading, error } = useQuery({
    queryKey: ['spider-history'],
    queryFn: async () => {
      try {
        // Primero intentar obtener del backend
        return await spiderFactoryService.getHistory();
      } catch (error) {
        // Si falla, usar historial local como fallback
        const localHistory = localStorage.getItem('spider-history');
        return localHistory ? JSON.parse(localHistory) : [];
      }
    },
    staleTime: 5 * 60 * 1000 // 5 minutos
  });

  const downloadSpider = (spider: GeneratedSpider) => {
    const blob = new Blob([spider.code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${spider.name}.py`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const viewCode = (spider: GeneratedSpider) => {
    // Navegar a vista de código o abrir modal
    navigate(`/spider-factory/code/${spider.id}`);
  };

  if (isLoading) return <CircularProgress />;
  if (error) return <Alert severity="error">Error cargando historial</Alert>;
  
  return (
    <Container>
      <Typography variant="h4" gutterBottom>
        Historial de Spiders Generados
      </Typography>
      
      <DataGrid
        rows={spiderHistory || []}
        columns={[
          { field: 'name', headerName: 'Nombre', width: 200 },
          { 
            field: 'generatedAt', 
            headerName: 'Fecha', 
            width: 150,
            valueFormatter: (params) => 
              new Date(params.value).toLocaleDateString()
          },
          { field: 'medio', headerName: 'Medio', width: 150 },
          { field: 'seccion', headerName: 'Sección', width: 120 },
          { 
            field: 'actions', 
            headerName: 'Acciones', 
            width: 150,
            renderCell: (params) => (
              <>
                <IconButton 
                  onClick={() => downloadSpider(params.row)}
                  title="Descargar spider"
                >
                  <DownloadIcon />
                </IconButton>
                <IconButton 
                  onClick={() => viewCode(params.row)}
                  title="Ver código"
                >
                  <CodeIcon />
                </IconButton>
              </>
            )
          }
        ]}
        pageSize={10}
        rowsPerPageOptions={[10, 25, 50]}
        autoHeight
        disableSelectionOnClick
      />
    </Container>
  );
};
```

### 📄 **Actualizar MainLayout.tsx**

#### 6.2 Agregar toggle de tema con Context API
```typescript
// contexts/ThemeContext.tsx
interface ThemeContextType {
  mode: 'light' | 'dark';
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [mode, setMode] = useState<'light' | 'dark'>(() => {
    // Cargar tema guardado o usar el preferido del sistema
    const saved = localStorage.getItem('theme');
    if (saved === 'light' || saved === 'dark') return saved;
    
    return window.matchMedia('(prefers-color-scheme: dark)').matches 
      ? 'dark' 
      : 'light';
  });

  const toggleTheme = () => {
    const newMode = mode === 'light' ? 'dark' : 'light';
    setMode(newMode);
    localStorage.setItem('theme', newMode);
  };

  const theme = createTheme({
    palette: { mode }
  });

  return (
    <ThemeContext.Provider value={{ mode, toggleTheme }}>
      <MuiThemeProvider theme={theme}>
        {children}
      </MuiThemeProvider>
    </ThemeContext.Provider>
  );
};

// Hook personalizado
export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
};

// Componente ThemeToggle
const ThemeToggle = () => {
  const { mode, toggleTheme } = useTheme();
  
  return (
    <IconButton onClick={toggleTheme} color="inherit">
      {mode === 'light' ? <DarkModeIcon /> : <LightModeIcon />}
    </IconButton>
  );
};
```

#### 6.3 Agregar navegación a historial
- Agregar item en el menú para "Historial"
- Link a la nueva página de historial

---

## 7. VALIDACIONES Y MEJORAS UX

### 📄 **Validaciones en tiempo real**

#### 7.1 Validar duplicados mientras escribe
```typescript
// En SiteInfoStep
const checkDuplicate = async (medio: string, seccion: string) => {
  if (medio && seccion) {
    const response = await spiderFactoryService.checkDuplicate({ medio, seccion });
    if (response.exists) {
      setError('seccion', { 
        message: `Ya existe un spider para ${medio} - ${seccion}` 
      });
    }
  }
};

// Debounce la validación
const debouncedCheck = useMemo(
  () => debounce(checkDuplicate, 500),
  []
);
```

#### 7.2 Indicadores visuales según plan
- Verde para éxito
- Amarillo para advertencias
- Rojo para errores
- Azul para información

### 📄 **Mejoras de accesibilidad**

#### 7.3 Implementar navegación por teclado
- Tab entre campos
- Enter para siguiente paso
- Escape para cancelar
- Atajos de teclado documentados

---

## 8. TESTING COMPLETO

### 📄 **Tests unitarios faltantes**

#### 8.1 Tests para hooks
```typescript
// useWebSocket.test.ts
// useBatchProcessing.test.ts
// useAnalysisProgress.test.ts
```

#### 8.2 Tests para servicios
```typescript
// spiderFactoryService.test.ts
// Tests con MSW (Mock Service Worker)
```

#### 8.3 Tests para páginas
```typescript
// WizardPage.test.tsx
// BulkUploadPage.test.tsx
// HomePage.test.tsx
```

#### 8.4 Tests de integración
```typescript
// Flujo completo del wizard
// Procesamiento batch
// WebSocket updates
```

---

## 9. OPTIMIZACIONES Y PERFORMANCE

### 9.1 Code splitting por rutas
```typescript
const WizardPage = lazy(() => import('./pages/WizardPage'));
const BulkUploadPage = lazy(() => import('./pages/BulkUploadPage'));
const HistoryPage = lazy(() => import('./pages/HistoryPage'));
```

### 9.2 Memoización de componentes pesados
```typescript
const MemoizedDataGrid = memo(DataGrid);
const MemoizedCodeBlock = memo(CodeBlock);
```

### 9.3 Optimización de re-renders
- Usar React.memo donde sea apropiado
- Implementar useMemo y useCallback
- Evitar props inline en componentes

---

## 10. DOCUMENTACIÓN Y TIPOS

### 10.1 Completar tipos TypeScript
```typescript
// types/index.ts actualizado
export interface SpiderConfig {
  medio: string;
  seccion: string;
  url: string;
  area_geografica: string;
  tipo_medio: 'diario' | 'revista' | 'agencia';
  frecuencia_minutos: number;
  rss_url?: string;
  comentarios?: string;
}

export interface AnalysisResult {
  strategy: 'rss' | 'scraping' | 'playwright';
  confidence: number;
  selectors?: Record<string, string>;
  sample_articles?: Article[];
  needs_javascript: boolean;
}
```

### 10.2 JSDoc para componentes complejos
```typescript
/**
 * Wizard para generación de spiders
 * @component
 * @example
 * <WizardPage onComplete={(data) => console.log(data)} />
 */
```

---

## 📅 CRONOGRAMA DE IMPLEMENTACIÓN

### Fase 1: Correcciones del Wizard
- [ ] Actualizar campos en SiteInfoStep
- [ ] Crear SectionUrlStep
- [ ] Implementar validación con react-hook-form
- [ ] Agregar dropdowns para área geográfica y tipo de medio

### Fase 2: Visualización de Datos
- [ ] Implementar DataGrid en BatchProcessingStatus
- [ ] Actualizar template CSV
- [ ] Agregar preview de artículos en AnalysisStep
- [ ] Implementar syntax highlighting en CodeBlock

### Fase 3: Notificaciones y UI
- [ ] Crear NotificationProvider con Context API
- [ ] Implementar persistencia simple con localStorage
- [ ] Crear toggle de tema con Context
- [ ] Hook useLocalStorage reutilizable

### Fase 4: Nuevas Páginas
- [ ] Crear HistoryPage
- [ ] Actualizar navegación
- [ ] Implementar descarga de spiders

### Fase 5: Testing y Optimización
- [ ] Escribir tests unitarios
- [ ] Tests de integración
- [ ] Optimizaciones de performance
- [ ] Documentación completa

---

## 🎯 CRITERIOS DE ÉXITO

1. ✅ Wizard con todos los campos del plan original
2. ✅ Validación en tiempo real funcionando
3. ✅ DataGrid implementado para visualización CSV
4. ✅ Preview de análisis con artículos detectados
5. ✅ Sistema de notificaciones con Snackbar
6. ✅ Persistencia local con localStorage
7. ✅ Historial de spiders con React Query
8. ✅ Tema oscuro/claro funcional
9. ✅ Cobertura de tests > 80%
10. ✅ Todos los campos del backend soportados en UI

---

## 🚨 RIESGOS Y MITIGACIONES

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Cambios rompen wizard existente | Alta | Alto | Tests exhaustivos antes de deploy |
| Conflictos con backend actualizado | Media | Alto | Coordinar cambios con backend |
| Performance con DataGrid grande | Media | Medio | Paginación y virtualización |
| Complejidad de validaciones | Baja | Medio | Usar schema de yup bien definido |

---

## 📝 NOTAS FINALES

- La implementación actual tiene una buena base pero le faltan características críticas
- El wizard necesita actualización urgente para incluir todos los campos
- La experiencia de usuario mejorará significativamente con estas correcciones
- Es importante mantener compatibilidad con el backend corregido
- Aprovechar las librerías ya instaladas (DataGrid, react-hook-form)

---

## 15. INDICADORES DE TIEMPO Y KPIs

### 15.1 Dashboard de KPIs
**Crear componente `KPIDashboard.tsx`:**
```typescript
interface KPIMetrics {
  tiempoReduccion: number;  // Target: 97%
  tiempoPromedioRSS: number;  // Target: <5s
  tiempoPromedioPrimeraVez: number;  // Target: ~20s
  tiempoPromedioCache: number;  // Target: <2s
  precisionSpiders: number;  // Target: >90%
  reduccionRequests: number;  // Target: 70%
  cacheHitRate: number;
  spidersPorDia: number;  // Target: 200+
  porcentajeAdopcion: number;  // Target: >80%
}

const KPIDashboard = () => {
  const { data: metrics } = useQuery(['kpi-metrics'], fetchKPIMetrics);
  
  return (
    <Grid container spacing={2}>
      <Grid item xs={12} md={3}>
        <MetricCard
          title="Reducción de Tiempo"
          value={`${metrics?.tiempoReduccion || 0}%`}
          target="97%"
          icon={<SpeedIcon />}
          color={metrics?.tiempoReduccion >= 97 ? 'success' : 'warning'}
        />
      </Grid>
      {/* Más métricas... */}
    </Grid>
  );
};
```

### 15.2 Indicadores de tiempo en generación
**Agregar a `WizardPage.tsx` y `AnalysisStep.tsx`:**
```typescript
// Componente de tiempo estimado
const TimeEstimate = ({ strategy }: { strategy: string }) => {
  const getEstimate = () => {
    switch (strategy) {
      case 'rss': return '<5 segundos';
      case 'cache': return '<2 segundos';
      case 'first_time': return '~20 segundos';
      default: return 'Calculando...';
    }
  };
  
  return (
    <Alert severity="info" icon={<TimerIcon />}>
      Tiempo estimado: {getEstimate()}
    </Alert>
  );
};
```

---

## 16. VALIDACIÓN CONTRA LISTA DE ÁREAS

### 16.1 Actualizar constantes de áreas geográficas
**En `src/constants/areas.ts`:**
```typescript
// Lista oficial del plan original
export const AREAS_GEOGRAFICAS_OFICIALES = [
  'HISPANIDAD', 'HISPANOAMERICA', 'CENTROAMERICA', 'CARIBE_HISPANO',
    'SUDAMERICA', 'TERRITORIOS_OCUPADOS', 'DIASPORA_HISPANA_USA',
    'GLOBAL', 'PAISES_NO_HISPANOS',
    'ARGENTINA', 'BOLIVIA', 'CHILE', 'COLOMBIA', 'COSTA_RICA',
    'CUBA', 'ECUADOR', 'EL_SALVADOR', 'ESPAÑA', 'FILIPINAS',
    'GUATEMALA', 'GUINEA_ECUATORIAL', 'HONDURAS', 'MÉXICO',
    'NICARAGUA', 'PANAMÁ', 'PARAGUAY', 'PERÚ', 'PUERTO_RICO',
    'REPÚBLICA_DOMINICANA', 'SAHARA_OCCIDENTAL', 'URUGUAY', 'VENEZUELA'
] as const;

export type AreaGeografica = typeof AREAS_GEOGRAFICAS_OFICIALES[number];
```

### 16.2 Agregar validación estricta
**En esquema de validación:**
```typescript
const validationSchema = yup.object({
  area_geografica: yup
    .string()
    .oneOf(
      AREAS_GEOGRAFICAS_OFICIALES,
      'Área geográfica no válida'
    )
    .required('El área geográfica es obligatoria'),
  // ... resto del schema
});
```

---

## 17. INTEGRACIÓN CON FIRECRAWL UI

### 17.1 Mostrar formatos obtenidos
**En `AnalysisStep.tsx`:**
```typescript
const FirecrawlFormats = ({ analysis }: { analysis: AnalysisResult }) => (
  <Box sx={{ mt: 2 }}>
    <Typography variant="subtitle2">Formatos analizados:</Typography>
    <Chip label="HTML" color="primary" size="small" sx={{ mr: 1 }} />
    <Chip label="Markdown" color="primary" size="small" sx={{ mr: 1 }} />
    <Chip label="Screenshot" color="primary" size="small" />
    <Typography variant="caption" display="block" sx={{ mt: 1 }}>
      ✓ Análisis completo en 1 sola petición a Firecrawl
    </Typography>
  </Box>
);
```

### 17.2 Preview con screenshot
**Agregar visualización de screenshot si está disponible:**
```typescript
const ScreenshotPreview = ({ screenshotUrl }: { screenshotUrl?: string }) => {
  if (!screenshotUrl) return null;
  
  return (
    <Box sx={{ mt: 2 }}>
      <Typography variant="subtitle2" gutterBottom>
        Vista previa del sitio:
      </Typography>
      <img 
        src={screenshotUrl} 
        alt="Vista previa"
        style={{ 
          maxWidth: '100%', 
          height: 'auto',
          border: '1px solid #e0e0e0',
          borderRadius: 8
        }}
      />
    </Box>
  );
};
```

---

## 18. INFORMACIÓN DE SCRAPYD

### 18.1 Mostrar configuración de scheduling
**En `ReviewStep.tsx` del wizard:**
```typescript
const ScrapydInfo = ({ frecuencia }: { frecuencia: number }) => (
  <Alert severity="info" sx={{ mt: 2 }}>
    <AlertTitle>Programación automática</AlertTitle>
    Este spider se ejecutará automáticamente cada {frecuencia} minutos
    en Scrapyd una vez desplegado.
  </Alert>
);
```

### 18.2 Indicador de compatibilidad
**Agregar badge de compatibilidad:**
```typescript
const CompatibilityBadge = () => (
  <Chip 
    label="Compatible con Scrapyd" 
    color="success" 
    size="small"
    icon={<CheckCircleIcon />}
  />
);
```

---

## 19. MÉTRICAS DE RENDIMIENTO EN UI

### 19.1 Monitor de rendimiento en tiempo real
**Crear `PerformanceMonitor.tsx`:**
```typescript
const PerformanceMonitor = () => {
  const [metrics, setMetrics] = useState({
    activeConnections: 0,
    cacheHitRate: 0,
    avgResponseTime: 0,
    requestsPerMinute: 0
  });
  
  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/metrics`);
    ws.onmessage = (event) => {
      setMetrics(JSON.parse(event.data));
    };
    return () => ws.close();
  }, []);
  
  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6">Rendimiento del Sistema</Typography>
      <Grid container spacing={2}>
        <Grid item xs={6}>
          <Typography variant="body2" color="text.secondary">
            Conexiones Redis activas
          </Typography>
          <Typography variant="h4">
            {metrics.activeConnections}/50
          </Typography>
        </Grid>
        <Grid item xs={6}>
          <Typography variant="body2" color="text.secondary">
            Cache Hit Rate
          </Typography>
          <Typography variant="h4">
            {metrics.cacheHitRate.toFixed(1)}%
          </Typography>
        </Grid>
      </Grid>
    </Box>
  );
};
```

---

## 20. CACHE WARMING INDICATOR

### 20.1 Indicador de patrones populares
**Mostrar cuando se usa un patrón popular:**
```typescript
const PopularPatternBadge = ({ usageCount }: { usageCount?: number }) => {
  if (!usageCount || usageCount < 10) return null;
  
  return (
    <Tooltip title="Este es un patrón popular pre-cargado en cache">
      <Chip
        label={`Usado ${usageCount} veces`}
        color="secondary"
        size="small"
        icon={<TrendingUpIcon />}
      />
    </Tooltip>
  );
};
```

### 20.2 Lista de medios populares
**En página principal o dashboard:**
```typescript
const PopularMediaList = () => {
  const { data: popularMedia } = useQuery(['popular-media'], 
    () => spiderFactoryService.getPopularMedia()
  );
  
  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Medios más generados
      </Typography>
      <List>
        {popularMedia?.map(media => (
          <ListItem key={media.domain}>
            <ListItemText 
              primary={media.name}
              secondary={`${media.count} spiders generados`}
            />
            <Chip 
              label="Respuesta instantánea" 
              size="small" 
              color="primary"
            />
          </ListItem>
        ))}
      </List>
    </Paper>
  );
};
```

---

## 🔧 CONFIGURACIÓN ADICIONAL NECESARIA

### Variables de entorno (.env)
```
VITE_API_URL=http://localhost:8005
VITE_WS_URL=ws://localhost:8005/ws
VITE_MAX_FILE_SIZE=5242880
VITE_SUPPORTED_AREAS=ESPAÑA,ARGENTINA,MÉXICO,...
```

### Scripts package.json
```json
{
  "scripts": {
    "test:coverage": "vitest run --coverage",
    "test:watch": "vitest watch",
    "analyze": "source-map-explorer 'dist/**/*.js'",
    "lint:fix": "eslint . --fix"
  }
}
```

---

## 21. ARQUITECTURA DOCKER Y NGINX - CONSIDERACIONES CRÍTICAS

### 21.1 Preservar configuración actual
**La implementación DEBE respetar:**
- Frontend servido por NGINX interno en puerto 80 del contenedor
- Base path `/spider-factory/` en Vite
- Variables de entorno configuradas en docker-compose
- Comunicación con backend a través de NGINX reverse proxy

### 21.2 Configuración de rutas crítica
**En vite.config.ts - NO CAMBIAR:**
```typescript
export default defineConfig({
  base: '/spider-factory/',  // MANTENER este base path
  // ... resto de config
})
```

**Variables de entorno - Usar las configuradas en Docker:**
```typescript
// services/api.ts
const API_BASE_URL = import.meta.env.VITE_API_URL || '/spider-factory/api'
const WS_BASE_URL = import.meta.env.VITE_WS_URL || '/spider-factory/ws'

// NO usar URLs absolutas como http://localhost:8000
```

### 21.3 TypeScript - Configuración que funciona
**tsconfig.json - Configuración probada:**
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,  // CRÍTICO para evitar errores de libs
    
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,  // Para Vite
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,  // Vite maneja la compilación
    "jsx": "react-jsx",
    
    "strict": true,
    "noUnusedLocals": false,  // Temporalmente flexible
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true,
    
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

### 21.4 Enfoque de migración no destructiva
**Fase 1 - Extender tipos existentes:**
```typescript
// types/index.ts - Mantener compatibilidad
export interface SiteInfo {
  url: string;
  name: string;  // MANTENER por compatibilidad
  
  // Nuevos campos opcionales
  medio?: string;
  seccion?: string;
  area_geografica?: string;
  tipo_medio?: 'diario' | 'revista' | 'agencia';
  frecuencia_minutos?: number;
}

// Nuevo tipo para migración gradual
export interface SpiderConfig extends SiteInfo {
  medio: string;  // Obligatorio en nueva versión
  seccion: string;  // Obligatorio en nueva versión
}
```

**Fase 2 - Componentes retrocompatibles:**
```typescript
// SiteInfoStep.tsx
const SiteInfoStep = ({ data, onUpdate }: StepProps) => {
  // Compatibilidad: usar medio si existe, sino name
  const medio = data.medio || data.name;
  
  // Mostrar campos nuevos solo si el backend los soporta
  const [backendVersion, setBackendVersion] = useState<'v1' | 'v2'>('v1');
  
  useEffect(() => {
    // Detectar versión del backend
    checkBackendCapabilities().then(setBackendVersion);
  }, []);
  
  return (
    <>
      {/* Campo existente */}
      <TextField
        label="Nombre"
        value={data.name}
        onChange={(e) => onUpdate({ name: e.target.value })}
      />
      
      {/* Campos nuevos solo si backend v2 */}
      {backendVersion === 'v2' && (
        <>
          <TextField
            label="Medio"
            value={data.medio || ''}
            onChange={(e) => onUpdate({ medio: e.target.value })}
          />
          <TextField
            label="Sección"
            value={data.seccion || ''}
            onChange={(e) => onUpdate({ seccion: e.target.value })}
          />
        </>
      )}
    </>
  );
};
```

### 21.5 Llamadas API compatibles
**spiderFactory.service.ts - Soporte dual:**
```typescript
class SpiderFactoryService {
  async analyze(data: AnalysisRequest) {
    // Enviar campos nuevos solo si están presentes
    const payload = {
      url: data.url,
      name: data.name,
      ...(data.medio && { medio: data.medio }),
      ...(data.seccion && { seccion: data.seccion }),
      ...(data.area_geografica && { area_geografica: data.area_geografica })
    };
    
    return fetch(`${API_BASE_URL}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
  }
  
  // Nueva función para check-duplicate
  async checkDuplicate(medio: string, seccion: string) {
    try {
      const response = await fetch(`${API_BASE_URL}/check-duplicate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ medio, seccion })
      });
      
      if (response.status === 404) {
        // Backend no soporta endpoint nuevo
        return { exists: false, supported: false };
      }
      
      return await response.json();
    } catch (error) {
      // Fallback si endpoint no existe
      return { exists: false, supported: false };
    }
  }
}
```

### 21.6 Docker build - Validación continua
**Dockerfile optimizado para TypeScript:**
```dockerfile
# Build stage
FROM node:18-alpine as builder
WORKDIR /app

# Copiar package files
COPY package*.json ./
RUN npm ci --only=production

# Copiar código fuente
COPY . .

# Build con validación de tipos
RUN npm run build || (echo "Build failed - check TypeScript errors" && exit 1)

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

### 21.7 Validación durante desarrollo
**Scripts de validación:**
```bash
# 1. Verificar tipos TypeScript
cd src/module_spider_factory_frontend
npm run type-check  # Agregar script: "tsc --noEmit"

# 2. Build local antes de Docker
npm run build

# 3. Test con Docker
docker-compose build --no-cache spider_factory_frontend
docker-compose up spider_factory_frontend

# 4. Verificar rutas a través de NGINX
curl http://localhost/spider-factory/
curl http://localhost/spider-factory/assets/index.js

# 5. Verificar conexión con API
# En browser: Developer Tools > Network
# Verificar que las llamadas van a /spider-factory/api/*
```

### 21.8 Puntos críticos a NO modificar
1. **NO cambiar** el base path `/spider-factory/` en Vite
2. **NO usar** URLs absolutas del backend (http://localhost:8000)
3. **NO cambiar** la estructura de carpetas del build
4. **NO modificar** nginx.conf del frontend sin probar
5. **Mantener** compatibilidad con campos existentes
6. **NO cambiar** el puerto 80 interno del contenedor

### 21.9 Testing con arquitectura completa
```bash
# Test del flujo completo frontend → nginx → backend
# 1. Iniciar todos los servicios
docker-compose up -d nginx_reverse_proxy spider_factory_backend spider_factory_frontend redis

# 2. Verificar que frontend carga
curl -I http://localhost/spider-factory/

# 3. Test de API a través del frontend
# Abrir browser: http://localhost/spider-factory/
# Abrir Developer Tools > Network
# Realizar análisis y verificar:
# - Request URL: http://localhost/spider-factory/api/analyze
# - NO debe ser: http://localhost:8000/analyze

# 4. Verificar WebSocket
# En Developer Tools > Network > WS
# Debe conectar a: ws://localhost/spider-factory/ws/[session-id]

# 5. Logs para debugging
docker-compose logs -f spider_factory_frontend
docker-compose logs -f nginx_reverse_proxy | grep spider-factory
```

### 21.10 Manejo de errores de build TypeScript
**Problemas comunes y soluciones:**
```typescript
// Error: Cannot find module '@/components'
// Solución: Verificar paths en tsconfig.json y vite.config.ts coincidan

// Error: Type 'X' is not assignable to type 'Y'
// Solución temporal durante migración:
// @ts-ignore // TODO: Fix types after migration

// Error en Docker build pero no en local
// Solución: Limpiar cache
rm -rf node_modules package-lock.json
npm install
npm run build
```

