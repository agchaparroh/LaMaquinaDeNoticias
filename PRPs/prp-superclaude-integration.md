name: "PRP Integration in SuperClaude - Selective Context Engineering Mode"
description: |

## Purpose
Integrate Context Engineering's PRP (Product Requirements Prompt) system into SuperClaude v2.0.1 as an optional "PRP Mode" for complex features, while preserving SuperClaude's simplicity for everyday tasks. This creates a hybrid approach leveraging the best of both frameworks.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, examples, and caveats
2. **Validation Loops**: Provide executable tests/lints the AI can run and fix
3. **Information Dense**: Use keywords and patterns from the codebase
4. **Progressive Success**: Start simple, validate, then enhance
5. **KISS/YAGNI**: Only activate PRP complexity when it adds real value

---

## Goal
Create a seamless integration where:
- SuperClaude commands remain primary for 80% of tasks (< 30 min, < 3 files)
- PRP Mode activates for complex features (multi-file, multi-system, critical)
- Existing SuperClaude components (personas, flags, optimization) enhance PRPs
- Single coherent interface without duplication or confusion
- Automatic triggers guide users to appropriate mode

## Why
- **Business value**: Faster development of complex features with higher success rate
- **Integration**: Combines SuperClaude's speed with Context Engineering's thoroughness
- **Problems solved**: 
  - Reduces AI context failures on complex projects
  - Maintains rapid iteration for simple tasks
  - Provides validation loops for critical features
  - Creates traceable documentation for large changes

## What
A new `/prp` command suite integrated into SuperClaude that:
- Provides suboperations: init, generate, execute, status, exit
- Integrates with existing task management system
- Leverages personas for specialized PRP generation
- Uses compression flags for token optimization
- Syncs with TodoWrite for real-time tracking
- Generates documentation upon completion

### Success Criteria
- [ ] `/prp` command works with all SuperClaude universal flags
- [ ] PRPs integrate seamlessly with `/task` management system
- [ ] Personas enhance PRP generation quality
- [ ] Token optimization works on large PRPs
- [ ] Clear decision rules prevent mode confusion
- [ ] Existing SuperClaude workflows remain unchanged
- [ ] Documentation auto-updates with new capabilities

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- file: /home/ec2-user/projects/LaMaquinaDeNoticias/.claude/commands/task.md
  why: Current task management system to integrate with
  
- file: /home/ec2-user/projects/LaMaquinaDeNoticias/.claude/commands/build.md
  why: Example command structure and @include patterns
  
- file: /home/ec2-user/projects/LaMaquinaDeNoticias/.claude/shared/superclaude-core.yml
  why: Core philosophy and standards to maintain
  
- file: /home/ec2-user/projects/LaMaquinaDeNoticias/.claude/shared/superclaude-personas.yml
  why: Personas to integrate into PRP generation
  
- file: /home/ec2-user/projects/LaMaquinaDeNoticias/.claude/commands/shared/task-management-patterns.yml
  why: Task hierarchy to extend with PRPs
  
- file: /home/ec2-user/projects/LaMaquinaDeNoticias/.claude/commands/shared/flag-inheritance.yml
  why: Universal flags that PRPs must support
  
- file: /home/ec2-user/projects/LaMaquinaDeNoticias/ContextEngineering/context-engineering-intro/PRPs/templates/prp_base.md
  why: Base PRP template to adapt
  
- file: /home/ec2-user/projects/LaMaquinaDeNoticias/ContextEngineering/context-engineering-intro/.claude/commands/generate-prp.md
  why: Generation logic to adapt for SuperClaude
  
- file: /home/ec2-user/projects/LaMaquinaDeNoticias/ContextEngineering/context-engineering-intro/.claude/commands/execute-prp.md
  why: Execution pattern to integrate

- url: https://github.com/anthropics/claude-code
  why: Claude Code documentation for best practices
```

### Current Codebase tree
```bash
/home/ec2-user/projects/LaMaquinaDeNoticias/
├── .claude/
│   ├── CLAUDE.md                    # Main config to update
│   ├── commands/
│   │   ├── analyze.md              # 19 existing commands
│   │   ├── build.md
│   │   ├── task.md                 # Integrate with this
│   │   └── ...
│   └── shared/
│       ├── superclaude-*.yml       # Core configs
│       └── ...
├── ContextEngineering/
│   ├── context-engineering-intro/   # PRP examples
│   └── SuperClaude/                # SuperClaude source
└── PRPs/                           # New directory for PRPs
```

### Desired Codebase tree with files to be added
```bash
/home/ec2-user/projects/LaMaquinaDeNoticias/
├── .claude/
│   ├── CLAUDE.md                    # UPDATE: Add PRP Mode section
│   ├── commands/
│   │   ├── prp.md                  # NEW: Main PRP command
│   │   ├── generate-prp.md         # NEW: Adapted generator
│   │   ├── execute-prp.md          # NEW: Adapted executor
│   │   └── task.md                 # UPDATE: Add task:prp operation
│   └── shared/
│       ├── prp-patterns.yml        # NEW: PRP-specific patterns
│       ├── prp-integration.yml     # NEW: Integration mappings
│       └── task-management-patterns.yml  # UPDATE: Add Level_0_PRPs
├── PRPs/
│   ├── templates/                  # NEW: Template directory
│   │   ├── prp_base.md            # Adapted base template
│   │   ├── prp_api.md             # API-specific template
│   │   ├── prp_frontend.md        # Frontend template
│   │   └── prp_fullstack.md       # Full-stack template
│   └── README.md                   # NEW: PRP usage guide
└── docs/
    └── GUIA_SUPERCLAUDE.md         # UPDATE: Add PRP section
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: SuperClaude uses @include syntax - must parse correctly
# CRITICAL: PRPs are YAML frontmatter + Markdown - preserve formatting
# CRITICAL: TodoWrite expects specific JSON structure - maintain compatibility
# CRITICAL: Personas are now flags (--persona-*) not separate modes
# CRITICAL: Task IDs use timestamp format - maintain consistency
# CRITICAL: Commands must inherit universal flags via @include
# CRITICAL: Evidence-based language required - no superlatives
```

## Implementation Blueprint

### Command Structure Pattern
```yaml
# /prp command following SuperClaude patterns
Purpose: "PRP mode for complex feature development"
Execute: "immediate | --plan→show first"
Operations:
  - init: "Start PRP mode for feature"
  - generate: "Create comprehensive PRP"
  - execute: "Run PRP with validation"
  - status: "Show PRP progress"
  - exit: "Return to normal mode"
```

### Task Hierarchy Integration
```yaml
# Extend task-management-patterns.yml
Task_Management_Hierarchy:
  Level_0_PRPs: "Comprehensive feature specs (PRPs/ folder)"
    Purpose: "Complex feature planning with validation"
    Scope: "Multi-file, multi-system features"
    Examples: ["auth system", "payment integration", "API redesign"]
    
  Level_1_Tasks: "High-level features (./claudedocs/tasks/)"
    # Existing definition remains
    
  Level_2_Todos: "Immediate actionable steps (TodoWrite)"
    # Existing definition remains

PRP_Task_Flow:
  Creation: "PRP generate → Task create → Todo breakdown"
  Execution: "PRP execute → Todo tracking → Validation loops"
  Completion: "Validation pass → Task complete → Doc generate"
```

### List of tasks to be completed

```yaml
Task 1: Create PRP command structure
CREATE .claude/commands/prp.md:
  - PATTERN: Follow structure from task.md and build.md
  - Include universal flags via @include
  - Define 5 operations: init, generate, execute, status, exit
  - Add examples for each operation
  - Integrate with existing patterns

Task 2: Create PRP patterns file
CREATE .claude/commands/shared/prp-patterns.yml:
  - PATTERN: Follow YAML structure from task-management-patterns.yml
  - Define PRP standards and validation rules
  - Create decision triggers for PRP mode
  - Add integration mappings

Task 3: Adapt Context Engineering commands
CREATE .claude/commands/generate-prp.md:
  - PATTERN: Adapt from context-engineering-intro version
  - Add persona integration for specialized generation
  - Include compression flags support
  - Research using existing SuperClaude tools

CREATE .claude/commands/execute-prp.md:
  - PATTERN: Adapt from context-engineering-intro version
  - Integrate with TodoWrite for tracking
  - Use SuperClaude validation patterns
  - Add recovery and checkpoint support

Task 4: Create PRP templates
CREATE PRPs/templates/:
  - PATTERN: Base on context-engineering-intro template
  - Add SuperClaude-specific sections
  - Create specialized variants (API, frontend, etc.)
  - Include @include references

Task 5: Integrate with task system
MODIFY .claude/commands/task.md:
  - ADD operation: /task:prp [task-id]
  - Convert existing task to PRP format
  - Maintain bidirectional sync

MODIFY .claude/commands/shared/task-management-patterns.yml:
  - ADD Level_0_PRPs to hierarchy
  - Define auto-trigger rules
  - Add PRP→Task→Todo mappings

Task 6: Update main configuration
MODIFY .claude/CLAUDE.md:
  - ADD section: ## PRP Mode
  - Include decision rules
  - Reference new commands
  - Explain integration

Task 7: Create documentation
CREATE PRPs/README.md:
  - Usage guide for PRP mode
  - Decision flowchart
  - Examples and best practices

MODIFY docs/GUIA_SUPERCLAUDE.md:
  - ADD PRP section with examples
  - Update command reference
  - Add workflow diagrams

Task 8: Validation and testing
TEST all commands:
  - Verify /prp operations work
  - Test persona integration
  - Confirm task sync works
  - Validate token optimization
```

### Per task pseudocode

```python
# Task 1: PRP Command Structure
# .claude/commands/prp.md
"""
**Purpose**: PRP mode for complex feature development

@include shared/universal-constants.yml#Universal_Legend

## Command Execution
Execute: immediate. --plan→show plan first
Purpose: "Manage PRPs for complex features"

Operations:
/prp --init [description]:
  - Check if feature complexity warrants PRP
  - Create PRP directory structure
  - Initialize tracking
  
/prp --generate:
  - Research codebase patterns
  - Apply selected persona logic
  - Generate comprehensive PRP
  - Save to PRPs/feature-name.md
  
/prp --execute [prp-file]:
  - Load PRP context
  - Create task breakdown
  - Execute with validation
  - Track via TodoWrite

@include shared/flag-inheritance.yml#Universal_Always
"""

# Task 3: Generate PRP Command
# Research and generation logic
async def generate_prp(feature_description, flags):
    # Apply persona if specified
    if flags.persona:
        context = load_persona_context(flags.persona)
    
    # Research phase
    patterns = await search_codebase_patterns(feature_description)
    docs = await search_documentation(feature_description)
    
    # Apply compression if requested
    if flags.uc:
        content = compress_content(patterns, docs)
    
    # Generate PRP using template
    prp = render_template('prp_base.md', {
        'feature': feature_description,
        'patterns': patterns,
        'documentation': docs,
        'persona_context': context
    })
    
    return prp

# Task 5: Task Integration
# Extend task.md with PRP operation
def task_prp_operation(task_id):
    task = load_task(task_id)
    
    # Check complexity triggers
    if task.file_count < 3 and task.estimated_time < 30:
        return "Task too simple for PRP. Use direct commands."
    
    # Convert to PRP format
    prp = create_prp_from_task(task)
    save_prp(prp)
    
    # Update task with PRP reference
    task.prp_file = f"PRPs/{task.id}.md"
    task.status = "prp_generated"
    save_task(task)
    
    return f"PRP generated: {task.prp_file}"
```

### Integration Points
```yaml
ENVIRONMENT:
  - Keep all existing SuperClaude configs
  - No new dependencies needed
  
COMMANDS:
  - /prp integrates with /task seamlessly
  - /generate-prp uses existing research patterns
  - /execute-prp leverages TodoWrite
  
VALIDATION:
  - Use existing SuperClaude validation patterns
  - Add PRP-specific checks for completeness
  - Integrate with git checkpoints
```

## Validation Loop

### Level 1: Command Structure
```bash
# Verify new commands load correctly
grep -r "@include" .claude/commands/prp.md
grep -r "Purpose:" .claude/commands/generate-prp.md

# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('.claude/commands/shared/prp-patterns.yml'))"

# Expected: No errors, all includes resolve
```

### Level 2: Integration Tests
```python
# Test PRP generation with persona
def test_prp_generation_with_persona():
    """Test that personas enhance PRP generation"""
    result = generate_prp("API authentication system", {"persona": "architect"})
    assert "Domain-Driven Design" in result
    assert "architectural patterns" in result

# Test task conversion
def test_task_to_prp_conversion():
    """Test converting existing task to PRP"""
    task = create_task("Complex feature")
    prp = task_prp_operation(task.id)
    assert os.path.exists(f"PRPs/{task.id}.md")
    assert task.prp_file is not None

# Test todo synchronization  
def test_prp_todo_sync():
    """Test that PRPs generate todos correctly"""
    prp = load_prp("test-feature.md")
    todos = execute_prp(prp)
    assert len(todos) > 0
    assert todos[0]["status"] == "pending"
```

### Level 3: Workflow Test
```bash
# Test complete workflow
/task:create "Implement OAuth 2.0 authentication"
/prp --init --from-task
/prp --generate --persona-architect --think-hard
# Review generated PRP
/prp --execute PRPs/oauth-authentication.md
/prp --status
# Verify todos created and tracking works

# Expected: Smooth flow with no command conflicts
```

## Final Validation Checklist
- [ ] All new commands follow SuperClaude patterns
- [ ] @include syntax works correctly
- [ ] PRPs integrate with task management
- [ ] Personas enhance PRP generation
- [ ] Token optimization applies to PRPs
- [ ] Decision triggers work correctly
- [ ] Existing workflows unchanged
- [ ] Documentation updated
- [ ] No duplicate functionality
- [ ] Clear mode boundaries

---

## Anti-Patterns to Avoid
- ❌ Don't force PRPs for simple tasks
- ❌ Don't create new syntax - use @include
- ❌ Don't bypass existing validation
- ❌ Don't duplicate task management
- ❌ Don't break universal flags
- ❌ Don't make PRPs mandatory

## Confidence Score: 9/10

High confidence due to:
- Clear integration points with existing systems
- Reuse of proven SuperClaude patterns
- Selective activation maintains simplicity
- Comprehensive validation approach

Minor uncertainty on exact trigger thresholds, but these can be tuned based on usage.