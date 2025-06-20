# Tests Pendientes - module_dashboard_review_frontend

## Tests de Componentes - Atoms
* ErrorBoundary captura errores y muestra fallback UI
* Button maneja eventos click correctamente
* Input valida y emite cambios
* Spinner muestra animación de carga

## Tests de Componentes - Molecules
* HechoCard renderiza información completa del hecho
* HechoCard maneja click para abrir modal de detalle
* FeedbackSnackbar muestra notificaciones y auto-cierra
* HechoDetailModal muestra información expandida y cierra correctamente

## Tests de Componentes - Organisms
* FilterHeader aplica filtros correctamente
* FilterHeader limpia filtros al hacer reset
* HechosList renderiza lista paginada
* HechosList muestra skeleton mientras carga
* HechosList muestra mensaje cuando no hay resultados

## Tests de Páginas
* DashboardPage carga y muestra datos iniciales
* DashboardPage maneja errores de API con fallback a mocks
* NotFoundPage renderiza correctamente con link de retorno

## Tests de Hooks
* useDashboard fetch inicial de datos
* useDashboard aplica filtros y paginación
* useFilters maneja cambios de filtros con debounce
* useFeedback envía cambios de importancia
* useFeedback envía marcado como falso

## Tests de Servicios
* dashboardApi maneja respuestas exitosas
* dashboardApi fallback a mocks cuando API falla
* feedbackApi envía actualizaciones correctamente
* Error handling con parseApiError

## Tests de Integración
* Flujo completo: cargar dashboard → filtrar → paginar
* Cambiar importancia de un hecho y verificar notificación
* Marcar hecho como falso con justificación
* Navegación entre rutas (dashboard, 404)

## Tests de Routing
* Redirección de / a /dashboard
* Rutas no existentes redirigen a /404
* Navegación mantiene estado de filtros

## Tests de Estado y Props
* Tipos TypeScript correctos en todos los componentes
* Props requeridas vs opcionales
* Estados de loading, error y empty
* Tema de Material UI aplicado correctamente

## Tests de Accesibilidad
* Navegación por teclado en modales
* Aria labels en elementos interactivos
* Contraste de colores adecuado
* Focus visible en elementos navegables

## Tests de Responsive
* Layout adaptable en mobile (< 768px)
* Layout adaptable en tablet (768px - 1024px)
* Layout completo en desktop (> 1024px)
* Modales responsivos en todas las resoluciones
