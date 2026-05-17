---
name: sb-creator-pptx
description: HTML 화면설계서·스토리보드(wireframe)를 편집 가능한 PowerPoint(.pptx)로 변환하는 다운로드 버튼·스크립트를 HTML 파일에 주입합니다. 변환된 PPTX는 이미지가 아닌 네이티브 도형·텍스트박스로 출력되어 텍스트 수정·도형 색상 변경이 가능합니다. 사용 트리거 - "이 HTML에 PPTX 다운로드 기능 추가", "화면설계서를 편집 가능한 PPT로", "스토리보드 PPTX 변환 버튼 넣어줘", "HTML to editable PPT", "PPTX export 버튼".
type: skill
---

# SB Creator (HTML → Editable PPTX)

HTML로 작성된 화면설계서·와이어프레임·스토리보드를 PowerPoint 편집 가능한 형태(.pptx)로 변환하는 다운로드 버튼·JS 스크립트를 대상 HTML 파일에 주입하는 스킬입니다.

## 핵심 특징

| 항목 | 내용 |
| --- | --- |
| **변환 방식** | DOM 요소 → PptxGenJS `addShape` / `addText` (네이티브 도형·텍스트박스) |
| **편집 가능 여부** | O (텍스트 더블클릭 수정, 도형 크기·색상 변경 가능) |
| **이미지 캡처 방식** | X (html2canvas 미사용) |
| **외부 라이브러리** | PptxGenJS 3.12.0 (CDN 동적 로드, 사전 설치 불필요) |
| **슬라이드 분할** | 7.5in 단위 자동 페이지 분할 (세로로 긴 화면) |
| **글꼴 처리** | "맑은 고딕" 매핑 (Mac/Windows 양 플랫폼 호환), monospace → Consolas |
| **단일행 자동 감지** | 짧은 한글(배지·버튼·H1)이 자릿수 단위로 잘리지 않도록 `wrap: false` |
| **폭 버퍼** | Pretendard 대비 Malgun Gothic 폭 차이 보정 (단일행 +15%, 다행 +8%) |
| **버튼 배치** | `auto` (기본): HTML에 `.download-btns` 영역이 있으면 표지 우측 상단 PDF 버튼 옆에 삽입(`cover` 모드). 없으면 화면 우상단 고정 버튼(`fixed` 모드)로 fallback. `--placement` 인자로 강제 가능. |

## 워크플로우

1. **대상 HTML 확인**: 변환하려는 HTML 경로 받기
2. **HTML 구조 파악**:
   - 슬라이드 단위가 되는 셀렉터 확인 (기본값 `.screen-section`)
   - 다른 셀렉터면 `--selector` 인자로 전달
3. **주입 실행**: `scripts/inject.py` 실행
   - 백업 자동 생성 (`<원본>.bak.html`)
   - 기존 PPTX 버튼·스크립트(현재 마커 + 레거시 마커 모두) 있으면 최신 버전으로 교체
   - 버튼 배치는 `auto` 감지:
     - 대상 HTML에 `<div class="download-btns ...">`가 있으면 그 안에 PDF 버튼 옆으로 삽입
     - 없으면 `<body>` 끝부분에 고정 우상단 버튼으로 삽입
   - 스크립트는 항상 `<body>` 끝부분에 삽입
4. **사용 안내**:
   - cover 모드: 표지 우측 상단의 PDF 버튼 옆 "PPTX" 클릭
   - fixed 모드: 화면 우상단 고정 "PPTX 다운로드" 클릭

## 사용법

```bash
# 기본 (섹션 셀렉터 = .screen-section, 슬라이드 13.33 x 7.5)
python3 ~/.claude/skills/sb-creator-pptx/scripts/inject.py <대상.html>

# 셀렉터 커스터마이즈
python3 ~/.claude/skills/sb-creator-pptx/scripts/inject.py <대상.html> --selector ".my-slide"

# 슬라이드 비율 커스터마이즈
python3 ~/.claude/skills/sb-creator-pptx/scripts/inject.py <대상.html> --slide-width 13.33 --slide-height 7.5

# 출력 파일명 (기본: 원본명 + _editable.pptx)
python3 ~/.claude/skills/sb-creator-pptx/scripts/inject.py <대상.html> --output-name "My_Storyboard"

# 백업 비활성화
python3 ~/.claude/skills/sb-creator-pptx/scripts/inject.py <대상.html> --no-backup

# 버튼 배치 강제 (auto | cover | fixed). 기본 auto (download-btns 감지)
python3 ~/.claude/skills/sb-creator-pptx/scripts/inject.py <대상.html> --placement cover
python3 ~/.claude/skills/sb-creator-pptx/scripts/inject.py <대상.html> --placement fixed
```

## 변환 시 주의사항

| 항목 | 동작 |
| --- | --- |
| **CSS 그림자·그라데이션·blur·transform** | 평면 색상으로 단순화 |
| **SVG 아이콘** | 제외 (텍스트와 도형만 변환) |
| **`<table>` 요소** | 셀별로 도형 + 텍스트박스로 분해 → 네이티브 표 아님 |
| **세로로 긴 섹션** | 7.5in 단위 자동 분할 (예: 18in 높이 → 3장 슬라이드) |
| **글꼴** | "맑은 고딕" 단일 매핑 — 시스템에 없으면 PPT가 fallback |
| **사용자 측정 폭** | 일시적으로 body 폭 1440px로 강제 후 측정, 변환 종료 후 복원 |

## 트러블슈팅

| 증상 | 원인 / 대응 |
| --- | --- |
| 글자 줄바꿈 깨짐 ("완료" → "완/료") | 단일행 감지 미작동 → 해당 요소에 `white-space: nowrap` 추가하거나 inject.py 재실행으로 최신 버전 적용 |
| 슬라이드 폭이 좁아 보임 | 사용자 브라우저 창이 1440px보다 좁음 → 변환 시 body 폭 자동 1440px 강제 |
| PPTX 슬라이드 수가 화면 수보다 많음 | 세로로 긴 섹션 자동 분할 결과 (정상) |
| 글꼴이 다르게 보임 | OS에 맑은 고딕이 없음 → Office 365 Mac은 자동 다운로드, 그 외 PPT fallback |
| `Cannot read properties of null` | 셀렉터에 매칭되는 요소가 없음 → `--selector` 인자 확인 |

## 파일 구조

```
sb-creator-pptx/
├── SKILL.md                          # 본 문서
├── scripts/
│   ├── inject.py                     # HTML 주입 도구 (Python 3)
│   ├── pptx-export.js                # 변환 JavaScript 본체 (템플릿)
│   ├── button-snippet-cover.html     # 표지 영역 내부 삽입용 버튼 (PDF 옆자리)
│   └── button-snippet-fixed.html     # 화면 우상단 고정 wrapper 버튼 (fallback)
└── references/
    └── usage-examples.md             # 적용 예시
```
