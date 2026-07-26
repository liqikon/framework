/* sb-creator -> Figma 플러그인 (메인 스레드)
 * scene.json(추출기 출력)을 받아 화면별 Frame + Text + Shape + Vector 를 생성한다.
 * - 기본: 절대좌표 배치(부모 상대 box.x/y) -> 시각 충실도 우선
 * - 옵션: Auto Layout 적용(실험적) -> flex 힌트가 있는 프레임에 오토레이아웃
 * 빌드 불필요: Figma가 code.js 를 직접 로드.
 */

figma.showUI(__html__, { width: 380, height: 460, themeColors: true });

// ---- 유틸 -----------------------------------------------------------------
function hexToRGB(hex) {
  if (!hex || hex[0] !== '#') return { r: 0, g: 0, b: 0 };
  let h = hex.slice(1);
  if (h.length === 3) h = h.split('').map(c => c + c).join('');
  const n = parseInt(h, 16);
  return { r: ((n >> 16) & 255) / 255, g: ((n >> 8) & 255) / 255, b: (n & 255) / 255 };
}

function solid(hex, opacity) {
  const p = { type: 'SOLID', color: hexToRGB(hex) };
  if (typeof opacity === 'number' && opacity < 1) p.opacity = opacity;
  return p;
}

// 폰트 weight -> 스타일명 (패밀리별 가용 스타일이 달라 분리)
function styleFor(family, w) {
  if (family === 'Noto Sans KR') {
    if (w <= 250) return 'Thin';
    if (w <= 350) return 'Light';
    if (w < 450) return 'Regular';
    if (w < 600) return 'Medium';
    if (w < 800) return 'Bold';
    return 'Black';
  }
  // Pretendard / Inter 계열
  if (w >= 800) return 'ExtraBold';
  if (w >= 700) return 'Bold';
  if (w >= 600) return 'SemiBold';
  if (w >= 500) return 'Medium';
  if (w <= 300) return 'Light';
  return 'Regular';
}

// 폰트 해석 + 폴백 체인.
// 핵심: 한글 폴백을 Inter/Roboto(한글 글리프 없음) 대신 Figma 내장 'Noto Sans KR'로 →
// 한글이 올바른 메트릭으로 렌더되어 겹침/크램핑이 사라진다. Pretendard 설치 시 그것을 우선.
const fontCache = {}; // key family|weight -> resolved {family,style}
const GENERIC_FONT = {
  'monospace': 'Roboto Mono', 'ui-monospace': 'Roboto Mono', 'menlo': 'Roboto Mono',
  'sans-serif': 'Inter', 'system-ui': 'Inter', '-apple-system': 'Inter',
  'serif': 'Noto Serif', 'inherit': 'Inter'
};
async function resolveFont(family, weight) {
  const norm = GENERIC_FONT[(family || '').toLowerCase()];
  if (norm) family = norm;
  const key = family + '|' + weight;
  if (fontCache[key]) return fontCache[key];
  const candidates = [
    { family: family, style: styleFor(family, weight) },
    { family: family, style: 'Regular' },
    { family: 'Pretendard', style: styleFor('Pretendard', weight) },
    { family: 'Noto Sans KR', style: styleFor('Noto Sans KR', weight) },
    { family: 'Noto Sans KR', style: 'Regular' },
    { family: 'Inter', style: styleFor('Inter', weight) },
    { family: 'Roboto', style: 'Regular' }
  ];
  for (const c of candidates) {
    try {
      await figma.loadFontAsync(c);
      fontCache[key] = c;
      return c;
    } catch (e) { /* 다음 후보 */ }
  }
  const fallback = { family: 'Roboto', style: 'Regular' };
  fontCache[key] = fallback;
  return fallback;
}

// scene 전체에서 사용된 (family,weight) 미리 로드
async function preloadFonts(scene) {
  const seen = new Set();
  const jobs = [];
  function walk(n) {
    if (n.kind === 'text' && n.style) {
      const k = (n.style.fontFamily || 'Inter') + '|' + (n.style.fontWeight || 400);
      if (!seen.has(k)) { seen.add(k); jobs.push(resolveFont(n.style.fontFamily || 'Inter', n.style.fontWeight || 400)); }
    }
    (n.children || []).forEach(walk);
  }
  for (const s of scene.screens) walk(s.root);
  await Promise.all(jobs);
}

// CSS 각도(deg) -> Figma 그라디언트 변환행렬. CSS 90deg(오른쪽) == Figma 기본(좌->우)
function gradTransform(angleDeg) {
  const r = (angleDeg - 90) * Math.PI / 180;
  const cos = Math.cos(r), sin = Math.sin(r);
  return [
    [cos, sin, (1 - cos - sin) / 2],
    [-sin, cos, (1 + sin - cos) / 2]
  ];
}

function gradientPaint(g) {
  const stops = (g.stops || []).map(s => {
    const c = hexToRGB(s.color);
    return { position: Math.max(0, Math.min(1, s.pos == null ? 0 : s.pos)),
             color: { r: c.r, g: c.g, b: c.b, a: typeof s.opacity === 'number' ? s.opacity : 1 } };
  });
  if (stops.length < 2) return null;
  return { type: 'GRADIENT_LINEAR', gradientTransform: gradTransform(g.angle || 180), gradientStops: stops };
}

function applyVisual(node, style) {
  if (!style) return;
  // 배경: 그라디언트 우선, 없으면 solid
  if (style.gradient) {
    const gp = gradientPaint(style.gradient);
    if (gp) node.fills = [gp];
    else if (style.fill) node.fills = [solid(style.fill, style.fillOpacity)];
  } else if (style.fill) {
    node.fills = [solid(style.fill, style.fillOpacity)];
  } else if (node.type !== 'TEXT') node.fills = [];
  if (style.stroke) {
    node.strokes = [solid(style.stroke)];
    node.strokeWeight = style.strokeWidth || 1;
    node.strokeAlign = 'INSIDE';
  }
  if (typeof style.cornerRadius === 'number' && 'cornerRadius' in node) {
    node.cornerRadius = style.cornerRadius;
  }
  // box-shadow -> Figma 이펙트 (카드 입체감 복원)
  if (style.shadow && style.shadow.length && 'effects' in node) {
    node.effects = style.shadow.map(sh => {
      const c = hexToRGB(sh.color);
      return {
        type: sh.type === 'INNER' ? 'INNER_SHADOW' : 'DROP_SHADOW',
        color: { r: c.r, g: c.g, b: c.b, a: typeof sh.opacity === 'number' ? sh.opacity : 0.25 },
        offset: { x: sh.x || 0, y: sh.y || 0 },
        radius: sh.blur || 0,
        spread: sh.spread || 0,
        visible: true, blendMode: 'NORMAL'
      };
    });
  }
  if (typeof style.opacity === 'number') node.opacity = style.opacity;
}

const alignMapH = { LEFT: 'LEFT', CENTER: 'CENTER', RIGHT: 'RIGHT', JUSTIFIED: 'JUSTIFIED' };

async function makeText(spec, opts) {
  opts = opts || {};
  const t = figma.createText();
  const f = await resolveFont(spec.style.fontFamily || 'Inter', spec.style.fontWeight || 400);
  t.fontName = f;
  t.fontSize = Math.max(1, spec.style.fontSize || 14);
  t.characters = spec.text || '';
  t.fills = [solid(spec.style.fill || '#000000')];
  if (spec.style.lineHeight) t.lineHeight = { value: spec.style.lineHeight, unit: 'PIXELS' };
  if (spec.style.letterSpacing) t.letterSpacing = { value: spec.style.letterSpacing, unit: 'PIXELS' };
  if (spec.style.decoration && spec.style.decoration !== 'NONE') t.textDecoration = spec.style.decoration;
  t.textAlignHorizontal = alignMapH[spec.style.textAlign] || 'LEFT';
  t.textAlignVertical = 'CENTER';

  const lh = spec.style.lineHeight || (spec.style.fontSize || 14) * 1.4;
  const singleLine = (spec.text || '').indexOf('\n') < 0 && spec.box.h <= lh * 1.7;

  if (opts.fixed) {
    // 버튼/뱃지 내부 텍스트: 자동 너비(줄바꿈 방지). 대체 폰트가 더 넓어도 겹치지 않음.
    // 배치는 buildNode 에서 프레임 기준 중앙정렬.
    t.textAutoResize = 'WIDTH_AND_HEIGHT';
  } else if (singleLine) {
    // 한 줄 텍스트(라벨·가격·포인트 등): 자동 너비로 줄바꿈 방지
    t.textAutoResize = 'WIDTH_AND_HEIGHT';
  } else {
    // 여러 줄(문단): 고정 너비 + 높이 자동
    t.textAutoResize = 'HEIGHT';
    t.resize(Math.max(1, spec.box.w), Math.max(1, spec.box.h));
  }
  t.name = (spec.text || 'text').slice(0, 30);
  return t;
}

// 노드 생성 (재귀). parent 에 append 후 위치 지정.
async function buildNode(spec, parent, opts) {
  let node = null;

  // 주석 마커(번호 원) 제외 (기본): sb-creator 표식이 UI 위에 겹침.
  // 설명 패널을 켜면 넘버링도 함께 표시(표의 번호와 대응).
  // 주의: 'ind-container'는 UI 콘텐츠 래퍼이므로 제외하지 않는다(제외 시 화면이 비어버림).
  if (!(opts.includeAnnotations || opts.descPanel) && spec.role === 'indicator') {
    return null;
  }

  if (spec.kind === 'text') {
    if (spec.bgStyle) {
      // 배경 있는 텍스트(버튼/뱃지) -> Frame + 내부 Text(고정폭·중앙)
      const fr = figma.createFrame();
      fr.name = (spec.role || 'btn') + ':' + (spec.text || '').slice(0, 16);
      if (spec.role) fr.setPluginData('sbrole', spec.role);
      fr.resize(Math.max(1, spec.box.w), Math.max(1, spec.box.h));
      applyVisual(fr, spec.bgStyle);
      fr.clipsContent = false;
      parent.appendChild(fr);
      fr.x = spec.box.x; fr.y = spec.box.y;
      const txt = await makeText(spec, { fixed: true });
      fr.appendChild(txt);
      // 프레임 기준 중앙정렬 (대체 폰트로 폭이 달라져도 균형 유지 -> 겹침/치우침 방지)
      txt.x = Math.round((spec.box.w - txt.width) / 2);
      txt.y = Math.round((spec.box.h - txt.height) / 2);
      return fr;
    }
    node = await makeText(spec);
    parent.appendChild(node);
    node.x = spec.box.x; node.y = spec.box.y;
    return node;
  }

  if (spec.kind === 'rect') {
    node = figma.createRectangle();
    node.resize(Math.max(1, spec.box.w), Math.max(1, spec.box.h));
    applyVisual(node, spec.style);
    node.name = spec.name || 'rect';
    parent.appendChild(node);
    node.x = spec.box.x; node.y = spec.box.y;
    return node;
  }

  if (spec.kind === 'vector') {
    try {
      node = figma.createNodeFromSvg(spec.svg);
    } catch (e) {
      node = figma.createRectangle();
      node.fills = [solid('#adb5bd')];
    }
    node.resize(Math.max(1, spec.box.w), Math.max(1, spec.box.h));
    node.name = spec.name || 'icon';
    parent.appendChild(node);
    node.x = spec.box.x; node.y = spec.box.y;
    return node;
  }

  if (spec.kind === 'image') {
    node = figma.createRectangle();
    node.resize(Math.max(1, spec.box.w), Math.max(1, spec.box.h));
    node.fills = [solid('#e9ecef')];
    node.name = (spec.name || 'image') + ' (placeholder)';
    parent.appendChild(node);
    node.x = spec.box.x; node.y = spec.box.y;
    return node;
  }

  // frame
  const fr = figma.createFrame();
  fr.name = spec.name || 'frame';
  fr.resize(Math.max(1, spec.box.w), Math.max(1, spec.box.h));
  applyVisual(fr, spec.style);
  fr.clipsContent = false;
  parent.appendChild(fr);
  fr.x = spec.box.x; fr.y = spec.box.y;

  for (const child of (spec.children || [])) {
    await buildNode(child, fr, opts);
  }

  // 오토레이아웃 (옵션, 실험적) — 자식 배치가 flex 방향과 어긋나면 절대배치 유지
  if (opts.autoLayout && spec.layout && spec.layout.mode !== 'NONE' && fr.children.length > 0
      && autoLayoutSafe(spec)) {
    try {
      fr.layoutMode = spec.layout.mode;
      fr.itemSpacing = spec.layout.gap || 0;
      const p = spec.layout.padding || [0, 0, 0, 0];
      fr.paddingTop = p[0]; fr.paddingRight = p[1]; fr.paddingBottom = p[2]; fr.paddingLeft = p[3];
      fr.primaryAxisAlignItems = spec.layout.primaryAlign === 'SPACE_BETWEEN' ? 'SPACE_BETWEEN'
        : spec.layout.primaryAlign === 'CENTER' ? 'CENTER'
        : spec.layout.primaryAlign === 'MAX' ? 'MAX' : 'MIN';
      fr.counterAxisAlignItems = spec.layout.counterAlign === 'CENTER' ? 'CENTER'
        : spec.layout.counterAlign === 'MAX' ? 'MAX' : 'MIN';
    } catch (e) { /* 무시 */ }
  }

  // 모바일 프레임 -> iPhone 디바이스 프레임 (옵션)
  if (opts.deviceFrame && DEVICE_ROLES.has(spec.role)) {
    try { styleAsDevice(fr); } catch (e) { /* 무시 */ }
  }
  return fr;
}

const DEVICE_ROLES = new Set(['mobile-frame', 'phone-frame', 'device-frame', 'app-frame']);

// 모바일 프레임을 세련된 iPhone 스타일로 변환:
// 라운드 코너 + 다크 베젤(외곽선) + 다이나믹 아일랜드 + 홈 인디케이터 + 드롭섀도.
function styleAsDevice(fr) {
  const w = fr.width, h = fr.height;
  const BEZEL = '#0a0a0c';
  fr.cornerRadius = Math.min(56, Math.round(w * 0.135));
  fr.clipsContent = true;                       // 화면 모서리를 라운드로 클립
  fr.fills = (fr.fills && fr.fills.length) ? fr.fills : [solid('#ffffff')];
  fr.strokes = [solid(BEZEL)];
  fr.strokeWeight = 12;                          // 베젤
  fr.strokeAlign = 'OUTSIDE';                    // 콘텐츠 폭(375) 유지, 베젤은 바깥으로
  fr.effects = [{
    type: 'DROP_SHADOW', color: { r: 0, g: 0, b: 0, a: 0.28 },
    offset: { x: 0, y: 18 }, radius: 42, spread: 0, visible: true, blendMode: 'NORMAL'
  }];

  // 다이나믹 아일랜드 (상단 중앙 검정 알약)
  const iw = Math.min(122, Math.round(w * 0.32)), ih = 30;
  const island = figma.createRectangle();
  island.resize(iw, ih);
  island.cornerRadius = ih / 2;
  island.fills = [solid(BEZEL)];
  island.name = 'dynamic-island';
  fr.appendChild(island);
  island.x = Math.round((w - iw) / 2);
  island.y = 9;

  // 홈 인디케이터 (하단 중앙 알약)
  const hw = Math.round(w * 0.36);
  const home = figma.createRectangle();
  home.resize(hw, 5);
  home.cornerRadius = 3;
  home.fills = [solid('#1a1a1c', 0.9)];
  home.name = 'home-indicator';
  fr.appendChild(home);
  home.x = Math.round((w - hw) / 2);
  home.y = Math.round(h - 15);
}

// 오토레이아웃 안전성 검사: flex 방향(가로/세로)과 자식들의 실제 좌표가 일치하는지.
// 예) product-card 는 HORIZONTAL 이지만 내부 텍스트들이 세로로 쌓여(같은 x, 다른 y) 있으면
// 오토레이아웃이 이를 가로로 펼쳐 깨뜨린다 -> 이런 경우 false 를 반환해 절대배치를 유지.
function autoLayoutSafe(spec) {
  const kids = (spec.children || []).filter(c => c.box);
  if (kids.length < 2) return true;
  const horizontal = spec.layout.mode === 'HORIZONTAL';
  let overlaps = 0, pairs = 0;
  for (let i = 0; i < kids.length; i++) {
    for (let j = i + 1; j < kids.length; j++) {
      pairs++;
      const a = kids[i].box, b = kids[j].box;
      const o = horizontal
        ? Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x)   // x축 겹침
        : Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);  // y축 겹침
      const minDim = horizontal ? Math.min(a.w, b.w) : Math.min(a.h, b.h);
      if (minDim > 0 && o > 0.3 * minDim) overlaps++;
    }
  }
  return overlaps <= pairs * 0.15;   // 주 축에서 겹치는 쌍이 거의 없어야 안전
}

// 설명 패널용 단순 텍스트 노드 (폭 지정 시 자동 줄바꿈)
async function makeLabel(text, opt) {
  opt = opt || {};
  const t = figma.createText();
  t.fontName = await resolveFont(opt.family || 'Pretendard', opt.weight || 400);
  t.fontSize = opt.size || 12;
  t.characters = text || '';
  t.fills = [solid(opt.color || '#212529')];
  if (opt.lineHeight) t.lineHeight = { value: opt.lineHeight, unit: 'PIXELS' };
  if (opt.width) { t.textAutoResize = 'HEIGHT'; t.resize(opt.width, t.height); }
  else t.textAutoResize = 'WIDTH_AND_HEIGHT';
  return t;
}

// 화면 위 마커(indicator)의 실제 색상을 찾아 설명 패널 배지에 동일 적용 -> 시각적 연계
function findMarkerColor(node) {
  let color = null;
  (function walk(n) {
    if (color) return;
    if (n.role === 'indicator' && n.bgStyle && n.bgStyle.fill) { color = n.bgStyle.fill; return; }
    (n.children || []).forEach(walk);
  })(node);
  return color || '#e67700';   // sb-creator 기본 마커색(주황)
}

// 화면 우측에 Description 표를 네이티브 텍스트로 렌더 (번호 배지 + 요소 + 설명)
async function renderDescPanel(screen, x, y, markerColor) {
  const ann = screen.annotations;
  if (!ann || !ann.rows || !ann.rows.length) return null;
  const BADGE_FILL = markerColor || '#e67700';
  const PANEL_W = 380, PAD = 20, BADGE = 22, GAP_COL = 12, ROW_GAP = 16;
  const colX = PAD + BADGE + GAP_COL;
  const colW = PANEL_W - colX - PAD;

  const panel = figma.createFrame();
  panel.name = screen.id + ' · 설명';
  panel.fills = [solid('#ffffff')];
  panel.cornerRadius = 8;
  panel.strokes = [solid('#e9ecef')]; panel.strokeWeight = 1; panel.strokeAlign = 'INSIDE';
  panel.clipsContent = false;
  figma.currentPage.appendChild(panel);
  panel.x = x; panel.y = y;

  let cy = PAD;
  const title = await makeLabel(ann.title || 'Description', { size: 16, weight: 700, color: '#212529' });
  panel.appendChild(title); title.x = PAD; title.y = cy;
  cy += title.height + 14;

  for (const row of ann.rows) {
    const no = row[0] || '', element = row[1] || '', desc = row[2] || '';
    const rowTop = cy;

    // 번호 배지 (원) — 화면 위 마커와 동일 색상으로 연계
    const badge = figma.createEllipse();
    badge.resize(BADGE, BADGE);
    badge.fills = [solid(BADGE_FILL)];
    badge.name = 'no-' + no;
    panel.appendChild(badge); badge.x = PAD; badge.y = rowTop;
    const noTxt = await makeLabel(no, { size: 11, weight: 700, color: '#ffffff' });
    panel.appendChild(noTxt);
    noTxt.x = PAD + (BADGE - noTxt.width) / 2;
    noTxt.y = rowTop + (BADGE - noTxt.height) / 2;

    // 요소명 (볼드)
    const el = await makeLabel(element, { size: 12.5, weight: 700, color: '#212529', width: colW, lineHeight: 17 });
    panel.appendChild(el); el.x = colX; el.y = rowTop;
    let h = el.height;

    // 설명 (회색, 줄바꿈)
    if (desc) {
      const d = await makeLabel(desc, { size: 11.5, weight: 400, color: '#6c757d', width: colW, lineHeight: 16 });
      panel.appendChild(d); d.x = colX; d.y = rowTop + el.height + 3;
      h = el.height + 3 + d.height;
    }

    cy = rowTop + Math.max(BADGE, h) + ROW_GAP;
  }

  panel.resize(PANEL_W, Math.round(cy - ROW_GAP + PAD));
  return panel;
}

// 주석 마커(번호 원)를 부모의 맨 앞(최상위 페인트)으로 이동.
// sb-creator 는 z-index 로 마커를 콘텐츠 위에 두지만, 변환기는 DOM 순서대로 칠하므로
// 먼저 나온 마커가 뒤이어 나온 불투명 콘텐츠에 가려진다 -> 마지막으로 재배치해 앞으로.
function bringIndicatorsToFront(node) {
  const inds = [];
  (function collect(n) {
    if (n.getPluginData && n.getPluginData('sbrole') === 'indicator') inds.push(n);
    if ('children' in n) for (const c of n.children) collect(c);
  })(node);
  for (const n of inds) { if (n.parent) n.parent.appendChild(n); }
}

async function importScene(scene, opts) {
  await preloadFonts(scene);

  // Pretendard 미설치 시 자간이 원본과 달라질 수 있음을 안내
  let wantsPretendard = false;
  (function scan(n) {
    if (n && n.kind === 'text' && n.style && /pretendard/i.test(n.style.fontFamily || '')) wantsPretendard = true;
    (n && n.children || []).forEach(scan);
  })({ children: scene.screens.map(s => s.root) });
  if (wantsPretendard) {
    try {
      await figma.loadFontAsync({ family: 'Pretendard', style: 'Regular' });
    } catch (e) {
      figma.notify('Pretendard 미설치 -> Noto Sans KR 로 대체 렌더링됩니다. 정확한 자간은 Pretendard 설치 권장.', { timeout: 4000 });
    }
  }

  const created = [];
  let offsetX = 0;
  const gap = opts.screenGap || 120;
  const baseX = figma.viewport.center.x - 600;
  const baseY = figma.viewport.center.y - 400;
  const pageFrame = opts.pageFrame !== false;     // 기본 ON
  const canvasW = opts.canvasWidth || 1440;
  const pageBg = opts.pageBg || '#eef0f2';

  for (const screen of scene.screens) {
    const contentW = screen.frame.w || 0;
    const contentH = screen.frame.h || 100;

    if (pageFrame) {
      // 더 넓은 페이지 프레임에 콘텐츠를 가로 가운데 배치 (양옆 여백)
      const cw = Math.max(canvasW, contentW);
      const page = figma.createFrame();
      page.resize(cw, contentH);
      page.fills = [solid(pageBg)];
      page.clipsContent = true;
      figma.currentPage.appendChild(page);
      page.x = baseX + offsetX;
      page.y = baseY;
      page.name = screen.id + ' · ' + screen.name;

      const root = await buildNode(screen.root, page, opts);
      root.x = Math.round((cw - contentW) / 2);   // 가로 가운데
      root.y = 0;
      root.name = 'content';
      if (!screen.root.style || !screen.root.style.fill) root.fills = [solid('#ffffff')];
      root.strokes = [];                            // 문서 캔버스 외곽선 제거
      if (opts.includeAnnotations || opts.descPanel) bringIndicatorsToFront(root);

      created.push(page);

      if (opts.descPanel && screen.annotations) {
        // 콘텐츠 오른쪽 끝 바로 옆(40px)에 밀착 배치 -> 마커↔설명 연계 강화
        const panelX = page.x + Math.round((cw + contentW) / 2) + 40;
        const panel = await renderDescPanel(screen, panelX, baseY, findMarkerColor(screen.root));
        if (panel) { created.push(panel); offsetX = (panel.x + panel.width + gap) - baseX; }
        else offsetX += cw + gap;
      } else {
        offsetX += cw + gap;
      }
    } else {
      const root = await buildNode(screen.root, figma.currentPage, opts);
      root.x = baseX + offsetX;
      root.y = baseY;
      root.name = screen.id + ' · ' + screen.name;
      if (!screen.root.style || !screen.root.style.fill) root.fills = [solid('#ffffff')];
      root.strokes = [];
      if (opts.includeAnnotations || opts.descPanel) bringIndicatorsToFront(root);
      created.push(root);

      if (opts.descPanel && screen.annotations) {
        const panel = await renderDescPanel(screen, root.x + contentW + 40, baseY, findMarkerColor(screen.root));
        if (panel) { created.push(panel); offsetX = (panel.x + panel.width + gap) - baseX; }
        else offsetX += contentW + gap;
      } else {
        offsetX += contentW + gap;
      }
    }
  }

  if (created.length) {
    figma.currentPage.selection = created;
    figma.viewport.scrollAndZoomIntoView(created);
  }
  return created.length;
}

figma.ui.onmessage = async (msg) => {
  if (msg.type === 'import') {
    try {
      const scene = typeof msg.scene === 'string' ? JSON.parse(msg.scene) : msg.scene;
      if (!scene || !Array.isArray(scene.screens)) throw new Error('screens 배열이 없습니다. 올바른 scene.json 인가요?');
      const opts = {
        autoLayout: !!msg.autoLayout,
        screenGap: msg.screenGap || 120,
        includeAnnotations: !!msg.includeAnnotations,
        pageFrame: msg.pageFrame !== false,
        canvasWidth: msg.canvasWidth || 1440,
        deviceFrame: msg.deviceFrame !== false,   // 기본 ON
        descPanel: !!msg.descPanel                 // 설명 패널 + 넘버링 (옵션)
      };
      const n = await importScene(scene, opts);
      figma.ui.postMessage({ type: 'done', count: n });
      figma.notify('완료: ' + n + '개 화면을 생성했습니다.');
    } catch (e) {
      figma.ui.postMessage({ type: 'error', message: String(e && e.message || e) });
      figma.notify('오류: ' + (e && e.message || e), { error: true });
    }
  } else if (msg.type === 'close') {
    figma.closePlugin();
  }
};
