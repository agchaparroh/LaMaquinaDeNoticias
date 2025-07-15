# PRP - Product Requirements Prompt Mode

**Purpose**: Manage comprehensive feature specifications for complex multi-file implementations

---

@include shared/universal-constants.yml#Universal_Legend

## Command Execution
Execute: immediate. --plan→show plan first
Legend: Symbols from Universal Legend apply throughout
Purpose: "Manage PRPs for complex features"

PRP Mode is a selective integration of Context Engineering into SuperClaude for complex features requiring:
- Multi-file changes (≥3 files)
- Multi-system integration
- Critical business logic
- Validation loops
- Comprehensive documentation

**NEW**: PRPs now include explicit SuperClaude commands for each task, ensuring deterministic execution without interpretation.

## Operations

### /prp --init [description]
Initialize PRP mode for a feature:
- Evaluate complexity triggers
- Create directory structure if needed
- Initialize tracking state
- Return decision (proceed/redirect to simpler approach)

### /prp --generate [feature-name]
Generate comprehensive PRP:
- Research codebase patterns using existing tools
- Apply selected persona logic (--persona-* flags)
- Generate context-rich specification
- **Map each task to explicit SuperClaude command**
- Save to `PRPs/[feature-name].md`
- Integrate with task management

### /prp --execute [prp-file]
Execute PRP with validation:
- Load PRP context and requirements
- **Extract explicit SuperClaude commands from tasks**
- Create task breakdown in TodoWrite
- **Execute commands exactly as specified (no interpretation)**
- Run validation loops
- Track progress in real-time

### /prp --status
Show current PRP execution status:
- Active PRP details
- Todo progress
- Validation results
- Remaining tasks

### /prp --exit
Return to normal SuperClaude mode:
- Complete documentation
- Archive PRP state
- Generate summary report

## Integration Points

### Task Management
- PRPs integrate as Level_0 in task hierarchy
- Automatic task creation from PRPs
- Bidirectional sync with TodoWrite
- Operation: `/task:prp [task-id]` converts tasks to PRPs

### Personas
All personas enhance PRP generation:
- `--persona-architect`: System design focus
- `--persona-qa`: Validation and testing emphasis
- `--persona-senior-dev`: Best practices and patterns
- `--persona-lead-dev`: Team coordination aspects

### Universal Flags
@include shared/flag-inheritance.yml#Universal_Always

### PRP-Specific Flags
| Flag | Purpose |
|------|---------|
| `--template=[name]` | Use specific PRP template (api, frontend, fullstack) |
| `--auto-trigger` | Evaluate complexity and auto-initiate if warranted |
| `--validation-strict` | Enforce all validation loops |
| `--context-full` | Include maximum context (may use more tokens) |

## Decision Rules

### When to Use PRP Mode
| Indicator | Threshold | Action |
|-----------|-----------|--------|
| Files affected | ≥3 | Consider PRP |
| Estimated time | >30 min | Consider PRP |
| System integration | Multi-system | Recommend PRP |
| Business critical | Yes | Strongly recommend PRP |
| New feature type | Unknown pattern | Recommend PRP |

### When NOT to Use PRP Mode
- Single file changes
- Simple bug fixes
- Documentation updates
- Configuration changes
- Refactoring with clear patterns

## Examples

Initialize PRP for complex feature:
```bash
/prp --init "Implement OAuth 2.0 authentication system"
# Evaluates complexity and initializes if warranted
```

Generate PRP with architect persona:
```bash
/prp --generate oauth-auth --persona-architect --think-hard
# Researches patterns and generates comprehensive spec
```

Execute PRP with validation:
```bash
/prp --execute PRPs/oauth-auth.md --validation-strict
# Implements with validation loops and progress tracking
```

Convert existing task to PRP:
```bash
/task:prp 20250115-093045
# Evaluates task complexity and converts if appropriate
```

Check execution status:
```bash
/prp --status
# Shows current PRP, todo progress, validation state
```

## Output Locations
- PRPs: `PRPs/[feature-name].md`
- Templates: `PRPs/templates/`
- Reports: `.claudedocs/reports/prp-[timestamp].md`
- Checkpoints: `.claudedocs/checkpoints/prp-[feature]/`

## Best Practices
1. Use PRP mode only when complexity warrants it
2. Always run `/prp --init` first to evaluate need
3. Select appropriate persona for domain expertise
4. Review generated PRP before execution
5. Monitor validation loops during execution
6. Complete all validations before marking done

## Anti-Patterns
- ❌ Using PRP for simple single-file changes
- ❌ Skipping validation loops
- ❌ Ignoring persona recommendations
- ❌ Forcing PRP when direct commands suffice
- ❌ Creating PRPs without clear requirements

---
*PRP Mode - Selective Context Engineering for complex SuperClaude features*