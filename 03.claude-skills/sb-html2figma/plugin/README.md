# sb-creator → Figma 플러그인 설치 안내

이 폴더(`plugin/`)는 `scene.json`을 Figma 캔버스에 편집 가능한 네이티브 노드(Frame·Text·Shape)로 그려 넣는 Figma 플러그인입니다. 빌드가 필요 없는 plain JS이며, 아래 절차로 바로 설치·실행합니다.

## 구성 파일

| 파일 | 용도 |
|------|------|
| `manifest.json` | Figma 플러그인 매니페스트 (Import 대상) |
| `code.js` | 노드 생성 메인 로직 |
| `ui.html` | scene.json 주입 UI (테마 대응) |

## 사전 준비

- **Figma 데스크톱 앱** (macOS/Windows). 웹 버전에서는 개발 플러그인 Import가 불가합니다.
- 변환할 `scene.json` 파일 — sb-html2figma 스킬(`scripts/extract.py`)로 HTML에서 추출합니다.

## 설치 (최초 1회)

1. Figma 데스크톱 앱을 엽니다.
2. 메뉴 → **Plugins → Development → Import plugin from manifest…**
3. 이 폴더의 **`manifest.json`** 을 선택합니다.
4. 목록에 **sb-creator → Figma** 가 등록되면 완료입니다. (재빌드·재설치 불필요)

## 실행

1. 아무 Figma 파일이나 엽니다.
2. **Plugins → Development → sb-creator → Figma** 실행.
3. 열린 창에서 `scene.json`을 **파일로 불러오거나** 내용을 붙여넣습니다.
4. 옵션(페이지 프레임 / iPhone 프레임 / 설명 패널 / 오토레이아웃 / 화면 간격)을 확인합니다.
5. **가져오기** 클릭 → 화면들이 좌→우로 나란히 생성됩니다.

## 폰트 (정확도)

플러그인 폰트 폴백 순서: **Pretendard**(설치 시) → **Noto Sans KR**(Figma 내장, 미설치 시 자동) → Inter → Roboto.
가장 원본에 가깝게 하려면 시스템에 **Pretendard**를 설치하세요. 미설치 상태여도 한글은 Noto Sans KR로 올바르게 렌더됩니다.

## 문제 해결

| 증상 | 원인 / 조치 |
|------|-------------|
| 메뉴에 플러그인이 안 보임 | 웹 버전 사용 중 — 데스크톱 앱에서 다시 Import |
| 텍스트가 세로로 쌓임 | 구버전 폰트 폴백 — 이 폴더의 최신 `code.js`인지 확인 후 재Import |
| 한글이 네모(□)로 보임 | 폰트 미해석 — Figma를 재시작하거나 Noto Sans KR 폴백 확인 |
| 노드가 안 생김 | scene.json이 손상됨 — `extract.py`로 다시 추출 |

## 참고

이 플러그인은 자동 생성된 `scene.json`을 대상으로 합니다. scene.json은 손으로 만들지 말고 반드시 sb-html2figma 스킬의 `extract.py`로 렌더링 추출하세요(CSS Grid/Flexbox 좌표 계산 때문).
