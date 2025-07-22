# Generate PRP

**Purpose**: Generate executable specifications for complex features

---

@include shared/universal-constants.yml#Universal_Legend

## Command
`/generate-prp [feature-name] [--flags]`

## Process Overview
Research → Analyze → Generate → Validate → Save

## 1. Research Phase

### Pre-Generation File Study
Before generating any task, deeply study ALL files that will be touched:

```yaml
For Each Target File:
  1. Read Complete Content:
     - Current structure and organization
     - Exact line numbers for modifications
     - Import patterns and dependencies
     - Error handling approaches
  
  2. Study Patterns:
     - Naming conventions (variables, functions)
     - Code style (spacing, brackets, quotes)
     - Comment format and location
     - Test coverage and patterns
  
  3. Map Interactions:
     - What imports this file?
     - What does this file export/expose?
     - Related test files
     - Configuration dependencies
```

### Configuration Ecosystem
Study ALL configuration files that affect the implementation:

```yaml
Essential Files:
  - package.json/requirements.txt: Exact versions
  - .env.example: Required environment variables
  - Config files: Build, lint, test settings
  - Docker/CI: Deployment constraints
  - Database schemas: Current structure
```

### Codebase Analysis
- Find similar features already implemented
- Document discovered conventions from file study
- Extract patterns from actual code (not assumptions)
- Note architectural decisions in practice

### External Research  
- Search Context7 for library docs (matching installed versions)
- Verify best practices against current codebase
- Identify security requirements
- Confirm compatibility with existing setup

## 2. Generation Phase

### Task Structure
Every task MUST include:

```yaml
Task N: [Specific description]
  Priority: [high/medium/low]
  Dependencies: [previous tasks]
  
  Consultar:
    Codebase: [files to review before executing]
    External: [Context7 refs, URLs]
    Tools: [analysis commands]
  
  Files: [files to create/modify]
  
  # Choose execution method based on criteria below
  [Execution Method - see section 3]
  
  Validation: [executable commands only]
  Expected_Output: [measurable outcome]
```

## 3. Execution Methods

### Decision Criteria

| Use Case | Method | When to Use |
|----------|--------|-------------|
| Standard operations | SuperClaude Command | Pattern exists, no special requirements |
| Precise changes | Explicit Instructions | Exact code/config needed |
| Complex features | Hybrid | Need guidance + specifics |

### Method 1: SuperClaude Command
```yaml
SuperClaude Command: /build --feature --tdd
Persona: --persona-backend
```

### Method 2: Explicit Instructions  
```yaml
Explicit Instructions: |
  1. In file.py line 45, replace X with Y
  2. Create new_file.py with: [complete code]
```

### Method 3: Hybrid
```yaml
SuperClaude Command: /build --feature
Additional Instructions: |
  - Specific requirement 1
  - Specific requirement 2
```

## 4. Zero Ambiguity Rules

ALL instructions must be:
- **Executable**: No interpretation needed
- **Complete**: Full code, not descriptions  
- **Specific**: Exact lines, values, commands
- **Verifiable**: Runnable validations

❌ Avoid: "Optimize performance"
✅ Use: "Replace sleep(1) with sleep(0.1) on line 42"

## 5. Quality Checklist

Before saving PRP, verify:
- □ All target files have been studied completely
- □ Line numbers for modifications are exact
- □ Code patterns match existing style
- □ Every task has Consultar field populated
- □ All instructions are unambiguous
- □ Validations are executable commands
- □ Dependencies are explicit
- □ No redundant information
- □ Each task maps to one execution method
- □ Checkpoints planned after each task
- □ Configuration requirements documented

## Output

Save to: `PRPs/[feature-name].md`

### PRP Structure
```markdown
name: [Feature] Implementation Spec
description: [One paragraph summary]

## Goal
[Specific, measurable end state]

## Context
[Only essential background]

## Tasks
[Generated tasks following structure above]

## Success Criteria
- [ ] [Measurable outcome 1]
- [ ] [Measurable outcome 2]

## Validation Commands
[Global validation commands to run after all tasks]
```

## Examples

### Example 1: Standard Feature
```bash
/generate-prp user-auth --persona-security

# Generates tasks like:
Task 1: Create authentication middleware
  Priority: high
  
  Consultar:
    Codebase: ["src/middleware/", "src/auth/"]
    External: [Context7: "/express/docs middleware"]
  
  Files: ["src/middleware/auth.js"]
  
  SuperClaude Command: /build --feature --tdd
  Persona: --persona-security
  
  Validation: |
    npm test src/middleware/auth.test.js
    npm run lint src/middleware/auth.js
```

### Example 2: Precise Configuration
```bash
/generate-prp redis-cache --template=backend

# After studying existing files, generates:
Task 2: Configure Redis connection
  Priority: high
  Dependencies: [Task 1]
  
  Consultar:
    Codebase: 
      - "config/database.js"  # Studied: uses similar pattern at line 12-28
      - "config/index.js"     # Studied: config structure at line 45
      - ".env.example"        # Studied: current vars end at line 14
    External: [Context7: "/redis/docs connection"]
  
  Files: ["config/redis.js", ".env.example"]
  
  Explicit Instructions: |
    1. Create config/redis.js following pattern from config/database.js:
       ```javascript
       // Matching require style from database.js line 1-3
       const Redis = require('ioredis');
       const logger = require('../utils/logger');
       
       // Following singleton pattern from database.js line 12
       const redisClient = new Redis({
         host: process.env.REDIS_HOST || 'localhost',
         port: process.env.REDIS_PORT || 6379,
         password: process.env.REDIS_PASSWORD,
         retryStrategy: (times) => Math.min(times * 50, 2000),
         maxRetriesPerRequest: 3
       });
       
       // Matching error handling from database.js line 22
       redisClient.on('error', (err) => {
         logger.error('Redis Client Error', err);
       });
       
       module.exports = redisClient;
       ```
    
    2. In .env.example, after line 14 (last DB config), add:
       ```
       # Redis Configuration
       REDIS_HOST=localhost
       REDIS_PORT=6379
       REDIS_PASSWORD=
       ```
  
  Validation: |
    node -e "require('./config/redis').ping().then(() => console.log('Redis connected'))"
    grep -q "REDIS_HOST" .env.example && echo "ENV vars added"
```

### Example 3: Complex Integration
```bash
/generate-prp payment-system --research-deep

# Generates tasks with hybrid approach:
Task 5: Implement Stripe webhook handler
  Priority: medium
  Dependencies: [Task 3, Task 4]
  
  Consultar:
    Codebase: ["src/webhooks/", "src/payments/"]
    External: 
      - Context7: "/stripe/docs webhooks"
      - URL: "https://stripe.com/docs/webhooks/signatures"
  
  Files: ["src/webhooks/stripe.js", "src/payments/webhook-handler.js"]
  
  SuperClaude Command: /build --feature --secure
  Additional Instructions: |
    - Verify webhook signatures using stripe.webhooks.constructEvent
    - Implement idempotency with 24-hour cache
    - Log all events to payments_webhook_log table
    - Return 200 immediately, process async
    - Handle these events: payment_intent.succeeded, payment_intent.failed
  
  Validation: |
    npm test src/webhooks/stripe.test.js
    curl -X POST http://localhost:3000/webhooks/stripe -H "stripe-signature: test"
```

## Persona Focus

| Persona | Enhances |
|---------|----------|
| `--persona-architect` | System design, scalability, patterns |
| `--persona-security` | Validation loops, auth, OWASP compliance |
| `--persona-qa` | Test coverage, edge cases, validation |
| `--persona-backend` | API design, data flow, performance |
| `--persona-frontend` | UI patterns, accessibility, UX |

## Flags

| Flag | Purpose |
|------|---------|
| `--research-deep` | Extended analysis phase |
| `--template=[type]` | Use specific template (backend/frontend/fullstack) |
| `--persona-[type]` | Apply persona focus (see table above) |
| `--validation-strict` | Include additional validation steps |

@include shared/flag-inheritance.yml#Universal_Always

---
*Generates deterministic, executable specifications for complex features*