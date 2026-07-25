"""수행절차 DSL 파서 / 실행기.

시나리오 엑셀의 `수행절차`(또는 `사전조건`) 셀에 한 줄에 한 동작씩 적는다.
대상과 값은 **2칸 이상 공백 또는 탭**으로 구분한다.

    goto /login
    fill #userId    test01
    fill #password  ${AUTOTEST_PASS}
    click 로그인
    wait 대시보드
    fill 검색       냉장고
    press Enter

지원 동사
    goto <url|/path>            페이지 이동 (상대경로는 BASE_URL 기준)
    fill <대상>  <값>            입력창 채우기 (기존 값 지움)
    type <대상>  <값>            한 글자씩 입력 (자동완성 등 키 이벤트가 필요할 때)
    click <대상>                클릭
    select <대상>  <값>          <select> 옵션 선택 (label 우선, 실패 시 value)
    check <대상> / uncheck <대상>  체크박스
    press <키> | press <대상>  <키>  키 입력 (Enter, Escape, Control+A ...)
    upload <대상>  <파일경로>     파일 업로드
    hover <대상>                호버
    wait <초>s                  고정 대기 (예: wait 2s)
    wait <대상>                 해당 요소가 보일 때까지 대기
    waitgone <대상>             해당 요소가 사라질 때까지 대기

대상(<대상>) 표기
    - `#id`, `.class`, `[attr=v]`, `//xpath`, `css=`, `xpath=` → 셀렉터로 해석
    - 그 외 문자열 → 라벨 / placeholder / 버튼이름 / 링크 / 화면텍스트 자동 탐색.
      탐색 순서는 동사에 맞춰 달라진다(click 은 버튼 우선, fill 은 라벨 우선) —
      `<label>검색어</label>` 와 `<button>검색</button>` 가 함께 있어도 올바른 쪽을 잡는다.

값 안의 `${ENV_VAR}` 는 실행 시점 환경변수로 치환된다(비밀번호를 파일에 남기지 않기 위함).
"""
import os
import re
import time

VERBS = {
    "goto", "fill", "type", "click", "select", "check", "uncheck",
    "press", "upload", "hover", "wait", "waitgone",
}

_SELECTOR_PREFIX = ("#", ".", "[", "//", "(", "css=", "xpath=", "text=", "role=")
_STEP_TIMEOUT_MS = 10_000


class ActionError(Exception):
    """수행절차 실행 실패. 케이스는 Block 처리된다."""


# ── 파싱 ────────────────────────────────────────────────────

def parse(text) -> list:
    """DSL 문자열 → [(verb, [args...]), ...]. 빈 줄/주석은 무시."""
    steps = []
    for raw in str(text or "").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue
        # "1. click 로그인", "- click 로그인" 같은 번호/불릿 접두 제거
        line = re.sub(r"^\s*(?:\d+[.)]|[-*•])\s+", "", line)
        m = re.match(r"^([A-Za-z]+)\b\s*(.*)$", line)
        if not m:
            raise ActionError(f"해석 불가한 절차 줄: {raw.strip()!r}")
        verb = m.group(1).lower()
        rest = m.group(2).strip()
        if verb not in VERBS:
            raise ActionError(
                f"알 수 없는 동사 {verb!r} (줄: {raw.strip()!r})\n"
                f"  지원 동사: {', '.join(sorted(VERBS))}"
            )
        steps.append((verb, _split_args(rest, verb)))
    return steps


def _split_args(rest: str, verb: str) -> list:
    """'대상  값' → ['대상', '값']. 2칸 이상 공백 또는 탭이 구분자."""
    if not rest:
        return []
    parts = [p.strip() for p in re.split(r"\s{2,}|\t", rest) if p.strip()]
    # 값이 필요한 동사인데 한 덩어리로 들어온 경우: 셀렉터처럼 보이면 첫 공백에서 분리
    if len(parts) == 1 and verb in ("fill", "type", "select", "upload"):
        one = parts[0]
        if " " in one and one.startswith(_SELECTOR_PREFIX):
            head, tail = one.split(" ", 1)
            return [head.strip(), tail.strip()]
    return parts


def expand_env(value: str) -> str:
    """${VAR} → 환경변수. 미설정이면 에러(빈 비밀번호로 조용히 실패하는 것 방지)."""
    def sub(m):
        name = m.group(1)
        if name not in os.environ:
            raise ActionError(f"환경변수 ${{{name}}} 가 설정되지 않았습니다. export {name}=... 후 재실행")
        return os.environ[name]
    return re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", sub, str(value))


def has_steps(text) -> bool:
    return bool(str(text or "").strip())


# ── 대상 해석 ────────────────────────────────────────────────

def locate(page, target: str, prefer: str = "field"):
    """대상 문자열 → Playwright Locator.

    prefer 는 탐색 순서를 정한다. 같은 낱말이 라벨과 버튼에 동시에 존재할 때
    (`<label>검색어</label>` 와 `<button>검색</button>`) 동사에 맞는 쪽을 먼저 찾는다.
      "field"  = 입력 대상 (fill/type/select/check/upload)
      "click"  = 클릭 대상 (click/hover)
      "any"    = 존재 확인 (wait)
    """
    t = (target or "").strip()
    if not t:
        raise ActionError("대상이 비어 있습니다")
    if t.startswith(_SELECTOR_PREFIX) or re.match(r"^[a-z][a-z0-9]*\[", t) or ">>" in t:
        return page.locator(t)

    by_label = lambda: page.get_by_label(t, exact=False)
    by_ph = lambda: page.get_by_placeholder(t, exact=False)
    by_btn = lambda: page.get_by_role("button", name=t)
    by_link = lambda: page.get_by_role("link", name=t)
    by_text = lambda: page.get_by_text(t, exact=False)

    if prefer == "click":
        candidates = (by_btn, by_link, by_label, by_ph, by_text)
    elif prefer == "any":
        candidates = (by_text, by_label, by_ph, by_btn, by_link)
    else:
        candidates = (by_label, by_ph, by_btn, by_link, by_text)

    for get in candidates:
        try:
            loc = get()
            if loc.count() > 0:
                return loc.first
        except Exception:
            continue
    # 최후: CSS 로 시도 (태그명 등)
    return page.locator(t)


def _need(args, n, verb):
    if len(args) < n:
        raise ActionError(f"{verb}: 인자 {n}개 필요 (받은 값: {args}). 대상과 값은 2칸 이상 공백으로 구분")


# ── 실행 ────────────────────────────────────────────────────

def run(page, dsl_text, log=None, base_resolve=None) -> int:
    """DSL 실행. 성공한 스텝 수 반환. 실패 시 ActionError."""
    steps = parse(dsl_text)
    for i, (verb, args) in enumerate(steps, 1):
        try:
            _exec_one(page, verb, args, base_resolve)
        except ActionError:
            raise
        except Exception as e:
            raise ActionError(f"[{i}번째 절차 실패] {verb} {' '.join(args)} → {type(e).__name__}: {e}")
        if log:
            log(f"    · {verb} {' '.join(args)[:60]}")
    return len(steps)


def _exec_one(page, verb, args, base_resolve):
    if verb == "goto":
        _need(args, 1, verb)
        url = base_resolve(args[0]) if base_resolve else args[0]
        page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        return

    if verb in ("fill", "type"):
        _need(args, 2, verb)
        loc = locate(page, args[0], "field")
        val = expand_env(args[1])
        loc.wait_for(state="visible", timeout=_STEP_TIMEOUT_MS)
        if verb == "fill":
            loc.fill(val)
        else:
            loc.click()
            loc.type(val, delay=40)
        return

    if verb == "click":
        _need(args, 1, verb)
        loc = locate(page, args[0], "click")
        loc.wait_for(state="visible", timeout=_STEP_TIMEOUT_MS)
        loc.click(timeout=_STEP_TIMEOUT_MS)
        return

    if verb == "hover":
        _need(args, 1, verb)
        locate(page, args[0], "click").hover(timeout=_STEP_TIMEOUT_MS)
        return

    if verb == "select":
        _need(args, 2, verb)
        loc = locate(page, args[0], "field")
        val = expand_env(args[1])
        try:
            loc.select_option(label=val, timeout=_STEP_TIMEOUT_MS)
        except Exception:
            loc.select_option(value=val, timeout=_STEP_TIMEOUT_MS)
        return

    if verb in ("check", "uncheck"):
        _need(args, 1, verb)
        loc = locate(page, args[0], "field")
        (loc.check if verb == "check" else loc.uncheck)(timeout=_STEP_TIMEOUT_MS)
        return

    if verb == "press":
        if len(args) >= 2:
            locate(page, args[0], "field").press(args[1], timeout=_STEP_TIMEOUT_MS)
        else:
            _need(args, 1, verb)
            page.keyboard.press(args[0])
        return

    if verb == "upload":
        _need(args, 2, verb)
        locate(page, args[0], "field").set_input_files(expand_env(args[1]), timeout=_STEP_TIMEOUT_MS)
        return

    if verb == "wait":
        _need(args, 1, verb)
        m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(?:s|초)?", args[0])
        if m:
            time.sleep(float(m.group(1)))
            return
        locate(page, args[0], "any").wait_for(state="visible", timeout=_STEP_TIMEOUT_MS)
        return

    if verb == "waitgone":
        _need(args, 1, verb)
        locate(page, args[0], "any").wait_for(state="hidden", timeout=_STEP_TIMEOUT_MS)
        return

    raise ActionError(f"미구현 동사: {verb}")
