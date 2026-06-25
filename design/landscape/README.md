# Handoff: ACW — The Landscape (Homepage Dashboard)

## Overview

This handoff covers the **homepage dashboard** ("The Landscape") for **Assistive Commons Watch (ACW)** — a living registry that tracks the health of open-source assistive technology projects. The page surfaces what's thriving, what needs attention, and where coverage gaps exist across disability areas.

## About the Design Files

The file `Landscape.dc.html` in this folder is a **high-fidelity interactive design reference** — a prototype showing intended look, content, and behavior. It is NOT production code to copy directly. Your task is to **recreate this design in your existing codebase** (whatever framework/stack ACW uses) using its established patterns and libraries. Treat this file as a pixel-accurate spec.

To open the prototype locally, you'll need the `support.js` runtime that ships with it. Simply open `Landscape.dc.html` in a browser (both files must be in the same folder).

## Fidelity

**High-fidelity.** Colors, typography, spacing, interactions, and copy are final. Recreate the UI faithfully — every measurement and color value below is exact.

---

## Design Tokens

### Colors (all in oklch — convert to hex/hsl for your stack)

| Token | oklch value | Role |
|---|---|---|
| `bg-page` | `oklch(0.97 0.012 76)` | Page background (warm off-white) |
| `bg-white` | `white` | Cards, header, hero, footer |
| `border` | `oklch(0.91 0.012 75)` | Default border |
| `border-subtle` | `oklch(0.94 0.008 75)` | Row dividers |
| `border-faint` | `oklch(0.97 0.006 75)` | Intra-card row dividers |
| `text-primary` | `oklch(0.18 0.025 50)` | Headlines |
| `text-secondary` | `oklch(0.42 0.02 50)` | Nav links, body |
| `text-muted` | `oklch(0.56 0.015 50)` | Labels, captions |
| `accent-green` | `oklch(0.43 0.14 165)` | Primary CTA, active tab underline, links |
| `accent-green-bg` | `oklch(0.94 0.06 165)` | About the data card background |
| `stat-green-bg` | `oklch(0.94 0.08 142)` | "Active or better" stat card bg |
| `stat-green-text` | `oklch(0.36 0.15 142)` | "Active or better" number |
| `stat-amber-bg` | `oklch(0.96 0.06 84)` | "Dormant" stat card bg |
| `stat-amber-text` | `oklch(0.44 0.10 84)` | "Dormant" number |

### Tier Colors

| Tier | Dot/block bg | Text on bg |
|---|---|---|
| Thriving | `oklch(0.52 0.16 142)` (green) | `white` |
| Stable | `oklch(0.50 0.14 245)` (blue) | `white` |
| Dormant | `oklch(0.72 0.13 83)` (amber) | `oklch(0.30 0.06 80)` |
| At Risk | `oklch(0.62 0.17 47)` (orange) | `white` |
| Archived | `oklch(0.52 0.14 22)` (red-brown) | `white` |
| Unverified | `oklch(0.80 0.02 250)` (cool grey) | `oklch(0.40 0.02 250)` |

### Typography

- **Font family:** `'Figtree'` (Google Fonts), weights 400/500/600/700/800. Fallback: `system-ui, sans-serif`.
- **Font import:** `https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700;800&display=swap`

| Usage | Size | Weight | Letter-spacing | Notes |
|---|---|---|---|---|
| Wordmark | 15px | 800 | -0.03em | |
| H1 hero | 40px | 800 | -0.03em | line-height 1.1 |
| H2 section | 26px | 800 | -0.025em | |
| Stat numbers | 32px | 800 | -0.04em | tabular-nums |
| Section label (eyebrow) | 11px | 700 | 0.09em | uppercase |
| Nav links | 13px | 500 | — | |
| CTA button | 13px | 600 | — | |
| Tab buttons | 14px | 400 active→600 | 0.01em | |
| Body / description | 16px | 400 | — | line-height 1.7 |
| Row labels | 14px | 600 | — | |
| Sub-labels / meta | 12px | 400 | — | |
| Tier badges | 10px | 700 | 0.03em | |
| Tier strip labels | 12px | 500 | — | |

---

## Screens / Views

### 1. Sticky Header

**Height:** 56px. `position: sticky; top: 0; z-index: 100`. White background, 1px bottom border (`border`).

Inner container: max-width 1200px, centered, 40px horizontal padding, flex row, `align-items: center`.

**Left: Wordmark**
- Text: "Assistive Commons Watch" — 15px, 800, -0.03em, `text-primary`
- Live badge: pill shape (`border-radius: 100px`), bg `oklch(0.94 0.07 142)`, padding 3px 8px, flex row with 5px gap
  - Animated dot: 6px circle, `oklch(0.50 0.17 142)`, pulse animation (opacity 1→0.2→1, 2s ease-in-out infinite)
  - Text: "LIVE", 10px, 700, 0.07em letter-spacing, uppercase, `oklch(0.33 0.14 142)`

**Right: Nav**
- Links: "Browse", "Recent Changes", "Needs Attention" — 13px, 500, `oklch(0.42 0.02 50)`, padding 7px 12px, border-radius 6px
- CTA button: "Submit a project →" — 13px, 600, white text, `accent-green` bg, padding 7px 15px, border-radius 7px, margin-left 8px

---

### 2. Hero Section

White background, 1px bottom border. Inner container: max-width 1200px, padding 52px 40px 44px. **CSS grid: `1fr 268px`, gap 52px**.

**Left column:**
- H1: "A live health registry for open-source assistive technology." — 40px, 800, -0.03em, line-height 1.1, `oklch(0.17 0.025 50)`. Has a `<br>` after "for".
- Body: 16px, line-height 1.7, `oklch(0.48 0.02 50)`, max-width 500px
- Meta row (flex, gap 8px, margin-top 20px): animated green dot (7px, 0.5s animation-delay) + "Last refreshed [date]" + separator "·" + "Data: CC0 (linked)"
  - Separator color: `oklch(0.82 0.01 75)`

**Right column: 2×2 stat grid** (gap 10px)

| Card | Bg | Value color | Label |
|---|---|---|---|
| Total projects | `oklch(0.97 0.012 76)` | `text-primary` | "Projects" |
| Areas | `oklch(0.97 0.012 76)` | `text-primary` | "Areas" |
| Active or better % | `oklch(0.94 0.08 142)` | `oklch(0.36 0.15 142)` | "Active or better" |
| Dormant count | `oklch(0.96 0.06 84)` | `oklch(0.44 0.10 84)` | "Dormant" |

Each stat card: padding 16px 18px, border-radius 10px. Number: 32px, 800, -0.04em, tabular-nums. Label: 12px, `oklch(0.52 0.02 50)`, 500, margin-top 3px.

---

### 3. Tier Strip

White background, 1px bottom border. Inner: max-width 1200px, padding 10px 40px, flex row, gap 6px, `overflow-x: auto`.

- "TIER BREAKDOWN" label: 11px, 700, 0.08em, uppercase, `oklch(0.60 0.015 50)`, margin-right 10px
- Per-tier pill (flex, gap 5px, padding 4px 10px, border 1px `oklch(0.90 0.01 75)`, border-radius 100px):
  - 7px dot in tier color
  - Tier name: 12px, 500, `oklch(0.35 0.02 50)`
  - Count: 12px, 700, tabular-nums, `oklch(0.38 0.02 50)`

Render only tiers with count > 0. Order: Thriving → Stable → Dormant → At Risk → Archived → Unverified.

---

### 4. Main Content Area

`max-width: 1200px`, padding 36px 40px 64px. **CSS grid: `1fr 304px`, gap 28px**, `align-items: start`.

#### Left: The Landscape Panel

**Section header (margin-bottom 26px):**
- Eyebrow: "PRIMARY VIEW", 11px, 700, 0.09em, uppercase, `accent-green`
- H2: "The Landscape", 26px, 800, -0.025em
- Description: 14px, `oklch(0.50 0.02 50)`

**Tab nav** (flex, gap 24px, border-bottom 1px `border`, margin-bottom 28px):

Three buttons: "By Disability Area" | "By Status" | "Coverage Gaps"

Active tab style: `border-bottom: 2px solid oklch(0.43 0.14 165)`, color `oklch(0.38 0.14 165)`, font-weight 600.
Inactive tab style: `border-bottom: 2px solid transparent`, color `oklch(0.50 0.02 50)`, font-weight 400.

All tabs: 14px, padding 10px 0, background none, no border except bottom, font-family inherit, cursor pointer, no outline.

---

#### Tab 0 — By Disability Area (default)

Introductory sentence (13px, `oklch(0.55 0.015 50)`, line-height 1.65, margin-bottom 20px).

**Per-area row** (flex, align-items center, gap 16px, padding 13px 0, border-bottom 1px `border-subtle`):
- Label column (width 196px, flex-shrink 0):
  - Area name: 14px, 600, `oklch(0.24 0.02 50)`
  - Count: 12px, `oklch(0.56 0.015 50)`, margin-top 2px, tabular-nums
- Blocks (flex, gap 5px, flex-wrap wrap, flex 1):
  - Each project = 36×28px rounded rect (border-radius 6px) in tier color
  - `title` attribute: `"{project name} — {tier label}"` (tooltip on hover)
  - Sorted: healthiest tier first (Thriving → Stable → Dormant → At Risk → Archived)

**Legend** (margin-top 20px, flex, gap 14px, flex-wrap wrap):
- "KEY" label: 11px, 700, 0.07em, uppercase, `oklch(0.58 0.015 50)`
- Per tier: 12×12px square (border-radius 3px) in tier color + 12px label `oklch(0.45 0.02 50)`

**Data (18 projects):**
```
AAC / Communication (4): cboard→Thriving, AsTeRICS-Grid→Thriving, speakeasy-aac→Dormant, otsimo/aac→Archived
Eye Gaze / Tracking (3): OptiKey→Thriving, asterics/eye-lcos-tracker→Dormant, iGaze→Dormant
Motor / Switch Access (5): LipSync→Thriving, OpenAT-Joysticks→Thriving, FABI→Stable, FLipMouse→Stable, switchboard→Dormant
Vision / Braille (2): NVDA→Thriving, BrailleTouch→Dormant
Hearing (2): Tympan_Library→Stable, hearingaid-prototype→Dormant
Prosthetics / Rehab (2): opensourceleg→Thriving, OpenBionics/Prosthetic-Hands→Dormant
```

---

#### Tab 1 — By Status

Grid layout: `200px 1fr`, gap 40px, align-items start.

**Left: Donut chart** (180×180px circle):
- Rendered as a CSS `conic-gradient` using tier colors proportional to count
- Center hole: 112×112px white circle, `box-shadow: 0 0 0 1px oklch(0.91 0.01 75)`, flex-column centered
  - Number: 28px, 800, -0.04em, tabular-nums
  - Label: 11px, `oklch(0.56 0.015 50)`, 500
- Caption below: 12px, `oklch(0.55 0.015 50)`, centered, line-height 1.5

**Right: Tier legend rows** (flex-column, gap 8px):
Per tier card (flex, gap 12px, padding 12px 14px, bg `oklch(0.98 0.008 76)`, border-radius 9px):
- 30×30px square (border-radius 7px) in tier color
- Right: tier name (14px, 700) + count (14px, 800) side by side with 8px gap
- Below: tier description (12px, `oklch(0.54 0.015 50)`, line-height 1.5)

**Tier descriptions:**
- Thriving: "Active, documented, welcoming"
- Stable: "Works, maintained passively, usable"
- Dormant: "Documented to replicate, inactive"
- Archived: "Explicitly archived or abandoned"

---

#### Tab 2 — Coverage Gaps

Intro text (13px, muted, line-height 1.65, margin-bottom 20px).

**Per-area row** (flex, align-items center, gap 14px, padding 14px 0, border-bottom 1px `border-subtle`):
- Label column (width 196px):
  - Area name: 14px, 600
  - Sub-label: 12px, muted — "{total} total · {activeN} active"
- Progress bar (flex 1, height 8px, bg `oklch(0.92 0.01 75)`, border-radius 100px, overflow hidden, position relative):
  - Fill: `oklch(0.45 0.14 165)`, width = `(total / maxTotal) * 100%`, same border-radius
- Badge (min-width 88px, flex justify-end):
  - **Sparse** (≤2 projects): bg `oklch(0.96 0.07 47)`, text `oklch(0.44 0.15 47)`, "⚑ Sparse"
  - **Moderate** (3 projects): bg `oklch(0.96 0.05 84)`, text `oklch(0.46 0.10 84)`, "◑ Moderate"
  - **Covered** (≥4 projects): bg `oklch(0.93 0.08 142)`, text `oklch(0.36 0.15 142)`, "✓ Covered"
  - Badge style: padding 3px 9px, border-radius 100px, 11px, 700, 0.03em letter-spacing

**Priority callout** (margin-top 24px):
- bg `oklch(0.97 0.05 47)`, border-radius 10px, padding 16px 18px
- Left accent border: 3px solid `oklch(0.62 0.17 47)`
- Title: 13px, 700, `oklch(0.40 0.13 47)`, margin-bottom 5px
- Body: 13px, `oklch(0.44 0.08 47)`, line-height 1.65

---

#### Right Sidebar (304px wide, flex-column, gap 18px)

**Card shell** (white, border-radius 12px, border 1px `border`, overflow hidden):

**Card 1 — Needs Attention**

Header (padding 14px 18px, border-bottom 1px `border-subtle`, flex row, gap 8px):
- 8px orange dot (`oklch(0.62 0.17 47)`)
- "Needs Attention" label: 13px, 700
- Spacer
- Count: 12px, muted

Per item (padding 14px 18px, border-bottom 1px `border-faint`):
- Row 1: project name (13px, 600, line-height 1.4) + tier badge (right-aligned, pill)
- Row 2: area name (11px, 500, uppercase, 0.04em, muted)
- Row 3: note text (12px, `oklch(0.48 0.07 47)`, line-height 1.55)

Items:
1. **iGaze** · Eye Gaze · Dormant — "Last commit 5+ years ago — approaching abandonment"
2. **OpenBionics/Prosthetic-Hands** · Prosthetics · Dormant — "No build docs; sole dormant project in a sparse area"
3. **hearingaid-prototype** · Hearing · Dormant — "Only 2 hearing projects — critical coverage gap"

Footer link: "View all needs attention →", 13px, 600, `accent-green`

**Card 2 — Recently Added**

Header (padding 14px 18px, border-bottom 1px `border-subtle`): "Recently Added", 13px, 700

Per item (padding 12px 18px, border-bottom 1px `border-faint`, flex, justify-content space-between, gap 10px):
- Left: project name (13px, 600, truncate) + area · date (11px, muted, margin-top 2px)
- Right: tier badge pill

Items:
1. **opensourceleg** · Prosthetics / Rehab · Jun 2026 · Thriving
2. **OpenAT-Joysticks** · Motor / Switch Access · May 2026 · Thriving
3. **AsTeRICS-Grid** · AAC / Communication · Apr 2026 · Thriving

Footer link: "View all recent changes →", 13px, 600, `accent-green`

**Card 3 — About this data** (no card shell — colored bg directly)

bg `oklch(0.94 0.06 165)`, border-radius 12px, padding 18px 20px.
- Title: 13px, 700, `oklch(0.26 0.12 165)`, margin-bottom 7px — "About this data"
- Body: 12px, `oklch(0.37 0.10 165)`, line-height 1.65
- Link: 12px, 600, `oklch(0.35 0.13 165)`, margin-top 10px — "Read the methodology →"

---

### 5. Footer

White background, 1px top border. Padding 20px 40px. Inner: max-width 1200px, flex row, space-between, flex-wrap, gap 12px.

- Left: 12px, `oklch(0.56 0.015 50)` — "Assistive Commons Watch · Data CC0 · Score methodology v1.0" (CC0 and v1.0 are links)
- Right: flex row, gap 16px — links "GitHub" | "About" | "API" | "Submit", 12px, `oklch(0.52 0.015 50)`

---

## Interactions & Behavior

### Tab switching
- Three tabs: "By Disability Area" (default), "By Status", "Coverage Gaps"
- Switching tab replaces the main panel content (no animation required, or use a simple fade-in)
- Active tab: green underline + green text + bold
- Inactive tab: transparent underline + muted text + normal weight

### Live pulse dot
- CSS animation `pulse-dot`: opacity oscillates 1→0.2→1 over 2s, ease-in-out, infinite
- Header badge dot: no delay. Hero meta dot: 0.5s delay.

### Project block tooltips
- Each colored block in Tab 0 has a native HTML `title` attribute with format: `"{name} — {tier}"`
- No custom tooltip needed unless your stack makes it easy

### Links
- All sidebar "View all …" links and footer links are navigation — wire to real routes in your app

---

## State Management

- `activeTab: number` (0 | 1 | 2) — local UI state, no persistence needed
- All stats, tier distributions, area rows, needs-attention, and recently-added lists are **computed from the project registry** at render time — no separate state for those
- The design uses a static seed of 18 projects; in production these come from your data layer

---

## Data Model

Each project record needs:
```ts
{
  id: string
  name: string
  area: 'aac' | 'eyegaze' | 'motor' | 'vision' | 'hearing' | 'prosthetics'
  tier: 'thriving' | 'stable' | 'dormant' | 'at-risk' | 'archived' | 'unverified'
}
```

The sidebar "Needs Attention" and "Recently Added" items are derived from the registry — filter by tier and sort by date added.

---

## Assets

No external images or icons used. All visual elements are CSS shapes and text. The tier color system is purely CSS. No icon library required.

---

## Files in This Package

| File | Purpose |
|---|---|
| `README.md` | This document — the full implementation spec |
| `Landscape.dc.html` | Interactive hi-fi prototype — open in browser to reference the live design |
