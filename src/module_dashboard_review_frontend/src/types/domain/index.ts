// Barrel exports for domain types
// Entidades de negocio y tipos del dashboard

// Dashboard types
export type {
  Hecho,
  HechoRelacion,
  HechoCluster,
  ArticuloMetadata,
  FilterState,
  PaginationParams,
  DashboardState,
  FilterOptions,
  DashboardStats,
  EvaluacionEditorial
} from './dashboard';

// Feedback types - all
export type {
  FeedbackType,
  Feedback,
  FeedbackResponse,
  FeedbackSubmission,
  ConfirmationDialogState,
  NotificationProps,
  ImportanciaFeedbackRequest,
  ImportanciaFeedbackResponse,
  EvaluacionEditorialRequest,
  EvaluacionEditorialResponse
} from './feedback';

// Filter and search types (existing)
export type {
  DashboardFilters,
  SortField,
  SortDirection,
  ActiveFiltersState,
  PaginationState,
  FilteredResults
} from './filters';

// Filter parameters types (Task 33)
export type {
  FilterParams,
  DashboardResponse,
  FilterOptionsResponse
} from './filterParams';
export {
  defaultFilters
} from './filterParams';

// Constants
export {
  IMPORTANCIA_MIN,
  IMPORTANCIA_MAX,
  DEFAULT_PAGE_SIZE,
  EVALUACION_OPTIONS
} from './dashboard';

// API Error types (importados directamente desde utils)
export type {
  ApiError
} from '@/utils/api/errorHandling';
export {
  ApiErrorType
} from '@/utils/api/errorHandling';