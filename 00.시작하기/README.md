# AP-Lecture 시작하기

> EDU-100 Agent PM 실무 트레이닝 — 수강생 환경 셋업 가이드
> 표준 환경: Antigravity + Claude Code 플러그인 / AP-Framework V0.42

---

## 1. 사전 준비 (수업 전날까지)

수업 첫날 환경 트러블슈팅으로 시간을 낭비하지 않도록, **수업 전날까지** 아래 13개 항목을 모두 완료해주세요.

### 1.1 설치 항목

| # | 항목 | 확인 명령 / 동작 |
|---|------|-----------------|
| 1 | Antigravity IDE 설치 | Antigravity 앱 실행 → 정상 기동 |
| 2 | Claude Code 플러그인 설치 | Antigravity 플러그인 마켓 → Claude Code 설치 |
| 3 | Claude Code 로그인 | Pro 또는 Max 계정 |
| 4 | 통합 터미널 | View → Terminal → 셸 프롬프트 |
| 5 | Git 2.40+ | `git --version` |
| 6 | Node.js 20.x | `node --version` |
| 7 | GitHub 계정 + 로그인 | github.com |
| 8 | GitHub PAT 발급 | Settings > Developer settings > PAT (권한: repo, workflow, project) |
| 9 | Slack 교육 채널 접속 | 강사가 공유한 초대 링크 |
| 10 | n8n Cloud 가입 | app.n8n.cloud |
| 11 | NotebookLM 접속 | notebooklm.google.com |
| 12 | Python 3.11+ | `python3 --version` (이 setup.sh가 `uv`로 보강) |
| 13 | macOS / Linux 셸 환경 | bash 또는 zsh (Windows는 WSL 권장) |

### 1.2 강사에게 제출 (Slack)

수업 전날까지 강사에게 다음을 알려주세요:
- **GitHub 사용자명** (예: `rodimacbook`) → Private repo Collaborator로 초대받기 위해
- **사전 설치 완료 여부** (13개 항목 손들기)

---

## 2. AP-Lecture Repo 받기

강사로부터 Collaborator 초대 메일을 받으면 **Accept invitation** 클릭 후, 본인 로컬에 clone합니다.

```bash
# 원하는 위치로 이동 (예: 홈 디렉토리)
cd ~

# Private repo clone (GitHub PAT 필요)
git clone https://github.com/{강사ID}/AP-Lecture.git

cd AP-Lecture
```

> 강의 진행 중 강사가 자료를 업데이트하면 `git pull`로 항상 최신 상태로 받을 수 있습니다.

---

## 3. 환경 셋업 (한 줄 명령)

`setup.sh`가 강의에 필요한 모든 것을 자동으로 설치해줍니다.

```bash
cd AP-Lecture/00.시작하기/
chmod +x setup.sh
./setup.sh
```

### setup.sh가 자동으로 해주는 것 (약 3분 소요)

| 단계 | 작업 | 결과 |
|------|------|------|
| 1 | `~/.claude/skills/` 셋업 | 강의용 스킬 22개 복사 |
| 2 | `uv` 패키지 매니저 설치 | Python 3.11+ 관리 도구 |
| 3 | `notebooklm-cli` (`nlm`) 설치 | NotebookLM CLI |
| 4 | Claude Code MCP 서버 등록 | `notebooklm-mcp` |
| 5 | 설치 결과 검증 | 22개 스킬 + 도구 버전 확인 |

> **기존 `~/.claude/skills/` 가 있는 경우**: 자동으로 `.bak.타임스탬프` 형식으로 백업되므로 안심하셔도 됩니다.

---

## 4. NotebookLM 인증 (최초 1회)

setup.sh 완료 후, NotebookLM 인증을 한 번 진행합니다 (이후 W1 P-104 실습에서 사용).

```bash
~/.local/bin/nlm login
```

Chrome이 자동으로 열립니다. Google 계정으로 로그인하면 인증이 완료됩니다.

> 인증 세션은 영구 보관됩니다. 만료 시 동일 명령으로 재인증.

---

## 5. Antigravity + Claude Code 플러그인 확인

1. Antigravity 실행
2. Claude Code 플러그인 사이드 패널 열기
3. 테스트 명령 입력: `"폴더 구조 보여줘"`
4. 정상 응답이 출력되면 OK

---

## 6. 강의 자료 구조

```
AP-Lecture/
├── 00.시작하기/                    # 환경 셋업 (이 폴더)
│   ├── README.md                   # 본 문서
│   └── setup.sh                    # 자동 설치 스크립트
├── 01.강의교재/                    # W1~W5 교안 + 슬라이드
│   ├── W1교안_기초이론_환경구축.md
│   ├── W2교안_관리자동화.md
│   ├── W3교안_기획자동화.md
│   ├── W4교안_구현자동화.md
│   └── W5교안_검수자동화.md
├── 02.AP-Framework-V0.42/          # 프레임워크 템플릿 (P-101 참조)
│   ├── CLAUDE.template.md
│   ├── PRD.template.md
│   ├── .progress.md
│   ├── prompts/                    # P-101 ~ P-504 슬래시 명령
│   ├── 00.통합자료실/ ~ 04.검수문서/
│   └── ...
├── 03.claude-skills/               # 강의용 스킬 22개 (setup.sh가 복사)
│   ├── doc-coauthoring/
│   ├── doc-report/
│   ├── pdf-report/
│   ├── sb-creator/
│   ├── n8n-workflow-patterns/
│   └── ... (총 22개)
├── 04.실습/                        # 주차별 실습 가이드
│   ├── exercise-01-환경구축/
│   ├── exercise-02-관리자동화/
│   ├── exercise-03-기획자동화/
│   ├── exercise-04-구현자동화/
│   └── exercise-05-검수자동화/
└── 05.참고자료/                    # 외부 링크, 백업 영상, 참고 문서
    ├── rodi-book-github-url.md
    └── 백업영상_링크모음.md
```

---

## 7. 강의용 스킬 22개 한눈에

setup.sh가 설치하는 스킬 목록입니다. Claude Code 사이드 패널에서 자동으로 트리거됩니다.

### 문서 작성 (4)
| 스킬 | 용도 | 사용 주차 |
|------|------|----------|
| `doc-coauthoring` | 문서 협업 워크플로우 가이드 | 전 주차 |
| `doc-report` | 마크다운 → 전문 Word 보고서 변환 | W2 / W5 |
| `pdf-report` | 마크다운 → Typst 기반 PDF 보고서 | W2 / W5 |
| `docx` | Word 문서 생성/편집 | W2 |

### 화면설계서 (W3 #9 산출물)
| 스킬 | 용도 |
|------|------|
| `sb-creator` | HTML 화면설계서(wireframe) 생성 |
| `sb-md-creator` | 마크다운 화면설계서 → HTML 변환 |
| `sb-creator-pptx` | HTML 화면설계서 → 편집 가능한 PPTX 변환 |

### n8n 자동화 (W1 첫 워크플로우 / W2 / W5)
| 스킬 | 용도 |
|------|------|
| `n8n-workflow-patterns` | 검증된 워크플로우 아키텍처 패턴 |
| `n8n-node-configuration` | 노드 설정 가이드 |
| `n8n-expression-syntax` | n8n 표현식 문법 |
| `n8n-code-javascript` | Code 노드 JavaScript |
| `n8n-code-python` | Code 노드 Python |
| `n8n-validation-expert` | 워크플로우 검증 |
| `n8n-mcp-tools-expert` | n8n-mcp 도구 활용 |

### 기획/리서치
| 스킬 | 용도 | 사용 주차 |
|------|------|----------|
| `socrates` | 소크라테스식 기획 (21개 질문으로 PRD 완성) | W1 |
| `tasks-generator` | 기획서 → 개발 태스크 자동 변환 | W2 WBS |
| `deep-research` | 다중 소스 깊이 있는 리서치 | W3 마켓리서치 |

### 문서/데이터 처리
| 스킬 | 용도 |
|------|------|
| `pdf` | PDF 읽기/병합/추출/OCR (P-104 NLM PDF 처리) |
| `pptx` | PowerPoint 생성/편집 (W2 주간보고, W3 발표) |
| `xlsx` | 스프레드시트 처리 (W2 WBS, 데이터) |

### 구현 / 검수
| 스킬 | 용도 | 사용 주차 |
|------|------|----------|
| `frontend-design` | 고품질 프론트엔드 디자인 | W4 |
| `webapp-testing` | Playwright 기반 웹앱 테스트 | W5 |

---

## 8. 강의 자료 업데이트 받기

강의 진행 중 강사가 자료를 업데이트하면, repo 폴더에서 다음 명령으로 최신 상태 동기화:

```bash
cd AP-Lecture
git pull
```

새 스킬이 추가되거나 기존 스킬이 갱신된 경우 setup.sh를 다시 실행:

```bash
cd 00.시작하기/
./setup.sh
```

---

## 9. 트러블슈팅

| 현상 | 원인 | 해결 |
|------|------|------|
| `Permission denied` (setup.sh 실행 시) | 실행 권한 없음 | `chmod +x setup.sh` |
| `command not found: uv` | PATH 미반영 | 새 터미널 창 열기 또는 `source ~/.zshrc` |
| `nlm login` Chrome 안 열림 | Chrome 미설치 | Chrome 설치 후 재시도 |
| `claude mcp add` 실패 | Claude Code CLI 미설치 | `npm install -g @anthropic-ai/claude-code` |
| `~/.claude/skills/` 권한 오류 | 폴더 소유권 문제 | `sudo chown -R $(whoami) ~/.claude` |
| Antigravity에서 스킬 안 보임 | Antigravity 재시작 필요 | Antigravity 완전 종료 후 재실행 |
| git clone 실패 (Private repo) | PAT 권한 부족 | PAT 재발급 (repo 권한 필수) |

해결되지 않으면 Slack 교육 채널에 스크린샷과 함께 질문해주세요.

---

## 10. 다음 단계

환경 셋업이 완료되면:

1. [01.강의교재/W1교안_기초이론_환경구축.md](../01.강의교재/W1교안_기초이론_환경구축.md) 정독
2. 본인 GitHub에서 **AP-Framework V0.42 Template repo** 생성 준비 (W1 Block C에서 진행)
3. 본인이 만들 프로젝트 주제 한 줄 정리 (W1 Block C에서 사용)

수업에서 만나요!

---

> **강사 연락처**: 박한근 (로디) · phk4568@naver.com · Slack #ap-lecture-1기
