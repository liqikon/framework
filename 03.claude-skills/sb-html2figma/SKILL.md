---
name: sb-html2figma
description: >
  Converts an sb-creator HTML Screen Design Document (화면설계서/wireframe) into a Figma-importable
  scene.json by rendering the HTML with Playwright and extracting each screen's absolute layout,
  colors, borders, typography, text, and flex auto-layout hints. The scene.json is then imported
  into Figma via the bundled "sb-creator → Figma" plugin to produce editable native Frame/Text/Shape
  nodes (not flat images). Use when the user asks to: convert a 화면설계서/wireframe HTML to Figma,
  make a scene.json for Figma import, "HTML to Figma", "피그마로 변환", "sb-html2figma", or turn screen
  design HTML into editable Figma frames.
---

# sb-creator HTML → Figma (scene.json 생성기)

sb-creator로 만든 화면설계서 HTML을 Figma 네이티브 디자인(편집 가능한 Frame·Text·Shape)으로 옮기기 위한 **중간 산출물 `scene.json`** 을 생성한다.

```
HTML 화면설계서 ──(이 스킬: Playwright 렌더링)──▶ scene.json ──(Figma 플러그인)──▶ Figma 캔버스
```

Figma는 외부에서 `.fig`를 만들 수 없고 REST API로도 노드를 생성하지 못한다. 따라서 좌표·스타일은 **반드시 렌더링해서** 추출하고(이 스킬), 실제 노드 생성은 **Figma 플러그인(Plugin API)** 으로 한다.

## 언제 쓰나

- 사용자가 sb-creator/sb-md-creator로 만든 **화면설계서 HTML**을 Figma로 옮기고 싶을 때
- "화면설계서를 피그마로", "HTML to Figma", "scene.json 만들어줘" 요청

전제: 입력 HTML은 sb-creator 계열 구조여야 한다 (`.screen-section` + 내부 `.wireframe-wrap`). 임의의 웹페이지가 아니다.

## 워크플로우

### 1단계 — 입력 확인
- 사용자가 준 HTML 경로를 확인한다. 없으면 프로젝트의 `02.기획문서/*화면설계서*.html` 등을 찾아 후보를 제시한다.
- HTML이 sb-creator 구조인지 가볍게 확인한다 (`grep -c 'screen-section' <file>` 이 1 이상).

### 2단계 — 사전 준비 (최초 1회, 이미 되어 있으면 생략)
```bash
python3 -c "import playwright" 2>/dev/null || pip install playwright
playwright install chromium   # 시스템 Chrome가 있으면 자동 폴백되므로 실패해도 계속 진행
```

### 3단계 — 추출 실행
스킬 번들의 추출기를 호출한다. `SKILL_DIR`는 이 SKILL.md가 있는 디렉토리다.
```bash
python3 "$SKILL_DIR/scripts/extract.py" "<입력 HTML 경로>" "<출력 scene.json 경로>"
```
- 출력 경로를 사용자가 지정하지 않으면 입력 HTML과 같은 폴더에 `<이름>.scene.json`으로 저장한다.
- 성공 시 스크립트가 `screens: N | nodes: M | components: ...` 요약을 출력한다. 이 수치를 사용자에게 보고한다.

### 4단계 — Figma 가져오기 안내
scene.json을 만든 뒤, Figma 플러그인으로 넣는 방법을 안내한다. 플러그인 자산은 **이 스킬 번들 안에**
동봉되어 있다: `$SKILL_DIR/plugin/`(manifest.json·code.js·ui.html). 별도 다운로드가 필요 없다.

1. Figma 데스크톱 앱 → Plugins → Development → **Import plugin from manifest…** → `$SKILL_DIR/plugin/manifest.json` (최초 1회, 빌드 불필요)
2. Plugins → Development → **sb-creator → Figma** 실행
3. 생성한 `scene.json`을 파일로 불러오거나 붙여넣기 → **가져오기**
4. 화면들이 좌→우로 나란히 생성됨

| 옵션 | 설명 |
|------|------|
| 페이지 프레임(가운데 정렬·여백) | 각 화면을 지정 폭(기본 1440px) 중앙에 배치 |
| iPhone 디바이스 프레임 | 모바일(`.mobile-frame` 등) 화면에 라운드 베젤·다이나믹 아일랜드·홈 인디케이터·그림자 적용. 기본 ON |
| 설명 패널 + 넘버링 | 각 화면 옆에 Description 표(No./Element/설명)를 네이티브 텍스트로 생성하고 화면 위 번호 마커도 함께 표시 |
| 주석 마커(번호 원) 포함 | 화면 위 번호 원만 표시(설명 표 없이). 기본 OFF = 깔끔한 UI |
| Auto Layout 적용 | flex 힌트가 있는 프레임에 오토레이아웃(실험적). 기본 OFF = 절대배치. 배치가 flex 방향과 어긋나면 자동으로 절대배치 폴백 |
| 화면 간격 | 생성 프레임 사이 간격(px) |

## scene.json 스키마

상세 필드는 `references/scene-schema.md` 참조. 핵심만:
- 최상위: `schemaVersion`, `source`, `project`, `screens[]`, `components[]`
- `screens[]`: `{ id, name, frame{w,h}, root }`
- 노드(`root` 및 `children[]`): `kind`(frame|text|rect|vector|image), `name`, `role`, `box{x,y,w,h}`(부모 상대 좌표), `style`, 그리고 text는 `text`+`style`, vector는 `svg`, image는 `src`

**scene.json을 직접 손으로 만들지 말 것.** 좌표가 CSS Grid/Flexbox로 계산되므로 반드시 `extract.py`로 렌더링 추출해야 정확하다.

## 폰트 안내
원본은 Pretendard. 플러그인 폰트 폴백: Pretendard(설치 시) → **Noto Sans KR**(한글 내장, 미설치 시 자동) → Inter → Roboto. 최상의 정확도는 Pretendard 설치.

## 한계 (M1~M2 기준)
- 외부 이미지는 회색 플레이스홀더(네트워크 차단 설계)
- CSS Grid는 절대배치 처리(오토레이아웃 근사는 flex만)
- 컴포넌트/베리언트 미생성 — `components[]`에 후보만 집계
- `no-print` 클래스 요소와 표지(`cover-page`)는 제외
