# scene.json 스키마 (schemaVersion 1.0)

`extract.py`가 출력하고 Figma 플러그인(`code.js`)이 소비하는 중간 포맷. 좌표 단위는 px, 색상은 `#rrggbb`.

## 최상위

```jsonc
{
  "schemaVersion": "1.0",
  "source": "사용자_피시_화면설계서_20250412.html",  // 입력 파일명
  "project": "사용자_피시_화면설계서_20250412",        // 확장자 제외
  "screens": [ /* Screen[] */ ],
  "components": [ { "key": "btn", "count": 32 } ]      // 2회 이상 등장한 role 집계(정보용)
}
```

## Screen

```jsonc
{
  "id": "scr-001",                    // .screen-section 의 id
  "name": "Screen홈 / 카탈로그",        // 탭 라벨 또는 screen-id-badge 옆 텍스트
  "frame": { "w": 1152, "h": 1060 },  // wireframe-wrap 의 렌더 크기
  "root": { /* Node */ }              // 화면 루트 프레임 (box 는 0,0 기준)
}
```

## Node (공통)

| 필드 | 타입 | 설명 |
|------|------|------|
| `kind` | `frame\|text\|rect\|vector\|image` | 노드 종류 |
| `name` | string | 레이어 이름(role 또는 태그 또는 텍스트 앞 24자) |
| `role` | string\|null | sb-creator 컴포넌트 역할(btn/input/card/indicator/badge 등). 없으면 null |
| `box` | `{x,y,w,h}` | **부모 프레임 기준 상대 좌표**. root 는 (0,0) |
| `style` | object | 시각 스타일(아래) — frame/rect |
| `children` | Node[] | frame 전용 |

### style (frame/rect 시각 스타일)
```jsonc
{
  "fill": "#ffffff",         // 배경색(있을 때만)
  "fillOpacity": 0.5,        // fill 불투명도 < 1 일 때만
  "stroke": "#e5e7eb",       // 4면 균일 테두리만 인정
  "strokeWidth": 1,
  "cornerRadius": 8,
  "opacity": 0.6             // 요소 전체 opacity < 1 일 때만
}
```
> 단일 구분선(border-bottom 등)은 stroke로 인정하지 않는다 — "없던 테두리가 박스 전체에 그려지는" 문제를 막기 위함.

### text 전용
```jsonc
{
  "kind": "text",
  "text": "입금 요청하기",
  "style": {
    "fontFamily": "Pretendard",
    "fontSize": 14,
    "fontWeight": 600,        // normal=400, bold=700
    "fill": "#111827",
    "lineHeight": 20,         // px
    "textAlign": "LEFT|CENTER|RIGHT|JUSTIFIED",
    "letterSpacing": 0,       // px
    "decoration": "NONE|UNDERLINE|STRIKETHROUGH"
  },
  "bgStyle": { /* style */ }  // 배경 있는 단일 텍스트(버튼/뱃지)일 때만 — 텍스트+배경을 한 프레임으로 생성
}
```

### vector 전용
```jsonc
{ "kind": "vector", "svg": "<svg>…</svg>" }   // createNodeFromSvg 로 생성
```

### image 전용
```jsonc
{ "kind": "image", "src": "https://…" }        // 외부 이미지는 회색 플레이스홀더로 대체
```

### layout (frame, flex 컨테이너일 때만 — Auto Layout 옵션 ON에서 사용)
```jsonc
{
  "mode": "HORIZONTAL|VERTICAL",
  "gap": 8,
  "padding": [top, right, bottom, left],
  "primaryAlign": "MIN|CENTER|MAX|SPACE_BETWEEN",
  "counterAlign": "MIN|CENTER|MAX"
}
```

## 추출 규칙 요약

- `.screen-section`(id 있고 `cover-page` 아님)만 순회, 내부 `.wireframe-wrap`을 루트로 삼음
- `display:none`/`visibility:hidden`/크기 <1px/`no-print`/`script,style,noscript` 제외
- 순수 패스스루 프레임(role 없음·layout 없음·배경/테두리 없음·자식 있음)은 평탄화(flatten)로 접힘
- role 은 `KNOWN_ROLES` 클래스 목록에서 매칭 (btn, input, select, card, product-card, badge, indicator, stat-card, tab-btn, sidebar-item 등)
