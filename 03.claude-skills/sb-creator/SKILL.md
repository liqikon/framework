---
name: sb-creator
description: >
  HTML Screen Design Document (화면설계서/Wireframe) generator.
  Creates a single self-contained HTML file documenting all screens of a web application
  with monochrome wireframes, numbered annotation indicators, a sticky Description panel,
  tab/scroll navigation, built-in PDF export, and an editable-PPTX export button auto-injected
  via the sb-creator-pptx skill at the end of generation.
  Use when the user asks to: create a screen design document, wireframe document,
  화면설계서, UI specification, screen specification, screen blueprint,
  or any request to document multiple screens of a web application in a visual format.
---

# Screen Design Document Builder

Generate a single self-contained HTML file that documents all screens of a web application as monochrome wireframes with numbered annotation indicators and a sticky Description panel.

## Output Format

Single `.html` file. No external dependencies except Google Fonts (Pretendard) and PptxGenJS (loaded on-demand from CDN by the injected editable-PPTX exporter). Everything -- CSS, HTML, JS -- lives in one file.

The template ships with a **PDF button only**. The **editable PPTX button** is added in the final step via `sb-creator-pptx`, so the generated file ends up with exactly one PDF button and one editable PPTX button — never an image-based PPTX.

## Workflow

### 1. Gather Screen List

Collect from user: project name, screen IDs (e.g. SCR-001), screen names, and a brief description of each screen's purpose and key UI elements.

### 2. Build the HTML

Copy `assets/template.html` as the starting point, then:

1. Update **cover page** metadata (project name, version, date, screen count, screen list).
2. Update **tab navigation** buttons to match the screen list.
3. Update **sidebar template** menu items to match the screen list.
4. For each screen, create a `<div class="screen-section" id="scr-NNN">` containing:
   - **meta-box**: screen ID badge, breadcrumb, description, date
   - **wireframe-wrap**: the monochrome wireframe using components from `references/components.md`
   - **desc-wrap**: a Description table annotating each numbered indicator

### 3. Add Indicators

Place `<div class="indicator" style="top:Ypx;left:Xpx;">N</div>` elements inside `.ind-container` wrappers. Each indicator number must correspond to a row in the Description table.

> **Author every wireframe so it survives PPTX conversion.** The Step 5 PptxGenJS exporter walks the live DOM and maps each element to a native shape/text box — it does NOT understand gradients, `aspect-ratio`, `calc()`, nested fl/grid centering, or text split across child spans. Wireframes built with raw fl/grid stacks render fine in HTML but come out garbled in PPTX (shifted boxes, "only the inner span" text, invisible light-on-light text). Follow [references/pptx-safe-authoring.md](references/pptx-safe-authoring.md) — solid colors, fixed-px absolute placement, single text leaves. This is mandatory for mobile device-frame mockups and any pixel-positioned layout.

### 4. Verify

- All tab buttons scroll to the correct section
- All indicator numbers have matching Description rows
- PDF download (window.print) works in landscape

### 5. Inject editable PPTX export (REQUIRED final step)

After the HTML is written, run the sb-creator-pptx injector so the only PPTX button in the file is the editable (PptxGenJS-based) one:

```bash
python3 ~/.claude/skills/sb-creator-pptx/scripts/inject.py <generated.html>
```

This auto-detects the cover's `<div class="download-btns ...">` and inserts the PPTX button **inside it, right next to the PDF button** (so both buttons sit at the cover's top-right). If the target HTML has no `.download-btns`, the injector falls back to a fixed top-right overlay. A `.bak.html` backup is created on each run. The template itself ships with no PPTX button, so the final file ends up with **one PDF button + one editable PPTX button** — never duplicates and no fixed header overlay.

Skip only if the user explicitly opts out of PPTX export.

## Design System

All wireframes use a **monochrome grayscale** palette:

| Token | Hex | Usage |
|-------|-----|-------|
| darkest | `#212529` | headings, primary text |
| dark | `#343a40` | sidebar bg, badge-dark, active tab |
| mid-dark | `#495057` | btn-dark, secondary text |
| mid | `#6c757d` | labels, badge-mid |
| border | `#ced4da` | input borders, badge-outline |
| light-border | `#dee2e6` | table borders, card borders |
| light-bg | `#e9ecef` | table headers, badge-light, hover |
| bg | `#f8f9fa` | page background, alternating rows |
| white | `#fff` | card backgrounds |
| accent | `#e67700` | indicator circles only |

Font: **Pretendard** (Google Fonts CDN). Fallback: system sans-serif.

## Key Constraints

- **Indicators**: Use `z-index:9999` but parent `.screen-section` has `position:relative; z-index:1;` to create a stacking context below the fixed header (`z-index:1000`).
- **Card overflow**: Must be `overflow:visible` so indicators aren't clipped.
- **Right panel**: Grid layout `1fr 400px`. Description panel is `position:sticky; top:52px;` with `max-height:calc(100vh - 60px); overflow-y:auto`.
- **Scroll nav**: Tab clicks use `scrollIntoView({ behavior:'smooth', block:'start' })`. Scroll spy highlights the active tab.
- **Description table**: No. column uses plain digits (1, 2, 3) in `#e67700`. Description column fixed at `240px`.
- **Print CSS**: `@page { size: landscape; }`, screens get `page-break-before: always`.
- **PPTX export**: Provided by the `sb-creator-pptx` skill (injected in Step 5). It dynamically loads `PptxGenJS@3.12.0` and converts DOM elements to native shapes/text (editable in PowerPoint). The sb-creator template itself emits **no** PPTX button — never bake one in or you'll end up with duplicates after injection.

## PPTX-Safe Authoring (read before building any pixel-positioned or mobile wireframe)

The editable-PPTX exporter (Step 5) converts the rendered DOM to native PowerPoint shapes. It has hard limitations — author around them or the PPTX comes out broken even when the HTML looks perfect:

| Don't | Why it breaks PPTX | Do instead |
|-------|--------------------|------------|
| `background: linear-gradient(...)` | Exporter falls back to the first color only | Solid `background:#RRGGBB` |
| `aspect-ratio: 3/4` | Not measured → zero/wrong height | Fixed `width`/`height` in px |
| `calc(...)` in positions | Not evaluated | Literal px values |
| Nested flex/grid for centering | Box offsets drift | `position:absolute` + fixed `left/top` inside a sized parent |
| Text split across children, e.g. `rodi-book<span>AX</span>` | Only the inner child renders | One text node per element |
| Light text on translucent `rgba(...,0.05)` card | Blends to near-white → invisible | Solid card color + readable text color |

For mobile app mockups, use the **device-frame pattern**: a fixed-size `.device` box with header / body / bottom-bar children placed by absolute px coordinates, and indicators positioned with literal px (not `calc()`) relative to the `.ind-container`. Full CSS + a worked example are in [references/pptx-safe-authoring.md](references/pptx-safe-authoring.md).

## Component Reference

See [references/components.md](references/components.md) for reusable HTML patterns: sidebar, header bar, stat cards, data tables, filter bars, form groups, badges, toggles, buttons, chat bubbles, and more.

For mobile / pixel-positioned wireframes, see [references/pptx-safe-authoring.md](references/pptx-safe-authoring.md) — the PPTX-safe device-frame CSS and component atoms (header, bottom bar, cover image, buttons, cards, inputs, banners).

## Template

Copy [assets/template.html](assets/template.html) as the starting skeleton. It includes all CSS, the cover page, tab navigation, sidebar template, and the JS for scroll/sidebar init and PDF download (window.print). It deliberately ships **without** any PPTX button — that gets injected by sb-creator-pptx in Step 5.
