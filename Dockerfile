FROM python:3.14.9-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /bin/uv

WORKDIR /app
COPY . .
RUN uv sync --no-cache

CMD ["uv", "run", "fastapi", "run", "src/septum/main.py"]
