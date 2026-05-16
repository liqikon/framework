# sb-creator-pptx 적용 예시

## 예시 1 — 기본 적용

```bash
python3 ~/.claude/skills/sb-creator-pptx/scripts/inject.py \
  "02.설계/022.Admin-화면설계/KB_Admin_화면설계서_20260512.html"
```

결과:
- 백업: `KB_Admin_화면설계서_20260512.html.bak.html`
- 주입: `</body>` 직전에 다운로드 버튼 + 변환 스크립트
- PPTX 출력 파일명: `KB_Admin_화면설계서_20260512_editable.pptx`

## 예시 2 — 셀렉터 커스터마이즈

대상 HTML이 `<section class="slide-page">` 단위로 구성된 경우:

```bash
python3 ~/.claude/skills/sb-creator-pptx/scripts/inject.py \
  "my-storyboard.html" \
  --selector ".slide-page"
```

## 예시 3 — 슬라이드 비율 변경 (4:3 표준)

```bash
python3 ~/.claude/skills/sb-creator-pptx/scripts/inject.py \
  "my-deck.html" \
  --slide-width 10 \
  --slide-height 7.5
```

## 예시 4 — UI 버튼 없이 스크립트만 주입 (콘솔에서 직접 호출)

```bash
python3 ~/.claude/skills/sb-creator-pptx/scripts/inject.py \
  "design.html" \
  --no-button
```

브라우저 콘솔에서 `downloadPPTX()` 호출하여 변환.

## 예시 5 — 출력 파일명 지정

```bash
python3 ~/.claude/skills/sb-creator-pptx/scripts/inject.py \
  "wireframe.html" \
  --output-name "MyStoryboard_v1"
```

PPTX 출력: `MyStoryboard_v1.pptx`

## 재실행

이미 주입된 HTML에 다시 실행하면 기존 주입 블록을 찾아 **최신 버전으로 교체**합니다.
마커(`<!-- BEGIN sb-creator-pptx -->` ~ `<!-- END sb-creator-pptx -->`)로 식별.

## 사용자 작업 순서

1. Claude에게 요청: "이 HTML에 PPTX 다운로드 버튼 추가해줘"
2. Claude가 `inject.py` 실행 (대상 파일·셀렉터 결정)
3. 사용자가 브라우저로 HTML 열기
4. 우상단 "PPTX 다운로드" 버튼 클릭
5. 자동 생성된 PPTX 파일 PowerPoint로 열어 편집

## 다른 HTML 구조에서 동작 확인

| 셀렉터 패턴 | 사용 예 |
| --- | --- |
| `.screen-section` | KB Admin 화면설계서 (기본값) |
| `.slide` | 일반 슬라이드 데크 |
| `.page` | 페이지 단위 와이어프레임 |
| `section.frame` | 프레임 단위 디자인 시안 |
| `[data-slide]` | 데이터 속성 기반 |

복합 셀렉터도 가능: `--selector "section.wireframe:not(.draft)"`
