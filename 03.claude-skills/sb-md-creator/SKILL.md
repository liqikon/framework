---
name: sb-md-creator
description: >
  마크다운 화면설계서를 HTML 화면설계서로 변환합니다.
  SCR-NNN 형식의 화면 ID, 화면명, URL, UI 컴포넌트 표, 레이아웃 ASCII art가 포함된
  마크다운 파일을 sb-creator 스타일의 단일 HTML 파일로 자동 변환합니다.
  사용 시점: "화면설계서 HTML로 변환해줘", "마크다운 화면설계서를 HTML로 만들어줘",
  "화면설계서.md를 sb-creator 형식으로", "wireframe HTML 만들어줘" 요청 시.
---

# Markdown 화면설계서 → HTML 변환기

마크다운 화면설계서를 파싱하여 [sb-creator](~/.claude/skills/sb-creator/) 스타일의
단일 자기완결형 HTML 파일로 변환합니다.

## 전제 조건

- `sb-creator` 스킬이 `~/.claude/skills/sb-creator/`에 설치되어 있어야 합니다
- 입력 마크다운은 SCR-NNN 화면 ID 체계를 따릅니다

## 워크플로우

### 1. 마크다운 파싱

파서 스크립트로 화면 데이터를 추출합니다:

```bash
python3 ~/.claude/skills/sb-md-creator/scripts/parse_md.py <input.md> /tmp/screens.json
```

출력 JSON 구조:
```json
{
  "project_name": "...",
  "version": "v1.0",
  "date": "YYYY-MM-DD",
  "screen_count": 31,
  "screens": [
    {
      "id": "SCR-001",
      "name": "로그인",
      "url": "/login",
      "platform": "모바일+PC",
      "priority": "P0",
      "meta": { "URL": "...", "플랫폼": "...", "관련 API": "..." },
      "layouts": ["ASCII art string"],
      "components": [{ "컴포넌트": "...", "타입": "...", "설명": "...", "인터랙션": "..." }],
      "states": [{ "상태": "...", "조건": "...", "표시 내용": "..." }]
    }
  ]
}
```

### 2. sb-creator 템플릿 읽기

```
~/.claude/skills/sb-creator/assets/template.html   ← HTML 기본 골격
~/.claude/skills/sb-creator/references/components.md  ← 와이어프레임 컴포넌트 패턴
```

### 3. HTML 생성 전략

**파싱된 JSON을 기반으로 template.html을 직접 수정합니다.**

#### 3-1. 커버 페이지 메타데이터 업데이트
- 프로젝트명, 버전, 날짜, 화면 수 삽입

#### 3-2. 탭 네비게이션 생성
화면 수가 많으면 그룹(유저단 / 관리자단)으로 묶어 탭 버튼 생성:
```html
<button class="tab-btn" onclick="scrollTo('scr-001')">SCR-001 로그인</button>
```

#### 3-3. 각 화면 섹션 생성

```html
<div class="screen-section" id="scr-001">
  <!-- meta-box: ID 배지, URL, 플랫폼, 관련 기능, 관련 API -->
  <div class="meta-box">...</div>

  <!-- 와이어프레임 + 어노테이션 패널 -->
  <div class="content-wrap">
    <div class="wireframe-wrap">
      <div class="ind-container">
        <!-- ASCII art → HTML 컴포넌트로 변환 -->
        <!-- indicator 원 배치 -->
      </div>
    </div>
    <div class="desc-wrap">
      <!-- Description 표: No. / 컴포넌트 / 설명 / 인터랙션 -->
    </div>
  </div>
</div>
```

### 4. ASCII Art → 와이어프레임 매핑 규칙

마크다운의 ASCII 레이아웃을 보고 컴포넌트를 선택합니다:

| ASCII 패턴 | HTML 컴포넌트 |
|-----------|--------------|
| `[버튼명]` / `+---버튼---+` | `<button>` (btn-dark or btn-outline) |
| `+---input---+` | `<input type="text">` 모양의 div |
| `[로고]` / `[이미지]` | placeholder 박스 (회색 fill) |
| 상품 카드 격자 | `.card` 컴포넌트 반복 |
| 테이블/목록 | `<table>` with light-bg 헤더 |
| 사이드바 | `.sidebar` 컴포넌트 |
| 헤더 바 | `.header-bar` 컴포넌트 |
| 탭 UI | `.tab-bar` 컴포넌트 |
| 모달 | 회색 오버레이 + 흰색 카드 |
| 검색 바 | 입력 + 버튼 인라인 배치 |

**컴포넌트 상세 패턴**: `~/.claude/skills/sb-creator/references/components.md` 참조

### 5. 인디케이터 배치

UI 컴포넌트 표의 각 행 = 인디케이터 1개. 
와이어프레임 내 해당 컴포넌트 위치에 오렌지 원 배치:

```html
<div class="indicator" style="top:120px;left:45px;">1</div>
```

Description 표와 번호가 1:1 매칭되어야 합니다.

### 6. 화면 수가 많을 때 처리 (20개 이상)

화면이 많으면 **배치(batch)** 처리합니다:
- P0 우선순위 화면 먼저 생성 → 저장
- 나머지 화면 추가 → 최종 파일 완성
- 중간에 사용자에게 진행 상황 보고

### 7. 출력 파일 저장

입력 파일과 같은 디렉토리에 저장:
- 입력: `02.기획문서/화면설계서.md`
- 출력: `02.기획문서/화면설계서.html`

## 디자인 시스템 (sb-creator 동일)

| Token | Hex | 용도 |
|-------|-----|------|
| darkest | `#212529` | 헤딩, 본문 |
| dark | `#343a40` | 사이드바, 활성 탭 |
| mid | `#6c757d` | 라벨 |
| border | `#ced4da` | 입력 테두리 |
| light-bg | `#e9ecef` | 테이블 헤더 |
| bg | `#f8f9fa` | 배경 |
| white | `#fff` | 카드 배경 |
| accent | `#e67700` | 인디케이터 원 |

폰트: **Pretendard** (Google Fonts CDN)

## 주요 제약

- 화면 섹션 부모: `position:relative; z-index:1`
- 인디케이터: `z-index:9999`
- 카드 overflow: `visible` (인디케이터 클리핑 방지)
- 우측 패널: `position:sticky; top:52px; max-height:calc(100vh - 60px); overflow-y:auto`
- 인쇄: `@page { size: landscape; }`
