# Reusable Wireframe Components

Copy-paste these HTML patterns when building screen wireframes. All components use the monochrome design system defined in the template CSS.

## Table of Contents

- [Screen Section Skeleton](#screen-section-skeleton)
- [Indicator](#indicator)
- [Header Bar](#header-bar)
- [Stat Cards Row](#stat-cards-row)
- [Data Table](#data-table)
- [Filter Bar](#filter-bar)
- [Form Group](#form-group)
- [Badges](#badges)
- [Toggle Switch](#toggle-switch)
- [Buttons](#buttons)
- [Chat Bubble](#chat-bubble)
- [Sidebar Menu Item](#sidebar-menu-item)
- [Gauge Ring (SVG)](#gauge-ring-svg)
- [Tab Group](#tab-group)
- [Description Table](#description-table)

---

## Screen Section Skeleton

```html
<div class="screen-section" id="scr-NNN">
  <!-- Meta Box (spans full grid width) -->
  <div class="meta-box" style="margin:8px 24px 0 24px;">
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
      <span class="screen-id-badge">SCR-NNN</span>
      <span class="breadcrumb">Admin > Section > <strong>Screen Name</strong></span>
    </div>
    <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px;">
      <div><span class="meta-label">DESCRIPTION</span><div class="meta-value">Screen description here</div></div>
      <div><span class="meta-label">LAST UPDATED</span><div class="meta-value">2026-04-21</div></div>
      <div><span class="meta-label">STATUS</span><div class="meta-value"><span class="badge badge-dark">Design Complete</span></div></div>
    </div>
  </div>

  <!-- Wireframe (grid column 1) -->
  <div class="wireframe-wrap" style="padding:20px 24px;">
    <div class="ind-container" style="display:flex; gap:0; min-height:600px; border:1px solid #dee2e6; border-radius:10px; overflow:visible;">
      <!-- Sidebar + Main content here -->
    </div>
  </div>

  <!-- Description Panel (grid column 2, sticky) -->
  <div class="desc-wrap">
    <h3 style="font-size:14px; font-weight:700; color:#343a40;">Description</h3>
    <table class="desc-table">
      <thead><tr><th>No</th><th>Element</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td class="num">1</td><td>Element name</td><td>What this element does</td></tr>
      </tbody>
    </table>
  </div>
</div>
```

---

## Indicator

Orange numbered circle. Place inside an `.ind-container` element.

```html
<div class="indicator" style="top:12px; left:80px;">1</div>
```

---

## Header Bar

Top bar inside the main content area (right of sidebar).

```html
<div style="padding:16px 24px; border-bottom:1px solid #e9ecef; display:flex; justify-content:space-between; align-items:center;">
  <h2 style="font-size:18px; font-weight:700; color:#212529; margin:0;">Page Title</h2>
  <div style="display:flex; gap:8px;">
    <button class="btn btn-outline btn-sm">Export</button>
    <button class="btn btn-dark btn-sm">+ New Item</button>
  </div>
</div>
```

---

## Stat Cards Row

```html
<div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:16px; padding:20px 24px;">
  <div class="stat-card">
    <div class="stat-label">Total Users</div>
    <div class="stat-value">1,234</div>
    <div class="stat-change stat-up">12.5%</div>
  </div>
  <!-- repeat for other cards -->
</div>
```

---

## Data Table

```html
<div class="card" style="margin:0 24px;">
  <div class="card-header" style="display:flex; justify-content:space-between; align-items:center;">
    <span>Item List</span>
    <span style="font-size:12px; color:#6c757d;">Total 128 items</span>
  </div>
  <div class="card-body" style="padding:0;">
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Name</th>
          <th>Status</th>
          <th>Date</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>#001</td>
          <td>Item name</td>
          <td><span class="badge badge-dark">Active</span></td>
          <td>2026-04-21</td>
          <td><button class="btn btn-outline btn-sm">View</button></td>
        </tr>
      </tbody>
    </table>
  </div>
</div>
```

---

## Filter Bar

```html
<div style="padding:16px 24px; display:flex; gap:12px; align-items:center; flex-wrap:wrap;">
  <select class="select" style="width:140px;">
    <option>All Status</option>
    <option>Active</option>
    <option>Inactive</option>
  </select>
  <input class="input" placeholder="Search..." style="width:240px;">
  <button class="btn btn-dark btn-sm">Search</button>
</div>
```

---

## Form Group

```html
<div style="margin-bottom:16px;">
  <label style="display:block; font-size:12px; font-weight:600; color:#495057; margin-bottom:4px;">Field Label</label>
  <input class="input" placeholder="Enter value...">
</div>
```

Textarea variant:

```html
<div style="margin-bottom:16px;">
  <label style="display:block; font-size:12px; font-weight:600; color:#495057; margin-bottom:4px;">Description</label>
  <textarea class="input" rows="4" placeholder="Enter description..." style="resize:vertical;"></textarea>
</div>
```

---

## Badges

```html
<span class="badge badge-dark">Dark</span>
<span class="badge badge-mid">Medium</span>
<span class="badge badge-light">Light</span>
<span class="badge badge-outline">Outline</span>
<span class="badge badge-pending">Pending</span>
<span class="badge badge-approved">Approved</span>
<span class="badge badge-rejected">Rejected</span>
<span class="badge badge-active">Active</span>
```

---

## Toggle Switch

```html
<div class="toggle on"></div>
<div class="toggle off"></div>
```

---

## Buttons

```html
<button class="btn btn-dark">Primary</button>
<button class="btn btn-outline">Secondary</button>
<button class="btn btn-dark btn-sm">Small Primary</button>
<button class="btn btn-outline btn-sm">Small Secondary</button>
```

---

## Chat Bubble

```html
<!-- User message (right-aligned) -->
<div style="display:flex; justify-content:flex-end; margin-bottom:12px;">
  <div style="max-width:70%; background:#e9ecef; padding:10px 14px; border-radius:14px 14px 4px 14px; font-size:13px; color:#343a40;">
    User message text here
  </div>
</div>

<!-- AI response (left-aligned) -->
<div style="display:flex; justify-content:flex-start; margin-bottom:12px;">
  <div style="max-width:70%; background:#fff; border:1px solid #dee2e6; padding:10px 14px; border-radius:14px 14px 14px 4px; font-size:13px; color:#343a40;">
    AI response text here
  </div>
</div>
```

---

## Sidebar Menu Item

These go inside the sidebar `<nav>`. The `data-screen` attribute is used by `initSidebars()`.

```html
<div class="sidebar-item active" data-screen="scr-002">
  <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
    <!-- icon path -->
  </svg>
  Menu Label
</div>
<div class="sidebar-item sidebar-sub" data-screen="scr-003">Sub-item</div>
```

---

## Gauge Ring (SVG)

Circular progress indicator. Adjust `stroke-dashoffset` for fill level (0 = full, 282.7 = empty, based on r=45 circumference).

```html
<svg width="100" height="100" viewBox="0 0 100 100">
  <circle cx="50" cy="50" r="45" stroke="#e9ecef" stroke-width="8" fill="none"/>
  <circle cx="50" cy="50" r="45" stroke="#495057" stroke-width="8" fill="none"
    stroke-dasharray="282.7" stroke-dashoffset="70" class="gauge-ring"
    transform="rotate(-90 50 50)"/>
  <text x="50" y="50" text-anchor="middle" dominant-baseline="central"
    font-size="18" font-weight="700" fill="#212529">75%</text>
</svg>
```

---

## Tab Group

Horizontal tabs inside main content.

```html
<div style="padding:0 24px; border-bottom:1px solid #e9ecef; display:flex; gap:0;">
  <div style="padding:10px 16px; font-size:13px; font-weight:600; color:#212529; border-bottom:2px solid #343a40; cursor:pointer;">Tab 1</div>
  <div style="padding:10px 16px; font-size:13px; color:#6c757d; cursor:pointer;">Tab 2</div>
  <div style="padding:10px 16px; font-size:13px; color:#6c757d; cursor:pointer;">Tab 3</div>
</div>
```

---

## Description Table

The right-panel annotation table. Use plain numbers, not circled digits.

```html
<table class="desc-table">
  <thead><tr><th>No</th><th>Element</th><th>Description</th></tr></thead>
  <tbody>
    <tr><td class="num">1</td><td>Header Bar</td><td>Page title and action buttons. Shows current section name.</td></tr>
    <tr><td class="num">2</td><td>Filter Area</td><td>Status dropdown and keyword search for filtering table data.</td></tr>
    <tr><td class="num">3</td><td>Data Table</td><td>List of items with sortable columns. Pagination at bottom.</td></tr>
  </tbody>
</table>
```
