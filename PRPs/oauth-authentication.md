name: "OAuth 2.0 Authentication System - SuperClaude Context-Rich Implementation Spec"
description: |
  Complete OAuth 2.0 authentication implementation with Google and GitHub providers,
  including secure token management and user profile synchronization.

## Purpose
Implement a production-ready OAuth 2.0 authentication system following security best practices and SuperClaude standards.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, examples, and caveats
2. **Validation Loops**: Provide executable tests/lints the AI can run and fix
3. **Information Dense**: Use keywords and patterns from the codebase
4. **Progressive Success**: Start simple, validate, then enhance
5. **SuperClaude Integration**: Leverage existing commands and patterns
6. **Explicit Commands**: Every task specifies exact SuperClaude command to execute

---

## Goal
Implement complete OAuth 2.0 authentication with Google and GitHub providers, secure token management, and user profile sync.

## Implementation Blueprint

### Task Breakdown
```yaml
# Each task includes explicit SuperClaude command for deterministic execution

Task 1: Analyze current authentication architecture
  Priority: high
  Dependencies: []
  SuperClaude Command: /analyze --architecture --code --dependencies
  Persona: --persona-architect
  Files: ["src/auth/*", "src/middleware/auth.py", "src/models/user.py"]
  Validation: /test --unit src/auth
  Expected_Output: Architecture analysis report with OAuth integration points

Task 2: Design OAuth 2.0 integration system
  Priority: high
  Dependencies: [Task 1]
  SuperClaude Command: /design --system --patterns --api --think-hard
  Persona: --persona-architect
  Focus: Provider abstraction, token storage, security flow
  Validation: /review --architecture --evidence
  Expected_Output: OAuth system design with provider interfaces

Task 3: Implement OAuth provider abstraction
  Priority: high
  Dependencies: [Task 2]
  SuperClaude Command: /build --feature --tdd --patterns --uc
  Persona: --persona-backend
  Files:
    - CREATE src/auth/providers/base.py
    - CREATE src/auth/providers/google.py
    - CREATE src/auth/providers/github.py
  Validation: /test --unit --coverage
  Expected_Output: OAuth provider classes with tests

Task 4: Build secure token management
  Priority: high
  Dependencies: [Task 3]
  SuperClaude Command: /build --feature --secure --tdd
  Persona: --persona-security
  Files:
    - CREATE src/auth/token_manager.py
    - CREATE src/auth/token_storage.py
  Validation: /scan --security --owasp
  Expected_Output: Secure token handling with encryption

Task 5: Create authentication API endpoints
  Priority: high
  Dependencies: [Task 3, Task 4]
  SuperClaude Command: /build --api --feature --secure --uc
  Persona: --persona-backend
  Files:
    - CREATE src/api/routes/auth.py
    - UPDATE src/api/routes/__init__.py
  Validation: /test --integration --api
  Expected_Output: OAuth endpoints with rate limiting

Task 6: Implement frontend OAuth flow
  Priority: medium
  Dependencies: [Task 5]
  SuperClaude Command: /build --react --feature --secure --magic
  Persona: --persona-frontend
  Files:
    - CREATE src/components/Auth/OAuthLogin.tsx
    - CREATE src/hooks/useOAuth.ts
  Validation: /test --unit --e2e
  Expected_Output: React components for OAuth login

Task 7: Add comprehensive security testing
  Priority: high
  Dependencies: [Task 5, Task 6]
  SuperClaude Command: /scan --security --owasp --strict --penetration
  Persona: --persona-security
  Focus: CSRF, token leakage, session fixation
  Validation: /improve --security --strict
  Expected_Output: Security audit report and fixes

Task 8: Performance optimization and monitoring
  Priority: medium
  Dependencies: [Task 7]
  SuperClaude Command: /improve --performance --metrics --monitoring
  Persona: --persona-performance
  Tasks: Add caching, optimize queries, setup monitoring
  Validation: /test --performance --load
  Expected_Output: Optimized auth system with metrics

Task 9: Create comprehensive documentation
  Priority: medium
  Dependencies: [Task 8]
  SuperClaude Command: /document --api --user --comprehensive
  Persona: --persona-mentor
  Files:
    - CREATE docs/oauth-integration.md
    - UPDATE API documentation
  Expected_Output: Complete OAuth documentation
```

## Validation Loop

### Security Validation Commands
```bash
# Run after each implementation task
/scan --security --owasp --auth
/test --security --penetration
/review --security --evidence
```

### Performance Validation
```bash
# Check auth endpoint performance
/test --performance --api --load
/analyze --performance --metrics
```

## Confidence Score: 9/10

This PRP demonstrates explicit command mapping with:
- Every task has a specific SuperClaude command
- Appropriate personas for each domain
- Clear validation commands
- No ambiguous or interpreted instructions