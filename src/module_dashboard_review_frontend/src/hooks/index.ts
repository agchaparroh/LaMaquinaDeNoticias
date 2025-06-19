/**
 * Barrel exports para hooks
 * Custom hooks organizados por funcionalidad y dominio de negocio
 */

// Common utilities hooks
export * from './common';

// Dashboard business logic hooks
export * from './dashboard';

// Feedback hooks (legacy - functionality moved to dashboard hooks)
export * from './feedback';

// Usage examples:
// import { useApi, useDashboard, useFilters, useFeedback } from '@/hooks';
// O específicamente:
// import { useApi, useDebounce } from '@/hooks/common';
// import { useDashboard, useFilters, useFeedback } from '@/hooks/dashboard';
