---
name: Previsão de Ondas — Pernambuco
description: Painel de previsão de ondas, vento e maré para a costa de Pernambuco, com classificação por referência histórica e alertas
colors:
  bg: "#0a1a28"
  bg-panel: "#123049"
  bg-panel-alt: "#0e2538"
  bg-row-alt: "#16354f"
  border: "#2a4d6b"
  border-strong: "#3a6690"
  text: "#f2f8fc"
  text-dim: "#9bb6c9"
  accent: "#5bd0f0"
  accent-strong: "#7ee0ff"
  scale-grande: "#f0922f"
  scale-extrema: "#e8452f"
typography:
  display:
    fontFamily: "Fraunces, Georgia, 'Times New Roman', serif"
    fontSize: "2.15rem"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "-0.01em"
  headline:
    fontFamily: "Fraunces, Georgia, 'Times New Roman', serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: "-0.01em"
  body:
    fontFamily: "Inter, 'Segoe UI', Roboto, Arial, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Inter, 'Segoe UI', Roboto, Arial, sans-serif"
    fontSize: "0.78rem"
    fontWeight: 600
    letterSpacing: "0.03em"
rounded:
  sm: "6px"
  md: "8px"
  lg: "12px"
spacing:
  sm: "8px"
  md: "16px"
  lg: "20px"
  xl: "24px"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.bg}"
    rounded: "{rounded.sm}"
    padding: "9px 18px"
  button-primary-hover:
    backgroundColor: "{colors.accent-strong}"
    textColor: "{colors.bg}"
  tab-active:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.bg}"
    rounded: "{rounded.sm}"
  panel:
    backgroundColor: "{colors.bg-panel}"
    textColor: "{colors.text}"
    rounded: "{rounded.lg}"
---

# Design System: Previsão de Ondas — Pernambuco

## Overview

**Creative North Star: "The Harbor Watch"**

The site reads like an operations board a harbor master or bridge officer would
actually stand in front of: the live condition signal comes first, full width,
color-coded to the Escala de Ondas em Pernambuco class, and only Grande/Extrema
earn a color shift (amber, then red) — everything below Grande stays in the
navy/cyan family so the page never turns into a rainbow of false urgency. Below
that status strip, a real CSS grid replaces the single stacked column: a
utility rail (alerts signup, escala methodology) sits beside the week-at-a-
-glance summary, and the technical series (wave, energy/power, wind,
temperature, tide) form their own two-column grid instead of one long scroll.
The product's differentiator is scientific rigor and transparency (ECMWF Open
Data, DHN tide tables, real physics formulas), not visual restraint for its
own sake — density is a feature, so the system commits to instrument-panel
precision (tabular numerals everywhere, hairline dividers, small-multiple
charts) rather than a minimal consumer-app look.

**Key Characteristics:**
- Condition-first hierarchy: the status strip is the page's real headline, not a decorative hero.
- Reserved-alert-color discipline: only Grande/Extrema shift the palette toward amber/red.
- True grid layout, not a stack: an aside rail, a primary week view, and a technical charts grid replace the single flex column.
- Instrument-grade micro-typography: tabular numerals, compact chart-axis labels, dense data-viz conventions.
- Editorial display type (Fraunces) reserved for numerals and page/panel identity; Inter carries everything functional.

## Colors

Dark navy ground with a single cyan accent; amber and red exist only as reserved severity signals, never as general-purpose accents.

### Primary
- **Signal Cyan** (`#5bd0f0` / accent-strong `#7ee0ff`): links, active tab state, primary buttons, chart accents, focus rings, selection color. The one color that means "interactive" or "highlighted" anywhere on the page.

### Neutral
- **Deep Navy** (`#0a1a28`): page background, the "water at depth" ground the whole system sits on.
- **Panel Navy** (`#123049` → `#0e2538` gradient): panel surfaces, status strip default state.
- **Row Navy** (`#16354f`): zebra striping on dense tables (tide table, scale table).
- **Border Navy** (`#2a4d6b` / strong `#3a6690`): hairline dividers, panel borders, table rules.
- **Ice Text** (`#f2f8fc`): primary text and headline numerals.
- **Muted Slate** (`#9bb6c9`): secondary text, captions, chart tick labels.

### Reserved Severity
- **Grande Amber** (`#f0922f`): status strip and sea-condition border/tint when the forecast crosses into "Grande".
- **Extrema Red** (`#e8452f`): same treatment, one step more urgent, for "Extrema".

### Named Rules
**The Reserved-Alert Rule.** Muito baixa / Baixa / Normal never receive their own color — they stay in the navy/cyan neutral system. Only Grande and Extrema are allowed to shift the page's palette (amber, then red). Adding color to any other class turns the scale into a meaningless rainbow and defeats its purpose as a genuine severity signal.

## Typography

**Display Font:** Fraunces (with Georgia, Times New Roman, serif fallback)
**Body Font:** Inter (with Segoe UI, Roboto, Arial, sans-serif fallback)

**Character:** Fraunces gives numerals and identity text an editorial, slightly warm authority against an otherwise instrument-panel-cold interface; Inter carries every functional and data-dense surface because it holds up at very small sizes without losing legibility.

### Hierarchy
- **Display** (600, 2.15rem, 1.1): the single most important number on the page — the first "Onda" stat in the status strip.
- **Headline** (600, 1.5rem, 1.15): the product name in the status strip; the sea-condition class value (1.7rem).
- **Title** (700, 0.9rem): panel titles. Sentence case, never uppercase — panel titles here run long ("Altura, período e direção das ondas (de onde vêm)") and all-caps destroys word-shape legibility at that length.
- **Body** (400, 1rem, 1.5): paragraphs, form copy, footer methodology text.
- **Label** (600, 0.78rem, 0.03em tracking): stat labels, table headers, fieldset legends — short (1-3 words) uppercase captions only.

### Named Rules
**The No Long Caps Rule.** Uppercase + letter-spacing is reserved for labels under ~15 characters. A panel title, sentence, or any string that runs longer stays in sentence case — the type carries hierarchy through weight and color, not through shouting.

## Layout

The page runs three structural bands, each a real CSS grid rather than a flex column:

1. **Status strip** (`header.status-strip`, full width, no max-width cap on the background — content capped at 1400px): brand + place selector on top, the live numeric readout plus escala condition box below, a fine-print footer line last. Background tints toward amber/red via `[data-scale-class]` when the forecast crosses Grande/Extrema.
2. **Intro grid** (`.dashboard-grid`, `minmax(280px,340px) 1fr`, collapses to one column under 900px): an aside rail (alerts signup, escala methodology) beside the week-at-a-glance primary panel.
3. **Charts grid** (`main`, 2 equal columns, collapses to one column under 900px): five technical panels. The richest one (wave height/period/direction, 4 tabs) spans both columns (`.panel-wide`); energy/power pairs with wind; temperature pairs with the tide panel. Every chart keeps its own internal horizontal scroll (`.chart-scroll`), so halving a panel's width only changes how much timeline is visible before scrolling — never a data loss.

Spacing rhythm: 20px gaps between grid siblings, 24px page gutters, panel interiors padded 12–18px. Chart columns are a fixed 34px (bar + label stack); this is a hard constraint from the multi-day hourly time series, not a spacing choice.

## Elevation & Depth

Panels sit on a soft gradient card (`var(--bg-panel)` → `var(--bg-panel-alt)`) with a 1px border and a diffuse ambient shadow (`0 8px 24px rgba(0,0,0,0.22)`). This is a pre-existing, user-confirmed treatment from the v1 redesign — depth is ambient (a panel "floats" slightly off the navy ground), not structural or interactive; shadows do not respond to state.

### Shadow Vocabulary
- **Panel ambient** (`box-shadow: 0 8px 24px rgba(0,0,0,0.22)`): every `.panel`, applied at rest, never on hover.

## Shapes

12px radius on panels and the status strip's internal condition box; 6px on buttons, selects, inputs, and tabs; 8px on the alerts fieldset and the sea-condition box. Borders are always 1px hairline in the border-navy family — no double borders, no colored border-left accents on cards or list rows.

## Components

### Buttons
- **Shape:** 6px radius.
- **Primary** (`.alerts-submit-btn`, active `.scale-toggle-btn`/`.tab-btn`): cyan background (`#5bd0f0`), navy text, 700 weight, 9–18px padding.
- **Secondary** (`.scale-toggle-btn` / `.tab-btn` at rest): panel-alt background, cyan-strong text, 1px border-strong.
- **Hover:** background shifts to `accent-strong` (`#7ee0ff`); no transform, no shadow change.

### Cards / Panels
- **Corner style:** 12px.
- **Background:** panel gradient (see Elevation).
- **Border:** 1px `var(--border)`.
- **Internal padding:** 12–18px for the title bar, 12–16px for body content.
- **Never nest a panel inside another panel** — the aside rail's alerts toggle button sits directly on the page ground; only the panel it reveals (`.alerts-panel`) carries card chrome.

### Inputs / Fields
- **Style:** panel-alt background, 1px `border-strong`, 6px radius, Inter body text.
- **Disabled** (e.g. the SMS phone field before the checkbox is checked): 0.45 opacity, no other treatment change.
- **Error / success messages:** tinted background + matching border + matching text color (green family for success, red family for error) — never color alone.

### Navigation (tabs)
- **Style:** small pill-ish rectangular buttons (6px radius), panel-alt background at rest, cyan fill + navy text + 700 weight when active. Wraps to a second line on narrow panels rather than overflowing.

### Status Strip (signature component)
- Full-width band, condition-reactive background (`data-scale-class` 0–4; only 3 and 4 change the gradient/tint).
- Left: SVG wave mark + product name (Fraunces) + one-line descriptive byline (never an uppercase kicker above the name — see Typography's No Long Caps Rule).
- Right: place selector.
- Below: the numeric readout row (first stat visually larger — the one number a decision-maker reads in under two seconds) plus the escala condition box, which only appears when the user has opted into the classification (`#scale-toggle-btn`).

## Do's and Don'ts

### Do:
- **Do** keep Muito baixa/Baixa/Normal in the neutral navy/cyan palette; reserve amber/red strictly for Grande/Extrema (`the Reserved-Alert Rule`).
- **Do** use Fraunces only for numerals and top-level identity text; everything functional stays in Inter.
- **Do** keep panel titles in sentence case regardless of length (`the No Long Caps Rule`).
- **Do** preserve every chart's internal horizontal scroll when placing it in a narrower grid column — never truncate or resample the underlying series.
- **Do** theme browser-native surfaces (selection, scrollbar, focus ring) from the palette rather than leaving OS defaults.

### Don't:
- **Don't** add a kicker/eyebrow label above a heading — delete it and let the heading's own weight carry hierarchy.
- **Don't** nest `.panel` chrome inside another `.panel`.
- **Don't** use emoji or Unicode glyphs as the icon system — the brand mark and alert bell are authored inline SVG; direction arrows on charts are a data encoding, not decoration, and stay as rotated glyphs.
- **Don't** let a single technical chart panel span less than half the grid on desktop — two-up is the floor for the technical grid; never three or more per row, which would crush the 34px-column charts below usability.
