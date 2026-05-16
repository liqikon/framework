---
name: pdf-report
description: "마크다운을 Typst 기반의 전문적인 기획 보고서 PDF로 변환합니다. 표지, 목차, 번호 제목, 정보 박스, 플로우 다이어그램을 자동 생성합니다. 'PDF 보고서', '기획서 PDF로', 'Typst로 변환' 요청에 사용하세요."
---

# pdf-report: Typst 기반 전문 PDF 보고서 생성기

마크다운을 **Typst 기반의 전문적인 기획 보고서 PDF**로 변환하는 스킬입니다.

## 특징

- **Typst 기반**: LaTeX보다 빠르고 마크다운과 유사한 문법
- **한글 지원**: Pretendard, Noto Sans KR 등 한글 폰트 자동 적용
- **전문적 레이아웃**: 표지, 목차, 번호 제목, 페이지 번호 자동 생성
- **커스텀 컴포넌트**: 정보 박스, 경고 박스, 플로우 다이어그램

## 사전 요구사항

```bash
# Typst CLI 설치
brew install typst

# Python 의존성 설치
pip install PyYAML
```

## 사용법

### CLI 실행
```bash
cd ~/.claude/skills/pdf-report
python3 -m pdf_report input.md output.pdf
```

### 옵션
```bash
python3 -m pdf_report input.md output.pdf --logo /path/to/logo.png
```

| 옵션 | 설명 |
|------|------|
| `--logo`, `-l` | 표지 로고 이미지 경로 |
| `--template`, `-t` | 커스텀 Typst 템플릿 경로 |

## 마크다운 문법

### YAML 메타데이터 (표지 정보)
```yaml
---
title: 대제목
subtitle: 부제목
description: 설명문
project: 프로젝트명
date: 2026-01-05
version: v1.0
author: 작성자
confidential: true
---
```

### 제목 (자동 번호)
```markdown
# H1 제목       → "1 H1 제목"
## H2 제목      → "1.1 H2 제목"
### H3 제목     → "1.1.1 H3 제목"
```

### 정보 박스
```markdown
:::info 핵심 키워드
NL2SQL | AWS Bedrock | 하이브리드 검색
:::
```

### 경고 박스
```markdown
:::warning 중요 사항
이 내용은 기밀입니다.
:::
```

### 플로우 다이어그램
```markdown
:::flow 그림 1: 시스템 구조
입력 -> 처리 -> LLM -> 출력
:::
```

### 표
```markdown
| 항목 | 내용 |
|:---:|------|
| 1장 | 개요 |
| 2장 | 설계 |
```

### 페이지 나누기
```markdown
<!-- pagebreak -->
```

## 스타일 가이드

### 색상 팔레트

#### 브랜드 & 텍스트
| 용도 | HEX |
|------|-----|
| 브랜드 블루 (강조) | `#2B579A` |
| 본문 텍스트 | `#1A1A1A` |
| 보조 텍스트 | `#666666` |

#### 배경색
| 용도 | HEX |
|------|-----|
| 정보박스 (info) | `#F5F5F5` |
| 경고박스 (warning) | `#FFF9C4` |

### 폰트
- 기본: Pretendard / Noto Sans KR / Malgun Gothic / Apple SD Gothic Neo
- 우선순위에 따라 시스템에서 사용 가능한 폰트 적용

## 파일 구조
```
pdf-report/
├── SKILL.md              # 이 파일
├── requirements.txt      # 의존성
├── templates/
│   └── report.typ        # Typst 템플릿
├── pdf_report/
│   ├── __init__.py
│   ├── __main__.py       # CLI 엔트리
│   ├── parser.py         # 마크다운 파서
│   └── generator.py      # Typst 생성기
└── examples/
    └── sample_input.md   # 샘플 입력
```

## doc-report와의 차이점

| 기능 | doc-report | pdf-report |
|------|------------|------------|
| 출력 형식 | .docx (Word) | .pdf |
| 엔진 | python-docx | Typst |
| 편집 가능성 | Word에서 편집 가능 | PDF 뷰어 전용 |
| 품질 | 비즈니스 문서 수준 | 출판 품질 |
| 렌더링 속도 | 보통 | 매우 빠름 |

## 참조 스타일
KB자산운용 AI기획 문서 (KB자산운용-AI기획-20260105.pdf) 기반 - Typst 0.13.0 생성
