name: "[Frontend Feature] - React Component Implementation Spec"
description: |

## Purpose
[UI/UX feature description following React best practices and SuperClaude standards]

## Core Principles
1. **Component Composition**: Small, reusable, testable components
2. **State Management**: Clear data flow, minimal state
3. **Accessibility**: WCAG 2.1 AA compliance
4. **Performance**: Lazy loading, memoization, code splitting
5. **SuperClaude Integration**: Follow existing UI patterns

---

## Goal
[Specific UI functionality and user experience goals]

## Why
- **User needs**: [What users can accomplish]
- **UX improvement**: [How this enhances experience]
- **Business metrics**: [KPIs affected]

## What
### User Stories
```yaml
As a: [user role]
I want to: [action/feature]
So that: [benefit/outcome]

Acceptance Criteria:
  - [ ] [Specific measurable criterion]
  - [ ] [User can perform X action]
  - [ ] [System responds with Y]
```

### UI/UX Requirements
- **Desktop**: Full functionality, optimized layout
- **Tablet**: Responsive, touch-friendly
- **Mobile**: Essential features, performance-first
- **Accessibility**: Keyboard nav, screen readers, ARIA

### Success Criteria
- [ ] Component renders without errors
- [ ] All user interactions work as designed
- [ ] Responsive on all screen sizes
- [ ] Accessibility audit passes
- [ ] Performance budget met (<3s load)
- [ ] Unit tests >90% coverage
- [ ] E2E tests for critical paths

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Frontend-specific context
- file: src/components/[similar_component]/index.tsx
  why: Component structure and patterns
  
- file: src/hooks/[related_hook].ts
  why: Custom hooks pattern
  
- file: src/styles/theme.ts
  why: Design system tokens
  
- url: https://react.dev/learn
  section: "Thinking in React"
  why: Component design principles
  
- file: src/utils/test-utils.tsx
  why: Testing setup and patterns
```

### Component Structure
```bash
src/
├── components/
│   └── [FeatureName]/
│       ├── index.tsx           # Main component
│       ├── [FeatureName].tsx   # Component logic
│       ├── [FeatureName].module.css  # Styles
│       ├── [FeatureName].test.tsx    # Tests
│       ├── [FeatureName].stories.tsx # Storybook
│       └── types.ts            # TypeScript types
├── hooks/
│   └── use[Feature].ts        # Custom hooks
├── services/
│   └── [feature]Service.ts    # API integration
└── store/
    └── [feature]Slice.ts      # State management
```

### Known Frontend Patterns & Gotchas
```typescript
// CRITICAL: Always use TypeScript with strict mode
// CRITICAL: Memoize expensive computations
// CRITICAL: Handle loading/error states
// PATTERN: Custom hooks for logic reuse
// PATTERN: CSS Modules for styling
// GOTCHA: React 18 Strict Mode double-renders
```

## Implementation Blueprint

### Component Architecture
```typescript
// types.ts
export interface FeatureProps {
  id: string;
  initialData?: FeatureData;
  onUpdate?: (data: FeatureData) => void;
  className?: string;
}

export interface FeatureData {
  // Define data structure
}

// [FeatureName].tsx
import React, { useState, useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import styles from './[FeatureName].module.css';
import { FeatureProps } from './types';

export const FeatureName: React.FC<FeatureProps> = ({
  id,
  initialData,
  onUpdate,
  className
}) => {
  const { t } = useTranslation();
  const [data, setData] = useState(initialData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  // PATTERN: Memoized computed values
  const computedValue = useMemo(() => {
    return expensiveComputation(data);
  }, [data]);
  
  // PATTERN: Callback optimization
  const handleUpdate = useCallback(async (newData: FeatureData) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await updateFeature(newData);
      setData(result);
      onUpdate?.(result);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [onUpdate]);
  
  // PATTERN: Early returns for states
  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;
  
  return (
    <div className={`${styles.container} ${className}`}>
      {/* Component JSX */}
    </div>
  );
};
```

### Custom Hooks
```typescript
// hooks/use[Feature].ts
import { useState, useEffect } from 'react';
import { featureService } from '../services/featureService';

export const useFeature = (id: string) => {
  const [data, setData] = useState<FeatureData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  
  useEffect(() => {
    let cancelled = false;
    
    const fetchData = async () => {
      try {
        const result = await featureService.getFeature(id);
        if (!cancelled) {
          setData(result);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err as Error);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };
    
    fetchData();
    
    return () => {
      cancelled = true;
    };
  }, [id]);
  
  return { data, loading, error, refetch: fetchData };
};
```

### State Management
```typescript
// store/[feature]Slice.ts (Redux Toolkit example)
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

export const fetchFeature = createAsyncThunk(
  'feature/fetch',
  async (id: string) => {
    return await featureService.getFeature(id);
  }
);

const featureSlice = createSlice({
  name: 'feature',
  initialState: {
    data: null,
    loading: false,
    error: null
  },
  reducers: {
    updateFeature: (state, action) => {
      state.data = action.payload;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchFeature.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchFeature.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
      })
      .addCase(fetchFeature.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      });
  }
});
```

### Task Breakdown
```yaml
# Each task MUST specify explicit SuperClaude command and persona
# Frontend-specific command mapping optimized for React development

Task 1: Create Component Structure
  Priority: high
  Dependencies: []
  SuperClaude Command: /build --react --init --uc
  Persona: --persona-frontend
  Files:
    - CREATE src/components/[Feature]/
    - CREATE types, component, styles, tests
  Validation: /test --type-check
  Expected_Output: Component structure with TypeScript types

Task 2: Implement Core Functionality
  Priority: high
  Dependencies: [Task 1]
  SuperClaude Command: /build --react --feature --magic
  Persona: --persona-frontend
  Implementation:
    - State management with hooks
    - Event handlers with proper types
    - API integration with error handling
  Pattern: Follow existing component patterns
  Validation: /test --unit --coverage
  Expected_Output: Fully functional React component

Task 3: Style Component
  Priority: medium
  Dependencies: [Task 2]
  SuperClaude Command: /build --react --style --responsive
  Persona: --persona-frontend
  Files:
    - CREATE/UPDATE CSS modules
  Requirements:
    - Responsive design (mobile-first)
    - Theme compliance
    - Accessibility (ARIA labels)
  Validation: /test --accessibility
  Expected_Output: Styled component with responsive design

Task 4: Add Comprehensive Tests
  Priority: high
  Dependencies: [Task 2]
  SuperClaude Command: /test --unit --integration --e2e
  Persona: --persona-qa
  Files:
    - Unit tests (React Testing Library)
    - Integration tests
    - Storybook stories
  Coverage: >90%
  Validation: /test --coverage --strict
  Expected_Output: Complete test suite with stories

Task 5: Optimize Performance
  Priority: medium
  Dependencies: [Task 2, Task 3]
  SuperClaude Command: /improve --performance --react --metrics
  Persona: --persona-performance
  Tasks:
    - Add React.memo and useMemo
    - Implement lazy loading
    - Run bundle analysis
  Target: <100KB component bundle
  Validation: /analyze --performance --bundle
  Expected_Output: Optimized component with performance metrics

Task 6: Document Component
  Priority: low
  Dependencies: [Task 4]
  SuperClaude Command: /document --component --examples
  Persona: --persona-mentor
  Files:
    - README.md for component
    - Props documentation
    - Usage examples
  Expected_Output: Complete component documentation
```

## Validation Loop

### Component Testing
```typescript
// [FeatureName].test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FeatureName } from './FeatureName';

describe('FeatureName', () => {
  it('renders without crashing', () => {
    render(<FeatureName id="test" />);
    expect(screen.getByRole('main')).toBeInTheDocument();
  });
  
  it('handles user interaction', async () => {
    const user = userEvent.setup();
    const onUpdate = jest.fn();
    
    render(<FeatureName id="test" onUpdate={onUpdate} />);
    
    await user.click(screen.getByRole('button'));
    
    await waitFor(() => {
      expect(onUpdate).toHaveBeenCalled();
    });
  });
  
  it('is accessible', async () => {
    const { container } = render(<FeatureName id="test" />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
```

### Visual Testing
```typescript
// [FeatureName].stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { FeatureName } from './FeatureName';

const meta: Meta<typeof FeatureName> = {
  title: 'Components/FeatureName',
  component: FeatureName,
  parameters: {
    layout: 'centered',
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    id: 'story-1',
  },
};

export const Loading: Story = {
  args: {
    id: 'story-2',
  },
  parameters: {
    mockData: {
      loading: true,
    },
  },
};
```

### Performance Testing
```bash
# Bundle size analysis
npm run build
npm run analyze

# Lighthouse audit
npm run lighthouse

# Runtime performance
npm run test:performance
```

## Final Validation Checklist
- [ ] TypeScript strict mode passes
- [ ] No React warnings in console
- [ ] Component tree optimized (React DevTools)
- [ ] Accessibility audit passes (axe)
- [ ] Responsive on all breakpoints
- [ ] Keyboard navigation works
- [ ] Error boundaries implemented
- [ ] Loading states handled
- [ ] Performance budget met
- [ ] Storybook documentation complete

---

## Frontend Anti-Patterns to Avoid
- ❌ Don't use inline styles
- ❌ Don't manipulate DOM directly
- ❌ Don't ignore React warnings
- ❌ Don't skip error boundaries
- ❌ Don't use index as key in lists
- ❌ Don't forget cleanup in useEffect

## Confidence Score: [X]/10

Frontend-specific assessment:
- Component design: [assessment]
- State management: [assessment]
- Accessibility: [assessment]
- Performance optimization: [assessment]