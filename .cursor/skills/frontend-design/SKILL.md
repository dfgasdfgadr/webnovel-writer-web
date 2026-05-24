# Frontend Design Skill

This skill guides the creation of distinctive, production-grade frontend interfaces. It avoids generic "AI slop" aesthetics and instead produces unique visual directions with careful attention to typography, color, spacing, and motion.

## When to Use

Invoke this skill for any frontend task involving:
- New pages, components, or layouts
- Visual redesign or restyling
- Design system decisions (color, typography, spacing)
- UI polish and refinement

## Design Principles

### 1. Distinctive visual direction
- Avoid default Inter/Roboto fonts. Choose distinctive typefaces that match the product's personality
- Develop a unique color identity — don't default to blue/purple gradients
- Use intentional asymmetry, negative space, and layout rhythm

### 2. Typography hierarchy
- Headings: Serif or distinctive display fonts for brand personality
- Body: Clean sans-serif optimized for reading
- Establish clear type scale with at least 5 levels
- Use proper line-height and letter-spacing

### 3. Color & theme
- Dark-first for editor/workbench products
- Accent colors should be purposeful, not decorative
- Use CSS custom properties for theme consistency
- Ensure WCAG AA contrast ratios

### 4. Spacing & density
- High-density for data-heavy workspaces (editors, dashboards)
- Low-density for marketing/onboarding flows
- Consistent spacing scale (4px base unit)

### 5. Motion & interaction
- Subtle transitions (150-200ms) for UI state changes
- Avoid bouncy/spring animations for work tools
- Loading states: skeleton screens over spinners
- Hover/press micro-interactions for interactive elements

### 6. Component states
- Every interactive component must handle: default, hover, active, focus, disabled, loading, error, empty
- Empty states should guide the user to their next action
- Error states should explain what happened and how to fix it

## Shadcn/ui Integration

- Use shadcn/ui components as building blocks, not finished design
- Customize through CSS variables in tokens.css
- Compose components for complex layouts (e.g., Card + Badge + DropdownMenu for project cards)

## NovelCraft-Specific Guidelines

- **Dark-first**: The editor workbench defaults to dark mode
- **Amber accent**: AI/action elements use amber; success/approved uses emerald
- **Font stack**: Headings use Noto Serif SC; body uses Geist/Source Han Sans SC
- **Density**: Writing workspace is high-density; wizards/settings are relaxed
- **Keyboard shortcuts**: Writing tools need visible shortcut hints
- **SSE streaming**: Subtle pulse animation for streaming text; no bounce

## Anti-Patterns (Avoid)

- Default shadcn theme without customization
- Inter/Roboto as the only font
- Blue/purple as the primary accent (use amber for NovelCraft)
- Over-animated interfaces for productivity tools
- Missing empty/loading/error states
- Placeholder lorem ipsum in production screens
