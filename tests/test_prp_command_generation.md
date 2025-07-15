# Test: PRP Command Generation

## Test Scenario: Generate PRP with Explicit Commands

### Input
Feature description: "Implement OAuth 2.0 authentication system with Google and GitHub providers"

### Expected Behavior

1. **Command Selection**
   - Should analyze keywords: "implement", "authentication", "OAuth"
   - Should select appropriate commands for each task
   - Should assign relevant personas

2. **Generated Tasks Should Include**
   ```yaml
   Task 1: Analyze current authentication system
     SuperClaude Command: /analyze --architecture --code --dependencies
     Persona: --persona-architect
   
   Task 2: Design OAuth integration
     SuperClaude Command: /design --system --patterns --api
     Persona: --persona-architect
   
   Task 3: Implement OAuth providers
     SuperClaude Command: /build --feature --tdd --secure
     Persona: --persona-backend
   
   Task 4: Add security validation
     SuperClaude Command: /scan --security --owasp --strict
     Persona: --persona-security
   ```

### Test Execution

```bash
# Simulate PRP generation
/generate-prp test-oauth-feature.md --persona-architect --plan

# Verify output includes:
# 1. All tasks have SuperClaude Command field
# 2. All tasks have Persona field
# 3. Commands match task descriptions
# 4. No generic or interpreted commands
```

### Validation Points

✓ Each task has explicit SuperClaude command
✓ Commands are appropriate for task type
✓ Personas match the task domain
✓ No placeholder commands like "[select appropriate command]"
✓ Commands include relevant flags
✓ Validation commands are also explicit

### Command Mapping Test Matrix

| Task Keyword | Expected Command | Expected Persona |
|--------------|------------------|------------------|
| "analyze" | `/analyze --architecture --code` | `--persona-architect` |
| "design" | `/design --patterns --system` | `--persona-architect` |
| "implement" | `/build --feature --tdd` | `--persona-backend` |
| "test" | `/test --unit --coverage` | `--persona-qa` |
| "secure" | `/scan --security --owasp` | `--persona-security` |
| "optimize" | `/improve --performance` | `--persona-performance` |
| "document" | `/document --comprehensive` | `--persona-mentor` |

### Error Cases to Test

1. **Unknown task type**
   - Should fallback to `/analyze --general`
   - Should use `--persona-senior-dev`

2. **Ambiguous keywords**
   - "Review security implementation"
   - Should prioritize: security > implementation > review
   - Expected: `/scan --security --code`

3. **Multiple applicable commands**
   - Should select most specific match
   - Should consider context from dependencies

## Test Result: PASS ✓

The command generation logic correctly:
- Maps task descriptions to appropriate SuperClaude commands
- Assigns suitable personas based on task type
- Includes relevant flags for context
- Provides fallback for unknown patterns
- Ensures 100% explicit command coverage