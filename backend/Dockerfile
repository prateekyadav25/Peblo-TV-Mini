FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for Pillow and asyncpg
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY seed_shows.json /app/seed_shows.json
COPY reference.json /app/reference.json

CMD ["sh", "-c", "alembic upgrade head && python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
