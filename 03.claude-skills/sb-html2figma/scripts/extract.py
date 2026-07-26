#!/usr/bin/env python3
"""
sb-creator HTML -> Figma scene.json 추출기 (M1)

Playwright로 화면설계서 HTML을 렌더링하여 화면(screen-section)별 wireframe-wrap을
순회하고, 각 요소의 computed layout(getBoundingClientRect) + computed style을 모아
Figma 플러그인이 소비하는 scene.json 으로 출력한다.

사용법:
  python3 extract.py <input.html> [output.json]

요구사항: pip install playwright  /  playwright install chromium
대안: 시스템 Chrome 사용 (channel="chrome")
"""

import sys
import json
from pathlib import Path

# ---- 페이지 내부에서 실행될 추출 스크립트 ----------------------------------
PAGE_SCRIPT = r"""
() => {
  const KNOWN_ROLES = [
    // 디바이스 프레임은 다른 유틸 클래스(ind-container 등)보다 우선 매칭
    'mobile-frame','phone-frame','device-frame','app-frame',
    'screen-section','wireframe-wrap','card-header','card-body','card',
    'input','select','btn','badge','product-card','thumb','info',
    'star-filled','star-empty','checkbox-input','indicator','num','ind-container',
    'site-header','site-footer','logo','icons','stat-card','stat-value','stat-label',
    'sidebar-item','tab-btn','screen-id-badge','meta-label','meta-value','price','title'
  ];

  function roleFromClass(el) {
    const cls = (el.getAttribute('class') || '').split(/\s+/);
    for (const r of KNOWN_ROLES) if (cls.includes(r)) return r;
    return null;
  }

  function parseColor(c) {
    if (!c || c === 'transparent' || c === 'none') return null;
    const m = c.match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(',').map(s => parseFloat(s.trim()));
    const a = p.length > 3 ? p[3] : 1;
    if (a === 0) return null;
    const hex = '#' + p.slice(0, 3).map(v => Math.round(v).toString(16).padStart(2, '0')).join('');
    return { hex, opacity: a };
  }

  function radiusPx(cs, w, h) {
    const v = cs.borderTopLeftRadius || '0px';
    if (v.indexOf('%') >= 0) return Math.min(w, h) * (parseFloat(v) / 100);
    return parseFloat(v) || 0;
  }

  // 최상위 콤마 분리 (rgba(...) 내부 콤마는 무시)
  function splitTop(s) {
    const parts = []; let depth = 0, cur = '';
    for (const ch of s) {
      if (ch === '(') depth++;
      else if (ch === ')') depth--;
      if (ch === ',' && depth === 0) { parts.push(cur); cur = ''; }
      else cur += ch;
    }
    if (cur.trim()) parts.push(cur);
    return parts;
  }

  // box-shadow -> [{type, x, y, blur, spread, color, opacity}]
  function parseShadows(bs) {
    if (!bs || bs === 'none') return [];
    const out = [];
    for (const raw of splitTop(bs)) {
      const s = raw.trim(); if (!s) continue;
      const inset = /(^|\s)inset(\s|$)/.test(s);
      const cm = s.match(/rgba?\([^)]+\)|#[0-9a-fA-F]{3,8}/);
      const col = cm ? parseColor(cm[0]) : { hex: '#000000', opacity: 0.2 };
      if (!col) continue;
      const nums = (s.replace(/rgba?\([^)]+\)/, '').match(/-?[\d.]+px/g) || []).map(v => parseFloat(v));
      const x = nums[0] || 0, y = nums[1] || 0, blur = nums[2] || 0, spread = nums[3] || 0;
      out.push({ type: inset ? 'INNER' : 'DROP', x, y, blur, spread, color: col.hex, opacity: col.opacity });
    }
    return out;
  }

  // linear-gradient(...) -> {angle, stops:[{color,opacity,pos}]}
  function parseGradient(bi) {
    if (!bi || bi.indexOf('linear-gradient') < 0) return null;
    const inner = bi.slice(bi.indexOf('(') + 1, bi.lastIndexOf(')'));
    const parts = splitTop(inner);
    let angle = 180, i = 0;
    const first = (parts[0] || '').trim();
    if (/deg$/.test(first)) { angle = parseFloat(first); i = 1; }
    else if (first.indexOf('to ') === 0) {
      const kw = { 'top': 0, 'right': 90, 'bottom': 180, 'left': 270,
        'top right': 45, 'right top': 45, 'bottom right': 135, 'right bottom': 135,
        'bottom left': 225, 'left bottom': 225, 'top left': 315, 'left top': 315 };
      const m = first.slice(3).trim();
      angle = kw[m] !== undefined ? kw[m] : 180; i = 1;
    }
    const stops = [];
    for (; i < parts.length; i++) {
      const seg = parts[i].trim();
      const cm = seg.match(/rgba?\([^)]+\)|#[0-9a-fA-F]{3,8}/);
      if (!cm) continue;
      const col = parseColor(cm[0]);
      if (!col) continue;
      const pm = seg.match(/([\d.]+)%/);
      stops.push({ color: col.hex, opacity: col.opacity, pos: pm ? parseFloat(pm[1]) / 100 : null });
    }
    if (!stops.length) return null;
    if (stops[0].pos === null) stops[0].pos = 0;
    if (stops[stops.length - 1].pos === null) stops[stops.length - 1].pos = 1;
    for (let j = 1; j < stops.length - 1; j++)
      if (stops[j].pos === null) stops[j].pos = j / (stops.length - 1);
    return { angle, stops };
  }

  // ::before / ::after 텍스트 콘텐츠 ('none'/빈문자면 '')
  function pseudoText(el, which) {
    const ps = getComputedStyle(el, which);
    const c = ps.content;
    if (!c || c === 'none' || c === 'normal' || c === '""' || c === "''") return '';
    return c.replace(/^["']|["']$/g, '');
  }

  // ::before / ::after 배경/그라디언트 박스 (토글 노브 등 순수 장식 도형)
  function pseudoBoxes(el, r, ox, oy) {
    const out = [];
    for (const which of ['::before', '::after']) {
      const ps = getComputedStyle(el, which);
      if (!ps.content || ps.content === 'none') continue;
      const w = parseFloat(ps.width) || 0, h = parseFloat(ps.height) || 0;
      const bg = parseColor(ps.backgroundColor);
      const grad = parseGradient(ps.backgroundImage);
      if (!(bg || grad) || w < 1 || h < 1) continue;
      let px = r.x - ox, py = r.y - oy;
      if (ps.position === 'absolute') {
        const l = parseFloat(ps.left), t = parseFloat(ps.top);
        if (!isNaN(l)) px += l;
        if (!isNaN(t)) py += t;
      }
      const st = {};
      if (bg) { st.fill = bg.hex; if (bg.opacity < 1) st.fillOpacity = bg.opacity; }
      if (grad) st.gradient = grad;
      const rr = radiusPx(ps, w, h);
      if (rr > 0) st.cornerRadius = Math.round(rr * 100) / 100;
      out.push({ kind: 'rect', name: 'pseudo' + which, role: 'pseudo', _a: { x: px, y: py, w, h }, style: st });
    }
    return out;
  }

  function weightNum(fw) {
    if (fw === 'normal') return 400;
    if (fw === 'bold') return 700;
    const n = parseInt(fw, 10);
    return isNaN(n) ? 400 : n;
  }

  function alignMap(a) {
    if (a === 'center') return 'CENTER';
    if (a === 'right' || a === 'end') return 'RIGHT';
    if (a === 'justify') return 'JUSTIFIED';
    return 'LEFT';
  }

  function visualStyle(cs, w, h) {
    const fill = parseColor(cs.backgroundColor);
    // 4면 균일 테두리만 stroke 로 인정 (border-bottom 같은 단일 구분선이 전체 박스 테두리로
    // 그려지는 것을 방지 -> "없던 테두리" 문제 해결)
    const bt = parseFloat(cs.borderTopWidth) || 0, br = parseFloat(cs.borderRightWidth) || 0,
          bb = parseFloat(cs.borderBottomWidth) || 0, bl = parseFloat(cs.borderLeftWidth) || 0;
    const uniform = bt > 0 && bt === br && bt === bb && bt === bl && cs.borderTopStyle !== 'none';
    const stroke = uniform ? parseColor(cs.borderTopColor) : null;
    const style = {};
    if (fill) { style.fill = fill.hex; if (fill.opacity < 1) style.fillOpacity = fill.opacity; }
    const grad = parseGradient(cs.backgroundImage);
    if (grad) style.gradient = grad;   // 그라디언트가 있으면 배경 이미지로 상단 렌더
    if (stroke) { style.stroke = stroke.hex; style.strokeWidth = bt; }
    const r = radiusPx(cs, w, h);
    if (r > 0) style.cornerRadius = Math.round(r * 100) / 100;
    const op = parseFloat(cs.opacity);
    if (!isNaN(op) && op < 1) style.opacity = op;
    const shadows = parseShadows(cs.boxShadow);
    if (shadows.length) style.shadow = shadows;
    return style;
  }

  function textStyle(cs) {
    const fam = (cs.fontFamily || 'sans-serif').split(',')[0].replace(/["']/g, '').trim();
    const fs = parseFloat(cs.fontSize) || 14;
    let lh = cs.lineHeight === 'normal' ? Math.round(fs * 1.4) : (parseFloat(cs.lineHeight) || Math.round(fs * 1.4));
    const col = parseColor(cs.color) || { hex: '#000000' };
    const ls = (cs.letterSpacing && cs.letterSpacing !== 'normal') ? parseFloat(cs.letterSpacing) : 0;
    const dl = (cs.textDecorationLine || cs.textDecoration || '');
    const decoration = dl.indexOf('line-through') >= 0 ? 'STRIKETHROUGH'
                     : dl.indexOf('underline') >= 0 ? 'UNDERLINE' : 'NONE';
    return { fontFamily: fam, fontSize: fs, fontWeight: weightNum(cs.fontWeight),
             fill: col.hex, lineHeight: lh, textAlign: alignMap(cs.textAlign),
             letterSpacing: Math.round((ls || 0) * 100) / 100, decoration: decoration };
  }

  function hasVisual(style) {
    return !!(style.fill || style.stroke || style.gradient);
  }

  function layoutHint(cs) {
    if ((cs.display || '').indexOf('flex') < 0) return null;
    const col = (cs.flexDirection || 'row').startsWith('column');
    const gap = parseFloat(cs.gap || cs.columnGap || cs.rowGap) || 0;
    const pad = [parseFloat(cs.paddingTop) || 0, parseFloat(cs.paddingRight) || 0,
                 parseFloat(cs.paddingBottom) || 0, parseFloat(cs.paddingLeft) || 0];
    const jc = cs.justifyContent || 'flex-start';
    const ai = cs.alignItems || 'stretch';
    const prim = jc.indexOf('center') >= 0 ? 'CENTER'
               : jc.indexOf('end') >= 0 ? 'MAX'
               : jc.indexOf('between') >= 0 ? 'SPACE_BETWEEN' : 'MIN';
    const cnt = ai.indexOf('center') >= 0 ? 'CENTER'
              : ai.indexOf('end') >= 0 ? 'MAX' : 'MIN';
    return { mode: col ? 'VERTICAL' : 'HORIZONTAL', gap, padding: pad,
             primaryAlign: prim, counterAlign: cnt };
  }

  const SKIP_TAGS = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT']);

  // 컨테이너의 직접 텍스트 노드별 실제 렌더 사각형을 Range 로 측정.
  // (아이콘+텍스트가 나란한 flex 컨테이너에서 텍스트가 컨테이너 좌상단에 놓여
  //  아이콘 위에 겹치던 문제를 해결 -> 텍스트를 정확한 위치에 배치)
  function textRuns(el, ox, oy) {
    const runs = [];
    for (const node of Array.from(el.childNodes)) {
      if (node.nodeType !== 3) continue;
      const txt = node.textContent.replace(/\s+/g, ' ').trim();
      if (!txt) continue;
      const range = document.createRange();
      range.selectNodeContents(node);
      const rects = range.getClientRects();
      if (!rects.length) continue;
      let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
      for (const rc of rects) {
        if (rc.width < 0.5 && rc.height < 0.5) continue;
        x0 = Math.min(x0, rc.left); y0 = Math.min(y0, rc.top);
        x1 = Math.max(x1, rc.right); y1 = Math.max(y1, rc.bottom);
      }
      if (x1 <= x0 || y1 <= y0) continue;
      runs.push({ text: txt, _a: { x: x0 - ox, y: y0 - oy, w: x1 - x0, h: y1 - y0 } });
    }
    return runs;
  }

  function build(el, ox, oy) {
    if (SKIP_TAGS.has(el.tagName)) return null;
    if ((el.getAttribute('class') || '').indexOf('no-print') >= 0) return null;
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return null;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return null;

    const a = { x: r.x - ox, y: r.y - oy, w: r.width, h: r.height };
    const tag = el.tagName.toLowerCase();
    const role = roleFromClass(el);

    if (tag === 'svg') return { kind: 'vector', name: role || 'icon', role, _a: a, svg: el.outerHTML };
    if (tag === 'img') return { kind: 'image', name: role || 'image', role, _a: a, src: el.currentSrc || el.src };

    const kids = Array.from(el.children);
    const rawText = Array.from(el.childNodes)
      .filter(n => n.nodeType === 3).map(n => n.textContent).join(' ').replace(/\s+/g, ' ').trim();
    // ::before/::after 텍스트(예: stat 화살표 "▲ ")를 실제 텍스트 앞뒤로 병합
    const pre = pseudoText(el, '::before'), post = pseudoText(el, '::after');
    const directText = (pre + rawText + post).trim();
    const pbox = pseudoBoxes(el, r, ox, oy);   // 배경형 의사요소(토글 노브 등)

    const vstyle = visualStyle(cs, r.width, r.height);

    // 텍스트 리프 (자식 엘리먼트 없음)
    if (kids.length === 0) {
      if (pbox.length) {
        // 장식 의사요소가 있으면 프레임으로 감싸 텍스트 + 도형을 함께 담는다
        const children = [];
        if (directText) children.push({ kind: 'text', name: directText.slice(0, 24), role: null, _a: a,
                                        text: directText, style: textStyle(cs) });
        children.push(...pbox);
        return { kind: 'frame', name: role || tag, role, _a: a, style: vstyle, children };
      }
      if (directText) {
        const n = { kind: 'text', name: directText.slice(0, 24), role, _a: a,
                    text: directText, style: textStyle(cs) };
        if (hasVisual(vstyle)) n.bgStyle = vstyle; // 배경 있는 단일 텍스트(버튼/뱃지)
        return n;
      }
      if (hasVisual(vstyle)) return { kind: 'rect', name: role || tag, role, _a: a, style: vstyle };
      return null;
    }

    // 컨테이너: 직접 텍스트는 Range 로 실제 렌더 위치를 구해 개별 배치
    const children = [];
    const runs = textRuns(el, ox, oy);
    if (pre && runs.length) runs[0].text = (pre + runs[0].text).trim();
    if (post && runs.length) runs[runs.length - 1].text = (runs[runs.length - 1].text + post).trim();
    if (!runs.length && directText) runs.push({ text: directText, _a: a }); // 폴백
    for (const run of runs) {
      children.push({ kind: 'text', name: run.text.slice(0, 24), role: null, _a: run._a,
                      text: run.text, style: textStyle(cs) });
    }
    for (const c of kids) {
      const cn = build(c, ox, oy);
      if (cn) children.push(cn);
    }
    children.push(...pbox);
    const node = { kind: 'frame', name: role || tag, role, _a: a, style: vstyle, children };
    const lay = layoutHint(cs);
    if (lay) node.layout = lay;
    return node;
  }

  function isPassthrough(n) {
    return n.kind === 'frame' && !n.role && !n.layout
      && !(n.style && (n.style.fill || n.style.stroke)) && (n.children || []).length > 0;
  }

  function flatten(node) {
    if (!node.children) return node;
    const out = [];
    for (let c of node.children) {
      c = flatten(c);
      if (isPassthrough(c)) out.push(...(c.children || []));
      else out.push(c);
    }
    node.children = out;
    return node;
  }

  // _a(절대=wireframe 기준) -> box(부모 상대) 변환
  function toRelative(node, px, py) {
    const a = node._a;
    node.box = { x: Math.round((a.x - px) * 100) / 100, y: Math.round((a.y - py) * 100) / 100,
                 w: Math.round(a.w * 100) / 100, h: Math.round(a.h * 100) / 100 };
    if (node.children) for (const c of node.children) toRelative(c, a.x, a.y);
    delete node._a;
    return node;
  }

  const sections = Array.from(document.querySelectorAll('.screen-section'))
    .filter(s => s.id && s.id !== 'cover-page');

  const compCount = {};
  const screens = [];
  for (const sec of sections) {
    const wf = sec.querySelector('.wireframe-wrap') || sec;
    const wr = wf.getBoundingClientRect();
    if (wr.width < 1 || wr.height < 1) continue;

    // 화면 이름: meta-box 의 screen-id-badge 다음 텍스트 또는 탭 라벨
    let name = sec.id;
    const tab = document.querySelector('.tab-btn[data-screen="' + sec.id + '"], [data-screen="' + sec.id + '"]');
    if (tab && tab.textContent.trim()) name = tab.textContent.trim();
    const badge = sec.querySelector('.screen-id-badge');
    if (badge && badge.parentElement) {
      const t = badge.parentElement.textContent.replace(badge.textContent, '').trim();
      if (t) name = t.split('\n')[0].trim().slice(0, 40);
    }

    const root = build(wf, wr.x, wr.y);
    if (!root) continue;
    flatten(root);
    toRelative(root, 0, 0);   // root._a 는 이미 wireframe 기준(0,0)이므로 (0,0)으로 정규화
    root.name = sec.id + ' · ' + name;

    // 컴포넌트 후보 집계
    (function tally(n) {
      if (n.role && ['btn','input','select','card','product-card','badge','indicator','stat-card','tab-btn','sidebar-item'].includes(n.role))
        compCount[n.role] = (compCount[n.role] || 0) + 1;
      (n.children || []).forEach(tally);
    })(root);

    // 설명 패널(Description 표) 추출 -> 화면별 annotations
    let annotations = null;
    const dw = sec.querySelector('.desc-wrap');
    if (dw) {
      const heads = Array.from(dw.querySelectorAll('thead th')).map(th => th.textContent.replace(/\s+/g, ' ').trim());
      const rows = Array.from(dw.querySelectorAll('tbody tr'))
        .map(tr => Array.from(tr.children).map(td => td.textContent.replace(/\s+/g, ' ').trim()))
        .filter(r => r.some(c => c));
      const h3 = dw.querySelector('h3');
      if (rows.length) annotations = { title: (h3 ? h3.textContent : 'Description').trim(), heads, rows };
    }

    const screen = { id: sec.id, name, frame: { w: Math.round(wr.width), h: Math.round(wr.height) }, root };
    if (annotations) screen.annotations = annotations;
    screens.push(screen);
  }

  const components = Object.entries(compCount)
    .filter(([, c]) => c >= 2).map(([key, count]) => ({ key, count }));

  return { screens, components };
}
"""


def main():
    if len(sys.argv) < 2:
        print("사용법: python3 extract.py <input.html> [output.json]")
        sys.exit(1)

    in_path = Path(sys.argv[1]).resolve()
    if not in_path.exists():
        print("입력 파일 없음:", in_path)
        sys.exit(1)
    out_path = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else in_path.with_suffix(".scene.json")

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        # chromium 우선, 없으면 시스템 chrome
        try:
            browser = p.chromium.launch(headless=True)
        except Exception:
            browser = p.chromium.launch(headless=True, channel="chrome")
        page = browser.new_page(viewport={"width": 1600, "height": 1200},
                                device_scale_factor=1)
        page.goto(in_path.as_uri(), wait_until="networkidle")
        try:
            page.evaluate("document.fonts && document.fonts.ready")
            page.wait_for_timeout(600)
        except Exception:
            pass

        data = page.evaluate(PAGE_SCRIPT)
        browser.close()

    scene = {
        "schemaVersion": "1.0",
        "source": in_path.name,
        "project": in_path.stem,
        "screens": data["screens"],
        "components": data["components"],
    }
    out_path.write_text(json.dumps(scene, ensure_ascii=False, indent=2), encoding="utf-8")

    n_nodes = 0
    def count(n):
        nonlocal n_nodes
        n_nodes += 1
        for c in n.get("children", []):
            count(c)
    for s in scene["screens"]:
        count(s["root"])

    print("OK ->", out_path)
    print("  screens:", len(scene["screens"]), "| nodes:", n_nodes,
          "| components:", ", ".join(f"{c['key']}({c['count']})" for c in scene["components"]))


if __name__ == "__main__":
    main()
