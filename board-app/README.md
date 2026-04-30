# board-app

> 멀티 리전 EKS + GitOps 학습용 게시판 애플리케이션

## 개요

이 앱은 **EKS 위에서 ArgoCD로 배포하고 멀티 리전 DR을 검증하기 위한 샘플 워크로드**입니다. 비즈니스 로직보다는 운영 관점 기능(헬스체크, 구조화 로그, 메트릭, 리전 표시)에 중점을 둡니다.

## 기술 스택

| 레이어 | 기술 |
|---|---|
| 리버스 프록시 | Nginx 1.27-alpine |
| 백엔드 | FastAPI (Python 3.12), SQLAlchemy 2.0 (비동기) |
| DB | MySQL 8.0 |
| 프론트엔드 | Jinja2 SSR |
| 마이그레이션 | Alembic |
| 메트릭 | prometheus-fastapi-instrumentator |
| 로깅 | structlog (JSON) |

## 로컬 실행

```bash
cp .env.example .env
docker compose up --build
```

**주요 엔드포인트**:
- `http://localhost/` - 게시판 목록
- `http://localhost/healthz` - Nginx 헬스체크
- `http://localhost:8000/healthz` - Liveness (DB 무관)
- `http://localhost:8000/ready` - Readiness (DB 체크)
- `http://localhost:8000/version` - 리전/환경/버전 정보
- `http://localhost:8000/metrics` - Prometheus 메트릭

## 환경 변수

| 변수 | 설명 | 기본값 |
|---|---|---|
| `DB_HOST` | MySQL 호스트 | `localhost` |
| `DB_PORT` | MySQL 포트 | `3306` |
| `DB_USER` | DB 사용자 | `boarduser` |
| `DB_PASSWORD` | DB 비밀번호 | `boardpass` |
| `DB_NAME` | DB 이름 | `boarddb` |
| `APP_REGION` | 리전 라벨 | `unknown` |
| `APP_ENV` | 환경 라벨 | `local` |
| `APP_VERSION` | 앱 버전 | `dev` |
| `LOG_LEVEL` | 로그 레벨 | `INFO` |

## API

### 웹 UI (Form)
- `GET /` - 목록
- `GET /posts/{id}` - 상세
- `GET /posts/new` - 작성 폼
- `POST /posts` - 작성 처리
- `GET /posts/{id}/edit` - 수정 폼
- `POST /posts/{id}/edit` - 수정 처리
- `POST /posts/{id}/delete` - 삭제

### JSON API
- `GET /api/posts` - 목록
- `GET /api/posts/{id}` - 상세
- `POST /api/posts` - 생성
- `PUT /api/posts/{id}` - 수정
- `DELETE /api/posts/{id}` - 삭제

### 운영
- `GET /healthz` - Liveness (DB 무관, 200 고정)
- `GET /ready` - Readiness (DB 체크, 실패 시 503)
- `GET /version` - 버전/리전/환경/호스트명
- `GET /metrics` - Prometheus 메트릭

## Liveness vs Readiness

| | `/healthz` | `/ready` |
|---|---|---|
| 목적 | Liveness | Readiness |
| DB 의존 | **하지 않음** | `SELECT 1` 실행 |
| DB 단절 시 | 200 유지 | 503 반환 |
| K8s 동작 | 실패 시 Pod **재시작** | 실패 시 트래픽 **분리** |

**중요**: DB가 잠깐 끊겼을 때 Liveness까지 실패하면 무한 재시작 루프에 빠집니다.

### 권장 Probes

```yaml
livenessProbe:
  httpGet: { path: /healthz, port: 8000 }
  initialDelaySeconds: 10
  periodSeconds: 20

readinessProbe:
  httpGet: { path: /ready, port: 8000 }
  initialDelaySeconds: 5
  periodSeconds: 5

startupProbe:
  httpGet: { path: /healthz, port: 8000 }
  periodSeconds: 5
  failureThreshold: 30
```

## 응답 헤더

모든 응답에 포함:
- `X-Request-ID` - 요청 추적 ID
- `X-Process-Time` - 처리 시간 (초)
- `X-Served-Region` / `X-Served-Env` / `X-Served-Pod` - DR 페일오버 확인용

## 메트릭

- 표준 HTTP 메트릭 (prometheus-fastapi-instrumentator)
- `posts_total` (Gauge) - 현재 게시글 수
- `posts_created_total` (Counter) - 누적 생성 수

## DB 스키마

```sql
CREATE TABLE posts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    author VARCHAR(50) NOT NULL,
    created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    INDEX idx_created_at (created_at)
);
```

마이그레이션은 entrypoint에서 자동 실행 (`alembic upgrade head`)

## 로깅

- JSON 1라인 형식, stdout 전용
- 필수 필드: `timestamp`, `level`, `logger`, `event`, `request_id`, `region`, `env`, `version`
- structlog contextvars로 요청 단위 `request_id` 자동 첨부

## 테스트

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest
```

---

**이 앱은 학습용 샘플입니다. 인증, 댓글, 파일 업로드, 검색 등의 기능은 의도적으로 제외되었습니다.**
