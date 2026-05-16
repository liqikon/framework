<style>
@media print {
    body, p, li { font-size: 13pt !important; line-height: 1.6 !important; }
    h1 { font-size: 22pt !important; margin-top: 22pt !important; margin-bottom: 14pt !important; }
    h2 { font-size: 18pt !important; margin-top: 18pt !important; margin-bottom: 12pt !important; }
    h3 { font-size: 16pt !important; margin-top: 16pt !important; margin-bottom: 10pt !important; }
    ul, ol { margin-top: 5pt !important; margin-bottom: 5pt !important; padding-left: 22pt !important; }
}
</style>

# CHANGELOG

AP-Framework 버전 변경 이력입니다.
형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/)를 따르며, [Semantic Versioning](https://semver.org/lang/ko/)을 사용합니다.

> 버전 규칙: `MAJOR.MINOR.PATCH`
> - MAJOR: 프레임워크 구조 변경 (폴더 체계, 산출물 흐름 재설계)
> - MINOR: 산출물 추가/삭제, 주요 기능 변경
> - PATCH: 템플릿 내용 수정, 오타 수정, 설명 보완

---

## [Unreleased]

---

## [0.42.0] - 2026-05-16

> 표준 기술 스택 기본값 확정: Next.js + Tailwind CSS / Express.js / PostgreSQL / Vercel.

### Added
- `CLAUDE.template.md`: "Tech Stack (V0.42 기본값 — 표준 스택)" 섹션 신설. 한 줄 표기 `Next.js + Tailwind CSS / Express.js / PostgreSQL / Vercel` 명시
- `03.구현문서/시스템정의서.md`: 기술 스택 표 기본값 4행 (Frontend/Backend/Database/Deploy) 사전 기입
- `02.기획문서/서비스기획서.md`: 7.1 기술 스택 요약 표 기본값 (프론트/백/DB/인프라) 사전 기입
- `01.관리문서/완료보고서.md`: 2.2 코드 산출물 표의 기본 기술 스택 자리 표시 갱신
- `prompts/week1-초기화.md`: P-102 PRD 작성 지시에 표준 기술 스택 명시 가이드 추가

### Changed
- 폴더명: `AP-Framework-V0.41/` -> `AP-Framework-V0.42/`
- `CLAUDE.template.md`: 버전 표기 V0.41 -> V0.42 (헤더, 주석, Project Initialization, prompts 경로)
- `PRD.template.md`: 기술 스택 기본값 `Next.js + Express.js + PostgreSQL` -> `Next.js + Tailwind CSS / Express.js / PostgreSQL / Vercel`
- `.progress.md`: 버전 표기 V0.41 -> V0.42
- `00.통합자료실/README.md`: NLM 동기화 섹션 헤더 (V0.41 신규) -> (V0.41 도입, V0.42 표준 스택 반영)
- `prompts/week1-초기화.md`: 모든 V0.41 폴더/버전 참조를 V0.42로 갱신

### 의도
- 강사/수강생/시연 프로젝트(rodi-book, AP-Rodi-Shop)가 **동일한 표준 스택**을 사용하여 W4 구현 자동화 시 코드 생성 결과의 일관성 확보
- 수강생이 PRD 작성 시 기술 스택을 매번 결정할 필요 없이 기본값을 따르도록 마찰 축소

---

## [0.41.0] - 2026-04-22

> NLM 양방향 동기화: NotebookLM 소스를 로컬 참고자료 폴더에 자동 다운로드.

### Added
- `CLAUDE.template.md`: NLM 양방향 동기화 섹션 (프로세스 다이어그램, 파일 명명 규칙, 소스 유형별 처리, 배치 병렬 처리, 인덱스 자동 생성)
- `prompts/week1-초기화.md`: P-104 NLM 양방향 동기화 프롬프트 (소스 목록 조회 -> 유형별 수집 -> 배치 병렬 -> 인덱스 생성)
- `.progress.md`: Phase 0에 "NLM 소스 로컬 동기화 (P-104)" 항목 추가
- `00.통합자료실/README.md`: NLM 동기화 파일 명명 규칙 (`NLM-XX_제목요약.md`) 및 파일 헤더 구조 안내

### Changed
- 폴더명: `AP-Framework-V0.4/` -> `AP-Framework-V0.41/`
- `CLAUDE.template.md`: 버전 표기 V0.4 -> V0.41
- `CLAUDE.template.md`: NotebookLM 동기화 시점에 P-104 추가 (기존 3가지 -> 4가지)
- `.progress.md`: Phase Gates의 Phase 0 포함 산출물에 NLM 동기화 추가
- `prompts/week1-초기화.md`: 전체 버전 참조 V0.3 -> V0.41 갱신
- `prompts/README.md`: Week 1 프롬프트 수 P-101~P-103 -> P-101~P-104 갱신

---

## [0.4.0] - 2026-04-19

> PRD 중심 전환 + NotebookLM Gate-Check 자동 동기화.

### Added
- Gate-Check 완료 처리 3단계: .progress.md 업데이트 -> NotebookLM 소스 등록 -> 실패 시 [NLM 미등록] 기록
- NotebookLM 동기화 시점 명시: P-103 초기화, Gate-Check 완료, 수동 요청 (3가지)

### Changed
- `README.template.md` -> `PRD.template.md`: 프로젝트 요구사항 문서로 역할 명확화
- PRD.md 헤더에 문서 성격 및 트리거 안내 추가 ("PRD 기반으로 프로젝트 셋팅해줘")
- `CLAUDE.template.md`: 모든 README.md 참조를 PRD.md로 변경
- `CLAUDE.template.md`: 버전 표기 V0.3 -> V0.4
- `CLAUDE.template.md`: NotebookLM 동기화 방식을 "요청 기반(수동)" -> "Gate-Check 연동 자동"으로 변경
- `CLAUDE.template.md`: notebooklm-mcp 설명 현행화 (소스 업로드 불가 -> source_add 지원)
- `.progress.md`: 전제조건 및 Phase Gates의 README.md -> PRD.md 변경
- `prompts/week1-초기화.md`: P-101 복사 대상, P-102 프롬프트를 PRD.md 기준으로 변경
- `prompts/week3-기획자동화.md`: 마켓리서치/서비스기획서 입력 참조를 PRD.md로 변경
- Document Chaining DAG 시작 노드: README -> PRD

---

## [0.3.0] - 2026-04-16

> 프레임워크 구조 개선: 루트 레벨 셋업, Gate-Check 순서 강제, 병렬 에이전트 실행.

### Added
- `CLAUDE.template.md`: 프로젝트 초기화(V0.3) 섹션 (읽기 전용 템플릿 + 루트 레벨 작업)
- `CLAUDE.template.md`: Gate-Check Rules 섹션 (전제조건 확인 -> 미충족 시 안내 -> 완료 기록)
- `CLAUDE.template.md`: Parallel Execution 섹션 (Group A/B 병렬 실행 그룹 정의)
- `CLAUDE.template.md`: 의존관계 DAG 다이어그램 (Mermaid, 순차 17단계 -> 그래프 전환)
- `.progress.md`: 진행 상태 추적기 (Document Chain Status, Phase Gates, Parallel Execution Groups)
- `prompts/week1-초기화.md`: P-101 프로젝트 초기화, P-102 README 작성, P-103 통합자료실 셋업
- `prompts/week3`: P-309 Group A 병렬 실행 (기능명세서 이후 #7, #8, #11, #15 동시 생성)
- `prompts/week4`: P-409 Group B 병렬 실행 (화면설계서 이후 #10, #12, #13 동시 생성)

### Changed
- `CLAUDE.md` -> `CLAUDE.template.md`: 템플릿 파일로 전환 (P-101이 루트에 CLAUDE.md 생성)
- `README.md` -> `README.template.md`: 템플릿 파일로 전환
- `.AP-key.md` -> `.AP-key.template.md`: 템플릿 파일로 전환
- Document Chaining: 순차 리스트(1->17) -> 의존관계 DAG + 산출물 전제조건 표
- `prompts/README.md`: week1 추가, 프롬프트 수 갱신

### 구조 변경 (Breaking)
- 프로젝트 초기화 방식 변경: AP-Framework 폴더 하위에 산출물 생성 -> 프로젝트 루트에 생성
- 산출물 생성 전 `.progress.md` Gate-Check 필수 (전제조건 미충족 시 차단)

---

## [0.2.0] - 2026-04-13

> AP-Rodi-Shop 프로덕션 구축 경험에서 발견된 프레임워크 개선 사항을 정식 반영.

### Added
- `CLAUDE.md`: 도메인 컨텍스트 템플릿 (착수보고서 후 채우기)
- `CLAUDE.md`: 05.리포트 운용 규칙 (온디맨드 파생 자료, NotebookLM 등록 제외)
- `CLAUDE.md`: 주간보고서 작성 규칙 (D-6~D 기간, 파일명 규칙, GitHub API 자동 수집)
- `CLAUDE.md`: Deployment Architecture 섹션 (Vercel, API 프록시, Supabase REST, bcryptjs)
- `CLAUDE.md`: n8n 워크플로우 테이블 5종 (WF 01~05, 트리거/용도/주차 명시)
- `.AP-key.md`: #5 Claude API 섹션 신규
- `.AP-key.md`: #6 Supabase 섹션 신규 (URL, DB 비밀번호, service_role)
- `.AP-key.md`: #7 배포 섹션 신규 (Frontend/Backend 분리)
- `.AP-key.md`: #8 PG사 섹션 신규 (토스페이먼츠 클라이언트/시크릿 키)
- `prompts/week4`: P-406 Vercel 배포 설정
- `prompts/week4`: P-407 결제 연동 (토스페이먼츠)
- `prompts/week4`: P-408 Supabase Storage 연동
- `prompts/week5`: P-505 배포 후 검증 자동화
- `prompts/week5`: P-506 온디맨드 리포트 생성기
- `n8n/`: WF 04 Slack AI GitHub Agent (Chat UI)
- `n8n/`: WF 05 Slack PM Agent (Slack 슬래시 명령)
- `tests/backend/`: jest.config.js 기본 템플릿
- `tests/backend/`: helpers.js (mockRequest/mockResponse 유틸)
- `tests/backend/`: setup.js (테스트 환경 설정)

### Changed
- `.gitignore`: `.AP-key.md` 하드코딩 -> `.*[Kk]ey*` 글로브 패턴 (키 파일명 변경에 유연 대응)
- `.AP-key.md`: PAT 권한에 `project` 추가 (`repo, workflow` -> `repo, workflow, project`)
- `.AP-key.md`: NotebookLM 소스 등록 테이블(24행) 제거 (키 관리 파일에 부적합)
- `.AP-key.md`: 체크리스트 11개 -> 5개로 통합 간소화
- `.AP-key.md`: Slack Webhook은 n8n Credential이 아님을 명시
- `prompts/week4`: P-401 프론트엔드 보강 (Vercel Root Directory, Suspense 래핑, API 프록시)
- `prompts/week4`: P-402 백엔드 보강 (Supabase REST 어댑터, bcryptjs, 커스텀 바디 파서)
- `n8n/README.md`: WF 04-05 아키텍처 설명, Credential 가이드 확장

---

## [0.1.3] - 2026-04-05

### Added
- `02.기획문서/화면설계서.md`: 플랫폼별 와이어프레임 샘플 추가
  - A. 모바일 사용자 (375px) - 8개 화면 (로그인, 회원가입, 본인인증, 목록, 상세, 장바구니, 완료, 설정)
  - B. PC 사용자 (1920px) - 4개 화면 (대시보드, 목록, 상세, 등록/수정 폼)
  - C. PC 어드민 (1920px) - 5개 화면 (대시보드, 회원관리, 콘텐츠관리, 시스템설정, 활동로그)
  - 공통 컴포넌트 가이드 (모달, 토스트, 스켈레톤, 빈 상태)

---

## [0.1.2] - 2026-04-04

### Added
- `02.기획문서/마켓리서치.md`: 시장/경쟁사/트렌드 분석 템플릿 (산업리서치 기반)
- `02.기획문서/서비스기획서.md`: 서비스 콘셉트/BM/MVP 정의 템플릿 (사업기획서 기반)
- `01.관리문서/중간보고서.md`: W3-4 작성 중간 점검 보고서 템플릿
- `01.관리문서/완료보고서.md`: W5 작성 프로젝트 종료 보고서 템플릿
- `03.구현문서/디자인스타일가이드.md`: 디자인 시스템 정의 템플릿

### Changed
- `CLAUDE.md`: Document Chaining 17단계로 확장 (마켓리서치, 서비스기획서, 중간보고서, 완료보고서, 디자인스타일가이드 추가)
- `README.md`: 프로젝트 구조 및 산출물 목록에 신규 문서 반영
- `.AP-key.md`: NotebookLM 소스 등록 체크리스트에 신규 문서 5건 추가
- `prompts/week2-관리자동화.md`: P-207 중간보고서, P-208 완료보고서 프롬프트 추가
- `prompts/week3-기획자동화.md`: P-301 마켓리서치, P-302 서비스기획서 프롬프트 추가
- `prompts/week4-구현자동화.md`: P-405 디자인스타일가이드 프롬프트 추가

---

## [0.1.0] - 2026-04-04

> CHANGELOG 도입 이전에 구축된 내용을 초기 버전으로 통합 기록합니다.

### Added
- AP-Framework 초기 구조 생성
- `00.통합자료실/`: NotebookLM 연동 통합 자료실 (고객/정책/인프라/회의록/참고 하위 폴더)
- `01.관리문서/`: 착수보고서, WBS, 주간보고서 템플릿
- `02.기획문서/`: 요구사항정의서, 기능명세서, API스펙, 정보구조도, 화면설계서 템플릿
- `03.구현문서/`: 인프라아키텍처, 시스템정의서, 데이터베이스설계서 템플릿
- `04.검수문서/`: 테스트시나리오, 테스트결과보고서 템플릿
- `05.리포트/`: 온디맨드 보고서 폴더
- `src/`: 소스 코드 폴더 (frontend/, backend/)
- `tests/`: 테스트 코드 폴더
- `.github/`: CI/CD 파이프라인 (GitHub Actions), Issue 템플릿
- `n8n/`: 워크플로우 자동화 템플릿 4종 (GitHub-Slack 연동, 주간요약, 배포알림)
- `prompts/`: Claude Code 프롬프트 라이브러리 (week2~5 자동화 프롬프트)
- `CLAUDE.md`: Claude Code 프로젝트 규칙 (Document Chaining 12단계, 통합자료실 운용, NotebookLM 연동)
- `README.md`: 프로젝트 개요 및 시작 가이드
- `.AP-key.md`: 서비스 키/URL 관리 파일
- `.gitignore`: Git 제외 규칙

---

## 버전 로드맵

| 버전 | 목표 | 상태 |
|------|------|------|
| 0.1.x | 템플릿 체계 완성 (산출물 17종 + 프롬프트 + 자동화) | 완료 |
| 0.2.0 | 공통 인프라 보강 (배포/결제/Storage 프롬프트, AI Agent WF, 테스트 템플릿) | 완료 |
| 0.3.0 | 구조 개선 (루트 레벨 셋업, Gate-Check, 병렬 실행) | 완료 |
| 0.4.0 | PRD 중심 전환 (README -> PRD.md, 트리거 시나리오) | 완료 |
| 0.41.0 | NLM 양방향 동기화 (NotebookLM -> 로컬 자동 다운로드) | 완료 |
| 0.42.0 | 표준 기술 스택 기본값 확정 (Next.js + Tailwind / Express.js / PostgreSQL / Vercel) | 완료 |
| 0.5.0 | 산업별 프리셋 추가 (금융, 커머스, 교육, 헬스케어) | 계획 |
| 0.6.0 | 다국어 지원 (영문 템플릿) | 계획 |
| 1.0.0 | 정식 릴리스 (문서 검증 완료, 교육 과정 3회 이상 운영) | 계획 |
