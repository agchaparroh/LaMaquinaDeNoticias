name: "[API Feature] - RESTful Service Implementation Spec"
description: |

## Purpose
[API endpoint/service description following REST principles and SuperClaude standards]

## Core Principles
1. **RESTful Design**: Follow REST conventions and HTTP semantics
2. **Contract First**: Define OpenAPI spec before implementation
3. **Security First**: Authentication, authorization, validation
4. **Performance**: Pagination, caching, rate limiting
5. **SuperClaude Integration**: Use existing API patterns

---

## Goal
[Specific API functionality to implement]

## Why
- **API consumers**: [Who will use this and why]
- **Business logic**: [Core functionality exposed]
- **Integration needs**: [Systems that will connect]

## What
### API Contract
```yaml
Endpoints:
  - GET /api/v1/[resource]
    Purpose: [List resources with filtering]
    Auth: [Required/Optional]
    
  - GET /api/v1/[resource]/{id}
    Purpose: [Get single resource]
    Auth: [Required/Optional]
    
  - POST /api/v1/[resource]
    Purpose: [Create new resource]
    Auth: Required
    
  - PUT /api/v1/[resource]/{id}
    Purpose: [Update entire resource]
    Auth: Required
    
  - PATCH /api/v1/[resource]/{id}
    Purpose: [Partial update]
    Auth: Required
    
  - DELETE /api/v1/[resource]/{id}
    Purpose: [Remove resource]
    Auth: Required
```

### Success Criteria
- [ ] All endpoints return correct HTTP status codes
- [ ] Proper error handling with consistent format
- [ ] Authentication/authorization working
- [ ] Input validation on all endpoints
- [ ] API documentation auto-generated
- [ ] Rate limiting implemented
- [ ] Response time <200ms for 95th percentile

## All Needed Context

### Documentation & References
```yaml
# MUST READ - API-specific context
- file: src/api/routes/[similar_endpoint].py
  why: Follow existing endpoint patterns
  
- file: src/api/middleware/auth.py
  why: Authentication middleware to integrate
  
- file: src/api/schemas/[related_schema].py
  why: Pydantic schema patterns
  
- url: https://fastapi.tiangolo.com/tutorial/
  section: "Path Parameters and Numeric Validations"
  why: Proper parameter validation
  
- doc: "OpenAPI Specification 3.0"
  why: Standard compliance for API documentation
```

### API Structure
```bash
src/api/
├── routes/
│   ├── __init__.py
│   └── [feature].py        # NEW: Your endpoints here
├── schemas/
│   ├── __init__.py
│   └── [feature].py        # NEW: Request/response models
├── services/
│   ├── __init__.py
│   └── [feature].py        # NEW: Business logic
├── middleware/
│   ├── auth.py            # Existing auth
│   └── rate_limit.py      # Existing rate limiting
└── dependencies/
    └── database.py        # Existing DB session
```

### Known API Patterns & Gotchas
```python
# CRITICAL: FastAPI dependency injection pattern
# CRITICAL: Always use Pydantic for validation
# CRITICAL: Async endpoints for I/O operations
# PATTERN: Consistent error response format:
# {
#   "error": {
#     "code": "VALIDATION_ERROR",
#     "message": "Human readable message",
#     "details": {...}
#   }
# }
```

## Implementation Blueprint

### Request/Response Schemas
```python
# schemas/[feature].py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class FeatureBase(BaseModel):
    """Base schema with common fields"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        # Custom validation logic
        return v.strip()

class FeatureCreate(FeatureBase):
    """Schema for creating resource"""
    pass

class FeatureUpdate(FeatureBase):
    """Schema for updating resource"""
    name: Optional[str] = None

class FeatureResponse(FeatureBase):
    """Schema for API responses"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class FeatureListResponse(BaseModel):
    """Paginated list response"""
    items: List[FeatureResponse]
    total: int
    page: int
    per_page: int
```

### Endpoint Implementation
```python
# routes/[feature].py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..dependencies import get_db
from ..schemas.feature import *
from ..services.feature import FeatureService
from ..middleware.auth import require_auth

router = APIRouter(prefix="/api/v1/features", tags=["features"])

@router.get("/", response_model=FeatureListResponse)
async def list_features(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List features with pagination and search"""
    service = FeatureService(db)
    return await service.list_features(page, per_page, search)

@router.post("/", response_model=FeatureResponse, status_code=201)
async def create_feature(
    feature: FeatureCreate,
    current_user = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Create new feature"""
    service = FeatureService(db)
    return await service.create_feature(feature, current_user)

# Additional endpoints...
```

### Service Layer
```python
# services/[feature].py
class FeatureService:
    def __init__(self, db: Session):
        self.db = db
    
    async def list_features(self, page: int, per_page: int, search: Optional[str]):
        # PATTERN: Efficient pagination
        query = self.db.query(Feature)
        
        if search:
            query = query.filter(Feature.name.ilike(f"%{search}%"))
        
        total = query.count()
        items = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page
        }
```

### Task Breakdown
```yaml
# Each task MUST specify explicit SuperClaude command and persona
# API-specific command mapping optimized for backend development

Task 1: Define API Schemas
  Priority: high
  Dependencies: []
  SuperClaude Command: /build --feature --tdd --uc
  Persona: --persona-backend
  Files:
    - CREATE src/api/schemas/[feature].py
  Validation: /test --type-check
  Expected_Output: Pydantic models with validation rules

Task 2: Implement Service Layer
  Priority: high
  Dependencies: [Task 1]
  SuperClaude Command: /build --feature --tdd --patterns
  Persona: --persona-backend
  Files:
    - CREATE src/api/services/[feature].py
  Pattern: Follow existing service patterns
  Include: Error handling, logging, transactions
  Validation: /test --unit --coverage
  Expected_Output: Service layer with business logic

Task 3: Create API Endpoints
  Priority: high
  Dependencies: [Task 1, Task 2]
  SuperClaude Command: /build --api --feature --uc
  Persona: --persona-backend
  Files:
    - CREATE src/api/routes/[feature].py
    - MODIFY src/api/routes/__init__.py (add router)
  Validation: /test --integration
  Expected_Output: RESTful endpoints with auth

Task 4: Add Comprehensive Tests
  Priority: medium
  Dependencies: [Task 3]
  SuperClaude Command: /test --unit --integration --coverage
  Persona: --persona-qa
  Files:
    - CREATE tests/api/test_[feature].py
  Coverage: >90% for endpoints
  Validation: /test --coverage --strict
  Expected_Output: Full test suite

Task 5: Security & Performance Review
  Priority: high
  Dependencies: [Task 3, Task 4]
  SuperClaude Command: /scan --security --owasp --performance
  Persona: --persona-security
  Validation: /improve --performance --metrics
  Expected_Output: Security audit and performance optimization

Task 6: Update API Documentation
  Priority: medium
  Dependencies: [Task 3]
  SuperClaude Command: /document --api --comprehensive
  Persona: --persona-mentor
  Files:
    - Auto-generated via FastAPI
    - CREATE docs/api/[feature].md (if needed)
  Verify: /docs endpoint shows new routes
  Expected_Output: Complete API documentation
```

## Validation Loop

### API-Specific Tests
```python
# Test authentication
def test_endpoint_requires_auth():
    response = client.get("/api/v1/features")
    assert response.status_code == 401

# Test validation
def test_invalid_input_rejected():
    response = client.post("/api/v1/features", json={"invalid": "data"})
    assert response.status_code == 422
    assert "validation_error" in response.json()

# Test pagination
def test_pagination_works():
    response = client.get("/api/v1/features?page=2&per_page=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 10
    assert data["page"] == 2
```

### Performance Validation
```bash
# Load testing
ab -n 1000 -c 10 -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/features

# Response time check
curl -w "@curl-format.txt" -o /dev/null -s \
  http://localhost:8000/api/v1/features
```

## Final Validation Checklist
- [ ] OpenAPI spec accurate and complete
- [ ] All endpoints follow REST conventions
- [ ] Proper HTTP status codes used
- [ ] Authentication/authorization working
- [ ] Input validation comprehensive
- [ ] Error responses consistent
- [ ] Rate limiting active
- [ ] API versioning implemented
- [ ] Documentation auto-generated
- [ ] Performance targets met

---

## API Anti-Patterns to Avoid
- ❌ Don't use verbs in endpoint paths
- ❌ Don't return 200 OK for errors
- ❌ Don't expose internal IDs
- ❌ Don't skip input validation
- ❌ Don't ignore rate limiting
- ❌ Don't break backwards compatibility

## Confidence Score: [X]/10

API-specific assessment:
- Endpoint design: [assessment]
- Security implementation: [assessment]
- Performance considerations: [assessment]
- Documentation completeness: [assessment]