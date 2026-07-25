"""시나리오 기반 자동 테스트 메인 러너.

두 가지 모드를 자동 판별한다.
  chat : `질의` 컬럼만 있는 시나리오 → 입력창에 질의 1건 = 케이스 1건 (기존 방식)
  ui   : `수행절차`/`대상 URL` 컬럼이 있는 시나리오 → 멀티스텝 DSL 실행

사용:
  python run_tests.py --scenario-file S.xlsx --result-file R.xlsx \
                      --shots-dir shots --url http://host/chat
  python run_tests.py --map-check --scenario-file S.xlsx   # 컬럼 인식만 확인
  python run_tests.py --discover --url <url>               # 셀렉터 자동 탐색
  python run_tests.py --save-auth --login-file login.txt --url <url>  # 로그인 세션 저장
  python run_tests.py --only TC-S01-01 / --scenario S01 / --limit 5
  python run_tests.py --headless / --isolate / --wait 45
"""
import argparse
import sys
import time
from datetime import datetime

import actions
import config
from evaluator import evaluate
from scenario_loader import load_cases

# playwright 는 브라우저 실행 시점에만 필요 (--map-check 는 미설치여도 동작)
try:
    from playwright.sync_api import sync_playwright, Page, TimeoutError as PWTimeout
except ImportError:
    sync_playwright = None
    Page = object

    class PWTimeout(Exception):
        pass

PLACEHOLDER_HOST = "your-chatbot-host.example.com"


def log(msg: str):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        with open(config.LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def cell(tc: dict, col) -> str:
    """매핑되지 않은 컬럼(None)도 안전하게 빈 문자열로."""
    if not col:
        return ""
    return str(tc.get(col, "") or "").strip()


# ── 셀렉터 유틸 ─────────────────────────────────────────────

def find_first(page: Page, selectors, timeout=5000):
    """후보 셀렉터 중 먼저 보이는 것을 반환.

    셀렉터마다 full timeout 을 쓰면 N×timeout 을 낭비하므로,
    1차로 짧게 전체를 훑고 없을 때만 2차로 길게 기다린다.
    """
    for probe in (400, timeout):
        for sel in selectors:
            try:
                el = page.wait_for_selector(sel, timeout=probe, state="visible")
                if el:
                    return el, sel
            except PWTimeout:
                continue
            except Exception:
                continue
        if probe >= timeout:
            break
    return None, None


def discover_selectors(page: Page):
    log("=== 셀렉터 자동 탐색 ===")
    page.goto(config.CHAT_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    for label, sel in [("textarea", "textarea"),
                       ("input text", 'input[type="text"], input:not([type])'),
                       ("contenteditable", '[contenteditable="true"], [contenteditable=""]'),
                       ("role=textbox", '[role="textbox"]')]:
        els = page.locator(sel).all()
        log(f"\n[{label}] {len(els)}개")
        for i, t in enumerate(els[:6]):
            try:
                ph = (t.get_attribute("placeholder") or t.get_attribute("aria-label")
                      or t.get_attribute("data-placeholder") or "")
                log(f"  [{i}] visible={t.is_visible()} placeholder='{ph}'")
            except Exception:
                pass

    buttons = page.locator("button").all()
    log(f"\n[button] {len(buttons)}개")
    for i, b in enumerate(buttons):
        try:
            txt = (b.inner_text() or "").strip()[:40]
            aria = b.get_attribute("aria-label") or ""
            log(f"  [{i}] text='{txt}' aria='{aria}' visible={b.is_visible()}")
        except Exception:
            pass

    # 판정 영역 후보도 함께 진단 (오탐 Pass 예방의 핵심)
    log("\n[판정영역 후보]")
    for key in ("response_container", "result_container"):
        for sel in config.SELECTORS[key]:
            try:
                n = page.locator(sel).count()
            except Exception:
                n = -1
            if n:
                log(f"  {key}: '{sel}' → {n}개")

    snippet_path = config.LOG_PATH.parent / "page_snapshot.html"
    snippet_path.write_text(page.content(), encoding="utf-8")
    log(f"\n[페이지 스냅샷 저장] {snippet_path}")
    log("--discover 완료. 위 출력 보고 config.py SELECTORS 정정.")


# ── 판정 영역(scope) 추출 ───────────────────────────────────

def _scope_locator(page: Page, mode: str):
    """판정 대상 영역 locator 반환. (locator, selector, is_multi) / 못 찾으면 (None, None, False)"""
    key = "response_container" if mode == "chat" else "result_container"
    for sel in config.SELECTORS[key]:
        try:
            loc = page.locator(sel)
            n = loc.count()
        except Exception:
            continue
        if not n:
            continue
        if mode == "chat" and config.RESPONSE_SCOPE_PICK == "all":
            return loc, sel, True
        if mode == "chat" and config.RESPONSE_SCOPE_PICK == "last":
            return loc.nth(n - 1), sel, False
        return loc.first, sel, False
    return None, None, False


def read_scope(page: Page, mode: str) -> dict:
    """판정 대상 영역의 text/html 을 읽는다.

    영역을 특정하지 못하면 body/page 전체로 폴백하고 scope_fallback=True 를 세운다.
    (evaluator 가 이 플래그를 보고 화면요소 룰을 자동 제외한다.)
    """
    loc, sel, is_multi = _scope_locator(page, mode)
    if loc is not None:
        try:
            if is_multi:
                els = loc.all()
                text = "\n".join(e.inner_text() for e in els)
                html = "\n".join(e.inner_html() for e in els)
            else:
                text = loc.inner_text()
                html = loc.inner_html()
            return {"text": text, "html": html, "scope_fallback": False, "scope": sel}
        except Exception:
            pass
    try:
        text = page.locator("body").inner_text()
    except Exception:
        text = ""
    try:
        html = page.content()
    except Exception:
        html = ""
    return {"text": text, "html": html, "scope_fallback": True, "scope": None}


def _scope_text(page: Page, mode: str) -> str:
    """폴링용 경량 텍스트 스냅샷."""
    loc, _, is_multi = _scope_locator(page, mode)
    try:
        if loc is None:
            return page.locator("body").inner_text()
        if is_multi:
            return "\n".join(loc.all_inner_texts())
        return loc.inner_text()
    except Exception:
        return ""


def _loading_visible(page: Page) -> bool:
    for sel in config.SELECTORS["loading"]:
        try:
            loc = page.locator(sel)
            if loc.count() and loc.first.is_visible():
                return True
        except Exception:
            continue
    return False


# ── 응답 대기 (고정 sleep → 조건 대기) ──────────────────────

def wait_for_response(page: Page, mode: str) -> float:
    """로딩 인디케이터 소멸 + 텍스트 무변화(STABLE_QUIET_S)를 만족할 때까지 폴링.

    최대 WAIT_MAX_S 까지만 기다린다. FIXED_WAIT_S>0 이면 구버전 고정 대기.
    """
    if config.FIXED_WAIT_S > 0:
        page.wait_for_timeout(int(config.FIXED_WAIT_S * 1000))
        return config.FIXED_WAIT_S

    t0 = time.time()
    time.sleep(config.WAIT_MIN_S)
    last = None
    last_change = time.time()
    while time.time() - t0 < config.WAIT_MAX_S:
        cur = _scope_text(page, mode)
        busy = _loading_visible(page)
        if cur != last:
            last = cur
            last_change = time.time()
        elif not busy and cur.strip() and (time.time() - last_change) >= config.STABLE_QUIET_S:
            break
        time.sleep(config.POLL_INTERVAL_S)
    return time.time() - t0


# ── 질의 전송 (Enter 실패 시 버튼 폴백) ─────────────────────

def _input_value(el) -> str:
    try:
        return el.input_value()
    except Exception:
        try:
            return el.inner_text()
        except Exception:
            return ""


def _confirm_sent(page, el, before_val, before_text, mode) -> bool:
    """전송이 실제로 일어났는지 확인. 입력창이 비워졌거나 화면이 변했거나 로딩 중이면 성공."""
    deadline = time.time() + config.SEND_CONFIRM_S
    while time.time() < deadline:
        if _loading_visible(page):
            return True
        cur_val = _input_value(el)
        if before_val and not cur_val.strip():
            return True
        if _scope_text(page, mode) != before_text:
            return True
        time.sleep(0.2)
    return False


def send_query(page: Page, query: str, mode: str):
    """입력창에 질의를 넣고 전송. 실패 사유 문자열 반환(성공이면 None)."""
    inp, _ = find_first(page, config.SELECTORS["input"], timeout=10_000)
    if not inp:
        return "입력창 미탐지 (--discover 로 셀렉터 확인 필요)"

    try:
        inp.fill("")
        inp.fill(query)
    except Exception:
        try:
            inp.click()
            page.keyboard.type(query)
        except Exception as e:
            return f"질의 입력 실패: {e}"
    page.wait_for_timeout(200)

    before_val = _input_value(inp)
    before_text = _scope_text(page, mode)

    sent = False
    try:
        inp.press("Enter")
        sent = _confirm_sent(page, inp, before_val, before_text, mode)
    except Exception:
        sent = False

    if not sent:
        # Enter 가 줄바꿈으로 소비되는 UI → 전송 버튼으로 폴백
        btn, _ = find_first(page, config.SELECTORS["submit"], timeout=3000)
        if not btn:
            return "전송 실패: Enter 무반응 + 전송 버튼 미탐지"
        try:
            btn.click()
            sent = _confirm_sent(page, inp, before_val, before_text, mode)
        except Exception as e:
            return f"전송 버튼 클릭 실패: {e}"

    if not sent:
        return "전송 실패: Enter/전송버튼 모두 화면 변화 없음"
    return None


# ── 케이스 실행 ─────────────────────────────────────────────

class CaseBlocked(Exception):
    """실행 자체가 불가능 → Block."""


def execute_case(page: Page, tc: dict, mode: str) -> dict:
    """케이스 1건 실행 후 응답 dict 반환. 실행 실패는 CaseBlocked."""
    url = cell(tc, config.COL_URL)
    pre = cell(tc, config.COL_PRECONDITION)
    steps = cell(tc, config.COL_STEPS)
    query = cell(tc, config.COL_QUERY)

    if url:
        target = config.resolve_url(url)
        try:
            page.goto(target, wait_until="domcontentloaded", timeout=30_000)
        except Exception as e:
            raise CaseBlocked(f"페이지 이동 실패({target}): {e}")

    if pre:
        try:
            actions.run(page, pre, log=None, base_resolve=config.resolve_url)
        except actions.ActionError as e:
            raise CaseBlocked(f"사전조건 실패 → {e}")

    if steps:
        try:
            actions.run(page, steps, log=log, base_resolve=config.resolve_url)
        except actions.ActionError as e:
            raise CaseBlocked(f"수행절차 실패 → {e}")
    elif query:
        err = send_query(page, query, mode)
        if err:
            raise CaseBlocked(err)
    else:
        raise CaseBlocked("실행할 질의도 수행절차도 없음")

    elapsed = wait_for_response(page, mode)
    return {"elapsed": elapsed}


def run_one_case(page: Page, tc: dict, mode: str, index: int) -> dict:
    tc_id = cell(tc, config.COL_ID) or f"CASE-{index}"
    label = cell(tc, config.COL_QUERY) or cell(tc, config.COL_STEPS).replace("\n", " / ")
    log(f"▶ {tc_id}: {label[:60]}")

    executed_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    elapsed = 0.0

    try:
        meta = execute_case(page, tc, mode)
        elapsed = meta["elapsed"]
    except CaseBlocked as e:
        _screenshot(page, tc_id)
        log(f"  └ Block ({e})")
        return {"tc_id": tc_id, "verdict": "Block", "elapsed": 0.0,
                "response_text": "", "note": f"[Block] {e}", "executed_at": executed_at}

    _screenshot(page, tc_id)
    response = read_scope(page, mode)

    for m in config.CUT_MARKERS:
        if m and m in response["text"]:
            response["text"] = response["text"].split(m)[0]

    # 판정은 자르기 전 전문 기준, 저장만 상한 적용
    checkpoint = cell(tc, config.COL_CHECKPOINT)
    expected = cell(tc, config.COL_EXPECTED)
    verdict, details = evaluate(checkpoint, expected, response)

    note = f"[{verdict}]"
    if verdict == "Pass":
        note += " 검증 통과"
        if details:
            note += "\n  - " + "\n  - ".join(details)
    else:
        if checkpoint or expected:
            note += f"\n  - 기대: {(expected or checkpoint)[:200]}"
        note += "\n  - " + "\n  - ".join(details) if details else ""
        note += f"\n  - 응답 길이: {len(response['text'])}자"
        if response.get("scope"):
            note += f"\n  - 판정영역: {response['scope']}"

    log(f"  └ {verdict} ({elapsed:.1f}s"
        + (", scope=body폴백" if response.get("scope_fallback") else "") + ")")
    return {
        "tc_id": tc_id,
        "verdict": verdict,
        "elapsed": elapsed,
        "response_text": response["text"][:config.RESPONSE_STORE_LIMIT],
        "note": note,
        "executed_at": executed_at,
    }


def _screenshot(page: Page, tc_id: str):
    shot_path = config.SHOTS_DIR / f"{tc_id}.png"
    try:
        page.screenshot(path=str(shot_path), full_page=config.SCREENSHOT_FULL_PAGE)
        log(f"  📸 {shot_path.name}")
    except Exception as e:
        log(f"  ❌ 스크린샷 실패: {e}")


# ── 모드/격리 판별 ──────────────────────────────────────────

def decide_mode(cases) -> str:
    if config.MODE in ("chat", "ui"):
        return config.MODE
    for tc in cases:
        if cell(tc, config.COL_STEPS) or cell(tc, config.COL_URL):
            return "ui"
    return "chat"


def decide_isolate(mode: str) -> bool:
    if config.ISOLATE is not None:
        return config.ISOLATE
    # chat 은 대화 맥락 유지가 필요하므로 단일 세션, ui 는 케이스 간 오염 방지
    return mode == "ui"


# ── 인증 ────────────────────────────────────────────────────

def perform_login(browser) -> bool:
    """LOGIN_STEPS 를 실행하고 세션을 STORAGE_STATE 에 저장."""
    if not config.LOGIN_STEPS.strip():
        log("❌ 로그인 절차가 없습니다. --login-file 또는 config.LOGIN_STEPS 를 지정하세요.")
        return False
    log("🔑 로그인 절차 실행 중...")
    ctx = browser.new_context(viewport=config.VIEWPORT)
    page = ctx.new_page()
    try:
        page.goto(config.CHAT_URL, wait_until="domcontentloaded", timeout=30_000)
    except Exception:
        pass
    try:
        actions.run(page, config.LOGIN_STEPS, log=log, base_resolve=config.resolve_url)
    except actions.ActionError as e:
        log(f"❌ 로그인 실패: {e}")
        ctx.close()
        return False
    config.STORAGE_STATE.parent.mkdir(parents=True, exist_ok=True)
    ctx.storage_state(path=str(config.STORAGE_STATE))
    ctx.close()
    log(f"✓ 세션 저장: {config.STORAGE_STATE}")
    return True


def build_context_kwargs(browser, args) -> dict:
    kwargs = {"viewport": config.VIEWPORT}
    has_login = bool(config.LOGIN_STEPS.strip())
    if args.relogin and has_login:
        if not perform_login(browser):
            sys.exit(1)
    elif not config.STORAGE_STATE.exists() and has_login:
        if not perform_login(browser):
            sys.exit(1)
    if config.STORAGE_STATE.exists():
        kwargs["storage_state"] = str(config.STORAGE_STATE)
        log(f"✓ 저장된 세션 사용: {config.STORAGE_STATE.name} (갱신하려면 --relogin)")
    return kwargs


# ── 메인 ────────────────────────────────────────────────────

def build_parser():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario-file", help="시나리오 .xlsx/.csv 경로")
    ap.add_argument("--result-file", help="결과 .xlsx 경로")
    ap.add_argument("--shots-dir", help="스크린샷 저장 폴더")
    ap.add_argument("--url", help="대상 URL")
    ap.add_argument("--wait", type=float, help="응답 최대 대기(초). 기본 30")
    ap.add_argument("--fixed-wait", type=float, help="조건대기 대신 고정 대기(초) — 구버전 동작")
    ap.add_argument("--only", help="특정 테스트 ID만")
    ap.add_argument("--scenario", help="특정 시나리오ID만 (S01, ...)")
    ap.add_argument("--limit", type=int, help="처음 N개만")
    ap.add_argument("--headless", action="store_true", help="헤드리스 모드")
    ap.add_argument("--viewport-shot", action="store_true", help="전체 페이지 대신 화면만 캡처")
    ap.add_argument("--mode", choices=["chat", "ui"], help="실행 모드 강제 (기본: 자동판별)")
    ap.add_argument("--isolate", action="store_true", help="케이스마다 새 브라우저 컨텍스트")
    ap.add_argument("--no-isolate", action="store_true", help="단일 세션 유지(대화 맥락 보존)")
    ap.add_argument("--login-file", help="로그인 절차 DSL 파일")
    ap.add_argument("--storage-state", help="세션 저장 경로 (기본 scripts/.auth/state.json)")
    ap.add_argument("--relogin", action="store_true", help="저장된 세션 무시하고 재로그인")
    ap.add_argument("--save-auth", action="store_true", help="로그인만 수행하고 세션 저장 후 종료")
    ap.add_argument("--discover", action="store_true", help="셀렉터 자동 탐색만")
    ap.add_argument("--map-check", action="store_true", help="헤더 매핑만 확인(브라우저 미실행)")
    return ap


def main():
    args = build_parser().parse_args()
    config.apply_overrides(args)

    if args.map_check:
        cases = load_cases()
        mode = decide_mode(cases)
        log(f"== 헤더 매핑 확인 == {config.SCENARIO_PATH.name}")
        for f, col in (("id", config.COL_ID), ("scenario", config.COL_SCENARIO),
                       ("query", config.COL_QUERY), ("checkpoint", config.COL_CHECKPOINT),
                       ("expected", config.COL_EXPECTED), ("url", config.COL_URL),
                       ("steps", config.COL_STEPS), ("precondition", config.COL_PRECONDITION)):
            log(f"   {f:<12} → {col if col else '(없음)'}")
        log(f"   로드된 케이스: {len(cases)}건 / 판별 모드: {mode} "
            f"(격리={decide_isolate(mode)})")
        for c in cases[:2]:
            act = (cell(c, config.COL_QUERY) or cell(c, config.COL_STEPS)).replace("\n", " / ")
            crit = (cell(c, config.COL_CHECKPOINT) or cell(c, config.COL_EXPECTED)).replace("\n", " ")
            log(f"   - {cell(c, config.COL_ID)} | {act[:50]} | 검증: {crit[:50]}")
        return

    if PLACEHOLDER_HOST in config.CHAT_URL:
        log("❌ 대상 URL 이 지정되지 않았습니다. --url <대상 주소> 를 반드시 지정하세요.")
        sys.exit(2)

    config.SHOTS_DIR.mkdir(parents=True, exist_ok=True)
    config.LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    config.LOG_PATH.unlink(missing_ok=True)

    if sync_playwright is None:
        log("❌ playwright 미설치. 설치: bash setup.sh")
        sys.exit(1)

    log("Playwright 시작 중...")
    try:
        sp = sync_playwright().start()
    except Exception as e:
        log(f"❌ Playwright 시작 실패: {e}")
        log("   → python3 -m playwright install chromium --force 실행 권고")
        sys.exit(1)

    try:
        log(f"Chromium 실행 중 (headless={config.HEADLESS})...")
        browser = sp.chromium.launch(headless=config.HEADLESS)
        log("✓ Chromium 정상 실행")
    except Exception as e:
        log(f"❌ Chromium 실행 실패: {e}")
        sp.stop()
        sys.exit(1)

    results = []
    try:
        if args.save_auth:
            ok = perform_login(browser)
            browser.close()
            sp.stop()
            sys.exit(0 if ok else 1)

        ctx_kwargs = build_context_kwargs(browser, args)

        if args.discover:
            ctx = browser.new_context(**ctx_kwargs)
            discover_selectors(ctx.new_page())
            ctx.close()
            browser.close()
            sp.stop()
            return

        cases = load_cases()
        if args.only:
            cases = [c for c in cases if cell(c, config.COL_ID) == args.only]
        elif args.scenario:
            cases = [c for c in cases if cell(c, config.COL_SCENARIO) == args.scenario]
        if args.limit:
            cases = cases[:args.limit]

        mode = decide_mode(cases)
        isolate = decide_isolate(mode)

        log(f"== 자동화 테스트 시작 == 총 {len(cases)}건")
        log(f"   대상: {config.CHAT_URL}")
        log(f"   모드: {mode} / 케이스 격리: {'ON' if isolate else 'OFF'} / 최대대기 {config.WAIT_MAX_S}s")
        log(f"   시나리오: {config.SCENARIO_PATH.name}  결과: {config.XLSX_PATH.name}")

        if not cases:
            log("⚠️ 실행할 케이스가 없습니다. 시나리오 파일/필터 확인.")
            browser.close()
            sp.stop()
            return

        if isolate:
            results = run_isolated(browser, ctx_kwargs, cases, mode)
        else:
            results = run_shared(browser, ctx_kwargs, cases, mode)
    finally:
        try:
            browser.close()
        except Exception:
            pass
        sp.stop()

    log("\n== 실행 완료 == 결과 XLSX 갱신 중...")
    from writer import update_xlsx
    update_xlsx(results)
    report(results)


def run_shared(browser, ctx_kwargs, cases, mode):
    """단일 세션 (chat 기본) — 대화 맥락 유지."""
    ctx = browser.new_context(**ctx_kwargs)
    page = ctx.new_page()
    log(f"페이지 진입: {config.CHAT_URL}")
    try:
        page.goto(config.CHAT_URL, wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_timeout(2000)
    except Exception as e:
        log(f"❌ 페이지 로드 실패: {e}")
        ctx.close()
        sys.exit(1)

    results = []
    for i, tc in enumerate(cases, 1):
        results.append(_guarded(page, tc, mode, i))
        time.sleep(config.WAIT_BETWEEN_CASES_S)
    ctx.close()
    return results


def run_isolated(browser, ctx_kwargs, cases, mode):
    """케이스마다 새 컨텍스트 (ui 기본) — 상태 오염 차단."""
    results = []
    for i, tc in enumerate(cases, 1):
        ctx = browser.new_context(**ctx_kwargs)
        page = ctx.new_page()
        try:
            if not cell(tc, config.COL_URL):
                page.goto(config.CHAT_URL, wait_until="domcontentloaded", timeout=30_000)
                page.wait_for_timeout(1000)
            results.append(_guarded(page, tc, mode, i))
        except Exception as e:
            log(f"  [예외] {cell(tc, config.COL_ID)}: {e}")
            results.append({
                "tc_id": cell(tc, config.COL_ID) or f"CASE-{i}",
                "verdict": "Block", "elapsed": 0, "response_text": "",
                "note": f"[Block] {str(e)[:300]}",
                "executed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            })
        finally:
            ctx.close()
    return results


def _guarded(page, tc, mode, index):
    try:
        return run_one_case(page, tc, mode, index)
    except Exception as e:
        log(f"  [예외] {cell(tc, config.COL_ID)}: {e}")
        return {
            "tc_id": cell(tc, config.COL_ID) or f"CASE-{index}",
            "verdict": "Block", "elapsed": 0, "response_text": "",
            "note": f"[Block] {str(e)[:300]}",
            "executed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }


def report(results):
    counts = {v: sum(1 for r in results if r["verdict"] == v)
              for v in ("Pass", "Fail", "N/A", "Block")}
    log(f"   Pass: {counts['Pass']} | Fail: {counts['Fail']} | "
        f"N/A: {counts['N/A']} | Block: {counts['Block']} | Total: {len(results)}")
    for v in ("Fail", "Block", "N/A"):
        ids = [r["tc_id"] for r in results if r["verdict"] == v]
        if ids:
            log(f"   {v}: {', '.join(ids)}")
    if counts["N/A"]:
        log("   ※ N/A 는 자동 판정 근거가 없는 케이스입니다. 스크린샷으로 수동 확인하거나")
        log("     기대 결과에 따옴표로 기대값을 명시하면 자동 판정됩니다.")
    log(f"   결과 파일: {config.XLSX_PATH}")


if __name__ == "__main__":
    main()
