---
name: auto-scen-test
description: 단위테스트 시나리오 엑셀(.xlsx/.csv)을 기반으로 웹 UI를 Playwright로 자동 구동하여, 케이스별 실행 → 응답/화면 캡처 → 스크린샷 → 자동 판정(Pass/Fail/N-A/Block)까지 수행하고 결과를 결과 XLSX에 자동 기록한다. "자동 테스트", "시나리오 테스트 돌려줘", "단위테스트 자동화", "auto-scen-test" 요청 시 사용. 챗봇형(질의 1건=케이스 1건)과 일반 웹 UI형(로그인·화면이동·폼입력 멀티스텝) 시나리오를 모두 지원하며 모드를 자동 판별한다. 임의의 URL과 시나리오 엑셀에 범용 적용된다(헤더 자동 매핑 + 셀렉터 폴백 + 수행절차 DSL).
---

# auto-scen-test — 시나리오 기반 자동 테스트

테스트 시나리오 엑셀의 각 케이스를 읽어 웹 UI를 자동 구동하고, 결과를 캡처·판정해 결과 XLSX에 기록하는 스킬이다.

## 두 가지 모드 (자동 판별)

| 모드 | 대상 | 케이스 1건이 뜻하는 것 | 필요한 컬럼 |
|---|---|---|---|
| `chat` | 챗봇·검색창 등 단일 입력 UI | 질의 1건 입력 → 응답 판정 | `질의` |
| `ui` | 일반 웹 화면 | 수행절차 여러 스텝 실행 → 화면 판정 | `수행절차` 또는 `대상 URL` |

시나리오에 `수행절차`/`대상 URL` 값이 하나라도 있으면 `ui`, 아니면 `chat`으로 **자동 판별**한다. `--mode chat|ui` 로 강제할 수 있다. 기존 챗봇 시나리오 파일은 수정 없이 그대로 동작한다.

## 처리 흐름

```
시나리오 파일(.xlsx/.csv) 로드 → 헤더 자동 매핑 → 모드 판별
        │
        ├─ (인증 필요 시) 로그인 절차 1회 실행 → 세션 저장/재사용
        │
        ▼  케이스별 반복
  ┌─ [ui] 대상 URL 이동 → 사전조건 실행 → 수행절차 DSL 실행
  ├─ [chat] 입력창 fill → 전송(Enter 실패 시 버튼 폴백)
  ├─ 응답 대기: 로딩 인디케이터 소멸 + 텍스트 무변화까지 폴링
  ├─ 스크린샷 → shots_dir/TC-xxx.png
  ├─ 판정 대상 영역(응답 컨테이너)만 추출 → text/html
  └─ 기대값 리터럴 대조 + 검증포인트 키워드 룰 → Pass/Fail/N/A
        │
        ▼
  결과 XLSX 갱신 (테스트결과/실행일시/응답요약/증적이미지 임베드/비고)
  + "결과 요약" 시트 자동 집계
```

## 판정 결과 4종

| 판정 | 의미 |
|---|---|
| `Pass` | 기대값이 실제로 검출됨 (또는 매칭 룰 80% 이상 통과) |
| `Fail` | 기대값 미검출 / 룰 미충족 — **실제 결함 후보** |
| `N/A` | 자동 판정 근거가 없음 → 스크린샷으로 **수동 확인 필요** |
| `Block` | 실행 자체가 불가 (입력창 미탐지, 절차 실패, 페이지 이동 실패) |

**"응답이 기니까 Pass" 같은 무근거 통과는 만들지 않는다.** 판정 근거가 없으면 Pass가 아니라 N/A다. N/A가 많으면 시나리오의 `기대 결과`에 따옴표로 기대값을 명시하면 자동 판정으로 바뀐다.

## 입력 / 출력

- **입력**: 시나리오 파일(.xlsx/.csv). 컬럼명은 **자동 인식**된다. 헤더 행 위치(앞에 안내문/병합셀이 있어도)와 컬럼 순서는 무관하다.
- **출력**:
  - 결과 XLSX (`단위테스트결과` 시트 + `결과 요약` 시트)
  - 스크린샷 PNG (케이스 ID당 1장, 셀에 임베드)

### 인식하는 컬럼

| 표준 필드 | 필수 | 인식하는 헤더 예시 |
|---|---|---|
| `id` | ✅ | 테스트ID, TC ID, 케이스번호, Test Case ID, No, 순번 |
| `query` | △ | 입력(사용자 질의), 질의, 질문, 프롬프트, Query, 사용자 발화 |
| `steps` | △ | 수행절차, 테스트절차, 실행절차, 수행단계, Steps, Procedure |
| `scenario` | | 시나리오ID, 시나리오, 그룹, 대분류, Scenario, Category |
| `checkpoint` | | 검증 포인트, 검증기준, 검증항목, 합격기준, Acceptance |
| `expected` | | 기대 결과, 기대값, 예상결과, Expected |
| `url` | | 대상 URL, 화면 URL, 화면주소, Endpoint |
| `precondition` | | 사전조건, 전제조건, 선행조건, Precondition, Given |

△ = `query` 와 `steps` 중 **최소 하나**는 있어야 한다.

## 사용 절차

작업 디렉터리는 스킬 폴더의 `scripts/`.

### 1단계 — 설치 (최초 1회)

```bash
cd ~/.claude/skills/auto-scen-test/scripts
bash setup.sh
```

### 2단계 — 헤더 매핑 확인 (새 시나리오 파일일 때)

브라우저 없이 컬럼 인식 결과와 판별된 모드만 빠르게 검증한다.

```bash
python3 run_tests.py --map-check --scenario-file "<시나리오 파일>"
```

매핑이 틀리면 `config.py` 의 `COLUMN_ALIASES_EXTRA` 에 별칭을 추가한다:

```python
COLUMN_ALIASES_EXTRA = {"query": ["사용자 발화"], "id": ["케이스No"]}
```

### 3단계 — 셀렉터 자동 탐색 (새 URL일 때만)

```bash
python3 run_tests.py --discover --url "<URL>"
```

입력창/버튼 목록과 **판정영역 후보**가 출력되고 `page_snapshot.html` 이 저장된다. 출력을 보고 `config.py` 의 `SELECTORS["input"]`, `["submit"]`, `["response_container"]` 맨 앞에 정확한 셀렉터를 추가한다.

> ⚠️ **`response_container` 보강이 판정 정확도의 핵심이다.** 이 영역을 특정하지 못하면 페이지 전체(body)로 폴백하는데, 그러면 네비게이션의 링크·로고 이미지·레이아웃 표를 응답으로 오인한다. 이 경우 화면요소 룰(차트/표/이미지/링크)은 자동으로 판정 보류(N/A) 처리되고 비고에 경고가 남는다.

### 4단계 — 로그인이 필요한 경우

로그인 절차를 수행절차 DSL 파일로 작성한다. 비밀번호는 파일에 쓰지 말고 `${환경변수}` 로 주입한다.

```bash
cat > login.txt <<'EOF'
goto /login
fill #userId    ${AUTOTEST_USER}
fill #password  ${AUTOTEST_PASS}
click 로그인
wait 대시보드
EOF

export AUTOTEST_USER=test01 AUTOTEST_PASS='...'
python3 run_tests.py --save-auth --login-file login.txt --url "<URL>"
```

세션이 `scripts/.auth/state.json` 에 저장되어 이후 실행에서 자동 재사용된다(`--relogin` 으로 갱신). 이후 실행 시엔 `--login-file` 만 계속 넘기면 세션 만료 시 자동 재로그인한다.

### 5단계 — 소수 케이스로 스모크 테스트

전체를 돌리기 전에 항상 소수로 검증한다.

```bash
python3 run_tests.py \
  --scenario-file "<시나리오.xlsx 절대경로>" \
  --result-file   "<결과.xlsx 절대경로>" \
  --shots-dir     "<스크린샷 폴더 절대경로>" \
  --url           "<URL>" \
  --limit 3
```

### 6단계 — 전체 실행 후 보고

```bash
python3 run_tests.py --scenario-file "<...>" --result-file "<...>" \
  --shots-dir "<...>" --url "<...>"
```

콘솔에 `Pass: n | Fail: n | N/A: n | Block: n | Total: n` 요약이 출력된다. 사용자에게:
- Pass/Fail/N/A/Block 합계와 비율
- **Fail** 케이스 ID와 사유 (실제 결함 후보)
- **Block** 케이스 ID와 사유 (셀렉터/절차 문제 — 시나리오나 설정을 고쳐야 함)
- **N/A** 케이스 ID (수동 확인 필요)
- 결과 XLSX 및 스크린샷 폴더 경로

를 간결히 보고한다. Fail/Block이 많으면 룰 오탐·셀렉터 문제 가능성을 함께 안내한다.

## 수행절차 DSL

`수행절차`/`사전조건` 셀에 **한 줄에 한 동작씩** 적는다. 대상과 값은 **2칸 이상 공백 또는 탭**으로 구분한다. `#` 로 시작하는 줄은 주석, `1.` `-` 같은 번호/불릿 접두는 자동 제거된다.

```
goto /login
fill #userId    test01
fill 검색어      냉장고
click 검색
wait 결과
```

| 동사 | 문법 | 설명 |
|---|---|---|
| `goto` | `goto /path` 또는 `goto http://...` | 페이지 이동 (상대경로는 `--url` 의 origin 기준) |
| `fill` | `fill <대상>  <값>` | 입력창 채우기 (기존 값 삭제) |
| `type` | `type <대상>  <값>` | 한 글자씩 입력 (자동완성 등 키 이벤트 필요 시) |
| `click` | `click <대상>` | 클릭 |
| `select` | `select <대상>  <값>` | 드롭다운 선택 (label 우선, 실패 시 value) |
| `check` / `uncheck` | `check <대상>` | 체크박스 |
| `press` | `press Enter` / `press <대상>  <키>` | 키 입력 |
| `upload` | `upload <대상>  <파일경로>` | 파일 업로드 |
| `hover` | `hover <대상>` | 호버 |
| `wait` | `wait 2s` / `wait <대상>` | 고정 대기 / 요소가 보일 때까지 대기 |
| `waitgone` | `waitgone <대상>` | 요소가 사라질 때까지 대기 |

**대상 표기**: `#id` `.class` `[attr=v]` `//xpath` 는 셀렉터로, 그 외 문자열은 라벨/placeholder/버튼이름/화면텍스트로 자동 탐색한다. 탐색 순서는 동사에 맞춰 달라져서(`click` 은 버튼 우선, `fill` 은 라벨 우선), `<label>검색어</label>` 와 `<button>검색</button>` 가 함께 있어도 올바른 쪽을 잡는다.

**비밀번호 등 비밀값**은 `${ENV_VAR}` 로 쓰고 환경변수로 주입한다. 미설정이면 빈 값으로 조용히 진행하지 않고 에러를 낸다.

## 주요 옵션

| 옵션 | 설명 |
|---|---|
| `--only TC-S01-01` | 특정 케이스만 |
| `--scenario S01` | 특정 시나리오ID만 |
| `--limit N` | 처음 N건만 |
| `--headless` | 브라우저 창 없이 실행 (CI/백그라운드) |
| `--wait N` | 응답 **최대** 대기(초). 기본 30 |
| `--fixed-wait N` | 조건 대기 대신 고정 대기(초) — 구버전 동작 |
| `--mode chat\|ui` | 모드 강제 (기본: 자동 판별) |
| `--isolate` / `--no-isolate` | 케이스마다 새 컨텍스트 / 단일 세션 유지 |
| `--login-file F` | 로그인 절차 DSL 파일 |
| `--save-auth` | 로그인만 수행하고 세션 저장 후 종료 |
| `--relogin` | 저장된 세션 무시하고 재로그인 |
| `--viewport-shot` | 전체 페이지 대신 보이는 화면만 캡처 |
| `--discover` | 셀렉터 자동 탐색 |
| `--map-check` | 헤더 매핑만 확인 (브라우저 미실행) |

## 케이스 격리

- `ui` 모드 기본 **ON** — 케이스마다 새 브라우저 컨텍스트를 만들어 앞 케이스의 상태(입력값·모달·스크롤)가 다음 케이스를 오염시키지 않는다. 로그인 세션은 유지된다.
- `chat` 모드 기본 **OFF** — 대화 맥락이 유지돼야 멀티턴 케이스가 성립하므로 단일 세션.
- `--isolate` / `--no-isolate` 로 강제할 수 있다.

## 필수 입력 확인 (인자 생략 시)

`--url` 과 `--scenario-file` 은 대상마다 달라지므로 **반드시 사용자에게 확인한다**. `config.py` 기본값은 동작하지 않는 플레이스홀더(`your-chatbot-host.example.com`)이며, URL 미지정 시 러너가 실행을 거부한다. 파일·폴더 경로는 항상 절대경로로 명시한다.

## 결과 파일이 없을 때

```bash
python3 build_result_xlsx.py --scenario-file "<시나리오>" --result-file "<생성할 결과.xlsx>"
```

## 자동 판정 규칙 (evaluator.py)

판정은 **판정 대상 영역**(페이지 전체가 아님)의 text/html 을 기준으로 두 축으로 이뤄진다.

**1) 리터럴 대조** — `기대 결과`(없으면 `검증 포인트`)에서 검증 가능한 값을 뽑아 실제 검출 여부를 확인한다. 하나라도 없으면 Fail.
- 따옴표로 감싼 문자열: `잔액이 "12,000원" 으로 표시된다` → `12,000원` 검사
- 따옴표가 없으면 3자리 이상 숫자·금액·퍼센트, 대문자 코드 토큰을 자동 추출
- 숫자는 경계를 검사하므로 기대값 `0건` 이 실제값 `1,250건` 에 오매칭되지 않는다
- `12,000원` 과 `12000원` 처럼 자릿수 콤마만 다른 경우는 통과

**2) 키워드 룰** — `검증 포인트` 문자열에 `RULES` 키워드가 포함되면 해당 룰 적용. 매칭 룰의 80% 이상 통과 시 Pass.

두 축 모두 근거가 없으면 **N/A**. 룰은 키워드 매칭 기반이라 표현이 다르면 오탐이 날 수 있으므로:
- Fail 케이스는 응답 요약을 직접 보고 실제 결함인지 룰 오탐인지 구분한다.
- 반복 오탐 키워드는 `evaluator.py` 의 `RULES` 에 항목을 추가/수정한다.
- 의미 검증이 필요하면 LLM-as-Judge 보강을 권고한다(선택).

## 로컬 / 클라우드 실행

`--headless` 로 화면 없는 서버에서도 그대로 동작한다. 클라우드(CI)로 옮길 때 실제 걸림돌은 브라우저가 아니라 다음 4가지다.

| 이슈 | 대응 |
|---|---|
| **대상 URL 도달성** | 사내망/`localhost` 대상은 공용 러너에서 접속 불가 → self-hosted runner 사용 |
| **한글 폰트** | 리눅스 컨테이너에 CJK 폰트가 없으면 증적 스크린샷이 `□□□` 로 깨진다 → `fonts-noto-cjk` 설치 필수 |
| **산출물 회수** | 결과 XLSX·PNG 를 artifact 로 업로드해야 확인 가능 |
| **인증정보** | `${ENV_VAR}` 를 CI Secrets 로 주입 |

브라우저·의존성이 미리 설치된 `mcr.microsoft.com/playwright/python` 이미지를 쓰면 설치 단계를 생략할 수 있다. 셀렉터·판정룰을 조정하는 초기 단계에는 로컬 실행이 적합하다.

## 트러블슈팅

- **입력창 미탐지(Block)** → `--discover` 로 셀렉터 재탐색 후 `config.py` 보강.
- **전송 실패(Block)** → Enter 가 줄바꿈으로 소비되는 UI. 러너가 전송 버튼으로 자동 폴백하지만, 버튼 셀렉터가 없으면 `SELECTORS["submit"]` 보강 필요.
- **N/A 과다** → 시나리오의 `기대 결과`에 따옴표로 기대값을 명시하거나, `검증 포인트`에 룰 키워드를 넣는다.
- **"판정영역 특정 실패" 경고** → `SELECTORS["response_container"]`(chat) / `["result_container"]`(ui) 보강. 이걸 방치하면 화면요소 룰이 계속 보류된다.
- **응답이 짧게 잘림** → `--wait` 값을 키운다(예 45). 조건 대기라 실제로는 응답 완료 즉시 진행한다.
- **수행절차 실패(Block)** → 오류 메시지에 몇 번째 줄에서 실패했는지 표시된다. 대상 문자열을 `#id` 셀렉터로 바꾸면 확실하다.
- **Chromium 실행 실패** → `python3 -m playwright install chromium --force`, `pkill -f Chromium` 후 재시도.

자세한 운영 가이드는 `scripts/README.md` 참고.
