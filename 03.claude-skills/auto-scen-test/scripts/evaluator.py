"""검증 포인트 → 자동 판정 룰.

`검증 포인트` 컬럼 문자열에 포함된 키워드로 RULES 의 룰을 적용한다.
매칭된 룰의 80% 이상 통과 시 Pass. 매칭 룰이 없으면 응답 길이로 fallback.

다른 도메인 검수에 쓸 때는 RULES 를 교체/보강하면 된다.
"""
import re

# 키워드 → 판정 함수 (응답 dict: {text, html})
#
# 아래는 범용 예시 룰이다. `검증 포인트` 컬럼에 키(keyword)가 포함되면 해당 룰을
# 적용하고, 매칭되는 키가 하나도 없으면 응답 길이 기반 fallback 으로 판정한다.
# 대상 챗봇/도메인에 맞게 자유롭게 키워드와 판정식을 교체·추가한다.
RULES = {
    # ─── UI/구조 요소 검증 (html 기준) ───
    "차트": lambda r: bool(re.search(r"<svg|<canvas|chart|차트|그래프", r["html"], re.I)),
    "표": lambda r: "table" in r["html"].lower() or r["text"].count("\t") >= 2,
    "이미지": lambda r: "<img" in r["html"].lower(),
    "링크": lambda r: bool(re.search(r'https?://|<a\s', r["html"], re.I)),
    "색상 강조": lambda r: bool(re.search(r'(color|background)\s*[:=]', r["html"])),

    # ─── 응답 내용/형식 검증 (text 기준) ───
    "목록": lambda r: r["text"].count("\n") >= 2 or bool(re.search(r"(^|\n)\s*(\d+\.|①|[-*])", r["text"])),
    "단계": lambda r: bool(re.search(r"(1\.|①|step|단계)", r["text"], re.I)),
    "숫자": lambda r: bool(re.search(r"\d", r["text"])),
    "출처": lambda r: "출처" in r["text"] or "기준일" in r["text"],
    "멀티턴": lambda r: "?" in r["text"] or "선택" in r["text"],
    "결과 없음": lambda r: "없음" in r["text"] or "찾을 수 없" in r["text"],
    "거절": lambda r: "제공하지 않" in r["text"] or "어렵습니다" in r["text"] or "안내가 어렵" in r["text"],

    # ─── 표준 룰 ───
    "응답 정상 생성": lambda r: len(r.get("text", "")) >= 50,
}


def evaluate(checkpoint: str, response: dict) -> tuple:
    """검증 포인트 문자열에서 키워드 추출하여 룰 평가.

    Returns: (전체 통과 여부, 실패 사유 상세 리스트)
    """
    if response.get("error"):
        return False, [f"응답 오류: {response.get('error')}"]
    if not checkpoint:
        return False, ["검증 포인트 정의되지 않음"]
    text = response.get("text", "")
    if not text or len(text) < 30:
        return False, [f"응답 텍스트가 비어있거나 너무 짧음 ({len(text)}자)"]

    failed = []
    matched_keywords = []
    for keyword, rule in RULES.items():
        if keyword in checkpoint:
            matched_keywords.append(keyword)
            try:
                if not rule(response):
                    failed.append(f"'{keyword}' 룰 미충족")
            except Exception as e:
                failed.append(f"'{keyword}' 평가 예외: {e}")

    # 매칭된 룰 자체가 없으면 응답 길이로 fallback 판정
    if not matched_keywords:
        if len(text) >= 100:
            return True, []
        return False, [f"매칭 룰 없음 + 응답 짧음 ({len(text)}자)"]

    matched = len(matched_keywords)
    pass_rate = (matched - len(failed)) / matched
    return pass_rate >= 0.8, failed
