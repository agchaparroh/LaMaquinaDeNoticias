/**
 * Barrel exports para hooks del dashboard
 * Exporta todos los hooks de lógica de negocio del dashboard
 */

export { useDashboard } from './useDashboard';
export type { DashboardState, UseDashboardOptions } from './useDashboard';

export { useFilters } from './useFilters';
export type { UseFiltersOptions, FiltersHookState } from './useFilters';

export { useFeedback } from './useFeedback';
export type { UseFeedbackOptions, FeedbackResult, SubmissionState } from './useFeedback';

// Integrated hook que combina los tres anteriores
export { useDashboardIntegrated } from './useDashboardIntegrated';

// Task 33 specific hooks
export { useFilters as useFiltersTask33 } from './useFiltersTask33';
export { useDashboardIntegrated as useDashboardTask33 } from './useDashboardIntegrated';
export type { FilterParams } from './useFiltersTask33';
