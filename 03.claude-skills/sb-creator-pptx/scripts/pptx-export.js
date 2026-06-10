/* ============================================================
 * sb-creator-pptx — HTML to Editable PPTX Export
 *   - 각 SECTION_SELECTOR 요소를 슬라이드로 변환
 *   - DOM 요소 → PptxGenJS addShape/addText (편집 가능 네이티브 형태)
 *   - body 폭 1440px 강제 측정으로 사용자 창 크기 무관 일정한 스케일
 *   - 단일행 자동 감지 → wrap:false (짧은 한글 잘림 방지)
 *   - 폰트 폭 보정 (단일행 +15%, 다행 +8%)
 *   - 세로로 긴 화면은 SLIDE_HEIGHT 단위로 자동 분할 (멀티 슬라이드)
 *
 * 템플릿 변수 (inject.py가 치환):
 *   __SECTION_SELECTOR__   기본 .screen-section
 *   __SLIDE_WIDTH__         기본 13.33 (인치, Widescreen)
 *   __SLIDE_HEIGHT__        기본 7.5
 *   __OUTPUT_NAME__         기본 PPTX_Export
 * ============================================================ */

async function downloadPPTX(e) {
  if (e && e.stopPropagation) e.stopPropagation();
  const btn = document.getElementById('btn-pptx');
  const progress = document.getElementById('download-progress');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" style="animation:sbpptx-spin 1s linear infinite;"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg> 생성 중...';
  }
  if (progress) progress.style.display = '';

  if (!document.getElementById('sbpptx-spin-style')) {
    const s = document.createElement('style');
    s.id = 'sbpptx-spin-style';
    s.textContent = '@keyframes sbpptx-spin{to{transform:rotate(360deg)}}';
    document.head.appendChild(s);
  }

  const hideEls = document.querySelectorAll('.no-print, .sbpptx-hide');
  const bodyOrigCss = document.body.style.cssText;
  const htmlOrigCss = document.documentElement.style.cssText;

  try {
    await loadScript([
      'https://cdn.jsdelivr.net/npm/pptxgenjs@3.12.0/dist/pptxgen.bundle.js',
      'https://cdn.jsdelivr.net/gh/gitbrent/PptxGenJS@3.12.0/dist/pptxgen.bundle.js',
      'https://unpkg.com/pptxgenjs@3.12.0/dist/pptxgen.bundle.js',
    ], () => typeof PptxGenJS !== 'undefined');

    const pptx = new PptxGenJS();
    const SLIDE_W = __SLIDE_WIDTH__;
    const SLIDE_H = __SLIDE_HEIGHT__;
    pptx.defineLayout({ name: 'WIDE', width: SLIDE_W, height: SLIDE_H });
    pptx.layout = 'WIDE';

    // 측정 일관성을 위해 본문 폭을 1440px로 고정
    hideEls.forEach(el => el.dataset._origDisplay = el.style.display);
    hideEls.forEach(el => el.style.display = 'none');
    document.documentElement.style.width = '1440px';
    document.documentElement.style.overflowX = 'hidden';
    document.body.style.width = '1440px';
    document.body.style.minWidth = '1440px';
    document.body.style.maxWidth = '1440px';
    void document.body.offsetHeight;
    window.scrollTo(0, 0);
    await new Promise(r => setTimeout(r, 400));

    const sections = document.querySelectorAll('__SECTION_SELECTOR__');
    if (sections.length === 0) {
      throw new Error('변환할 섹션이 없습니다. 셀렉터: __SECTION_SELECTOR__');
    }

    for (let i = 0; i < sections.length; i++) {
      const section = sections[i];
      const isCover = (i === 0);

      const sRect = section.getBoundingClientRect();
      const sx = sRect.left + window.scrollX;
      const sy = sRect.top + window.scrollY;
      const sw = sRect.width;
      const sh = sRect.height;
      if (sw < 10 || sh < 10) continue;

      // 가로 폭 기준 단일 스케일 (인치/픽셀)
      const scale = SLIDE_W / sw;
      const sectionHInches = sh * scale;
      const numPages = Math.max(1, Math.ceil(sectionHInches / SLIDE_H));
      const verticalCenterOffset = (numPages === 1) ? Math.max(0, (SLIDE_H - sectionHInches) / 2) : 0;

      for (let p = 0; p < numPages; p++) {
        if (progress) {
          progress.textContent = `${i + 1}/${sections.length}` + (numPages > 1 ? ` (페이지 ${p + 1}/${numPages})` : '');
        }
        const slide = pptx.addSlide();
        slide.background = { color: isCover ? '212529' : 'F8F9FA' };

        const pageOffsetY = verticalCenterOffset - p * SLIDE_H;
        const elements = section.querySelectorAll('*');
        // 1차 패스: 인디케이터·.on-top 외 모든 요소
        for (const el of elements) {
          if (el.classList && (el.classList.contains('indicator') || el.classList.contains('on-top'))) continue;
          sbpptxRenderElement(pptx, slide, el, sx, sy, scale, 0, pageOffsetY, SLIDE_W, SLIDE_H);
        }
        // 2차 패스: 인디케이터·.on-top을 맨 위 레이어로
        for (const el of elements) {
          if (!el.classList || (!el.classList.contains('indicator') && !el.classList.contains('on-top'))) continue;
          sbpptxRenderElement(pptx, slide, el, sx, sy, scale, 0, pageOffsetY, SLIDE_W, SLIDE_H);
        }
        await new Promise(r => requestAnimationFrame(r));
      }
    }

    // 파일명에 타임스탬프 추가: YYYYMMDD_HHMM
    const _ts = (() => {
      const n = new Date();
      const z = v => String(v).padStart(2, '0');
      return `${n.getFullYear()}${z(n.getMonth()+1)}${z(n.getDate())}_${z(n.getHours())}${z(n.getMinutes())}`;
    })();
    await pptx.writeFile({ fileName: `__OUTPUT_NAME___${_ts}.pptx` });
  } catch (err) {
    console.error('PPTX generation failed:', err);
    alert('PPTX 생성 실패: ' + err.message);
  } finally {
    document.body.style.cssText = bodyOrigCss;
    document.documentElement.style.cssText = htmlOrigCss;
    hideEls.forEach(el => { el.style.display = el.dataset._origDisplay || ''; delete el.dataset._origDisplay; });
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg> PPTX 다운로드';
    }
    if (progress) progress.style.display = 'none';
  }
}

function sbpptxRenderElement(pptx, slide, el, baseX, baseY, scale, offsetX, offsetY, slideW, slideH) {
  const tag = el.tagName;
  if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'LINK' || tag === 'META' || tag === 'TITLE' || tag === 'HEAD' || tag === 'TEMPLATE' || tag === 'BR' || tag === 'HR') return;
  if (tag === 'svg' || tag === 'SVG' || tag === 'PATH' || tag === 'CIRCLE' || tag === 'LINE' || tag === 'RECT' || tag === 'POLYLINE' || tag === 'POLYGON') return;
  if (el.classList && (el.classList.contains('no-print') || el.classList.contains('sbpptx-hide'))) return;
  if (el.closest && (el.closest('.no-print') || el.closest('.sbpptx-hide'))) return;

  const rect = el.getBoundingClientRect();
  if (rect.width < 0.5 || rect.height < 0.5) return;

  const style = window.getComputedStyle(el);
  if (style.display === 'none' || style.visibility === 'hidden') return;
  if (parseFloat(style.opacity) === 0) return;

  const rx = rect.left + window.scrollX;
  const ry = rect.top + window.scrollY;
  const x = offsetX + (rx - baseX) * scale;
  const y = offsetY + (ry - baseY) * scale;
  const w = rect.width * scale;
  const h = rect.height * scale;

  if (x >= slideW + 0.05 || y >= slideH + 0.05) return;
  if (x + w <= -0.05 || y + h <= -0.05) return;
  if (w < 0.02 || h < 0.02) return;

  // (1) 배경/테두리 도형
  const bg = style.backgroundColor;
  let bgHex = null;
  if (!sbpptxIsTransparent(bg)) {
    bgHex = sbpptxRgbToHex(bg);
    const alpha = sbpptxGetAlpha(bg);
    if (alpha !== null && alpha < 1) {
      const parentBg = sbpptxFindOpaqueParentBg(el);
      bgHex = sbpptxBlendHex(parentBg, bgHex, alpha);
    }
  }
  // backgroundColor 투명 + background-image 그래디언트 → 첫 색상으로 폴백
  if (!bgHex && style.backgroundImage && style.backgroundImage.includes('gradient')) {
    const m = style.backgroundImage.match(/rgba?\([^)]+\)|#[0-9a-fA-F]{6,8}|#[0-9a-fA-F]{3}\b/);
    if (m) {
      const c = m[0];
      bgHex = c.startsWith('#')
        ? (c.length === 4 ? c.slice(1).split('').map(h => h+h).join('') : c.slice(1)).toUpperCase().slice(0, 6)
        : sbpptxRgbToHex(c);
    }
  }
  const bw = parseFloat(style.borderTopWidth) || 0;
  const bColor = bw > 0 ? sbpptxRgbToHex(style.borderTopColor) : null;
  const radiusPx = parseFloat(style.borderTopLeftRadius) || 0;

  if (bgHex || (bw > 0 && bColor)) {
    const sx = Math.max(0, x);
    const sy = Math.max(0, y);
    const sw = Math.min(x + w, slideW) - sx;
    const sh = Math.min(y + h, slideH) - sy;
    if (sw > 0.02 && sh > 0.02) {
      const opts = {
        x: sx, y: sy, w: sw, h: sh,
        fill: bgHex ? { color: bgHex } : { type: 'none' },
        line: (bw > 0 && bColor) ? { color: bColor, width: Math.max(0.25, bw * 0.6) } : { type: 'none' },
      };
      // 도형 종류 선택 (단순화):
      //   - 정사각형(1:1) + border-radius ≥ 절반 → OVAL (완전한 원, 예: 넘버링 인디케이터)
      //   - 그 외 모든 도형 → RECTANGLE (직각, HTML 둥근 모서리는 무시)
      const minDim = Math.min(rect.width, rect.height);
      const aspectRatio = Math.max(rect.width, rect.height) / Math.max(0.1, minDim);
      const fullyRounded = radiusPx >= minDim / 2 - 1;
      const isCircle = fullyRounded && aspectRatio <= 1.2;
      const shapeType = isCircle ? pptx.shapes.OVAL : pptx.shapes.RECTANGLE;
      try { slide.addShape(shapeType, opts); } catch (err) { /* ignore */ }
    }
  }

  // (1-b) ::after 가상 요소 렌더 (예: 토글 스위치 핸들 등 CSS pseudo로 만들어진 동그라미)
  try {
    const after = window.getComputedStyle(el, '::after');
    if (after) {
      const contentVal = after.content;
      if (contentVal && contentVal !== 'none' && contentVal !== 'normal') {
        const aW = parseFloat(after.width) || 0;
        const aH = parseFloat(after.height) || 0;
        const aBg = after.backgroundColor;
        if (aW > 0 && aH > 0 && !sbpptxIsTransparent(aBg)) {
          const aLeft = parseFloat(after.left) || 0;
          const aTop = parseFloat(after.top) || 0;
          const ax = x + aLeft * scale;
          const ay = y + aTop * scale;
          const aw = aW * scale;
          const ah = aH * scale;
          const aR = parseFloat(after.borderTopLeftRadius) || 0;
          const aFullyRounded = aR >= Math.min(aW, aH) / 2 - 1;
          const aIsCircle = aFullyRounded && Math.abs(aW - aH) < 2;
          const aShape = aIsCircle ? pptx.shapes.OVAL : pptx.shapes.RECTANGLE;
          slide.addShape(aShape, {
            x: ax, y: ay, w: aw, h: ah,
            fill: { color: sbpptxRgbToHex(aBg) },
            line: { type: 'none' },
          });
        }
      }
    }
  } catch (err) { /* ignore */ }

  // (2-a) 폼 요소(input/select/textarea) — 직접 표시 텍스트 추출하여 렌더
  if (el.tagName === 'INPUT' || el.tagName === 'SELECT' || el.tagName === 'TEXTAREA') {
    let formText = '';
    let isPlaceholder = false;
    try {
      if (el.tagName === 'SELECT') {
        const opt = el.querySelector('option[selected]') || el.querySelector('option');
        if (opt) formText = String(opt.textContent || '').trim();
      } else {
        formText = String(el.value || '').trim();
        if (!formText) {
          const ph = el.getAttribute('placeholder');
          if (ph) {
            formText = String(ph).trim();
            isPlaceholder = !!formText;
          }
        }
        if (!formText) {
          const inputType = el.type || el.getAttribute('type') || '';
          if (inputType === 'date') {
            formText = 'YYYY.MM.DD';
            isPlaceholder = true;
          } else if (inputType === 'time') {
            formText = 'HH:MM';
            isPlaceholder = true;
          } else if (inputType === 'datetime-local') {
            formText = 'YYYY.MM.DD HH:MM';
            isPlaceholder = true;
          }
        }
      }
    } catch (e) { /* form access failed */ }

    if (formText) {
      // 폼 요소는 본문 텍스트 → 7pt 고정
      const fontPt = 7;
      const color = isPlaceholder ? '6C757D' : (sbpptxRgbToHex(style.color) || '212529');
      const fontFace = sbpptxFontName(style.fontFamily);
      const padL = (parseFloat(style.paddingLeft) || 0) * scale;
      const padR = (parseFloat(style.paddingRight) || 0) * scale;
      const tx = Math.max(0, x + padL);
      const ty = Math.max(0, y);
      const tw = Math.max(0.3, Math.min(slideW - tx, w - padL - padR + w * 0.2));
      const th = Math.max(0.15, Math.min(slideH - ty, h));
      const opts = {
        x: tx, y: ty, w: tw, h: th,
        fontFace: fontFace,
        fontSize: fontPt,
        color: color,
        align: 'left',
        valign: 'middle',
        margin: 0,
        wrap: false,
        fit: 'shrink',
        isTextBox: true,
      };
      try {
        slide.addText(formText, opts);
      } catch (err) {
        console.warn('form addText failed:', err, formText, opts);
      }
    }
    return;
  }

  // (2) 텍스트 리프 요소만 텍스트박스로 추가
  if (sbpptxIsTextLeaf(el)) {
    const text = (el.textContent || '').replace(/\s+/g, ' ').trim();
    if (text && text.length > 0 && text.length < 2500) {
      const fontPx = parseFloat(style.fontSize) || 13;
      // 폰트 규칙:
      //   - 본문 글씨 (HTML font-size < 20px) → 7pt 고정 (전체 영역 통일)
      //   - 헤딩·큰 숫자 (HTML font-size ≥ 20px) → 8~14pt 클램프 (h1, stat-value 등 강조)
      const rawPt = fontPx * scale * 72;
      const isLargeText = fontPx >= 20;
      const fontPt = isLargeText
        ? Math.max(8, Math.min(14, rawPt))
        : 7;
      const color = sbpptxRgbToHex(style.color) || '212529';
      const fw = parseInt(style.fontWeight) || 400;
      const bold = fw >= 600;
      const italic = style.fontStyle === 'italic';
      const fontFace = sbpptxFontName(style.fontFamily);
      let align = 'left';
      if (style.textAlign === 'center') align = 'center';
      else if (style.textAlign === 'right') align = 'right';
      // flex의 justify-content:center도 가로 중앙 정렬로 처리
      if (style.display === 'flex' && style.justifyContent === 'center') align = 'center';
      // .desc-table/.desc-wrap/.always-top 영역은 예외 없이 상단 정렬
      const forceTop = el.closest && (el.closest('.desc-table') || el.closest('.desc-wrap') || el.closest('.always-top'));
      const valign = forceTop ? 'top' :
                     (style.display === 'flex' && style.alignItems === 'center') ? 'middle' :
                     (style.verticalAlign === 'middle') ? 'middle' : 'top';

      // 단일행 텍스트 자동 감지:
      //   - white-space:nowrap/pre, 또는
      //   - 버튼·배지·사이드바·탭 항목, 또는
      //   - 요소 높이 < line-height × 1.8
      let lineHeightPx = parseFloat(style.lineHeight);
      if (!isFinite(lineHeightPx) || style.lineHeight === 'normal') {
        lineHeightPx = fontPx * 1.2;
      }
      const nowrapCss = style.whiteSpace === 'nowrap' || style.whiteSpace === 'pre';
      const tagName = el.tagName;
      const cls = el.classList || { contains: () => false };
      const isButtonLike = tagName === 'BUTTON' || tagName === 'A'
                          || cls.contains('btn') || cls.contains('badge')
                          || cls.contains('sidebar-item') || cls.contains('tab-btn')
                          || cls.contains('chip') || cls.contains('pill') || cls.contains('tag');
      const isSingleLine = nowrapCss || isButtonLike || (rect.height < lineHeightPx * 1.8);

      // padding inset
      const padT = (parseFloat(style.paddingTop) || 0) * scale;
      const padL = (parseFloat(style.paddingLeft) || 0) * scale;
      const padR = (parseFloat(style.paddingRight) || 0) * scale;
      const padB = (parseFloat(style.paddingBottom) || 0) * scale;

      // 텍스트박스 폭 버퍼: 단일행 +15% / Description 영역 0% / 기타 다행 +5%
      // Description 영역은 우측 슬라이드 가장자리 안전 여백 확대 (텍스트가 모서리에 닿지 않도록)
      const inDescAreaText = el.closest && (el.closest('.desc-wrap') || el.closest('.desc-table') || el.closest('.always-top'));
      const widthBufferRatio = isSingleLine ? 0.15 : (inDescAreaText ? 0 : 0.05);
      const widthBuffer = w * widthBufferRatio;
      const rightSafe = inDescAreaText ? 0.15 : 0.05;

      const tx = Math.max(0, x + padL);
      const ty = Math.max(0, y + padT);
      const naturalRight = x + w - padR + widthBuffer;
      const trEdge = Math.min(slideW - rightSafe, naturalRight);
      const tbEdge = Math.min(slideH, y + h - padB);
      const tw = Math.max(0.1, trEdge - tx);
      const th = Math.max(0.1, tbEdge - ty);

      try {
        slide.addText(text, {
          x: tx, y: ty, w: tw, h: th,
          fontFace: fontFace,
          fontSize: fontPt,
          color: color,
          bold: bold,
          italic: italic,
          align: align,
          valign: valign,
          margin: 0,
          wrap: !isSingleLine,
          shrinkText: true,
          autoFit: true,
          isTextBox: true,
        });
      } catch (err) { /* ignore */ }
    }
  }
}

function sbpptxIsTextLeaf(el) {
  if (!el.textContent || !el.textContent.trim()) return false;
  if (el.children.length === 0) return true;
  for (const child of el.children) {
    const t = child.tagName;
    if (t === 'svg' || t === 'BR' || t === 'IMG' || t === 'INPUT' || t === 'HR') continue;
    if (child.textContent && child.textContent.trim()) return false;
  }
  return true;
}

function sbpptxRgbToHex(s) {
  if (!s) return null;
  if (s === 'transparent') return null;
  const m = s.match(/rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)/);
  if (!m) return null;
  const a = s.match(/rgba?\([^,]+,[^,]+,[^,]+,\s*([\d.]+)\s*\)/);
  if (a && parseFloat(a[1]) === 0) return null;
  const r = Math.round(parseFloat(m[1]));
  const g = Math.round(parseFloat(m[2]));
  const b = Math.round(parseFloat(m[3]));
  return ((r << 16) | (g << 8) | b).toString(16).padStart(6, '0').toUpperCase();
}

function sbpptxIsTransparent(c) {
  if (!c) return true;
  if (c === 'transparent') return true;
  if (c === 'rgba(0, 0, 0, 0)') return true;
  const a = c.match(/rgba?\([^,]+,[^,]+,[^,]+,\s*([\d.]+)\s*\)/);
  if (a && parseFloat(a[1]) === 0) return true;
  return false;
}

// rgba 알파 값 추출
function sbpptxGetAlpha(c) {
  if (!c) return null;
  const a = c.match(/rgba\([^,]+,[^,]+,[^,]+,\s*([\d.]+)\s*\)/);
  if (a) return parseFloat(a[1]);
  if (c.startsWith('rgb(')) return 1;
  return null;
}

// 상위 요소를 거슬러 올라가며 불투명한 background-color 검색
function sbpptxFindOpaqueParentBg(el) {
  let p = el.parentElement;
  while (p) {
    const ps = window.getComputedStyle(p);
    const pbg = ps.backgroundColor;
    if (!sbpptxIsTransparent(pbg)) {
      const alpha = sbpptxGetAlpha(pbg);
      if (alpha === null || alpha >= 1) {
        return sbpptxRgbToHex(pbg);
      }
    }
    p = p.parentElement;
  }
  return 'FFFFFF';
}

// 알파 블렌딩 (bg + alpha*fg)
function sbpptxBlendHex(bgHex, fgHex, alpha) {
  if (!bgHex || !fgHex) return fgHex || bgHex;
  const br = parseInt(bgHex.slice(0, 2), 16);
  const bgC = parseInt(bgHex.slice(2, 4), 16);
  const bb = parseInt(bgHex.slice(4, 6), 16);
  const fr = parseInt(fgHex.slice(0, 2), 16);
  const fgC = parseInt(fgHex.slice(2, 4), 16);
  const fb = parseInt(fgHex.slice(4, 6), 16);
  const r = Math.round(alpha * fr + (1 - alpha) * br);
  const g = Math.round(alpha * fgC + (1 - alpha) * bgC);
  const b = Math.round(alpha * fb + (1 - alpha) * bb);
  return ((r << 16) | (g << 8) | b).toString(16).padStart(6, '0').toUpperCase();
}

function sbpptxFontName(ff) {
  if (!ff) return '맑은 고딕';
  const f = ff.toLowerCase();
  if (f.includes('mono') || f.includes('courier') || f.includes('consolas')) return 'Consolas';
  return '맑은 고딕';
}

// 여러 CDN을 순차 시도하는 폴백 로더.
//   - src: 단일 URL 또는 URL 배열 (앞에서부터 차례로 시도)
//   - isReady: (선택) 로드 성공 판정 함수. 라이브러리 전역이 실제로 정의됐는지 확인
//     (사내/교육망 프록시가 200 + 빈/에러 본문을 반환하는 경우까지 방어)
function loadScript(src, isReady) {
  const urls = Array.isArray(src) ? src : [src];
  const ready = () => (typeof isReady === 'function' ? isReady() : true);
  function tryLoad(i) {
    return new Promise((resolve, reject) => {
      if (i >= urls.length) { reject(new Error('모든 CDN에서 라이브러리 로드 실패: ' + urls.join(', '))); return; }
      const url = urls[i];
      if (ready()) { resolve(); return; }
      const existing = document.querySelector(`script[src="${url}"]`);
      if (existing && existing.dataset._sbpptxLoaded === '1' && ready()) { resolve(); return; }
      const s = existing || document.createElement('script');
      s.src = url;
      s.onload = () => {
        s.dataset._sbpptxLoaded = '1';
        if (ready()) resolve();
        else tryLoad(i + 1).then(resolve, reject); // 200이지만 라이브러리 미정의 → 다음 CDN
      };
      s.onerror = () => {
        if (s.parentNode) s.parentNode.removeChild(s); // 실패한 태그 제거 후 다음 CDN
        tryLoad(i + 1).then(resolve, reject);
      };
      if (!existing) document.head.appendChild(s);
    });
  }
  return tryLoad(0);
}
