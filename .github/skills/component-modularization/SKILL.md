---
name: component-modularization
description: "Use when: breaking down large monolithic components into smaller, focused modules; improving separation of concerns; enhancing testability; increasing component reusability; refactoring for better maintainability while ensuring zero errors."
---

# Component Modularization

## Use when
- A single component file exceeds 300–500 lines and handles multiple responsibilities.
- A component renders different views or features that could be independently useful.
- A component's state management or rendering logic could be isolated and tested separately.
- UI logic and business logic are tangled and difficult to follow.
- Multiple child features are embedded in a parent component.
- You need to improve code clarity without changing end-user behavior.

## Goal
Break large, monolithic components into smaller, focused, reusable modules while maintaining feature parity and ensuring zero TypeScript/lint errors. Improve separation of concerns, testability, maintainability, and component reusability.

## Standard workflow

### Phase 1: Analysis
1. **Identify large component** — Find files exceeding 300+ lines with multiple distinct responsibilities.
2. **Map responsibilities** — Document what the component does:
   - Rendering views (open state, closed state, details modal, etc.)
   - State management (filters, sorting, selection, async operations)
   - Data transformation and formatting
   - User interactions and callbacks
3. **Identify breakpoints** — Find natural boundaries for splitting:
   - Distinct views that could stand alone (e.g., "OpenIpoDashboard", "PastIpoDashboard")
   - Modal or overlay content that could be extracted
   - Reusable sub-sections (e.g., shared tables, cards, sections)
4. **Plan component tree** — Sketch how parent and child components will relate:
   - Parent: Retains shared state, orchestrates views, handles fetching/API calls
   - Children: Receive filtered data and callbacks via props
   - Siblings: Rendered conditionally based on parent state

### Phase 2: Extract child components
1. **Create new component files with functionality-based names** — One component per file, and each file name must describe the responsibility or view it encapsulates (e.g., `OpenIpoDashboard.tsx`, `PastIpoDashboard.tsx`, `IpoSummaryCards.tsx`). Avoid vague or generic names such as `Section.tsx`, `Panel.tsx`, or `Widget.tsx` unless the file is truly a shared generic primitive. Name files by feature, page section, or behavior, not by a temporary placeholder.
2. **Define TypeScript prop interfaces** — Be explicit about data and callbacks:
   ```typescript
   type FeatureComponentProps = {
     data: DataType[];
     selected: DataType | null;
     onSelect: (item: DataType) => void;
     onAction: () => void;
     isLoading: boolean;
   };
   ```
3. **Extract rendering logic** — Move JSX, tables, cards, and display formatting to child components.
4. **Keep state in parent** — Child components should be stateless/presentation-only or manage local UI state only.
5. **Import utilities and types** — Use existing shared utilities (formatting, parsing, styling helpers).

### Phase 3: Refactor parent component
1. **Import new child components** — Add imports at the top.
2. **Replace conditional rendering** — Use new components in place of large JSX blocks.
3. **Pass required props** — Ensure all data and callbacks flow correctly from parent to children.
4. **Preserve header and orchestration** — Keep parent-level UI (header, summary stats, modals, refresh logic) in the parent.
5. **Remove duplicated code** — Delete old JSX that's now in child components.
6. **Keep shared utilities** — Leave data transformation, API calls, and complex state in parent.

### Phase 4: Validate
1. **Run TypeScript check** — Ensure `npx tsc --noEmit` or similar passes with zero errors.
2. **Check import paths** — Verify all relative imports resolve correctly.
3. **Test functional flows** — Verify conditional rendering, state updates, callbacks work as before.
4. **Review component tree** — Ensure prop flow is unidirectional (parent → children).
5. **Check styling** — Confirm Tailwind classes, dark mode, responsive behavior unchanged.

## Guardrails
- **No behavior changes** — End users should not notice any difference in how the component works.
- **Functionality-based naming** — New files must be named for the responsibility they implement, not for their location or a vague pattern. Example: `OpenIpoDashboard.tsx` is better than `DashboardSection.tsx` when it renders the open-IPO view.
- **Props are the contract** — Use TypeScript to enforce type-safe prop interfaces; avoid implicit dependencies.
- **Avoid prop drilling** — If props go too deep, consider lifting state or using context (but prefer props first).
- **One component per file** — Keep component files focused (e.g., don't mix OpenIpoDashboard and PastIpoDashboard in one file).
- **Stateless child components** — Children should be "dumb" presentation components; keep "smart" logic in parents.
- **Keep parent lean** — After extraction, parent should orchestrate, not render everything.
- **Preserve public APIs** — If components are exported or used elsewhere, maintain their interface.
- **No breaking imports** — Update only the component being split; don't break existing consumer imports.
- **Test incrementally** — Validate each component as you add it, not after all changes.

## Common patterns

### Conditional View Rendering
**Before:** Large parent component with multiple conditional blocks (if open, render Table A; if closed, render Table B).
**After:** Create `OpenView.tsx` and `ClosedView.tsx`; parent renders one based on state.

```typescript
// Before: All in one 1000-line component
{activeView === "open" && renderOpenSection()}
{activeView === "past" && renderPastSection()}

// After: Clean parent delegation
{activeView === "open" ? (
  <OpenIpoDashboard {...props} />
) : (
  <PastIpoDashboard {...props} />
)}
```

### Modal or Detail Views
**Before:** Modal JSX embedded in parent; state management intertwined.
**After:** Extract modal into `DetailModal.tsx`; parent controls `isOpen`, passes `data`, and `onClose`.

### Reusable Tables or Lists
**Before:** Table markup repeated in multiple places with minor variations.
**After:** Create generic `DataTable.tsx` component with column configuration; reuse in multiple parents.

### Complex Render Methods
**Before:** `renderTableRow()`, `renderHeader()`, `renderFooter()` as functions in one file.
**After:** Extract into `TableRow.tsx`, `TableHeader.tsx`, `TableFooter.tsx`; import and compose.

## Code checklist

- [ ] Large component file identified (300+ lines, multiple responsibilities).
- [ ] Child components extracted with clear, single responsibilities.
- [ ] TypeScript prop interfaces defined for all child components.
- [ ] Parent component imports and uses child components correctly.
- [ ] All duplicated code removed from parent.
- [ ] Conditional rendering updated to use child components.
- [ ] Prop flow is unidirectional (parent → children).
- [ ] State management remains in parent; children are presentation-focused.
- [ ] No breaking changes to component exports or imports.
- [ ] TypeScript compilation passes with zero errors.
- [ ] No linting errors (ESLint, Prettier formatting checked).
- [ ] Responsive design and styling preserved.
- [ ] Dark mode / theme colors consistent.
- [ ] Callbacks (onSelect, onAction, etc.) properly passed and invoked.
- [ ] Edge cases (empty state, loading, errors) handled in child components.

## Example: IpoDashboard modularization

**Original problem:** `IpoDashboard.tsx` was 1040 lines with two distinct views (open IPOs, past issues) tangled together.

**Solution:**
1. Created `OpenIpoDashboard.tsx` (138 lines) — Renders Mainboard and SME open IPO tables with selection and report generation.
2. Created `PastIpoDashboard.tsx` (95 lines) — Renders gain/loss snapshots for closed IPOs.
3. Refactored `IpoDashboard.tsx` parent (825 lines) to:
   - Retain header, summary stats, modals, and API orchestration.
   - Import new child components.
   - Conditionally render `<OpenIpoDashboard />` or `<PastIpoDashboard />` based on `activeView` state.
   - Pass filtered data (`mainBoardIpos`, `smeIpos`, `pastMainboardRows`, `pastSmeRows`) and callbacks as props.
   - Remove ~200+ lines of duplicated table rendering code.

**Outcome:**
- ✅ Separation of concerns: Each component has one responsibility.
- ✅ Better testability: Smaller components easier to unit test in isolation.
- ✅ Improved maintainability: View logic separated from orchestration.
- ✅ Reusability: Child components can be used independently.
- ✅ Zero errors: TypeScript validation passes without issues.

## Performance considerations
- **Memoization:** Use `useMemo` and `useCallback` to prevent unnecessary re-renders when passing derived data/callbacks to children.
- **Lazy loading (optional):** For heavy child components, consider `React.lazy()` and `Suspense` if they're not needed immediately.
- **Props stability:** Ensure callback functions are stable (wrap in `useCallback` if created inline).

## Testing strategy
1. **Unit tests for child components:** Test with different prop combinations (data present, loading, empty, error states).
2. **Integration tests for parent:** Test view switching, callbacks, API interactions.
3. **Snapshot tests (optional):** Capture rendered output of child components to catch unintended visual changes.
4. **Manual browser tests:** Verify UI responsiveness, dark mode, accessibility across browsers.

## Common mistakes to avoid
- ❌ **Extracting too early** — Don't split components unnecessarily; only extract when there's clear separation.
- ❌ **Prop drilling hell** — If you're passing 10+ props, consider grouping or lifting state higher.
- ❌ **Mixing concerns** — Don't put API logic, formatting, AND rendering all in one component; separate them.
- ❌ **Breaking existing imports** — Ensure users of the old component still work (export from same location if needed).
- ❌ **Ignoring TypeScript errors** — Don't suppress errors with `any`; fix root cause (prop types, imports, etc.).
- ❌ **Forgetting to remove old code** — When extracting, delete the old rendering logic; don't leave duplicates.
- ❌ **Stateless children receiving mutable state** — If children need to modify parent state, use callbacks, not direct mutation.

## Example file structure after modularization

```
src/components/Dashboard/
  ├── IpoDashboard.tsx          (parent orchestrator, 825 lines)
  ├── OpenIpoDashboard.tsx      (open view, 138 lines)
  ├── PastIpoDashboard.tsx      (past view, 95 lines)
  ├── IpoSummaryCards.tsx       (shared summary metrics UI)
  └── __tests__/
      ├── IpoDashboard.test.tsx
      ├── OpenIpoDashboard.test.tsx
      ├── PastIpoDashboard.test.tsx
      └── IpoSummaryCards.test.tsx
```

Use names that reflect the actual functionality and role of each module. If a file renders a view, name it after that view; if it contains a reusable summary block, name it after that block; if it contains a specific action flow, name it after that flow.

## Output expectations
- Summarize the components created and their responsibilities.
- List the lines of code removed from parent and added to children.
- Confirm TypeScript compilation passes with zero errors.
- Note any behavioral changes (there should be none).
- Highlight improvements: testability, separation of concerns, reusability.
- Provide examples of how child components could be reused in other contexts.

## Related skills
- `modularize-project` — For broader architectural refactoring across multiple files/modules.
- Project conventions — Refer to the codebase's component naming, folder structure, and styling patterns.
