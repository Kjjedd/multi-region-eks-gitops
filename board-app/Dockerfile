# syntax=docker/dockerfile:1.7

ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN python -m venv /opt/venv \
 && /opt/venv/bin/pip install --upgrade pip \
 && /opt/venv/bin/pip install \
    "fastapi>=0.115" \
    "uvicorn[standard]>=0.32" \
    "sqlalchemy[asyncio]>=2.0" \
    "asyncmy>=0.2.10" \
    "pymysql>=1.1" \
    "cryptography>=43.0" \
    "alembic>=1.13" \
    "pydantic>=2.9" \
    "pydantic-settings>=2.6" \
    "jinja2>=3.1" \
    "python-multipart>=0.0.12" \
    "prometheus-fastapi-instrumentator>=7.0" \
    "structlog>=24.4"


FROM python:${PYTHON_VERSION}-slim AS runtime

ARG APP_VERSION=0.1.0
ARG APP_COMMIT=unknown
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:${PATH}" \
    APP_VERSION=${APP_VERSION} \
    APP_COMMIT=${APP_COMMIT}

LABEL org.opencontainers.image.source="https://github.com/sigwan/board-app" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.revision="${APP_COMMIT}" \
      org.opencontainers.image.title="board-app" \
      org.opencontainers.image.description="Minimal board app for K8s + GitOps + DR study"

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/* \
 && groupadd -g 1000 appuser \
 && useradd -m -u 1000 -g 1000 -s /usr/sbin/nologin appuser

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser alembic ./alembic
COPY --chown=appuser:appuser alembic.ini ./alembic.ini
COPY --chown=appuser:appuser docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/healthz || exit 1

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
