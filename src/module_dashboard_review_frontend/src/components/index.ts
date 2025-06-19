// Barrel exports for components
// Exports organizados por Atomic Design

// Re-export all component categories
export * from './atoms';
export * from './molecules';
export * from './organisms';
export * from './pages';

// Named exports para facilitar imports específicos
// Cuando se creen componentes, se podrán usar así:
// import { Button, HechoCard, FilterHeader, DashboardPage } from '@components';
// O específicamente:
// import { Button } from '@components/atoms';
// import { HechoCard } from '@components/molecules';
