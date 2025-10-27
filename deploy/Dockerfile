FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.local/bin:${PATH}"

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

COPY pyproject.toml README.md ./

RUN uv pip install --system .

COPY app ./app
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
