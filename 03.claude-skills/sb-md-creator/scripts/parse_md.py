#!/usr/bin/env python3
"""
화면설계서 마크다운 파서.
마크다운 화면설계서를 파싱하여 구조화된 JSON으로 출력합니다.

Usage:
    python3 parse_md.py <input.md> [output.json]
"""
import re
import json
import sys
from pathlib import Path


def parse_table(text):
    """마크다운 표를 dict 리스트로 파싱."""
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    table_lines = [l for l in lines if l.startswith('|')]
    if len(table_lines) < 2:
        return []
    headers = [h.strip() for h in table_lines[0].split('|')[1:-1]]
    rows = []
    for line in table_lines[2:]:  # skip header + separator
        cells = [c.strip() for c in line.split('|')[1:-1]]
        if len(cells) == len(headers):
            rows.append(dict(zip(headers, cells)))
    return rows


def extract_screen_list(content):
    """## 1. 화면 목록 섹션에서 screen list 추출."""
    screens = []
    m = re.search(r'## 1\. 화면 목록(.*?)(?=^## |\Z)', content, re.DOTALL | re.MULTILINE)
    if not m:
        return screens
    section = m.group(1)
    # Find all markdown tables in the section
    table_blocks = re.findall(r'(\|.+\|(?:\n\|.+\|)*)', section)
    for block in table_blocks:
        rows = parse_table(block)
        for row in rows:
            # Normalize keys
            scr_id = row.get('화면 ID', row.get('ID', ''))
            if re.match(r'SCR-\d+', scr_id):
                screens.append({
                    'id': scr_id,
                    'name': row.get('화면명', ''),
                    'url': row.get('URL', ''),
                    'platform': row.get('플랫폼', ''),
                    'feature_ids': row.get('관련 기능 ID', row.get('관련 기능', '')),
                    'priority': row.get('우선순위', ''),
                })
    return screens


def extract_screen_detail(scr_id, name, content):
    """SCR-NNN 섹션에서 상세 정보 추출."""
    pattern = rf'###\s+{re.escape(scr_id)}\.\s+[^\n]+(.*?)(?=###\s+SCR-|\Z)'
    m = re.search(pattern, content, re.DOTALL)
    if not m:
        return {}

    section = m.group(1)

    # Metadata table (first table at top)
    meta = {}
    meta_match = re.search(r'(\| 항목.*?\| 내용.*?\n(?:\|.*?\n)+)', section, re.DOTALL)
    if meta_match:
        rows = parse_table(meta_match.group(1))
        for row in rows:
            key = row.get('항목', '').strip()
            val = row.get('내용', '').strip()
            meta[key] = val

    # Layout ASCII art (inside code blocks)
    layouts = re.findall(r'```(?:\w*\n)?([\s\S]*?)```', section)

    # UI 컴포넌트 table
    components = []
    comp_match = re.search(r'\*\*UI 컴포넌트\*\*(.*?)(?=\*\*|\Z)', section, re.DOTALL)
    if comp_match:
        comp_table = re.search(r'(\|.+\|(?:\n\|.+\|)*)', comp_match.group(1))
        if comp_table:
            components = parse_table(comp_table.group(1))

    # 상태별 화면 table
    states = []
    state_match = re.search(r'\*\*상태별 화면\*\*(.*?)(?=^---|\*\*|\Z)', section, re.DOTALL | re.MULTILINE)
    if state_match:
        state_table = re.search(r'(\|.+\|(?:\n\|.+\|)*)', state_match.group(1))
        if state_table:
            states = parse_table(state_table.group(1))

    return {
        'meta': meta,
        'layouts': layouts,
        'components': components,
        'states': states,
    }


def parse_md(filepath):
    content = Path(filepath).read_text(encoding='utf-8')

    # Project name from H1
    title_m = re.search(r'^#\s+(.+)', content, re.MULTILINE)
    project_name = title_m.group(1).strip() if title_m else 'Unknown Project'
    # Remove prefix like "화면설계서: "
    project_name = re.sub(r'^화면설계서[:\s]+', '', project_name)

    # Version/date from blockquote
    version_m = re.search(r'버전[:\s]+(v[\d.]+)', content)
    date_m = re.search(r'작성일[:\s]+(\d{4}-\d{2}-\d{2})', content)
    version = version_m.group(1) if version_m else 'v1.0'
    date = date_m.group(1) if date_m else ''

    screens_list = extract_screen_list(content)

    screens = []
    for s in screens_list:
        detail = extract_screen_detail(s['id'], s['name'], content)
        screens.append({**s, **detail})

    return {
        'project_name': project_name,
        'version': version,
        'date': date,
        'screen_count': len(screens),
        'screens': screens,
    }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python3 parse_md.py <input.md> [output.json]')
        sys.exit(1)

    result = parse_md(sys.argv[1])

    if len(sys.argv) >= 3:
        Path(sys.argv[2]).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'Parsed {result["screen_count"]} screens → {sys.argv[2]}')
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
