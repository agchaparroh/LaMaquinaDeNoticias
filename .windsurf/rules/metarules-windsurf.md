---
trigger: manual
---

---
# METARULES_WINDSURF.md
# Guidelines for creating, maintaining, and improving Windsurf AI rule documents.
# Project: La Máquina de Noticias
---

## Section: RULE_DOCUMENT_STRUCTURE

**Description:** Consistent structure for all Windsurf AI rule documents (e.g., `DEV_WORKFLOW_WINDSURF.md`, `PROJECT_STRUCTURE_WINDSURF.md`).
**Applies to:** All `.md` rule documents for Windsurf AI.
**Always Apply:** true

-   **Document Identification:**
    -   Start with `---`
    -   `# [FILENAME.md]`
    -   `# [One-line purpose of this rule document]`
    -   `# Project: La Máquina de Noticias` (if not globally assumed)
    -   End with `---`
-   **Section Formatting:**
    -   Use Markdown headings (`##`, `###`).
    -   For rule sets/major sections, clearly state: `Description:`, `Applies to:`, `Always Apply: true/false`.
-   **Rule Content:**
    -   Start sections with a high-level intent.
    -   Provide specific, actionable requirements relevant to "La Máquina de Noticias".
    -   Include Windsurf-specific examples where helpful.
    -   Reference Windsurf code/structure (from `PROJECT_STRUCTURE_WINDSURF.md`) to ground rules.
    -   Be DRY: Reference other rules/docs (e.g., "See `TASKMASTER_REFERENCE_WINDSURF.md` for commands").
    -   Use SHOULD (recommendation) or MUST (requirement) for clarity if needed.
-   **Code Examples:**
    -   Use fenced code blocks with language specification.
    -   Clearly show ✅ DO and ❌ DON'T for Windsurf practices.
      ```typescript
      // ✅ DO: Windsurf best practice.
      // ❌ DON'T: Windsurf anti-pattern.
      ```
-   **Writing Best Practices:**
    -   Use bullets for clarity.
    -   Be concise.
    -   Prefer actual Windsurf code/structure in examples.
    -   Maintain consistent formatting.

## Section: RULE_SYSTEM_IMPROVEMENT

**Description:** Continuously improving Windsurf AI rule documents based on project evolution, TCC Trinity effectiveness, and best practices for "La Máquina de Noticias".
**Applies to:** All Windsurf AI rule documents.
**Always Apply:** true

-   **Improvement Triggers:**
    -   New/changed Windsurf code patterns not covered (update `PROJECT_STRUCTURE_WINDSURF.md`).
    -   Repeated implementations needing standardization.
    -   Common errors preventable by a rule.
    -   New tools, libraries, or architectural changes in Windsurf.
    -   Inefficiencies in TCC Trinity workflow (`DEV_WORKFLOW_WINDSURF.md`).
-   **Analysis & Updates:**
    -   Compare new Windsurf code with rules. Identify gaps.
    -   Review LLM (with Context7) effectiveness; adjust rules for better AI performance.
    -   Analyze CodeRabbit feedback for proactive rule creation.
    -   **Add/Modify Rules When:** New tech is adopted, common bugs occur, reviews show repeated feedback, or Windsurf details (e.g., paths in `PROJECT_STRUCTURE_WINDSURF.md`) change.
    -   **Refine `DEV_WORKFLOW_WINDSURF.md` When:** Workflow steps are unclear/missed or tool leverage can be improved.
-   **Example: Pattern Recognition for `PROJECT_STRUCTURE_WINDSURF.md`**
    ```typescript
    // Repeated Windsurf data access:
    // const user = await db.user.findUnique({ where: { id }, include: { profile: true }});
    // Consider adding to PROJECT_STRUCTURE_WINDSURF.md:
    // "Default 'include' for user queries: { profile: true }"
    ```
-   **Quality Checks:**
    -   Rules actionable & Windsurf-specific.
    -   Examples from/for Windsurf.
    -   References (paths, tools) up-to-date.
-   **Continuous Improvement Process:**
    -   Monitor code reviews & dev questions for rule gaps.
    -   Update rules after major Windsurf refactors.
-   **Rule Deprecation:**
    -   Mark outdated rules/patterns as deprecated with explanation/link to new.
    -   Remove rules no longer applicable to Windsurf.
-   **Document Maintenance:**
    -   Keep examples & references synchronized with Windsurf's current state.
    -   Maintain clarity & consistency.