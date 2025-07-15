name: "OAuth 2.0 Authentication System - SuperClaude Implementation Example"
description: |
  Comprehensive example of OAuth 2.0 authentication implementation using SuperClaude with explicit commands

## Purpose
Implement a complete OAuth 2.0 authentication system supporting Google and GitHub providers, with secure token management and user profile synchronization.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, examples, and caveats
2. **Validation Loops**: Provide executable tests/lints the AI can run and fix
3. **Information Dense**: Use keywords and patterns from the codebase
4. **Progressive Success**: Start simple, validate, then enhance
5. **SuperClaude Integration**: Leverage existing commands and patterns
6. **Explicit Commands**: Every task specifies exact SuperClaude command to execute

---

## Goal
Build a production-ready OAuth 2.0 authentication system that:
- Supports Google and GitHub OAuth providers
- Handles secure token storage and refresh
- Synchronizes user profiles automatically
- Integrates with existing authentication middleware
- Provides comprehensive error handling and logging

## Why
- **Business value**: Enable social login to increase user conversion by ~40%
- **Integration**: Replaces current basic email/password with modern OAuth flow
- **Problems solved**: 
  - Reduces password management complexity
  - Improves user experience with one-click login
  - Enhances security with provider-managed authentication

## What
User-visible behavior:
- "Login with Google" and "Login with GitHub" buttons
- Seamless redirect flow with provider authorization
- Automatic account creation or linking
- Profile picture and basic info synchronization
- Persistent login sessions with automatic token refresh

Technical requirements:
- OAuth 2.0 compliant implementation
- Support for authorization code flow
- Secure token storage (encrypted)
- Background token refresh
- Integration with existing user management

### Success Criteria
- [ ] OAuth flow completes successfully for both providers
- [ ] User profiles sync correctly from provider APIs
- [ ] Token refresh works automatically in background
- [ ] All security validations pass (OWASP compliance)
- [ ] Integration tests pass with >95% coverage
- [ ] Load testing handles >1000 concurrent OAuth flows

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- file: src/auth/middleware.js
  why: Current authentication patterns and session management
  
- file: src/models/User.js
  why: User model structure for OAuth integration
  
- url: https://developers.google.com/identity/protocols/oauth2
  why: Google OAuth 2.0 implementation guide
  critical: Scope management and token refresh patterns
  
- url: https://docs.github.com/en/apps/oauth-apps/building-oauth-apps
  why: GitHub OAuth application setup and API usage
  
- file: .env.example
  why: Environment variable patterns for OAuth credentials
  
- file: src/config/database.js
  why: Database connection patterns for OAuth token storage
```

### Current Codebase Structure
```bash
src/
├── auth/
│   ├── middleware.js          # Current auth middleware
│   ├── routes.js             # Auth routes
│   └── validators.js         # Input validation
├── models/
│   ├── User.js               # User model to extend
│   └── Session.js            # Session management
├── config/
│   ├── database.js           # DB config
│   └── app.js               # App configuration
└── tests/
    ├── auth/                 # Existing auth tests
    └── integration/          # Integration test patterns
```

### Desired Changes
```bash
CREATE: src/auth/oauth/
  Purpose: OAuth-specific authentication logic
  
CREATE: src/auth/oauth/providers/
  Purpose: Provider-specific implementations
  
CREATE: src/auth/oauth/providers/google.js
  Purpose: Google OAuth 2.0 implementation
  
CREATE: src/auth/oauth/providers/github.js
  Purpose: GitHub OAuth implementation
  
CREATE: src/auth/oauth/token-manager.js
  Purpose: Secure token storage and refresh logic
  
MODIFY: src/models/User.js
  Changes: Add OAuth provider fields and profile sync
  
MODIFY: src/auth/routes.js
  Changes: Add OAuth routes and callback handlers
  
CREATE: tests/auth/oauth/
  Purpose: Comprehensive OAuth testing suite
```

### Known Gotchas & Library Quirks
```javascript
// CRITICAL: OAuth state parameter must be cryptographically secure
// CRITICAL: Tokens must be encrypted at rest, never plain text
// CRITICAL: Provider APIs have rate limits - implement backoff
// CRITICAL: Token refresh must handle concurrent requests safely
// CRITICAL: PKCE required for mobile/SPA implementations
// Example: Google requires offline_access scope for refresh tokens
// Example: GitHub tokens expire after 8 hours by default
// CRITICAL: Follow SuperClaude patterns from shared/*.yml
```

## Implementation Blueprint

### Command Selection Guide
Quick reference for task command mapping:
- **Analysis tasks** → `/analyze --architecture --code`
- **Design tasks** → `/design --patterns --system`
- **Implementation** → `/build --feature --tdd`
- **Testing** → `/test --unit --coverage`
- **Security** → `/scan --security --owasp`
- **Optimization** → `/improve --performance --quality`
- **Documentation** → `/document --comprehensive --examples`

### Task Breakdown
```yaml
Task 1: Analyze current authentication system
  Priority: high
  Dependencies: []
  SuperClaude Command: /analyze --architecture --code --dependencies src/auth/
  Persona: --persona-architect
  Files: ["src/auth/*", "src/models/User.js", "src/config/*"]
  Pattern: Document current auth flow and integration points
  Validation: /document --analysis .claudedocs/analysis/current-auth.md
  Expected_Output: Architecture analysis with OAuth integration recommendations

Task 2: Design OAuth 2.0 system architecture
  Priority: high
  Dependencies: [Task 1]
  SuperClaude Command: /design --api --security --patterns --think-hard
  Persona: --persona-architect
  Deliverable: docs/design/oauth-architecture.md
  Implementation:
    - DESIGN secure token flow with encryption
    - PLAN provider abstraction layer
    - DEFINE error handling patterns
  Validation: 
    - /scan --security docs/design/oauth-architecture.md
    - Architecture includes security considerations
  Expected_Output: Comprehensive OAuth system design

Task 3: Set up OAuth configuration structure
  Priority: high
  Dependencies: [Task 2]
  SuperClaude Command: /build --config --structure --tdd
  Persona: --persona-backend
  Files:
    - CREATE: src/auth/oauth/config.js
    - CREATE: src/auth/oauth/providers/index.js
    - MODIFY: .env.example
  Implementation:
    - PATTERN: Configuration loading from src/config/app.js
    - ADD OAuth provider settings
    - IMPLEMENT secure credential management
  Validation: /test --unit --coverage src/auth/oauth/config.test.js
  Expected_Output: OAuth configuration system with validation

Task 4: Implement Google OAuth provider
  Priority: high
  Dependencies: [Task 3]
  SuperClaude Command: /build --feature --oauth --google --tdd
  Persona: --persona-backend
  Files:
    - CREATE: src/auth/oauth/providers/google.js
    - CREATE: tests/auth/oauth/providers/google.test.js
  Implementation:
    - IMPLEMENT authorization URL generation
    - HANDLE authorization code exchange
    - IMPLEMENT token refresh logic
    - ADD user profile fetching
  Validation: 
    - /test --unit --coverage tests/auth/oauth/providers/google.test.js
    - /scan --security src/auth/oauth/providers/google.js
  Expected_Output: Complete Google OAuth integration

Task 5: Implement GitHub OAuth provider  
  Priority: high
  Dependencies: [Task 4]
  SuperClaude Command: /build --feature --oauth --github --tdd
  Persona: --persona-backend
  Files:
    - CREATE: src/auth/oauth/providers/github.js
    - CREATE: tests/auth/oauth/providers/github.test.js
  Pattern: Follow Google provider structure from Task 4
  Validation:
    - /test --unit --coverage tests/auth/oauth/providers/github.test.js
    - /scan --security src/auth/oauth/providers/github.js
  Expected_Output: GitHub OAuth provider with same interface as Google

Task 6: Implement secure token management
  Priority: high
  Dependencies: [Task 3]
  SuperClaude Command: /build --feature --security --encryption --tdd
  Persona: --persona-security
  Files:
    - CREATE: src/auth/oauth/token-manager.js
    - CREATE: tests/auth/oauth/token-manager.test.js
  Implementation:
    - IMPLEMENT AES-256 token encryption
    - ADD automatic token refresh
    - HANDLE concurrent refresh requests
    - IMPLEMENT token revocation
  Validation:
    - /test --unit --coverage tests/auth/oauth/token-manager.test.js
    - /scan --security --owasp src/auth/oauth/token-manager.js
  Expected_Output: Secure token management system

Task 7: Extend User model for OAuth integration
  Priority: medium
  Dependencies: [Task 1]
  SuperClaude Command: /build --model --database --migration
  Persona: --persona-backend
  Files:
    - MODIFY: src/models/User.js
    - CREATE: migrations/add-oauth-fields.js
  Implementation:
    - ADD provider, provider_id, profile_data fields
    - IMPLEMENT account linking logic
    - ADD profile sync methods
  Validation:
    - /test --unit tests/models/User.test.js
    - /migrate --dry-run migrations/add-oauth-fields.js
  Expected_Output: User model with OAuth support

Task 8: Create OAuth route handlers
  Priority: high
  Dependencies: [Task 5, Task 6]
  SuperClaude Command: /build --api --routes --oauth --tdd
  Persona: --persona-backend
  Files:
    - CREATE: src/auth/oauth/routes.js
    - MODIFY: src/auth/routes.js
    - CREATE: tests/auth/oauth/routes.test.js
  Implementation:
    - ADD /auth/oauth/google and /auth/oauth/github routes
    - IMPLEMENT callback handlers
    - ADD error handling middleware
    - INTEGRATE with existing session management
  Validation:
    - /test --integration tests/auth/oauth/routes.test.js
    - /test --api tests/integration/oauth-flow.test.js
  Expected_Output: Complete OAuth API endpoints

Task 9: Implement frontend OAuth integration
  Priority: medium
  Dependencies: [Task 8]
  SuperClaude Command: /build --frontend --oauth --react
  Persona: --persona-frontend
  Files:
    - CREATE: frontend/components/OAuthButtons.jsx
    - CREATE: frontend/hooks/useOAuth.js
    - MODIFY: frontend/pages/Login.jsx
  Implementation:
    - ADD OAuth login buttons
    - IMPLEMENT redirect handling
    - ADD loading states and error handling
    - INTEGRATE with existing auth context
  Validation:
    - /test --e2e tests/e2e/oauth-flow.spec.js
    - /test --accessibility frontend/components/OAuthButtons.jsx
  Expected_Output: User-friendly OAuth login interface

Task 10: Comprehensive security testing
  Priority: high
  Dependencies: [Task 8]
  SuperClaude Command: /scan --security --owasp --oauth --strict
  Persona: --persona-security
  Focus:
    - Token storage security
    - CSRF protection
    - State parameter validation
    - Provider response validation
  Tests:
    - OAuth flow security tests
    - Token manipulation attempts
    - Cross-site request forgery tests
  Validation:
    - /test --security tests/security/oauth-security.test.js
    - Zero security vulnerabilities found
  Expected_Output: Security audit report with no critical issues

Task 11: Performance optimization and monitoring
  Priority: medium
  Dependencies: [Task 9]
  SuperClaude Command: /improve --performance --monitoring --oauth
  Persona: --persona-performance
  Implementation:
    - ADD OAuth flow metrics
    - OPTIMIZE token refresh performance
    - IMPLEMENT caching for provider metadata
    - ADD performance monitoring
  Validation:
    - /test --performance tests/performance/oauth-load.test.js
    - OAuth flow completes in <2 seconds
    - Token refresh under 500ms
  Expected_Output: Optimized OAuth system with monitoring

Task 12: Documentation and deployment preparation
  Priority: low
  Dependencies: [Task 11]
  SuperClaude Command: /document --api --deployment --comprehensive
  Persona: --persona-mentor
  Files:
    - CREATE: docs/oauth-setup-guide.md
    - CREATE: docs/api/oauth-endpoints.md
    - UPDATE: README.md
  Content:
    - OAuth setup instructions
    - API documentation
    - Security considerations
    - Troubleshooting guide
  Validation:
    - Documentation is complete and accurate
    - Setup guide tested on fresh environment
  Expected_Output: Complete OAuth documentation
```

### Integration Points
```yaml
DATABASE:
  - Migration: "ALTER TABLE users ADD oauth_provider, oauth_id, profile_data"
  - Indexes: "CREATE INDEX idx_oauth_provider_id ON users(oauth_provider, oauth_id)"
  
API:
  - Routes: "/auth/oauth/:provider, /auth/oauth/:provider/callback"
  - Middleware: "OAuth state validation, CSRF protection"
  
CONFIGURATION:
  - Environment: "GOOGLE_CLIENT_ID, GITHUB_CLIENT_SECRET, etc."
  - Settings: "OAuth provider configurations, token encryption keys"
  
MONITORING:
  - Logs: "OAuth flow events, token refresh activities, errors"
  - Metrics: "OAuth success rate, provider response times, token refresh frequency"
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
npm run lint           # ESLint with OAuth-specific rules
npm run format         # Prettier formatting
npm run typecheck      # TypeScript validation

# Expected: No errors. If errors, fix before continuing.
```

### Level 2: Unit Tests
```javascript
// Test cases implemented
describe('OAuth Providers', () => {
  it('generates secure authorization URLs', () => {
    const url = googleProvider.getAuthUrl('secure-state');
    expect(url).toContain('state=secure-state');
    expect(url).toContain('scope=openid email profile');
  });

  it('handles token exchange correctly', async () => {
    const tokens = await googleProvider.exchangeCode('auth-code');
    expect(tokens).toHaveProperty('access_token');
    expect(tokens).toHaveProperty('refresh_token');
  });

  it('encrypts tokens before storage', () => {
    const encrypted = tokenManager.encrypt('sample-token');
    expect(encrypted).not.toBe('sample-token');
    expect(tokenManager.decrypt(encrypted)).toBe('sample-token');
  });
});
```

### Level 3: Integration Tests
```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d

# Run OAuth integration tests
npm run test:integration -- --testNamePattern="OAuth"

# Manual verification
curl -X GET "http://localhost:3000/auth/oauth/google" \
  -H "Accept: application/json"
# Expected: Redirect to Google OAuth with proper parameters

# Load testing
npm run test:load -- oauth-flow.yml
# Expected: >1000 concurrent users, <2s response time
```

## Final Validation Checklist
- [ ] All syntax checks pass without errors
- [ ] TypeScript compilation successful
- [ ] Unit tests pass with >95% coverage
- [ ] Integration tests pass for both providers
- [ ] Security scan shows no vulnerabilities
- [ ] OAuth flow works end-to-end in browser
- [ ] Token refresh works automatically
- [ ] Performance targets met (<2s flow, <500ms refresh)
- [ ] Documentation complete and tested
- [ ] Deployment configuration validated

---

## Anti-Patterns to Avoid
- ❌ Don't store OAuth tokens in plain text
- ❌ Don't skip state parameter validation (CSRF risk)
- ❌ Don't hardcode provider URLs (use discovery)
- ❌ Don't ignore token expiration handling
- ❌ Don't bypass HTTPS in production
- ❌ Don't forget to revoke tokens on logout

## Confidence Score: 9/10

Rationale:
- Context completeness: Comprehensive provider documentation and security considerations
- Pattern clarity: Clear task breakdown with explicit SuperClaude commands
- Validation coverage: Multi-level testing including security and performance
- Risk factors: OAuth complexity manageable with proper patterns

Target: Successful one-pass implementation with production-ready security.

---
*OAuth 2.0 Authentication - SuperClaude PRP Example v1.0*