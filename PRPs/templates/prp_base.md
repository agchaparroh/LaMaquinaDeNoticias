name: "[Feature Name] - SuperClaude Context-Rich Implementation Spec"
description: |

## Purpose
[Brief description of what this PRP accomplishes, following SuperClaude evidence-based language standards]

## Core Principles
1. **Context is King**: Include ALL necessary documentation, examples, and caveats
2. **Validation Loops**: Provide executable tests/lints the AI can run and fix
3. **Information Dense**: Use keywords and patterns from the codebase
4. **Progressive Success**: Start simple, validate, then enhance
5. **SuperClaude Integration**: Leverage existing commands and patterns
6. **Explicit Commands**: Every task specifies exact SuperClaude command to execute

---

## Goal
[What needs to be built - be specific about the end state]

## Why
- **Business value**: [Impact on users and stakeholders]
- **Integration**: [How it fits with existing features]
- **Problems solved**: [Specific issues addressed]

## What
[User-visible behavior and technical requirements]

### Success Criteria
- [ ] [Specific measurable outcome 1]
- [ ] [Specific measurable outcome 2]
- [ ] [Specific measurable outcome 3]

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- file: [path/to/relevant/file.py]
  why: [Specific patterns to follow or gotchas to avoid]
  
- url: [API documentation URL]
  why: [Specific sections/methods needed]
  
- file: .claude/CLAUDE.md
  why: Project-specific instructions and conventions
  
- doc: [Library documentation URL]
  section: [Specific section about implementation]
  critical: [Key insight that prevents common errors]
```

### Current Codebase Structure
```bash
# Output of 'tree -L 3' or relevant structure
[Project structure relevant to this feature]
```

### Desired Changes
```bash
# Files to be created/modified
CREATE: [new/file/path.py]
  Purpose: [What this file does]
  
MODIFY: [existing/file.py]
  Changes: [What needs to be changed]
  
INTEGRATE: [integration/points.py]
  How: [Integration approach]
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: [Library/framework name] requires [specific setup]
# Example: FastAPI endpoints must be async for WebSocket support
# Example: This ORM batch operations limited to 1000 records
# CRITICAL: Follow SuperClaude patterns from shared/*.yml
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

Full mapping: @include shared/prp-patterns.yml#Task_Command_Mapping

### Data Models & Structure
```python
# Core data models ensuring type safety
# Examples:
#   - Pydantic models for validation
#   - ORM models for persistence
#   - Type hints throughout
```

### Task Breakdown
```yaml
# Each task MUST specify explicit SuperClaude command and persona
# Format follows @include shared/prp-patterns.yml#Task_Format_With_Commands

Task 1: [Setup and Prerequisites]
  Priority: high
  Dependencies: []
  SuperClaude Command: /build --init --config --uc
  Persona: --persona-senior-dev
  Files: [files to create/modify]
  Pattern: Follow existing [pattern] from [file]
  Validation: /test --lint --type-check
  Expected_Output: Configuration files created and validated

Task 2: [Core Implementation]
  Priority: high
  Dependencies: [Task 1]
  SuperClaude Command: /build --feature --tdd --uc
  Persona: --persona-backend
  Implementation:
    - FIND pattern in [existing/file.py]
    - ADAPT for [new requirement]
    - PRESERVE [critical behavior]
  Validation: /test --unit --coverage
  Expected_Output: Core functionality implemented with tests
  
Task 3: [Integration & Testing]
  Priority: medium
  Dependencies: [Task 1, Task 2]
  SuperClaude Command: /test --integration --e2e
  Persona: --persona-qa
  Validation Commands:
    - /test --integration
    - /test --e2e
    - /scan --security
  Expected_Output: All integration tests passing

[Additional tasks as needed with explicit commands...]
```

### Pseudocode & Patterns
```python
# Task 1: Setup pattern
async def setup_feature():
    # PATTERN: Configuration loading (see src/config.py)
    config = load_config()
    validate_config(config)  # raises on invalid
    
    # PATTERN: Database setup (see src/db/init.py)
    await setup_database_tables()
    
    return config

# Task 2: Core implementation
@retry(attempts=3, backoff=exponential)
async def core_feature(input_data: FeatureInput) -> FeatureOutput:
    # PATTERN: Input validation first (see src/validators/)
    validated = validate_input(input_data)
    
    # GOTCHA: Rate limiting required
    async with rate_limiter:
        result = await process_feature(validated)
    
    # PATTERN: Standardized response (see src/responses.py)
    return format_response(result)
```

### Integration Points
```yaml
DATABASE:
  - Migration: "Add tables/columns for feature"
  - Indexes: "CREATE INDEX idx_feature ON table(column)"
  
API:
  - Routes: "Add to src/api/routes.py"
  - Middleware: "Update auth/validation middleware"
  
CONFIGURATION:
  - Environment: "Add FEATURE_* variables"
  - Settings: "Update settings.py with defaults"
  
MONITORING:
  - Logs: "Add structured logging for feature"
  - Metrics: "Track usage and performance"
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
make lint           # or: ruff check src/ --fix
make format         # or: black src/
make typecheck      # or: mypy src/

# Expected: No errors. If errors, fix before continuing.
```

### Level 2: Unit Tests
```python
# Test cases to implement
def test_feature_happy_path():
    """Basic functionality works as expected"""
    result = feature_function("valid_input")
    assert result.status == "success"
    assert result.data is not None

def test_feature_validation():
    """Invalid input handled gracefully"""
    with pytest.raises(ValidationError):
        feature_function("invalid_input")

def test_feature_edge_cases():
    """Handles edge cases properly"""
    # Test empty input, max size, special chars, etc.
```

### Level 3: Integration Tests
```bash
# Start services
docker-compose up -d

# Run integration tests
make test-integration

# Manual verification
curl -X POST http://localhost:8000/api/feature \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'

# Expected: {"status": "success", "data": {...}}
```

## Final Validation Checklist
- [ ] All syntax checks pass
- [ ] Type checking passes
- [ ] Unit tests pass with >80% coverage
- [ ] Integration tests pass
- [ ] Manual testing successful
- [ ] Documentation updated
- [ ] SuperClaude patterns followed
- [ ] No security vulnerabilities introduced

---

## Anti-Patterns to Avoid
- ❌ Don't create new patterns when existing ones work
- ❌ Don't skip validation because "it should work"
- ❌ Don't ignore SuperClaude conventions
- ❌ Don't hardcode values that should be configurable
- ❌ Don't catch all exceptions - be specific
- ❌ Don't bypass existing authentication/authorization

## Confidence Score: [X]/10

Rationale:
- Context completeness: [assessment]
- Pattern clarity: [assessment]
- Validation coverage: [assessment]
- Risk factors: [any concerns]

Target: 8+/10 for successful one-pass implementation.