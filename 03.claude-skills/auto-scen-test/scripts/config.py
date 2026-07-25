"""시나리오 기반 자동 테스트 설정.

대상 URL과 시나리오/결과 파일 경로는 run_tests.py 의 CLI 인자
(--scenario-file / --result-file / --shots-dir / --url / --wait) 로
런타임에 덮어쓴다. (apply_overrides 참조)
아래 값들은 예시 플레이스홀더이므로 실제 사용 시 인자로 지정한다.
"""
from pathlib import Path

# ── 대상 환경 (기본값/예시) ─────────────────────────────────
# 실제 주소는 --url 로 지정한다. (예시 플레이스홀더)
BASE_URL = "http://your-chatbot-host.example.com"
CHAT_URL = f"{BASE_URL}/chat"

# ── 경로 (기본값/예시) ──────────────────────────────────────
# 시나리오/결과 파일과 스크린샷 폴더는 보통 CLI 인자로 덮어쓴다.
_DEFAULT_ROOT = Path("~/auto-scen-test").expanduser()
SCENARIO_PATH = _DEFAULT_ROOT / "단위테스트_시나리오.xlsx"
XLSX_PATH = _DEFAULT_ROOT / "단위테스트_결과.xlsx"
SHOTS_DIR = _DEFAULT_ROOT / "screenshots_auto"
LOG_PATH = Path(__file__).resolve().parent / "run.log"

# ── Playwright 설정 ─────────────────────────────────────────
HEADLESS = False
VIEWPORT = {"width": 1440, "height": 900}
SCREENSHOT_FULL_PAGE = True       # 대화가 길게 누적되면 False 권장(--viewport-shot)
WAIT_BETWEEN_CASES_S = 2          # 캡처 후 다음 케이스 전 간격

# ── 응답 대기 (조건 대기) ───────────────────────────────────
# 고정 sleep 이 아니라 "로딩 인디케이터 소멸 + 텍스트 무변화" 를 폴링한다.
WAIT_MAX_S = 30.0                 # 최대 대기(초). --wait 로 덮어씀
WAIT_MIN_S = 0.5                  # 최소 대기(초)
STABLE_QUIET_S = 1.5              # 이 시간 동안 텍스트 변화 없으면 완료로 간주
POLL_INTERVAL_S = 0.4             # 폴링 주기(초)
FIXED_WAIT_S = 0.0                # >0 이면 조건대기 대신 고정 대기 (--fixed-wait)
SEND_CONFIRM_S = 2.0              # Enter 전송이 먹혔는지 확인하는 대기(초)

# ── 실행 모드 ───────────────────────────────────────────────
# MODE: None=자동판별, "chat"=질의1건/케이스, "ui"=수행절차 멀티스텝
#   자동판별 = 시나리오에 수행절차/URL 값이 하나라도 있으면 "ui", 아니면 "chat"
MODE = None
# ISOLATE: None=자동(ui→True, chat→False), True=케이스마다 새 컨텍스트, False=단일 세션
ISOLATE = None

# ── 인증 (로그인 프리스텝) ──────────────────────────────────
# 로그인 절차를 수행절차 DSL 로 적어두면 1회 실행 후 세션을 STORAGE_STATE 에 저장하고,
# 이후 실행은 저장된 세션을 재사용한다. 비밀번호는 ${ENV_VAR} 로 주입한다.
#   LOGIN_STEPS = '''
#   goto /login
#   fill #userId    ${AUTOTEST_USER}
#   fill #password  ${AUTOTEST_PASS}
#   click 로그인
#   wait 대시보드
#   '''
STORAGE_STATE = Path(__file__).resolve().parent / ".auth" / "state.json"
LOGIN_STEPS = ""

# ── 시나리오 컬럼명 ─────────────────────────────────────────
# 기본값. 실제 파일 로드 시 column_mapper 가 헤더를 자동 인식해
# 아래 값들을 실제 헤더명으로 덮어쓴다(set_columns). 별칭으로도
# 못 잡는 특이 컬럼명은 COLUMN_ALIASES_EXTRA 로 보강.
# 파일에 없는 컬럼은 None 이 되며, 코드는 `if config.COL_STEPS:` 로 존재를 판단한다.
COL_ID = "테스트ID"
COL_SCENARIO = "시나리오ID"
COL_QUERY = "입력(사용자 질의)"
COL_CHECKPOINT = "검증 포인트"
COL_EXPECTED = "기대 결과"
COL_URL = "대상 URL"
COL_STEPS = "수행절차"
COL_PRECONDITION = "사전조건"

# 프로젝트별 헤더 별칭 추가. 예: {"query": ["사용자 발화"], "id": ["케이스No"]}
COLUMN_ALIASES_EXTRA = {}

_COL_ATTR = {
    "id": "COL_ID",
    "scenario": "COL_SCENARIO",
    "query": "COL_QUERY",
    "checkpoint": "COL_CHECKPOINT",
    "expected": "COL_EXPECTED",
    "url": "COL_URL",
    "steps": "COL_STEPS",
    "precondition": "COL_PRECONDITION",
}


def set_columns(mapping):
    """column_mapper.resolve() 결과로 실제 헤더명을 반영."""
    g = globals()
    for field, attr in _COL_ATTR.items():
        if field in mapping:
            g[attr] = mapping.get(field)


# ── 셀렉터 (--discover 확인 후 정정 가능) ───────────────────
SELECTORS = {
    "input": [
        'input[placeholder*="물어보세요"]',
        'input[placeholder*="메시지"]',
        'input[type="text"]',
        'textarea',
        '[contenteditable="true"]',
        '[role="textbox"]',
    ],
    "submit": [
        'button[aria-label="전송"]',
        'button[aria-label*="전송"]',
        'button[type="submit"]',
        'button:has-text("전송")',
    ],
    # 판정 대상 영역(chat 모드). 여기서 찾은 요소의 텍스트/HTML 만 평가한다.
    # 못 찾으면 body 로 폴백하되 결과 비고에 경고를 남긴다.
    # 주의: 너무 넓은 셀렉터(main, [class*="message"])를 넣으면 네비/로고까지
    #       판정에 들어가 오탐 Pass 가 발생한다. 좁은 것부터 나열할 것.
    "response_container": [
        '[data-role="assistant"]',
        '[data-message-role="assistant"]',
        '.message.assistant',
        '.assistant-message',
        '.bot-message',
        '[class*="assistant"]',
    ],
    # 판정 대상 영역(ui 모드). 화면 본문만 보도록 좁힌다.
    "result_container": [
        'main',
        '[role="main"]',
        '#content',
        '.content',
        '#container',
    ],
    "loading": [
        '.loading',
        '[aria-busy="true"]',
        '.typing-indicator',
        '[data-loading="true"]',
    ],
}

# response_container 가 여러 개 매칭될 때 판정 대상 선택 방식.
# "last"=마지막(챗봇 최신 응답), "first"=첫번째, "all"=전부 합침
RESPONSE_SCOPE_PICK = "last"

# 응답 텍스트 추출 시 잘라낼 푸터/네비 문구. 대상 UI에 맞게 채운다.
# 예: ["추천 질문 새로고침", "이용약관"]
CUT_MARKERS = []

# 응답 텍스트 저장 상한(자). 판정은 자르기 전 전문(全文) 기준으로 수행한다.
RESPONSE_STORE_LIMIT = 4000


def apply_overrides(args):
    """CLI 인자로 기본 경로/URL/대기시간/모드를 덮어쓴다."""
    global SCENARIO_PATH, XLSX_PATH, SHOTS_DIR, CHAT_URL, BASE_URL
    global WAIT_MAX_S, FIXED_WAIT_S, HEADLESS, MODE, ISOLATE
    global STORAGE_STATE, LOGIN_STEPS, SCREENSHOT_FULL_PAGE
    if getattr(args, "scenario_file", None):
        SCENARIO_PATH = Path(args.scenario_file).expanduser().resolve()
    if getattr(args, "result_file", None):
        XLSX_PATH = Path(args.result_file).expanduser().resolve()
    if getattr(args, "shots_dir", None):
        SHOTS_DIR = Path(args.shots_dir).expanduser().resolve()
    if getattr(args, "url", None):
        CHAT_URL = args.url
        BASE_URL = origin_of(args.url)
    if getattr(args, "wait", None):
        WAIT_MAX_S = float(args.wait)
    if getattr(args, "fixed_wait", None):
        FIXED_WAIT_S = float(args.fixed_wait)
    if getattr(args, "headless", False):
        HEADLESS = True
    if getattr(args, "viewport_shot", False):
        SCREENSHOT_FULL_PAGE = False
    if getattr(args, "mode", None):
        MODE = args.mode
    if getattr(args, "isolate", False):
        ISOLATE = True
    if getattr(args, "no_isolate", False):
        ISOLATE = False
    if getattr(args, "storage_state", None):
        STORAGE_STATE = Path(args.storage_state).expanduser().resolve()
    if getattr(args, "login_file", None):
        LOGIN_STEPS = Path(args.login_file).expanduser().resolve().read_text(encoding="utf-8")


def origin_of(url: str) -> str:
    """'http://host/a/b' → 'http://host' (상대 경로 goto 의 기준)."""
    try:
        from urllib.parse import urlsplit
        p = urlsplit(url)
        if p.scheme and p.netloc:
            return f"{p.scheme}://{p.netloc}"
    except Exception:
        pass
    return url


def resolve_url(u: str) -> str:
    """상대 경로면 BASE_URL 기준으로 절대화."""
    u = (u or "").strip()
    if not u:
        return ""
    if u.startswith(("http://", "https://")):
        return u
    if u.startswith("/"):
        return BASE_URL.rstrip("/") + u
    return BASE_URL.rstrip("/") + "/" + u
