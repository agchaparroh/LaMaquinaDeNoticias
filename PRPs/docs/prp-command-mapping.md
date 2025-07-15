# PRP Command Mapping System Design

**Date**: 2025-01-15
**Designer**: SuperClaude with --persona-architect
**Design Pattern**: Deterministic Command Mapping

## System Overview

The PRP Command Mapping System transforms task descriptions into explicit SuperClaude commands, ensuring deterministic execution without interpretation.

## Architecture Design

### 1. Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    PRP Command Mapping System                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐    ┌──────────────────┐               │
│  │ Task Analyzer   │───▶│ Command Mapper   │               │
│  └─────────────────┘    └──────────────────┘               │
│           │                      │                           │
│           ▼                      ▼                           │
│  ┌─────────────────┐    ┌──────────────────┐               │
│  │ Context Engine  │    │ Persona Selector │               │
│  └─────────────────┘    └──────────────────┘               │
│           │                      │                           │
│           └──────────┬───────────┘                          │
│                      ▼                                       │
│            ┌─────────────────┐                              │
│            │ Command Builder │                              │
│            └─────────────────┘                              │
│                      │                                       │
│                      ▼                                       │
│            ┌─────────────────┐                              │
│            │ Task with Command│                              │
│            └─────────────────┘                              │
└─────────────────────────────────────────────────────────────┘
```

### 2. Mapping Strategy

#### Task Categories → Commands

```yaml
Task_Category_Definitions:
  Analysis:
    Keywords: ["analyze", "understand", "investigate", "examine", "review"]
    Primary_Command: "/analyze"
    Flags: ["--architecture", "--code", "--dependencies"]
    
  Design:
    Keywords: ["design", "architect", "plan", "structure", "blueprint"]
    Primary_Command: "/design"
    Flags: ["--patterns", "--system", "--api", "--think-hard"]
    
  Implementation:
    Keywords: ["implement", "build", "create", "develop", "code"]
    Primary_Command: "/build"
    Flags: ["--tdd", "--feature", "--uc"]
    
  Testing:
    Keywords: ["test", "verify", "validate", "check", "ensure"]
    Primary_Command: "/test"
    Flags: ["--unit", "--integration", "--coverage", "--strict"]
    
  Security:
    Keywords: ["secure", "audit", "scan", "vulnerability", "protect"]
    Primary_Command: "/scan"
    Flags: ["--security", "--owasp", "--strict"]
    
  Optimization:
    Keywords: ["optimize", "improve", "refactor", "enhance", "performance"]
    Primary_Command: "/improve"
    Flags: ["--performance", "--refactor", "--quality"]
    
  Documentation:
    Keywords: ["document", "describe", "explain", "guide", "readme"]
    Primary_Command: "/document"
    Flags: ["--api", "--user", "--examples", "--comprehensive"]
```

#### Persona Assignment Rules

```yaml
Persona_Assignment_Matrix:
  Analysis_Tasks:
    Primary: "analyzer"
    Secondary: "architect"
    Context_Rules:
      - If "system-wide": "architect"
      - If "debugging": "analyzer"
      
  Design_Tasks:
    Primary: "architect"
    Secondary: "senior-dev"
    Context_Rules:
      - If "API": "backend"
      - If "UI/UX": "frontend"
      
  Implementation_Tasks:
    Primary: "senior-dev"
    Secondary: ["backend", "frontend"]
    Context_Rules:
      - If "API|service|database": "backend"
      - If "UI|component|style": "frontend"
      - If "full-stack": "senior-dev"
      
  Testing_Tasks:
    Primary: "qa"
    Secondary: "senior-dev"
    Context_Rules:
      - If "performance": "performance"
      - If "security": "security"
      
  Security_Tasks:
    Primary: "security"
    Secondary: "senior-dev"
    
  Optimization_Tasks:
    Primary: "performance"
    Secondary: "refactorer"
    Context_Rules:
      - If "code quality": "refactorer"
      - If "speed|memory": "performance"
      
  Documentation_Tasks:
    Primary: "mentor"
    Secondary: "senior-dev"
```

### 3. Command Building Algorithm

```python
class CommandMapper:
    def map_task_to_command(self, task_description, context):
        # 1. Categorize task
        category = self.categorize_task(task_description)
        
        # 2. Get base command
        base_command = self.get_base_command(category)
        
        # 3. Determine context-specific flags
        flags = self.determine_flags(task_description, context, category)
        
        # 4. Select appropriate persona
        persona = self.select_persona(category, context)
        
        # 5. Build complete command
        return {
            "command": f"{base_command} {' '.join(flags)}",
            "persona": f"--persona-{persona}"
        }
    
    def categorize_task(self, description):
        # Use keyword matching with weights
        scores = {}
        for category, data in TASK_CATEGORIES.items():
            score = sum(1 for keyword in data['keywords'] 
                       if keyword in description.lower())
            scores[category] = score
        
        return max(scores, key=scores.get)
```

### 4. Integration Points

#### With generate-prp.md
```yaml
Generation_Enhancement:
  Input: Task description from PRP template
  Process:
    1. Parse task description
    2. Apply command mapping
    3. Insert command and persona into task
  Output: Task with explicit SuperClaude command
```

#### With execute-prp.md
```yaml
Execution_Modification:
  Current: Interprets task and chooses tools
  New: Reads and executes specified command
  Change:
    - Remove: Tool selection logic
    - Add: Command extraction and execution
    - Add: Persona adoption before execution
```

### 5. Command Format in Tasks

```yaml
Standard_Task_Format:
  Task_Number: "Sequential identifier"
  Description: "Clear task description"
  Priority: "high|medium|low"
  Dependencies: "Previous task references"
  SuperClaude_Command: "Exact command with flags"
  Persona: "Persona flag"
  Files: "Files to create/modify"
  Validation: "Validation commands"
  Expected_Output: "What this produces"
```

### 6. Validation Rules

```yaml
Command_Validation:
  - Must be one of 19 valid SuperClaude commands
  - Flags must be valid for the command
  - Persona must be one of 9 valid personas
  - Command must align with task description
  
Mapping_Quality_Checks:
  - Coverage: All task types map to commands
  - Consistency: Similar tasks get similar commands
  - Appropriateness: Commands match task intent
  - Completeness: No unmapped task types
```

### 7. Fallback Strategy

```yaml
Fallback_Rules:
  Unknown_Task_Type:
    Default_Command: "/analyze --general"
    Default_Persona: "senior-dev"
    Log: "Unknown task type, using general analysis"
    
  Ambiguous_Category:
    Strategy: "Use primary keyword match"
    Secondary: "Apply context rules"
    Default: "Use most conservative command"
```

## Implementation Guidelines

### Phase 1: Core Mapping
1. Implement Task_Command_Mapping in prp-patterns.yml
2. Create command selection logic in generate-prp.md
3. Test with various task descriptions

### Phase 2: Context Enhancement
1. Add context-aware flag selection
2. Implement persona assignment rules
3. Validate command appropriateness

### Phase 3: Execution Integration
1. Modify execute-prp.md for strict execution
2. Add command extraction logic
3. Implement persona adoption

### Phase 4: Validation & Testing
1. Create command validation tests
2. Test all 19 commands coverage
3. Verify deterministic execution

## Success Metrics

1. **Command Coverage**: 100% of tasks have valid commands
2. **Mapping Accuracy**: >95% appropriate command selection
3. **Execution Fidelity**: 100% commands executed as specified
4. **Persona Utilization**: All 9 personas actively used
5. **Determinism**: Same task always maps to same command

## Risk Mitigation

1. **Over-specification**: Balance between flexibility and determinism
2. **Command Mismatch**: Validation to ensure command fits task
3. **Persona Confusion**: Clear rules for persona selection
4. **Edge Cases**: Comprehensive fallback strategy

---

*Design complete. This system ensures every PRP task explicitly specifies its SuperClaude command, creating fully deterministic execution plans.*