"""시나리오 기반 자동 테스트 설정.

대상 챗봇 URL과 시나리오/결과 파일 경로는 run_tests.py 의 CLI 인자
(--scenario-file / --result-file / --shots-dir / --url / --wait) 로
런타임에 덮어쓴다. (apply_overrides 참조)
아래 값들은 예시 플레이스홀더이므로 실제 사용 시 인자로 지정한다.
"""
from pathlib import Path

# ── 대상 환경 (기본값/예시) ─────────────────────────────────
# 실제 챗봇 주소는 --url 로 지정한다. (예시 플레이스홀더)
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
WAIT_AFTER_SEND_S = 20            # 질의 전송 후 캡처까지 고정 대기(초)
WAIT_BETWEEN_CASES_S = 2          # 캡처 후 다음 질의 전 간격
VIEWPORT = {"width": 1440, "height": 900}

# ── 시나리오 컬럼명 ─────────────────────────────────────────
# 기본값. 실제 파일 로드 시 column_mapper 가 헤더를 자동 인식해
# 아래 값들을 실제 헤더명으로 덮어쓴다(set_columns). 별칭으로도
# 못 잡는 특이 컬럼명은 COLUMN_ALIASES_EXTRA 로 보강.
COL_ID = "테스트ID"
COL_SCENARIO = "시나리오ID"
COL_QUERY = "입력(사용자 질의)"
COL_CHECKPOINT = "검증 포인트"

# 프로젝트별 헤더 별칭 추가. 예: {"query": ["사용자 발화"], "id": ["케이스No"]}
COLUMN_ALIASES_EXTRA = {}


def set_columns(mapping):
    """column_mapper.resolve() 결과로 실제 헤더명을 반영."""
    global COL_ID, COL_SCENARIO, COL_QUERY, COL_CHECKPOINT
    if mapping.get("id"):
        COL_ID = mapping["id"]
    if mapping.get("scenario"):
        COL_SCENARIO = mapping["scenario"]
    if mapping.get("query"):
        COL_QUERY = mapping["query"]
    if mapping.get("checkpoint"):
        COL_CHECKPOINT = mapping["checkpoint"]

# ── 셀렉터 (DevTools 확인 후 정정 가능) ─────────────────────
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
    "response_container": [
        '[data-role="assistant"]',
        '[data-message-role="assistant"]',
        '.message.assistant',
        '.assistant-message',
        '.bot-message',
        '[class*="assistant"]',
        '[class*="message"]',
        'main article',
    ],
    "loading": [
        '.loading',
        '[aria-busy="true"]',
        '.typing-indicator',
        '[data-loading="true"]',
    ],
}

# ── 케이스 별 처리 모드 (UI-only 검증 등) ───────────────────
# 대상 시나리오의 케이스 ID → UI 검증 모드. 비워두면 모두 일반 텍스트 판정.
# 예: {"TC-001": "ui_chart", "TC-002": "ui_table_2", "TC-003": "ui_color"}
CASE_MODE = {}

# 응답 텍스트 추출 시 잘라낼 푸터/네비 문구. 대상 챗봇 UI에 맞게 채운다.
# 예: ["추천 질문 새로고침", "이용약관"]
CUT_MARKERS = []


def apply_overrides(args):
    """CLI 인자로 기본 경로/URL/대기시간을 덮어쓴다."""
    global SCENARIO_PATH, XLSX_PATH, SHOTS_DIR, CHAT_URL, WAIT_AFTER_SEND_S, HEADLESS
    if getattr(args, "scenario_file", None):
        SCENARIO_PATH = Path(args.scenario_file).expanduser().resolve()
    if getattr(args, "result_file", None):
        XLSX_PATH = Path(args.result_file).expanduser().resolve()
    if getattr(args, "shots_dir", None):
        SHOTS_DIR = Path(args.shots_dir).expanduser().resolve()
    if getattr(args, "url", None):
        CHAT_URL = args.url
    if getattr(args, "wait", None):
        WAIT_AFTER_SEND_S = int(args.wait)
    if getattr(args, "headless", False):
        HEADLESS = True
