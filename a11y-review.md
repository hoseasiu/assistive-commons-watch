# Accessibility Review — Assistive Commons Watch
**Standard:** WCAG 2.1 AA | **Audited:** 2026-06-29  
**Pages:** `site/index.njk`, `site/browse.njk`, `site/projects.njk`, `site/about.njk`, `site/_includes/base.njk`

---

## Critical

- [ ] **[index.njk] Add `<main id="main-content">` to the homepage**  
  The homepage has no `<main>` landmark at all — the body goes straight into `<section class="hero">`.  
  The skip link in `base.njk` (`href="#main-content"`) lands nowhere. Wrap all three sections  
  (`hero`, `path-section`, `landscape-section`) in `<main id="main-content">`.  
  **WCAG 2.4.1, 4.1.2**

- [ ] **[browse.njk] Add `id="main-content"` to the existing `<main>` tag (line 348)**  
  `<main>` exists but has no id, so the skip link fails silently.  
  **WCAG 2.4.1**

- [ ] **[base.njk] Fix mobile navigation — all nav links vanish at ≤640px**  
  `@media (max-width: 640px) { .site-nav a:not(.nav-cta) { display: none; } }` removes Contribute,  
  Find a Tool, and About — leaving only the Submit CTA and the wordmark. AT and keyboard users on  
  mobile have no way to navigate between sections. Add a hamburger button that expands a drawer, or  
  allow the nav links to wrap instead of hiding.  
  **WCAG 2.1.1**

---

## Major

- [ ] **[index.njk + browse.njk] Add arrow-key navigation to both tab widgets**  
  Both `role="tablist"` widgets only attach a `click` handler. The ARIA authoring pattern requires:
  - Left/Right arrows move focus between tab buttons
  - Inactive tabs get `tabindex="-1"`, active tab gets `tabindex="0"`
  - Tab key exits the tablist (moves to the panel or next focusable element)  
  
  A small shared helper can cover both; the landscape tabs are in `index.njk:624–636` and the  
  mode tabs in `browse.njk:1046–1062`.  
  **WCAG 2.1.1**

- [ ] **[browse.njk] Add `aria-controls` to mode tab buttons**  
  The `role="tab"` buttons (lines 337–343) have no `aria-controls` attribute, so the relationship  
  between the tab and its controlled content region is undeclared. Add  
  `aria-controls="browse-results"` to each and `id="browse-results"` to the `.results-area` div.  
  **WCAG 4.1.2**

- [ ] **[index.njk] Name the three `<section>` landmarks**  
  Unnamed sections are skipped in landmark navigation. Add `aria-labelledby` pointing to each  
  section's heading:
  - `<section class="hero" aria-labelledby="hero-heading">` + `id="hero-heading"` on `.hero-h1`
  - `<section class="path-section" aria-labelledby="path-heading">` + `id="path-heading"` on `.path-section-h2`
  - `<section class="landscape-section" aria-labelledby="landscape-heading">` + `id="landscape-heading"` on `.section-h2`  
  
  **WCAG 1.3.1**

- [ ] **[base.njk] Darken footer text and links**  
  Footer text (`--text-muted` = `oklch(0.56)`, 12px) and footer links (`oklch(0.52)`, 12px) on  
  white both fall around 3.5:1 — below the 4.5:1 threshold for normal text. Use  
  `var(--text-secondary)` (`oklch(0.42)`) or darker for both.  
  **WCAG 1.4.3**

- [ ] **[index.njk + projects.njk] Fix contrast on 10px sub-labels**  
  `.stat-sublabel` (index.njk:56, color `oklch(0.60)` at 10px) and `.pill-weight`  
  (projects.njk:170, `opacity: 0.65` at 10px) both fail the 4.5:1 ratio by a large margin.  
  Options: raise to ≥12px, darken the color to ≥`oklch(0.38)`, or mark as decorative and  
  move the information elsewhere.  
  **WCAG 1.4.3**

---

## Minor

- [ ] **[index.njk] Add visible or screen-reader-accessible percentage to coverage gap bars**  
  `.gap-bar-fill` widths (Tab 2 — Coverage Gaps) are set via `style="width:{{ barPct }}%"` but  
  no numeric text is shown. The badge (Sparse / Moderate / Covered) gives a category but not  
  the value. Add a visually-hidden `<span class="sr-only">{{ barPct }}%</span>` beside each bar,  
  or include the number in the `.gap-sub` text.  
  **WCAG 1.3.1**

- [ ] **[browse.njk] Add `aria-label` to SSR score-dots container**  
  The server-rendered project cards (lines 595–610) don't have an `aria-label` on the  
  `.score-dots` wrapper. JS re-renders them with a proper label  
  (`aria-label="Availability: X of 5, Momentum: Y of 5"`), but there's a flash where the  
  unlabelled version is visible. Mirror the JS label in the Nunjucks template.  
  **WCAG 1.3.1**

- [ ] **[base.njk] Increase footer link touch targets to 44×44px**  
  `.footer-links a` has no minimum height. Add  
  `min-height: 44px; display: inline-flex; align-items: center;` to meet the touch target  
  requirement.  
  **WCAG 2.5.5**

- [ ] **[projects.njk] Replace inline `onmouseover`/`onmouseout` handlers with CSS on ecosystem links**  
  Lines 490–492 use inline event handlers for hover styling. No `:focus-visible` state is  
  defined for these links. Convert to a CSS class with `:hover, :focus-visible` rules so  
  keyboard users get the same visual feedback.  
  **WCAG 2.4.7**

---

## Contrast Reference

| Element | Color | Size | Est. ratio | Required | Status |
|---------|-------|------|------------|----------|--------|
| Body text | `--text-secondary` oklch(0.42) | 16px | ~6:1 | 4.5:1 | ✅ |
| Accent green links | oklch(0.43 0.14 165) | varies | ~5.1:1 | 4.5:1 | ✅ |
| Tier-pill text | oklch(0.35) | 12px | ~7:1 | 4.5:1 | ✅ |
| Gap badge text | oklch(0.44 0.15 47) | 11px | ~5:1 est. | 4.5:1 | ✅ |
| Inactive tab labels | oklch(0.50) | 14px | ~4.2:1 | 4.5:1 | ⚠️ borderline |
| Footer text/links | oklch(0.52–0.56) | 12px | ~3.5:1 | 4.5:1 | ❌ |
| `stat-sublabel` | oklch(0.60) | 10px | ~2.7:1 | 4.5:1 | ❌ |
| `pill-weight` | oklch + opacity 0.65 | 10px | <3:1 | 4.5:1 | ❌ |

*Ratios are estimates from oklch values — verify with browser DevTools or a contrast checker against live rendered output before closing tickets.*
