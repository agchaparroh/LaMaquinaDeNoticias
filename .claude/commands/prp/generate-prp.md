# Generate PRP

**Purpose**: Generate comprehensive Product Requirements Prompt from feature description

---

@include shared/universal-constants.yml#Universal_Legend

## Command Execution
Execute: immediate. --plan→show research & generation steps
Legend: Research→Analyze→Generate→Validate→Save
Purpose: "Generate comprehensive PRP for complex feature implementation"

## Feature File: $ARGUMENTS

Generate a complete PRP (Product Requirements Prompt) with thorough research and context gathering. The generated PRP will include all necessary context for AI agents to implement features through self-validation and iterative refinement.

## Research Process

### 1. Codebase Analysis
- Search for similar features and patterns using /analyze
- Identify relevant files with Glob and Grep
- Note existing conventions using pattern recognition
- Check test patterns for validation approaches
- Document architectural decisions

### 2. External Research
- Search documentation with WebSearch when needed
- Find implementation examples (GitHub, docs)
- Identify best practices and common pitfalls
- Gather library-specific requirements
- Note version compatibility issues

### 3. Context Gathering
- Analyze dependencies and integrations
- Map data flow and system boundaries
- Identify security considerations
- Document performance requirements
- List regulatory/compliance needs

## Generation Process

### Phase 1: Feature Analysis
```yaml
Analyze:
  - Complexity evaluation against triggers
  - Persona selection based on domain
  - Template selection from patterns
  - Risk assessment for critical paths
```

### Phase 2: Research & Discovery
```yaml
Research:
  Codebase:
    - Similar implementations
    - Existing patterns
    - Test approaches
    - Error handling
  External:
    - API documentation
    - Best practices
    - Common issues
    - Security guides
```

### Phase 3: PRP Generation
Using selected template (`PRPs/templates/[type].md`):
- Populate all sections with gathered context
- Include specific file references
- Add executable validation commands
- Define clear success criteria
- Create task breakdown with explicit commands

#### Command Mapping Process
For each task in the breakdown:
1. Analyze task description keywords
2. Match against Task_Categories in prp-patterns.yml
3. Select appropriate SuperClaude command
4. Determine context-specific flags
5. Assign suitable persona
6. Format with explicit command specification

@include shared/prp-patterns.yml#Task_Command_Mapping

### Phase 4: Quality Validation
```yaml
Validate:
  - Context completeness (>90%)
  - Validation coverage (all components)
  - Pattern references (≥3)
  - Success criteria (measurable)
  - Task clarity (actionable)
```

## Persona Integration

Selected persona enhances generation focus:

| Persona | Enhancement Focus |
|---------|------------------|
| `--persona-architect` | System design, scalability, patterns |
| `--persona-qa` | Validation loops, test coverage, edge cases |
| `--persona-senior-dev` | Best practices, maintainability, documentation |
| `--persona-lead-dev` | Team interfaces, deployment, coordination |
| `--persona-devops` | Infrastructure, monitoring, deployment |

## Template Selection

@include shared/prp-patterns.yml#Template_Selection

## Output Format

Generated PRP includes:
```markdown
name: "[Feature Name] - Context-Rich Implementation Spec"
description: |
  [Comprehensive description]

## Goal
[Clear end state]

## Why
[Business value and problems solved]

## What
[User-visible behavior and technical requirements]

### Success Criteria
- [ ] [Measurable outcomes]

## All Needed Context
[Documentation, examples, references]

## Implementation Blueprint
[Task breakdown with explicit SuperClaude commands]

### Task Format
@include shared/prp-patterns.yml#Task_Format_With_Commands

## Validation Loop
[Executable validation commands]

## Confidence Score: [1-10]/10
```

## Command Selection Logic

When generating tasks with explicit commands:

### Keyword Analysis
```python
# Pseudo-code for command selection
def select_command(task_description):
    for category, config in Task_Categories:
        if any(keyword in task_description.lower() 
               for keyword in config['Keywords']):
            return {
                'command': config['Primary_Command'],
                'flags': select_flags(task_description, config),
                'persona': select_persona(task_description, config)
            }
    return default_analyze_command()
```

### Flag Selection
@include shared/prp-patterns.yml#Command_Selection_Algorithm

### Example Mappings
| Task Description | Selected Command | Persona |
|-----------------|------------------|---------|
| "Analyze authentication flow" | `/analyze --architecture --code` | `--persona-architect` |
| "Implement OAuth endpoints" | `/build --feature --tdd --uc` | `--persona-backend` |
| "Test security vulnerabilities" | `/scan --security --owasp --strict` | `--persona-security` |
| "Optimize database queries" | `/improve --performance --metrics` | `--persona-performance` |

## Quality Metrics

Target metrics for generated PRPs:
- Context Completeness: >90%
- One-pass Success Rate: >80%
- Validation Coverage: 100%
- Pattern References: ≥3
- Confidence Score: ≥8/10
- Command Mapping: 100% of tasks with explicit commands

@include shared/flag-inheritance.yml#Universal_Always

### PRP-Specific Flags
| Flag | Purpose |
|------|---------|
| `--research-deep` | Extended research phase |
| `--context-full` | Maximum context inclusion |
| `--validation-strict` | Comprehensive validation loops |
| `--template=[name]` | Force specific template |

## Examples

Generate PRP with architect persona:
```bash
/generate-prp oauth-implementation.md --persona-architect
# Researches and generates with system design focus
```

Generate with deep research:
```bash
/generate-prp payment-integration.md --research-deep --think-hard
# Extended research phase before generation
```

Generate with specific template:
```bash
/generate-prp user-dashboard.md --template=frontend --persona-qa
# Uses frontend template with QA focus
```

## Output Location
Save as: `PRPs/[feature-name].md`

## Post-Generation
After generation:
1. Review generated PRP for completeness
2. Run `/prp --execute` to implement
3. Or convert to task: `/task:create --from-prp`

---
*Generate PRP - Context-rich specification generation for SuperClaude*