"""검증 포인트 / 기대 결과 → 자동 판정.

판정은 두 축으로 이뤄진다.

1) **리터럴 대조** — `기대 결과`(없으면 `검증 포인트`)에서 따옴표로 감싼 문자열,
   숫자, 코드 토큰을 뽑아 응답에 실제로 들어있는지 확인한다. 하나라도 없으면 Fail.
       기대 결과: 잔액이 "12,000원" 으로 표시된다   → "12,000원" 포함 여부 검사
2) **키워드 룰** — `검증 포인트` 문자열에 RULES 의 키가 포함되면 해당 룰을 적용한다.
   매칭 룰의 80% 이상 통과 시 Pass.

두 축 모두 근거가 없으면 **Pass 가 아니라 N/A(수동 확인)** 를 반환한다.
"응답이 기니까 통과" 같은 무근거 Pass 를 만들지 않는 것이 원칙이다.

판정 대상은 페이지 전체가 아니라 run_tests 가 좁혀 준 **응답 영역**의 text/html 이다.
영역 특정에 실패해 body 전체로 폴백한 경우(scope_fallback), 화면요소 룰(차트/표/링크 등)은
네비게이션·로고를 오검출하므로 자동으로 제외하고 N/A 로 넘긴다.

다른 도메인 검수에 쓸 때는 RULES 를 교체/보강하면 된다.
"""
import re

# 키워드 → 판정 함수 (응답 dict: {text, html})
RULES = {
    # ─── UI/구조 요소 검증 (html 기준) ───
    "차트": lambda r: bool(re.search(r"<svg|<canvas|chart|차트|그래프", r["html"], re.I)),
    "그래프": lambda r: bool(re.search(r"<svg|<canvas|chart|차트|그래프", r["html"], re.I)),
    "표": lambda r: "<table" in r["html"].lower() or r["text"].count("\t") >= 2,
    "테이블": lambda r: "<table" in r["html"].lower(),
    "이미지": lambda r: "<img" in r["html"].lower(),
    "링크": lambda r: bool(re.search(r'https?://|<a\s', r["html"], re.I)),
    "버튼": lambda r: bool(re.search(r"<button|role=[\"']button", r["html"], re.I)),
    "색상 강조": lambda r: bool(re.search(r'(color|background)\s*[:=]', r["html"])),

    # ─── 응답 내용/형식 검증 (text 기준) ───
    "목록": lambda r: r["text"].count("\n") >= 2 or bool(re.search(r"(^|\n)\s*(\d+\.|①|[-*])", r["text"])),
    "단계": lambda r: bool(re.search(r"(1\.|①|step|단계)", r["text"], re.I)),
    "숫자": lambda r: bool(re.search(r"\d", r["text"])),
    "출처": lambda r: "출처" in r["text"] or "기준일" in r["text"],
    "멀티턴": lambda r: "?" in r["text"] or "선택" in r["text"],
    "결과 없음": lambda r: bool(
        re.search(r"없습니다|없음|찾을 수 없|0건|결과가 없", r["text"])
    ),
    "거절": lambda r: "제공하지 않" in r["text"] or "어렵습니다" in r["text"] or "안내가 어렵" in r["text"],
    "오류 메시지": lambda r: bool(re.search(r"오류|에러|실패|error", r["text"], re.I)),

    # ─── 표준 룰 ───
    "응답 정상 생성": lambda r: len(r.get("text", "")) >= 50,
}

# html(=화면 구조)에 의존하는 룰. 판정 영역 특정에 실패하면 신뢰할 수 없어 제외한다.
UI_RULES = {"차트", "그래프", "표", "테이블", "이미지", "링크", "버튼", "색상 강조"}

# 한 글자 키워드는 단순 부분일치 시 다른 낱말에 오매칭된다("표" ⊂ "표시", "대표").
# 앞뒤 한글 경계를 요구하되 조사는 허용한다.
_JOSA = r"(?:가|이|를|을|는|은|와|과|도|만|로|으로|에|의|나)?"
KEYWORD_REGEX = {
    "표": rf"(?<![가-힣])표{_JOSA}(?![가-힣])",
}


def keyword_in(keyword: str, source: str) -> bool:
    """검증 포인트 문자열에 룰 키워드가 '낱말로서' 등장하는지."""
    pat = KEYWORD_REGEX.get(keyword)
    if pat:
        return bool(re.search(pat, source))
    return keyword in source

# 리터럴 추출용
_QUOTED = re.compile(r"[\"'“”‘’「」『』]([^\"'“”‘’「」『』]{1,80}?)[\"'“”‘’「」『』]")
_NUMBER = re.compile(r"\d[\d,]{2,}(?:\.\d+)?%?")          # 3자리 이상 숫자/금액/퍼센트
_CODE = re.compile(r"\b[A-Z]{2,}[A-Z0-9_-]{1,}\b")        # ERR_CODE, HTTP4XX 등


def literal_targets(source: str) -> list:
    """기대 결과 문자열에서 '실제로 화면에 있어야 하는 값'을 추출.

    산문 전체를 부분일치로 비교하면 늘 실패하므로 검증 가능한 토큰만 뽑는다.
    아무것도 못 뽑으면 빈 리스트(=리터럴 검사 생략).
    """
    s = str(source or "").strip()
    if not s:
        return []
    quoted = [m.group(1).strip() for m in _QUOTED.finditer(s)]
    quoted = [q for q in quoted if q]
    if quoted:
        return _dedup(quoted)
    out = [m.group(0) for m in _NUMBER.finditer(s)]
    out += [m.group(0) for m in _CODE.finditer(s)]
    return _dedup(out)


def _dedup(items):
    seen, out = set(), []
    for i in items:
        k = i.lower()
        if k not in seen:
            seen.add(k)
            out.append(i)
    return out


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip().lower()


def _find(hay: str, needle: str) -> bool:
    """부분일치. 단 숫자로 시작/끝나는 기대값은 숫자 경계를 요구한다.

    이게 없으면 기대값 '0건' 이 실제값 '1,250건' 에 부분일치해 오탐 Pass 가 난다.
    """
    if not needle:
        return True
    pat = re.escape(needle)
    if needle[0].isdigit():
        pat = r"(?<![0-9.,])" + pat
    if needle[-1].isdigit():
        pat = pat + r"(?![0-9])"
    return bool(re.search(pat, hay))


def contains_literal(text: str, literal: str) -> bool:
    t, l = _norm(text), _norm(literal)
    if not l:
        return True
    if _find(t, l):
        return True
    # 12,000원 vs 12000원 처럼 자릿수 콤마만 다른 경우 허용
    return _find(t.replace(",", ""), l.replace(",", ""))


def evaluate(checkpoint: str, expected: str, response: dict) -> tuple:
    """Returns (verdict, details) — verdict ∈ {"Pass", "Fail", "N/A"}.

    Block(실행 자체 실패)은 호출부(run_tests)가 판정한다.
    """
    text = response.get("text", "") or ""
    html = response.get("html", "") or ""
    r = {"text": text, "html": html}
    details = []

    if not text.strip() and not html.strip():
        return "Fail", ["응답/화면 내용이 비어 있음 (전송 실패 또는 미응답 의심)"]

    scope_fallback = bool(response.get("scope_fallback"))
    if scope_fallback:
        details.append("⚠ 판정영역 특정 실패 → body 전체 기준 (config.SELECTORS 보강 권장)")

    # ── 1) 리터럴 대조 ──────────────────────────────────────
    lits = literal_targets(expected) or literal_targets(checkpoint)
    lit_missing = [v for v in lits if not contains_literal(text, v)]

    # ── 2) 키워드 룰 ────────────────────────────────────────
    rule_source = " ".join(x for x in (checkpoint, expected) if x)
    matched, rule_failed, skipped_ui = [], [], []
    for keyword, rule in RULES.items():
        if not keyword_in(keyword, rule_source):
            continue
        if scope_fallback and keyword in UI_RULES:
            skipped_ui.append(keyword)      # body 전체에선 오탐 확정 → 평가 제외
            continue
        matched.append(keyword)
        try:
            if not rule(r):
                rule_failed.append(f"'{keyword}' 룰 미충족")
        except Exception as e:
            rule_failed.append(f"'{keyword}' 평가 예외: {e}")

    if skipped_ui:
        details.append(f"화면요소 룰 판정 보류: {', '.join(skipped_ui)}")

    # ── 3) 종합 ────────────────────────────────────────────
    if not lits and not matched:
        if skipped_ui:
            details.append("판정영역 특정 실패로 화면요소 룰을 적용할 수 없음 → 스크린샷으로 수동 확인")
        else:
            details.append("자동 판정 근거 없음: 기대 결과에 대조 가능한 값(따옴표 문자열·숫자·코드)이 "
                           "없고 검증 포인트에 매칭되는 룰도 없음 → 스크린샷으로 수동 확인")
        return "N/A", details

    if lit_missing:
        details += [f"기대값 미검출: '{v}'" for v in lit_missing]
    details += rule_failed

    if lit_missing:
        return "Fail", details
    if matched:
        rate = (len(matched) - len(rule_failed)) / len(matched)
        if rate < 0.8:
            return "Fail", details
    return "Pass", details
