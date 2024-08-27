FROM python:3.11-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app
COPY . .
RUN uv sync --frozen --no-cache

CMD ["uv", "run", "fastapi", "run", "src/septaplusplus/main.py"]
