#!/bin/bash
# auto-scen-test 환경 1회 설치
set -e
cd "$(dirname "$0")"

if command -v python3 &> /dev/null; then PY=python3
elif command -v python &> /dev/null; then PY=python
else echo "❌ Python 미설치. brew install python3 후 재실행."; exit 1; fi

echo "✓ Python: $($PY --version)"
echo "[1/2] 패키지 설치..."
$PY -m pip install --user -r requirements.txt
echo "[2/2] Chromium 설치..."
$PY -m playwright install chromium
echo "✅ 설치 완료."
echo "  $PY run_tests.py --discover --url <챗봇URL>   # (새 UI일 때) 셀렉터 탐색"
echo "  $PY run_tests.py --scenario-file S.xlsx --result-file R.xlsx --shots-dir shots --url <URL> --limit 3"
