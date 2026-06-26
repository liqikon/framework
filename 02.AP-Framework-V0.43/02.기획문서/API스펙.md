# API 스펙

> Week 3 산출물. Claude Code에 다음 명령으로 자동 생성:
> `claude "기능명세서.md를 기반으로 RESTful API 스펙을 작성해줘. 엔드포인트별 Method, URL, Request, Response, 에러코드를 포함해줘"`

**프로젝트명**: [프로젝트명]
**작성일**: YYYY-MM-DD

---

## API 공통 사항

| 항목 | 내용 |
|------|------|
| Base URL | `http://localhost:3000/api` |
| 인증 방식 | Bearer Token (JWT) |
| 응답 형식 | JSON |
| 문자 인코딩 | UTF-8 |

## 공통 에러 코드

| HTTP 상태 코드 | 에러 코드 | 설명 |
|----------------|-----------|------|
| 400 | BAD_REQUEST | 잘못된 요청 |
| 401 | UNAUTHORIZED | 인증 필요 |
| 403 | FORBIDDEN | 권한 없음 |
| 404 | NOT_FOUND | 리소스 없음 |
| 500 | INTERNAL_ERROR | 서버 내부 오류 |

## API 엔드포인트 목록

| API-ID | Method | URL | 기능명 | 관련 기능 ID |
|--------|--------|-----|--------|-------------|
| API-001 | | | | F-001 |
| API-002 | | | | F-002 |

## API 상세

### API-001. [API명]

| 항목 | 내용 |
|------|------|
| Method | GET / POST / PUT / DELETE |
| URL | `/api/...` |
| 설명 | |

**Request**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| | | | |

**Response (200 OK)**

```json
{
  "status": "success",
  "data": {}
}
```

**에러 Response**

| 상태 코드 | 에러 코드 | 조건 |
|-----------|-----------|------|
| | | |
