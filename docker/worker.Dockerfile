FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip

RUN pip install \
    --prefix=/install \
    --no-cache-dir \
    -r requirements.txt

RUN playwright install --with-deps chromium


FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 10001 appgroup \
    && useradd \
        --uid 10001 \
        --gid appgroup \
        --create-home \
        --shell /usr/sbin/nologin \
        appuser

COPY --from=builder /install /usr/local

COPY . .

RUN mkdir -p /app/data \
    && chown -R appuser:appgroup /app

USER appuser

CMD [
    "celery",
    "-A",
    "app.tasks.celery_app",
    "worker",
    "--loglevel=INFO",
    "--queues=research",
    "--concurrency=2"
]