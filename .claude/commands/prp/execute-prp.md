# Execute PRP

**Purpose**: Implement feature using comprehensive Product Requirements Prompt

---

@include shared/universal-constants.yml#Universal_Legend

## Command Execution
Execute: immediate. --plan→show execution strategy
Legend: Load→Plan→Execute→Validate→Complete
Purpose: "Execute PRP with validation loops and progress tracking"

## PRP File: $ARGUMENTS

Execute a Product Requirements Prompt with integrated validation, progress tracking, and recovery mechanisms.

## Execution Modes

### Strict Command Mode (Default)
When PRP contains explicit SuperClaude commands:
- Execute EXACTLY as specified in task
- No autonomous tool selection
- No command interpretation
- Persona adoption before execution
- Validation commands run as specified

### Legacy Mode (Fallback)
For older PRPs without explicit commands:
- AI interprets task and selects tools
- Flexible execution based on context
- Best-effort command selection
- Standard validation patterns

## Execution Process

### 1. Load PRP
- Read specified PRP file from `PRPs/` directory
- Parse YAML frontmatter and markdown content
- Validate PRP completeness and structure
- Load all referenced context and documentation
- Identify required tools and dependencies

### 2. Planning Phase
- Analyze task breakdown from PRP
- Create execution sequence with dependencies
- Generate todos using TodoWrite
- Set up validation checkpoints
- Establish recovery points

### 3. Implementation
Execute tasks in sequence with:
- Extract explicit SuperClaude command from task
- Adopt specified persona before execution
- Execute command exactly as specified
- Real-time progress tracking via todos
- Checkpoint creation at milestones
- Validation after each component
- Error recovery with context preservation
- Continuous status updates

#### Command Extraction & Execution
```python
# Extract and execute explicit commands
def execute_task(task):
    # Extract command and persona from task
    command = task.get('SuperClaude Command')
    persona = task.get('Persona')
    
    # Adopt persona if specified
    if persona:
        adopt_persona(persona)
    
    # Execute command exactly as specified
    # NO interpretation or tool selection
    execute_command(command)
    
    # Run validation if specified
    if task.get('Validation'):
        execute_command(task['Validation'])
```

### 4. Validation Loops
Run validation at each checkpoint:
```yaml
Validation_Sequence:
  Syntax: "Lint and format checks"
  Types: "Type checking and compilation"
  Unit: "Component-level tests"
  Integration: "System-level tests"
  Manual: "User-facing verification"
```

### 5. Completion
- Verify all success criteria met
- Generate completion report
- Update task management system
- Archive PRP execution state
- Document lessons learned

## Integration Features

### TodoWrite Integration
Automatic todo management with command tracking:
```python
# Parse PRP tasks into todos with commands
for task in prp.tasks:
    todo = {
        "id": f"prp-{prp.id}-task-{task.number}",
        "content": f"{task.description} - {task.superclaude_command}",
        "status": "pending",
        "priority": task.priority,
        "metadata": {
            "command": task.superclaude_command,
            "persona": task.persona,
            "validation": task.validation
        }
    }
    TodoWrite.add(todo)

# Execute with strict command following
on_task_start:
    todo = TodoWrite.get(todo_id)
    execute_explicit_command(todo.metadata.command, todo.metadata.persona)
    
# Track progress in real-time
on_task_complete:
    TodoWrite.update(todo_id, status="completed")
    update_prp_progress()
```

### Checkpoint System
Save progress at key milestones:
```yaml
Checkpoints:
  After_Setup: "Environment configured"
  After_Core: "Core functionality implemented"
  After_Tests: "Tests passing"
  After_Validation: "All validations complete"
```

### Recovery Mechanisms
Handle failures gracefully:
```yaml
On_Validation_Failure:
  - Analyze error output
  - Apply fixes using available tools
  - Re-run validation
  - Continue if fixed, escalate if blocked

On_Context_Overflow:
  - Save checkpoint
  - Compress context using --uc
  - Resume from checkpoint

On_Missing_Dependency:
  - Document requirement
  - Attempt installation
  - Update PRP if needed
```

## Expected Task Format

Tasks in PRPs should follow this format for strict execution:
```yaml
Task 1: Analyze current authentication system
  Priority: high
  Dependencies: []
  SuperClaude Command: /analyze --architecture --code --dependencies
  Persona: --persona-architect
  Files: ["src/auth/*", "src/middleware/auth.js"]
  Validation: /test --unit --coverage src/auth
  Expected_Output: Architecture analysis report
```

@include shared/prp-patterns.yml#Task_Format_With_Commands

## Progress Tracking

Real-time status updates with commands:
```
═══════════════════════════════════════════════════
PRP: OAuth Authentication Implementation
Status: In Progress (65%)
═══════════════════════════════════════════════════
✅ Task 1: Set up OAuth provider configuration
   Command: /build --config --yaml
   Persona: --persona-backend
   
✅ Task 2: Implement authorization endpoint  
   Command: /build --feature --tdd --uc
   Persona: --persona-backend
   
⏳ Task 3: Create token management system
   Command: /build --feature --secure
   Persona: --persona-security
   
□ Task 4: Add refresh token logic
□ Task 5: Implement user profile sync

Validation Status:
✅ Syntax checks passing (/test --lint)
✅ Type checks passing (/test --type-check)
⏳ Unit tests (8/12 passing) (/test --unit --coverage)
□ Integration tests pending
═══════════════════════════════════════════════════
```

## Validation Patterns

@include shared/prp-patterns.yml#Validation_Patterns

### Validation Commands
Execute these at checkpoints:
```bash
# Syntax validation
make lint || npm run lint || ruff check --fix

# Type checking  
make typecheck || npm run typecheck || mypy .

# Unit tests
make test || npm test || pytest tests/unit -v

# Integration tests
make test-integration || npm run test:e2e

# Coverage check
make coverage || npm run test:coverage
```

@include shared/flag-inheritance.yml#Universal_Always

### Execution-Specific Flags
| Flag | Purpose |
|------|---------|
| `--checkpoint=[name]` | Resume from specific checkpoint |
| `--validation-level=[level]` | Set validation strictness |
| `--parallel` | Execute independent tasks in parallel |
| `--interactive` | Pause for user confirmation at milestones |

## Examples

Execute PRP with standard validation:
```bash
/execute-prp PRPs/oauth-auth.md
# Implements with progress tracking and validation
```

Resume from checkpoint:
```bash
/execute-prp PRPs/payment-integration.md --checkpoint=After_Core
# Resumes execution after core implementation
```

Execute with strict validation:
```bash
/execute-prp PRPs/security-audit.md --validation-level=strict
# Enforces all validation loops including manual checks
```

Interactive execution:
```bash
/execute-prp PRPs/database-migration.md --interactive
# Pauses for confirmation at each major milestone
```

## Output Locations
- Progress: Real-time in console
- Checkpoints: `.claudedocs/checkpoints/prp-[feature]/`
- Reports: `.claudedocs/reports/prp-execution-[timestamp].md`
- Logs: `.claudedocs/logs/prp-[feature].log`

## Error Handling

Common issues and solutions:

| Issue | Solution |
|-------|----------|
| Validation failure | Auto-fix with tools, re-run |
| Missing context | Load additional files, update PRP |
| Test failures | Debug with error output, fix, retry |
| Dependency issues | Install requirements, update configs |
| Context overflow | Compress, checkpoint, continue |

## Success Criteria
Execution completes when:
- All PRP tasks marked complete
- All validations passing
- Success criteria checkboxes checked
- No blocking errors remain
- Completion report generated

---
*Execute PRP - Comprehensive implementation with validation and tracking*