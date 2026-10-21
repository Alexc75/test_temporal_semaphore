# One build, two images: `--target worker` and `--target starter`.
# Both share every layer except the default command.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS base

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install dependencies first so this layer is cached until uv.lock changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY README.md ./
COPY src ./src
RUN uv sync --locked --no-dev --no-editable

RUN useradd --system --no-create-home app
USER app

FROM base AS worker
CMD ["python", "-m", "laugh_loop.worker"]

FROM base AS starter
CMD ["python", "-m", "laugh_loop.cli"]
