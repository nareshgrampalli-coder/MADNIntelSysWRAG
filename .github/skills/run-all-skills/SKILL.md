---
name: run-all-skills
description: "Use when: running the repository's skill workflow in proper sequence; orchestration of all project skills in the correct order before final verification or delivery."
---

# Run All Skills in Sequence

## Use when
- The user asks to run the full skill flow for the repository.
- A project task spans multiple skill areas and should follow a fixed execution order.
- The user wants a standard, repeatable orchestration across the repo's skill library.
- A change requires documentation, architecture review, modularization, UI cleanup, and final git save/push in order.

## Goal
Execute the repository's available skills in a disciplined sequence so each step builds on the previous one, avoids rework, and keeps the final result consistent with the project's conventions.

## Required execution order
Run the skills in this sequence:

1. `github-copilot-model-cost-order`
   - Confirm the active repo-specific model tier before work begins.
   - Use the lowest-cost viable model unless the task actually requires escalation.

2. `modularize-project`
   - Refactor the work into clear modules or focused responsibilities when needed.
   - Keep the change minimal and behavior-preserving.

3. `component-modularization`
   - Break large UI or component responsibilities into smaller, focused modules if component complexity justifies it.
   - Keep state and orchestration in the parent; presentation in child modules.

4. `bootstrap-style-standardization`
   - Apply a consistent Bootstrap-inspired visual pattern after structural changes are settled.
   - Keep the styling pass presentation-only and avoid behavioral drift.

5. `update-all-markdown-docs`
   - Update documentation and design notes to reflect the code or workflow changes.
   - Keep docs factual and aligned with the current repo structure.

6. `commit-and-push-all-changes`
   - Stage, commit, and push the final repository state.
   - Use a concise, accurate commit message and confirm the push result.

## Required workflow rules
- Do not skip earlier steps unless the user explicitly says the task is limited to a later phase.
- Keep the sequence fixed and predictable so the project evolves in a clean progression.
- If a step is not needed for a task, note that it was intentionally skipped rather than misrepresenting the sequence.
- Prefer minimal, focused edits at each stage instead of broad rewrites.
- Ensure each skill's output is consistent with the repository's architecture, naming conventions, and project purpose.
- Keep open-IPO and past-IPO logic separated and do not mix route-specific responsibilities.

## Guardrails
- Do not reorder the sequence for convenience.
- Do not perform unrelated refactors outside the current task scope.
- Do not create new root-level files or architecture unless the task truly requires it.
- Do not add dependencies unless clearly necessary.
- Do not claim completion of a later step before earlier ones are finished.
- Maintain evidence-based validation after each substantive change when practical.

## Typical orchestration pattern
```text
Task -> model selection -> project/module refactor -> component split -> UI polish -> docs update -> git save/push
```

## Output expectations
- State which skills were run and in what order.
- Summarize the result of each stage briefly and clearly.
- Call out any steps intentionally skipped because they were not needed.
- Confirm final repository status and whether the final push succeeded.

## Related skills
- `modularize-project`
- `component-modularization`
- `bootstrap-style-standardization`
- `update-all-markdown-docs`
- `commit-and-push-all-changes`
- `github-copilot-model-cost-order`
