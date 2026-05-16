# AP-Lecture

> **EDU-100 Agent PM 실무 트레이닝** 강의 자료 저장소
> 강사: 박한근 (로디) · phk4568@naver.com

5주 과정으로 AI 기반 프로젝트 관리(Agent PM)를 실무 트레이닝합니다. AP-Framework V0.42 기반으로 PRD부터 검수 자동화까지 17개 산출물 전 생명주기를 다룹니다.

## 시작하기

처음이라면 **[00.시작하기/README.md](00.시작하기/README.md)** 를 먼저 읽어주세요.

```bash
# 환경 셋업 (한 줄)
cd 00.시작하기/ && chmod +x setup.sh && ./setup.sh
```

## 폴더 구조

| 폴더 | 내용 |
|------|------|
| [00.시작하기/](00.시작하기/) | 환경 셋업 가이드 + `setup.sh` 자동 설치 스크립트 |
| [01.강의교재/](01.강의교재/) | W1~W5 주차별 교안 |
| [02.AP-Framework-V0.42/](02.AP-Framework-V0.42/) | 프레임워크 템플릿 (P-101 참조 대상) |
| [03.claude-skills/](03.claude-skills/) | 강의용 Claude 스킬 22개 |
| [04.실습/](04.실습/) | 주차별 실습 가이드 |
| [05.참고자료/](05.참고자료/) | 외부 링크, 백업 영상, 참고 문서 |

## 표준 환경

- **IDE**: Antigravity + Claude Code 플러그인
- **프레임워크**: AP-Framework V0.42
- **기술 스택**: Next.js + Tailwind CSS / Express.js / PostgreSQL / Vercel
- **자동화**: n8n Cloud
- **AI 위키**: NotebookLM (P-104 양방향 동기화)

## 5주 로드맵

| 주차 | 테마 | 학습 산출물 |
|------|------|------------|
| W1 | 기초 이론 · 환경 구축 | PRD · AP-Framework 셋팅 (P-101 + P-102) |
| W2 | 관리 자동화 | 착수보고서 · WBS · 주간보고 · n8n 워크플로우 |
| W3 | 기획 자동화 | 마켓리서치 ~ 화면설계서 (#3 ~ #9) |
| W4 | 구현 자동화 | 인프라/시스템/DB/디자인 + 코드 생성 |
| W5 | 검수 자동화 | 테스트 · CI/CD · 완료보고 · AI Agent |

## 업데이트 받기

강의 진행 중 강사가 자료를 갱신하면:

```bash
git pull
cd 00.시작하기/ && ./setup.sh    # 스킬 갱신이 있는 경우
```

## 라이선스 / 문의

본 자료는 EDU-100 수강생 전용입니다. 외부 배포 금지.
문의: Slack 교육 채널 또는 phk4568@naver.com
