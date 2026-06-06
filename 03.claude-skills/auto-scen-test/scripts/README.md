# auto-scen-test 운영 가이드

시나리오 엑셀 → 챗봇 UI 자동 구동 → 응답 캡처/스크린샷/판정 → 결과 XLSX 기록.

## 파일 구성

| 파일 | 역할 |
|---|---|
| `config.py` | URL/경로/셀렉터/대기시간/컬럼별칭/판정모드. CLI 인자로 런타임 덮어쓰기 |
| `column_mapper.py` | 헤더 자동 매핑 (별칭 사전 → 표준 4필드 id/scenario/query/checkpoint) |
| `scenario_loader.py` | 시나리오 .xlsx/.csv 로더 (헤더행 자동 탐지 + 컬럼 자동 매핑) |
| `run_tests.py` | 메인 러너 (Playwright) |
| `evaluator.py` | 검증 포인트 키워드 → Pass/Fail 룰 |
| `writer.py` | 결과 XLSX 입력 + 스크린샷 임베드 + 요약 시트 집계 |
| `build_result_xlsx.py` | 결과 파일이 없을 때 시나리오로부터 생성 |
| `setup.sh` | 패키지/Chromium 1회 설치 |

## 설치

```bash
bash setup.sh
```

## 실행

```bash
# 결과 파일이 없으면 먼저 생성
python3 build_result_xlsx.py --scenario-file S.xlsx --result-file R.xlsx

# 스모크 (3건)
python3 run_tests.py --scenario-file S.xlsx --result-file R.xlsx \
  --shots-dir shots --url http://host/chat --limit 3

# 전체
python3 run_tests.py --scenario-file S.xlsx --result-file R.xlsx \
  --shots-dir shots --url http://host/chat
```

## 주요 옵션

| 옵션 | 설명 |
|---|---|
| `--only TC-S01-01` | 특정 케이스만 |
| `--scenario S01` | 특정 시나리오ID만 |
| `--limit N` | 처음 N건만 |
| `--headless` | 브라우저 창 없이 (CI) |
| `--wait N` | 응답 캡처 전 고정 대기(초), 기본 20 |
| `--discover` | 셀렉터 자동 탐색 (page_snapshot.html 생성) |

## 헤더 자동 매핑

`column_mapper.py`가 헤더를 별칭으로 인식해 표준 4필드로 매핑한다(id·query 필수, scenario·checkpoint 선택). 컬럼 순서·헤더 행 위치 무관. 인식 결과 확인:

```bash
python3 run_tests.py --map-check --scenario-file S.xlsx
```

별칭으로 못 잡는 특이 컬럼명은 `config.py`의 `COLUMN_ALIASES_EXTRA`로 보강:

```python
COLUMN_ALIASES_EXTRA = {"query": ["사용자 발화"], "id": ["케이스No"]}
```

## 판정 룰 보강

`evaluator.py`의 `RULES` 딕셔너리. `검증 포인트` 문자열에 키워드가 포함되면 해당 룰 적용,
매칭 룰의 80% 이상 통과 시 Pass. 매칭 룰이 없으면 응답 길이(≥100자)로 fallback.
키워드 매칭 기반이라 오탐 가능 — Fail은 응답 요약으로 실제 결함 여부 확인.

## 셀렉터 보강

UI가 처음이면 `--discover`로 입력창/버튼을 출력하고 `config.py`의
`SELECTORS["input"]`, `["submit"]` 맨 앞에 정확한 셀렉터를 추가.
