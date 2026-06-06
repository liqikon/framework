"""시나리오 기반 자동 테스트 메인 러너.

사용:
  python run_tests.py --scenario-file S.xlsx --result-file R.xlsx \
                      --shots-dir shots --url http://host/chat
  python run_tests.py --only TC-S01-01       # 특정 케이스만
  python run_tests.py --scenario S01          # 특정 시나리오ID만
  python run_tests.py --limit 5               # 처음 5건만
  python run_tests.py --headless              # 브라우저 안 띄움
  python run_tests.py --discover --url <url>  # 셀렉터 자동 탐색
  python run_tests.py --wait 30               # 응답 대기 30초
"""
import argparse
import time
import sys
from datetime import datetime
from pathlib import Path

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


def log(msg: str):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        with open(config.LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def find_first(page: Page, selectors, timeout=5000):
    for sel in selectors:
        try:
            el = page.wait_for_selector(sel, timeout=timeout, state="visible")
            if el:
                return el, sel
        except PWTimeout:
            continue
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

    snippet_path = config.LOG_PATH.parent / "page_snapshot.html"
    snippet_path.write_text(page.content(), encoding="utf-8")
    log(f"\n[페이지 스냅샷 저장] {snippet_path}")
    log("--discover 완료. 위 출력 보고 config.py SELECTORS 정정.")


def send_query_and_capture(page: Page, query: str, tc_id: str, screenshot_dir: Path) -> dict:
    result = {"text": "", "html": "", "elapsed": 0.0, "error": None}
    try:
        inp_el, _ = find_first(page, config.SELECTORS["input"], timeout=10000)
        if not inp_el:
            result["error"] = "입력창 미탐지"
            return result

        try:
            body_before = page.locator("body").inner_text()
        except Exception:
            body_before = ""

        inp_el.fill("")
        inp_el.fill(query)
        page.wait_for_timeout(300)

        t0 = time.time()
        try:
            inp_el.press("Enter")
        except Exception:
            btn_el, _ = find_first(page, config.SELECTORS["submit"], timeout=3000)
            if btn_el:
                btn_el.click()
            else:
                result["error"] = "전송 버튼 미탐지"
                return result

        log(f"  ⏳ {config.WAIT_AFTER_SEND_S}초 대기 중...")
        page.wait_for_timeout(config.WAIT_AFTER_SEND_S * 1000)
        result["elapsed"] = time.time() - t0

        shot_path = screenshot_dir / f"{tc_id}.png"
        try:
            page.screenshot(path=str(shot_path), full_page=True)
            log(f"  📸 스크린샷 저장: {shot_path.name}")
        except Exception as e:
            log(f"  ❌ 스크린샷 실패: {e}")

        try:
            body_after = page.locator("body").inner_text()
            if body_before and body_after.startswith(body_before[:200]):
                diff = body_after[len(body_before):]
            else:
                idx = body_after.rfind(query)
                diff = body_after[idx + len(query):] if idx >= 0 else body_after[-2000:]

            for m in config.CUT_MARKERS:
                if m in diff:
                    diff = diff.split(m)[0]

            result["text"] = diff.strip()[:1500]
            result["html"] = page.content()
        except Exception as e:
            result["error"] = f"응답 추출 실패: {e}"

    except Exception as e:
        result["error"] = f"실행 예외: {e}"
    return result


def run_one_case(page: Page, tc: dict) -> dict:
    tc_id = tc[config.COL_ID]
    query = tc.get(config.COL_QUERY, "")
    checkpoint = tc.get(config.COL_CHECKPOINT, "")
    log(f"▶ {tc_id}: {query[:50]}...")

    response = send_query_and_capture(page, query, tc_id, config.SHOTS_DIR)
    passed, failures = evaluate(checkpoint, response)

    if response.get("error"):
        verdict = "Block"
        note = f"[Block] {response['error']}"
    elif passed:
        verdict = "Pass"
        note = "[Pass] 검증 통과"
        if failures:
            note += f" (부분 실패: {', '.join(failures)})"
    else:
        verdict = "Fail"
        note = (f"[Fail] 검증 포인트 미충족\n"
                f"  - 기대: {checkpoint}\n"
                f"  - 미통과 룰: {', '.join(failures)}\n"
                f"  - 응답 길이: {len(response.get('text',''))}자")
        if len(response.get("text", "")) < 50:
            note += "\n  - ⚠️ 응답이 너무 짧음 (대기 부족 또는 응답 미생성 의심)"

    log(f"  └ {verdict} ({response['elapsed']:.1f}s)")
    return {
        "tc_id": tc_id,
        "verdict": verdict,
        "elapsed": response["elapsed"],
        "response_text": response["text"][:300],
        "note": note,
        "executed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario-file", help="시나리오 .xlsx/.csv 경로")
    ap.add_argument("--result-file", help="결과 .xlsx 경로")
    ap.add_argument("--shots-dir", help="스크린샷 저장 폴더")
    ap.add_argument("--url", help="챗봇 URL")
    ap.add_argument("--wait", type=int, help="질의 전송 후 대기(초)")
    ap.add_argument("--only", help="특정 테스트 ID만")
    ap.add_argument("--scenario", help="특정 시나리오ID만 (S01, ...)")
    ap.add_argument("--headless", action="store_true", help="헤드리스 모드")
    ap.add_argument("--discover", action="store_true", help="셀렉터 자동 탐색만")
    ap.add_argument("--map-check", action="store_true", help="헤더 매핑만 확인하고 종료(브라우저 미실행)")
    ap.add_argument("--limit", type=int, help="처음 N개만")
    args = ap.parse_args()

    config.apply_overrides(args)

    if args.map_check:
        cases = load_cases()
        log(f"== 헤더 매핑 확인 == {config.SCENARIO_PATH.name}")
        log(f"   id='{config.COL_ID}' scenario='{config.COL_SCENARIO}' "
            f"query='{config.COL_QUERY}' checkpoint='{config.COL_CHECKPOINT}'")
        log(f"   로드된 케이스: {len(cases)}건")
        for c in cases[:2]:
            log(f"   - {c.get(config.COL_ID)} | {str(c.get(config.COL_QUERY))[:40]} "
                f"| 검증: {str(c.get(config.COL_CHECKPOINT))[:40]}")
        return

    config.SHOTS_DIR.mkdir(parents=True, exist_ok=True)
    config.LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    config.LOG_PATH.unlink(missing_ok=True)

    headless = config.HEADLESS

    if sync_playwright is None:
        log("❌ playwright 미설치. 설치: python3 -m pip install --user playwright && python3 -m playwright install chromium")
        sys.exit(1)

    log("Playwright 시작 중...")
    try:
        sp = sync_playwright().start()
    except Exception as e:
        log(f"❌ Playwright 시작 실패: {e}")
        log("   → python3 -m playwright install chromium --force 실행 권고")
        sys.exit(1)

    try:
        log(f"Chromium 실행 중 (headless={headless})...")
        browser = sp.chromium.launch(headless=headless)
        log("✓ Chromium 정상 실행")
    except Exception as e:
        log(f"❌ Chromium 실행 실패: {e}")
        sp.stop()
        sys.exit(1)

    results = []
    with browser:
        ctx = browser.new_context(viewport=config.VIEWPORT)
        page = ctx.new_page()

        if args.discover:
            discover_selectors(page)
            browser.close()
            sp.stop()
            return

        cases = load_cases()
        if args.only:
            cases = [c for c in cases if c[config.COL_ID] == args.only]
        elif args.scenario:
            cases = [c for c in cases if c.get(config.COL_SCENARIO) == args.scenario]
        if args.limit:
            cases = cases[:args.limit]

        log(f"== 자동화 테스트 시작 == 총 {len(cases)}건")
        log(f"   대상: {config.CHAT_URL}")
        log(f"   시나리오: {config.SCENARIO_PATH.name}  결과: {config.XLSX_PATH.name}")

        if not cases:
            log("⚠️ 실행할 케이스가 없습니다. 시나리오 파일/필터 확인.")
            browser.close()
            sp.stop()
            return

        log(f"페이지 진입 시도: {config.CHAT_URL}")
        try:
            page.goto(config.CHAT_URL, wait_until="domcontentloaded", timeout=30_000)
            log("✓ 페이지 로드 성공")
            page.wait_for_timeout(3000)
            try:
                page.wait_for_selector(config.SELECTORS["input"][0], timeout=10_000)
                log("✓ 입력창 렌더 확인")
            except Exception:
                log("⚠️ 입력창 렌더 대기 타임아웃 (계속 진행)")
        except Exception as e:
            log(f"❌ 페이지 로드 실패: {e}")
            browser.close()
            sp.stop()
            sys.exit(1)

        for tc in cases:
            try:
                results.append(run_one_case(page, tc))
            except Exception as e:
                log(f"  [예외] {tc.get(config.COL_ID)}: {e}")
                results.append({
                    "tc_id": tc.get(config.COL_ID),
                    "verdict": "Block",
                    "elapsed": 0,
                    "response_text": "",
                    "note": str(e)[:200],
                    "executed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                })
            time.sleep(config.WAIT_BETWEEN_CASES_S)

        browser.close()
    sp.stop()

    log("\n== 실행 완료 == 결과 XLSX 갱신 중...")
    from writer import update_xlsx
    update_xlsx(results)

    pass_n = sum(1 for r in results if r["verdict"] == "Pass")
    fail_n = sum(1 for r in results if r["verdict"] == "Fail")
    block_n = sum(1 for r in results if r["verdict"] == "Block")
    log(f"   Pass: {pass_n} | Fail: {fail_n} | Block: {block_n} | Total: {len(results)}")
    if fail_n or block_n:
        bad = [r["tc_id"] for r in results if r["verdict"] in ("Fail", "Block")]
        log(f"   Fail/Block: {', '.join(bad)}")
    log(f"   결과 파일: {config.XLSX_PATH}")


if __name__ == "__main__":
    main()
