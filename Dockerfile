FROM python:3.11.6-slim

WORKDIR /app
COPY pyproject.toml poetry.lock* ./
RUN pip install poetry && poetry install --no-root --only main

COPY src/ ./src/
CMD ["poetry", "run", "python", "-m", "zlog-discord"]
