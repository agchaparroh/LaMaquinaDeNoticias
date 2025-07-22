# Execute PRP

**Purpose**: Execute feature implementation from Product Requirements Prompt

---

@include shared/universal-constants.yml#Universal_Legend

## Command
`/execute-prp [prp-file] [--flags]`

## Process Overview
Load → Plan → Execute → Validate → Checkpoint → Repeat

### 🎯 CORE PRINCIPLE: Absolute Fidelity
The PRP is your CONTRACT. You are a faithful executor, not an improver. Every deviation, no matter how "helpful," breaks the contract and may cause cascading failures in later tasks.

## 1. Load Phase

### Load PRP File
- Read PRP from `PRPs/[feature-name].md`
- Validate structure and completeness
- Extract task list with dependencies
- Load all referenced documentation

### Verify Pre-Study
Confirm that all target files were studied during generation:
- Check line numbers are current
- Verify patterns still match
- Confirm dependencies exist

## 2. Execution Phase

### ⚠️ MANDATORY EXECUTION DISCIPLINE

**YOU MUST:**
1. **ALWAYS return to PRP file** for each task - NO exceptions
2. **NEVER combine or skip tasks** - Execute one at a time
3. **EXECUTE EXACTLY as written** - NO improvements or optimizations
4. **PRESERVE ALL CONTEXT** - Never lose track of previous changes
5. **OBEY INSTRUCTIONS LITERALLY** - If it says line 45, it means line 45

**YOU MUST NOT:**
- ❌ Add "helpful" extra features not in the task
- ❌ Refactor code unless explicitly instructed
- ❌ Skip validation steps
- ❌ Combine multiple tasks for "efficiency"
- ❌ Make assumptions about intent

### Task Execution Loop

```
STRICT LOOP:
  1. Open PRP file
  2. Find next pending task (in sequence)
  3. Read COMPLETE task definition
  4. Load Consultar resources
  5. Execute EXACTLY as specified
  6. Run ALL validations
  7. Create checkpoint
  8. Mark complete in TodoWrite
  9. GOTO step 1 (NO SHORTCUTS!)
```

### Task Processing
For each task:

1. **Update Todo Status**
   ```
   Mark task as "in_progress" in TodoWrite
   ```

2. **Review Consultar Section**
   - Load ALL files listed in Consultar.Codebase
   - Access Context7 references if needed
   - Run any Tools commands specified
   - This is MANDATORY - never skip

3. **Execute Based on Method**

#### Method 1: SuperClaude Command
```yaml
If task has "SuperClaude Command":
  - Adopt specified Persona
  - Execute command exactly as written
  - No interpretation or modification
```

#### Method 2: Explicit Instructions
```yaml
If task has "Explicit Instructions":
  - Follow each step precisely
  - Execute in exact order given
  - Use specified line numbers
  - Insert/replace code exactly as shown
```

#### Method 3: Hybrid Approach
```yaml
If task has both Command + Additional Instructions:
  - Execute SuperClaude Command first
  - Apply Additional Instructions as modifications
  - Maintain context from command execution
```

4. **Run Validation**
   ```
   Execute all commands in Validation section
   If any fail: attempt fix, re-validate
   ```

5. **Create Checkpoint**
   ```
   After EACH task completion:
   - Save current state
   - Document changes made
   - Update progress tracking
   ```

## 3. Progress Tracking

Real-time status display:
```
═══════════════════════════════════════════════════
PRP: [Feature Name]
Progress: 3/8 tasks (37.5%)
═══════════════════════════════════════════════════
✅ Task 1: Configure environment
✅ Task 2: Create base structure  
✅ Task 3: Implement core logic
⏳ Task 4: Add validation layer
□ Task 5: Create test suite
□ Task 6: Add documentation
□ Task 7: Integration tests
□ Task 8: Performance optimization

Current: Following explicit instructions in auth.py
Validation: 2/3 checks passing
═══════════════════════════════════════════════════
```

## 4. Expected Task Format

Tasks must follow the format defined in generate-prp:

```yaml
Task N: [Specific description]
  Priority: [high/medium/low]
  Dependencies: [previous tasks]
  
  Consultar:
    Codebase: [files to review before executing]
    External: [Context7 refs, URLs]
    Tools: [analysis commands]
  
  Files: [files to create/modify]
  
  # ONE of these execution methods:
  SuperClaude Command: /command --flags
  Persona: --persona-type
  
  # OR
  Explicit Instructions: |
    Step-by-step instructions
    
  # OR  
  SuperClaude Command: /command --flags
  Additional Instructions: |
    Specific modifications
  
  Validation: [executable commands]
  Expected_Output: [measurable outcome]
```

## 5. Checkpoint System

**After EVERY task** (not just milestones):
```yaml
Checkpoint-[task-N]:
  - State saved to .claudedocs/checkpoints/
  - Changes documented
  - Validation results stored
  - Ready for recovery if needed
  - Context summary for next session
```

### Checkpoint Must Include
```yaml
Task_Summary:
  - Task number and description
  - Files created: [list with paths]
  - Files modified: [list with line ranges]
  - Patterns followed: [conventions used]
  - Dependencies: [what relies on this task]
  - Next task preview: [what comes next]
```

## 6. Error Recovery

### Validation Failures
```yaml
On_Failure:
  1. Analyze error output
  2. Apply targeted fix
  3. Re-run validation
  4. If still failing: pause for user input
```

### Missing Dependencies
```yaml
On_Missing:
  1. Check if installable
  2. Update package.json/requirements
  3. Install and retry
  4. Document new dependency
```

### Context Management
```yaml
If approaching token limits:
  1. Complete current task
  2. Create DETAILED checkpoint with:
     - Summary of ALL files created/modified so far
     - Key patterns and conventions discovered
     - Dependencies between components
     - Critical decisions made
     - Validation results for each task
  
  3. Start new session with:
     - Load checkpoint summary FIRST
     - Re-open PRP file 
     - Load relevant files from recent tasks
     - Continue from EXACT task number
     - NEVER lose awareness of previous work
  
  # Context is ALWAYS critical - preserve it!
```

### Context Preservation Checklist
Before starting ANY task, verify:
- □ I know what files were created in previous tasks
- □ I understand the patterns established
- □ I have the PRP file open
- □ I'm on the correct task number
- □ I've loaded files from Consultar section
- □ I remember validation results from earlier tasks

## 7. Validation Execution

Run these checks after each task:
```bash
# Language-specific validation
npm test [specific-test-file]     # JavaScript
pytest [test-file] -v             # Python
go test ./... -v                  # Go

# Code quality
npm run lint                      # or eslint
ruff check                        # or flake8
mypy [file] --strict             # Type checking

# Integration validation  
curl -X POST localhost:3000/endpoint
docker-compose ps
```

## Flags

| Flag | Purpose |
|------|---------|
| `--checkpoint=[name]` | Resume from specific checkpoint |
| `--validation-strict` | Stop on any validation failure |
| `--parallel` | Execute independent tasks concurrently |
| `--dry-run` | Show what would be executed |

@include shared/flag-inheritance.yml#Universal_Always

## Examples

### Basic Execution
```bash
/execute-prp PRPs/user-auth.md
# Executes all tasks in sequence with checkpoints
```

### Resume from Checkpoint
```bash
/execute-prp PRPs/payment-system.md --checkpoint=task-3
# Continues from after task 3 completion
```

### Strict Validation
```bash
/execute-prp PRPs/security-update.md --validation-strict
# Stops immediately on any validation failure
```

## Success Criteria

Execution completes when:
- ✅ All tasks marked complete
- ✅ All validations passing
- ✅ Expected outputs achieved
- ✅ Success criteria from PRP checked
- ✅ Final checkpoint created

---
*Executes PRPs with precision, validation, and checkpoint recovery*