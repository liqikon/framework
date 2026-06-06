"""유연한 헤더 자동 매핑.

프로젝트마다 시나리오 엑셀의 컬럼명이 달라도(예: '테스트ID' vs 'TC ID' vs '케이스번호',
'입력(사용자 질의)' vs '질의' vs 'Query') 표준 4개 필드로 자동 매핑한다.

표준 필드:
  id         - 테스트/케이스 식별자  (필수)
  query      - 챗봇에 입력할 사용자 질의 (필수)
  scenario   - 시나리오/그룹 ID (선택, 요약 집계용)
  checkpoint - 검증 포인트/기대 결과 (선택, 없으면 응답 길이로 판정)

config.COLUMN_ALIASES_EXTRA 로 프로젝트별 별칭을 추가할 수 있다.
"""
import re
import unicodedata

# 표준 필드 → 별칭 후보. 정규화(소문자·공백/괄호/기호 제거) 후 비교.
BASE_ALIASES = {
    "id": [
        "테스트id", "테스트케이스id", "테스트케이스", "케이스id", "케이스번호", "시험id",
        "tcid", "tc", "tcno", "testid", "testcaseid", "caseid", "id",
        "no", "번호", "순번", "seq",
    ],
    "scenario": [
        "시나리오id", "시나리오", "시나리오명", "그룹id", "그룹", "대분류", "분류",
        "scenarioid", "scenario", "group", "category",
    ],
    "query": [
        "입력사용자질의", "사용자질의", "입력질의", "입력", "질의", "질문", "발화", "요청",
        "사용자입력", "프롬프트", "query", "input", "prompt", "userinput", "utterance",
    ],
    "checkpoint": [
        "검증포인트", "검증기준", "검증항목", "검증", "확인사항", "판정기준", "합격기준",
        "기대결과정상응답", "기대결과", "기대값", "expected", "expectedresult",
        "checkpoint", "acceptance", "criteria",
    ],
}

# 너무 짧아 오탐 위험이 큰 별칭은 '완전 일치'일 때만 인정
EXACT_ONLY = {"id", "tc", "no", "번호", "순번", "seq", "group", "input", "query", "분류", "그룹"}

REQUIRED = ["id", "query"]   # 없으면 에러
OPTIONAL = ["scenario", "checkpoint"]


def _norm(s):
    if s is None:
        return ""
    s = unicodedata.normalize("NFKC", str(s)).lower().strip()
    # 공백/괄호/기호/언더바 등 제거 → 한글·영문·숫자만
    return re.sub(r"[^0-9a-z가-힣]", "", s)


def _aliases(extra=None):
    table = {k: list(v) for k, v in BASE_ALIASES.items()}
    if extra:
        for field, al in extra.items():
            table.setdefault(field, [])
            table[field] = list(al) + table[field]  # 사용자 별칭 우선
    return table


def _score(header_norm, alias, rank=0):
    """헤더 정규화 문자열 vs 별칭 매칭 점수 (0=불일치).

    rank: 별칭 리스트 내 순서(0=가장 우선). 동일 매칭 품질일 때
    리스트 앞쪽 별칭이 이기도록 작은 가산점을 준다. 이렇게 하면
    한 파일에 '검증 포인트'와 '기대 결과'가 모두 있어도 앞에 둔
    '검증*' 별칭이 checkpoint 로 선택된다.
    """
    if not header_norm or not alias:
        return 0
    prio = max(0, 30 - rank)  # 앞쪽 별칭 우대 (품질 티어 간격보다 작게)
    if header_norm == alias:
        return 1000 + prio          # 완전 일치: 길이 무관, 우선순위로 tie-break
    if alias in EXACT_ONLY:
        return 0                    # 짧은 별칭은 완전 일치만
    if header_norm.startswith(alias) or alias.startswith(header_norm):
        return 500 + min(len(alias), len(header_norm)) + prio
    if alias in header_norm:
        return 300 + len(alias) + prio
    return 0


def match(headers, extra_aliases=None):
    """헤더 리스트 → {field: actual_header_name|None}, 전체 신뢰 점수.

    각 (필드, 컬럼) 쌍 점수를 구해 점수 내림차순으로 1:1 그리디 배정.
    """
    table = _aliases(extra_aliases)
    cand = []  # (score, field, col_index, col_name)
    for ci, h in enumerate(headers):
        hn = _norm(h)
        if not hn:
            continue
        for field, al_list in table.items():
            best = max((_score(hn, _norm(a), rank) for rank, a in enumerate(al_list)),
                       default=0)
            if best > 0:
                cand.append((best, field, ci, h))

    cand.sort(key=lambda x: (-x[0], x[2]))
    mapping = {f: None for f in table}
    used_cols = set()
    used_fields = set()
    total = 0
    for score, field, ci, name in cand:
        if field in used_fields or ci in used_cols:
            continue
        mapping[field] = name
        used_fields.add(field)
        used_cols.add(ci)
        total += score

    return mapping, total


def header_quality(headers, extra_aliases=None):
    """헤더 후보의 '시나리오 헤더다움' 점수 (헤더 행 자동 탐지용)."""
    mapping, total = match(headers, extra_aliases)
    found_required = sum(1 for f in REQUIRED if mapping.get(f))
    # 필수 필드가 다 잡힐수록 가산
    return found_required * 1000 + total, mapping


def resolve(headers, extra_aliases=None):
    """매핑을 확정하고 필수 누락 시 에러. Returns mapping dict."""
    mapping, _ = match(headers, extra_aliases)
    missing = [f for f in REQUIRED if not mapping.get(f)]
    if missing:
        raise ValueError(
            "필수 컬럼 매핑 실패: " + ", ".join(missing) +
            f"\n  헤더: {headers}\n"
            "  → config.py 의 COLUMN_ALIASES_EXTRA 에 별칭을 추가하세요. 예:\n"
            "    COLUMN_ALIASES_EXTRA = {'query': ['우리프로젝트질의컬럼명']}"
        )
    return mapping
