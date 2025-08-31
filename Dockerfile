FROM python:3.11-slim AS backend

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    WORKERS=2

WORKDIR /app

# Install system dependencies including Python pip
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ libffi-dev libssl-dev curl \
    python3-dev python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Ensure pip is available and updated
RUN python3 -m pip install --upgrade pip

# Cache-friendly: copier uniquement requirements avant le reste
COPY backend/requirements.txt ./backend/requirements.txt

# Install Python dependencies
RUN python3 -m pip install -r backend/requirements.txt

COPY backend ./backend

# Port Railway (dynamique)
EXPOSE $PORT

# Health check pour emergent.sh avec port dynamique
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -fsS http://127.0.0.1:${PORT:-8001}/api/health || exit 1

# CMD standard emergent.sh - avec variables d'environnement correctes
CMD ["sh", "-c", "python3 -m uvicorn backend.server:app --host 0.0.0.0 --port ${PORT:-8001} --workers ${WORKERS:-2}"]