# Testing Plan - Dashboard Review Frontend

## Objetivo

Desarrollar una suite completa de tests para el módulo Dashboard Review Frontend, asegurando la calidad y confiabilidad del sistema de revisión editorial.

## Stack de Testing

- **Framework**: Vitest 1.0+
- **Testing Library**: React Testing Library
- **Mocking**: MSW (Mock Service Worker)
- **Coverage**: Vitest Coverage (v8)
- **Assertions**: Jest DOM matchers

## Estrategia de Testing

### 1. Tests Unitarios (60% del esfuerzo)

#### Components - Atoms
- [ ] ErrorBoundary: Captura errores y muestra UI de fallback
- [ ] Button: Maneja clicks y estados disabled
- [ ] Input: Valida entrada y emite cambios
- [ ] Spinner: Renderiza animación de carga

#### Components - Molecules  
- [ ] HechoCard: Renderiza información completa del hecho
- [ ] HechoCard: Maneja click para abrir modal
- [ ] FeedbackSnackbar: Muestra notificaciones y auto-cierra
- [ ] HechoDetailModal: Muestra información expandida y maneja cierre

#### Components - Organisms
- [ ] FilterHeader: Aplica filtros correctamente
- [ ] FilterHeader: Limpia filtros con reset
- [ ] HechosList: Renderiza lista con paginación
- [ ] HechosList: Muestra skeleton en loading
- [ ] HechosList: Muestra mensaje empty state

#### Hooks
- [ ] useDashboard: Fetch inicial de datos
- [ ] useDashboard: Aplica filtros y paginación
- [ ] useFilters: Maneja cambios con debounce
- [ ] useFeedback: Envía cambios de importancia
- [ ] useFeedback: Marca hechos como falsos

#### Services
- [ ] dashboardApi: Maneja respuestas exitosas
- [ ] dashboardApi: Fallback a mocks cuando API falla
- [ ] feedbackApi: Envía actualizaciones
- [ ] Error handling con parseApiError

#### Utils
- [ ] dataMappers: Conversión frontend/backend
- [ ] formatters: Formateo de fechas y números
- [ ] validators: Validación de datos

### 2. Tests de Integración (30% del esfuerzo)

#### Pages
- [ ] DashboardPage: Carga inicial con datos
- [ ] DashboardPage: Manejo de errores con fallback
- [ ] NotFoundPage: Renderizado y navegación

#### User Flows
- [ ] Flujo completo: cargar → filtrar → paginar
- [ ] Cambiar importancia y verificar notificación
- [ ] Marcar como falso con justificación
- [ ] Navegación entre rutas

### 3. Tests E2E (10% del esfuerzo)

- [ ] Flujo editorial completo
- [ ] Performance con datos grandes
- [ ] Responsive en diferentes viewports

## Prioridades de Implementación

### Fase 1: Core (Alta Prioridad)
1. Setup y configuración base ✅
2. Tests de servicios API
3. Tests de hooks principales
4. Tests de páginas

### Fase 2: Components (Media Prioridad)  
1. Tests de organisms
2. Tests de molecules
3. Tests de atoms

### Fase 3: Polish (Baja Prioridad)
1. Tests de utils
2. Tests de accesibilidad
3. Tests de performance

## Métricas de Éxito

- **Coverage mínimo**: 80% overall
- **Coverage crítico**: 95% en servicios y hooks
- **Tiempo de ejecución**: < 30 segundos
- **Tests flaky**: 0%

## Convenciones

### Nombres de archivos
- Components: `ComponentName.test.tsx`
- Hooks: `useHookName.test.ts`
- Services: `serviceName.test.ts`
- Utils: `utilName.test.ts`

### Estructura de tests
```typescript
describe('ComponentName', () => {
  describe('rendering', () => {
    it('should render with default props', () => {})
    it('should render with custom props', () => {})
  })
  
  describe('interactions', () => {
    it('should handle user actions', () => {})
  })
  
  describe('edge cases', () => {
    it('should handle errors gracefully', () => {})
  })
})
```

### Mocking
- Usar MSW para APIs externas
- Mock mínimo necesario
- Preferir datos realistas

## Ejecución

1. **Desarrollo**: `npm run test:watch`
2. **CI/CD**: `npm test`
3. **Coverage**: `npm run test:coverage`

## Mantenimiento

- Actualizar tests con cada cambio de funcionalidad
- Revisar coverage semanalmente
- Refactorizar tests duplicados
- Mantener mocks actualizados
