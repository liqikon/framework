---
title: KB RISE ETF
subtitle: AI 챗봇 서비스 기획
description: 초기 킥오프 내부 공유용
project: KB자산운용 AI ETF
date: 2026-01-05
version: v1.0
author: Frentis
confidential: true
---

# Executive Summary

## 문서 개요

### 문서 구성
이 문서는 KB RISE ETF AI 챗봇 서비스의 기획 내용을 담고 있습니다.

:::info 핵심 키워드
NL2SQL | AWS Bedrock | 하이브리드 검색 | 투자자 여정
:::

### 프로젝트 요약
KB자산운용의 RISE ETF 브랜드를 위한 AI 기반 투자 상담 서비스입니다.

# 프로젝트 개요

## 프로젝트 배경

### 시장 상황
국내 ETF 시장은 빠르게 성장하고 있으며, 투자자들의 정보 접근성 향상이 필요합니다.

| 지표 | 2024년 | 2025년 (예상) |
|:---:|:---:|:---:|
| ETF 순자산 | 100조원 | 150조원 |
| 상품 수 | 700개+ | 900개+ |

## 프로젝트 목적

:::warning 핵심 목표
투자자 경험 혁신을 통한 RISE ETF 브랜드 가치 제고
:::

# 시스템 아키텍처

## 전체 구성도

:::flow 그림 1: 시스템 처리 흐름
사용자 질문 -> Intent 분류 -> NL2SQL/RAG -> 응답 생성 -> 출력
:::

## 기술 스택

| 영역 | 기술 |
|------|------|
| LLM | AWS Bedrock (Claude 3.5) |
| 컨테이너 | ECS + Fargate |
| 프론트엔드 | React |

<!-- pagebreak -->

# 결론

## 핵심 요약

이 프로젝트는 KB자산운용의 디지털 혁신 전략의 일환으로, AI 기술을 활용하여 투자자 경험을 혁신하고자 합니다.

```python
# 샘플 코드
def process_query(query: str) -> str:
    intent = classify_intent(query)
    if intent == "product_lookup":
        return handle_product_lookup(query)
    return handle_general_query(query)
```

> "AI는 투자자와 금융 정보 사이의 거리를 좁혀줍니다."
