---
name: modularize-project
description: "Use when: modularize the project, refactor into smaller modules, split large files into reusable components, create cleaner architecture, improve maintainability and separation of concerns."
---

# Modularize the Project

## Use when
- The user asks to refactor the codebase into smaller, clearer modules.
- Large files or responsibilities are bundled together and should be split.
- The project needs better separation of concerns without changing behavior.

## Goal
Improve maintainability by breaking large implementations into focused modules while preserving existing functionality and public behavior.

## Root directory policy
Keep the repository root limited to files required by the package manager, framework, deployment platform, version control, or repository onboarding. Project plans, progress logs, design notes, generated output, runtime logs, and domain-specific assets belong in a named subdirectory such as `docs/`, `config/`, `scripts/`, `input/`, or `output/`.

Target outcome: the root should contain only essential top-level artifacts, with no more than the smallest practical set of configuration and entry-point files. Do not move files merely to meet a number; classify each root item first and preserve tools' expected paths unless their configuration is updated in the same change.

## Root minimization workflow
1. Inventory root entries and classify each as essential configuration, source entry point, documentation, generated/runtime output, or misplaced domain content.
2. Keep essential configuration and framework-required files in place.
3. Move documentation into `docs/`, generated/runtime files out of version control, and domain content into the nearest existing folder.
4. Update references, scripts, ignore rules, and deployment configuration for every moved item.
5. Remove empty or redundant root artifacts only after checking tracked references and build tooling.
6. Validate with the narrowest relevant checks, including the application build and documentation/reference searches when paths changed.

## Standard workflow
1. Identify the large responsibility or file that is doing too much.
2. Group related functions or logic into a cohesive module.
3. Keep interfaces small and stable.
4. Move data handling, formatting, validation, and domain logic into clear modules.
5. Reuse existing patterns and project conventions before introducing new abstractions.
6. Keep the change minimal and targeted.

## Guardrails
- Do not rewrite the whole project in one pass.
- Do not change behavior unless required by the refactor.
- Prefer small, focused extraction over broad structural redesign.
- Keep naming clear and consistent with the current codebase.
- Preserve public APIs where they are already used.
- Do not create unnecessary abstraction layers.
- Do not add stray files to the repository root; keep the root directory reserved for project-level configuration and only essential top-level artifacts.
- Prefer existing project folders (for example, `web/`, `src/`, `docs/`, and `config/`) over creating new root-level modules or helper files.
- If a refactor creates a new file, confirm it belongs in the relevant domain folder and not at the project root.
- Never move framework-required files, package manifests, lockfiles, deployment manifests, or standard repository metadata without updating the tool that consumes them and validating the result.
- Treat generated logs and build output as non-source artifacts: ignore them and remove them from the working tree when they are not user-owned data.

## Common refactor targets
- Large UI files into reusable components or hooks
- Data-fetch and normalization logic into domain-specific modules
- Shared formatting, parsing, or validation helpers into utility files
- Service-specific flows into dedicated modules or packages

## Example approach
- Extract reusable business logic from a large file into a `utils`, `services`, or `domain` module.
- Keep the entry point thin and orchestrate calls between modules.
- Update imports to reflect the new structure.
- Validate the result with the smallest relevant build or test command.

## Output expectations
- Summarize the modules created or extracted.
- Call out the responsibilities moved into each module.
- Note any files left unchanged because they were already appropriately scoped.
