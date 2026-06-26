#!/bin/bash
# =====================================================================
# AP-Lecture 수강생용 환경 셋업 스크립트
# EDU-100 Agent PM 실무 트레이닝
# =====================================================================
# 사용법:
#   cd AP-Lecture/00.시작하기/
#   chmod +x setup.sh
#   ./setup.sh
# =====================================================================
# 이 스크립트가 자동으로 해주는 것:
#   1. ~/.claude/skills/ 에 강의용 스킬 22개 복사
#   2. uv 패키지 매니저 설치 (Python 3.11+ 관리용)
#   3. notebooklm-cli (nlm) 설치 (P-104 NLM 동기화에 필요)
#   4. Claude Code MCP 서버 등록 (notebooklm-mcp)
#   5. 설치 결과 검증
# =====================================================================

set -e

echo "======================================================"
echo "  AP-Lecture 환경 셋업 시작"
echo "======================================================"
echo ""

# ---------- 1. 경로 확인 ----------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_SRC="$REPO_ROOT/03.claude-skills"

if [ ! -d "$SKILLS_SRC" ]; then
    echo "[오류] 강의 스킬 폴더를 찾을 수 없습니다: $SKILLS_SRC"
    echo "       이 스크립트는 AP-Lecture/00.시작하기/ 안에서 실행해야 합니다."
    exit 1
fi

SKILL_COUNT_SRC=$(ls "$SKILLS_SRC" | wc -l | tr -d ' ')
echo "[확인] 강의 스킬 ${SKILL_COUNT_SRC}개를 발견했습니다: $SKILLS_SRC"
echo ""

# ---------- 2. ~/.claude/skills/ 셋업 ----------
echo "[1/5] ~/.claude/skills/ 셋업 중..."

mkdir -p ~/.claude

if [ -e ~/.claude/skills ] && [ ! -L ~/.claude/skills ]; then
    BACKUP="~/.claude/skills.bak.$(date +%Y%m%d%H%M%S)"
    echo "      기존 ~/.claude/skills 발견 → ${BACKUP} 으로 백업"
    mv ~/.claude/skills "$(eval echo $BACKUP)"
elif [ -L ~/.claude/skills ]; then
    echo "      기존 심볼릭 링크 제거"
    rm ~/.claude/skills
fi

mkdir -p ~/.claude/skills

# 강의 스킬 22개를 ~/.claude/skills/ 로 복사
for skill_dir in "$SKILLS_SRC"/*/; do
    skill_name=$(basename "$skill_dir")
    cp -R "$skill_dir" ~/.claude/skills/
done

SKILL_COUNT_DST=$(ls ~/.claude/skills/ | wc -l | tr -d ' ')
echo "[OK]  ${SKILL_COUNT_DST}개 스킬이 ~/.claude/skills/ 에 설치되었습니다"
echo ""

# ---------- 3. uv 패키지 매니저 설치 ----------
echo "[2/5] uv 패키지 매니저 확인 중..."

if [ -x "$HOME/.local/bin/uv" ] || command -v uv &> /dev/null; then
    UV_PATH=$(command -v uv 2>/dev/null || echo "$HOME/.local/bin/uv")
    echo "[OK]  uv 이미 설치됨: $($UV_PATH --version)"
else
    echo "      uv 설치 중..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "[OK]  uv 설치 완료"
fi
echo ""

# ---------- 4. notebooklm-cli 설치 ----------
echo "[3/5] notebooklm-cli (nlm) 확인 중..."

UV_BIN="$HOME/.local/bin/uv"
[ ! -x "$UV_BIN" ] && UV_BIN=$(command -v uv)

if [ -x "$HOME/.local/bin/nlm" ] || command -v nlm &> /dev/null; then
    echo "[OK]  nlm 이미 설치됨"
else
    echo "      notebooklm-mcp-cli 설치 중... (시간이 좀 걸릴 수 있습니다)"
    "$UV_BIN" tool install notebooklm-mcp-cli
    echo "[OK]  notebooklm-mcp-cli 설치 완료"
fi
echo ""

# ---------- 5. Claude Code MCP 서버 등록 ----------
echo "[4/5] Claude Code MCP 서버 등록 중..."

if command -v claude &> /dev/null; then
    if [ -x "$HOME/.local/bin/notebooklm-mcp" ]; then
        claude mcp add --scope user notebooklm-mcp "$HOME/.local/bin/notebooklm-mcp" 2>/dev/null || true
        echo "[OK]  notebooklm-mcp 서버가 Claude Code에 등록되었습니다"
    else
        echo "[!]   notebooklm-mcp 실행 파일을 찾을 수 없습니다"
        echo "      수동 등록: claude mcp add --scope user notebooklm-mcp ~/.local/bin/notebooklm-mcp"
    fi
else
    echo "[!]   Claude Code CLI가 설치되지 않았습니다 (Antigravity 플러그인은 별도)"
    echo "      필요 시 수동 설치: npm install -g @anthropic-ai/claude-code"
fi
echo ""

# ---------- 6. 설치 결과 검증 ----------
echo "[5/5] 설치 결과 검증"
echo "------------------------------------------------------"

INSTALLED_SKILLS=$(ls ~/.claude/skills/ 2>/dev/null | wc -l | tr -d ' ')
echo "  설치된 스킬 수:    ${INSTALLED_SKILLS}개 (목표: 22개)"

if [ "$INSTALLED_SKILLS" = "22" ]; then
    echo "  스킬 설치:         OK"
else
    echo "  스킬 설치:         경고 (목표 22개와 다름)"
fi

UV_VER=$([ -x "$HOME/.local/bin/uv" ] && "$HOME/.local/bin/uv" --version 2>/dev/null || echo "미설치")
echo "  uv:                ${UV_VER}"

NLM_VER=$([ -x "$HOME/.local/bin/nlm" ] && "$HOME/.local/bin/nlm" --version 2>/dev/null || echo "미설치")
echo "  nlm:               ${NLM_VER}"

NLM_MCP=$([ -x "$HOME/.local/bin/notebooklm-mcp" ] && echo "설치됨" || echo "미설치")
echo "  notebooklm-mcp:    ${NLM_MCP}"

CLAUDE_VER=$(command -v claude &> /dev/null && claude --version 2>/dev/null || echo "미설치 (Antigravity 플러그인은 별도)")
echo "  claude CLI:        ${CLAUDE_VER}"

echo "------------------------------------------------------"
echo ""

# ---------- 다음 단계 안내 ----------
echo "======================================================"
echo "  셋업 완료!"
echo "======================================================"
echo ""
echo "  다음 단계:"
echo ""
echo "  1. NotebookLM 인증 (최초 1회):"
echo "     ~/.local/bin/nlm login"
echo "     (Chrome 브라우저가 열리면 Google 로그인)"
echo ""
echo "  2. Antigravity IDE 실행 후 Claude Code 플러그인 로그인"
echo "     (Pro / Max 계정)"
echo ""
echo "  3. 강의 첫 명령 테스트 (Antigravity 사이드 패널):"
echo "     \"폴더 구조 보여줘\""
echo ""
echo "  4. 강의 자료 확인:"
echo "     - 01.강의교재/      W1~W5 교안"
echo "     - 02.AP-Framework-V0.43/  프레임워크 템플릿"
echo "     - 04.실습/          주차별 실습 가이드"
echo ""
echo "  스킬 사용법은 README.md를 참고하세요."
echo "======================================================"
