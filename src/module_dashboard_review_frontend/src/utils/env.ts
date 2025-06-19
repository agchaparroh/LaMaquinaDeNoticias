// Environment variable utility with type safety and mock mode
export const env = {
  // API URL with fallback to backend port
  apiUrl: import.meta.env.VITE_APP_API_URL || 'http://localhost:8004',
  
  // Environment name
  environment: import.meta.env.VITE_APP_ENV || 'development',
  
  // Debug mode
  debug: import.meta.env.VITE_APP_DEBUG === 'true',
  
  // Force mock mode when backend is not available
  forceMockMode: import.meta.env.VITE_APP_FORCE_MOCK === 'true' || false,
  
  // Helper to check if we're in production
  isProduction: () => env.environment === 'production',
  
  // Helper to check if we're in development
  isDevelopment: () => env.environment === 'development',
  
  // Helper to check if we should use mock data
  shouldUseMocks: () => env.forceMockMode || !env.apiUrl.startsWith('http'),
};