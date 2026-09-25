---
name: bootstrap-style-standardization
description: "Use when: standardizing UI across a project to a Bootstrap-like look and feel; unifying cards, pills, buttons, tables, and modal sections; applying consistent typography and spacing; polishing dark dashboard panels without changing data logic."
---

# Bootstrap-Style Standardization

## Use when
- The app needs a consistent visual language across pages and sections.
- Multiple components use different card, button, badge, and table styles.
- Dark dashboard panels feel inconsistent or patchwork instead of cohesive.
- Modal/detail blocks still use legacy custom styling while the rest of the app has been standardized.
- Typography, spacing, radii, and button treatments need a single design system.
- A UI cleanup is required without altering business logic or data behavior.

## Goal
Create a shared Bootstrap-inspired visual system that makes the dashboard feel clean, consistent, and production-ready while keeping implementation lightweight, minimal, and based on the existing app architecture.

## Standard workflow

### Phase 1: Audit
1. Identify the current visual inconsistencies:
   - card borders and shadows
   - table shell styling
   - button appearance
   - badge/pill treatment
   - modal container styling
   - typography scale and line height
2. Note which sections are already standardized and which still use ad hoc classes.
3. Prioritize sections that are user-visible and repeated across the app.

### Phase 2: Define shared primitives
Create or reuse common classes in the app stylesheet, avoiding unnecessary component-level class duplication.

Core patterns:
- `.card` for modal and main panel shells
- `.metric-card`, `.stat-card`, `.table-card` for repeated section blocks
- `.btn`, `.btn-primary`, `.btn-secondary`, `.btn-outline` for action controls
- `.badge`, `.badge-primary`, `.badge-secondary`, `.badge-success` for labels
- `.pill` for compact status badges
- `.table-shell` for consistent table containers
- `.score-badge` for score chips

Keep styling centralized in one shared source rather than spreading repeated CSS across many components.

### Phase 3: Standardize typography
Apply a single system for:
- font family
- base body size
- heading scale
- compact metadata text
- text weights and letter spacing

Prefer:
- one consistent sans-serif font stack
- one body font size scale across pages
- predictable sizes for tables, chips, labels, and modal content

### Phase 4: Normalize spacing and rhythm
Use a consistent scale for:
- card padding
- section gaps
- row spacing in tables
- modal padding and spacing between blocks
- border radius and pill radius

This should be driven by shared CSS tokens rather than ad hoc inline values.

### Phase 5: Apply to repeated sections
Update sections that are still using legacy styling:
- dashboard modals
- analyst or detail panels
- summary cards and metric rows
- open IPO and past IPO table shells
- close buttons and action buttons

Keep the change scoped to presentation. Do not alter data sources, calculation logic, or route behavior.

### Phase 6: Validate
1. Ensure the app still builds and TypeScript passes.
2. Check the layout for obvious spacing drift or misalignment.
3. Verify that modal and detail blocks match the rest of the app’s visual language.
4. Confirm no business logic or route behavior changed.

## Guardrails
- Keep the design system light and minimal; no new UI libraries unless absolutely required.
- Prefer shared CSS utilities over scattered page-specific styling.
- Do not mix Bootstrap-specific classes with custom ad hoc styling without a clear system.
- Preserve existing functionality and data rules.
- Do not refactor unrelated components.
- Maintain dark-mode dashboard aesthetics consistently across all views.
- Keep the approach incremental and low-risk.

## Typical patterns

### Shared design tokens
Use global CSS variables for:
- surface colors
- border colors
- text colors
- shadows
- radius values
- font sizing scale

Example:
```css
:root {
  --bs-surface: rgba(15, 23, 42, 0.82);
  --bs-border: rgba(148, 163, 184, 0.16);
  --font-ui: var(--font-geist-sans), "Segoe UI", Arial, sans-serif;
  --radius-card: 1.5rem;
  --radius-panel: 1.25rem;
}
```

### Reusable section structure
Apply the same pattern across cards and tables:
```tsx
<div className="card p-6">
  <div className="metric-card p-4">
    <h3 className="text-lg font-semibold text-white">Title</h3>
  </div>
</div>
```

### Modal cleanup pattern
Standardize legacy modal sections by replacing custom borders, shadows, and button styles with shared classes such as:
- `.card`
- `.btn btn-outline`
- `.stat-card`
- `.table-shell`

## Common tasks covered by this skill
- Bootstrap-like cleanup on modal sections
- Typography standardization for dashboard pages
- Shared card/table/button cleanup
- Final UI consistency pass across multiple components
- Dark dashboard polish without logic changes
- Visual alignment across route-specific pages and overlays

## Example outcome
After applying the skill, the project should have:
- consistent typography across headings and table cells
- consistent button, badge, and pill styling
- uniform cards and panels across home, open-IPO, and past-issues views
- polished modal and detail sections that match the rest of the dashboard
- no breakage in data rendering or route logic

## Validation checklist
- [ ] Shared utility styles defined in one stylesheet or central location
- [ ] Typography scale is consistent throughout the app
- [ ] Buttons, pills, and badges share the same design language
- [ ] Modals and detail panels match the rest of the dashboard styling
- [ ] Tables use shared container styling and no inconsistent legacy blocks remain
- [ ] TypeScript build still passes
- [ ] User-facing logic unchanged

## Related work
This skill complements:
- `component-modularization`
- `modularize-project`
- `update-all-markdown-docs`

Use it when the task is primarily about visual consistency, design system cleanup, and final UI polish rather than feature logic or architecture changes.
