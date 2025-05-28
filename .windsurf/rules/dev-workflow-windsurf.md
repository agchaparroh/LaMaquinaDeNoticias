---
trigger: always_on
description: s
---

## Core Development Philosophy: The TCC Trinity

The Windsurf development process is centered around the "TCC Trinity": TaskmasterAI, your primary LLM (enhanced by Context7), and CodeRabbit. Each plays a crucial role:

-   **TaskmasterAI (task-master CLI):** Defines the roadmap and manages the task lifecycle (creation, breakdown, status, dependencies). It's the driver for *what* to do and *when*.
-   **Primary LLM with Context7:**
    -   Your primary LLM is your main AI assistant for coding, problem-solving, and understanding.
    -   **Context7** enhances this LLM by providing it with on-demand, in-depth, and version-aware technical knowledge about **external libraries, APIs, and SDKs**. This includes best practices and code examples for these tools, ensuring the LLM generates accurate and up-to-date solutions for tasks. It's key for understanding *how* to implement tasks effectively using external dependencies.
-   **CodeRabbit:** Performs automated code reviews to ensure quality, adherence to Windsurf standards, and identify potential issues. 

**Note on Context7 Integration:** "Context7" references mean interacting with your primary LLM (using Context7 as its MCP server for real-time, version-aware external tool data). The LLM synthesizes this with Windsurf project context (code, prompts, docs) for task assistance. Context7: technical accuracy for external dependencies; LLM: project-specific application.

## Development Workflow Process (Integrated with TCC Trinity)

1.  **Project Initiation:**
    *   Start new Windsurf projects with `task-master init` or `task-master parse-prd --input=<prd-file.txt>` to generate `tasks.json`.
    *   Consult your **primary LLM (with Context7)** for an overview of Windsurf's domain, architecture, and technical considerations, ensuring discussions about external technologies are up-to-date.

2.  **Session Start & Task Selection:**
    *   Begin with `task-master list` to review current tasks.
    *   Determine the next task using `task-master next`.
    *   Select tasks based on completed dependencies, priority, and ID.

3.  **Task Understanding & Clarification:**
    *   View details with `task-master show <id>`.
    *   Consult your **primary LLM (with Context7)** for a deep understanding of the task's technical requirements. Context7 ensures exploration of solutions involving external libraries/APIs uses correct, up-to-date information. The LLM assists in identifying relevant existing Windsurf code.
    *   Clarify ambiguities with user input if needed.

4.  **Complexity Analysis & Task Breakdown:**
    *   Analyze complexity with `task-master analyze-complexity --research`.
    *   Consult your **primary LLM (with Context7)** to understand task complexity within Windsurf. If external tech is a factor, Context7 provides accurate insights for the LLM to inform breakdown strategies.
    *   Break down tasks with `task-master expand --id=<id>`, informed by LLM/Context7 insights.
    *   Use `task-master clear-subtasks --id=<id>` before regenerating subtasks if necessary.

5.  **Implementation:**
    *   Continuously leverage your **primary LLM (with Context7)**. Context7 ensures the LLM provides Windsurf-related code examples that correctly use external libraries/APIs, advises on algorithm design incorporating these tools accurately, and aids in troubleshooting.
    *   Implement code per task details, dependencies, Windsurf standards, and LLM/Context7 best practices.

6.  **Verification & Quality Assurance:**
    *   Verify tasks per their test strategies.
    *   **CodeRabbit:** *Before* marking tasks "done", submit code for review by CodeRabbit (configured with Windsurf rules). Address all critical CodeRabbit feedback. This may involve code changes or new/updated TaskmasterAI tasks.

7.  **Task Completion:**
    *   Mark completed and CodeRabbit-approved tasks with `task-master set-status --id=<id> --status=done`.

8.  **Maintenance & Iteration:**
    *   If implementation differs from the plan, update dependent tasks using `task-master update`. Your **primary LLM (with Context7 data)** can help assess the impact.
    *   Regenerate task files with `task-master generate` after `tasks.json` updates.
    *   Use `task-master fix-dependencies` as needed.
    *   **Periodic Full Review (CodeRabbit):** At milestones, run comprehensive CodeRabbit reviews on the integrated Windsurf codebase. Issues may become new TaskmasterAI tasks.

## Task Status Management

-   **pending:** Ready for work.
-   **in-review:** Submitted to CodeRabbit, awaiting approval.
-   **done:** Completed, verified by tests, and **approved by CodeRabbit**.
-   **deferred:** Postponed.

## Implementation Drift Handling

When implementation significantly diverges, impacting future tasks or creating new dependencies:
1.  Consult your **primary LLM (with Context7)** to analyze implications for Windsurf, understand best practices for the new direction (especially concerning external tools), and formulate a technically accurate explanation.
2.  Call `task-master update --from=<futureTaskId> --prompt="<explanation_refined_by_primary_LLM_with_Context7>"` to update `tasks.json`.

## Code Analysis & Refactoring Techniques

-   **Initial Scan (grep):** Use `grep -E "export (function|const) \w+|function \w+\(|const \w+ = \(|module\.exports" --include="*.js" --include="*.ts" -r ./` to find exported functions across the Windsurf codebase.
-   **Primary LLM (with Context7) Integration:** Feed function/module lists to your primary LLM to understand purpose and interdependencies. If refactoring involves external libraries, the LLM (using Context7 data) provides accurate suggestions. The LLM considers Windsurf's architecture based on the available codebase.
-   **CodeRabbit Integration:** After refactoring, use CodeRabbit to check for dead code, new linting issues, or side effects.
-   **TaskmasterAI Integration:** Create TaskmasterAI tasks for specific refactoring activities.