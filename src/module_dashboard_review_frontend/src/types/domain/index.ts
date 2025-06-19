// Barrel exports for domain types
// Entidades de negocio y tipos del dashboard

// Dashboard types
export type {
  Hecho,
  ArticuloMetadata,
  FilterState,
  PaginationParams,
  DashboardState,
  FilterOptions,
  DashboardStats,
  EvaluacionEditorial
} from './dashboard';

// Feedback types - existing
export type {
  ImportanciaFeedbackRequest,
  ImportanciaFeedbackResponse,
  EvaluacionEditorialRequest,
  EvaluacionEditorialResponse,
  EvaluacionModalState,
  ImportanciaFeedbackState,
  FeedbackNotification,
  FeedbackType
} from './feedback';

// Feedback types - new (Task 34)
export type {
  Feedback,
  FeedbackResponse,
  FeedbackSubmission,
  ConfirmationDialogState,
  NotificationProps
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