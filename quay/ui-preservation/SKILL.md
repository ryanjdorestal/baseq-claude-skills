---
name: quay-ui-preservation
description: Preserve the Base44 visual baseline while upgrading the QUAY UI. Defines what a "visual upgrade" is allowed to change, what it must not change, and how to verify.
---

# QUAY UI Preservation and Upgrade Rules

## Purpose

The Base44 cloned app is the **visual contract** for QUAY today. Members, staff, and stakeholders have seen it; trust is built on continuity. This skill defines the rules for changing the UI: what is preserved by default, what is allowed to evolve, and how to verify a change before it ships.

## When to use

- Any PR that touches a page, layout, component, theme, or design token.
- Any "let's modernize this" or "let's tighten this up" task.
- Any AI-generated UI scaffolding that's about to land in the app.
- Before adding a new component library, theme, or CSS framework.

Do **not** use it for backend-only changes that have no visible effect.

## Expected inputs

1. **Page or component** being changed (path + route).
2. **Reason for the change** — bug, accessibility, content, feature, or deliberate visual upgrade.
3. **Before screenshots** — every viewport that's about to change.
4. **Scope** — single component, single page, design system, or theme-wide.

## Output format

For each change:

1. **Before/after screenshots** at desktop (≥1280) and mobile (375) for every affected page.
2. **Diff note** in the PR description: what's preserved, what's intentionally changed, why.
3. **Token changes** (if any) called out separately — token edits are global by definition.
4. **Accessibility delta** — any change to contrast, focus order, keyboard reachability, or aria.

## Rules of preservation

**Preserved by default** (changing requires an explicit "visual upgrade" callout in the PR):

- Page composition: hero → nav → content blocks in the same order.
- Primary colors, font family, font scale, and spacing scale.
- Iconography style and weight.
- Empty states' copy and tone.
- Microcopy on primary CTAs.
- Loading and error states' shape (skeleton vs. spinner, banner vs. modal).

**Allowed to evolve** (still calls for a screenshot diff, but does not need a "visual upgrade" callout):

- Bug fixes that restore the original Base44 intent.
- Accessibility fixes (contrast, focus rings, aria labels, keyboard order).
- Content updates (member names, cohort numbers, dates).
- Adding *new* surfaces that don't replace existing ones.
- Performance changes invisible to a sighted user (lazy-loading, image format).

**Deliberate visual upgrade** (requires explicit approval + a design note):

- New token values (color, spacing, radius, shadow).
- New typography scale or family.
- New layout primitives that replace existing ones.
- Component-library swap.

## Constraints

- The Base44 baseline is **not** a starting point to drift from. It is the contract until a deliberate visual upgrade lands.
- Component refactors that "look the same" but rewrite the markup must produce a pixel-similar screenshot diff at the same viewports.
- No silent token edits — every change to `tokens.css` / theme is a PR of its own with screenshots of three representative pages.
- No new utility CSS classes that duplicate existing ones; extend the existing token set.

## Anti-patterns

- "I cleaned up the Tailwind classes" PR with no screenshots.
- AI-generated component that looks fine in isolation but breaks the page rhythm.
- Replacing the existing button with a "better" button from a different library.
- Swapping the empty-state illustration because "it looked dated."
- Quiet font-stack change inside a CSS reset.

## Checklist

- [ ] Before screenshots captured at desktop + mobile for every affected page.
- [ ] After screenshots captured at the same viewports.
- [ ] Diff note in PR body: preserved / intentionally changed / why.
- [ ] No token changes — or, if there are, listed explicitly with screenshots of 3 representative pages.
- [ ] No accessibility regression (contrast, focus, keyboard).
- [ ] No new dependency for styling without justification.
- [ ] PR description tagged `visual-upgrade` if scope qualifies.

## Example prompt

> Review this PR against `skills/quay/ui-preservation/SKILL.md`. List anything that's a visual upgrade vs. preserved-by-default. Flag any token changes. Do not modify the code; just produce the diff note I should paste into the PR description.
