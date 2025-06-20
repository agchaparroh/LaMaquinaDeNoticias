# Testing Documentation - Dashboard Review Frontend

## Overview

This directory contains all tests for the Dashboard Review Frontend module. We use Vitest as our testing framework with React Testing Library for component testing.

## Test Structure

```
tests/
├── setup.ts              # Global test setup
├── test-utils.tsx        # Custom render with providers
├── unit/                 # Unit tests for components and utilities
│   ├── components/       # Component tests
│   ├── hooks/           # Hook tests
│   ├── services/        # API service tests
│   └── utils/           # Utility function tests
├── integration/         # Integration tests
│   ├── flows/          # User flow tests
│   └── pages/          # Full page tests
└── mocks/              # Mock data and handlers
    ├── data/           # Mock data fixtures
    └── handlers/       # MSW request handlers
```

## Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage
```

## Test Categories

### Unit Tests
- **Components**: Test individual components in isolation
- **Hooks**: Test custom hooks with renderHook
- **Services**: Test API calls with mocked responses
- **Utils**: Test pure utility functions

### Integration Tests
- **User Flows**: Test complete user interactions
- **Page Tests**: Test full pages with all components
- **API Integration**: Test API error handling and fallbacks

## Testing Guidelines

1. **Use Testing Library queries**: Prefer `getByRole`, `getByLabelText` over `getByTestId`
2. **Test user behavior**: Focus on what users see and do, not implementation details
3. **Mock external dependencies**: Use MSW for API mocking
4. **Keep tests focused**: One test should verify one behavior
5. **Use descriptive test names**: `it('should show error message when API fails')`

## Coverage Goals

- Overall: 80%+
- Critical paths: 95%+
- Components: 90%+
- Utils: 100%

## Common Testing Patterns

### Testing Components
```typescript
import { render, screen, fireEvent } from '@/tests/test-utils'
import { MyComponent } from '@/components/MyComponent'

describe('MyComponent', () => {
  it('should render correctly', () => {
    render(<MyComponent />)
    expect(screen.getByText('Expected Text')).toBeInTheDocument()
  })
})
```

### Testing Hooks
```typescript
import { renderHook, act } from '@testing-library/react'
import { useMyHook } from '@/hooks/useMyHook'

describe('useMyHook', () => {
  it('should update state', () => {
    const { result } = renderHook(() => useMyHook())
    
    act(() => {
      result.current.updateValue('new value')
    })
    
    expect(result.current.value).toBe('new value')
  })
})
```

### Testing API Calls
```typescript
import { server } from '@/tests/mocks/server'
import { rest } from 'msw'
import { dashboardApi } from '@/services/dashboard'

describe('dashboardApi', () => {
  it('should handle API errors', async () => {
    server.use(
      rest.get('/api/hechos', (req, res, ctx) => {
        return res(ctx.status(500))
      })
    )
    
    await expect(dashboardApi.getHechos()).rejects.toThrow()
  })
})
```
