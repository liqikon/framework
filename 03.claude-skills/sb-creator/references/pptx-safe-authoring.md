# PPTX-Safe Authoring & Mobile Device-Frame Pattern

The Step 5 exporter (`sb-creator-pptx/scripts/pptx-export.js`) walks the **rendered DOM** and maps each element to a native PowerPoint shape or text box. It does not run a layout engine. Anything that depends on CSS the exporter can't read renders fine in the browser but comes out garbled in PPTX. This file documents the safe constructs and a ready-to-use mobile device frame.

## What the exporter can and cannot do

| Reads correctly | Cannot interpret |
|-----------------|------------------|
| `background:#RRGGBB` (solid) | `linear-gradient()` → uses first color only |
| Fixed `width`/`height` in px | `aspect-ratio` → element gets zero/wrong size |
| Absolute `left`/`top` in px | `calc()` → not evaluated |
| `border`, `border-radius` (rect/circle) | Nested flex/grid centering → box drift |
| A single text node per element | Text split across child spans → only inner child renders |
| `color` on opaque backgrounds | Light text over `rgba(...,0.05)` → blends to ~white, invisible |

Circles: a 1:1 element with `border-radius ≥ half` becomes an OVAL. Everything else becomes a RECTANGLE (rounded corners are dropped — acceptable for wireframes).

## The six rules

1. **Solid colors only.** Replace every gradient with a single hex. Cover/background panels too.
2. **Fixed px sizing.** Never `aspect-ratio`; give book covers, avatars, thumbnails explicit `width`+`height`.
3. **No `calc()`.** Use literal px for positions and indicator coordinates.
4. **Absolute placement for anything that must align.** Put children at `position:absolute; left/top` inside a parent that has a fixed size (e.g. the `.device` box). Flex is fine only for trivial single-row chips where exact alignment doesn't matter.
5. **One text node per element.** `rodi-book AX`, not `rodi-book<span>AX</span>`. If you need two colors in one logical label, accept one color or use two separate absolutely-positioned nodes.
6. **Readable contrast on solid cards.** On a dark cover, use a solid dark card (e.g. `#3730A3`) with light text — never a translucent white overlay.

After writing, always re-run the injector and open the PPTX to confirm. The HTML looking right is not sufficient proof.

## Mobile device-frame CSS (validated)

Drop this into the `<style>` block. It produces a phone frame whose contents convert cleanly because every atom is solid-color + fixed-px.

```css
/* MOBILE DEVICE FRAME — converter-friendly: solid colors, fixed px, no gradient/aspect-ratio/calc */
.device { width: 360px; height: 660px; background: #F1F5F9; border: 8px solid #1E293B; border-radius: 28px; position: relative; overflow: hidden; }

.hdr { position: absolute; left: 0; top: 0; width: 100%; height: 48px; background: #FFFFFF; border-bottom: 1px solid #E2E8F0; }
.hdr-logo  { position: absolute; left: 14px; top: 14px; font-size: 16px; font-weight: 700; color: #4F46E5; }
.hdr-title { position: absolute; left: 44px; top: 14px; font-size: 15px; font-weight: 700; color: #0F172A; }
.hdr-back  { position: absolute; left: 12px; top: 12px; width: 24px; height: 24px; border: 1px solid #CBD5E1; border-radius: 6px; color: #334155; font-size: 14px; text-align: center; line-height: 22px; }
.hdr-ic    { position: absolute; top: 12px; width: 26px; height: 26px; border: 1px solid #E2E8F0; border-radius: 7px; background: #F8FAFC; color: #475569; font-size: 12px; text-align: center; line-height: 25px; }
.cnt       { position: absolute; width: 16px; height: 16px; border-radius: 8px; background: #F97316; color: #fff; font-size: 9px; font-weight: 700; text-align: center; line-height: 16px; }

.bbar { position: absolute; left: 0; bottom: 0; width: 100%; background: #FFFFFF; border-top: 1px solid #E2E8F0; }

.cover-img { position: absolute; border-radius: 6px; }   /* always set width+height inline, never aspect-ratio */
.cv1 { background: #4338CA; } .cv2 { background: #0F766E; } .cv3 { background: #9333EA; } .cv4 { background: #B45309; }
.cv-t { position: absolute; left: 0; bottom: 4px; width: 100%; color: #fff; font-size: 9px; font-weight: 700; text-align: center; }

.btn-pri   { background: #4F46E5; color: #FFFFFF; border-radius: 9px; font-size: 13px; font-weight: 600; text-align: center; }
.btn-sec   { background: #FFFFFF; color: #4F46E5; border: 1px solid #4F46E5; border-radius: 9px; font-size: 13px; font-weight: 600; text-align: center; }
.btn-ghost { background: #FFFFFF; color: #64748B; border: 1px solid #E2E8F0; border-radius: 9px; font-size: 13px; font-weight: 600; text-align: center; }
.card-box  { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 11px; }
.inp       { background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 9px; color: #94A3B8; font-size: 12px; line-height: 40px; padding-left: 12px; }
.pill      { background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 8px; color: #475569; font-size: 11px; text-align: center; }
.chip      { background: #EEF2FF; border-radius: 8px; color: #4338CA; font-size: 11px; font-weight: 600; text-align: center; }
.tagx      { background: #F1F5F9; border-radius: 6px; color: #475569; font-size: 10px; text-align: center; }
.bn-info   { background: #EFF6FF; border-radius: 8px; color: #1E40AF; font-size: 11px; line-height: 1.45; padding: 8px 10px; }
.bn-ok     { background: #ECFDF5; border-radius: 8px; color: #047857; font-size: 11px; line-height: 1.45; padding: 8px 10px; }
.divln     { background: #E2E8F0; height: 1px; }
```

> The palette above is a sample app theme (indigo `#4F46E5` brand, orange `#F97316` accent). Swap hex values to match the project's design system — keep them **solid**. Indicator circles stay `#e67700` per the sb-creator standard.

## Worked example — one screen, device frame + indicators + description

Buttons/labels/banners are placed by absolute px inside the `.device`. Indicators use literal px on the `.ind-container` (which wraps the device and is centered with `width:360px; margin:0 auto`).

```html
<div id="scr-001" class="screen-section">
  <div class="meta-box" style="margin:60px 24px 0 24px;">
    <div style="display:flex; align-items:center; gap:16px; flex-wrap:wrap;">
      <span class="screen-id-badge">SCR-001</span>
      <div><span class="meta-label">Screen</span><div class="meta-value" style="font-weight:600; font-size:15px;">홈</div></div>
      <div style="margin-left:24px;"><span class="meta-label">URL</span><div class="meta-value">/</div></div>
    </div>
  </div>

  <div class="wireframe-wrap" style="margin:0 24px 24px 24px; padding:20px 0;">
    <div class="ind-container" style="width:360px; margin:0 auto;">
      <div class="device">
        <!-- header: each element absolutely placed, single text node each -->
        <div class="hdr"></div>
        <div class="hdr-logo">brand AX</div>          <!-- NOT brand<span>AX</span> -->
        <div class="hdr-ic" style="right:72px;">장바</div>
        <div class="cnt"   style="right:64px; top:8px;">2</div>
        <div class="hdr-ic" style="right:14px;">메뉴</div>
        <!-- hero card on a solid tint -->
        <div style="position:absolute; left:14px; top:96px; width:332px; height:150px; background:#EEF2FF; border-radius:16px;"></div>
        <div class="cover-img cv1" style="left:28px; top:134px; width:62px; height:84px;"><div class="cv-t">표지</div></div>
        <div style="position:absolute; left:104px; top:151px; width:230px; font-size:14px; font-weight:700; color:#0F172A;">추천 도서 제목</div>
        <div class="btn-pri" style="position:absolute; left:104px; top:214px; width:228px; height:30px; line-height:30px;">지금 보기</div>
        <!-- bottom bar -->
        <div class="bbar" style="height:60px;"></div>
        <div class="btn-pri" style="position:absolute; left:16px; bottom:13px; width:328px; height:44px; line-height:44px; font-size:14px;">담기</div>
      </div>
      <!-- indicators: literal px relative to .ind-container, NOT calc() -->
      <div class="indicator" style="left:8px;   top:14px;">1</div>
      <div class="indicator" style="left:300px; top:14px;">2</div>
      <div class="indicator" style="left:330px; top:100px;">3</div>
    </div>
  </div>

  <div class="desc-wrap">
    <h3 style="font-size:16px; font-weight:700; color:#212529;">Description</h3>
    <table class="desc-table">
      <thead><tr><th class="num">No.</th><th>요소</th><th>설명</th></tr></thead>
      <tbody>
        <tr><td class="num">1</td><td>헤더 로고</td><td>홈으로 이동.</td></tr>
        <tr><td class="num">2</td><td>장바구니</td><td>수량 배지. 클릭 시 /cart.</td></tr>
        <tr><td class="num">3</td><td>히어로 CTA</td><td>[지금 보기] → 상세.</td></tr>
      </tbody>
    </table>
  </div>
</div>
```

## Multi-device on one slide (e.g. login + signup)

Place two `.device` boxes side by side with `position:absolute; left:0` and `left:400px` inside an `.ind-container` sized `width:760px; height:480px`. Position that screen's indicators against the same 760px container with literal px (negative `left` for the left device's left-edge markers is fine).

## Cover page

The cover converts to the first slide on a dark background. Keep it solid:

- Page wrapper: `background:#312E81` (solid), not a gradient.
- Meta/Screen-List cards: solid `#3730A3` boxes with light text (`#E0E7FF`, `#FFFFFF`) — never translucent white.
- Title: one text node (`brand AX 화면설계서`), centered with `text-align:center`, not flex centering.
