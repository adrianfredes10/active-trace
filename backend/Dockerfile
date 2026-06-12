FROM python:3.13-slim AS builder

WORKDIR /build

RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
COPY app ./app

RUN uv venv /opt/venv \
    && . /opt/venv/bin/activate \
    && uv pip install .

FROM python:3.13-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

COPY --from=builder /opt/venv /opt/venv
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY scripts ./scripts

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
