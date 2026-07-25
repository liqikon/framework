# auto-scen-test 운영 가이드

시나리오 엑셀 → 웹 UI 자동 구동 → 응답/화면 캡처·스크린샷·판정 → 결과 XLSX 기록.

## 파일 구성

| 파일 | 역할 |
|---|---|
| `config.py` | URL/경로/셀렉터/대기설정/컬럼별칭/인증. CLI 인자로 런타임 덮어쓰기 |
| `column_mapper.py` | 헤더 자동 매핑 (별칭 사전 → 표준 8필드) |
| `scenario_loader.py` | 시나리오 .xlsx/.csv 로더 (헤더행 자동 탐지 + 컬럼 자동 매핑) |
| `actions.py` | 수행절차 DSL 파서/실행기 (goto/fill/click/select/wait ...) |
| `run_tests.py` | 메인 러너 (Playwright) |
| `evaluator.py` | 기대값 리터럴 대조 + 키워드 룰 → Pass/Fail/N/A |
| `writer.py` | 결과 XLSX 입력 + 스크린샷 임베드 + 요약 시트 집계 |
| `build_result_xlsx.py` | 결과 파일이 없을 때 시나리오로부터 생성 |
| `setup.sh` | 패키지/Chromium 1회 설치 |

## 설치

```bash
bash setup.sh
```

## 실행

```bash
# 0) 컬럼 인식 + 모드 판별 확인 (브라우저 미실행)
python3 run_tests.py --map-check --scenario-file S.xlsx

# 1) 결과 파일이 없으면 먼저 생성
python3 build_result_xlsx.py --scenario-file S.xlsx --result-file R.xlsx

# 2) 스모크 (3건)
python3 run_tests.py --scenario-file S.xlsx --result-file R.xlsx \
  --shots-dir shots --url http://host/chat --limit 3

# 3) 전체
python3 run_tests.py --scenario-file S.xlsx --result-file R.xlsx \
  --shots-dir shots --url http://host/chat
```

## 모드 자동 판별

| 모드 | 조건 | 케이스 1건 | 격리 기본값 |
|---|---|---|---|
| `chat` | `질의` 컬럼만 있음 | 질의 입력 → 응답 판정 | OFF (대화 맥락 유지) |
| `ui` | `수행절차`/`대상 URL` 값 존재 | 멀티스텝 DSL 실행 → 화면 판정 | ON (상태 오염 차단) |

`--mode chat|ui`, `--isolate` / `--no-isolate` 로 강제 가능.

## 주요 옵션

| 옵션 | 설명 |
|---|---|
| `--only TC-S01-01` | 특정 케이스만 |
| `--scenario S01` | 특정 시나리오ID만 |
| `--limit N` | 처음 N건만 |
| `--headless` | 브라우저 창 없이 (CI) |
| `--wait N` | 응답 **최대** 대기(초), 기본 30 |
| `--fixed-wait N` | 조건 대기 대신 고정 대기 (구버전 동작) |
| `--viewport-shot` | 전체 페이지 대신 화면만 캡처 |
| `--login-file F` / `--save-auth` / `--relogin` | 로그인 세션 관리 |
| `--storage-state P` | 세션 저장 경로 (기본 `scripts/.auth/state.json`) |
| `--discover` | 셀렉터 자동 탐색 (`page_snapshot.html` 생성) |
| `--map-check` | 헤더 매핑만 확인 |

## 응답 대기 (조건 대기)

고정 sleep 이 아니라 **로딩 인디케이터 소멸 + 판정영역 텍스트 무변화**를 폴링한다.

```
WAIT_MAX_S       최대 대기 (기본 30, --wait)
WAIT_MIN_S       최소 대기 (기본 0.5)
STABLE_QUIET_S   이 시간 동안 변화 없으면 완료 (기본 1.5)
POLL_INTERVAL_S  폴링 주기 (기본 0.4)
```

응답이 잘리면 `--wait` 를 키운다. 조건 대기이므로 값을 키워도 실제 소요는 늘지 않는다(응답 완료 즉시 진행).

## 판정 영역이 정확도를 좌우한다

판정은 **페이지 전체가 아니라 응답 영역**의 text/html 만 본다. 영역을 특정하지 못하면 body 로 폴백하는데, 그러면 네비게이션 링크·로고 이미지·레이아웃 표가 응답으로 오인돼 **오탐 Pass** 가 난다. 이 경우 러너가 화면요소 룰(차트/표/이미지/링크/버튼)을 자동으로 판정 보류(N/A)하고 비고에 경고를 남긴다.

```python
SELECTORS["response_container"]   # chat 모드 판정 영역
SELECTORS["result_container"]     # ui 모드 판정 영역
RESPONSE_SCOPE_PICK = "last"      # 여러 개 매칭 시: last | first | all
```

`--discover` 출력의 `[판정영역 후보]` 섹션을 보고 좁은 셀렉터부터 맨 앞에 추가한다. **`main` 이나 `[class*="message"]` 처럼 넓은 셀렉터를 앞에 두면 안 된다.**

## 판정 룰 보강

`evaluator.py`:
- `RULES` — 검증 포인트 키워드 → 판정 함수. 매칭 룰 80% 이상 통과 시 Pass
- `UI_RULES` — html 구조에 의존하는 룰. 판정영역 폴백 시 자동 제외
- `KEYWORD_REGEX` — 한 글자 키워드의 낱말 경계 처리 (`표` 가 `표시` 에 오매칭되지 않도록)
- `literal_targets()` — 기대 결과에서 따옴표 문자열/숫자/코드 토큰 추출
- `contains_literal()` — 숫자 경계 검사 (`0건` 이 `1,250건` 에 오매칭되지 않도록)

근거가 없으면 Pass 가 아니라 **N/A** 를 반환한다. 무근거 Pass 를 만들지 않는 것이 원칙.

## 수행절차 DSL

한 줄에 한 동작. 대상과 값은 **2칸 이상 공백 또는 탭**으로 구분.

```
goto /login
fill #userId    ${AUTOTEST_USER}
fill #password  ${AUTOTEST_PASS}
click 로그인
wait 대시보드
select 지역     서울
check 약관동의
wait 2s
```

동사: `goto` `fill` `type` `click` `select` `check` `uncheck` `press` `upload` `hover` `wait` `waitgone`

- 대상이 `#id` `.class` `[attr=v]` `//xpath` 면 셀렉터, 아니면 라벨/placeholder/버튼이름/텍스트 자동 탐색
- 탐색 순서는 동사별로 다름 (`click`=버튼 우선, `fill`=라벨 우선)
- `${ENV_VAR}` 는 환경변수로 치환. 미설정이면 에러(빈 비밀번호로 조용히 실패 방지)
- `#` 주석, `1.` `-` 번호/불릿 접두 자동 제거

## 로그인 세션

```bash
export AUTOTEST_USER=test01 AUTOTEST_PASS='...'
python3 run_tests.py --save-auth --login-file login.txt --url http://host
```

`scripts/.auth/state.json` 에 저장되어 이후 자동 재사용(`--relogin` 으로 갱신). 격리 모드에서도 컨텍스트마다 이 세션이 주입되므로 케이스마다 다시 로그인하지 않는다.

> `.auth/state.json` 에는 세션 쿠키가 들어간다. **버전관리에 커밋하지 말 것.**

## 헤더 자동 매핑

컬럼 순서·헤더 행 위치 무관. 인식 결과 확인:

```bash
python3 run_tests.py --map-check --scenario-file S.xlsx
```

별칭으로 못 잡는 특이 컬럼명은 `config.py` 의 `COLUMN_ALIASES_EXTRA` 로 보강:

```python
COLUMN_ALIASES_EXTRA = {"query": ["사용자 발화"], "id": ["케이스No"]}
```

`id` 는 필수, `query`/`steps` 중 최소 하나 필수. 나머지는 선택.

## 셀렉터 보강

UI가 처음이면 `--discover` 로 입력창/버튼/판정영역 후보를 출력하고 `config.py` 의 `SELECTORS` 맨 앞에 정확한 셀렉터를 추가.

## CI / 클라우드 실행

`--headless` 로 그대로 동작한다. 주의할 점:

- **대상 URL 도달성** — 사내망/`localhost` 대상은 공용 러너에서 접속 불가. self-hosted runner 필요
- **한글 폰트** — 리눅스 컨테이너에 `fonts-noto-cjk` 가 없으면 증적 스크린샷의 한글이 깨진다
- **산출물** — 결과 XLSX·스크린샷 폴더를 artifact 로 업로드
- **비밀값** — `${ENV_VAR}` 를 CI Secrets 로 주입
- 브라우저가 포함된 `mcr.microsoft.com/playwright/python` 이미지 권장
