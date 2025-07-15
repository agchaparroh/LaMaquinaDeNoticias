name: "PRP-SuperClaude Integration with Explicit Commands - Implementation Spec"
description: |

## Purpose
Implement the vision for PRP-SuperClaude integration where each generated PRP specifies explicit SuperClaude commands, and execution is absolutely faithful to the plan without autonomous decisions.

## Core Principles
1. **Especificidad Total**: Each task specifies exact SuperClaude command
2. **Obediencia Absoluta**: Execution follows plan without interpretation
3. **Determinismo**: Same PRP produces same results
4. **Trazabilidad**: Every action documented and auditable
5. **SuperClaude Integration**: Leverage all 19 commands and 9 personas

---

## Goal
Transform the PRP system to generate deterministic execution plans with explicit SuperClaude commands, and modify execution to follow these plans without deviation.

## Why
- **Business value**: Predictable, repeatable feature implementation
- **Integration**: Full utilization of SuperClaude's 19 commands and 9 personas
- **Problems solved**: 
  - Eliminates execution variability
  - Provides complete audit trail
  - Enables review before execution
  - Maximizes SuperClaude capabilities

## What
A modified PRP system where:
- Generated PRPs include explicit SuperClaude commands for each task
- Execution follows commands exactly as specified
- Personas are adopted as indicated
- No autonomous tool selection occurs

### Success Criteria
- [ ] All generated PRPs include SuperClaude commands in tasks
- [ ] Execution uses specified commands without deviation
- [ ] Personas are properly adopted during execution
- [ ] Command mapping covers all task types
- [ ] Templates updated with new format
- [ ] Documentation reflects new behavior

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- file: /home/ec2-user/projects/LaMaquinaDeNoticias/ContextEngineering/VISION_PRP_SUPERCLAUDE_INTEGRATION.md
  why: Complete vision document with examples and requirements
  
- file: /home/ec2-user/projects/LaMaquinaDeNoticias/.claude/commands/generate-prp.md
  why: Current generation logic to modify
  
- file: /home/ec2-user/projects/LaMaquinaDeNoticias/.claude/commands/execute-prp.md
  why: Current execution logic to modify
  
- file: /home/ec2-user/projects/LaMaquinaDeNoticias/.claude/commands/shared/prp-patterns.yml
  why: Patterns file to extend with command mappings
  
- file: /home/ec2-user/projects/LaMaquinaDeNoticias/PRPs/templates/prp_base.md
  why: Base template to update with command format
  
- file: /home/ec2-user/projects/LaMaquinaDeNoticias/.claude/shared/superclaude-personas.yml
  why: Persona definitions for task mapping
  
- file: /home/ec2-user/projects/LaMaquinaDeNoticias/.claude/commands/shared/universal-constants.yml
  why: Command list and patterns
```

### Current Codebase Structure
```bash
/home/ec2-user/projects/LaMaquinaDeNoticias/
├── .claude/
│   ├── commands/
│   │   ├── generate-prp.md      # Modify generation logic
│   │   ├── execute-prp.md       # Modify execution logic
│   │   └── prp.md               # Update examples
│   └── shared/
│       └── prp-patterns.yml     # Add command mappings
├── PRPs/
│   └── templates/               # Update all templates
│       ├── prp_base.md
│       ├── prp_api.md
│       ├── prp_frontend.md
│       └── prp_fullstack.md
└── docs/
    └── PRPs/README.md           # Update documentation
```

### Desired Changes
```bash
MODIFY: .claude/commands/generate-prp.md
  Changes: Add command mapping logic, include in output
  
MODIFY: .claude/commands/execute-prp.md
  Changes: Strict command execution, persona adoption
  
MODIFY: .claude/commands/shared/prp-patterns.yml
  Changes: Add Task_Command_Mapping section
  
MODIFY: PRPs/templates/*.md (all 4 templates)
  Changes: Update task format with SuperClaude commands
  
MODIFY: PRPs/README.md
  Changes: Document new command-explicit format

MODIFY: .claude/GUIA_SUPERCLAUDE.md
  Changes: Update examples with new format
```

### Known Gotchas & Requirements
```python
# CRITICAL: SuperClaude commands must be valid (19 commands)
# CRITICAL: Personas must match existing 9 personas
# CRITICAL: Maintain @include syntax compatibility
# CRITICAL: Preserve YAML frontmatter in PRPs
# CRITICAL: Task format must include: Command, Persona, Validation
# CRITICAL: No interpretation during execution
```

## Implementation Blueprint

### Command Mapping Structure
```yaml
Task_Command_Mapping:
  Analysis_Tasks:
    Default: "/analyze --architecture --code --dependencies"
    Personas: ["analyzer", "architect"]
    
  Design_Tasks:
    Default: "/design --patterns --think-hard"
    Personas: ["architect", "senior-dev"]
    
  Implementation_Tasks:
    Default: "/build --tdd --uc"
    Personas: ["backend", "frontend", "senior-dev"]
    
  Testing_Tasks:
    Default: "/test --unit --coverage"
    Personas: ["qa", "senior-dev"]
    
  Security_Tasks:
    Default: "/scan --security --owasp --strict"
    Personas: ["security"]
    
  Optimization_Tasks:
    Default: "/improve --performance --refactor"
    Personas: ["performance", "refactorer"]
    
  Documentation_Tasks:
    Default: "/document --api --examples"
    Personas: ["mentor"]
```

### Task Breakdown

```yaml
Task 1: Analyze current PRP implementation
  Priority: high
  SuperClaude Command: /analyze --architecture --code .claude/commands/*prp*.md PRPs/
  Persona: --persona-analyzer
  Purpose: Understand current implementation patterns
  Expected Output: Analysis report of PRP system architecture
  Validation: 
    - Report exists in .claudedocs/analysis/prp-system.md

Task 2: Design command mapping system
  Priority: high
  Dependencies: Task 1
  SuperClaude Command: /design --system --patterns --think-hard
  Persona: --persona-architect
  Deliverable: Design document for command mapping integration
  Files:
    - CREATE: docs/design/prp-command-mapping.md
  Validation:
    - Design covers all 19 SuperClaude commands
    - Mapping logic is deterministic

Task 3: Update prp-patterns.yml with command mappings
  Priority: high
  Dependencies: Task 2
  SuperClaude Command: /build --config --yaml --uc
  Persona: --persona-backend
  Files:
    - MODIFY: .claude/commands/shared/prp-patterns.yml
  Implementation:
    - ADD Task_Command_Mapping section
    - MAP task types to SuperClaude commands
    - INCLUDE persona assignments
  Validation:
    - YAML syntax valid
    - All task types covered

Task 4: Modify generate-prp.md command logic
  Priority: high
  Dependencies: Task 3
  SuperClaude Command: /build --feature --command-generation --tdd
  Persona: --persona-senior-dev
  Files:
    - MODIFY: .claude/commands/generate-prp.md
  Changes:
    - ADD command selection logic
    - INCLUDE persona mapping
    - UPDATE output format
  Validation:
    - Generated PRPs include commands
    - Commands are valid SuperClaude commands

Task 5: Modify execute-prp.md for strict execution
  Priority: high
  Dependencies: Task 4
  SuperClaude Command: /build --feature --execution-engine --strict
  Persona: --persona-backend
  Files:
    - MODIFY: .claude/commands/execute-prp.md
  Changes:
    - REMOVE autonomous decision logic
    - ADD strict command execution
    - IMPLEMENT persona adoption
  Validation:
    - Execution follows commands exactly
    - No tool selection occurs

Task 6: Update base template with command format
  Priority: high
  Dependencies: Task 5
  SuperClaude Command: /build --template --update --uc
  Persona: --persona-senior-dev
  Files:
    - MODIFY: PRPs/templates/prp_base.md
  Changes:
    - UPDATE task format
    - ADD SuperClaude Command field
    - ADD Persona field
  Validation:
    - Template includes command examples
    - Format is clear and consistent

Task 7: Update specialized templates
  Priority: medium
  Dependencies: Task 6
  SuperClaude Command: /build --templates --batch --uc
  Persona: --persona-senior-dev
  Files:
    - MODIFY: PRPs/templates/prp_api.md
    - MODIFY: PRPs/templates/prp_frontend.md
    - MODIFY: PRPs/templates/prp_fullstack.md
  Pattern: Apply same format as base template
  Validation:
    - All templates updated consistently
    - Domain-specific commands included

Task 8: Test command generation logic
  Priority: high
  Dependencies: Task 7
  SuperClaude Command: /test --unit --integration --strict
  Persona: --persona-qa
  Test Cases:
    - Generate PRP with various features
    - Verify command inclusion
    - Check persona assignment
  Validation:
    - All test cases pass
    - Commands are appropriate

Task 9: Test execution compliance
  Priority: high
  Dependencies: Task 8
  SuperClaude Command: /test --integration --execution --strict
  Persona: --persona-qa
  Test Scenarios:
    - Execute sample PRP
    - Verify exact command usage
    - Confirm no deviation
  Validation:
    - Execution matches plan exactly
    - Personas adopted correctly

Task 10: Security and quality review
  Priority: high
  Dependencies: Task 9
  SuperClaude Command: /scan --security --quality --strict
  Persona: --persona-security
  Focus:
    - Command injection risks
    - Execution safety
    - Error handling
  Validation:
    - No security vulnerabilities
    - Proper error handling

Task 11: Update documentation
  Priority: medium
  Dependencies: Task 10
  SuperClaude Command: /document --update --comprehensive --examples
  Persona: --persona-mentor
  Files:
    - MODIFY: PRPs/README.md
    - MODIFY: .claude/GUIA_SUPERCLAUDE.md
  Include:
    - New PRP format examples
    - Command mapping explanation
    - Execution behavior
  Validation:
    - Documentation is complete
    - Examples are accurate

Task 12: Create migration guide
  Priority: low
  Dependencies: Task 11
  SuperClaude Command: /document --guide --migration
  Persona: --persona-mentor
  Files:
    - CREATE: docs/guides/prp-explicit-commands-migration.md
  Content:
    - Changes from old format
    - Migration steps
    - Benefits explanation
  Validation:
    - Guide is clear and actionable
```

### Pseudocode & Patterns

```python
# For Task 4: Command mapping in generate-prp
def map_task_to_command(task_type, context):
    """Map task type to specific SuperClaude command"""
    mapping = load_yaml('.claude/commands/shared/prp-patterns.yml')
    command_map = mapping['Task_Command_Mapping']
    
    # Determine task category
    if 'analyze' in task_type.lower():
        base_command = command_map['Analysis_Tasks']['Default']
        personas = command_map['Analysis_Tasks']['Personas']
    elif 'design' in task_type.lower():
        base_command = command_map['Design_Tasks']['Default']
        personas = command_map['Design_Tasks']['Personas']
    # ... more mappings
    
    # Select appropriate persona
    persona = select_best_persona(personas, context)
    
    return {
        'command': base_command,
        'persona': f'--persona-{persona}'
    }

# For Task 5: Strict execution in execute-prp
async def execute_task_with_command(task):
    """Execute exactly the command specified in task"""
    # NO interpretation or tool selection
    command = task['SuperClaude Command']
    persona = task['Persona']
    
    # Execute EXACTLY as specified
    result = await execute_superclaude_command(command, persona)
    
    # Run specified validations
    for validation in task['Validation']:
        validate_result(validation)
    
    return result
```

### Integration Points
```yaml
CONFIGURATION:
  - No new dependencies needed
  - Reuse existing SuperClaude infrastructure
  
COMMANDS:
  - All 19 SuperClaude commands available
  - All 9 personas integrated
  - Universal flags preserved
  
VALIDATION:
  - Command validity checking
  - Persona existence verification
  - Execution compliance tracking
```

## Validation Loop

### Level 1: Syntax & Structure
```bash
# Verify YAML syntax
python -c "import yaml; yaml.safe_load(open('.claude/commands/shared/prp-patterns.yml'))"

# Check command format
grep -E "SuperClaude Command:" PRPs/templates/*.md

# Validate persona references
grep -E "Persona:" PRPs/templates/*.md

# Expected: All files have correct format
```

### Level 2: Command Generation Tests
```python
# Test command mapping
def test_task_command_mapping():
    """Verify tasks map to appropriate commands"""
    test_cases = [
        ("Analyze existing auth", "/analyze", "analyzer"),
        ("Design new API", "/design", "architect"),
        ("Implement feature", "/build", "backend"),
        ("Write tests", "/test", "qa"),
        ("Security audit", "/scan", "security")
    ]
    
    for task, expected_cmd, expected_persona in test_cases:
        result = map_task_to_command(task, {})
        assert expected_cmd in result['command']
        assert expected_persona in result['persona']

# Test PRP generation includes commands
def test_prp_generation_with_commands():
    """Verify generated PRPs include SuperClaude commands"""
    prp = generate_prp("OAuth authentication", {"persona": "architect"})
    
    # Parse PRP content
    tasks = parse_prp_tasks(prp)
    
    for task in tasks:
        assert 'SuperClaude Command' in task
        assert 'Persona' in task
        assert task['SuperClaude Command'].startswith('/')
```

### Level 3: Execution Compliance Tests
```python
# Test strict execution
def test_strict_command_execution():
    """Verify execution follows commands exactly"""
    test_prp = """
    Task 1: Test task
      SuperClaude Command: /analyze --code src/
      Persona: --persona-analyzer
    """
    
    # Mock execution
    with patch('execute_superclaude_command') as mock_exec:
        execute_prp(test_prp)
        
        # Verify exact command was used
        mock_exec.assert_called_with('/analyze --code src/', '--persona-analyzer')
        
        # Verify no other commands were called
        assert mock_exec.call_count == 1
```

### Level 4: Integration Test
```bash
# Generate a PRP with new system
/generate-prp test-feature.md --persona-architect

# Verify commands in output
grep "SuperClaude Command:" PRPs/test-feature.md

# Execute and verify compliance
/execute-prp PRPs/test-feature.md --dry-run

# Expected: Shows exact commands that would be executed
```

## Final Validation Checklist
- [ ] All task types map to SuperClaude commands
- [ ] Generated PRPs include explicit commands
- [ ] Execution follows commands without deviation
- [ ] Personas are properly adopted
- [ ] All 19 commands are covered in mappings
- [ ] All 9 personas are utilized appropriately
- [ ] Templates updated with new format
- [ ] Documentation reflects changes
- [ ] No autonomous tool selection occurs
- [ ] Execution is fully deterministic

---

## Anti-Patterns to Avoid
- ❌ Don't allow execution to choose tools
- ❌ Don't generate PRPs without commands
- ❌ Don't ignore specified personas
- ❌ Don't add commands not in SuperClaude
- ❌ Don't break existing PRP functionality
- ❌ Don't make execution less reliable

## Confidence Score: 9/10

High confidence due to:
- Clear vision document as guide
- Existing SuperClaude infrastructure to leverage
- Well-defined command set (19 commands)
- Established persona system (9 personas)
- Straightforward mapping logic

Minor uncertainty only on edge cases in command selection for complex tasks.