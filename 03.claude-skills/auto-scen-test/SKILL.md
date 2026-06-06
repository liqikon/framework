---
name: auto-scen-test
description: 단위테스트 시나리오 엑셀(.xlsx/.csv)을 기반으로 웹 챗봇 UI를 Playwright로 자동 구동하여, 케이스별 질의 입력 → 응답 캡처 → 스크린샷 → 자동 판정(Pass/Fail/Block)까지 수행하고 결과를 결과 XLSX에 자동 기록한다. "자동 테스트", "시나리오 테스트 돌려줘", "단위테스트 자동화", "auto-scen-test" 요청 시 사용. 임의의 웹 챗봇 URL과 시나리오 엑셀에 범용 적용된다(헤더 자동 매핑 + 셀렉터 폴백). 도메인별 셀렉터·판정룰 예시가 기본 번들로 포함되어 있으며, 대상에 맞게 교체하거나 그대로 폴백 동작시킬 수 있다.
---

# auto-scen-test — 시나리오 기반 자동 테스트

테스트 시나리오 엑셀의 각 케이스(질의 + 검증 포인트)를 읽어, 챗봇 웹 UI에 자동으로 질의를 입력하고 응답을 캡처·스크린샷·판정한 뒤 결과 XLSX에 기록하는 스킬이다.

## 처리 흐름

```
시나리오 파일(.xlsx/.csv) 로드
        │
        ▼  케이스별 반복
  ┌─ 입력창에 질의 fill → 전송(Enter/버튼)
  ├─ 응답 스트리밍 안정화 대기
  ├─ 응답 텍스트(질의 전후 diff) 추출
  ├─ 전체 페이지 스크린샷 → shots_dir/TC-xxx.png
  └─ 검증 포인트 키워드 → 룰 평가 (Pass/Fail/Block)
        │
        ▼
  결과 XLSX 갱신 (테스트결과/실행일시/응답요약/증적이미지 임베드/비고)
  + "결과 요약" 시트 자동 집계 (Pass/Fail 카운트, 시나리오별 진행률)
```

## 입력 / 출력

- **입력**: 시나리오 파일(.xlsx/.csv). 컬럼명은 **자동 인식**된다(아래 "헤더 자동 매핑"). 표준 4필드 — 식별자(id) / 시나리오(scenario) / 질의(query) / 검증포인트(checkpoint) 중 **id·query는 필수**, scenario·checkpoint는 선택. 헤더 행 위치(앞에 안내문/병합셀이 있어도)와 컬럼 순서는 무관하다.
- **출력**:
  - 결과 XLSX (`단위테스트결과` 시트 + `결과 요약` 시트). 시나리오 컬럼 뒤에 `테스트결과 / 실행일시 / 응답 요약 / 증적 이미지 / 검증자/비고` 컬럼 추가.
  - 스크린샷 PNG (케이스 ID당 1장, 셀에 임베드)

## 사용 절차

작업 디렉터리는 스킬 폴더의 `scripts/`. **`uv`가 있으면 `uv run`을, 없으면 시스템 `python3`을 사용**한다.

### 1단계 — 환경 확인 및 설치 (최초 1회)

```bash
cd ~/.claude/skills/auto-scen-test/scripts
python3 -m pip install --user playwright openpyxl
python3 -m playwright install chromium
```

### 1.5단계 — 헤더 매핑 확인 (새 시나리오 파일일 때 권장)

브라우저 없이 컬럼 인식 결과만 빠르게 검증한다. 다른 프로젝트 파일이면 먼저 이걸로 확인한다.

```bash
python3 run_tests.py --map-check --scenario-file "<시나리오 파일>"
```

`id / scenario / query / checkpoint` 가 어떤 실제 헤더로 매핑됐는지와 케이스 수가 출력된다.
특이한 컬럼명이라 매핑이 틀리거나 "필수 컬럼 매핑 실패"가 나오면 `config.py`의
`COLUMN_ALIASES_EXTRA` 에 별칭을 추가한다. 예:

```python
COLUMN_ALIASES_EXTRA = {"query": ["사용자 발화"], "id": ["케이스No"]}
```

### 2단계 — 셀렉터 자동 탐색 (새 챗봇 URL일 때만)

대상 챗봇 UI가 처음이면 입력창/전송버튼 셀렉터를 먼저 확인한다.

```bash
python3 run_tests.py --discover --url "<챗봇 URL>"
```

출력된 textarea/input/button 목록과 `page_snapshot.html`을 보고, 필요 시 `config.py`의 `SELECTORS["input"]`, `["submit"]` 맨 앞에 정확한 셀렉터를 추가한다. `config.py`의 `SELECTORS`에는 범용 폴백(`input[type="text"]`, `textarea`, `[contenteditable]`, `[role="textbox"]` 등)이 들어 있어 일반적인 챗봇은 별도 설정 없이 동작하는 경우가 많다. 자동 매칭이 안 될 때만 이 단계로 정확한 셀렉터를 보강한다.

### 3단계 — 소수 케이스로 스모크 테스트

전체를 돌리기 전에 항상 소수로 동작을 검증한다 (셀렉터/대기시간/판정 룰 확인).

```bash
python3 run_tests.py \
  --scenario-file "<시나리오.xlsx 또는 .csv 절대경로>" \
  --result-file   "<결과.xlsx 절대경로>" \
  --shots-dir     "<스크린샷 폴더 절대경로>" \
  --url           "<챗봇 URL>" \
  --limit 3
```

결과 XLSX와 스크린샷을 열어 응답이 제대로 캡처됐는지, 판정이 합리적인지 확인한다.

### 4단계 — 전체 실행

```bash
python3 run_tests.py \
  --scenario-file "<...>" --result-file "<...>" \
  --shots-dir "<...>" --url "<...>"
```

옵션:
- `--only TC-S01-01` : 특정 케이스만
- `--scenario S01` : 특정 시나리오ID만
- `--limit N` : 처음 N건만
- `--headless` : 브라우저 창 없이 실행 (CI/백그라운드)
- `--wait N` : 질의 전송 후 응답 캡처까지 고정 대기(초). 기본 20. 응답이 잘리면 키운다.

### 5단계 — 결과 보고

실행 후 콘솔에 `Pass: n | Fail: n | Block: n | Total: n` 요약이 출력된다. 사용자에게:
- Pass/Fail/Block 합계와 비율
- Fail/Block 케이스 ID 목록과 사유(응답 요약 기반)
- 결과 XLSX 및 스크린샷 폴더 경로
를 간결히 보고한다. Fail이 많으면 판정 룰 오탐 가능성(아래)을 함께 안내한다.

## 헤더 자동 매핑 (범용성 핵심)

`column_mapper.py`가 시나리오 파일의 헤더를 별칭 사전으로 인식해 표준 4필드로 매핑한다. 프로젝트마다 컬럼명이 달라도 코드 수정 없이 동작한다.

| 표준 필드 | 인식하는 헤더 예시 |
|---|---|
| `id` (필수) | 테스트ID, TC ID, 케이스번호, Test Case ID, No, 순번 |
| `query` (필수) | 입력(사용자 질의), 질의, 질문, 프롬프트, Query, Input, 사용자 발화 |
| `scenario` | 시나리오ID, 시나리오, 그룹, 대분류, Scenario, Category |
| `checkpoint` | 검증 포인트, 검증기준, 검증항목, 합격기준, Expected, Acceptance |

- 헤더 행은 앞부분 15행 중 매핑 품질이 가장 높은 행을 자동 선택(안내문/병합셀 무시).
- 한 파일에 `검증 포인트`와 `기대 결과`가 모두 있으면 `검증*` 컬럼을 checkpoint로 우선 선택(판정 룰이 검증 포인트 기준이므로).
- 별칭으로도 못 잡으면 `config.py`의 `COLUMN_ALIASES_EXTRA`로 보강.

## 필수 입력 확인 (인자 생략 시)

`--url`(챗봇 주소)과 `--scenario-file`(시나리오 파일)은 대상마다 달라지므로 **반드시 사용자에게 확인한다**. `config.py`의 기본값은 동작하지 않는 예시 플레이스홀더(`your-chatbot-host.example.com`, `~/auto-scen-test/...`)이므로, 둘 중 하나라도 주어지지 않으면 실행하지 말고 먼저 사용자에게 대상 URL과 시나리오 파일 경로를 묻는다. 파일·폴더 경로는 항상 절대경로로 `--scenario-file` / `--result-file` / `--shots-dir`를 명시한다.

## 결과 파일이 없을 때

`--result-file` 이 가리키는 XLSX가 없으면 시나리오 파일로부터 결과 XLSX를 생성한다:

```bash
python3 build_result_xlsx.py --scenario-file "<시나리오>" --result-file "<생성할 결과.xlsx>"
```

## 자동 판정 룰 (evaluator.py)

`검증 포인트` 컬럼의 문자열에서 키워드를 찾아 `RULES` 딕셔너리의 룰을 적용한다. 매칭 룰의 80% 이상 통과 시 Pass. 매칭 룰이 없으면 응답 길이(≥100자)로 fallback 판정. 룰은 키워드 매칭 기반이라 표현이 다르면 오탐이 날 수 있으므로:
- Fail 케이스는 응답 요약을 직접 보고 실제 결함인지 룰 오탐인지 구분한다.
- 반복 오탐 키워드는 `evaluator.py`의 `RULES`에 항목을 추가/수정한다.
- 의미 검증이 필요하면 LLM-as-Judge 보강을 권고한다(선택).

`evaluator.py`에는 범용 예시 룰(차트/표/이미지/링크 등 UI 요소, 목록·단계·출처·거절 등 응답 형식)이 들어 있다. `검증 포인트` 컬럼에 룰 키워드가 포함되면 해당 룰로 판정하고, **매칭되는 키워드가 없으면 자동으로 응답 길이 기반 fallback 판정으로 동작**한다. 도메인 특화 검증이 필요하면 `RULES`에 키워드·판정식을 추가하거나 LLM-as-Judge로 보강한다.

## UI-only 케이스 주의

차트 렌더링/색상 강조/멀티턴 "다시 보기" 같은 케이스는 텍스트 응답이 아닌 UI 요소 검증이 필요하다. 1차 룰 판정 후 스크린샷으로 수동 보정하는 구조다. `config.py`의 `CASE_MODE`에 예시 케이스 ID가 등록되어 있으며(번들 예시), 대상 시나리오의 해당 케이스 ID로 교체해 쓴다. 등록되지 않은 케이스는 일반 텍스트 판정으로 처리된다.

## 트러블슈팅

- **입력창 미탐지** → `--discover`로 셀렉터 재탐색 후 `config.py` 보강.
- **응답이 짧게 잘림** → `--wait` 값을 키운다(예 30~40).
- **Chromium 실행 실패** → `python3 -m playwright install chromium --force`, `pkill -f Chromium` 후 재시도.
- **Fail 과다** → 룰 오탐 가능. 실제 응답 샘플로 `evaluator.py` 보강.

자세한 운영 가이드는 `scripts/README.md` 참고.
