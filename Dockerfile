FROM python:slim

RUN pip install uv

WORKDIR /app
COPY . .
RUN uv pip install --no-cache --system -r requirements.lock

CMD fastapi run src/theseptaapi/main.py
