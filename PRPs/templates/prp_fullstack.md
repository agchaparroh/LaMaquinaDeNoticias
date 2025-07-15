name: "[Fullstack Feature] - End-to-End Implementation Spec"
description: |

## Purpose
[Complete feature spanning frontend, API, and backend following SuperClaude standards]

## Core Principles
1. **End-to-End Thinking**: User flow from UI to database
2. **Separation of Concerns**: Clean architecture layers
3. **Data Consistency**: Transactions, validation, sync
4. **Security Throughout**: Defense in depth
5. **SuperClaude Integration**: Leverage all patterns

---

## Goal
[Complete feature description from user perspective to system implementation]

## Why
- **User value**: [Complete user journey enabled]
- **System enhancement**: [Architecture improvements]
- **Business impact**: [Metrics and KPIs affected]

## What
### Feature Overview
```yaml
Frontend:
  - Components: [List of UI components]
  - Routes: [New/modified routes]
  - State: [State management needs]

API:
  - Endpoints: [REST/GraphQL endpoints]
  - Authentication: [Auth requirements]
  - Validation: [Input/output validation]

Backend:
  - Services: [Business logic services]
  - Database: [Schema changes]
  - Integration: [External services]

Infrastructure:
  - Deployment: [Container/service updates]
  - Monitoring: [Logs, metrics, alerts]
  - Configuration: [Environment variables]
```

### Success Criteria
- [ ] Complete user flow works end-to-end
- [ ] All layers properly integrated
- [ ] Data consistency maintained
- [ ] Security requirements met
- [ ] Performance targets achieved
- [ ] Monitoring and alerts configured
- [ ] Documentation complete

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Fullstack context
- file: docs/architecture/overview.md
  why: System architecture and patterns
  
- file: src/api/routes/[similar_feature].py
  why: API pattern reference
  
- file: src/components/[similar_feature]/
  why: Frontend pattern reference
  
- file: src/services/[similar_service].py
  why: Service layer patterns
  
- file: docker-compose.yml
  why: Service orchestration
  
- url: [Architecture decision records]
  why: Design decisions and rationale
```

### System Architecture
```bash
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│     API     │────▶│   Backend   │
│    React    │     │   FastAPI   │     │  Services   │
└─────────────┘     └─────────────┘     └─────────────┘
       │                    │                    │
       └────────────────────┴────────────────────┘
                            │
                    ┌───────▼────────┐
                    │    Database     │
                    │   PostgreSQL    │
                    └────────────────┘
```

### Data Flow
```yaml
User Action:
  1. UI Component → User interaction
  2. State Update → Local state/Redux
  3. API Call → Async request
  4. Validation → Input validation
  5. Auth Check → Verify permissions
  6. Service Logic → Business rules
  7. Database → CRUD operations
  8. Response → Format and return
  9. UI Update → Display results
  10. Analytics → Track event
```

## Implementation Blueprint

### Database Schema
```sql
-- Migration: add_feature_tables.sql
CREATE TABLE features (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_features_user_id ON features(user_id);
CREATE INDEX idx_features_created_at ON features(created_at);

-- Add audit triggers
CREATE TRIGGER update_features_updated_at
    BEFORE UPDATE ON features
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### Backend Service Layer
```python
# services/feature_service.py
from typing import List, Optional
from sqlalchemy.orm import Session
from ..models import Feature
from ..schemas import FeatureCreate, FeatureUpdate

class FeatureService:
    def __init__(self, db: Session):
        self.db = db
    
    async def create_feature(
        self, 
        feature_data: FeatureCreate, 
        user_id: int
    ) -> Feature:
        """Create feature with business logic"""
        # Validate business rules
        await self._validate_feature_limits(user_id)
        
        # Create with transaction
        with self.db.begin():
            feature = Feature(
                **feature_data.dict(),
                user_id=user_id
            )
            self.db.add(feature)
            
            # Additional operations in transaction
            await self._update_user_stats(user_id)
            await self._send_notification(user_id, feature)
        
        return feature
    
    async def _validate_feature_limits(self, user_id: int):
        """Check user hasn't exceeded limits"""
        count = self.db.query(Feature).filter_by(
            user_id=user_id
        ).count()
        
        if count >= MAX_FEATURES_PER_USER:
            raise BusinessLogicError("Feature limit exceeded")
```

### API Layer
```python
# api/routes/features.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ..dependencies import get_current_user, get_db
from ..services import FeatureService
from ..schemas import FeatureResponse, FeatureCreate

router = APIRouter(prefix="/api/v1/features")

@router.post("/", response_model=FeatureResponse)
async def create_feature(
    feature_data: FeatureCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new feature with full validation"""
    try:
        service = FeatureService(db)
        feature = await service.create_feature(
            feature_data, 
            current_user.id
        )
        
        # Log for monitoring
        logger.info(f"Feature created: {feature.id}")
        
        return feature
    except BusinessLogicError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Frontend Integration
```typescript
// services/featureApi.ts
import { api } from '../utils/api';
import { Feature, FeatureCreate } from '../types/feature';

export const featureApi = {
  create: async (data: FeatureCreate): Promise<Feature> => {
    const response = await api.post('/api/v1/features', data);
    return response.data;
  },
  
  list: async (params?: ListParams): Promise<PaginatedResponse<Feature>> => {
    const response = await api.get('/api/v1/features', { params });
    return response.data;
  }
};

// components/FeatureForm/FeatureForm.tsx
import React from 'react';
import { useForm } from 'react-hook-form';
import { useMutation, useQueryClient } from 'react-query';
import { featureApi } from '../../services/featureApi';

export const FeatureForm: React.FC = () => {
  const queryClient = useQueryClient();
  const { register, handleSubmit, formState: { errors } } = useForm();
  
  const createMutation = useMutation(featureApi.create, {
    onSuccess: () => {
      queryClient.invalidateQueries('features');
      toast.success('Feature created successfully');
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Error creating feature');
    }
  });
  
  const onSubmit = (data: FeatureCreate) => {
    createMutation.mutate(data);
  };
  
  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      {/* Form fields */}
    </form>
  );
};
```

### Task Breakdown
```yaml
# Each task MUST specify explicit SuperClaude command and persona
# Fullstack command mapping covers database to UI

Task 1: Database Setup
  Priority: high
  Dependencies: []
  SuperClaude Command: /migrate --create --schema
  Persona: --persona-backend
  Files:
    - CREATE migrations/add_feature_tables.sql
    - CREATE src/models/feature.py
  Validation: /test --database --migrate
  Expected_Output: Database schema and models created

Task 2: Backend Service Implementation
  Priority: high
  Dependencies: [Task 1]
  SuperClaude Command: /build --feature --tdd --patterns
  Persona: --persona-backend
  Files:
    - CREATE src/services/feature_service.py
    - CREATE tests/services/test_feature_service.py
  Validation: /test --unit --coverage
  Expected_Output: Service layer with business logic

Task 3: API Endpoints
  Priority: high
  Dependencies: [Task 2]
  SuperClaude Command: /build --api --feature --uc
  Persona: --persona-backend
  Files:
    - CREATE src/api/routes/features.py
    - CREATE src/api/schemas/feature.py
    - UPDATE src/api/routes/__init__.py
  Validation: /test --integration --api
  Expected_Output: RESTful API with documentation

Task 4: Frontend Components
  Priority: medium
  Dependencies: [Task 3]
  SuperClaude Command: /build --react --feature --magic
  Persona: --persona-frontend
  Files:
    - CREATE src/components/Feature/
    - CREATE src/services/featureApi.ts
    - UPDATE src/routes/index.tsx
  Validation: /test --unit --e2e
  Expected_Output: React components with API integration

Task 5: Integration Testing
  Priority: medium
  Dependencies: [Task 1, Task 2, Task 3, Task 4]
  SuperClaude Command: /test --e2e --integration --full-stack
  Persona: --persona-qa
  Files:
    - CREATE tests/e2e/feature.spec.ts
  Validation: /test --e2e --coverage
  Expected_Output: Complete user flow tests

Task 6: Security & Performance Review
  Priority: high
  Dependencies: [Task 5]
  SuperClaude Command: /scan --security --performance --fullstack
  Persona: --persona-security
  Validation: /improve --performance --security
  Expected_Output: Security audit and performance optimization

Task 7: Deployment & Monitoring
  Priority: low
  Dependencies: [Task 6]
  SuperClaude Command: /deploy --setup --monitoring
  Persona: --persona-devops
  Files:
    - UPDATE docker-compose.yml
    - UPDATE .env.example
    - CREATE monitoring/feature-dashboard.json
  Validation: /deploy --test --health-check
  Expected_Output: Deployed service with monitoring
```

## Validation Loop

### Integration Testing
```python
# tests/integration/test_feature_flow.py
async def test_complete_feature_flow():
    """Test entire feature flow from API to DB"""
    # Create user
    user = await create_test_user()
    
    # Authenticate
    token = await get_auth_token(user)
    
    # Create feature via API
    response = await client.post(
        "/api/v1/features",
        json={"name": "Test Feature"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    feature_id = response.json()["id"]
    
    # Verify in database
    feature = await get_feature_from_db(feature_id)
    assert feature.name == "Test Feature"
    assert feature.user_id == user.id
    
    # Verify via API
    response = await client.get(
        f"/api/v1/features/{feature_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
```

### End-to-End Testing
```typescript
// tests/e2e/feature.spec.ts
describe('Feature Management', () => {
  beforeEach(() => {
    cy.login();
    cy.visit('/features');
  });
  
  it('creates new feature', () => {
    cy.findByRole('button', { name: /create feature/i }).click();
    
    cy.findByLabelText(/name/i).type('Test Feature');
    cy.findByLabelText(/description/i).type('Test Description');
    
    cy.findByRole('button', { name: /submit/i }).click();
    
    cy.findByText('Feature created successfully').should('be.visible');
    cy.findByText('Test Feature').should('be.visible');
  });
});
```

### Performance Testing
```bash
# API load testing
locust -f tests/load/feature_api.py --host=http://localhost:8000

# Database query analysis
EXPLAIN ANALYZE SELECT * FROM features WHERE user_id = 1;

# Frontend bundle analysis
npm run build:analyze
```

## Final Validation Checklist
- [ ] Database migrations applied cleanly
- [ ] Backend services tested (>90% coverage)
- [ ] API endpoints documented and tested
- [ ] Frontend components render correctly
- [ ] End-to-end user flow works
- [ ] Performance requirements met
- [ ] Security scan passes
- [ ] Monitoring dashboards configured
- [ ] Documentation complete
- [ ] Deployment successful

---

## Fullstack Anti-Patterns to Avoid
- ❌ Don't bypass any layer's validation
- ❌ Don't duplicate business logic
- ❌ Don't ignore transaction boundaries
- ❌ Don't skip integration tests
- ❌ Don't hardcode cross-layer configs
- ❌ Don't forget error propagation

## Confidence Score: [X]/10

Fullstack assessment:
- Architecture alignment: [assessment]
- Layer integration: [assessment]
- Data flow clarity: [assessment]
- Testing coverage: [assessment]
- Deployment readiness: [assessment]