# Migration Guide: PRP Explicit Commands

## Overview

This guide helps you migrate existing PRPs to the new explicit command format, ensuring deterministic execution with full SuperClaude integration.

## What's Changed

### Before (Legacy PRPs)
```yaml
Task 1: Implement user authentication
  Priority: high
  Files: [src/auth/*, tests/auth/*]
  Validation: Run unit tests and check coverage
```

### After (Explicit Commands)
```yaml
Task 1: Implement user authentication
  Priority: high
  Dependencies: []
  SuperClaude Command: /build --feature --tdd --secure
  Persona: --persona-backend
  Files: [src/auth/*, tests/auth/*]
  Validation: /test --unit --coverage
  Expected_Output: Authentication system with tests
```

## Migration Steps

### Step 1: Identify Legacy PRPs

Find PRPs without explicit commands:
```bash
# Look for PRPs without "SuperClaude Command"
grep -L "SuperClaude Command:" PRPs/*.md
```

### Step 2: Analyze Task Types

For each task in your PRP, identify the primary action:

| Task Contains | Primary Action | Suggested Command |
|---------------|----------------|-------------------|
| "analyze", "investigate" | Analysis | `/analyze` |
| "design", "architect" | Design | `/design` |
| "implement", "build" | Implementation | `/build` |
| "test", "verify" | Testing | `/test` |
| "secure", "audit" | Security | `/scan` |
| "optimize", "improve" | Optimization | `/improve` |
| "document", "describe" | Documentation | `/document` |

### Step 3: Add Commands to Tasks

For each task, add:

1. **SuperClaude Command**
   ```yaml
   SuperClaude Command: /[command] --[flags]
   ```

2. **Persona**
   ```yaml
   Persona: --persona-[type]
   ```

3. **Validation** (if applicable)
   ```yaml
   Validation: /[command] --[flags]
   ```

### Step 4: Select Appropriate Flags

Common flag patterns:

| Task Type | Common Flags |
|-----------|--------------|
| API Implementation | `--api --feature --tdd` |
| Frontend Component | `--react --feature --magic` |
| Security Audit | `--security --owasp --strict` |
| Performance Work | `--performance --metrics` |
| Architecture | `--architecture --patterns` |

### Step 5: Validate Migration

Test your migrated PRP:
```bash
# Dry run to check parsing
/execute-prp PRPs/your-prp.md --dry-run

# Check all tasks have commands
grep -c "SuperClaude Command:" PRPs/your-prp.md
```

## Quick Reference

### Command Mapping Cheat Sheet

```yaml
# Analysis Tasks
"Analyze system architecture" → /analyze --architecture --dependencies
"Review code quality" → /review --quality --evidence
"Investigate performance" → /analyze --performance --metrics

# Design Tasks
"Design API structure" → /design --api --patterns
"Plan database schema" → /design --ddd --patterns
"Architect microservices" → /design --architecture --system

# Implementation Tasks
"Implement REST API" → /build --api --feature --tdd
"Create React component" → /build --react --feature --magic
"Setup configuration" → /build --config --yaml

# Testing Tasks
"Write unit tests" → /test --unit --coverage
"Add integration tests" → /test --integration --e2e
"Performance testing" → /test --performance --load

# Security Tasks
"Security audit" → /scan --security --owasp
"Vulnerability scan" → /scan --vulnerabilities --strict
"Penetration testing" → /scan --security --penetration
```

### Persona Selection Guide

```yaml
Architecture Tasks → --persona-architect
Backend Development → --persona-backend
Frontend Development → --persona-frontend
Testing & QA → --persona-qa
Security Tasks → --persona-security
Performance → --persona-performance
Documentation → --persona-mentor
General Development → --persona-senior-dev
```

## Example Migration

### Original Task
```yaml
Task 3: Add user authentication endpoints
  Priority: high
  Dependencies: [Task 1, Task 2]
  Description: |
    Create REST endpoints for login, logout, and token refresh.
    Include proper validation and error handling.
  Validation: Test all endpoints and check auth
```

### Migrated Task
```yaml
Task 3: Add user authentication endpoints
  Priority: high
  Dependencies: [Task 1, Task 2]
  SuperClaude Command: /build --api --feature --secure --tdd
  Persona: --persona-backend
  Description: |
    Create REST endpoints for login, logout, and token refresh.
    Include proper validation and error handling.
  Files:
    - CREATE src/api/routes/auth.py
    - UPDATE src/api/routes/__init__.py
  Validation: /test --integration --api --auth
  Expected_Output: Authentication endpoints with tests
```

## Automated Migration Script

For bulk migration, use this pattern:
```python
# Pseudo-code for migration
def migrate_task(task):
    # Extract task description
    description = task.get('description', '')
    
    # Determine command based on keywords
    command = map_description_to_command(description)
    
    # Determine persona based on domain
    persona = map_domain_to_persona(task)
    
    # Add explicit fields
    task['SuperClaude Command'] = command
    task['Persona'] = persona
    
    # Convert validation to command
    if 'Validation' in task:
        task['Validation'] = map_validation_to_command(task['Validation'])
    
    return task
```

## Backward Compatibility

### Legacy Mode
PRPs without explicit commands still work:
- System detects missing commands
- Falls back to interpretation mode
- Logs warning about deprecated format
- Execution continues normally

### Gradual Migration
You can migrate PRPs incrementally:
1. Start with critical PRPs
2. Migrate as you update PRPs
3. New PRPs use explicit format automatically

## Verification Checklist

After migration, verify:

- [ ] All tasks have `SuperClaude Command:` field
- [ ] All tasks have `Persona:` field
- [ ] Commands are from SuperClaude's 19 commands
- [ ] Personas are from SuperClaude's 9 personas
- [ ] Validation uses SuperClaude commands
- [ ] No placeholder commands remain
- [ ] PRP executes successfully

## Common Pitfalls

### 1. Generic Commands
❌ Wrong:
```yaml
SuperClaude Command: /execute task
```

✅ Correct:
```yaml
SuperClaude Command: /build --feature --tdd
```

### 2. Missing Flags
❌ Wrong:
```yaml
SuperClaude Command: /test
```

✅ Correct:
```yaml
SuperClaude Command: /test --unit --coverage
```

### 3. Invalid Personas
❌ Wrong:
```yaml
Persona: --persona-developer
```

✅ Correct:
```yaml
Persona: --persona-senior-dev
```

## Support

If you encounter issues:
1. Check command syntax against `/home/ec2-user/projects/LaMaquinaDeNoticias/.claude/commands/index.md`
2. Verify persona names
3. Test with `--dry-run`
4. Review examples in templates

## Summary

Migration benefits:
- Deterministic execution
- No interpretation variance
- Full SuperClaude utilization
- Clear execution intent
- Better debugging

Start with one PRP, verify it works, then migrate others as needed.

---

*Migration Guide v1.0 - Upgrade PRPs for explicit command execution*