# PRP Explicit Commands Documentation

## Overview

The PRP (Product Requirements Prompt) system now features **explicit command mapping**, ensuring every task in a PRP specifies exactly which SuperClaude command to execute. This creates deterministic, reproducible execution plans that leverage all 19 SuperClaude commands and 9 cognitive personas.

## Key Features

### 1. Explicit Command Specification
Every task in a PRP now includes:
```yaml
Task N: [Clear task description]
  Priority: high|medium|low
  Dependencies: [Task M, Task L]
  SuperClaude Command: /[command] --[flags] [arguments]
  Persona: --persona-[type]
  Validation: /[validation-command] --[flags]
  Expected_Output: [What this task produces]
```

### 2. Automatic Command Mapping
The system analyzes task descriptions and automatically selects:
- Appropriate SuperClaude command
- Relevant flags based on context
- Suitable persona for the domain

### 3. Strict Execution Mode
PRPs execute in strict mode by default:
- Commands executed exactly as specified
- No interpretation or tool selection
- Personas adopted before execution
- Validation commands run automatically

## Command Mapping Reference

### Task Categories → Commands

| Category | Keywords | Primary Command | Default Persona |
|----------|----------|-----------------|-----------------|
| Analysis | analyze, investigate, examine | `/analyze` | analyzer/architect |
| Design | design, architect, plan | `/design` | architect |
| Implementation | implement, build, create | `/build` | senior-dev/backend |
| Testing | test, verify, validate | `/test` | qa |
| Security | secure, audit, scan | `/scan` | security |
| Optimization | optimize, improve, refactor | `/improve` | performance |
| Documentation | document, describe, explain | `/document` | mentor |
| Review | review, inspect, assess | `/review` | senior-dev |

### Context-Aware Flag Selection

The system selects flags based on:
- Task description keywords
- File types mentioned
- Dependencies context
- Previous task patterns

Example mappings:
- "analyze system architecture" → `--architecture --dependencies`
- "implement API endpoint" → `--api --feature --tdd`
- "optimize database queries" → `--performance --metrics`

## Usage Guide

### 1. Generating PRPs with Explicit Commands

```bash
/generate-prp feature-description.md --persona-architect
```

The generated PRP will include:
- Tasks with explicit SuperClaude commands
- Appropriate personas for each task
- Validation commands
- No generic placeholders

### 2. Executing PRPs

```bash
/execute-prp PRPs/feature-name.md
```

Execution behavior:
1. Loads PRP and detects explicit commands
2. For each task:
   - Extracts SuperClaude command
   - Adopts specified persona
   - Executes command exactly
   - Runs validation if specified
3. No tool selection or interpretation

### 3. Template Usage

All PRP templates updated with:
- Command selection guide
- Example task formats
- Explicit command requirements

## Migration Guide

### For Existing PRPs

Existing PRPs without explicit commands still work:
- System detects missing commands
- Falls back to legacy interpretation mode
- Logs deprecation warning
- Continues execution

### Updating Old PRPs

To update a legacy PRP:
1. Add `SuperClaude Command:` to each task
2. Add `Persona:` specification
3. Use command mapping reference
4. Test with `/execute-prp --dry-run`

## Benefits

1. **Deterministic Execution**
   - Same PRP always executes identically
   - No variance from interpretation
   - Reproducible results

2. **Full SuperClaude Utilization**
   - All 19 commands actively used
   - All 9 personas engaged
   - Maximum framework leverage

3. **Clear Intent**
   - Explicit commands show exact execution
   - No ambiguity in implementation
   - Better planning visibility

4. **Enhanced Control**
   - Precise command specification
   - Exact flag control
   - Validation automation

## Examples

### Simple Task
```yaml
Task 1: Analyze authentication system
  Priority: high
  Dependencies: []
  SuperClaude Command: /analyze --architecture --code
  Persona: --persona-architect
  Expected_Output: Architecture analysis report
```

### Complex Task
```yaml
Task 5: Implement OAuth providers
  Priority: high
  Dependencies: [Task 2, Task 3]
  SuperClaude Command: /build --feature --tdd --secure --uc
  Persona: --persona-backend
  Files:
    - CREATE src/auth/providers/google.py
    - CREATE src/auth/providers/github.py
  Validation: /test --unit --coverage
  Expected_Output: OAuth provider implementations with tests
```

## Command Reference

See `/home/ec2-user/projects/LaMaquinaDeNoticias/.claude/commands/index.md` for complete command list.

Key commands for PRPs:
- `/analyze` - Architecture and code analysis
- `/design` - System design and patterns
- `/build` - Implementation and features
- `/test` - Testing and validation
- `/scan` - Security and quality scanning
- `/improve` - Performance optimization
- `/document` - Documentation generation

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Unknown command in PRP" | Check command against SuperClaude's 19 commands |
| "Invalid persona" | Use one of 9 valid personas |
| "Command failed" | Check flags are valid for command |
| "No command specified" | Add explicit SuperClaude Command to task |

## Best Practices

1. **Use Specific Commands**
   - Match command to task intent
   - Include relevant flags
   - Specify validation commands

2. **Appropriate Personas**
   - Match persona to domain
   - Use specialized personas
   - Leverage persona strengths

3. **Clear Task Descriptions**
   - Include keywords for mapping
   - Specify expected outcomes
   - Define validation criteria

4. **Validation Coverage**
   - Include validation commands
   - Test after implementation
   - Automate quality checks

---

*PRP Explicit Commands - Deterministic execution with full SuperClaude integration*