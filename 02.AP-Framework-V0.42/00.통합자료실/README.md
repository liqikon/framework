# 00.통합자료실

> 이 폴더는 **NotebookLM과 연동되는 프로젝트 통합 자료실**입니다.
> 프로젝트에 필요한 모든 참조 자료를 이 폴더에 보관하면, NotebookLM에서 AI 기반 조회/요약/분석이 가능합니다.

---

## 운용 원칙

### 동기화 방식

- **요청 기반 (수동)**: NotebookLM 공식 API가 없으므로 자동 동기화는 불가하다
- 산출물을 생성/수정한 후, 아래 절차로 NotebookLM에 등록한다
- 비공식 쿠키 기반 인증이므로 세션이 만료되면 `nlm login`을 재실행한다

### 양방향 동기화 구조

```
로컬 (00.통합자료실/)              NotebookLM (프로젝트 노트북)
        |                                    |
        |  ---- nlm source add (업로드) ---->|
        |                                    |
        |  <--- nlm source content (다운) ---|
        |                                    |
        |  <--- AI Q&A / 요약 / 차트 ----    |
        |                                    |
```

1. **로컬 -> NotebookLM**: 이 폴더에 자료를 추가한 후, `nlm source add`로 소스 등록한다
2. **NotebookLM -> 로컬**: `nlm source content`로 NotebookLM 소스를 로컬에 다운로드한다
3. **NotebookLM -> 조회**: NotebookLM에서 등록된 자료를 대상으로 AI 질의, 요약, 차트를 생성한다
4. **최신 상태 유지**: 자료가 갱신되면 NotebookLM 소스도 갱신한다

### 동기화 도구

| 도구 | 설치 | 기능 | 용도 |
|------|------|------|------|
| `notebooklm-cli` (pip) | `pip3 install notebooklm-cli` | 소스 추가/삭제/조회/다운로드 | 파일 업로드/다운로드 (풀 기능) |
| `notebooklm-mcp` (npm) | `claude mcp add notebooklm -- npx notebooklm-mcp@latest` | 질의(RAG)만 가능 | Claude Code에서 노트북에 질문 |

### 자료 등록 절차

#### 방법 1: notebooklm-cli (권장)

```bash
# 최초 1회: 설치
pip3 install notebooklm-cli

# 인증 (Chrome DevTools Protocol, 세션 만료 시 재실행)
nlm login

# 소스 목록 확인
nlm source list <notebook_id>

# 업로드 (파일 내용을 텍스트로 전달)
nlm source add <notebook_id> --text "파일 내용" --title "제목"

# 다운로드
nlm source content <source_id>
```

> `<notebook_id>`는 `.AP-key.md`의 NotebookLM 노트북 URL에서 확인한다.

#### 방법 2: 수동 업로드

1. 이 폴더의 적절한 하위 폴더에 파일을 저장한다
2. [NotebookLM 프로젝트 노트북](https://notebooklm.google.com) 웹에서 해당 파일을 소스로 추가한다
3. `.AP-key.md`의 "등록된 소스 수"를 갱신한다

---

## 폴더 구조

| 폴더 | 용도 | 예시 |
|------|------|------|
| **고객자료/** | 고객 요구사항, RFP, 제안요청서, 사업 브리프 | RFP.pdf, 고객요구사항.md |
| **정책자료/** | 법규, 가이드라인, 사내 표준, 보안 정책 | 개인정보보호법.pdf, 코딩표준.md |
| **인프라자료/** | 서버 구성, 네트워크, DB, 배포 환경 문서 | 인프라구성도.md, Supabase설정.md |
| **회의록/** | 킥오프, 주간회의, 이해관계자 미팅 기록 | 20260404_킥오프.md |
| **참고자료/** | 경쟁사 분석, 벤치마킹, 기술 조사, 레퍼런스 | 경쟁사분석.md, UX트렌드.pdf |

---

## 파일 명명 규칙

- 날짜가 있는 자료: `YYYYMMDD_자료명.확장자` (예: `20260404_킥오프회의록.md`)
- 일반 자료: `자료명.확장자` (예: `RFP_쇼핑몰리뉴얼.pdf`)
- NLM 동기화 자료: `NLM-XX_제목요약.md` (XX: 2자리 번호, 01부터 시작)
- 지원 형식: `.md`, `.pdf`, `.txt`, `.docx`, `.csv` (NotebookLM 지원 형식 기준)

### NLM 동기화 파일 구조 (V0.41 도입 · V0.42 유지)

`참고자료/` 폴더에 NotebookLM 소스를 `NLM-XX_제목요약.md` 형식으로 저장합니다.
P-104 프롬프트 실행 시 자동으로 생성되며, 파일 헤더에 원본 URL과 소스 유형을 명시합니다.

```markdown
# NLM-XX: 제목

> 원본 URL: https://...
> 출처: 도메인명
> 수집일: YYYY-MM-DD
> NotebookLM 소스 유형: web_page | generated_text | pdf

---

(본문)
```

동기화 완료 후 `참고자료/README.md`에 전체 소스 인덱스가 자동 생성됩니다.

---

## NotebookLM 활용 예시

자료가 등록된 상태에서 다음과 같은 질의가 가능하다:

- "고객 RFP에서 요구하는 핵심 기능을 정리해줘"
- "보안 정책에서 개인정보 처리 관련 조항을 요약해줘"
- "인프라 구성과 기능명세서를 비교하여 기술적 제약사항을 분석해줘"
- "지난 3회 회의록에서 미결 사항을 추출해줘"
- "고객자료와 요구사항정의서의 정합성을 검토해줘"

---

## 주의사항

- 민감 정보(인증 키, 비밀번호 등)는 이 폴더에 저장하지 않는다 (`.AP-key.md` 사용)
- 대용량 파일(100MB 이상)은 NotebookLM에 직접 업로드가 불가하므로, 요약본을 별도 작성한다
- 이 폴더는 GitHub에 커밋되므로, 공개 저장소에서는 고객 NDA 자료 포함 여부를 확인한다
