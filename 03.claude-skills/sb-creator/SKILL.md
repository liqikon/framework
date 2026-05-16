---
name: sb-creator
description: >
  HTML Screen Design Document (화면설계서/Wireframe) generator.
  Creates a single self-contained HTML file documenting all screens of a web application
  with monochrome wireframes, numbered annotation indicators, a sticky Description panel,
  tab/scroll navigation, and built-in PDF/PPTX export.
  Use when the user asks to: create a screen design document, wireframe document,
  화면설계서, UI specification, screen specification, screen blueprint,
  or any request to document multiple screens of a web application in a visual format.
---

# Screen Design Document Builder

Generate a single self-contained HTML file that documents all screens of a web application as monochrome wireframes with numbered annotation indicators and a sticky Description panel.

## Output Format

Single `.html` file. No external dependencies except Google Fonts (Pretendard) and dynamically-loaded CDN libs for PPTX export. Everything -- CSS, HTML, JS -- lives in one file.

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

### 4. Verify

- All tab buttons scroll to the correct section
- All indicator numbers have matching Description rows
- PDF download (window.print) works in landscape
- PPTX download captures all screens

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
- **PPTX export**: Dynamically loads `html2canvas@1.4.1` + `PptxGenJS@3.12.0` from CDN.

## Component Reference

See [references/components.md](references/components.md) for reusable HTML patterns: sidebar, header bar, stat cards, data tables, filter bars, form groups, badges, toggles, buttons, chat bubbles, and more.

## Template

Copy [assets/template.html](assets/template.html) as the starting skeleton. It includes all CSS, the cover page, tab navigation, sidebar template, and all JS functions (scroll, sidebar init, PDF/PPTX download).
