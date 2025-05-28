---
trigger: model_decision
description: Aplicar esta regla cuando la tarea actual involucre la creación, interpretación o ejecución de comandos de task-master CLI, o cuando se necesite entender la estructura de tareas de TaskmasterAI o sus variables de entorno para el proyecto
---

Global CLI Usage (TaskmasterAI)
Command: task-master <command> [options] (replaces node scripts/dev.js)
Installation: npm install -g task-master-ai (or claude-task-master); or npx task-master-ai.
Note for "La Máquina de Noticias": TaskmasterAI files (e.g., tasks.json) are typically in the project's taskmaster/ root directory.
Task Structure Fields
Core fields for tasks in tasks.json and individual files:
id: (String|Number) Unique ID (e.g., "1", "1.1").
title: (String) Brief task title.
description: (String) Concise task summary.
status: (String) e.g., "pending", "in-review", "done", "deferred".
dependencies: (Array<String|Number>) Prerequisite task IDs. (Status shown in listings: ✅ done, ⏱️ pending).
priority: (String) e.g., "high", "medium", "low".
details: (String) In-depth implementation notes; can be informed by primary LLM (using Context7 for external tech accuracy) for "La Máquina de Noticias".
testStrategy: (String) Verification approach.
subtasks: (Array<Task Object>) Smaller, specific sub-tasks.
context7QuerySuggestions: (Optional Array<String>) Queries for primary LLM (using Context7 for external tech) e.g., "How to use [library] for [feature] in La Máquina?".
codeRabbitReviewNotes: (Optional Array<String>) Notes for CodeRabbit, e.g., "Focus on [aspect] in La Máquina's [module].".
Key Environment Variables (TaskmasterAI)
ANTHROPIC_API_KEY (Required): Primary LLM API key (e.g., Claude).
MODEL (Default: "claude-3-opus-20240229"): Primary LLM model.
MAX_TOKENS (Default: "4000"): Max LLM response tokens.
PROJECT_NAME (Default: "La Máquina de Noticias"): Project name in metadata.
(Otros como TEMPERATURE, DEBUG, TASKMASTER_LOG_LEVEL, DEFAULT_SUBTASKS, DEFAULT_PRIORITY, PROJECT_VERSION, PERPLEXITY_API_KEY, PERPLEXITY_MODEL son configurables pero menos críticos para la referencia básica de la IA).
Core Operations
Determining Next Task: task-master next
Shows next task with satisfied dependencies (prioritized by priority, dep count, ID). Includes details, subtasks, Context7 suggestions. Use before starting work.
Viewing Specific Task: task-master show <id|subtask_id> (e.g., task-master show 1.2)
Displays full task info. Use details for precise LLM (with Context7) queries.
Managing Dependencies:
task-master add-dependency --id=<id> --depends-on=<dep_id>
task-master remove-dependency --id=<id> --depends-on=<dep_id>
(Prevents circular/duplicates; auto-regenerates task files).
Command Reference
(All commands interact with tasks.json and/or tasks/ directory, typically within taskmaster/ for this project).
init: Initializes TaskmasterAI project structure for "La Máquina de Noticias".
parse-prd --input=<file.txt>: Parses PRD, generates tasks.json (overwrites).
list [opts]: Lists tasks. Opts: --status=<val>, --with-subtasks, --file=<path>.
generate [opts]: Generates task files in tasks/ from tasks.json. Opts: --file=<path>, --output=<dir>. (Overwrites existing task files).
set-status --id=<id> --status=<val>: Updates task status.
update --from=<id> --prompt="<text>": Updates tasks (ID >= from_id, not 'done') with new context.
analyze-complexity [opts]: Analyzes task complexity, gives expansion recommendations. Opts: --output=<file>, --model=<model>, --threshold=<num>, --file=<path>, --research (Perplexity).
complexity-report [opts]: Displays formatted complexity report. Opts: --file=<path>.
expand --id=<id> [opts]: Expands task with subtasks. Opts: --all (pending tasks), --num=<val>, --research, --prompt="<text>", --force.
clear-subtasks --id=<id|ids> | --all: Removes subtasks for regeneration.
add-task [opts]: Adds AI-generated task. Opts: --file=<path>, --prompt="<desc>" (req), --dependencies=<ids>, --priority=<val>. (Consult LLM+Context7 for complex prompts).
validate-dependencies [opts]: Checks for invalid dependencies. Opts: --file=<path>.
fix-dependencies [opts]: Finds & fixes invalid dependencies. Opts: --file=<path>.