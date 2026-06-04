# =============================================================================
# AI Librarian Platform — Dockerfile (FIXED)
# =============================================================================

# --- Stage 1: Build dependencies with uv ------------------------------------
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# UBAH: Gunakan /app di sini agar path venv sama dengan runtime
WORKDIR /app 

COPY pyproject.toml uv.lock* ./

RUN uv sync --frozen --no-dev --no-install-project

# --- Stage 2: Runtime -------------------------------------------------------
FROM python:3.12-slim AS runtime

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# UBAH: Copy dari /app/.venv ke /app/.venv
COPY --from=builder /app/.venv /app/.venv

COPY pyproject.toml uv.lock* alembic.ini ./
COPY app/ ./app/
COPY migrations/ ./migrations/

ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/.venv"

EXPOSE 8000

# Opsional namun disarankan: Gunakan python -m uvicorn
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]